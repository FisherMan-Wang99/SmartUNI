import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import numpy as np
from openai import OpenAI

def create_weighted_query_embedding(profile, embed_model):
    weights = {
        "interests": 1.0,
        "academics": 3.0,
        "background": 5.0,
        "personality": 1.0,
        "preferences": 1.0
    }

    embeddings = []
    total_weight = 0

    # 1. 专业兴趣
    interests = profile.get("interests")
    if interests:
        interest_text = f"Interested in {', '.join(interests)}"
        interest_emb = embed_model.encode(interest_text)
        embeddings.append(weights["interests"] * interest_emb)
        total_weight += weights["interests"]

    # 2. 学术背景
    academics = profile.get("academics", {})
    academic_text = (
        f"GPA {academics.get('gpa')}, "
        f"SAT {academics.get('sat')}, "
        f"TOEFL {academics.get('toefl')}"
    )
    academic_emb = embed_model.encode(academic_text)
    embeddings.append(weights["academics"] * academic_emb)
    total_weight += weights["academics"]

    # 3. 个人背景（科研、实习、活动）
    background = profile.get("background", {})
    bg_parts = []
    if background.get("research"):
        bg_parts.append(f"Research experience: {background['research']}")
    if background.get("internship"):
        bg_parts.append(f"Internship: {background['internship']}")
    if background.get("extracurricular"):
        bg_parts.append("Extracurriculars: " + ", ".join(background["extracurricular"]))
    if bg_parts:
        bg_text = " | ".join(bg_parts)
        bg_emb = embed_model.encode(bg_text)
        embeddings.append(weights["background"] * bg_emb)
        total_weight += weights["background"]

    # 4. 个性
    personality = profile.get("personality", {})
    p_parts = []
    if personality.get("type"):
        p_parts.append(f"Personality type: {personality['type']}")
    if personality.get("traits"):
        p_parts.append("Traits: " + ", ".join(personality["traits"]))
    if p_parts:
        p_text = " | ".join(p_parts)
        p_emb = embed_model.encode(p_text)
        embeddings.append(weights["personality"] * p_emb)
        total_weight += weights["personality"]

    # 5. 偏好（地点、规模、气候、专业、教学风格等）
    preferences = profile.get("preferences", {})
    pref_parts = []
    for key, value in preferences.items():
        pref_parts.append(f"{key.capitalize()}: {value}")
    if pref_parts:
        pref_text = " | ".join(pref_parts)
        pref_emb = embed_model.encode(pref_text)
        embeddings.append(weights["preferences"] * pref_emb)
        total_weight += weights["preferences"]

    # ⚖️ 加权平均
    query_embedding = np.sum(embeddings, axis=0) / total_weight

    return query_embedding


# used to strictly filter students with specific climate preferences
def filter_by_climate(universities, student_profile):
    required_climate = student_profile["preferences"]["climate"].lower()
    if required_climate == "none":
        return universities  # 如果用户没要求，就不强制过滤
    
    filtered = [
        uni for uni in universities
        if "climate" in uni and uni["climate"].lower() == required_climate
    ]
    return filtered

# called within def format_universities_for_prompt()
def classify_schools_strict(student, universities):
    reach, match, safety = [], [], []

    gpa = student["academics"]["gpa"]
    sat = student["academics"]["sat"]
    toefl = student["academics"]["toefl"]

    #print("universities:",universities)

    for uni in universities:
        # Convert JSON string to dict if necessary
        threshold = uni.get("admission_threshold", {})
        if isinstance(threshold, str):
            threshold = json.loads(threshold)

        gpa_req = threshold.get("gpa", 0)
        sat_req = threshold.get("sat", 0)
        toefl_req = threshold.get("toefl", 0)

        # Non-overlapping strict logic:
        if ((gpa_req - 0.3 <= gpa < gpa_req) 
            or (toefl_req - 5 <= toefl < toefl_req) 
            or (sat_req - 50 <= sat < sat_req)) and len(reach) <= 3:
            reach.append(uni)
            

        elif gpa >= gpa_req and sat >= sat_req and toefl >= toefl_req:
            # Safety only if student clearly exceeds threshold
            if gpa > gpa_req + 0.2 and sat > sat_req + 30 and toefl > toefl_req + 5 and len(safety) <= 3:
                safety.append(uni)
                
            elif len(match) <= 3:
                match.append(uni)
                

    #print("reach:",reach,"match:",match,"safety:",safety)
    return {
        "reach": reach[:3],
        "match": match[:3],
        "safety": safety[:3]
    }

# Convert list/dict fields to JSON strings so Chroma accepts them
def flatten_metadata(uni):
    meta = {}
    for k, v in uni.items():
        if isinstance(v, (list, dict)):
            meta[k] = json.dumps(v)   # store safely as JSON string
        else:
            meta[k] = v
    return meta

# Initialize or load vector database
def init_or_load_vector_database(universities_list, collection_name="universities", persist_directory="./university_db"):
    # Use ChromaDB Client
    #client = chromadb.Client()
    client = chromadb.PersistentClient(path = persist_directory)

    try:
        # Try to get an existing collection
        collection = client.get_collection(name=collection_name)
        print("Loading existing university database...")
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        # If not exists, create new collection and add data
        print("Creating new university database and vectorizing...")
        collection = client.create_collection(name=collection_name)

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        for uni in universities_list:
            text_to_embed = f"{uni['name']}. Known for: {', '.join(uni['academics']['strong_programs'])}. Culture: {uni['culture']}. For students who: {', '.join(uni['strengths_for'])}. Tags: {', '.join(uni['fit_tags'])}"

            documents.append(text_to_embed)
            # Convert metadata to JSON string for compatibility
            #metadatas.append({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in uni.items()})
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

# Convert student profile into query text
def create_student_query(profile):
    query_parts = []

    ac = profile['academics']
    query_parts.append(f"Academics: GPA {ac['gpa']}, SAT {ac['sat']}, TOEFL {ac['toefl']}")

    bg = profile['background']
    query_parts.append(f"Background: {bg['research']}. {bg['internship']}. Activities: {', '.join(bg['extracurricular'])}")

    pref = profile['preferences']
    query_parts.append(f"Preferences: {pref['location']} location, {pref['size']} size, {pref['climate']} climate. Wants to study {pref['major']}. Prefers {pref['teaching_style']} teaching.")

    pers = profile['personality']
    query_parts.append(f"Personality: {pers['type']}. Traits: {', '.join(pers['traits'])}")

    return " ".join(query_parts)

# Format matched universities with strict categories
def format_universities_for_prompt(matched_universities, distances, student_profile=None):
    # First classify all matched universities
    categories = classify_schools_strict(student_profile, matched_universities)
    
    #print("categories:",categories)
    formatted_text = ""
    for cat_name, uni_list in categories.items():
        for i, uni in enumerate(uni_list):
            # find index in matched_universities to get similarity
            idx = next((j for j, u in enumerate(matched_universities) if u['id'] == uni['id']), None)
            similarity = 1 - distances[idx] if idx is not None else 0

            academics = json.loads(uni.get('academics', '{}'))
            strengths_for = json.loads(uni.get('strengths_for', '[]'))
            fit_tags = json.loads(uni.get('fit_tags', '[]'))

            formatted_text += (
                f"Name: {uni.get('name')}\n"
                f"Category: {cat_name.capitalize()}\n"   
                f"Location: {uni.get('location')}\n"
                f"Size: {uni.get('size')}\n"
                f"Climate: {uni.get('climate')}\n"
                f"Strong programs: {', '.join(academics.get('strong_programs', []))}\n"
                f"Culture: {uni.get('culture')}\n"
                f"Strengths for students: {', '.join(strengths_for)}\n"
                f"Tags: {', '.join(fit_tags)}\n"
                f"Similarity: {similarity:.3f}\n\n"
            )
    return formatted_text


# Generate report using LLM
from openai import OpenAI
import json

def generate_report(student_profile, matched_universities_text):
    prompt = f"""
# 🎓 University Selection Report Generator

## 🔐 Absolute Instructions & Hard Constraints
1.  **Data Source Limitation**: You MUST ONLY use the universities provided in the **"Matched Universities Information"** section below. This is your sole source of data.
2.  **Zero Hallucination Tolerance**: It is strictly forbidden to invent, include, or reference any university not present in the provided list. If the list has fewer than 3 schools for a category, you must explicitly state: **"Not enough universities available in the database for this category."**
3.  **Uniqueness**: Each university can appear in **one and only one category** (Reach, Match, or Safety). No overlaps are permitted.
4.  **Mandatory Pre-Filtering**: You must FIRST filter schools based on academic thresholds before considering fit.

## 📊 Classification Rules: A Two-Step Process

### Step 1: Academic Categorization (Non-Negotiable)
Categorize each university by directly comparing the student's scores to the university's `admission_threshold`:
-   **Reach**: The student's GPA **OR** SAT score is **below** the university's stated threshold.
-   **Match**: The student's GPA **AND** SAT score are **at or above** the university's stated threshold.
-   **Safety**: The student's GPA **AND** SAT score are **significantly above** the university's threshold (e.g., GPA +0.3, SAT +100 points).
-   **Elite Exception**: Ultra-selective institutions (e.g., Ivy League, Stanford, MIT) are classified as **Reach** by default, unless the student's scores are exceptional (e.g., above the 90th percentile).

### Step 2: Fit-Based Prioritization (**Core Rule**)
**Within each academic category (Reach, Match, Safety), you MUST prioritize and rank schools based on their overall fit with the student's profile.** Use the following order of priority:
1. First consider: **Major Program Strength (Highest Weight)**: Does the university have a top program (`strong_programs`) in the student's intended major (`{student_profile['preferences']['major']}`)? This is the single most important factor.
2. Second consider: **Culture & Personality Fit**: Does the university's culture (`culture`) and strengths (`strengths_for`) align with the student's personality (`personality`), traits (`traits`), and extracurricular background (`extracurricular`)? 
3. Last consider: **Preference Alignment**: How well does the university match the student's stated preferences (`preferences`) for location, size, climate, and teaching style?
**The best-fitting school in each category must be listed first.**

---

## Student Profile
{json.dumps(student_profile, indent=2, ensure_ascii=False)}

## Matched Universities Information (Database — ONLY use these schools)
{matched_universities_text}

### 5. Personalized Recommendations  
(Application strategy, essays, balancing list, etc.)

## Style & Output
- Writing style: **professional, encouraging, conversational**  
- Output format: **Markdown**  
- ❌ IMPORTANT: If a school is not listed in the "Matched Universities Information," do NOT include it under any circumstances.
"""

    try:
        # 初始化 DeepSeek 客户端
        client = OpenAI(api_key="sk-b4eb51f2fa7346aea731e120dd77da54", base_url="https://api.deepseek.com")
        
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


if __name__ == "__main__":
    # Example student profile
    student_profile = {
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


    # Example universities database
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
},
{
    "id": 5,
    "name": "Georgetown University",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Washington, D.C.)",
    "climate": "Moderate",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["International Relations", "Political Science", "Business"], "teaching_style": "Discussion-based, Professional"},
    "culture": "Political, Prestigious, Global",
    "strengths_for": ["Future diplomats and politicians", "Students passionate about policy"],
    "fit_tags": ["prestigious", "global", "politics", "professional"],
    "admission_threshold": {"gpa": 3.8, "sat": 1410, "toefl": 95}
},
{
    "id": 6,
    "name": "Boston College",
    "type": ["National University", "Research"],
    "location": "Suburban (Chestnut Hill, MA)",
    "climate": "Cold winters",
    "size": "Medium (~9k undergrad)",
    "academics": {"strong_programs": ["Economics", "Business", "Education"], "teaching_style": "Collaborative, Jesuit tradition"},
    "culture": "Collegiate, Community-oriented, Faith-inspired",
    "strengths_for": ["Students seeking a Jesuit education", "Collaborative learners"],
    "fit_tags": ["collaborative", "community", "faith", "business"],
    "admission_threshold": {"gpa": 3.7, "sat": 1340, "toefl": 90}
},
{
    "id": 7,
    "name": "University of Wisconsin-Madison",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Madison, WI)",
    "climate": "Cold winters",
    "size": "Large (~33k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Agricultural Sciences", "Political Science"], "teaching_style": "Research-oriented, Practical"},
    "culture": "Spirited, Collegiate, Activist",
    "strengths_for": ["Students seeking large campus life", "STEM and social sciences"],
    "fit_tags": ["large", "research", "spirited", "public"],
    "admission_threshold": {"gpa": 3.6, "sat": 1260, "toefl": 85}
},
{
    "id": 8,
    "name": "University of Florida",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Gainesville, FL)",
    "climate": "Warm",
    "size": "Large (~34k undergrad)",
    "academics": {"strong_programs": ["Biology", "Engineering", "Business"], "teaching_style": "Collaborative, Research-focused"},
    "culture": "Spirited, Collegiate, Competitive",
    "strengths_for": ["Students seeking research opportunities", "Large public university environment"],
    "fit_tags": ["large", "public", "research", "collaborative"],
    "admission_threshold": {"gpa": 3.6, "sat": 1280, "toefl": 85}
},
{
    "id": 9,
    "name": "Arizona State University",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Tempe, AZ)",
    "climate": "Warm",
    "size": "Large (~40k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Computer Science"], "teaching_style": "Collaborative, Practical"},
    "culture": "Innovative, Socially Active, Dynamic",
    "strengths_for": ["Students seeking large campus opportunities", "Tech and business students"],
    "fit_tags": ["large", "public", "collaborative", "tech"],
    "admission_threshold": {"gpa": 3.4, "sat": 1200, "toefl": 80}
},
{
    "id": 10,
    "name": "University of Arizona",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Tucson, AZ)",
    "climate": "Warm",
    "size": "Large (~36k undergrad)",
    "academics": {"strong_programs": ["Astronomy", "Engineering", "Business"], "teaching_style": "Research-oriented, Collaborative"},
    "culture": "Spirited, Collegiate, Research-driven",
    "strengths_for": ["Students interested in STEM research", "Large campus learners"],
    "fit_tags": ["large", "research", "public", "STEM"],
    "admission_threshold": {"gpa": 3.3, "sat": 1180, "toefl": 75}
},
{
    "id": 11,
    "name": "University of Colorado Boulder",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Boulder, CO)",
    "climate": "Mild",
    "size": "Large (~30k undergrad)",
    "academics": {"strong_programs": ["Environmental Science", "Engineering", "Business"], "teaching_style": "Collaborative, Hands-on"},
    "culture": "Active, Collegiate, Outdoorsy",
    "strengths_for": ["Students who love outdoor activities", "STEM and business learners"],
    "fit_tags": ["large", "public", "collaborative", "active"],
    "admission_threshold": {"gpa": 3.4, "sat": 1220, "toefl": 80}
},
{
    "id": 12,
    "name": "Indiana University Bloomington",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Bloomington, IN)",
    "climate": "Moderate",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Business", "Music", "Economics"], "teaching_style": "Collaborative, Student-focused"},
    "culture": "Collegiate, Spirited, Community-oriented",
    "strengths_for": ["Students seeking business or music programs", "Large campus learners"],
    "fit_tags": ["large", "public", "collaborative", "community"],
    "admission_threshold": {"gpa": 3.4, "sat": 1210, "toefl": 80}
},
{
    "id": 13,
    "name": "University of Minnesota, Twin Cities",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Minneapolis, MN)",
    "climate": "Cold winters",
    "size": "Large (~30k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Computer Science"], "teaching_style": "Collaborative, Research-oriented"},
    "culture": "Diverse, Academic, Research-driven",
    "strengths_for": ["STEM and business students", "Research enthusiasts"],
    "fit_tags": ["large", "research", "public", "collaborative"],
    "admission_threshold": {"gpa": 3.5, "sat": 1250, "toefl": 85}
},
{
    "id": 14,
    "name": "University of Oregon",
    "type": ["Public University", "Research"],
    "location": "Urban (Eugene, OR)",
    "climate": "Mild",
    "size": "Large (~23k undergrad)",
    "academics": {"strong_programs": ["Business", "Environmental Science", "Journalism"], "teaching_style": "Collaborative, Hands-on"},
    "culture": "Active, Outdoorsy, Collegiate",
    "strengths_for": ["Students who love outdoors and sustainability", "Collaborative learners"],
    "fit_tags": ["large", "public", "active", "collaborative"],
    "admission_threshold": {"gpa": 3.3, "sat": 1170, "toefl": 75}
},
{
    "id": 15,
    "name": "Temple University",
    "type": ["Public University", "Research"],
    "location": "Urban (Philadelphia, PA)",
    "climate": "Moderate",
    "size": "Large (~27k undergrad)",
    "academics": {"strong_programs": ["Business", "Media", "Education"], "teaching_style": "Practical, Collaborative"},
    "culture": "Urban, Diverse, Professional",
    "strengths_for": ["Students seeking urban exposure", "Practical learners"],
    "fit_tags": ["large", "urban", "diverse", "collaborative"],
    "admission_threshold": {"gpa": 3.2, "sat": 1150, "toefl": 70}
},
{
    "id": 16,
    "name": "San Diego State University",
    "type": ["Public University", "Research"],
    "location": "Urban (San Diego, CA)",
    "climate": "Warm",
    "size": "Large (~33k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Communications"], "teaching_style": "Collaborative, Practical"},
    "culture": "Active, Social, Urban",
    "strengths_for": ["Students seeking sunny campus life", "Practical learners"],
    "fit_tags": ["large", "urban", "public", "collaborative"],
    "admission_threshold": {"gpa": 3.3, "sat": 1180, "toefl": 75}
},
{
    "id": 17,
    "name": "University of Alabama",
    "type": ["Public University", "Research"],
    "location": "Suburban (Tuscaloosa, AL)",
    "climate": "Warm",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Communications"], "teaching_style": "Collaborative, Practical"},
    "culture": "Spirited, Collegiate, Social",
    "strengths_for": ["Students who value sports culture", "Practical learners"],
    "fit_tags": ["large", "public", "collaborative", "social"],
    "admission_threshold": {"gpa": 3.2, "sat": 1120, "toefl": 70}
},
{
    "id": 18,
    "name": "Portland State University",
    "type": ["Public University", "Research"],
    "location": "Urban (Portland, OR)",
    "climate": "Mild",
    "size": "Medium (~27k undergrad)",
    "academics": {"strong_programs": ["Business", "Urban Planning", "Engineering"], "teaching_style": "Collaborative, Applied"},
    "culture": "Urban, Diverse, Socially Active",
    "strengths_for": ["Students who want applied experience", "Urban learners"],
    "fit_tags": ["medium", "urban", "collaborative", "applied"],
    "admission_threshold": {"gpa": 3.1, "sat": 1100, "toefl": 70}
},
{
    "id": 19,
    "name": "Boise State University",
    "type": ["Public University", "Research"],
    "location": "Urban (Boise, ID)",
    "climate": "Mild",
    "size": "Medium (~22k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Health Sciences"], "teaching_style": "Practical, Collaborative"},
    "culture": "Active, Community-focused, Collegiate",
    "strengths_for": ["Students seeking affordable education", "Collaborative learners"],
    "fit_tags": ["medium", "public", "collaborative", "practical"],
    "admission_threshold": {"gpa": 3.0, "sat": 1100, "toefl": 70}
},
{
    "id": 20,
    "name": "Western Washington University",
    "type": ["Public University", "Research"],
    "location": "Suburban (Bellingham, WA)",
    "climate": "Mild",
    "size": "Medium (~16k undergrad)",
    "academics": {"strong_programs": ["Environmental Science", "Education", "Business"], "teaching_style": "Collaborative, Student-centered"},
    "culture": "Outdoorsy, Community-focused, Collaborative",
    "strengths_for": ["Students interested in nature and sustainability", "Student-centered learners"],
    "fit_tags": ["medium", "public", "collaborative", "outdoorsy"],
    "admission_threshold": {"gpa": 2.9, "sat": 1100, "toefl": 70}
},
{
    "id": 21,
    "name": "Stanford University",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Stanford, CA)",
    "climate": "Mild",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Computer Science", "Engineering", "Business"], "teaching_style": "Innovative, Entrepreneurial"},
    "culture": "Entrepreneurial, Competitive, Sunny",
    "strengths_for": ["Innovators and future entrepreneurs", "STEM leaders"],
    "fit_tags": ["innovative", "STEM", "entrepreneurial", "prestigious"],
    "admission_threshold": {"gpa": 3.95, "sat": 1500, "toefl": 100}
},
{
    "id": 22,
    "name": "Massachusetts Institute of Technology (MIT)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Cambridge, MA)",
    "climate": "Cold winters",
    "size": "Medium (~4.5k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Computer Science", "Physics"], "teaching_style": "Problem-solving, Rigorous"},
    "culture": "Intense, Collaborative, Nerdy",
    "strengths_for": ["Problem solvers and builders", "Math and science prodigies"],
    "fit_tags": ["STEM", "rigorous", "collaborative", "innovative"],
    "admission_threshold": {"gpa": 3.9, "sat": 1540, "toefl": 100}
},
{
    "id": 23,
    "name": "University of Chicago",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Chicago, IL)",
    "climate": "Cold winters",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Economics", "Political Science", "Biology"], "teaching_style": "Theoretical, Discussion-based"},
    "culture": "Intellectual, Rigorous, Self-motivated",
    "strengths_for": ["Debaters and theoretical thinkers", "Students who love core curricula"],
    "fit_tags": ["academic", "rigorous", "theoretical", "urban"],
    "admission_threshold": {"gpa": 3.9, "sat": 1530, "toefl": 100}
},
{
    "id": 24,
    "name": "Northwestern University",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Evanston, IL)",
    "climate": "Cold winters",
    "size": "Medium (~8k undergrad)",
    "academics": {"strong_programs": ["Journalism", "Engineering", "Business"], "teaching_style": "Balanced, Pre-professional"},
    "culture": "Collaborative, Pre-professional, Spirited",
    "strengths_for": ["Students who want strong academics and Big Ten sports", "Future journalists"],
    "fit_tags": ["balanced", "pre-professional", "collaborative", "journalism"],
    "admission_threshold": {"gpa": 3.9, "sat": 1490, "toefl": 100}
},
{
    "id": 25,
    "name": "Johns Hopkins University",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Baltimore, MD)",
    "climate": "Moderate",
    "size": "Medium (~6k undergrad)",
    "academics": {"strong_programs": ["Biomedical Engineering", "Public Health", "International Studies"], "teaching_style": "Research-intensive, Pre-med focused"},
    "culture": "Pre-med, Competitive, Research-driven",
    "strengths_for": ["Aspiring doctors and researchers", "Globally-minded students"],
    "fit_tags": ["research", "pre-med", "STEM", "global"],
    "admission_threshold": {"gpa": 3.9, "sat": 1510, "toefl": 100}
},
{
    "id": 26,
    "name": "Duke University",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Durham, NC)",
    "climate": "Mild",
    "size": "Medium (~6.5k undergrad)",
    "academics": {"strong_programs": ["Economics", "Public Policy", "Biology"], "teaching_style": "Collaborative, Interdisciplinary"},
    "culture": "Spirited, Collaborative, Pre-professional",
    "strengths_for": ["Students who want top academics and fierce school spirit", "Future leaders"],
    "fit_tags": ["spirited", "collaborative", "pre-professional", "balanced"],
    "admission_threshold": {"gpa": 3.9, "sat": 1520, "toefl": 100}
},
{
    "id": 27,
    "name": "Brown University",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Providence, RI)",
    "climate": "Cold winters",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Computer Science", "Economics", "Biology"], "teaching_style": "Student-designed, Open Curriculum"},
    "culture": "Creative, Non-conformist, Independent",
    "strengths_for": ["Independent learners who hate requirements", "Artists and innovators"],
    "fit_tags": ["independent", "creative", "open-curriculum", "non-conformist"],
    "admission_threshold": {"gpa": 3.9, "sat": 1500, "toefl": 100}
},
{
    "id": 28,
    "name": "Vanderbilt University",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Nashville, TN)",
    "climate": "Mild",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Economics", "Human Development", "Engineering"], "teaching_style": "Collaborative, Student-centered"},
    "culture": "Friendly, Collaborative, Southern",
    "strengths_for": ["Students seeking top academics with a friendly vibe", "Collaborative learners"],
    "fit_tags": ["collaborative", "friendly", "student-centered", "southern"],
    "admission_threshold": {"gpa": 3.8, "sat": 1500, "toefl": 100}
},
{
    "id": 29,
    "name": "Washington University in St. Louis",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (St. Louis, MO)",
    "climate": "Moderate",
    "size": "Medium (~7.5k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Biology"], "teaching_style": "Collaborative, Pre-med focused"},
    "culture": "Collaborative, Pre-professional, Midwestern",
    "strengths_for": ["Pre-med students", "Those seeking a collaborative top-tier school"],
    "fit_tags": ["collaborative", "pre-med", "pre-professional", "midwestern"],
    "admission_threshold": {"gpa": 3.9, "sat": 1520, "toefl": 100}
},
{
    "id": 30,
    "name": "University of Southern California (USC)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Los Angeles, CA)",
    "climate": "Warm",
    "size": "Large (~20k undergrad)",
    "academics": {"strong_programs": ["Film", "Business", "Engineering"], "teaching_style": "Professional, Network-driven"},
    "culture": "Spirited, Trojan Family, Professional",
    "strengths_for": ["Students seeking strong alumni networks", "Aspiring entertainers and entrepreneurs"],
    "fit_tags": ["network", "professional", "spirited", "arts"],
    "admission_threshold": {"gpa": 3.8, "sat": 1440, "toefl": 100}
},
{
    "id": 31,
    "name": "University of Michigan, Ann Arbor",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Ann Arbor, MI)",
    "climate": "Cold winters",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Political Science"], "teaching_style": "Rigorous, Spirited"},
    "culture": "Spirited, Academic, Collaborative",
    "strengths_for": ["Students who want the best of public academics and sports", "Leaders in many fields"],
    "fit_tags": ["spirited", "public", "rigorous", "collaborative"],
    "admission_threshold": {"gpa": 3.8, "sat": 1430, "toefl": 95}
},
{
    "id": 32,
    "name": "University of Virginia (UVA)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Charlottesville, VA)",
    "climate": "Mild",
    "size": "Large (~17k undergrad)",
    "academics": {"strong_programs": ["Business", "Economics", "History"], "teaching_style": "Traditional, Discussion-based"},
    "culture": "Pre-professional, Traditional, Honor-bound",
    "strengths_for": ["Students who appreciate tradition and honor codes", "Future leaders and professionals"],
    "fit_tags": ["traditional", "pre-professional", "honor-code", "public"],
    "admission_threshold": {"gpa": 3.9, "sat": 1410, "toefl": 90}
},
{
    "id": 33,
    "name": "University of North Carolina at Chapel Hill (UNC)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Chapel Hill, NC)",
    "climate": "Mild",
    "size": "Large (~19k undergrad)",
    "academics": {"strong_programs": ["Media & Journalism", "Business", "Public Health"], "teaching_style": "Collaborative, Student-focused"},
    "culture": "Spirited, Collaborative, Tar Heel Pride",
    "strengths_for": ["Students seeking top-tier public education with spirit", "Future journalists and business people"],
    "fit_tags": ["spirited", "public", "collaborative", "journalism"],
    "admission_threshold": {"gpa": 3.8, "sat": 1380, "toefl": 90}
},
{
    "id": 34,
    "name": "University of California, Berkeley (UC Berkeley)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Berkeley, CA)",
    "climate": "Mild",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Computer Science", "Economics"], "teaching_style": "Rigorous, Competitive"},
    "culture": "Activist, Intellectual, Competitive",
    "strengths_for": ["Self-motivated and competitive students", "Activists and innovators"],
    "fit_tags": ["competitive", "activist", "STEM", "rigorous"],
    "admission_threshold": {"gpa": 3.9, "sat": 1450, "toefl": 90}
},
{
    "id": 35,
    "name": "University of California, Los Angeles (UCLA)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Los Angeles, CA)",
    "climate": "Warm",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Psychology", "Economics", "Biology"], "teaching_style": "Collaborative, Research-oriented"},
    "culture": "Spirited, Diverse, Sunny",
    "strengths_for": ["Well-rounded students who love sun and spirit", "Aspiring researchers"],
    "fit_tags": ["spirited", "diverse", "sunny", "collaborative"],
    "admission_threshold": {"gpa": 3.9, "sat": 1400, "toefl": 90}
},
{
    "id": 36,
    "name": "Carnegie Mellon University (CMU)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Pittsburgh, PA)",
    "climate": "Cold winters",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Computer Science", "Engineering", "Drama"], "teaching_style": "Intense, Project-based"},
    "culture": "Intense, Work-hard-play-hard, Nerdy",
    "strengths_for": ["Students who live to code and build", "Unique blend of tech and arts"],
    "fit_tags": ["STEM", "intense", "project-based", "nerdy"],
    "admission_threshold": {"gpa": 3.8, "sat": 1510, "toefl": 100}
},
{
    "id": 37,
    "name": "Emory University",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Atlanta, GA)",
    "climate": "Mild",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Business", "Biology", "Political Science"], "teaching_style": "Collaborative, Pre-med focused"},
    "culture": "Pre-professional, Collaborative, Southern",
    "strengths_for": ["Pre-med and business students", "Those seeking a top school in the South"],
    "fit_tags": ["pre-professional", "collaborative", "pre-med", "southern"],
    "admission_threshold": {"gpa": 3.8, "sat": 1480, "toefl": 100}
},
{
    "id": 38,
    "name": "University of Notre Dame",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Notre Dame, IN)",
    "climate": "Cold winters",
    "size": "Medium (~8.5k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Theology"], "teaching_style": "Traditional, Faith-based"},
    "culture": "Spirited, Faith-based, Community-oriented",
    "strengths_for": ["Students seeking a faith-based top education", "Future business leaders"],
    "fit_tags": ["faith", "spirited", "traditional", "community"],
    "admission_threshold": {"gpa": 3.9, "sat": 1470, "toefl": 100}
},
{
    "id": 39,
    "name": "University of California, San Diego (UCSD)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (La Jolla, CA)",
    "climate": "Warm",
    "size": "Large (~33k undergrad)",
    "academics": {"strong_programs": ["Biology", "Engineering", "Cognitive Science"], "teaching_style": "Research-oriented, STEM-focused"},
    "culture": "STEM-focused, Collaborative, Beachy",
    "strengths_for": ["STEM students who love the beach", "Aspiring researchers"],
    "fit_tags": ["STEM", "research", "beachy", "collaborative"],
    "admission_threshold": {"gpa": 3.8, "sat": 1360, "toefl": 90}
},
{
    "id": 40,
    "name": "Boston University (BU)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Boston, MA)",
    "climate": "Cold winters",
    "size": "Large (~18k undergrad)",
    "academics": {"strong_programs": ["Business", "Communications", "Engineering"], "teaching_style": "Professional, Practical"},
    "culture": "Pre-professional, Urban, Diverse",
    "strengths_for": ["Students who want a city experience", "Career-focused learners"],
    "fit_tags": ["urban", "pre-professional", "diverse", "practical"],
    "admission_threshold": {"gpa": 3.7, "sat": 1410, "toefl": 90}
},
{
    "id": 51,
    "name": "University of Illinois at Urbana-Champaign (UIUC)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Champaign, IL)",
    "climate": "Cold winters",
    "size": "Large (~34k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Computer Science", "Business"], "teaching_style": "Rigorous, STEM-focused"},
    "culture": "Spirited, Nerdy, Collaborative",
    "strengths_for": ["Top-tier STEM students", "Those who love big school spirit"],
    "fit_tags": ["STEM", "spirited", "rigorous", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1370, "toefl": 90}
},
{
    "id": 52,
    "name": "University of Texas at Austin (UT Austin)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Austin, TX)",
    "climate": "Warm",
    "size": "Large (~41k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Computer Science"], "teaching_style": "Competitive, Pre-professional"},
    "culture": "Spirited, Weird, Proud",
    "strengths_for": ["Students who want a top education in a cool city", "Future business and tech leaders"],
    "fit_tags": ["spirited", "pre-professional", "competitive", "urban"],
    "admission_threshold": {"gpa": 3.8, "sat": 1350, "toefl": 90}
},
{
    "id": 53,
    "name": "University of Washington, Seattle (UW)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Seattle, WA)",
    "climate": "Mild",
    "size": "Large (~32k undergrad)",
    "academics": {"strong_programs": ["Computer Science", "Engineering", "Business"], "teaching_style": "Collaborative, Research-oriented"},
    "culture": "Nerdy, Collaborative, Outdoorsy",
    "strengths_for": ["STEM students who love the outdoors", "Collaborative learners"],
    "fit_tags": ["STEM", "collaborative", "outdoorsy", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1340, "toefl": 90}
},
{
    "id": 54,
    "name": "University of Georgia (UGA)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Athens, GA)",
    "climate": "Mild",
    "size": "Large (~30k undergrad)",
    "academics": {"strong_programs": ["Business", "Journalism", "Biology"], "teaching_style": "Collaborative, Spirited"},
    "culture": "Spirited, Greek-life, Southern",
    "strengths_for": ["Students who love football and strong academics", "Future business leaders"],
    "fit_tags": ["spirited", "public", "collaborative", "southern"],
    "admission_threshold": {"gpa": 3.9, "sat": 1320, "toefl": 80}
},
{
    "id": 55,
    "name": "Pennsylvania State University (Penn State)",
    "type": ["Public University", "Research Intensive"],
    "location": "Rural (State College, PA)",
    "climate": "Cold winters",
    "size": "Large (~41k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Communications"], "teaching_style": "Spirited, Pre-professional"},
    "culture": "Spirited, Alumni Network, Traditional",
    "strengths_for": ["Students who want the ultimate big college experience", "Those valuing a powerful alumni network"],
    "fit_tags": ["spirited", "network", "traditional", "public"],
    "admission_threshold": {"gpa": 3.6, "sat": 1270, "toefl": 80}
},
{
    "id": 56,
    "name": "Ohio State University (OSU)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Columbus, OH)",
    "climate": "Cold winters",
    "size": "Large (~46k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Psychology"], "teaching_style": "Spirited, Research-oriented"},
    "culture": "Spirited, Massive, Collaborative",
    "strengths_for": ["Students who want endless opportunities", "Those who love school spirit"],
    "fit_tags": ["spirited", "massive", "collaborative", "public"],
    "admission_threshold": {"gpa": 3.8, "sat": 1320, "toefl": 80}
},
{
    "id": 57,
    "name": "Purdue University",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (West Lafayette, IN)",
    "climate": "Cold winters",
    "size": "Large (~34k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Agriculture"], "teaching_style": "Rigorous, STEM-focused"},
    "culture": "Nerdy, Collaborative, Spirited",
    "strengths_for": ["Future engineers and scientists", "Students who value practicality"],
    "fit_tags": ["STEM", "rigorous", "nerdy", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1310, "toefl": 80}
},
{
    "id": 58,
    "name": "University of California, Davis (UC Davis)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Davis, CA)",
    "climate": "Mild",
    "size": "Large (~31k undergrad)",
    "academics": {"strong_programs": ["Agricultural Sciences", "Environmental Science", "Biology"], "teaching_style": "Collaborative, Research-oriented"},
    "culture": "Outdoorsy, Bike-friendly, Collaborative",
    "strengths_for": ["Environmentalists and animal lovers", "Students who prefer a collaborative vibe"],
    "fit_tags": ["outdoorsy", "environmental", "collaborative", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1280, "toefl": 80}
},
{
    "id": 59,
    "name": "University of California, Irvine (UC Irvine)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Irvine, CA)",
    "climate": "Warm",
    "size": "Large (~30k undergrad)",
    "academics": {"strong_programs": ["Criminology", "Biology", "Computer Science"], "teaching_style": "Research-oriented, Collaborative"},
    "culture": "Diverse, Studious, Suburban",
    "strengths_for": ["Pre-med and STEM students", "Those seeking a studious environment near the beach"],
    "fit_tags": ["studious", "diverse", "STEM", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1270, "toefl": 80}
},
{
    "id": 60,
    "name": "University of Massachusetts Amherst (UMass Amherst)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Amherst, MA)",
    "climate": "Cold winters",
    "size": "Large (~24k undergrad)",
    "academics": {"strong_programs": ["Business", "Computer Science", "Food Science"], "teaching_style": "Collaborative, Student-focused"},
    "culture": "Spirited, Collegiate, Diverse",
    "strengths_for": ["Students seeking a classic New England college experience", "Collaborative learners"],
    "fit_tags": ["spirited", "collaborative", "diverse", "public"],
    "admission_threshold": {"gpa": 3.5, "sat": 1260, "toefl": 80}
},
{
    "id": 61,
    "name": "Rensselaer Polytechnic Institute (RPI)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Troy, NY)",
    "climate": "Cold winters",
    "size": "Medium (~6k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Computer Science", "Business"], "teaching_style": "Rigorous, Problem-solving"},
    "culture": "Nerdy, Intense, Isolated",
    "strengths_for": ["Die-hard problem solvers", "Future engineers and tech founders"],
    "fit_tags": ["STEM", "rigorous", "nerdy", "intense"],
    "admission_threshold": {"gpa": 3.8, "sat": 1400, "toefl": 90}
},
{
    "id": 62,
    "name": "Worcester Polytechnic Institute (WPI)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Worcester, MA)",
    "climate": "Cold winters",
    "size": "Medium (~5k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Robotics", "Computer Science"], "teaching_style": "Project-based, Hands-on"},
    "culture": "Collaborative, Project-focused, Nerdy",
    "strengths_for": ["Students who learn by doing", "Future engineers and roboticists"],
    "fit_tags": ["STEM", "project-based", "hands-on", "collaborative"],
    "admission_threshold": {"gpa": 3.8, "sat": 1390, "toefl": 90}
},
{
    "id": 63,
    "name": "Bentley University",
    "type": ["National University"],
    "location": "Suburban (Waltham, MA)",
    "climate": "Cold winters",
    "size": "Medium (~4k undergrad)",
    "academics": {"strong_programs": ["Business", "Finance", "Marketing"], "teaching_style": "Professional, Career-focused"},
    "culture": "Pre-professional, Corporate, Networking",
    "strengths_for": ["Students 100% focused on business careers", "Networkers and future executives"],
    "fit_tags": ["business", "pre-professional", "corporate", "networking"],
    "admission_threshold": {"gpa": 3.5, "sat": 1300, "toefl": 90}
},
{
    "id": 64,
    "name": "Babson College",
    "type": ["National University"],
    "location": "Suburban (Wellesley, MA)",
    "climate": "Cold winters",
    "size": "Small (~2.5k undergrad)",
    "academics": {"strong_programs": ["Entrepreneurship", "Business", "Finance"], "teaching_style": "Entrepreneurial, Hands-on"},
    "culture": "Entrepreneurial, Competitive, Networking",
    "strengths_for": ["Future entrepreneurs and business founders", "Students who want to start companies"],
    "fit_tags": ["entrepreneurship", "business", "networking", "competitive"],
    "admission_threshold": {"gpa": 3.6, "sat": 1350, "toefl": 90}
},
{
    "id": 65,
    "name": "Rhode Island School of Design (RISD)",
    "type": ["Specialty School", "Art School"],
    "location": "Urban (Providence, RI)",
    "climate": "Cold winters",
    "size": "Small (~2k undergrad)",
    "academics": {"strong_programs": ["Fine Arts", "Graphic Design", "Industrial Design"], "teaching_style": "Studio-based, Critique-focused"},
    "culture": "Creative, Intense, Non-traditional",
    "strengths_for": ["Dedicated artists and designers", "Visual thinkers and creators"],
    "fit_tags": ["art", "design", "creative", "studio-based"],
    "admission_threshold": {"gpa": 3.5, "sat": 1270, "toefl": 85}
},
{
    "id": 66,
    "name": "Berklee College of Music",
    "type": ["Specialty School", "Music School"],
    "location": "Urban (Boston, MA)",
    "climate": "Cold winters",
    "size": "Medium (~5k undergrad)",
    "academics": {"strong_programs": ["Music Performance", "Music Production", "Film Scoring"], "teaching_style": "Performance-based, Industry-focused"},
    "culture": "Artistic, Musical, Diverse",
    "strengths_for": ["Serious musicians of all genres", "Future music industry professionals"],
    "fit_tags": ["music", "performance", "artistic", "industry-focused"],
    "admission_threshold": {"gpa": 3.3, "sat": 1150, "toefl": 80}
},
{
    "id": 67,
    "name": "Stevens Institute of Technology",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Hoboken, NJ)",
    "climate": "Moderate",
    "size": "Medium (~3.5k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Computer Science", "Business"], "teaching_style": "Practical, Career-focused"},
    "culture": "Nerdy, Career-oriented, Urban",
    "strengths_for": ["STEM students who want NYC proximity", "Career-focused engineers"],
    "fit_tags": ["STEM", "career-focused", "urban", "practical"],
    "admission_threshold": {"gpa": 3.7, "sat": 1410, "toefl": 90}
},
{
    "id": 68,
    "name": "Clarkson University",
    "type": ["National University", "Research Intensive"],
    "location": "Rural (Potsdam, NY)",
    "climate": "Cold winters",
    "size": "Small (~3k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Environmental Science"], "teaching_style": "Hands-on, Collaborative"},
    "culture": "Collaborative, Outdoorsy, STEM-focused",
    "strengths_for": ["Hands-on learners who don't mind cold", "Future engineers and business leaders"],
    "fit_tags": ["STEM", "hands-on", "collaborative", "outdoorsy"],
    "admission_threshold": {"gpa": 3.5, "sat": 1260, "toefl": 80}
},
{
    "id": 69,
    "name": "Rochester Institute of Technology (RIT)",
    "type": ["National University", "Research Intensive"],
    "location": "Suburban (Rochester, NY)",
    "climate": "Cold winters",
    "size": "Large (~13k undergrad)",
    "academics": {"strong_programs": ["Computer Science", "Engineering", "Design"], "teaching_style": "Hands-on, Cooperative education"},
    "culture": "Nerdy, Creative, Cooperative",
    "strengths_for": ["Students who want extensive co-op experience", "Blend of tech and creative arts"],
    "fit_tags": ["STEM", "hands-on", "co-op", "creative"],
    "admission_threshold": {"gpa": 3.6, "sat": 1300, "toefl": 85}
},
{
    "id": 70,
    "name": "Texas A&M University",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (College Station, TX)",
    "climate": "Warm",
    "size": "Large (~56k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Agriculture"], "teaching_style": "Traditional, Spirit-oriented"},
    "culture": "Spirited, Traditional, Massive",
    "strengths_for": ["Students who value tradition and spirit", "Future engineers and business leaders"],
    "fit_tags": ["spirited", "traditional", "massive", "public"],
    "admission_threshold": {"gpa": 3.7, "sat": 1270, "toefl": 85}
},
{
    "id": 71,
    "name": "University of South Carolina (UofSC)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Columbia, SC)",
    "climate": "Warm",
    "size": "Large (~27k undergrad)",
    "academics": {"strong_programs": ["Business", "International Business", "Hospitality"], "teaching_style": "Collaborative, Student-focused"},
    "culture": "Spirited, Southern, Greek-life",
    "strengths_for": ["Business students, especially international business", "Those who love Southern spirit"],
    "fit_tags": ["spirited", "business", "southern", "public"],
    "admission_threshold": {"gpa": 3.6, "sat": 1240, "toefl": 80}
},
{
    "id": 72,
    "name": "University of Tennessee, Knoxville (UTK)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Knoxville, TN)",
    "climate": "Mild",
    "size": "Large (~23k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Architecture"], "teaching_style": "Spirited, Research-oriented"},
    "culture": "Spirited, Traditional, Southern",
    "strengths_for": ["Students who want strong academics with SEC spirit", "Collaborative learners"],
    "fit_tags": ["spirited", "southern", "traditional", "public"],
    "admission_threshold": {"gpa": 3.5, "sat": 1220, "toefl": 80}
},
{
    "id": 73,
    "name": "University of Oklahoma (OU)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Norman, OK)",
    "climate": "Mild",
    "size": "Large (~22k undergrad)",
    "academics": {"strong_programs": ["Meteorology", "Engineering", "Business"], "teaching_style": "Spirited, Research-oriented"},
    "culture": "Spirited, Traditional, Greek-life",
    "strengths_for": ["Future meteorologists", "Students who love school spirit"],
    "fit_tags": ["spirited", "traditional", "public", "research"],
    "admission_threshold": {"gpa": 3.5, "sat": 1210, "toefl": 80}
},
{
    "id": 74,
    "name": "University of Kansas (KU)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Lawrence, KS)",
    "climate": "Moderate",
    "size": "Large (~19k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Journalism"], "teaching_style": "Spirited, Research-oriented"},
    "culture": "Spirited, Traditional, Collegiate",
    "strengths_for": ["Students who want a classic college town experience", "Future journalists and business leaders"],
    "fit_tags": ["spirited", "traditional", "collegiate", "public"],
    "admission_threshold": {"gpa": 3.4, "sat": 1200, "toefl": 80}
},
{
    "id": 75,
    "name": "Iowa State University",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Ames, IA)",
    "climate": "Cold winters",
    "size": "Large (~30k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Agriculture", "Design"], "teaching_style": "Practical, Hands-on"},
    "culture": "Friendly, Collaborative, STEM-focused",
    "strengths_for": ["Future engineers and agricultural scientists", "Hands-on learners"],
    "fit_tags": ["STEM", "hands-on", "friendly", "public"],
    "admission_threshold": {"gpa": 3.4, "sat": 1200, "toefl": 80}
},
{
    "id": 76,
    "name": "University of Nebraska-Lincoln (UNL)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Lincoln, NE)",
    "climate": "Moderate",
    "size": "Large (~20k undergrad)",
    "academics": {"strong_programs": ["Business", "Engineering", "Journalism"], "teaching_style": "Collaborative, Research-oriented"},
    "culture": "Spirited, Friendly, Traditional",
    "strengths_for": ["Students who want Big Ten spirit", "Collaborative learners"],
    "fit_tags": ["spirited", "friendly", "traditional", "public"],
    "admission_threshold": {"gpa": 3.4, "sat": 1180, "toefl": 80}
},
{
    "id": 77,
    "name": "University of Utah",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Salt Lake City, UT)",
    "climate": "Mild",
    "size": "Large (~25k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Business", "Games"], "teaching_style": "Research-oriented, Collaborative"},
    "culture": "Outdoorsy, Innovative, Diverse",
    "strengths_for": ["Students who love skiing and outdoors", "Future game developers"],
    "fit_tags": ["outdoorsy", "innovative", "diverse", "public"],
    "admission_threshold": {"gpa": 3.5, "sat": 1220, "toefl": 80}
},
{
    "id": 78,
    "name": "Utah State University",
    "type": ["Public University", "Research"],
    "location": "Suburban (Logan, UT)",
    "climate": "Mild",
    "size": "Large (~28k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Education", "Agriculture"], "teaching_style": "Practical, Hands-on"},
    "culture": "Outdoorsy, Friendly, Traditional",
    "strengths_for": ["Students who love the outdoors", "Hands-on learners"],
    "fit_tags": ["outdoorsy", "hands-on", "friendly", "public"],
    "admission_threshold": {"gpa": 3.3, "sat": 1150, "toefl": 75}
},
{
    "id": 79,
    "name": "Montana State University",
    "type": ["Public University", "Research"],
    "location": "Suburban (Bozeman, MT)",
    "climate": "Cold winters",
    "size": "Medium (~17k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Nursing", "Agriculture"], "teaching_style": "Practical, Hands-on"},
    "culture": "Outdoorsy, Adventurous, Friendly",
    "strengths_for": ["Students who love mountains and adventure", "Hands-on learners"],
    "fit_tags": ["outdoorsy", "adventurous", "hands-on", "public"],
    "admission_threshold": {"gpa": 3.3, "sat": 1150, "toefl": 75}
},
{
    "id": 80,
    "name": "University of New Mexico (UNM)",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Albuquerque, NM)",
    "climate": "Mild",
    "size": "Large (~17k undergrad)",
    "academics": {"strong_programs": ["Health Sciences", "Engineering", "Business"], "teaching_style": "Research-oriented, Diverse"},
    "culture": "Diverse, Southwestern, Artistic",
    "strengths_for": ["Students interested in health sciences", "Those who appreciate Southwestern culture"],
    "fit_tags": ["diverse", "southwestern", "research", "public"],
    "admission_threshold": {"gpa": 3.2, "sat": 1130, "toefl": 75}
},
{
    "id": 81,
    "name": "New Mexico State University (NMSU)",
    "type": ["Public University", "Research"],
    "location": "Suburban (Las Cruces, NM)",
    "climate": "Mild",
    "size": "Medium (~12k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Agriculture", "Education"], "teaching_style": "Practical, Hands-on"},
    "culture": "Southwestern, Friendly, Diverse",
    "strengths_for": ["Students seeking affordable education", "Hands-on learners"],
    "fit_tags": ["southwestern", "hands-on", "friendly", "public"],
    "admission_threshold": {"gpa": 3.1, "sat": 1100, "toefl": 75}
},
{
    "id": 82,
    "name": "University of Hawaii at Manoa",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (Honolulu, HI)",
    "climate": "Tropical",
    "size": "Large (~12k undergrad)",
    "academics": {"strong_programs": ["Marine Biology", "Astronomy", "Business"], "teaching_style": "Diverse, Research-oriented"},
    "culture": "Diverse, Island-style, Relaxed",
    "strengths_for": ["Students interested in marine science and astronomy", "Those who love island life"],
    "fit_tags": ["diverse", "island", "tropical", "research"],
    "admission_threshold": {"gpa": 3.4, "sat": 1150, "toefl": 80}
},
{
    "id": 83,
    "name": "University of Alaska Fairbanks (UAF)",
    "type": ["Public University", "Research Intensive"],
    "location": "Suburban (Fairbanks, AK)",
    "climate": "Cold winters",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Geology", "Arctic Biology", "Engineering"], "teaching_style": "Research-oriented, Hands-on"},
    "culture": "Adventurous, Isolated, Close-knit",
    "strengths_for": ["Students interested in Arctic research", "Adventurous spirits"],
    "fit_tags": ["adventurous", "research", "close-knit", "arctic"],
    "admission_threshold": {"gpa": 3.0, "sat": 1080, "toefl": 70}
},
{
    "id": 84,
    "name": "Alaska Pacific University",
    "type": ["Private University", "Liberal Arts"],
    "location": "Urban (Anchorage, AK)",
    "climate": "Cold winters",
    "size": "Small (~500 undergrad)",
    "academics": {"strong_programs": ["Environmental Science", "Business", "Education"], "teaching_style": "Experiential, Student-centered"},
    "culture": "Adventurous, Close-knit, Environmental",
    "strengths_for": ["Students passionate about Alaska and the environment", "Those who prefer small classes"],
    "fit_tags": ["adventurous", "environmental", "close-knit", "small"],
    "admission_threshold": {"gpa": 3.0, "sat": 1050, "toefl": 70}
},
{
    "id": 85,
    "name": "Hawaii Pacific University (HPU)",
    "type": ["Private University"],
    "location": "Urban (Honolulu, HI)",
    "climate": "Tropical",
    "size": "Medium (~5k undergrad)",
    "academics": {"strong_programs": ["Business", "Marine Biology", "International Studies"], "teaching_style": "Practical, Diverse"},
    "culture": "Diverse, International, Island-style",
    "strengths_for": ["Students seeking an international experience in Hawaii", "Business and marine science students"],
    "fit_tags": ["diverse", "international", "island", "practical"],
    "admission_threshold": {"gpa": 3.2, "sat": 1100, "toefl": 80}
},
{
    "id": 86,
    "name": "Chaminade University of Honolulu",
    "type": ["Private University", "Liberal Arts"],
    "location": "Urban (Honolulu, HI)",
    "climate": "Tropical",
    "size": "Small (~1k undergrad)",
    "academics": {"strong_programs": ["Criminal Justice", "Business", "Nursing"], "teaching_style": "Personalized, Service-oriented"},
    "culture": "Close-knit, Service-oriented, Island-style",
    "strengths_for": ["Students seeking small classes in Hawaii", "Those interested in service and justice"],
    "fit_tags": ["close-knit", "service", "island", "small"],
    "admission_threshold": {"gpa": 3.0, "sat": 1050, "toefl": 70}
},
{
    "id": 87,
    "name": "University of Puerto Rico, Río Piedras",
    "type": ["Public University", "Research Intensive"],
    "location": "Urban (San Juan, PR)",
    "climate": "Tropical",
    "size": "Large (~15k undergrad)",
    "academics": {"strong_programs": ["Law", "Humanities", "Sciences"], "teaching_style": "Rigorous, Spanish-language"},
    "culture": "Vibrant, Cultural, Spanish-speaking",
    "strengths_for": ["Spanish-speaking students", "Those interested in Caribbean culture"],
    "fit_tags": ["cultural", "spanish", "vibrant", "public"],
    "admission_threshold": {"gpa": 3.0, "sat": 1000, "toefl": 70}
},
{
    "id": 88,
    "name": "University of the Virgin Islands",
    "type": ["Public University", "Liberal Arts"],
    "location": "Suburban (St. Thomas, VI)",
    "climate": "Tropical",
    "size": "Small (~2k undergrad)",
    "academics": {"strong_programs": ["Business", "Education", "Marine Biology"], "teaching_style": "Personalized, Island-focused"},
    "culture": "Close-knit, Caribbean, Diverse",
    "strengths_for": ["Students interested in Caribbean studies", "Those seeking small classes in paradise"],
    "fit_tags": ["close-knit", "caribbean", "island", "small"],
    "admission_threshold": {"gpa": 2.5, "sat": 950, "toefl": 65}
},
{
    "id": 89,
    "name": "American University (AU)",
    "type": ["National University", "Research"],
    "location": "Urban (Washington, D.C.)",
    "climate": "Moderate",
    "size": "Medium (~8k undergrad)",
    "academics": {"strong_programs": ["International Relations", "Political Science", "Business"], "teaching_style": "Discussion-based, Professional"},
    "culture": "Political, Activist, Professional",
    "strengths_for": ["Future politicians and diplomats", "Students passionate about policy"],
    "fit_tags": ["political", "activist", "professional", "DC"],
    "admission_threshold": {"gpa": 3.7, "sat": 1320, "toefl": 90}
},
{
    "id": 90,
    "name": "George Washington University (GWU)",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Washington, D.C.)",
    "climate": "Moderate",
    "size": "Large (~12k undergrad)",
    "academics": {"strong_programs": ["International Affairs", "Political Science", "Business"], "teaching_style": "Professional, Network-driven"},
    "culture": "Professional, Political, Urban",
    "strengths_for": ["Students who want DC internships", "Future leaders in policy and business"],
    "fit_tags": ["professional", "political", "DC", "network"],
    "admission_threshold": {"gpa": 3.7, "sat": 1350, "toefl": 90}
},
{
    "id": 91,
    "name": "Howard University",
    "type": ["National University", "Research Intensive"],
    "location": "Urban (Washington, D.C.)",
    "climate": "Moderate",
    "size": "Medium (~7k undergrad)",
    "academics": {"strong_programs": ["Business", "Communications", "Health Sciences"], "teaching_style": "Collaborative, Culturally-focused"},
    "culture": "Historically Black, Cultural, Prestigious",
    "strengths_for": ["Students seeking an HBCU experience", "Future leaders in business and health"],
    "fit_tags": ["HBCU", "cultural", "prestigious", "DC"],
    "admission_threshold": {"gpa": 3.5, "sat": 1180, "toefl": 80}
},
{
    "id": 92,
    "name": "Hampton University",
    "type": ["National University", "Research"],
    "location": "Suburban (Hampton, VA)",
    "climate": "Mild",
    "size": "Medium (~4k undergrad)",
    "academics": {"strong_programs": ["Business", "Journalism", "Pharmacy"], "teaching_style": "Traditional, Career-focused"},
    "culture": "Historically Black, Traditional, Close-knit",
    "strengths_for": ["Students seeking an HBCU experience", "Future business and health professionals"],
    "fit_tags": ["HBCU", "traditional", "career-focused", "close-knit"],
    "admission_threshold": {"gpa": 3.3, "sat": 1100, "toefl": 80}
},
{
    "id": 93,
    "name": "Morehouse College",
    "type": ["Liberal Arts College", "HBCU"],
    "location": "Urban (Atlanta, GA)",
    "climate": "Mild",
    "size": "Small (~2k undergrad)",
    "academics": {"strong_programs": ["Business", "Political Science", "Humanities"], "teaching_style": "Leadership-focused, Traditional"},
    "culture": "Historically Black, Leadership-focused, Brotherhood",
    "strengths_for": ["Young men seeking leadership development", "Future business and community leaders"],
    "fit_tags": ["HBCU", "leadership", "brotherhood", "traditional"],
    "admission_threshold": {"gpa": 3.4, "sat": 1160, "toefl": 80}
},
{
    "id": 94,
    "name": "Spelman College",
    "type": ["Liberal Arts College", "HBCU"],
    "location": "Urban (Atlanta, GA)",
    "climate": "Mild",
    "size": "Small (~2k undergrad)",
    "academics": {"strong_programs": ["Biology", "Psychology", "Political Science"], "teaching_style": "Leadership-focused, Collaborative"},
    "culture": "Historically Black, Leadership-focused, Sisterhood",
    "strengths_for": ["Young women seeking leadership development", "Future STEM and policy leaders"],
    "fit_tags": ["HBCU", "leadership", "sisterhood", "collaborative"],
    "admission_threshold": {"gpa": 3.5, "sat": 1180, "toefl": 80}
},
{
    "id": 95,
    "name": "Florida A&M University (FAMU)",
    "type": ["Public University", "HBCU"],
    "location": "Urban (Tallahassee, FL)",
    "climate": "Warm",
    "size": "Large (~9k undergrad)",
    "academics": {"strong_programs": ["Pharmacy", "Business", "Journalism"], "teaching_style": "Professional, Career-focused"},
    "culture": "Historically Black, Spirited, Professional",
    "strengths_for": ["Students seeking an HBCU experience", "Future pharmacists and business leaders"],
    "fit_tags": ["HBCU", "spirited", "professional", "public"],
    "admission_threshold": {"gpa": 3.3, "sat": 1100, "toefl": 80}
},
{
    "id": 96,
    "name": "North Carolina A&T State University",
    "type": ["Public University", "HBCU"],
    "location": "Urban (Greensboro, NC)",
    "climate": "Mild",
    "size": "Large (~12k undergrad)",
    "academics": {"strong_programs": ["Engineering", "Agriculture", "Business"], "teaching_style": "Practical, Hands-on"},
    "culture": "Historically Black, Spirited, STEM-focused",
    "strengths_for": ["STEM students seeking an HBCU", "Hands-on learners"],
    "fit_tags": ["HBCU", "STEM", "hands-on", "spirited"],
    "admission_threshold": {"gpa": 3.3, "sat": 1080, "toefl": 80}
},
{
    "id": 97,
    "name": "Berea College",
    "type": ["Liberal Arts College"],
    "location": "Rural (Berea, KY)",
    "climate": "Mild",
    "size": "Small (~1.5k undergrad)",
    "academics": {"strong_programs": ["Sustainability", "Education", "Business"], "teaching_style": "Labor-based, Student-centered"},
    "culture": "Service-oriented, Close-knit, Tuition-free",
    "strengths_for": ["Students seeking a tuition-free education", "Those committed to service and labor"],
    "fit_tags": ["tuition-free", "service", "close-knit", "labor-based"],
    "admission_threshold": {"gpa": 3.5, "sat": 1150, "toefl": 80}
},
{
    "id": 98,
    "name": "Deep Springs College",
    "type": ["Liberal Arts College"],
    "location": "Rural (Deep Springs, CA)",
    "climate": "Desert",
    "size": "Very Small (~26 undergrad)",
    "academics": {"strong_programs": ["Humanities", "Social Sciences", "Labor"], "teaching_style": "Discussion-based, Labor-intensive"},
    "culture": "Isolated, Self-governed, Intellectual",
    "strengths_for": ["Highly self-motivated and intellectual students", "Those seeking a unique labor-based education"],
    "fit_tags": ["isolated", "self-governed", "labor-based", "intellectual"],
    "admission_threshold": {"gpa": 3.8, "sat": 1450, "toefl": 100}
},
{
    "id": 99,
    "name": "Cooper Union",
    "type": ["Specialty School", "Engineering/Art"],
    "location": "Urban (New York, NY)",
    "climate": "Moderate",
    "size": "Very Small (~900 undergrad)",
    "academics": {"strong_programs": ["Engineering", "Architecture", "Art"], "teaching_style": "Rigorous, Project-based"},
    "culture": "Intense, Creative, Merit-based",
    "strengths_for": ["Exceptional artists, architects, and engineers", "Students seeking a tuition-free education"],
    "fit_tags": ["tuition-free", "rigorous", "creative", "project-based"],
    "admission_threshold": {"gpa": 3.8, "sat": 1480, "toefl": 100}
},
{
    "id": 100,
    "name": "Webb Institute",
    "type": ["Specialty School", "Engineering"],
    "location": "Suburban (Glen Cove, NY)",
    "climate": "Moderate",
    "size": "Very Small (~100 undergrad)",
    "academics": {"strong_programs": ["Naval Architecture", "Marine Engineering"], "teaching_style": "Rigorous, Hands-on"},
    "culture": "Nerdy, Close-knit, Nautical",
    "strengths_for": ["Students passionate about ship design", "Those seeking a tuition-free engineering education"],
    "fit_tags": ["tuition-free", "nautical", "close-knit", "rigorous"],
    "admission_threshold": {"gpa": 3.9, "sat": 1450, "toefl": 100}
}
]

    # Initialize or load database
    collection, embed_model = init_or_load_vector_database(universities_db)

    # Convert student profile into query text
    student_query = create_student_query(student_profile)
    print("Student Query:", student_query)

    # Encode query and retrieve top 3
    query_embedding = create_weighted_query_embedding(student_profile, embed_model)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=30,
        include=["metadatas", "distances"]
    )

    matched_universities = results['metadatas'][0]
    distances = results['distances'][0]

    print("matched_universities:",matched_universities)
    #matched_universities = filter_by_climate(matched_universities, student_profile)

    #print(distances)
    # Format universities with strict categories
    matched_universities_text = format_universities_for_prompt(
        matched_universities, distances, student_profile
    )

    try:
    # 生成报告
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
