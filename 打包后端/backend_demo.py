from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
import time
from contextlib import contextmanager

# 导入数据库相关模块
from db import SessionLocal, StudentProfile, RecommendationResult
from sqlalchemy.orm import Session
from fastapi import Query

# 从 ranking_rag.py 中导入所有需要的函数
from ranking_rag import (
    init_or_load_vector_database,
    generate_university_recommendations
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

# 创建FastAPI应用实例，添加描述信息
app = FastAPI(
    title="大学推荐系统API",
    description="基于学生档案和偏好的个性化大学推荐服务",
    version="1.0.0"
)

# 允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        raise HTTPException(status_code=400, detail=f"无法解析前端发送的数据: {str(e)}")

    try:
        # 验证数据结构是否正确
        if not isinstance(data, dict) or 'academics' not in data:
            raise HTTPException(status_code=400, detail="数据结构错误，缺少必要的'academics'字段")
        
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
                
        # 确保academics是字典
        if not isinstance(data['academics'], dict):
            data['academics'] = {}
            
        # 确保activities和preferences存在
        if 'activities' not in data:
            data['activities'] = {}
        if 'preferences' not in data:
            data['preferences'] = {}
                
        data['academics']['gpa'] = convert_to_number(data['academics'].get('gpa'), 0, True)
        data['academics']['sat'] = convert_to_number(data['academics'].get('sat'), 0)
        data['academics']['act'] = convert_to_number(data['academics'].get('act'), 0)
        data['academics']['toefl'] = convert_to_number(data['academics'].get('toefl'), 0)
        data['academics']['ielts'] = convert_to_number(data['academics'].get('ielts'), 0, True)
        data['academics']['det'] = convert_to_number(data['academics'].get('det'), 0)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"学术成绩字段格式错误: {str(e)}")

    # 使用新的函数生成JSON格式的推荐结果
    try:
        recommendations = generate_university_recommendations(data, universities_db)
        
        if recommendations.get("status") == "error":
            return {"error": recommendations.get("message", "生成推荐结果时发生错误")}
        
        report = recommendations.get("report", "")
        simplified_results = recommendations.get("simplified_results", [])
    except Exception as e:
        return {"error": f"生成推荐结果时发生错误: {e}"}

# -------------------------- 保存到数据库（带重试机制） --------------------------
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用依赖注入的db实例
            
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
            db.rollback()
            
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"数据库锁定，第{attempt+1}次重试...")
                time.sleep(0.5 * (attempt + 1))  # 指数退避
                continue
            else:
                print(f"数据库保存失败（最终）: {str(e)}")
                # 不返回错误，让用户仍然能看到推荐结果
                break

    #print("simplified_results:", simplified_results)
    #print("report:", report)
    return {"report": report, "results": simplified_results}


@app.get("/history")
def get_history(student_id: int = Query(..., description="学生ID"), db: Session = Depends(get_db)):
    try:
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="没有找到对应 student_id")

        results = db.query(RecommendationResult).filter(
            RecommendationResult.student_id == student_id
        ).order_by(RecommendationResult.created_at.desc()).all()

        history = []
        for r in results:
            history.append({
                "report": r.report,
                "universities": r.universities_json,
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at)
            })

        return {
            "student_id": student.id,
            "profile": student.profile_json,
            "history": history,
            "total_records": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询历史记录失败: {str(e)}")

if __name__ == "__main__":
    # 从环境变量获取端口号，默认为8000
    port = int(os.getenv("PORT", 80))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

# 用于云托管环境的ASGI入口
# 云托管平台通常会寻找app变量或application变量
application = app  # 兼容更多ASGI服务器