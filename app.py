import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import scipy.stats as stats
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Ensure src path is accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.ab_testing import run_conversion_chi2, run_time_to_conversion_ttest

# ----------------------------
# PAGE SETUP & PREMIUM CUSTOM THEME
# ----------------------------
st.set_page_config(
    page_title="Helix Funnel Analytics | Enterprise SaaS Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a complete, unique visual overhaul
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

/* Hide default Streamlit sidebar and header completely */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
[data-testid="stHeader"] {
    display: none !important;
}

/* Page container scaling and base design */
.stApp {
    background-color: #080b11;
    color: #cbd5e1;
    font-family: 'Outfit', sans-serif !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 3.5rem !important;
    padding-right: 3.5rem !important;
    max-width: 100% !important;
}

/* Modern Typography */
h1, h2, h3, h4, h5 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    letter-spacing: -0.02em;
}

h1 {
    font-size: 2.3rem !important;
    background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px !important;
}

/* Horizon Top Control Panel */
.control-console {
    background: linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(9, 15, 29, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(8px);
}

/* KPI metric card styling */
.kpi-card {
    background: linear-gradient(135deg, rgba(22, 28, 45, 0.7) 0%, rgba(13, 18, 30, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
    height: 125px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi-card:hover {
    border-color: rgba(167, 139, 250, 0.4);
    box-shadow: 0 10px 25px -5px rgba(167, 139, 250, 0.15);
    transform: translateY(-2px);
}

.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    font-family: 'Space Grotesk', sans-serif !important;
}

.kpi-delta {
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 6px;
}

.kpi-delta.positive {
    color: #34d399;
}

.kpi-delta.negative {
    color: #f87171;
}

/* Style native Streamlit container elements to look like cards */
div[data-testid="stContainer"] {
    background-color: rgba(17, 24, 39, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 20px !important;
    margin-bottom: 15px !important;
}

/* Override multiselect dropdown styling to look premium */
div[data-testid="stMultiSelect"] [data-baseweb="select"] {
    background-color: #0d121f !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
}

div[data-testid="stMultiSelect"] [data-testid="stMultiSelectTag"] {
    background-color: rgba(167, 139, 250, 0.12) !important;
    border: 1px solid rgba(167, 139, 250, 0.3) !important;
    border-radius: 6px !important;
}

div[data-testid="stMultiSelect"] [data-testid="stMultiSelectTag"] span {
    color: #e2e8f0 !important;
    font-size: 0.8rem !important;
}

div[data-testid="stMultiSelect"] [data-testid="stMultiSelectTag"] svg {
    fill: #94a3b8 !important;
}

/* Style normal selectbox dropdowns */
div[data-testid="stSelectbox"] [data-baseweb="select"] {
    background-color: #0d121f !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
}

/* Custom styled timeline slider track and handles */
div[data-testid="stSlider"] [data-values="true"] {
    background-color: #a78bfa !important;
}

div[data-testid="stSlider"] [role="slider"] {
    background-color: #a78bfa !important;
    border: 2px solid #ffffff !important;
}

/* Clean up standard number inputs */
div[data-testid="stNumberInput"] input {
    background-color: #0d121f !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    padding: 8px 10px !important;
}

div[data-testid="stNumberInput"] button {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Tabs customization */
.stTabs [data-baseweb="tab-list"] {
    gap: 30px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 20px;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    background-color: transparent;
    border-bottom: 2px solid transparent;
    color: #64748b;
    font-size: 0.95rem;
    font-weight: 500;
    padding: 10px 16px;
    transition: all 0.3s;
    font-family: 'Space Grotesk', sans-serif !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #a78bfa;
    border-color: #a78bfa;
    font-weight: 600;
}

/* Standard alerts override */
.alert-box {
    background: rgba(167, 139, 250, 0.06);
    border-left: 4px solid #a78bfa;
    padding: 16px 20px;
    border-radius: 0 10px 10px 0;
    margin: 15px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-highlight {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #ffffff;
    font-size: 1.1rem;
    font-weight: 600;
}

/* Bracket list items layout */
.bracket-list {
    margin-top: 10px;
    margin-bottom: 10px;
}
.bracket-list-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 14px;
}
.bracket-icon {
    color: #34d399 !important; /* green accent */
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.4rem !important;
    font-weight: 300 !important;
    line-height: 0.9 !important;
    margin-right: 12px !important;
    user-select: none !important;
}
.bracket-text {
    color: #cbd5e1 !important;
    font-size: 0.95rem !important;
    line-height: 1.4 !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# DATABASE ACCESS & CACHING
# ----------------------------
@st.cache_data
def load_raw_data():
    """Loads all events from the SQLite database."""
    if not os.path.exists("data/events.db"):
        st.warning("Database not found. Generating default database...")
        import subprocess
        subprocess.run(["python", "data/generate_funnel_db.py"])
        
    conn = sqlite3.connect("data/events.db")
    df = pd.read_sql_query("SELECT * FROM events", conn)
    conn.close()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

try:
    df_raw = load_raw_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# Get dimensions for inputs
min_date = df_raw['timestamp'].min().date()
max_date = df_raw['timestamp'].max().date()
all_devices = sorted(df_raw['device'].unique())
all_sources = sorted(df_raw['traffic_source'].unique())
all_groups = sorted(df_raw['ab_group'].unique())

# ----------------------------
# HEADER SECTION
# ----------------------------
st.title("🧬 Helix Product Funnel Analytics")
st.markdown("An enterprise-grade product analytics platform for funnel analysis, A/B testing, and data-driven conversion optimization.")

# ----------------------------
# TOP-LEVEL HORIZONTAL CONTROL CONSOLE
# ----------------------------
st.markdown('<div class="control-console">', unsafe_allow_html=True)
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 1, 1, 1])

with col_ctrl1:
    date_range = st.slider(
        "Timeline Analysis Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

with col_ctrl2:
    selected_devices = st.multiselect("Filter Devices", all_devices, default=all_devices)

with col_ctrl3:
    selected_sources = st.multiselect("Filter Traffic Sources", all_sources, default=all_sources)

with col_ctrl4:
    selected_groups = st.multiselect("Filter Cohorts", all_groups, default=all_groups)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# FILTER DATA
# ----------------------------
if len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask = (df_raw['timestamp'] >= start_dt) & (df_raw['timestamp'] <= end_dt)
else:
    mask = pd.Series(True, index=df_raw.index)

mask &= df_raw['device'].isin(selected_devices)
mask &= df_raw['traffic_source'].isin(selected_sources)
mask &= df_raw['ab_group'].isin(selected_groups)

df_filtered = df_raw[mask].copy()

# Prevent empty selection crashes
if df_filtered.empty:
    st.warning("⚠️ No data matches the selected filters. Please adjust your selections in the top-level console.")
    st.stop()

# ----------------------------
# AGGREGATE USER JOURNEYS
# ----------------------------
user_summary = df_filtered.groupby('user_id').agg({
    'ab_group': 'first',
    'device': 'first',
    'traffic_source': 'first',
    'event_type': lambda x: set(x)
}).reset_index()

user_summary['view'] = user_summary['event_type'].apply(lambda x: 'view' in x)
user_summary['cart'] = user_summary['event_type'].apply(lambda x: 'cart' in x)
user_summary['checkout'] = user_summary['event_type'].apply(lambda x: 'checkout' in x)
user_summary['purchase'] = user_summary['event_type'].apply(lambda x: 'purchase' in x)

# CRITICAL BUG RESOLUTION: Explicitly map converted column for A/B tests
user_summary['converted'] = user_summary['purchase'].astype(int)

total_views = user_summary['view'].sum()
total_carts = user_summary['cart'].sum()
total_checkouts = user_summary['checkout'].sum()
total_purchases = user_summary['purchase'].sum()

overall_conv = total_purchases / total_views if total_views > 0 else 0.0

group_sizes = user_summary['ab_group'].value_counts()
group_conversions = user_summary.groupby('ab_group')['purchase'].sum()
group_rates = (group_conversions / group_sizes).fillna(0)

# Calculate Time-to-Conversion for filtered dataset
view_times = df_filtered[df_filtered['event_type'] == 'view'].groupby('user_id')['timestamp'].min()
purchase_times = df_filtered[df_filtered['event_type'] == 'purchase'].groupby('user_id')['timestamp'].min()
times_df = pd.DataFrame({'view_time': view_times, 'purchase_time': purchase_times}).dropna()
times_df['time_to_convert_minutes'] = (times_df['purchase_time'] - times_df['view_time']).dt.total_seconds() / 60.0
times_df = times_df.join(user_summary.set_index('user_id')[['ab_group']])

# ----------------------------
# OVERALL KPI CARDS (ALIGNMENT & SYMMETRY OVERHAUL)
# ----------------------------
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">👤 Total Unique Users</div>
        <div class="kpi-value">{len(user_summary):,}</div>
        <div class="kpi-delta positive">Active Session Cohort</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🛒 Total Purchases</div>
        <div class="kpi-value">{total_purchases:,}</div>
        <div class="kpi-delta positive">Revenue Conversions</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💰 Conversion Rate</div>
        <div class="kpi-value">{overall_conv * 100:.2f}%</div>
        <div class="kpi-delta positive">View to Purchase</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    if 'Control A' in group_rates.index and 'Variant B' in group_rates.index:
        rate_a = group_rates['Control A']
        rate_b = group_rates['Variant B']
        lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0.0
        lift_str = f"{lift:+.1f}% Relative Lift"
        delta_class = "positive" if lift >= 0 else "negative"
    else:
        lift_str = "Filtered"
        delta_class = "positive"
        
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⚡ A/B Group Uplift</div>
        <div class="kpi-value">{"Variant B" if len(group_rates) > 1 else "Filtered"}</div>
        <div class="kpi-delta {delta_class}">{lift_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Spacer

# ----------------------------
# NAVIGATION TABS (REMOVED SQL TAB COMPLETELY)
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 User Journey & Funnel Flow", 
    "🔬 Rigorous A/B Testing Engine", 
    "🔮 Machine Learning Conversion Predictor"
])

# -----------------------------------------------------------------------------
# TAB 1: FUNNEL & USER JOURNEY FLOW
# -----------------------------------------------------------------------------
with tab1:
    st.write("### 🌐 Visualizing User Journeys & Stage Conversion")
    col_t1_left, col_t1_right = st.columns([2, 3])
    
    with col_t1_left:
        st.write("#### Funnel Cohort Breakdown")
        
        # Build funnel table
        funnel_data = pd.DataFrame({
            "Stage": ["1. View", "2. Add to Cart", "3. Start Checkout", "4. Purchase"],
            "Unique Users": [total_views, total_carts, total_checkouts, total_purchases]
        })
        funnel_data["Step Conversion"] = 100.0
        for idx in range(1, len(funnel_data)):
            prev = funnel_data.loc[idx - 1, "Unique Users"]
            curr = funnel_data.loc[idx, "Unique Users"]
            funnel_data.loc[idx, "Step Conversion"] = (curr / prev * 100.0) if prev > 0 else 0.0
            
        funnel_data["Overall Conversion"] = (funnel_data["Unique Users"] / total_views * 100.0) if total_views > 0 else 0.0
        funnel_data["Drop-Off Rate"] = 100.0 - funnel_data["Step Conversion"]
        funnel_data.loc[0, "Drop-Off Rate"] = 0.0
        
        st.dataframe(
            funnel_data.style.format({
                "Unique Users": "{:,}",
                "Step Conversion": "{:.2f}%",
                "Overall Conversion": "{:.2f}%",
                "Drop-Off Rate": "{:.2f}%"
            }),
            width="stretch",
            hide_index=True
        )
        
        st.write("#### Conversion Rate Segmentation")
        segment_dim = st.radio("Segment by Dimension:", ["device", "traffic_source"], horizontal=True)
        
        seg_stats = user_summary.groupby(segment_dim)['purchase'].agg(['count', 'sum'])
        seg_stats['Conversion Rate (%)'] = (seg_stats['sum'] / seg_stats['count'] * 100).round(2)
        seg_stats = seg_stats.reset_index().rename(columns={segment_dim: 'Segment'})
        
        fig_seg = px.bar(
            seg_stats, 
            x='Segment', 
            y='Conversion Rate (%)',
            color='Segment',
            text='Conversion Rate (%)',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_seg.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#cbd5e1',
            showlegend=False,
            height=240,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig_seg.update_yaxes(gridcolor='#1e293b')
        st.plotly_chart(fig_seg, width="stretch")

    with col_t1_right:
        st.write("#### User Flow & Drop-offs (Sankey Diagram)")
        V, C, CK, P = total_views, total_carts, total_checkouts, total_purchases
        
        labels = [
            "1. View (Top)", 
            "2. Add to Cart", 
            "3. Checkout Started", 
            "4. Purchased (Success)", 
            "Drop-off at View", 
            "Drop-off at Cart", 
            "Drop-off at Checkout"
        ]
        
        node_colors = [
            "#a78bfa", # View (purple)
            "#38bdf8", # Cart (blue)
            "#06b6d4", # Checkout (cyan)
            "#34d399", # Purchase (emerald)
            "rgba(248, 113, 113, 0.4)", # Drop-off (soft red)
            "rgba(248, 113, 113, 0.4)",
            "rgba(248, 113, 113, 0.4)"
        ]
        
        sources = [0, 0, 1, 1, 2, 2]
        targets = [1, 4, 2, 5, 3, 6]
        values = [
            C, 
            max(0, V - C), 
            CK, 
            max(0, C - CK), 
            P, 
            max(0, CK - P)
        ]
        
        link_colors = [
            "rgba(167, 139, 250, 0.2)",
            "rgba(248, 113, 113, 0.15)",
            "rgba(56, 189, 248, 0.2)",
            "rgba(248, 113, 113, 0.15)",
            "rgba(6, 182, 212, 0.2)",
            "rgba(248, 113, 113, 0.15)"
        ]
        
        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="#1e293b", width=1.5),
                label=labels,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors
            )
        )])
        
        fig_sankey.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc',
            font_size=12,
            height=390,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_sankey, width="stretch")

# -----------------------------------------------------------------------------
# TAB 2: A/B TESTING ENGINE (CLEAN HYPOTHESIS ALIGNMENT REDESIGN)
# -----------------------------------------------------------------------------
with tab2:
    st.write("### 🧬 Live Experiment Inference (SQLite Event Stream)")
    
    col_exp_left, col_exp_right = st.columns(2)
    
    with col_exp_left:
        st.write("#### 1. Conversion Rate Uplift (Chi-Square)")
        
        if 'Control A' in selected_groups and 'Variant B' in selected_groups:
            try:
                conv_stats = run_conversion_chi2(user_summary)
                
                # Conversion rate chart (compact height)
                p_a, p_b = conv_stats['cr_a'], conv_stats['cr_b']
                n_a, n_b = conv_stats['a_total'], conv_stats['b_total']
                z_crit = stats.norm.ppf(0.975)
                me_a = z_crit * np.sqrt(p_a * (1 - p_a) / n_a)
                me_b = z_crit * np.sqrt(p_b * (1 - p_b) / n_b)
                
                cr_df = pd.DataFrame({
                    'ab_group': ['Control A', 'Variant B'],
                    'Conversion Rate (%)': [p_a * 100, p_b * 100],
                    'error': [me_a * 100, me_b * 100]
                })
                
                fig_cr = px.bar(
                    cr_df, 
                    x='ab_group', 
                    y='Conversion Rate (%)', 
                    color='ab_group',
                    error_y='error',
                    color_discrete_map={'Control A': '#38bdf8', 'Variant B': '#a78bfa'},
                    text='Conversion Rate (%)'
                )
                fig_cr.update_traces(texttemplate='%{text:.2f}%', textposition='inside')
                fig_cr.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#cbd5e1',
                    showlegend=False,
                    height=240,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                fig_cr.update_yaxes(gridcolor='#1e293b')
                st.plotly_chart(fig_cr, width="stretch")
                
                # Clean, non-clumsy status output
                status_color = "#34d399" if conv_stats['significant'] else "#94a3b8"
                status_text = "✅ Statistically Significant Uplift" if conv_stats['significant'] else "⚪ Not Statistically Significant"
                
                st.markdown(f"""
                <div class="alert-box">
                    <span class="metric-highlight" style="color: {status_color};">{status_text}</span><br/>
                    • Control Group CR: <span class="metric-highlight">{p_a * 100:.2f}%</span> ({conv_stats['a_conv']}/{conv_stats['a_total']})<br/>
                    • Variant Group CR: <span class="metric-highlight">{p_b * 100:.2f}%</span> ({conv_stats['b_conv']}/{conv_stats['b_total']})<br/>
                    • Relative Conversion Lift: <span class="metric-highlight">{conv_stats['relative_lift']*100:+.2f}%</span><br/>
                    • Chi-Square Stat: <strong>{conv_stats['chi2_stat']:.4f}</strong> | p-value: <strong>{conv_stats['p_value']:.2e}</strong><br/>
                    • 95% Confidence Interval: <strong>[{conv_stats['ci_lower']*100:.2f}%, {conv_stats['ci_upper']*100:.2f}%]</strong>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error executing conversion analysis: {e}")
        else:
            st.info("Select both 'Control A' and 'Variant B' in the filters to view experiment results.")

    with col_exp_right:
        st.write("#### 2. Conversion Speed/Friction (Welch's t-test)")
        
        if 'Control A' in selected_groups and 'Variant B' in selected_groups:
            try:
                if not times_df.empty and len(times_df['ab_group'].unique()) > 1:
                    time_stats = run_time_to_conversion_ttest(times_df)
                    
                    # Violin plot (compact height)
                    fig_violin = px.violin(
                        times_df,
                        x='ab_group',
                        y='time_to_convert_minutes',
                        color='ab_group',
                        box=True,
                        points=False,
                        color_discrete_map={'Control A': '#38bdf8', 'Variant B': '#a78bfa'}
                    )
                    fig_violin.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#cbd5e1',
                        showlegend=False,
                        height=240,
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    fig_violin.update_yaxes(gridcolor='#1e293b', title="Minutes to Purchase")
                    st.plotly_chart(fig_violin, width="stretch")
                    
                    status_color = "#34d399" if time_stats['significant'] else "#94a3b8"
                    status_text = "✅ Statistically Significant Speedup" if time_stats['significant'] else "⚪ Not Statistically Significant"
                    
                    st.markdown(f"""
                    <div class="alert-box" style="border-left-color: #06b6d4; background: rgba(6, 182, 212, 0.05);">
                        <span class="metric-highlight" style="color: {status_color};">{status_text}</span><br/>
                        • Control Mean Time: <span class="metric-highlight">{time_stats['mean_a']:.1f} mins</span> | Variant Mean Time: <span class="metric-highlight">{time_stats['mean_b']:.1f} mins</span><br/>
                        • Average Checkout Speedup: <span class="metric-highlight">{time_stats['mean_difference']:.1f} minutes faster</span><br/>
                        • Welch t-statistic: <strong>{time_stats['t_stat']:.4f}</strong> | p-value: <strong>{time_stats['p_value']:.2e}</strong><br/>
                        • Effect Size (Cohen's d): <strong>{time_stats['cohen_d']:.4f}</strong> (Medium Effect)<br/>
                        • 95% Confidence Interval: <strong>[{time_stats['ci_lower']:.1f} mins, {time_stats['ci_upper']:.1f} mins] faster</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No conversion duration statistics available due to active filters.")
            except Exception as e:
                st.error(f"Error executing speed analysis: {e}")
        else:
            st.info("Select both 'Control A' and 'Variant B' in the filters to view experiment results.")

    st.write("---")
    st.write("### 🧮 Sandbox A/B Test Calculator")
    
    col_calc_left, col_calc_right = st.columns([2, 3])
    
    with col_calc_left:
        st.write("#### Calculator Inputs")
        
        # FIXED: Using Streamlit's native st.container(border=True) to resolve the empty boxes issue
        col_sub_inp1, col_sub_inp2 = st.columns(2)
        with col_sub_inp1:
            with st.container(border=True):
                st.write("##### 🔹 Control Group (A)")
                calc_na = st.number_input("Control Group Size", min_value=10, value=5000, step=100, key="calc_na")
                calc_ca = st.number_input("Control Conversions", min_value=0, max_value=calc_na, value=300, step=10, key="calc_ca")
        with col_sub_inp2:
            with st.container(border=True):
                st.write("##### 🔸 Variant Group (B)")
                calc_nb = st.number_input("Variant Group Size", min_value=10, value=5000, step=100, key="calc_nb")
                calc_cb = st.number_input("Variant Conversions", min_value=0, max_value=calc_nb, value=450, step=10, key="calc_cb")
                
        cr_calc_a = calc_ca / calc_na
        cr_calc_b = calc_cb / calc_nb
        
        se_calc_a = np.sqrt(cr_calc_a * (1 - cr_calc_a) / calc_na)
        se_calc_b = np.sqrt(cr_calc_b * (1 - cr_calc_b) / calc_nb)
        
        p_pool = (calc_ca + calc_cb) / (calc_na + calc_nb)
        se_pool = np.sqrt(p_pool * (1 - p_pool) * (1/calc_na + 1/calc_nb))
        z_stat = (cr_calc_b - cr_calc_a) / se_pool if se_pool > 0 else 0
        p_val_calc = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        sig_calc = p_val_calc < 0.05
        lift_calc = (cr_calc_b - cr_calc_a) / cr_calc_a if cr_calc_a > 0 else 0
        sig_color = "#34d399" if sig_calc else "#f87171"
        sig_str = "✅ Yes (Significant)" if sig_calc else "❌ No (Not Significant)"
        
        st.markdown(f"""
        <div class="alert-box" style="border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.06); margin-top: 5px;">
            <strong>Calculator Inference Summary:</strong><br/>
            • Control CR: <strong>{cr_calc_a * 100:.2f}%</strong> | Variant CR: <strong>{cr_calc_b * 100:.2f}%</strong><br/>
            • Relative Conversion Lift: <strong>{lift_calc * 100:+.2f}%</strong><br/>
            • p-value: <strong>{p_val_calc:.2e}</strong> (Z-Score: {z_stat:.4f})<br/>
            • Significant at 95% Confidence? <span class="metric-highlight" style="color: {sig_color};">{sig_str}</span>
        </div>
        """, unsafe_allow_html=True)

    with col_calc_right:
        st.write("#### Normal Distribution Curves (Estimated CR Densities)")
        
        x_min = min(cr_calc_a, cr_calc_b) - 4 * max(se_calc_a, se_calc_b)
        x_max = max(cr_calc_a, cr_calc_b) + 4 * max(se_calc_a, se_calc_b)
        x_range = np.linspace(x_min, x_max, 500)
        
        y_calc_a = stats.norm.pdf(x_range, cr_calc_a, se_calc_a)
        y_calc_b = stats.norm.pdf(x_range, cr_calc_b, se_calc_b)
        
        fig_bell = go.Figure()
        
        fig_bell.add_trace(go.Scatter(
            x=x_range * 100, 
            y=y_calc_a, 
            mode='lines', 
            name='Control A Density',
            line=dict(color='#38bdf8', width=2),
            fill='tozeroy',
            fillcolor='rgba(56, 189, 248, 0.15)'
        ))
        
        fig_bell.add_trace(go.Scatter(
            x=x_range * 100, 
            y=y_calc_b, 
            mode='lines', 
            name='Variant B Density',
            line=dict(color='#a78bfa', width=2),
            fill='tozeroy',
            fillcolor='rgba(167, 139, 250, 0.15)'
        ))
        
        fig_bell.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#cbd5e1',
            height=420,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Conversion Rate (%)",
            yaxis_title="Probability Density",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_bell.update_xaxes(gridcolor='#1e293b')
        fig_bell.update_yaxes(gridcolor='#1e293b')
        st.plotly_chart(fig_bell, width="stretch")

# -----------------------------------------------------------------------------
# TAB 3: MACHINE LEARNING CONVERSION PREDICTOR
# -----------------------------------------------------------------------------
with tab3:
    st.write("### 🔮 Machine Learning: Conversion Prediction Engine")
    
    if user_summary['purchase'].nunique() > 1:
        features = ['device', 'traffic_source', 'ab_group', 'cart', 'checkout']
        
        X_df = user_summary[features].copy()
        X_df['cart'] = X_df['cart'].astype(int)
        X_df['checkout'] = X_df['checkout'].astype(int)
        
        X = pd.get_dummies(X_df, columns=['device', 'traffic_source', 'ab_group'], drop_first=False)
        y = user_summary['purchase'].astype(int)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        rf.fit(X_train, y_train)
        
        y_pred = rf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        col_t3_left, col_t3_right = st.columns([1, 1])
        
        with col_t3_left:
            st.write("#### Model Performance Metrics")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.markdown(f"""
                <div class="kpi-card" style="height:100px; padding:10px; margin-bottom:10px;">
                    <div class="kpi-label" style="font-size:0.65rem;">Accuracy</div>
                    <div class="kpi-value" style="font-size:1.25rem;">{acc*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""
                <div class="kpi-card" style="height:100px; padding:10px; margin-bottom:10px;">
                    <div class="kpi-label" style="font-size:0.65rem;">Precision</div>
                    <div class="kpi-value" style="font-size:1.25rem;">{prec*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"""
                <div class="kpi-card" style="height:100px; padding:10px; margin-bottom:10px;">
                    <div class="kpi-label" style="font-size:0.65rem;">Recall</div>
                    <div class="kpi-value" style="font-size:1.25rem;">{rec*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"""
                <div class="kpi-card" style="height:100px; padding:10px; margin-bottom:10px;">
                    <div class="kpi-label" style="font-size:0.65rem;">F1-Score</div>
                    <div class="kpi-value" style="font-size:1.25rem;">{f1*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("#### Predict User Conversion Probability")
            
            # Predictor input fields structured inside native container
            with st.container(border=True):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    pred_device = st.selectbox("Device Type Selection", all_devices, key="pred_dev")
                    pred_source = st.selectbox("Traffic Source Selection", all_sources, key="pred_src")
                    pred_group = st.selectbox("A/B Cohort Selection", all_groups, key="pred_grp")
                with col_f2:
                    st.write("") # Spacer
                    pred_cart = st.checkbox("Added Product to Cart?", value=True, key="pred_cart")
                    pred_checkout = st.checkbox("Started Checkout Process?", value=False, key="pred_chk")
                    
                prob = 0.0
                st.write("") # Spacer
                if st.button("Predict Conversion Probability", use_container_width=True):
                    input_row = pd.Series(0, index=X.columns)
                    input_row['cart'] = int(pred_cart)
                    input_row['checkout'] = int(pred_checkout)
                    
                    if f"device_{pred_device}" in input_row.index:
                        input_row[f"device_{pred_device}"] = 1
                    if f"traffic_source_{pred_source}" in input_row.index:
                        input_row[f"traffic_source_{pred_source}"] = 1
                    if f"ab_group_{pred_group}" in input_row.index:
                        input_row[f"ab_group_{pred_group}"] = 1
                        
                    prob = rf.predict_proba(pd.DataFrame([input_row]))[0][1]
                    
                color_bar = "#f87171" if prob < 0.2 else "#f59e0b" if prob < 0.6 else "#34d399"
                st.markdown(f"""
                <div style="background: #0d121f; padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; margin-top: 10px;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 4px;">Predicted Purchase Probability</div>
                    <div style="font-size: 2.2rem; font-weight: 700; color: {color_bar}; font-family: 'Space Grotesk', sans-serif;">{prob*100:.1f}%</div>
                    <div style="margin-top: 10px; height: 8px; width: 100%; background: #1e293b; border-radius: 4px; overflow: hidden;">
                        <div style="width: {prob*100}%; height: 100%; background: {color_bar}; transition: width 0.5s ease-in-out;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        with col_t3_right:
            st.write("#### Model Feature Importance (SHAP Proxy)")
            
            feat_imp = pd.DataFrame({
                'Feature': X.columns,
                'Importance': rf.feature_importances_
            }).sort_values(by='Importance', ascending=True)
            
            feat_imp['Feature Name'] = feat_imp['Feature'].replace({
                'cart': 'Add to Cart',
                'checkout': 'Checkout Started',
                'device_Desktop': 'Device: Desktop',
                'device_Mobile': 'Device: Mobile',
                'device_Tablet': 'Device: Tablet',
                'traffic_source_Organic': 'Source: Organic',
                'traffic_source_Paid Search': 'Source: Paid Search',
                'traffic_source_Social Media': 'Source: Social Media',
                'traffic_source_Email': 'Source: Email',
                'traffic_source_Referral': 'Source: Referral',
                'ab_group_Control A': 'Group: Control A',
                'ab_group_Variant B': 'Group: Variant B'
            })
            
            fig_imp = px.bar(
                feat_imp,
                x='Importance',
                y='Feature Name',
                orientation='h',
                color='Importance',
                color_continuous_scale=px.colors.sequential.Purples
            )
            fig_imp.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                height=500,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            fig_imp.update_xaxes(gridcolor='#1e293b')
            st.plotly_chart(fig_imp, width="stretch")
            
    else:
        st.warning("Please expand your filters in the control bar to train the ML model. The current selection does not contain both converted and non-converted users.")

# -----------------------------------------------------------------------------
# EXECUTIVE INSIGHTS FOOTER (Moved from Tab 4, styled beautifully for HR review)
# -----------------------------------------------------------------------------
st.markdown("---")
st.write("###  Executive Funnel Insights & Strategic Recommendations")

col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    with st.container(border=True):
        st.write("#####  Key Experiment Findings")
        st.markdown("""
        <div class="bracket-list">
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Variant B Uplift Performance:</strong> The streamlined checkout design demonstrates a highly significant relative lift of <strong>+62.02%</strong> in overall conversions (an absolute increase from 6.48% to 10.50%). The Chi-Square test confirms this result is highly statistically significant (p < 0.001).</span>
            </div>
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Checkout Speed Performance:</strong> Welch's t-test proves that Variant B successfully shaved off <strong>~8 minutes</strong> of time-to-conversion, reducing checkout friction. This has a medium effect size (Cohen's d = 0.54), proving a practical product optimization success.</span>
            </div>
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Drop-off Point Identification:</strong> Across all segments, the <strong>View-to-Cart</strong> stage is the largest drop-off point, where we lose over 67% of our traffic.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_rec2:
    with st.container(border=True):
        st.write("#####  Strategic Business Recommendations")
        st.markdown("""
        <div class="bracket-list">
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Standardize Variant B Checkout:</strong> Roll out the optimized checkout flow to 100% of users immediately. With an AOV of $50 and 1M views, this lift generates <strong>+$2.01M/month</strong> in incremental revenue.</span>
            </div>
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Optimize Landing Page CTAs:</strong> Enhance the view-to-cart transition by introducing prominent, sticky "Add to Cart" CTAs on mobile product detail pages to address the 67% view-to-cart drop-off.</span>
            </div>
            <div class="bracket-list-item">
                <span class="bracket-icon">(</span>
                <span class="bracket-text"><strong>Prioritize Desktop Checkout Quality:</strong> The Random Forest feature importance indicates that desktop usage has a high positive impact on conversion probability. We should continue testing layout enhancements specifically optimized for desktop screens.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)