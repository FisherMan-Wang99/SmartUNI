import streamlit as st
from utils import save_final_response

# Set page configuration and styling
st.set_page_config(initial_sidebar_state="expanded")

# Keep the content area styling
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

st.title("🎓 US University Fit Questionnaire")

st.markdown("Complete this questionnaire to get personalized recommendations. Fields marked with * are required.")

progress_bar = st.progress(0)

name = st.text_input("Full Name *", key="name_input", help="Please enter your full name")
email = st.text_input("Email Address (Optional)", key="email_input", help="Providing an email allows you to save your results")

grade = st.selectbox(
    "Current Grade *",
    options=["Select an option", "9th Grade", "10th Grade", "11th Grade", "12th Grade"],
    index=0,
    key="grade_selectbox",
    help="Please select your current grade level"
)

gpa = st.slider(
    "GPA (4.0 Scale) *",
    min_value=0.0,
    max_value=4.0,
    value=0.0,
    step=0.1,
    key="gpa_slider",
    help="Please enter your current GPA"
)

sat = st.number_input(
    "SAT Score (Optional)",
    min_value=400,
    max_value=1600,
    value=400,
    step=10,
    key="sat_input",
    help="Leave blank if you haven't taken the test"
)

interests = st.multiselect(
    "Academic Interests (Select 1-3) *",
    options=["STEM", "Humanities & Social Sciences", "Business", "Arts", "Pre-med"],
    default=[],
    key="interests_multiselect",
    help="Choose the fields you are most interested in"
)

size = st.radio(
    "Preferred School Size *",
    options=["Select an option", "Small (<5,000)", "Medium (5,000-15,000)", "Large (>15,000)"],
    index=0,
    key="size_radio",
    help="The size of the university you wish to attend"
)

location = st.selectbox(
    "Preferred Geographic Location *",
    options=["Select an option", "East Coast", "West Coast", "Midwest", "South", "No Preference"],
    index=0,
    key="location_selectbox",
    help="Preferred geographic region in the US"
)

extracurriculars = st.text_area(
    "Extracurricular Activities/Talents (Optional)",
    key="extracurriculars_textarea",
    help="Briefly describe your extracurricular activities or special talents"
)

special_needs = st.multiselect(
    "Special Needs (Optional)",
    options=["Accessibility Facilities", "Learning Support", "Mental Health Services", "Other"],
    key="special_needs_multiselect",
    help="Any special support you may require"
)

def calculate_progress():
    total_required = 6
    filled = 0
    if st.session_state.get("name_input", ""):
        filled += 1
    if st.session_state.get("grade_selectbox", "Select an option") != "Select an option":
        filled += 1
    if st.session_state.get("gpa_slider", 0) > 0:
        filled += 1
    interests_sel = st.session_state.get("interests_multiselect", [])
    if 1 <= len(interests_sel) <= 3:
        filled += 1
    if st.session_state.get("size_radio", "Select an option") != "Select an option":
        filled += 1
    if st.session_state.get("location_selectbox", "Select an option") != "Select an option":
        filled += 1
    return int(filled / total_required * 100)

progress = calculate_progress()
progress_bar.progress(progress)

if st.button("Submit Questionnaire"):
    errors = []
    if not name:
        errors.append("Name is required.")
    if grade == "Select an option":
        errors.append("Please select your grade.")
    if gpa <= 0:
        errors.append("Please enter a valid GPA.")
    if not interests or len(interests) > 3:
        errors.append("Please select between 1 and 3 academic interests.")
    if size == "Select an option":
        errors.append("Please select a preferred school size.")
    if location == "Select an option":
        errors.append("Please select a preferred location.")

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

        save_code = save_final_response(survey_data)

        st.session_state.survey_data = survey_data
        st.session_state.save_code = save_code

        progress_bar.progress(100)
        st.success("Successfully submitted! We're loading the results now...")
        st.switch_page("pages/结果.py")
