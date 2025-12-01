import sqlite3
from datetime import datetime
import hashlib
import json
import pandas as pd
import json
import os

DB_FILE = "survey_data.db"
DATA_FILE = "survey_results.json"

def load_all_survey_data():
    """
    从数据库读取所有问卷记录，返回Python列表，列表中是字典格式的问卷数据
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_data FROM surveys ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    data_list = []
    for (raw_json,) in rows:
        try:
            data = json.loads(raw_json)
            data_list.append(data)
        except Exception as e:
            # 如果json解析失败，跳过该条数据
            continue
    return data_list

def save_survey_data(data):
    """
    将用户问卷数据追加保存到本地 JSON 文件
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.append(data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

def generate_pdf_report(data, recommendations):
    # 这里先返回一个简单的 PDF 文件内容，作为示例
    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 800, f"大学推荐报告 for {data['name']}")
    c.drawString(100, 780, "推荐大学：")
    for i, uni in enumerate(recommendations, 1):
        c.drawString(120, 780 - i*20, f"{i}. {uni}")
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('university_match.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS survey_responses (
        id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        grade TEXT,
        gpa REAL,
        sat INTEGER,
        interests TEXT,
        size_pref TEXT,
        location_pref TEXT,
        extracurriculars TEXT,
        special_needs TEXT,
        save_code TEXT,
        completed INTEGER DEFAULT 0,
        timestamp DATETIME
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS temp_saves (
        session_id TEXT PRIMARY KEY,
        data TEXT,
        timestamp DATETIME
    )
    ''')
    
    conn.commit()
    conn.close()

def save_temp_progress(session_id, data):
    """保存临时进度"""
    conn = get_db_connection()
    try:
        conn.execute('''
        INSERT OR REPLACE INTO temp_saves (session_id, data, timestamp)
        VALUES (?, ?, ?)
        ''', (session_id, json.dumps(data), datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"保存临时进度出错: {e}")
    finally:
        conn.close()

def load_temp_progress(session_id):
    """加载临时进度"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM temp_saves WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else {}
    except Exception as e:
        print(f"加载临时进度出错: {e}")
        return {}
    finally:
        conn.close()

def save_final_response(response_data):
    """保存最终问卷结果"""
    conn = get_db_connection()
    try:
        response_id = hashlib.md5(f"{response_data['name']}{datetime.now()}".encode()).hexdigest()
        save_code = hashlib.md5(response_id.encode()).hexdigest()[:6].upper()
        
        conn.execute('''
        INSERT INTO survey_responses (
            id, name, email, grade, gpa, sat, interests, 
            size_pref, location_pref, extracurriculars, 
            special_needs, save_code, completed, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            response_id,
            response_data['name'],
            response_data.get('email', ''),
            response_data['grade'],
            response_data['gpa'],
            response_data.get('sat'),
            ','.join(response_data['interests']),
            response_data['size'],
            response_data['location'],
            response_data.get('extracurriculars', ''),
            ','.join(response_data.get('special_needs', [])),
            save_code,
            datetime.now()
        ))
        conn.commit()
        return save_code
    except Exception as e:
        print(f"保存最终结果出错: {e}")
        return None
    finally:
        conn.close()

def recommend_universities(data):
    # 这里写你的推荐逻辑，先用一个示例
    gpa = float(data.get('gpa', 0))
    if gpa >= 3.8:
        return ["Harvard University", "MIT", "Stanford University"]
    elif gpa >= 3.5:
        return ["University of Michigan", "UCLA", "New York University"]
    else:
        return ["Arizona State University", "University of Oregon", "University of Kansas"]

# 初始化数据库
init_db()