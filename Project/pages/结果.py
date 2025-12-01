import streamlit as st
from utils import *
import plotly.express as px
from utils import generate_pdf_report, recommend_universities


# 检查是否完成了问卷
if 'survey_data' not in st.session_state:
    st.warning("请先完成问卷")
    st.switch_page("pages/问卷.py")

# 获取问卷数据
data = st.session_state.survey_data
save_code = st.session_state.get('save_code', 'N/A')

# 页面标题
st.title(f"🎓 {data['name']}的美国大学推荐")
st.markdown(f"你的保存代码: `{save_code}` - 使用此代码可以随时查看你的结果")

# 显示摘要信息
with st.expander("查看我的问卷回答", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("GPA", data['gpa'])
        st.metric("年级", data['grade'])
    with col2:
        st.metric("SAT", data['sat'] if data['sat'] else "未提供")
        st.metric("偏好规模", data['size'].split(')')[0])
    
    st.write(f"**兴趣领域:** {', '.join(data['interests'])}")
    st.write(f"**地理位置偏好:** {data['location']}")

# 获取大学推荐
recommendations = recommend_universities(data)

# 显示推荐结果
st.subheader("🏫 为你推荐的大学")
for i, uni in enumerate(recommendations, 1):
    st.markdown(f"{i}. **{uni}**")

# 可视化 - 匹配度分析
st.subheader("📊 你的匹配度分析")
match_scores = {uni: min(90 + i*5 + data['gpa']*10, 100) for i, uni in enumerate(recommendations)}  # 示例算法
df = pd.DataFrame(list(match_scores.items()), columns=['大学', '匹配度'])
fig = px.bar(df, x='大学', y='匹配度', color='匹配度', range_y=[0,100])
st.plotly_chart(fig, use_container_width=True)

# 下一步建议
st.subheader("📅 下一步行动建议")
st.markdown("""
1. **研究推荐的大学** - 访问大学官网了解详情
2. **规划访校** - 如果可能，实地参观校园
3. **准备申请材料** - 开始准备文书和推荐信
4. **考试准备** - 考虑是否需要重考SAT/ACT提高分数
""")

# 移除隐藏样式，确保所有内容正常显示
# 自定义CSS样式
st.markdown("""
<style>
/* 移除所有隐藏样式 */
</style>
""", unsafe_allow_html=True)

# 重新测试选项
st.markdown("---")
if st.button("重新填写问卷"):
    del st.session_state.survey_data
    st.switch_page("pages/问卷.py")

if st.button("了解云道榜单"):
    st.switch_page("pages/云道_ranking.py")