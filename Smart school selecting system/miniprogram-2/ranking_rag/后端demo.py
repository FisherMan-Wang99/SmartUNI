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
        # 转换学术成绩为适当的类型，同时处理None值和空字符串
        def convert_to_number(value, default=0, is_float=False):
            if value is None or value == '':
                return default
            try:
                if is_float:
                    return float(value)
                else:
                    return int(value)
            except:
                return default
                
        data['academics']['gpa'] = convert_to_number(data['academics'].get('gpa'), 0, True)
        data['academics']['sat'] = convert_to_number(data['academics'].get('sat'), 0)
        data['academics']['act'] = convert_to_number(data['academics'].get('act'), 0)
        data['academics']['toefl'] = convert_to_number(data['academics'].get('toefl'), 0)
        data['academics']['ielts'] = convert_to_number(data['academics'].get('ielts'), 0, True)
        data['academics']['det'] = convert_to_number(data['academics'].get('det'), 0)
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

    simplified_results = [] 
    level_counts = {"Reach": 0, "Match": 0, "Safety": 0} 

    # 准备RAG结果的映射，方便查找 
    rag_university_map = {} 
    for i, uni in enumerate(matched_universities): 
        uni_name = uni.get("name", "未知学校") 
        
        # 从RAG结果中提取所有信息，包括reasoning 
        rag_info = { 
            'name': uni_name, 
            'reasoning': uni.get("reasoning", "基于您的学术背景与该校录取标准的匹配度"),  # 提取RAG的reasoning 
            'ranking': uni.get("ranking", {}), 
            'location': uni.get("location", ""), 
            'size': uni.get("size", ""), 
            'academics': uni.get("academics", {}), 
            'distance': distances[i] if i < len(distances) else None 
        } 
        rag_university_map[uni_name] = rag_info 

    for i, uni in enumerate(matched_universities): 
        # 学生成绩 - 包含所有新字段 
        student_gpa = data['academics'].get('gpa', 0) 
        student_sat = data['academics'].get('sat', 0) 
        student_act = data['academics'].get('act', 0) 
        student_toefl = data['academics'].get('toefl', 0) 
        student_ielts = data['academics'].get('ielts', 0) 
        student_det = data['academics'].get('det', 0) 

        # 录取阈值 
        threshold_raw = uni.get("admission_threshold", "{}") 
        if isinstance(threshold_raw, str):  
            threshold = json.loads(threshold_raw.replace("'", '"')) 
        else: 
            threshold = threshold_raw 

        avg_gpa = threshold.get('gpa', 3.0) 
        avg_sat = threshold.get('sat', 1300) 

        # 标准化语言成绩（将IELTS和DET转换为TOEFL等效分数） 
        def get_standardized_toefl(toefl, ielts, det): 
            if toefl > 0: 
                return toefl 
            elif ielts > 0: 
                return min(120, round(ielts * 13.33))  # IELTS * 13.33 约等于 TOEFL 
            elif det > 0: 
                return min(120, round(det * 0.75))  # DET * 0.75 约等于 TOEFL 
            return 0 

        # 标准化SAT/ACT成绩（将ACT转换为SAT等效分数） 
        def get_standardized_sat(sat, act): 
            if sat > 0: 
                return sat 
            elif act > 0: 
                return min(1600, round(act * 40))  # ACT * 40 约等于 SAT 
            return 0 

        # 获取标准化成绩 
        student_std_sat = get_standardized_sat(student_sat, student_act) 
        student_std_toefl = get_standardized_toefl(student_toefl, student_ielts, student_det) 
        avg_toefl = threshold.get('toefl', 80) 

        # 分类 - 基于标准化后的成绩 
        if student_gpa < avg_gpa - 0.3 or student_std_sat < avg_sat - 100 or student_std_toefl < avg_toefl - 5: 
            level = "Reach" 
        elif student_gpa > avg_gpa + 0.3 and student_std_sat > avg_sat + 100 and student_std_toefl > avg_toefl + 5: 
            level = "Safety" 
        else: 
            level = "Match" 

        # 获取RAG相关信息 
        uni_name = uni.get("name", "未知学校") 
        rag_info = rag_university_map.get(uni_name, {}) 
        
        # 直接使用RAG返回的reasoning，如果没有则使用默认值 
        # reasoning = rag_info.get('reasoning', '基于您的学术背景与该校录取标准的匹配度') 

        # 限制每个级别最多5个 
        if level_counts[level] < 5: 
            # 计算录取概率描述 
            def calculate_admission_probability(gpa, std_sat, std_toefl, avg_gpa, avg_sat, avg_toefl): 
                gpa_diff = gpa - avg_gpa 
                sat_diff = std_sat - avg_sat 
                toefl_diff = std_toefl - avg_toefl 
                
                if gpa_diff >= 0.3 and sat_diff >= 100 and toefl_diff >= 5: 
                    return "高" 
                elif gpa_diff >= 0 and sat_diff >= 0 and toefl_diff >= 0: 
                    return "中等" 
                else: 
                    return "较低" 
            
            admission_probability = calculate_admission_probability( 
                student_gpa, student_std_sat, student_std_toefl, 
                avg_gpa, avg_sat, avg_toefl 
            ) 
            
            # 生成推理说明 
            reasoning_points = [] 
            if student_gpa > avg_gpa: 
                reasoning_points.append(f"您的GPA ({student_gpa}) 高于该校平均要求 ({avg_gpa})") 
            elif student_gpa < avg_gpa: 
                reasoning_points.append(f"您的GPA ({student_gpa}) 低于该校平均要求 ({avg_gpa})") 
            
            if student_std_sat > avg_sat: 
                reasoning_points.append(f"您的标准化SAT成绩 ({student_std_sat}) 高于该校平均要求 ({avg_sat})") 
            elif student_std_sat < avg_sat: 
                reasoning_points.append(f"您的标准化SAT成绩 ({student_std_sat}) 低于该校平均要求 ({avg_sat})") 
            
            # 添加专业匹配信息（如果有专业偏好） 
            if data.get('preferences', {}).get('major'): 
                student_major = data['preferences']['major'] 
                # 确保academics是字典 
                academics_data = rag_info.get('academics', {}) 
                if isinstance(academics_data, str): 
                    try: 
                        academics_data = json.loads(academics_data.replace("'", '"')) 
                    except: 
                        academics_data = {} 
                strong_programs = academics_data.get('strong_programs', []) 
                if strong_programs and any(student_major.lower() in prog.lower() for prog in strong_programs): 
                    reasoning_points.append(f"该校的优势项目包含您感兴趣的专业 ({student_major})") 
            
            reasoning = "; ".join(reasoning_points) if reasoning_points else "基于您的学术背景与该校录取标准的匹配度" 
            
            simplified_results.append({ 
                "name": uni_name, 
                "level": level, 
                "reasoning": reasoning, 
                "admission_probability": admission_probability, 
                "ranking": rag_info.get('ranking', {}), 
                "location": rag_info.get('location', ""), 
                "size": rag_info.get('size', ""), 
                "academics": rag_info.get('academics', {}),
                "standardized_sat": student_std_sat 
            }) 
            level_counts[level] += 1 

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

    #print("results before:", simplified_results)
    #print("report:", report)
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