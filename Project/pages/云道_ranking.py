import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Initialization ---
st.set_page_config(
    page_title="Yundao Ranking System", 
    page_icon="🏫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Default Weight Configuration ---
DEFAULT_WEIGHTS = {
    'Academics': 0.15,
    'Safety': 0.1,
    'Happiness': 0.08,
    'Opportunities': 0.08,
    'Infrastructure': 0.07,
    'International friendliness': 0.05,
    'Location': 0.05,
    'Social': 0.05,
    'Learning Opportunities': 0.1,
    'Preparation for Career': 0.1,
    'Learning Facilities': 0.07,
    'Character Development': 0.05,
    'Recommendation Score': 0.03,
    'Academic Reputation': 0.02
}

# --- Load Student Survey Data ---
@st.cache_data
def load_survey_data():
    try:
        # Assuming survey results are in 'survey_results.xlsx'
        survey_df = pd.read_excel('Project/data/survey_results.xlsx')
        
        # Check if necessary columns exist
        required_columns = ['红色', '紫色', '蓝色', '金色', '绿色']
        for col in required_columns:
            if col not in survey_df.columns:
                st.warning(f"Column '{col}' missing in survey data, using sample data.")
                raise ValueError(f"Missing '{col}' column")
        
        # Extract results for the first student
        student_data = survey_df.iloc[0].to_dict()
        
        # Keep internal keys as requested, mapping to radar format
        radar_data = {
            '红色': student_data.get('红色', 10),
            '紫色': student_data.get('紫色', 10),
            '蓝色': student_data.get('蓝色', 10),
            '金色': student_data.get('金色', 10),
            '绿色': student_data.get('绿色', 10),
        }
        return radar_data
    
    except Exception as e:
        st.warning(f"Failed to load survey data: {str(e)}. Using sample data.")
        return {
            '红色': 0, '紫色': 0, '蓝色': 0, '金色': 0, '绿色': 0
        }

# --- Data Loading and Normalization ---
@st.cache_data
def load_and_normalize_data():
    df = pd.read_excel('Project/data/unidata.xlsx') 
    
    required_columns = ['大学'] + list(DEFAULT_WEIGHTS.keys())
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column in data file: {col}")
    
    five_point_metrics = ['Academics', 'Safety', 'Happiness', 'Opportunities', 
                         'Infrastructure', 'International friendliness', 
                         'Location', 'Social']
    
    hundred_point_metrics = ['Learning Opportunities', 'Preparation for Career',
                           'Learning Facilities', 'Character Development',
                           'Recommendation Score', 'Academic Reputation']
    
    for metric in five_point_metrics:
        df[metric] = df[metric] * 20
    
    for metric in five_point_metrics + hundred_point_metrics:
        df[metric] = df[metric].clip(0, 100)
    
    return df

# Load Data
df = load_and_normalize_data()
metrics = list(DEFAULT_WEIGHTS.keys())
survey_data = load_survey_data()

# --- Page Header ---
st.markdown('<div class="main-title">🏫 Care4YA Yundao US University Ranking System</div>', unsafe_allow_html=True)

# Bar Chart Data (Mapping Chinese keys to English labels for the UI)
key_mapping = {
    '红色': 'Academic Focus',
    '紫色': 'Career Drive',
    '蓝色': 'Campus Life',
    '金色': 'Global Vision',
    '绿色': 'Personal Growth'
}
categories = [key_mapping.get(k, k) for k in survey_data.keys()]
values = list(survey_data.values())

# Create Bar Chart
fig_bar = px.bar(
    x=categories,
    y=values,
    color=categories,
    color_discrete_sequence=['#3A7BD5', '#8E54E9', '#00B4DB', '#F46B45', '#F79D00'],
    labels={'x': 'Dimension', 'y': 'Interest Index'},
    title="📊 Student Interest Index (Based on Survey)"
)

fig_bar.update_layout(
    title={
        'text': "📊 Student Interest Index (Based on Survey)",
        'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
        'font': dict(size=18)
    },
    xaxis_title="Interest Dimension",
    yaxis_title="Interest Index",
    yaxis=dict(range=[0, 6]),
    height=400,
    margin=dict(l=50, r=50, b=50, t=80),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False,
    hovermode="x unified"
)

fig_bar.update_traces(texttemplate='%{y}', textposition='outside')
st.plotly_chart(fig_bar, use_container_width=True)

# --- CSS Styles ---
st.markdown("""
<style>
.main-title { font-size: 32px !important; font-weight: 700 !important; color: #1a3e72 !important; margin-bottom: 20px !important; padding-bottom: 10px; border-bottom: 2px solid #e1e5eb; }
.section-title { font-size: 24px !important; font-weight: 600 !important; color: #2c4e7a !important; margin: 25px 0 15px 0 !important; }
.card { background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; border-left: 4px solid #3a7bd5; }
.metric-card { background-color: #f8fafc; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 3px solid #3a7bd5; }
</style>
""", unsafe_allow_html=True)

# --- Weight Management Logic ---
def init_weights():
    for key, val in DEFAULT_WEIGHTS.items():
        if f"weight_{key}" not in st.session_state:
            st.session_state[f"weight_{key}"] = val

def reset_weights():
    for key, val in DEFAULT_WEIGHTS.items():
        st.session_state[f"weight_{key}"] = val
    st.rerun()

init_weights()

# --- Sidebar Weight Adjustment ---
st.sidebar.title("⚖️ Weight Adjustment")
st.sidebar.info("Customize weights for each metric to see how they impact the rankings.")

if st.sidebar.button("🔄 Reset to Default"):
    reset_weights()

st.sidebar.divider()

with st.sidebar.expander("📊 Adjust Metric Weights", expanded=False):
    current_weights = [st.session_state[f"weight_{key}"] for key in metrics]
    total_weight = sum(current_weights)
    
    academic_metrics = ['Academics', 'Learning Opportunities', 'Learning Facilities', 'Academic Reputation']
    career_metrics = ['Preparation for Career', 'Opportunities', 'Recommendation Score']
    life_metrics = ['Safety', 'Happiness', 'Infrastructure', 'International friendliness', 'Location', 'Social', 'Character Development']
    
    st.subheader("🎓 Academic")
    for metric in academic_metrics:
        if metric in metrics:
            st.session_state[f"weight_{metric}"] = st.sidebar.slider(f"{metric}", 0.0, 0.3, st.session_state[f"weight_{metric}"], 0.01)
    
    st.subheader("💼 Career")
    for metric in career_metrics:
        if metric in metrics:
            st.session_state[f"weight_{metric}"] = st.sidebar.slider(f"{metric}", 0.0, 0.3, st.session_state[f"weight_{metric}"], 0.01)
    
    st.subheader("🏫 Campus Life")
    for metric in life_metrics:
        if metric in metrics:
            st.session_state[f"weight_{metric}"] = st.sidebar.slider(f"{metric}", 0.0, 0.3, st.session_state[f"weight_{metric}"], 0.01)
    
    if st.sidebar.button("✅ Auto-Normalize Weights"):
        if total_weight > 0:
            for key in metrics:
                st.session_state[f"weight_{key}"] /= total_weight
            st.rerun()
    
    st.sidebar.info(f"Current Sum: {total_weight:.2f} (Target: 1.00)")

# Calculate Weighted Score
user_weights = [st.session_state[f"weight_{key}"] for key in metrics]
total_w = sum(user_weights)
if total_w > 0:
    normalized_weights = [w/total_w for w in user_weights]
    df['总分'] = sum(df[metric] * weight for metric, weight in zip(metrics, normalized_weights))
else:
    df['总分'] = sum(df[metric] * DEFAULT_WEIGHTS[metric] for metric in metrics)

# --- Ranking Display ---
st.markdown('<div class="section-title">🏆 Overall Rankings (Out of 100)</div>', unsafe_allow_html=True)

with st.expander("📝 Ranking Notes", expanded=False):
    st.markdown("""
    - Rankings are calculated based on your custom weights.
    - Click headers to sort.
    - Scroll horizontally to see full metrics.
    - Select a university below for in-depth analysis.
    """)

df_sorted = df.sort_values("总分", ascending=False).reset_index(drop=True)
df_sorted.index += 1

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div style="text-align: right; color: #666; font-size: 12px; margin-bottom: 5px;">← Swipe to view more →</div>', unsafe_allow_html=True)
    
    # Map column display names for the dataframe
    display_df = df_sorted[["大学", "总分"] + metrics].copy()
    display_df.columns = ["University", "Total Score"] + metrics
    
    st.dataframe(
        display_df.style.format({"Total Score": "{:.1f}", **{m: "{:.1f}" for m in metrics}})
            .background_gradient(cmap='Blues', subset=["Total Score"]),
        height=600, use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- School Details Analysis ---
st.markdown('<div class="section-title">🔍 Detailed Analysis</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_search, col_select = st.columns([2, 3])
    with col_search:
        search_term = st.text_input("🔍 Search University", placeholder="Type name here...", key="school_search")
    with col_select:
        matched_schools = [s for s in df['大学'].unique() if search_term.lower() in s.lower()] if search_term else df['大学'].unique()
        selected_school = st.selectbox("Select University", matched_schools, index=0)
    st.markdown('</div>', unsafe_allow_html=True)

if not df[df["大学"] == selected_school].empty:
    school_data = df[df["大学"] == selected_school].iloc[0]
    rank = int(df_sorted[df_sorted['大学'] == selected_school].index[0])
    
    st.markdown(f"""
    <div class="card" style="background: linear-gradient(135deg, #f5f9ff 0%, #e0e9f8 100%);">
        <h2 style="color: #1a3e72; margin-top: 0;">{selected_school}</h2>
        <div style="font-size: 16px; color: #4a6fa5;">
            <b>Overall Rank:</b> #{rank} | <b>Total Score:</b> {school_data['总分']:.1f}/100
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        core_metrics = ['Academics', 'Safety', 'Happiness', 'Opportunities', 'Learning Opportunities', 'Preparation for Career', 'Academic Reputation']
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[school_data[m] for m in core_metrics], theta=core_metrics, fill='toself', name=selected_school))
        fig_radar.add_trace(go.Scatterpolar(r=[df[m].mean() for m in core_metrics], theta=core_metrics, name='National Avg'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Core Metrics vs National Avg", height=500)
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        learning_metrics = ['Learning Opportunities', 'Preparation for Career', 'Learning Facilities', 'Character Development', 'Recommendation Score', 'Academic Reputation']
        fig_bar_comp = go.Figure()
        fig_bar_comp.add_trace(go.Bar(x=learning_metrics, y=[school_data[m] for m in learning_metrics], name=selected_school))
        fig_bar_comp.add_trace(go.Bar(x=learning_metrics, y=[df[m].mean() for m in learning_metrics], name='National Avg'))
        fig_bar_comp.update_layout(barmode='group', title="Learning & Development (Out of 100)", height=500)
        st.plotly_chart(fig_bar_comp, use_container_width=True)

    with st.expander("📊 View Detailed Data", expanded=True):
        st.markdown("#### Foundation Metrics")
        basic_metrics = {
            'Academics': ('📚', 'Academic Level'), 'Safety': ('🛡️', 'Safety Score'), 
            'Happiness': ('😊', 'Student Happiness'), 'Opportunities': ('💼', 'Growth Ops'),
            'Infrastructure': ('🏛️', 'Facilities'), 'International friendliness': ('🌍', 'Global Friendly'),
            'Location': ('📍', 'Location Score'), 'Social': ('👥', 'Social Life')
        }
        cols = st.columns(3)
        for i, (metric, (icon, name)) in enumerate(basic_metrics.items()):
            with cols[i % 3]:
                delta = school_data[metric] - df[metric].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 24px;">{icon}</span>
                        <div style="text-align: right;">
                            <div style="font-size: 20px; font-weight: bold;">{school_data[metric]:.1f}</div>
                            <div style="font-size: 11px; color: {'green' if delta >=0 else 'red'}">{delta:+.1f} vs Avg</div>
                        </div>
                    </div>
                    <div style="font-size: 14px; color: #4a6fa5;">{name}</div>
                </div>
                """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px;">
    <p>© 2026 Yundao Education Research Institute | Version: v2.3.0</p>
    <p>Rankings are for reference only based on user-defined weights.</p>
</div>
""", unsafe_allow_html=True)
