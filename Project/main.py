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
st.title("🎓 美国大学适配测试")
st.markdown("""
欢迎使用美国大学适配测试系统！这个工具将帮助你：

- 根据你的学术表现和兴趣发现最适合的大学
- 了解你的竞争力水平
- 获得个性化的申请建议
""")

# 隐藏菜单
hide_style = """
<style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(hide_style, unsafe_allow_html=True)


# 添加“开始测试”按钮
if st.button("🚀 开始测试"):
    st.switch_page("pages/问卷.py")

# 如果 URL 里带有保存代码，提供查看结果的快捷入口
if 'save_code' in query_params:
    st.sidebar.markdown("### 你有保存的结果")
    save_code = query_params['save_code'][0]
    if st.sidebar.button(f"查看保存代码 {save_code} 的结果"):
        st.switch_page("pages/结果.py")
