import streamlit as st
import pandas as pd
import plotly.express as px
from utils import init_db, generate_pdf_report, recommend_universities

# Check if the questionnaire has been completed
if 'survey_data' not in st.session_state:
    st.warning("Please complete the questionnaire first.")
    # Ensure this matches your filename in the pages folder
    st.switch_page("pages/Questionnaire.py")

# Get survey data
data = st.session_state.survey_data
save_code = st.session_state.get('save_code', 'N/A')

# Page Title
st.title(f"🎓 US University Recommendations for {data['name']}")
st.markdown(f"Your Save Code: `{save_code}` — Use this code to access your results anytime.")

# Display Summary Information
with st.expander("View My Survey Responses", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("GPA", data['gpa'])
        st.metric("Grade Level", data['grade'])
    with col2:
        st.metric("SAT Score", data['sat'] if data['sat'] else "Not Provided")
        # Assuming data['size'] format is "Large (10,000+)"
        st.metric("Size Preference", data['size'].split(')')[0] + ")")
    
    st.write(f"**Fields of Interest:** {', '.join(data['interests'])}")
    st.write(f"**Location Preference:** {data['location']}")

# Get University Recommendations
recommendations = recommend_universities(data)

# Display Recommendation Results
st.subheader("🏫 Recommended Universities for You")
for i, uni in enumerate(recommendations, 1):
    st.markdown(f"{i}. **{uni}**")

# Visualization - Match Analysis
st.subheader("📊 Your Fit Analysis")
# Example matching algorithm for visualization
match_scores = {uni: min(90 + i*5 + data['gpa']*10, 100) for i, uni in enumerate(recommendations)}
df = pd.DataFrame(list(match_scores.items()), columns=['University', 'Match Score'])
fig = px.bar(df, x='University', y='Match Score', color='Match Score', range_y=[0, 100])
st.plotly_chart(fig, use_container_width=True)

# Next Steps
st.subheader("📅 Recommended Next Steps")
st.markdown("""
1. **Research Recommended Universities** — Visit official university websites to learn more details.
2. **Plan Campus Visits** — If possible, visit the campuses in person to get a feel for the environment.
3. **Prepare Application Materials** — Start working on your personal statements and requesting letters of recommendation.
4. **Test Preparation** — Consider whether you need to retake the SAT/ACT to improve your score.
""")

# Custom CSS Styles (Ensuring all content displays correctly)
st.markdown("""
<style>
/* Reset or add custom styles here */
</style>
""", unsafe_allow_html=True)

# Retest Option
st.markdown("---")
if st.button("重新填写问卷"):
    del st.session_state.survey_data
    st.switch_page("pages/问卷.py")

if st.button("了解云道榜单"):
    st.switch_page("pages/云道_ranking.py")