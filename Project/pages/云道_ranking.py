import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 初始化设置 ---
st.set_page_config(
    page_title="云道排名系统", 
    page_icon="🏫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏菜单
hide_style = """
<style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- 默认权重配置 ---
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

# --- 加载学生调查问卷数据 ---
@st.cache_data
def load_survey_data():
    try:
        # 假设问卷结果存储在'survey_results.xlsx'文件中
        survey_df = pd.read_excel('data/survey_results.xlsx')
        
        # 检查必要的列是否存在
        required_columns = ['红色', '紫色', '蓝色', '金色', '绿色']
        for col in required_columns:
            if col not in survey_df.columns:
                st.warning(f"问卷数据中缺少'{col}'列，将使用示例数据")
                raise ValueError(f"缺少'{col}'列")
        
        # 提取第一个学生的问卷结果(假设每行是一个学生的问卷)
        student_data = survey_df.iloc[0].to_dict()
        print(student_data)
        # 转换为雷达图需要的数据格式
        radar_data = {
            '红色': student_data.get('红色',10),
            '紫色': student_data.get('紫色',10),
            '蓝色': student_data.get('蓝色',10),
            '金色': student_data.get('金色',10),
            '绿色': student_data.get('绿色',10),
            
        }
        
        return radar_data
    
    except Exception as e:
        st.warning(f"加载问卷数据失败: {str(e)}，将使用示例数据")
        # 返回示例数据
        return {
            '红色': 0,
            '紫色': 0,
            '蓝色': 0,
            '金色': 0,
            '绿色': 0
        }

# --- 数据加载和转换到100分制 ---
@st.cache_data
def load_and_normalize_data():
    df = pd.read_excel('Project/pages/unidata.xlsx') # 学校相关数据
    
    # 确保所有指标都存在
    required_columns = ['大学'] + list(DEFAULT_WEIGHTS.keys())
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"数据文件中缺少必要列: {col}")
    
    # 转换不同量纲的指标到100分制
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

# 加载数据
df = load_and_normalize_data()
metrics = list(DEFAULT_WEIGHTS.keys())
survey_data = load_survey_data()

# --- 在页面顶部添加学生个人关注柱状图 ---
st.markdown('<div class="main-title">🏫 Care4YA云道美国大学排名系统</div>', unsafe_allow_html=True)

# 创建柱状图数据
categories = list(survey_data.keys())
values = list(survey_data.values())

# 创建柱状图
fig_bar = px.bar(
    x=categories,
    y=values,
    color=categories,
    color_discrete_sequence=['#3A7BD5', '#8E54E9', '#00B4DB', '#F46B45', '#F79D00'],
    labels={'x': '关注维度', 'y': '关注指数'},
    title="📊 学生个人关注指数柱状图 (基于问卷结果)"
)

# 更新图表布局
fig_bar.update_layout(
    title={
        'text': "📊 学生个人关注指数柱状图 (基于问卷结果)",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=18)
    },
    xaxis_title="关注维度",
    yaxis_title="关注指数",
    yaxis=dict(range=[0, 6]),  # 保持与雷达图相同的范围
    height=400,
    margin=dict(l=50, r=50, b=50, t=80),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False,
    hovermode="x unified"
)

# 添加数据标签
fig_bar.update_traces(
    texttemplate='%{y}',
    textposition='outside',
    marker_line_color='rgb(8,48,107)',
    marker_line_width=1.5
)

# 显示柱状图
st.plotly_chart(fig_bar, use_container_width=True)

# --- 权重管理模块 ---
def reset_all_weights():
    for key, val in DEFAULT_WEIGHTS.items():
        st.session_state[f"{key}_weight"] = val
        st.session_state[f"slider_{key}"] = val
        st.session_state[f"input_{key}"] = val
    st.rerun()

def init_weights():
    for key, val in DEFAULT_WEIGHTS.items():
        if f"{key}_weight" not in st.session_state:
            st.session_state[f"{key}_weight"] = val

# --- 添加CSS样式 ---
st.markdown("""
<style>
.main-title {
    font-size: 32px !important;
    font-weight: 700 !important;
    color: #1a3e72 !important;
    margin-bottom: 20px !important;
    padding-bottom: 10px;
    border-bottom: 2px solid #e1e5eb;
}

.section-title {
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #2c4e7a !important;
    margin: 25px 0 15px 0 !important;
}

.card {
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    padding: 20px;
    margin-bottom: 20px;
    border-left: 4px solid #3a7bd5;
}

.metric-card {
    background-color: #f8fafc;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 3px solid #3a7bd5;
}

.dataframe {
    border-radius: 8px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
}

.sidebar .sidebar-content {
    background-color: #f8fafc;
    border-right: 1px solid #e1e5eb;
}

.stButton>button {
    border-radius: 6px !important;
    border: 1px solid #3a7bd5 !important;
    background-color: #3a7bd5 !important;
    color: white !important;
}

.stSlider>div>div>div>div {
    background-color: #3a7bd5 !important;
}

.st-bd {
    font-weight: 500 !important;
}

.sidebar-header {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #1a3e72 !important;
    margin-bottom: 15px !important;
    padding-bottom: 5px;
    border-bottom: 1px solid #e1e5eb;
}

/* 新增：固定首列样式 */
[data-testid="stDataFrame-container"] {
    overflow-x: auto;
}

[data-testid="stDataFrame-container"] div[data-testid="stHorizontalBlock"] > div:first-child {
    position: sticky !important;
    left: 0 !important;
    background-color: white !important;
    z-index: 1 !important;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1) !important;
    min-width: 250px !important;
}

[data-testid="stDataFrame-container"] div[data-testid="stHorizontalBlock"] > div:not(:first-child) {
    min-width: 150px !important;
}
</style>
""", unsafe_allow_html=True)

# --- 侧边栏权重控制 ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚖️ 权重配置</div>', unsafe_allow_html=True)
    init_weights()
    
    if st.button("♻️ 恢复默认权重", help="将所有指标权重重置为默认值"):
        reset_all_weights()
    
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(to right, transparent, #e1e5eb, transparent); 
        margin: 10px 0 15px 0;"></div>
    """, unsafe_allow_html=True)
    
    mode = st.radio("调整方式", ["滑块调整", "手动输入"], index=0, horizontal=True)
    
    if mode == "滑块调整":
        st.write("使用滑块调整各维度权重：")
        for key in metrics:
            st.session_state[f"{key}_weight"] = st.slider(
                f"{key} 权重", 0.0, 1.0, st.session_state.get(f"{key}_weight", DEFAULT_WEIGHTS[key]), 0.01,
                key=f"slider_{key}",
                help=f"调整{key}指标的权重"
            )
    
    elif mode == "手动输入":
        st.write("精确输入各维度权重（0.0~1.0）：")
        cols = st.columns(2)
        for i, key in enumerate(metrics):
            with cols[i % 2]:
                st.session_state[f"{key}_weight"] = st.number_input(
                    f"{key} 权重", 0.0, 1.0, st.session_state.get(f"{key}_weight", DEFAULT_WEIGHTS[key]), 0.01,
                    format="%.2f", key=f"input_{key}",
                    help=f"精确设置{key}指标的权重"
                )
    
    st.markdown("---")
    with st.expander("📈 权重统计", expanded=True):
        current_weights = [st.session_state[f"{key}_weight"] for key in metrics]
        total_weight = sum(current_weights)
        
        col1, col2 = st.columns(2)
        col1.metric("当前总权重", f"{total_weight:.2f}", 
                   delta="正常" if 0.99 <= total_weight <= 1.01 else "需调整",
                   delta_color="normal")
        
        if col2.button("自动归一化", help="自动调整所有权重使总和为1"):
            if total_weight > 0:
                for key in metrics:
                    st.session_state[f"{key}_weight"] /= total_weight
                st.rerun()
        
        st.write("各维度实际占比：")
        for key, weight in zip(metrics, current_weights):
            percent = (weight / total_weight) * 100 if total_weight > 0 else 0
            st.progress(percent / 100, text=f"{key}: {weight:.2f} → {percent:.1f}%")

# 计算加权总分
weights = [st.session_state[f"{key}_weight"] for key in metrics]
df['总分'] = sum(df[metric] * weight for metric, weight in zip(metrics, weights))

# 显示排名结果
st.markdown('<div class="section-title">🏆 综合排名 (满分100分)</div>', unsafe_allow_html=True)

# 排名说明
with st.expander("📝 排名说明", expanded=False):
    st.markdown("""
    - 排名基于您设置的权重计算得出
    - 点击表头可排序
    - 左右滑动可查看完整数据
    - 点击学校名称可查看详情
    """)

df_sorted = df.sort_values("总分", ascending=False).reset_index(drop=True)
df_sorted.index += 1

# 使用卡片容器包装表格
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # 添加水平滚动提示
    st.markdown("""
    <div style="text-align: right; color: #666; font-size: 12px; margin-bottom: 5px;">
        ← 左右滑动查看完整数据 →
    </div>
    """, unsafe_allow_html=True)
    
    # 显示数据表格 - 优化后的版本
    st.dataframe(
        df_sorted[["大学", "总分"] + metrics].style
            .format({"总分": "{:.1f}", **{metric: "{:.1f}" for metric in metrics}})
            .background_gradient(cmap='Blues', subset=["总分"])
            .apply(lambda x: ['background: #f8fafc' if x.name % 2 == 0 else '' for i in x], axis=1)
            .set_properties(**{'border': '1px solid #e1e5eb'}),
        height=600,
        use_container_width=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 学校详情分析 ---
st.markdown('<div class="section-title">🔍 学校详情分析</div>', unsafe_allow_html=True)

# 搜索和选择框放在卡片中
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_search, col_select = st.columns([2, 3])
    
    with col_search:
        search_term = st.text_input("🔍 搜索学校", placeholder="输入学校名称关键词...", key="school_search")
        
    with col_select:
        if search_term:
            matched_schools = [s for s in df['大学'].unique() if search_term.lower() in s.lower()]
            if not matched_schools:
                st.warning(f"未找到包含'{search_term}'的学校")
        else:
            matched_schools = df['大学'].unique()
        
        selected_school = st.selectbox(
            "选择学校",
            matched_schools,
            index=0,
            label_visibility="collapsed"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# 学校概览卡片优化
if not df[df["大学"] == selected_school].empty:
    school_data = df[df["大学"] == selected_school].iloc[0]
    rank = int(df_sorted[df_sorted['大学'] == selected_school].index[0])
    
    with st.container():
        st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #f5f9ff 0%, #e0e9f8 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="color: #1a3e72; margin-top: 0;">{selected_school}</h2>
                    <div style="font-size: 16px; color: #4a6fa5;">
                        <span style="font-weight: bold;">综合排名:</span> 第{rank}名 | 
                        <span style="font-weight: bold;">总分:</span> {school_data['总分']:.1f}/100
                    </div>
                </div>
                <div style="font-size: 14px; color: #6b7c93;">
                    数据更新时间: {pd.Timestamp.now().strftime("%Y-%m-%d")}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 创建两列布局：雷达图和柱状图
    col1, col2 = st.columns(2)
    
    with col1:
        # 雷达图 - 显示核心指标
        core_metrics = ['Academics', 'Safety', 'Happiness', 'Opportunities', 
                       'Learning Opportunities', 'Preparation for Career', 'Academic Reputation']
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=[school_data[metric] for metric in core_metrics],
            theta=core_metrics,
            fill='toself',
            name=selected_school,
            line=dict(color='rgb(31,119,180)'),
            fillcolor='rgba(31,119,180,0.2)'
        ))
        
        # 添加平均线
        avg_values = [df[metric].mean() for metric in core_metrics]
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_values,
            theta=core_metrics,
            name='全国平均',
            line=dict(color='rgb(255,127,14)'),
            fillcolor='rgba(255,127,14,0.2)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    color='#4a6fa5'
                ),
                angularaxis=dict(
                    color='#4a6fa5'
                )
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            title=dict(
                text=f"{selected_school} vs 全国平均 (核心指标)",
                x=0.5,
                xanchor="center",
                font=dict(size=16)
            ),
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        # 柱状图比较 - 显示所有学习相关指标
        learning_metrics = ['Learning Opportunities', 'Preparation for Career', 
                          'Learning Facilities', 'Character Development',
                          'Recommendation Score', 'Academic Reputation']
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            x=learning_metrics,
            y=[school_data[metric] for metric in learning_metrics],
            name=selected_school,
            marker_color='rgb(31,119,180)'
        ))
        
        fig_bar.add_trace(go.Bar(
            x=learning_metrics,
            y=[df[metric].mean() for metric in learning_metrics],
            name='全国平均',
            marker_color='rgb(255,127,14)'
        ))
        
        fig_bar.update_layout(
            barmode='group',
            title=dict(
                text='学习相关指标比较 (满分100分)',
                x=0.5,
                xanchor="center",
                font=dict(size=16)
            ),
            yaxis=dict(range=[0, 100]),
            yaxis_title='得分',
            xaxis_title='指标',
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 显示详细数据
    with st.expander("📊 查看详细数据", expanded=True):
        st.markdown('<div class="section-title">详细指标分析</div>', unsafe_allow_html=True)
        
        # 基础指标
        st.markdown("#### 基础指标")
        cols = st.columns(3)
        basic_metrics = {
            'Academics': ('📚', '学术水平', '#3a7bd5'),
            'Safety': ('🛡️', '安全程度', '#4a90e2'), 
            'Happiness': ('😊', '学生幸福感', '#5aa5e9'),
            'Opportunities': ('💼', '发展机会', '#6ab9f0'),
            'Infrastructure': ('🏛️', '基础设施', '#7bc8f7'),
            'International friendliness': ('🌍', '国际友好度', '#8cd7ff'),
            'Location': ('📍', '地理位置', '#9de6ff'),
            'Social': ('👥', '社交生活', '#aef5ff')
        }
        
        for i, (metric, (icon, name, color)) in enumerate(basic_metrics.items()):
            with cols[i % 3]:
                delta = school_data[metric] - df[metric].mean()
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 24px;">{icon}</div>
                        <div style="text-align: right;">
                            <div style="font-size: 24px; font-weight: bold; color: {color};">{school_data[metric]:.1f}</div>
                            <div style="font-size: 12px; color: {'#4caf50' if delta >=0 else '#f44336'}">
                                {delta:+.1f} vs 平均
                            </div>
                        </div>
                    </div>
                    <div style="font-weight: 500; margin-top: 5px; color: #4a6fa5;">{name}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # 学习与发展指标
        st.markdown("#### 学习与发展指标")
        cols = st.columns(3)
        learning_metrics_display = {
            'Learning Opportunities': ('🎓', '学习机会', '#3a7bd5'),
            'Preparation for Career': ('💼', '职业准备', '#4a90e2'),
            'Learning Facilities': ('🏫', '学习设施', '#5aa5e9'),
            'Character Development': ('🧠', '品格发展', '#6ab9f0'),
            'Recommendation Score': ('⭐', '推荐评分', '#7bc8f7'),
            'Academic Reputation': ('🏆', '学术声誉', '#8cd7ff')
        }
        
        for i, (metric, (icon, name, color)) in enumerate(learning_metrics_display.items()):
            with cols[i % 3]:
                delta = school_data[metric] - df[metric].mean()
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 24px;">{icon}</div>
                        <div style="text-align: right;">
                            <div style="font-size: 24px; font-weight: bold; color: {color};">{school_data[metric]:.1f}</div>
                            <div style="font-size: 12px; color: {'#4caf50' if delta >=0 else '#f44336'}">
                                {delta:+.1f} vs 平均
                            </div>
                        </div>
                    </div>
                    <div style="font-weight: 500; margin-top: 5px; color: #4a6fa5;">{name}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # 添加详细数据表格
        st.markdown("### 详细指标数据 (满分100分)")
        detailed_df = pd.DataFrame({
            '指标': metrics,
            '得分': [school_data[metric] for metric in metrics],
            '全国平均': [df[metric].mean() for metric in metrics],
            '差异': [school_data[metric] - df[metric].mean() for metric in metrics]
        })
        st.dataframe(
            detailed_df.style.format({
                '得分': '{:.1f}',
                '全国平均': '{:.1f}',
                '差异': '{:+.1f}'
            }).apply(lambda x: ['color: green' if x['差异'] > 0 else 'color: red' for i in x], axis=1),
            use_container_width=True,
            height=400
        )

# --- 页脚 ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px;">
    <p>© 2023 云道教育研究院 | 数据版本: v2.3.0 (100分制)</p>
    <p>本排名系统根据用户自定义权重计算，结果仅供参考</p>
</div>

""", unsafe_allow_html=True)

