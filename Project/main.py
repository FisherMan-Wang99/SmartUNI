import streamlit as st
from utils import init_db

# Initialize database
init_db()

# Page configuration
st.set_page_config(
    page_title="US University Fit Test",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Read URL query parameters
query_params = st.query_params
if 'session_id' in query_params:
    st.session_state.session_id = query_params['session_id'][0]

# Welcome Page
st.title("🎓 US University Fit Test System")
st.markdown("## Your Personalized Study Abroad Planning Assistant")

# Main Introduction Section
st.markdown("""
### 🎯 System Introduction
Welcome to the US University Fit Test System! This is an application assistance tool specifically designed for students to find the most suitable study abroad destinations through scientific algorithms and comprehensive data.

### ✨ Core Features

**🔍 Personalized Fit Analysis**
- Receive precise university matches based on your academic performance, interests, and personal preferences.
- Factors like GPA, standardized test scores, and fields of interest are all considered.
- Generates a fit visualization report to intuitively show your competitiveness.

**📊 CloudPath University Rankings**
- Provides multi-dimensional university evaluations that differ from traditional rankings.
- Includes key indicators such as academic reputation, career prospects, and internationalization.
- Supports custom weighting so you can adjust rankings based on what matters most to you.

**📝 Complete Evaluation Process**
- A brief questionnaire to quickly capture your basic information and preferences.
- Intelligent algorithms generate personalized recommendation results.
- Provides detailed school information and application advice.

### 💡 User Guide

1. **Start the Test** - Fill out a short survey with your academic info and preferences.
2. **View Results** - Get personalized university recommendations and fit analysis.
3. **Explore Rankings** - Browse CloudPath University Rankings to discover more school options.
4. **Save Results** - Use a save code to view your recommendation results at any time.

### 🔒 Privacy Protection
We value your privacy. All personal information is used solely for generating recommendation results and will not be shared with third parties.
""")

# Feature Highlight Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Data-Driven Analysis")
    st.markdown("Based on the latest US university data and application trends to provide accurate recommendations.")
    
with col2:
    st.markdown("### 🎯 Personalized Matching")
    st.markdown("Considers your unique background and preferences to find the best fit for your university choices.")
    
with col3:
    st.markdown("### 📚 Comprehensive Resources")
    st.markdown("Provides detailed university information and application suggestions to assist your planning.")

# FAQ Section
with st.expander("❓ Frequently Asked Questions", expanded=False):
    st.markdown("**Q: How accurate are the test results?**")
    st.markdown("A: The system generates recommendations based on actual university admission data and multi-dimensional analysis, but final results are influenced by many factors.")
    
    st.markdown("**Q: How long does the test take to complete?**")
    st.markdown("A: The complete questionnaire usually takes only 5-10 minutes.")
    
    st.markdown("**Q: How do I save my test results?**")
    st.markdown("A: A unique save code is generated after submitting the survey; use this code to access your results later.")
    
    st.markdown("**Q: What school information is included in the recommendations?**")
    st.markdown("A: It includes school names, fit scores, basic introductions, and specific application advice.")

# Custom CSS Styles
st.markdown("""
<style>
/* Remove all hidden styles */
</style>
""", unsafe_allow_html=True)


# Add "Start Test" Button
if st.button("🚀 Start Test"):
    st.switch_page("pages/问卷.py")

# 如果 URL 里带有保存代码，提供查看结果的快捷入口
if 'save_code' in query_params:
    st.sidebar.markdown("### 你有保存的结果")
    save_code = query_params['save_code'][0]
    if st.sidebar.button(f"查看保存代码 {save_code} 的结果"):
        st.switch_page("pages/结果.py")
