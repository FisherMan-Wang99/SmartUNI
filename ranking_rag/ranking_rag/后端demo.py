from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

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
async def recommend(request: Request):
    
    # ----------------------------------------------------
    # 硬编码一个 student profile 用于测试
    # 在测试完成后，请移除这个硬编码的变量，并取消对下面代码的注释
    # ----------------------------------------------------
    data= {
    "academics": {
        "gpa": 3.7,            # Above NYU threshold (3.5)
        "sat": 1370,           # Above NYU threshold (1370)
        "toefl": 85
    },
    "background": {
        "research": "none",
        "internship": "None",
        "extracurricular": ["Film club", "Video production", "Media projects"]  # Emphasize arts/media
    },
    "preferences": {
        "location": "urban",     
        "size": "large",         
        "climate": "moderate",  
        "major": "Film studies",         # Aligns with NYU's strong program
        "Type": "Research",      
        "teaching_style": "Professional, Network-driven"  # Matches NYU style
    },
    "personality": {
        "type": "leadership",
        "traits": ["creative", "networking", "dynamic"]  # Fits NYU culture
    }
}

    universities_db = UNIVERSITIES_DB

    # ----------------------------------------------------
    # 调用你的 RAG 逻辑并获取结果

    # Initialize or load database
    collection, embed_model = init_or_load_vector_database(universities_db)
    
    if collection is None:
        return {"error": "无法加载大学数据库，请检查您的 universities.py 文件。"}

    student_query = create_student_query(data)
    print("Student Query:", student_query)
    print("you have passed student query")

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

    print("you have passed distances")

    matched_universities_text = format_universities_for_prompt(
        matched_universities, distances, data
    )

    try:
        report = generate_report(data, matched_universities_text)
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "生成报告时发生错误，请检查服务器日志。"}

    
    try:
    # 生成报告
        report = generate_report(data, matched_universities_text)
        print("\n" + "="*50)
        print("Generated matched_universities_text:")
        print("="*50)
        print(matched_universities_text)

    except Exception as e:
        # 捕获异常，打印详细错误信息
        import traceback
        print("\n" + "="*50)
        print("Error: Unable to generate report")
        print("Exception:", str(e))
        print("Traceback:")
        traceback.print_exc()
        report = "生成报告时出现错误，请检查服务器日志。"



    print("\n" + "="*50)
    print("Generated University Selection Report:")
    print("="*50)
    print(report)

    simplified_results = []
    for uni in matched_universities:
        simplified_results.append({
            "name": uni.get("name"),
            "level": "N/A",  
            "size": uni.get("size"),
            "academics": uni.get("academics")
        })

    return {"report": report, "results": simplified_results}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)