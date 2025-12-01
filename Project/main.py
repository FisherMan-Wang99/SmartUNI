import streamlit as st
from utils import init_db

# 初始化数据库
init_db()

# 页面基础配置
st.set_page_config(
    page_title="美国大学适配测试",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 读取 URL 查询参数
query_params = st.query_params
if 'session_id' in query_params:
    st.session_state.session_id = query_params['session_id'][0]

# 欢迎页面
st.title("🎓 美国大学适配测试系统")
st.markdown("## 你的个性化留学规划助手")

# 主要介绍区域
st.markdown("""
### 🎯 系统简介
欢迎使用美国大学适配测试系统！这是一个为中国学生量身打造的美国大学申请辅助工具，通过科学的算法和全面的数据，帮助你找到最适合的留学目的地。

### ✨ 核心功能

**🔍 个性化适配分析**
- 根据你的学术成绩、兴趣爱好和个人偏好提供精准的大学匹配
- 考虑GPA、标准化考试成绩、兴趣领域等多维度因素
- 生成匹配度可视化报告，直观展示你的竞争力

**📊 云道大学排名**
- 提供不同于传统排名的多维度大学评估
- 包含学术声誉、就业前景、国际化程度等关键指标
- 支持自定义权重，根据你的关注点调整排名结果

**📝 完整的评估流程**
- 简短问卷快速获取你的基本信息和偏好
- 智能算法生成个性化推荐结果
- 提供详细的学校信息和申请建议

### 💡 使用指南

1. **开始测试** - 填写简短问卷，输入你的学术信息和偏好
2. **查看结果** - 获得个性化的大学推荐和匹配度分析
3. **探索榜单** - 浏览云道大学排名，了解更多学校选择
4. **保存结果** - 通过保存代码随时查看你的推荐结果

### 🔒 隐私保护
我们重视你的隐私，所有个人信息仅用于生成推荐结果，不会共享给第三方。
""")

# 功能亮点卡片
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 数据驱动分析")
    st.markdown("基于最新的美国大学数据和申请趋势，提供科学准确的推荐。")
    
with col2:
    st.markdown("### 🎯 个性化匹配")
    st.markdown("考虑你的独特背景和偏好，找到最适合你的大学选择。")
    
with col3:
    st.markdown("### 📚 全面资源")
    st.markdown("提供大学详细信息和申请建议，助力你的留学规划。")

# 常见问题解答
with st.expander("❓ 常见问题", expanded=False):
    st.markdown("**Q: 测试结果的准确度如何？**")
    st.markdown("A: 系统基于实际大学录取数据和多维度分析生成推荐，但最终申请结果还受多种因素影响。")
    
    st.markdown("**Q: 测试需要多长时间完成？**")
    st.markdown("A: 完整问卷通常只需5-10分钟即可完成。")
    
    st.markdown("**Q: 如何保存我的测试结果？**")
    st.markdown("A: 提交问卷后会生成唯一的保存代码，使用此代码可以随时查看你的结果。")
    
    st.markdown("**Q: 推荐结果包括哪些学校信息？**")
    st.markdown("A: 包括学校名称、匹配度评分、基本介绍以及申请建议等信息。")

# 移除隐藏样式，确保所有内容正常显示
# 自定义CSS样式
st.markdown("""
<style>
/* 移除所有隐藏样式 */
</style>
""", unsafe_allow_html=True)


# 添加“开始测试”按钮
if st.button("🚀 开始测试"):
    st.switch_page("pages/问卷.py")

# 如果 URL 里带有保存代码，提供查看结果的快捷入口
if 'save_code' in query_params:
    st.sidebar.markdown("### 你有保存的结果")
    save_code = query_params['save_code'][0]
    if st.sidebar.button(f"查看保存代码 {save_code} 的结果"):
        st.switch_page("pages/结果.py")
