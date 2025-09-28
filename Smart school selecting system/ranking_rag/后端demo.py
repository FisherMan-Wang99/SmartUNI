from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from db import SessionLocal, StudentProfile, RecommendationResult
from sqlalchemy.orm import Session
from fastapi import Query
from contextlib import contextmanager

# 从 ranking_rag.py 中导入所有需要的函数
from ranking_rag import (
    generate_report,
    init_or_load_vector_database,
    create_student_query,
    create_weighted_query_embedding,
    format_universities_for_prompt,
    filter_by_climate,
    classify_schools_strict,
    flatten_metadata
)
# 从 universities.py 中导入数据
from university_db import UNIVERSITIES_DB


universities_db = UNIVERSITIES_DB

# 添加数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 上下文管理器用于数据库操作
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize or load database
collection, embed_model = init_or_load_vector_database(universities_db)

app = FastAPI()

# 允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def home():
    return {"message": "University Recommendation API is running!"}

@app.post("/recommend")
async def recommend(request: Request, db: Session = Depends(get_db)):
    try:
        # 从前端接收 JSON 数据
        data = await request.json()
        print("前端传来的 student profile:", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        return {"error": "无法解析前端发送的数据，请确保发送的是正确的 JSON 格式。"}

    try:
        data['academics']['gpa'] = float(data['academics'].get('gpa', 0))
        data['academics']['sat'] = int(data['academics'].get('sat', 0))
        data['academics']['toefl'] = int(data['academics'].get('toefl', 0))
    except Exception as e:
        return {"error": f"学术成绩字段格式错误: {e}"}

    # -------------------------- 调用 RAG 逻辑 --------------------------
    if collection is None:
        return {"error": "无法加载大学数据库，请检查 universities.py 文件。"}

    student_query = create_student_query(data)
    query_embedding = create_weighted_query_embedding(data, embed_model)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=30,
        include=["metadatas", "distances"]
    )

    if not results['metadatas'] or not results['metadatas'][0]:
        return {"report": "未找到匹配的大学。", "results": []}

    matched_universities = results['metadatas'][0]
    distances = results['distances'][0]

    matched_universities_text = format_universities_for_prompt(
        matched_universities, distances, data
    )

    try:
        report = generate_report(data, matched_universities_text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        report = "生成报告时出现错误，请检查服务器日志。"

# -------------------------- 构建简化返回结果 --------------------------
    simplified_results = []
    level_counts = {"Reach": 0, "Match": 0, "Safety": 0}

    for uni in matched_universities:
        # 学生成绩
        student_gpa = data['academics'].get('gpa', 0)
        student_sat = data['academics'].get('sat', 0)
        student_toefl = data['academics'].get('toefl', 0)

        # 进入 threshold
        threshold_raw = uni.get("admission_threshold", "{}")
        if isinstance(threshold_raw, str):  
            threshold = json.loads(threshold_raw.replace("'", '"'))
        else:
            threshold = threshold_raw

        avg_gpa = threshold.get('gpa', 3.0)
        avg_sat = threshold.get('sat', 1300)
        avg_toefl = threshold.get('toefl', 80)

        # 分类
        if student_gpa < avg_gpa - 0.3 or student_sat < avg_sat - 100 or student_toefl < avg_toefl - 5:
            level = "Reach"
        elif student_gpa > avg_gpa + 0.3 and student_sat > avg_sat + 100 and student_toefl > avg_toefl + 5:
            level = "Safety"
        else:
            level = "Match"

        # 限制最多 10 个
        if level_counts[level] < 5:
            simplified_results.append({
                "name": uni.get("name", "未知学校"),
                "level": level,
                "reasoning": f"基于您的学术背景与该校录取标准的匹配度",
                "admission_probability": "待计算",
                "ranking": uni.get("ranking", {}),
                "location": uni.get("location", ""),
                "size": uni.get("size", ""),
                "academics": uni.get("academics", {})
            })
            level_counts[level] += 1

    # 暂时跳过数据库保存，先确保前端能正常显示结果
    print("推荐结果已生成")
    
# -------------------------- 保存到数据库（带重试机制） --------------------------
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            
            # 1. 存 student profile
            student = StudentProfile(profile_json=data)
            db.add(student)
            db.commit()
            db.refresh(student)

            # 2. 存推荐结果
            recommendation = RecommendationResult(
                student_id=student.id,
                report=report,
                universities_json=simplified_results
            )
            db.add(recommendation)
            db.commit()
            
            print("数据库保存成功")
            break  # 成功则跳出重试循环
            
        except Exception as e:
            if db:
                db.rollback()
                
            if "locked" in str(e) and attempt < max_retries - 1:
                print(f"数据库锁定，第{attempt+1}次重试...")
                import time
                time.sleep(0.5 * (attempt + 1))  # 指数退避
                continue
            else:
                print(f"数据库保存失败（最终）: {e}")
                # 不返回错误，让用户仍然能看到推荐结果
                break
        finally:
            if db:
                db.close()

    print("results:", simplified_results)
    return {"report": report, "results": simplified_results}


@app.get("/history")
def get_history(student_id: int = Query(..., description="学生ID"), db: Session = Depends(get_db)):
    try:
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            return {"error": "没有找到对应 student_id"}

        results = db.query(RecommendationResult).filter(
            RecommendationResult.student_id == student_id
        ).order_by(RecommendationResult.created_at.desc()).all()

        history = []
        for r in results:
            history.append({
                "report": r.report,
                "universities": r.universities_json,
                "created_at": r.created_at
            })

        return {
            "student_id": student.id,
            "profile": student.profile_json,
            "history": history
        }
    except Exception as e:
        return {"error": f"查询历史记录失败: {e}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)