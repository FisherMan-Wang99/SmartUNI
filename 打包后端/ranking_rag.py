import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import numpy as np
from openai import OpenAI
import os

"""
大学推荐系统 - RAG模块
功能：基于学生档案和大学数据库，通过向量相似度匹配生成个性化大学推荐
"""


def create_weighted_query_embedding(profile, embed_model):
    """
    创建加权查询嵌入向量，根据学生档案的不同部分分配不同权重
    
    参数:
        profile: 学生档案字典
        embed_model: 用于生成嵌入向量的模型
    
    返回:
        numpy数组: 加权平均后的查询嵌入向量
    """
    weights = {
        "academics": 3.0,
        "activities": 5.0,
        "preferences": 2.0
    }

    embeddings = []
    total_weight = 0

    # 1. 学术背景
    academics = profile.get("academics", {})
    academic_parts = [f"GPA {academics.get('gpa')}", f"SAT {academics.get('sat')}"]
    
    # 新增的考试成绩字段
    for exam_type in ['act', 'toefl', 'ielts', 'det']:
        if academics.get(exam_type):
            academic_parts.append(f"{exam_type.upper()} {academics.get(exam_type)}")
    
    academic_text = ", ".join(academic_parts)
    academic_emb = embed_model.encode(academic_text)
    embeddings.append(weights["academics"] * academic_emb)
    total_weight += weights["academics"]

    # 2. 活动背景
    activities = profile.get("activities", {})
    activities_parts = []
    
    # 处理各种活动经历
    activity_types = [
        ('research_months', 'research_type', 'Research experience'),
        ('volunteer_months', 'volunteer_type', 'Volunteer experience'),
        ('internship_months', 'internship_type', 'Internship'),
        ('art_months', 'art_type', 'Art experience'),
        ('full_time_work_months', 'full_time_work_type', 'Full-time work')
    ]
    
    for months_key, type_key, prefix in activity_types:
        if activities.get(months_key) > 0 and activities.get(type_key):
            activities_parts.append(f"{prefix}: {activities[months_key]} months in {activities[type_key]}")
    
    # 荣誉奖项
    if activities.get("honors"):
        activities_parts.append(f"Honors: {activities['honors']}")
    
    if activities_parts:
        activities_text = " | ".join(activities_parts)
        activities_emb = embed_model.encode(activities_text)
        embeddings.append(weights["activities"] * activities_emb)
        total_weight += weights["activities"]

    # 3. 偏好信息
    preferences = profile.get("preferences", {})
    pref_parts = []
    
    # 基本偏好字段
    pref_mapping = {
        'location': 'Location',
        'size': 'Size',
        'major': 'Major',
        'career_interest': 'Career interest',
        'tuition': 'Tuition budget',
        'teacher_student_ratio': 'Teacher-student ratio preference',
        'school_atmosphere': 'School atmosphere',
        'international_level': 'International level'
    }
    
    for key, label in pref_mapping.items():
        if preferences.get(key):
            pref_parts.append(f"{label}: {preferences[key]}")
    
    if pref_parts:
        pref_text = " | ".join(pref_parts)
        pref_emb = embed_model.encode(pref_text)
        embeddings.append(weights["preferences"] * pref_emb)
        total_weight += weights["preferences"]

    # 加权平均
    query_embedding = np.sum(embeddings, axis=0) / total_weight
    return query_embedding


def safe_json_parse(value, default=None):
    """
    安全地解析JSON字符串，如果解析失败则返回原始值或默认值
    
    参数:
        value: 要解析的值
        default: 解析失败时的默认返回值
    
    返回:
        解析后的值或默认值
    """
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return value
    return value if value is not None else default


def classify_schools_strict(student, universities):
    """
    根据学生成绩和大学录取要求，将大学严格分类为Reach/Match/Safety
    使用改进的录取概率计算和百分位排名算法
    
    参数:
        student: 学生档案字典
        universities: 大学列表
    
    返回:
        字典: 包含reach、match、safety三个分类的大学列表
    """
    # 确保universities是列表
    if not isinstance(universities, list):
        universities = []
    
    reach, match, safety = [], [], []
    
    # 获取学生成绩并标准化
    try:
        gpa = float(student["academics"]["gpa"])
    except (KeyError, ValueError, TypeError):
        gpa = 0.0
        
    try:
        sat = int(student["academics"]["sat"]) if student["academics"].get("sat") else 0
    except (KeyError, ValueError, TypeError):
        sat = 0
        
    try:
        toefl = int(student["academics"]["toefl"]) if student["academics"].get("toefl") else 0
    except (KeyError, ValueError, TypeError):
        toefl = 0
        
    try:
        ielts = float(student["academics"]["ielts"]) if student["academics"].get("ielts") else 0
    except (KeyError, ValueError, TypeError):
        ielts = 0
        
    try:
        det = int(student["academics"]["det"]) if student["academics"].get("det") else 0
    except (KeyError, ValueError, TypeError):
        det = 0
        
    try:
        act = int(student["academics"]["act"]) if student["academics"].get("act") else 0
    except (KeyError, ValueError, TypeError):
        act = 0
    
    # 使用标准化函数处理成绩
    std_toefl = get_standardized_toefl(toefl, ielts, det)
    std_sat = get_standardized_sat(sat, act)
    
    # 为每所大学计算录取概率并分类
    university_probs = []
    
    for uni in universities:
        try:
            # 从academics字段获取大学标化成绩范围（基于university_db.py的结构）
            academics = safe_json_parse(uni.get("academics", {}), {})
            
            # 使用成绩范围的平均值作为计算基准
            # GPA要求
            gpa_range = academics.get("gpa_range", [3.0, 3.5])
            gpa_req = sum(gpa_range) / len(gpa_range)  # 使用范围平均值
            
            # SAT要求
            sat_range = academics.get("sat_range", [1000, 1200])
            sat_req = sum(sat_range) / len(sat_range)  # 使用范围平均值
            
            # TOEFL要求 - 使用最低要求
            toefl_req = academics.get("toefl_min", 80)
            
            # 获取大学排名和录取率
            ranking = uni.get("ranking", {}).get("USNews", 999)
            admission_rate = uni.get("admission_rate", 0.5)
            
            # 使用改进的录取概率计算函数
            prob = calculate_admission_probability(
                gpa, std_sat, std_toefl, 
                gpa_req, sat_req, toefl_req,
                ranking, admission_rate
            )
            
            # 存储大学及其录取概率
            university_probs.append({
                "university": uni,
                "probability": prob,
                "ranking": ranking,
                "admission_rate": admission_rate
            })
        except Exception as e:
            # 记录错误但不中断分类
            print(f"Error classifying university {uni.get('name', 'Unknown')}: {str(e)}")
    
    # 按录取概率排序
    university_probs.sort(key=lambda x: x["probability"], reverse=True)
    
    # 根据录取概率和学校特性进行分类
    for item in university_probs:
        uni = item["university"]
        prob = item["probability"]
        ranking = item["ranking"]
        admission_rate = item["admission_rate"]
        
        # 精英学校特殊处理（排名前20或录取率低于15%）
        if ranking <= 20 or admission_rate < 0.15:
            if prob >= 65:  # 对于精英学校，录取概率65%以上可以视为匹配
                if len(match) < 6:
                    match.append(uni)
            elif prob >= 40:  # 40%以上可以考虑冲刺
                if len(reach) < 3:
                    reach.append(uni)
            else:  # 更低概率也可以作为冲刺学校，但要限制数量
                if len(reach) < 3:
                    reach.append(uni)
        else:
            # 常规学校分类
            if prob >= 80:  # 学生明显强于学校要求
                if len(safety) < 6:
                    safety.append(uni)
            elif prob >= 50:  # 学生与学校要求相当
                if len(match) < 6:
                    match.append(uni)
            else:  # 学生略低于学校要求
                if len(reach) < 3:
                    reach.append(uni)
    
    # 补充逻辑：确保每个类别都有足够的学校
    remaining_unis = [u["university"] for u in university_probs if 
                     u["university"] not in reach and 
                     u["university"] not in match and 
                     u["university"] not in safety]
    
    # 为reach类别补充学校
    if len(reach) < 3 and remaining_unis:
        # 选择排名最高的学校作为冲刺校
        remaining_unis.sort(key=lambda x: x.get("ranking", {}).get("USNews", 999))
        for uni in remaining_unis[:3-len(reach)]:
            reach.append(uni)
            if uni in remaining_unis:
                remaining_unis.remove(uni)
    
    # 为match类别补充学校
    if len(match) < 6 and remaining_unis:
        # 选择录取概率适中的学校作为匹配校
        remaining_unis.sort(key=lambda x: abs(calculate_admission_probability(
            gpa, std_sat, std_toefl,
            x.get("admission_threshold", {}).get("gpa", 3.0),
            x.get("admission_threshold", {}).get("sat", 1000),
            x.get("admission_threshold", {}).get("toefl", 80),
            x.get("ranking", {}).get("USNews", 999),
            x.get("admission_rate", 0.5)
        ) - 60))  # 寻找最接近60%录取概率的学校作为匹配
        for uni in remaining_unis[:6-len(match)]:
            match.append(uni)
            if uni in remaining_unis:
                remaining_unis.remove(uni)
    
    # 为safety类别补充学校
    if len(safety) < 6 and remaining_unis:
        # 选择录取率较高的学校作为保底校
        remaining_unis.sort(key=lambda x: x.get("admission_rate", 0), reverse=True)
        for uni in remaining_unis[:6-len(safety)]:
            safety.append(uni)
    
    # 确保每个类别至少有1所学校（如果可能）
    if len(reach) == 0 and universities:
        sorted_by_ranking = sorted(universities, key=lambda x: x.get("ranking", {}).get("USNews", 999))
        for uni in sorted_by_ranking:
            if uni not in match and uni not in safety:
                reach.append(uni)
                break
    
    if len(match) == 0 and universities:
        # 寻找最接近60%录取概率的学校作为匹配
        sorted_by_match_prob = sorted(
            [u for u in universities if u not in reach and u not in safety],
            key=lambda x: abs(calculate_admission_probability(
                gpa, std_sat, std_toefl,
                x.get("admission_threshold", {}).get("gpa", 3.0),
                x.get("admission_threshold", {}).get("sat", 1000),
                x.get("admission_threshold", {}).get("toefl", 80),
                x.get("ranking", {}).get("USNews", 999),
                x.get("admission_rate", 0.5)
            ) - 60)
        )
        for uni in sorted_by_match_prob:
            match.append(uni)
            break
    
    if len(safety) == 0 and universities:
        sorted_by_admission = sorted(universities, key=lambda x: x.get("admission_rate", 0), reverse=True)
        for uni in sorted_by_admission:
            if uni not in reach and uni not in match:
                safety.append(uni)
                break
    
    # 按要求返回各类别的学校数量：reach最多3所，match和safety最多6所
    return {
        "reach": reach[:3],
        "match": match[:6],
        "safety": safety[:6]
    }


def flatten_metadata(uni):
    """
    将大学元数据中的列表和字典转换为JSON字符串，以便ChromaDB存储
    
    参数:
        uni: 大学信息字典
    
    返回:
        处理后的元数据字典
    """
    meta = {}
    for k, v in uni.items():
        if isinstance(v, (list, dict)):
            meta[k] = json.dumps(v)  # 安全地存储为JSON字符串
        else:
            meta[k] = v
    return meta


def init_or_load_vector_database(universities_list, collection_name="universities", persist_directory="./university_db"):
    """
    初始化或加载向量数据库
    
    参数:
        universities_list: 大学数据列表
        collection_name: 集合名称
        persist_directory: 持久化存储目录
    
    返回:
        tuple: (collection, embed_model)
    """
    # 确保持久化目录存在
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
        
    # 使用ChromaDB客户端
    client = chromadb.PersistentClient(path=persist_directory)

    try:
        # 尝试获取现有集合
        collection = client.get_collection(name=collection_name)
        print("Loading existing university database...")
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        # 如果不存在，创建新集合并添加数据
        print("Creating new university database and vectorizing...")
        collection = client.create_collection(name=collection_name)

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        for uni in universities_list:
            # 创建用于嵌入的文本
            if 'academics' in uni and isinstance(uni['academics'], dict):
                # 适配新的数据结构
                name = uni.get('name', 'Unknown University')
                
                # 从新的数据结构中提取关键信息
                program_parts = []
                academics = uni['academics']
                if 'gpa_range' in academics:
                    program_parts.append(f"GPA range {academics['gpa_range'][0]}-{academics['gpa_range'][1]}")
                if 'sat_range' in academics:
                    program_parts.append(f"SAT range {academics['sat_range'][0]}-{academics['sat_range'][1]}")
                programs_text = ', '.join(program_parts)
                
                # 从preferences中获取文化氛围和位置信息
                culture = ''
                location = ''
                size = ''
                career_orientation = []
                
                if 'preferences' in uni and isinstance(uni['preferences'], dict):
                    pref = uni['preferences']
                    culture = pref.get('school_atmosphere', 'University culture')
                    location = pref.get('location', '')
                    size = pref.get('size', '')
                    career_orientation = pref.get('career_orientation', [])
                
                # 构建适配新数据结构的嵌入文本
                text_parts = [f"{name}"]
                if programs_text:
                    text_parts.append(f"Known for: {programs_text}")
                text_parts.append(f"Culture: {culture}")
                if location:
                    text_parts.append(f"Location: {location}")
                if size:
                    text_parts.append(f"Size: {size}")
                if career_orientation:
                    text_parts.append(f"Career orientation: {', '.join(career_orientation)}")
                    
                text_to_embed = ". ".join(text_parts)
            else:
                # 旧数据结构
                text_to_embed = f"{uni['name']}. Known for: {', '.join(uni['academics']['strong_programs'])}. Culture: {uni['culture']}. For students who: {', '.join(uni['strengths_for'])}. Tags: {', '.join(uni['fit_tags'])}"

            documents.append(text_to_embed)
            metadatas.append(flatten_metadata(uni))
            ids.append(str(uni["id"]))
            embeddings.append(embed_model.encode(text_to_embed).tolist())

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("University database created and vectorized!")

    return collection, embed_model


def create_student_query(profile):
    """
    将学生档案转换为查询文本
    
    参数:
        profile: 学生档案字典
    
    返回:
        str: 格式化的查询文本
    """
    query_parts = []

    # 学术信息
    ac = profile['academics']
    academic_parts = [f"GPA {ac['gpa']}", f"SAT {ac['sat']}"]
    for exam_type in ['act', 'toefl', 'ielts', 'det']:
        if ac.get(exam_type):
            academic_parts.append(f"{exam_type.upper()} {ac[exam_type]}")
    query_parts.append(f"Academics: {', '.join(academic_parts)}")

    # 活动经历
    activities = profile['activities']
    activities_parts = []
    
    # 处理各种活动经历
    activity_types = [
        ('research_months', 'research_type', '{} months research in {}'),
        ('volunteer_months', 'volunteer_type', '{} months volunteer in {}'),
        ('internship_months', 'internship_type', '{} months internship in {}'),
        ('art_months', 'art_type', '{} months art in {}'),
        ('full_time_work_months', 'full_time_work_type', '{} months full-time work in {}')
    ]
    
    for months_key, type_key, format_str in activity_types:
        if activities.get(months_key) > 0 and activities.get(type_key):
            activities_parts.append(format_str.format(activities[months_key], activities[type_key]))
    
    # 荣誉奖项
    if activities.get('honors'):
        activities_parts.append(f"Honors: {activities['honors']}")
    
    if activities_parts:
        query_parts.append(f"Activities: {'; '.join(activities_parts)}")

    # 偏好信息
    pref = profile['preferences']
    pref_parts = [
        f"{pref['location']} location", 
        f"{pref['size']} size",
        f"wants to study {pref['major']}"
    ]
    
    # 新增的偏好字段
    pref_mapping = {
        'career_interest': 'career interest in {}',
        'tuition': 'tuition budget {}',
        'teacher_student_ratio': '{} teacher-student ratio',
        'school_atmosphere': '{} school atmosphere',
        'international_level': '{} international level'
    }
    
    for key, format_str in pref_mapping.items():
        if pref.get(key):
            pref_parts.append(format_str.format(pref[key]))
    
    query_parts.append(f"Preferences: {'; '.join(pref_parts)}")

    return " ".join(query_parts)


def format_universities_for_prompt(matched_universities, distances, student_profile=None):
    """
    格式化匹配的大学信息，用于生成报告
    
    参数:
        matched_universities: 匹配的大学列表
        distances: 距离列表（用于计算相似度）
        student_profile: 学生档案字典（可选）
    
    返回:
        str: 格式化的大学信息文本
    """
    # 首先对所有匹配的大学进行分类
    categories = classify_schools_strict(student_profile, matched_universities)
    
    formatted_text = """
```

# 匹配大学列表（按类别分组）

以下是根据您的学术背景和个人偏好匹配到的大学，按录取难度分为冲刺校(Reach)、匹配校(Match)和保底校(Safety)三类：
"""
    
    for cat_name, uni_list in categories.items():
        # 添加类别标题
        category_title = {
            "reach": "## 冲刺校 (Reach) - 有挑战性但值得尝试的大学",
            "match": "## 匹配校 (Match) - 与您的学术水平最匹配的大学",
            "safety": "## 保底校 (Safety) - 录取把握较大的大学"
        }.get(cat_name, f"## {cat_name.capitalize()}")
        
        formatted_text += f"\n{category_title}\n\n"
        
        if not uni_list:
            formatted_text += "数据库中该类别大学数量不足\n\n"
            continue
            
        for i, uni in enumerate(uni_list):
            # 找到索引以获取相似度
            idx = next((j for j, u in enumerate(matched_universities) if u['id'] == uni['id']), None)
            similarity = 1 - distances[idx] if idx is not None else 0

            # 解析JSON格式的字段
            academics = safe_json_parse(uni.get('academics', '{}'), {})
            strengths_for = safe_json_parse(uni.get('strengths_for', '[]'), [])
            fit_tags = safe_json_parse(uni.get('fit_tags', '[]'), [])
            
            # 计算录取概率
            if student_profile and academics:
                try:
                    # 获取学生成绩
                    student_gpa = float(student_profile['academics']['gpa'])
                    student_sat = int(student_profile['academics']['sat']) if student_profile['academics'].get('sat') else 0
                    student_toefl = int(student_profile['academics']['toefl']) if student_profile['academics'].get('toefl') else 0
                    student_ielts = float(student_profile['academics']['ielts']) if student_profile['academics'].get('ielts') else 0
                    student_det = int(student_profile['academics']['det']) if student_profile['academics'].get('det') else 0
                    student_act = int(student_profile['academics']['act']) if student_profile['academics'].get('act') else 0
                    
                    # 从academics字段获取大学标化成绩范围（基于university_db.py的结构）
                    # GPA要求 - 使用范围平均值
                    gpa_range = academics.get("gpa_range", [3.0, 3.5])
                    uni_gpa_req = sum(gpa_range) / len(gpa_range)
                    
                    # SAT要求 - 使用范围平均值
                    sat_range = academics.get("sat_range", [1000, 1200])
                    uni_sat_req = sum(sat_range) / len(sat_range)
                    
                    # TOEFL要求 - 使用最低要求
                    uni_toefl_req = academics.get("toefl_min", 80)
                    
                    # 获取大学排名和录取率
                    ranking = uni.get('ranking', {}).get('USNews', 999)
                    admission_rate = uni.get('admission_rate', 0.5)
                    
                    # 使用标准化函数处理成绩
                    std_toefl = get_standardized_toefl(student_toefl, student_ielts, student_det)
                    std_sat = get_standardized_sat(student_sat, student_act)
                    
                    # 使用改进的录取概率计算函数
                    admission_chance = calculate_admission_probability(
                        student_gpa, std_sat, std_toefl, 
                        uni_gpa_req, uni_sat_req, uni_toefl_req,
                        ranking, admission_rate
                    )
                except Exception as e:
                    admission_chance = "无法评估"
            else:
                admission_chance = "无法评估"

            # 专业匹配度
            if student_profile and 'major' in student_profile.get('preferences', {}):
                student_major = student_profile['preferences']['major']
                strong_programs = academics.get('strong_programs', [])
                
                # 检查专业匹配
                major_match = "高" if any(student_major in prog for prog in strong_programs) else "中"
            else:
                major_match = "中"

            # 添加大学信息到输出文本
            formatted_text += (
                f"### {i+1}. {uni.get('name')}\n"
                f"- **类别**: {cat_name.capitalize()}\n"
                f"- **位置**: {uni.get('location')}\n"
                f"- **规模**: {uni.get('size')}\n"
                f"- **气候**: {uni.get('climate', '未知')}\n"
                f"- **优势项目**: {', '.join(academics.get('strong_programs', []))}\n"
                f"- **学校文化**: {uni.get('culture', '未知')}\n"
                f"- **适合学生**: {', '.join(strengths_for)}\n"
                f"- **匹配标签**: {', '.join(fit_tags)}\n"
                f"- **整体匹配度**: {similarity:.1%}\n"
                f"- **专业匹配度**: {major_match}\n"
                f"- **录取概率评估**: {admission_chance}\n\n"
            )
    
    # 添加总结信息
    formatted_text += """
---

## 选校建议总结

- **冲刺校**: 建议申请1-3所，这些学校对您有一定挑战性，但您的背景也有机会被录取
- **匹配校**: 建议申请3-5所，这些学校与您的学术水平最为匹配，是您的主申请目标
- **保底校**: 建议申请2-3所，这些学校您的录取把握较大，确保有学可上

请结合您的个人意愿和实际情况，从上述大学中选择适合您的申请组合。
"""
    
    return formatted_text


def generate_report(student_profile, matched_universities_text):
    """
    使用LLM生成选校报告
    
    参数:
        student_profile: 学生档案字典
        matched_universities_text: 格式化的大学信息文本
    
    返回:
        str: 生成的报告文本
    """
    prompt = f"""
# 你是一名专业的升学顾问（College Admission Counselor），你的职责是根据学生提供的学术成绩与偏好，从给定的大学数据库中筛选出合适的院校，并为每个推荐提供清晰、理性的理由。
你不能使用、臆造或引用任何不在数据库中的大学信息。

# 硬性规则
1. **数据来源限制**：在你匹配学校的时候，你只能使用下面"匹配到的大学信息"中提供的大学数据，严禁添加或引用任何其他大学，但是你给的针对学生的个性化建议可以不在"匹配到的大学信息"里面
2. **严禁虚构**：如果某个类别大学数量不足，必须明确说明"数据库中该类别大学数量不足"
3. **唯一性**：每所大学只能出现在一个类别中（Reach/Match/Safety）
4. **严格遵守分类标准**：必须按照下面的学术标准进行分类

# 分类流程（两步法）

## 第一步：学术门槛分类（强制性）
根据学生成绩与大学录取门槛的对比进行分类：

**Reach（冲刺校）**：学生的GPA **或** 所选择的学校官方录取率应为1%-15%，
**Match（匹配校）**：学生的GPA **和** 所选择的学校官方录取率应为15%-60%，
**Safety（保底校）**：学生的GPA **和** 所选择的学校官方录取率应为61%-100%。

*特殊规则*：对于极度选拔性的大学（如常春藤盟校），默认归类为Reach，除非学生成绩异常突出

## 第二步：匹配度排序（核心逻辑）
**在每个学术类别内部，按照以下优先级对大学进行排序：**

1. **专业匹配度（最高权重）**：大学在学生意向专业方面的实力
2. **个人特质匹配**：大学文化与学生个性、特质的契合度
3. **偏好匹配**：大学与学生地理位置、规模等偏好的匹配程度

# 输入数据

## 学生背景信息
{json.dumps(student_profile, indent=2, ensure_ascii=False)}

## 匹配到的大学信息（唯一数据源）
{matched_universities_text}

# 输出要求
**严格使用以下格式输出，不要包含任何其他内容：**
告诉学生，选每个学校的具体原因，尽可能的全面
"""

    try:
        # 初始化 DeepSeek 客户端
        client = OpenAI(api_key = os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates university selection reports."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        # 返回生成的文本
        return response.choices[0].message.content

    except Exception as e:
        return f"Error connecting to DeepSeek API: {str(e)}"


def get_standardized_toefl(toefl, ielts, det):
    """
    标准化语言成绩，将IELTS和DET转换为TOEFL等效分数
    
    参数:
        toefl: TOEFL分数
        ielts: IELTS分数
        det: DET分数
    
    返回:
        int: 标准化后的TOEFL等效分数
    """
    if toefl > 0:
        return toefl
    elif ielts > 0:
        # 使用更精确的IELTS到TOEFL转换公式
        toefl_equiv = {
            9.0: 120,
            8.5: 116,
            8.0: 110,
            7.5: 100,
            7.0: 94,
            6.5: 87,
            6.0: 79,
            5.5: 71,
            5.0: 61
        }
        # 线性插值获取更精确的值
        lower = max([s for s in toefl_equiv.keys() if s <= ielts], default=5.0)
        upper = min([s for s in toefl_equiv.keys() if s >= ielts], default=9.0)
        if lower == upper:
            return toefl_equiv[lower]
        # 线性插值
        lower_score = toefl_equiv[lower]
        upper_score = toefl_equiv[upper]
        interpolated = lower_score + ((ielts - lower) / (upper - lower)) * (upper_score - lower_score)
        return min(120, round(interpolated))
    elif det > 0:
        # 使用更精确的DET到TOEFL转换
        if det >= 130:
            return 115 + min(5, det - 130)
        elif det >= 120:
            return 100 + (det - 120)
        elif det >= 110:
            return 85 + (det - 110) * 1.5
        elif det >= 100:
            return 70 + (det - 100) * 1.5
        else:
            return max(0, 40 + det * 0.3)
    return 0


def get_standardized_sat(sat, act):
    """
    标准化SAT/ACT成绩，将ACT转换为SAT等效分数
    使用College Board官方的ACT到SAT转换表作为参考
    
    参数:
        sat: SAT分数
        act: ACT分数
    
    返回:
        int: 标准化后的SAT等效分数
    """
    if sat > 0:
        return sat
    elif act > 0:
        # 使用更精确的ACT到SAT转换
        act_to_sat = {
            36: 1600,
            35: 1560,
            34: 1520,
            33: 1490,
            32: 1450,
            31: 1420,
            30: 1380,
            29: 1350,
            28: 1310,
            27: 1280,
            26: 1240,
            25: 1210,
            24: 1180,
            23: 1140,
            22: 1110,
            21: 1070,
            20: 1040,
            19: 1000,
            18: 960,
            17: 930,
            16: 890,
            15: 850,
            14: 810,
            13: 770,
            12: 730,
            11: 690,
            10: 650
        }
        if act in act_to_sat:
            return act_to_sat[act]
        else:
            # 对于ACT分数不在转换表中的情况
            if act > 36:
                return 1600
            elif act < 10:
                return 610 + (act * 40)
            else:
                # 线性插值
                lower_act = max([a for a in act_to_sat.keys() if a < act])
                upper_act = min([a for a in act_to_sat.keys() if a > act])
                lower_sat = act_to_sat[lower_act]
                upper_sat = act_to_sat[upper_act]
                return lower_sat + ((act - lower_act) / (upper_act - lower_act)) * (upper_sat - lower_sat)
    return 0


def calculate_gpa_percentile(gpa):
    """
    计算GPA的百分位排名
    基于美国大学申请常见的GPA分布
    
    参数:
        gpa: GPA成绩
    
    返回:
        float: 百分位排名 (0-100)
    """
    if gpa >= 4.0:
        return 99.9
    elif gpa >= 3.9:
        return 98.5
    elif gpa >= 3.8:
        return 95.0
    elif gpa >= 3.7:
        return 89.0
    elif gpa >= 3.6:
        return 82.0
    elif gpa >= 3.5:
        return 75.0
    elif gpa >= 3.4:
        return 67.0
    elif gpa >= 3.3:
        return 59.0
    elif gpa >= 3.2:
        return 51.0
    elif gpa >= 3.1:
        return 43.0
    elif gpa >= 3.0:
        return 35.0
    elif gpa >= 2.8:
        return 25.0
    elif gpa >= 2.5:
        return 15.0
    else:
        return 8.0


def calculate_sat_percentile(sat):
    """
    计算SAT的百分位排名
    基于最新的SAT百分位数据
    
    参数:
        sat: SAT分数
    
    返回:
        float: 百分位排名 (0-100)
    """
    if sat >= 1550:
        return 99.8
    elif sat >= 1500:
        return 98.8
    elif sat >= 1450:
        return 97.0
    elif sat >= 1400:
        return 94.0
    elif sat >= 1350:
        return 89.0
    elif sat >= 1300:
        return 83.0
    elif sat >= 1250:
        return 75.0
    elif sat >= 1200:
        return 67.0
    elif sat >= 1150:
        return 57.0
    elif sat >= 1100:
        return 46.0
    elif sat >= 1050:
        return 35.0
    elif sat >= 1000:
        return 25.0
    elif sat >= 950:
        return 17.0
    elif sat >= 900:
        return 11.0
    elif sat >= 850:
        return 7.0
    elif sat >= 800:
        return 4.0
    else:
        return 2.0


def calculate_toefl_percentile(toefl):
    """
    计算TOEFL的百分位排名
    基于国际学生TOEFL分数分布
    
    参数:
        toefl: TOEFL分数
    
    返回:
        float: 百分位排名 (0-100)
    """
    if toefl >= 115:
        return 98.5
    elif toefl >= 110:
        return 94.0
    elif toefl >= 105:
        return 87.0
    elif toefl >= 100:
        return 75.0
    elif toefl >= 95:
        return 62.0
    elif toefl >= 90:
        return 48.0
    elif toefl >= 85:
        return 34.0
    elif toefl >= 80:
        return 22.0
    elif toefl >= 75:
        return 14.0
    elif toefl >= 70:
        return 8.0
    else:
        return 4.0


def calculate_admission_probability(gpa, std_sat, std_toefl, avg_gpa, avg_sat, avg_toefl, ranking=999, admission_rate=0.5):
    """
    计算录取概率百分比，使用百分位匹配和学校特性加权
    
    参数:
        gpa: 学生GPA
        std_sat: 标准化SAT分数
        std_toefl: 标准化TOEFL分数
        avg_gpa: 大学平均GPA要求
        avg_sat: 大学平均SAT要求
        avg_toefl: 大学平均TOEFL要求
        ranking: 大学排名（越低越好）
        admission_rate: 录取率
    
    返回:
        float: 录取概率百分比 (0-100)
    """
    # 计算学生各项成绩的百分位
    student_gpa_percentile = calculate_gpa_percentile(gpa)
    student_sat_percentile = calculate_sat_percentile(std_sat)
    student_toefl_percentile = calculate_toefl_percentile(std_toefl)
    
    # 计算大学期望的百分位（基于录取要求）
    uni_gpa_percentile = calculate_gpa_percentile(avg_gpa)
    uni_sat_percentile = calculate_sat_percentile(avg_sat)
    uni_toefl_percentile = calculate_toefl_percentile(avg_toefl)
    
    # 计算百分位差异分数
    percentile_diff_scores = []
    
    # GPA百分位差异（权重30%）
    gpa_percentile_diff = student_gpa_percentile - uni_gpa_percentile
    percentile_diff_scores.append(gpa_percentile_diff * 0.3)
    
    # SAT百分位差异（权重40%）
    sat_percentile_diff = student_sat_percentile - uni_sat_percentile
    percentile_diff_scores.append(sat_percentile_diff * 0.4)
    
    # TOEFL百分位差异（权重20%）
    toefl_percentile_diff = student_toefl_percentile - uni_toefl_percentile
    percentile_diff_scores.append(toefl_percentile_diff * 0.2)
    
    # 基础分数
    base_score = sum(percentile_diff_scores)
    
    # 学校竞争力调整因子
    competitiveness_factor = 0
    
    # 根据排名调整
    if ranking <= 20:
        competitiveness_factor -= 15  # 顶级学校门槛更高
    elif ranking <= 50:
        competitiveness_factor -= 8
    elif ranking <= 100:
        competitiveness_factor -= 3
    
    # 根据录取率调整
    if admission_rate < 0.1:
        competitiveness_factor -= 12  # 录取率极低的学校
    elif admission_rate < 0.2:
        competitiveness_factor -= 8
    elif admission_rate < 0.3:
        competitiveness_factor -= 4
    elif admission_rate > 0.6:
        competitiveness_factor += 6  # 录取率高的学校更容易录取
    elif admission_rate > 0.4:
        competitiveness_factor += 3
    
    # 最终综合分数
    final_score = base_score + competitiveness_factor
    
    # 将最终分数转换为百分比概率（限制在0-100范围内）
    # 使用S型函数映射分数到概率
    probability = 50 + (50 * final_score) / (10 + abs(final_score))
    
    # 确保概率在合理范围内
    probability = max(0, min(100, probability))
    
    return probability


def generate_university_recommendations(student_profile, universities_db=None, matched_universities=None, distances=None, embed_model=None):
    """
    生成JSON格式的大学推荐结果，供小程序使用
    
    参数:
        student_profile: 学生档案字典
        universities_db: 大学数据库（可选）
        matched_universities: 已匹配的大学列表（可选）
        distances: 距离列表（可选）
        embed_model: 嵌入模型（可选）
    
    返回:
        字典: 包含推荐结果的JSON格式数据
    """
    try:
        # 如果没有提供大学数据库，则使用内置的示例数据
        if universities_db is None:
            universities_db = [
                {
                "id": 1,
                "name": "California Institute of Technology (Caltech)",
                "type": ["National University", "Research Intensive"],
                "location": "Urban (Pasadena, CA)",
                "climate": "Mild",
                "size": "Small (~1k undergrad)",
                "academics": {"strong_programs": ["Physics", "Engineering", "Computer Science"], "teaching_style": "Research-intensive, Analytical"},
                "culture": "Innovative, STEM-focused, Rigorous",
                "strengths_for": ["Students passionate about science and math", "Problem solvers"],
                "fit_tags": ["STEM", "innovative", "research", "rigorous"],
                "admission_threshold": {"gpa": 3.95, "sat": 1530, "toefl": 100}
            },
            {
                "id": 2,
                "name": "Williams College",
                "type": ["Liberal Arts College"],
                "location": "Rural (Williamstown, MA)",
                "climate": "Cold winters",
                "size": "Small (~2k undergrad)",
                "academics": {"strong_programs": ["Economics", "Mathematics", "Political Science"], "teaching_style": "Tutorial-based, Collaborative"},
                "culture": "Intellectual, Close-knit, Traditional",
                "strengths_for": ["Students who love discussion-based learning", "Liberal arts enthusiasts"],
                "fit_tags": ["liberal-arts", "collaborative", "academic", "small"],
                "admission_threshold": {"gpa": 3.9, "sat": 1450, "toefl": 100}
            },
            {
                "id": 3,
                "name": "New York University (NYU)",
                "type": ["National University", "Research Intensive"],
                "location": "Urban (New York, NY)",
                "climate": "Moderate",
                "size": "Large (~29k undergrad)",
                "academics": {"strong_programs": ["Film", "Business", "Performing Arts"], "teaching_style": "Professional, Network-driven"},
                "culture": "Dynamic, Global, Arts-focused",
                "strengths_for": ["Students interested in arts and media", "Urban learners"],
                "fit_tags": ["large", "urban", "arts", "network"],
                "admission_threshold": {"gpa": 3.5, "sat": 1370, "toefl": 90}
            },
            {
                "id": 4,
                "name": "Rice University",
                "type": ["National University", "Research Intensive"],
                "location": "Urban (Houston, TX)",
                "climate": "Warm",
                "size": "Small (~4k undergrad)",
                "academics": {"strong_programs": ["Engineering", "Biology", "Architecture"], "teaching_style": "Collaborative, Research-oriented"},
                "culture": "Tight-knit, Collegiate, Innovative",
                "strengths_for": ["Students interested in STEM", "Collaborative learners"],
                "fit_tags": ["STEM", "collaborative", "research", "small"],
                "admission_threshold": {"gpa": 3.9, "sat": 1490, "toefl": 100}
            }
        ]

        # 如果没有提供匹配结果，则需要初始化向量数据库并进行查询
        if matched_universities is None or distances is None:
            collection, embed_model = init_or_load_vector_database(universities_db)
            student_query = create_student_query(student_profile)
            print("Student Query:", student_query)

            query_embedding = create_weighted_query_embedding(student_profile, embed_model)
            # 添加调试行
            print(f"【类型检查】query_embedding 类型: {type(query_embedding)}")
            print(f"【类型检查】query_embedding 形状: {query_embedding.shape if hasattr(query_embedding, 'shape') else '无shape属性'}")
            print(f"【类型检查】query_embedding 前5个元素: {query_embedding[:5] if hasattr(query_embedding, '__getitem__') else query_embedding}")

            # 然后使用修复后的代码
            query_embedding_list = [query_embedding.tolist()]
            results = collection.query(
                query_embeddings=query_embedding_list,
                n_results=40,
                include=["metadatas", "distances"]
            )

            if not results['metadatas'] or not results['metadatas'][0]:
                return {"status": "success", "report": "未找到匹配的大学。", "simplified_results": []}

            matched_universities = results['metadatas'][0]
            distances = results['distances'][0]

        # 格式化匹配的大学信息
        matched_universities_text = format_universities_for_prompt(
            matched_universities, distances, student_profile
        )

        # 生成报告
        try:
            report = generate_report(student_profile, matched_universities_text)
        except Exception as e:
            import traceback
            traceback.print_exc()
            report = "生成报告时出现错误，请检查服务器日志。"

        # 准备简化的推荐结果
        simplified_results = [] 
        level_counts = {"Reach": 0, "Match": 0, "Safety": 0} 

        # 设置不同类别学校的最大数量限制
        max_schools = {"Reach": 3, "Match": 6, "Safety": 6}

        # 为每个匹配的大学生成推荐结果
        for i, uni in enumerate(matched_universities): 
            # 获取学生成绩
            student_gpa = float(student_profile['academics'].get('gpa', 0))
            student_sat = int(student_profile['academics'].get('sat', 0))
            student_act = int(student_profile['academics'].get('act', 0))
            student_toefl = int(student_profile['academics'].get('toefl', 0))
            student_ielts = float(student_profile['academics'].get('ielts', 0))
            student_det = int(student_profile['academics'].get('det', 0))

            # 从academics字段获取大学标化成绩范围（基于university_db.py的结构）
            academics = safe_json_parse(uni.get('academics', {}), {})
            
            # GPA要求 - 使用范围平均值
            gpa_range = academics.get("gpa_range", [3.0, 3.5])
            avg_gpa = sum(gpa_range) / len(gpa_range)
            
            # SAT要求 - 使用范围平均值
            sat_range = academics.get("sat_range", [1000, 1200])
            avg_sat = sum(sat_range) / len(sat_range)
            
            # 获取标准化成绩
            student_std_sat = get_standardized_sat(student_sat, student_act)
            student_std_toefl = get_standardized_toefl(student_toefl, student_ielts, student_det)
            
            # TOEFL要求 - 使用最低要求
            avg_toefl = academics.get("toefl_min", 80)

            # 分类 - 基于标准化后的成绩
            if student_gpa < avg_gpa - 0.3 or student_std_sat < avg_sat - 100 or student_std_toefl < avg_toefl - 5:
                level = "Reach"
            elif student_gpa > avg_gpa + 0.3 and student_std_sat > avg_sat + 100 and student_std_toefl > avg_toefl + 5:
                level = "Safety"
            else:
                level = "Match"

            # 获取大学信息
            uni_name = safe_json_parse(uni.get("name", "未知学校"))
            rag_info = {
                'name': uni_name,
                'reasoning': safe_json_parse(uni.get("reasoning", "基于您的学术背景与该校录取标准的匹配度")),
                'ranking': safe_json_parse(uni.get("ranking", {})),
                'location': safe_json_parse(uni.get("location", "")),
                'size': safe_json_parse(uni.get("size", "")),
                'academics': safe_json_parse(uni.get("academics", {})),
                'distance': distances[i] if i < len(distances) else None
            }
            
            # 根据学校类型应用不同的数量限制
            if level_counts[level] < max_schools[level]: 
                # 计算录取概率
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
                if student_profile.get('preferences', {}).get('major'):
                    student_major = student_profile['preferences']['major']
                    academics_data = rag_info.get('academics', {})
                    strong_programs = []
                    
                    # 适配不同的数据结构
                    if isinstance(academics_data, dict):
                        if 'strong_programs' in academics_data:
                            strong_programs = academics_data['strong_programs']
                        # 适配新的数据结构
                        elif 'preferences' in uni and isinstance(uni['preferences'], dict):
                            career_orientation = uni['preferences'].get('career_orientation', [])
                            if career_orientation and isinstance(career_orientation, list):
                                # 检查职业方向是否与专业相关
                                for orientation in career_orientation:
                                    if student_major.lower() in orientation.lower():
                                        reasoning_points.append(f"该校的职业导向包含您感兴趣的专业领域 ({student_major})")
                                        break
                    
                    # 检查优势项目匹配
                    if strong_programs and isinstance(strong_programs, list) and any(student_major.lower() in prog.lower() for prog in strong_programs):
                        reasoning_points.append(f"该校的优势项目包含您感兴趣的专业 ({student_major})")
                
                reasoning = "; ".join(reasoning_points) if reasoning_points else "基于您的学术背景与该校录取标准的匹配度"
                
                # 添加到结果列表
                simplified_results.append({
                    "name": uni_name,
                    "level": level,
                    "reasoning": reasoning,
                    "admission_probability": round(admission_probability, 2),  # 四舍五入到两位小数
                    "ranking": rag_info.get('ranking', {}),
                    "location": rag_info.get('location', ""),
                    "size": rag_info.get('size', ""),
                    "academics": rag_info.get('academics', {}),
                    "standardized_sat": student_std_sat
                })
                level_counts[level] += 1

        # 按录取难度和匹配度排序结果
        level_order = {"Safety": 0, "Match": 1, "Reach": 2}
        simplified_results.sort(key=lambda x: (level_order.get(x['level'], 999), -x.get('admission_probability', 0)))  # 按录取概率降序排列

        # 返回结果
        result_json = {
            "status": "success",
            "report": report,
            "simplified_results": simplified_results,
            "student_profile": student_profile
        }
        
        return result_json
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"处理过程中发生错误: {str(e)}",
            "report": "",
            "simplified_results": []
        }


# 示例大学数据
EXAMPLE_UNIVERSITIES_DB = [
    {
        "id": 1,
        "name": "Harvard University",
        "academics": {
            "gpa_range": [3.8, 4.0],
            "sat_range": [1460, 1580],
            "act_range": [33, 36],
            "toefl_min": 105,
            "ielts_min": 7.5,
            "det_min": 130
        },
        "activities": {
            "research_preference": "科研导向",
            "volunteer_preference": "社会公益",
            "internship_preference": "咨询、金融、科技公司",
            "art_preference": "古典、音乐、人文类",
            "full_time_work_preference": "学术科研",
            "honors_emphasis": "高"
        },
        "preferences": {
            "location": "大城市（Boston, MA）",
            "size": "中等（20,000）",
            "tuition": 65000,
            "teacher_student_ratio": "7:1",
            "school_atmosphere": "严谨学术型",
            "international_level": "极高",
            "career_orientation": ["科研", "深造", "非营利组织"]
        }
    },
    {
        "id": 2,
        "name": "Stanford University",
        "academics": {
            "gpa_range": [3.8, 4.0],
            "sat_range": [1450, 1570],
            "act_range": [33, 35],
            "toefl_min": 100,
            "ielts_min": 7.5,
            "det_min": 125
        },
        "activities": {
            "research_preference": "创新型科研",
            "volunteer_preference": "科技教育类志愿",
            "internship_preference": "科技创业公司",
            "art_preference": "多媒体、创意艺术",
            "full_time_work_preference": "科技研发",
            "honors_emphasis": "高"
        },
        "preferences": {
            "location": "大城市（Palo Alto, CA）",
            "size": "中等（18,000）",
            "tuition": 64000,
            "teacher_student_ratio": "5:1",
            "school_atmosphere": "自由创新",
            "international_level": "极高",
            "career_orientation": ["创业", "研发", "科研"]
        }
    },
    # 更多大学数据可以根据需要添加
]


if __name__ == "__main__":
    # 示例学生档案
    student_profile = {
        "academics": {
            "gpa": "3.8",
            "sat": "1450",
            "act": "33",
            "toefl": "105",
            "ielts": "7.5",
            "det": "130"
        },
        "activities": {
            "research_months": 12,
            "research_type": "校内科研项目",
            "volunteer_months": 6,
            "volunteer_type": "公益组织",
            "internship_months": 3,
            "internship_type": "科技公司",
            "art_months": 0,
            "art_type": "",
            "full_time_work_months": 0,
            "full_time_work_type": "",
            "honors": "数学竞赛省一等奖"
        },
        "preferences": {
            "career_interest": "做科研、进大学、企业科研部门当老师、研发人员",
            "location": "城市",
            "size": "正常（10，000+）",
            "tuition": 150000,
            "major": "计算机科学",
            "teacher_student_ratio": "更关心（师生比高）",
            "school_atmosphere": "Nerdy School",
            "international_level": "高"
        }
    }

    try:
        # 使用示例大学数据库
        universities_db = EXAMPLE_UNIVERSITIES_DB
        
        # 初始化或加载数据库
        collection, embed_model = init_or_load_vector_database(universities_db)

        # 转换学生资料为查询文本
        student_query = create_student_query(student_profile)
        print("Student Query:", student_query)

        # 编码查询并检索结果
        query_embedding = create_weighted_query_embedding(student_profile, embed_model)
        # 添加调试行
        print(f"【类型检查】query_embedding 类型: {type(query_embedding)}")
        print(f"【类型检查】query_embedding 形状: {query_embedding.shape if hasattr(query_embedding, 'shape') else '无shape属性'}")
        print(f"【类型检查】query_embedding 前5个元素: {query_embedding[:5] if hasattr(query_embedding, '__getitem__') else query_embedding}")

        # 然后使用修复后的代码
        query_embedding_list = [query_embedding.tolist()]
        results = collection.query(
            query_embeddings=query_embedding_list,
            n_results=40,
            include=["metadatas", "distances"]
        )

        matched_universities = results['metadatas'][0]
        distances = results['distances'][0]

        # 格式化大学信息
        matched_universities_text = format_universities_for_prompt(
            matched_universities, distances, student_profile
        )

        # 生成报告
        try:
            report = generate_report(student_profile, matched_universities_text)
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

        # 生成并显示返回给小程序的JSON格式推荐结果
        try:
            print("\n" + "="*50)
            print("生成返回给小程序的JSON格式推荐结果...")
            print("="*50)
            
            # 调用函数生成推荐结果
            recommendations = generate_university_recommendations(
                student_profile, matched_universities=matched_universities, 
                distances=distances, embed_model=embed_model
            )
            
            print("\n" + "="*50)
            print("推荐结果生成完成")
            print("="*50)
        except Exception as e:
            print("\n" + "="*50)
            print("生成推荐结果时出错:")
            print("Exception:", str(e))
            import traceback
            traceback.print_exc()
            print("="*50)
    except Exception as e:
        print(f"运行示例时出错: {str(e)}")
        import traceback
        traceback.print_exc()
