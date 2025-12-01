import streamlit as st
from utils import save_final_response

# 设置页面配置和样式
st.set_page_config(initial_sidebar_state="expanded")

# 保留内容区域的样式，但移除隐藏元素的设置
style = """
<style>
    section.main > div.block-container {
        max-width: 700px;
        padding-left: 1rem;
        padding-right: 1rem;
    }
</style>
"""
st.markdown(style, unsafe_allow_html=True)

st.title("🎓 美国大学适配问卷")

st.markdown("完成此问卷，获取个性化推荐。所有带*项为必填。")

progress_bar = st.progress(0)

name = st.text_input("姓名 *", key="name_input", help="请输入你的全名")
email = st.text_input("电子邮箱 (选填)", key="email_input", help="填写邮箱可保存结果")

grade = st.selectbox(
    "当前年级 *",
    options=["请选择", "9年级", "10年级", "11年级", "12年级"],
    index=0,
    key="grade_selectbox",
    help="请选择当前年级"
)

gpa = st.slider(
    "GPA (4.0制) *",
    min_value=0.0,
    max_value=4.0,
    value=0.0,
    step=0.1,
    key="gpa_slider",
    help="请输入你的GPA成绩"
)

sat = st.number_input(
    "SAT分数 (选填)",
    min_value=400,
    max_value=1600,
    value=400,
    step=10,
    key="sat_input",
    help="如果没考可不填"
)

interests = st.multiselect(
    "学术兴趣（选1-3项） *",
    options=["STEM", "人文社科", "商科", "艺术", "医学预科"],
    default=[],
    key="interests_multiselect",
    help="选择你最感兴趣的领域"
)

size = st.radio(
    "偏好的学校规模 *",
    options=["请选择", "小型(<5,000)", "中型(5,000-15,000)", "大型(>15,000)"],
    index=0,
    key="size_radio",
    help="希望就读大学规模"
)

location = st.selectbox(
    "偏好的地理位置 *",
    options=["请选择", "东海岸", "西海岸", "中西部", "南部", "不限"],
    index=0,
    key="location_selectbox",
    help="希望就读的地理区域"
)

extracurriculars = st.text_area(
    "课外活动/特长 (选填)",
    key="extracurriculars_textarea",
    help="简述你的课外活动或特长"
)

special_needs = st.multiselect(
    "特殊需求 (选填)",
    options=["无障碍设施", "学习支持", "心理健康服务", "其他"],
    key="special_needs_multiselect",
    help="需要的特殊支持"
)

def calculate_progress():
    total_required = 6
    filled = 0
    if st.session_state.get("name_input", ""):
        filled += 1
    if st.session_state.get("grade_selectbox", "请选择") != "请选择":
        filled += 1
    if st.session_state.get("gpa_slider", 0) > 0:
        filled += 1
    interests_sel = st.session_state.get("interests_multiselect", [])
    if 1 <= len(interests_sel) <= 3:
        filled += 1
    if st.session_state.get("size_radio", "请选择") != "请选择":
        filled += 1
    if st.session_state.get("location_selectbox", "请选择") != "请选择":
        filled += 1
    return int(filled / total_required * 100)

progress = calculate_progress()
progress_bar.progress(progress)

if st.button("提交问卷"):
    errors = []
    if not name:
        errors.append("姓名为必填")
    if grade == "请选择":
        errors.append("请选择年级")
    if gpa <= 0:
        errors.append("请输入有效GPA")
    if not interests or len(interests) > 3:
        errors.append("学术兴趣必须选择1-3项")
    if size == "请选择":
        errors.append("请选择学校规模")
    if location == "请选择":
        errors.append("请选择地理位置")

    if errors:
        for e in errors:
            st.error(e)
    else:
        survey_data = {
            "name": name,
            "email": email,
            "grade": grade,
            "gpa": gpa,
            "sat": sat if sat >= 400 else None,
            "interests": interests,
            "size": size,
            "location": location,
            "extracurriculars": extracurriculars,
            "special_needs": special_needs,
        }
        st.success("问卷提交成功！")
        st.write("提交数据:", survey_data)
        # 这里接入保存数据库和跳转等逻辑

        save_code = save_final_response(survey_data)

        st.session_state.survey_data = survey_data
        st.session_state.save_code = save_code

        progress_bar.progress(100)
        st.success("问卷提交成功！正在生成你的个性化推荐...")
        st.switch_page("pages/结果.py")
