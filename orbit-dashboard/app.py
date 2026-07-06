import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# 1. SETUP PAGE
st.set_page_config(page_title="Orbit Ecosystem | Impact Dashboard", page_icon="🚀", layout="wide")

# Get absolute path to the directory where app.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. SIDEBAR: TOGGLES & DYNAMIC LOGOS
company = st.sidebar.radio("🏢 Select Organization", ["Orbit Innovation Hub", "Orbit Health"])

# Bulletproof logo paths
oih_logo = os.path.join(BASE_DIR, "oih_logo.png")
oh_logo = os.path.join(BASE_DIR, "oh_logo.png")

if company == "Orbit Innovation Hub" and os.path.exists(oih_logo):
    st.sidebar.image(oih_logo, use_container_width=True)
elif company == "Orbit Health" and os.path.exists(oh_logo):
    st.sidebar.image(oh_logo, use_container_width=True)
else:
    st.sidebar.title(company)

st.sidebar.divider()

platform = st.sidebar.selectbox("📱 Select Platform", ["LinkedIn", "Facebook", "X (Twitter)", "Telegram", "TikTok", "Instagram"])

st.sidebar.divider()

# 3. SMART SCALABLE DATA LOADER
@st.cache_data
def load_csv(company_name, platform_name, filename, skip_rows=0, date_col=None):
    comp_folder = company_name.replace(" ", "_")
    plat_folder = "X" if platform_name == "X (Twitter)" else platform_name
    
    # This precisely maps to your new structure: data/Orbit_Innovation_Hub/LinkedIn/filename.csv
    filepath = os.path.join(BASE_DIR, "data", comp_folder, plat_folder, filename)
    
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, skiprows=skip_rows)
            if date_col and date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.dropna(subset=[date_col]).sort_values(date_col)
            return df
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()

# Load datasets
df_metrics = load_csv(company, platform, "Content - Metrics.csv", skip_rows=1, date_col="Date")
df_posts = load_csv(company, platform, "Content - All posts.csv", skip_rows=1, date_col="Created date")
df_competitors = load_csv(company, platform, "Competitor Analytics - COMPETITORS.csv", skip_rows=1)
df_visitors = load_csv(company, platform, "Visitors - Visitor metrics.csv", date_col="Date")
df_followers_growth = load_csv(company, platform, "Followers - New followers.csv", date_col="Date")

# 4. DUAL-SYNCED DATE FILTERS
st.sidebar.subheader("📅 Filter by Specific Dates")

# Set safe defaults
min_date, max_date = datetime.date(2025, 1, 1), datetime.date(2026, 12, 31)
if not df_metrics.empty:
    min_date = df_metrics['Date'].min().date()
    max_date = df_metrics['Date'].max().date()

# Initialize session state for synced dates
if "date_range" not in st.session_state:
    st.session_state.date_range = (min_date, max_date)

# Callback functions to sync calendar and slider
def sync_from_slider():
    st.session_state.date_range = st.session_state.slider_key

def sync_from_calendar():
    if len(st.session_state.cal_key) == 2:
        st.session_state.date_range = st.session_state.cal_key

st.sidebar.slider(
    "Drag to select dates:",
    min_value=min_date, max_value=max_date,
    key="slider_key",
    value=st.session_state.date_range,
    on_change=sync_from_slider
)

st.sidebar.date_input(
    "Or type/click specific dates:",
    min_value=min_date, max_value=max_date,
    key="cal_key",
    value=st.session_state.date_range,
    on_change=sync_from_calendar
)

start_date, end_date = st.session_state.date_range

# Apply filters
if not df_metrics.empty:
    df_metrics = df_metrics[(df_metrics['Date'].dt.date >= start_date) & (df_metrics['Date'].dt.date <= end_date)]
if not df_posts.empty:
    df_posts = df_posts[(df_posts['Created date'].dt.date >= start_date) & (df_posts['Created date'].dt.date <= end_date)]
if not df_visitors.empty:
    df_visitors = df_visitors[(df_visitors['Date'].dt.date >= start_date) & (df_visitors['Date'].dt.date <= end_date)]

# 5. HEADER & TOP KPIs
st.title(f"🚀 {company} Impact Dashboard")
st.write(f"Currently viewing analytics for **{platform}**")

col1, col2, col3, col4 = st.columns(4)

# Dynamic Follower KPI
if not df_followers_growth.empty:
    # Use .sum() to calculate all followers accumulated in the selected date range
    accumulated_followers = df_followers_growth['Total followers'].sum()
    
    # Optional: If you prefer to show your absolute page total (9,884) with the accumulated amount as the green arrow, you can use this:
    if company == "Orbit Innovation Hub" and platform == "LinkedIn":
        col1.metric(label=f"Total {platform} Followers", value="9,884", delta=f"+{accumulated_followers:,.0f} in selected dates")
    else:
        # For all other platforms, it will just show the accumulated sum as the main number
        col1.metric(label=f"Accumulated {platform} Followers", value=f"{accumulated_followers:,.0f}", delta="In selected date range")
else:
    col1.metric(label=f"Accumulated {platform} Followers", value="No data", delta="--")

# 6. PROGRESSIVE DISCLOSURE: TABS
tab1, tab2, tab3, tab4 = st.tabs(["📊 Content Performance", "👥 Audience Demographics", "📈 Traffic & Growth", "🏆 Competitors"])

# --- TAB 1: CONTENT PERFORMANCE ---
with tab1:
    st.subheader(f"{platform} Engagement Trends")
    if not df_metrics.empty:
        metric_choice = st.selectbox(
            "Select Metric to Visualize:", 
            ["Impressions (total)", "Clicks (total)", "Reactions (total)", "Comments (total)"]
        )
        
        fig_metrics = px.line(df_metrics, x="Date", y=metric_choice, markers=True)
        fig_metrics.update_traces(line_color='#005B5C')
        st.plotly_chart(fig_metrics, use_container_width=True)
        
    if not df_posts.empty:
        with st.expander("📂 View Top Performing Posts (Raw Data)"):
            display_cols = ['Created date', 'Post title', 'Impressions', 'Clicks', 'Engagement rate']
            st.dataframe(df_posts[display_cols].sort_values(by="Impressions", ascending=False), use_container_width=True)

# --- TAB 2: AUDIENCE DEMOGRAPHICS ---
with tab2:
    st.subheader(f"Who is in our {platform} ecosystem?")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        user_type = st.radio("Select Audience Type:", ["Followers", "Visitors"])
    with col_b:
        demo_category = st.radio("Select Demographic Category:", ["Seniority", "Job function", "Company size", "Industry", "Location"], horizontal=True)
    
    demo_file = f"{user_type} - {demo_category}.csv"
    df_demo = load_csv(company, platform, demo_file)
    
    if not df_demo.empty:
        y_col = "Total followers" if user_type == "Followers" else "Total views"
        df_demo = df_demo.sort_values(by=y_col, ascending=False).head(15)
        
        if demo_category == "Company size":
            fig_demo = px.pie(df_demo, names=demo_category, values=y_col, color_discrete_sequence=px.colors.sequential.Teal)
        else:
            fig_demo = px.bar(df_demo, x=demo_category, y=y_col, color_discrete_sequence=['#005B5C'])
            
        st.plotly_chart(fig_demo, use_container_width=True)
        with st.expander(f"📂 View raw {user_type} {demo_category} data"):
            st.dataframe(df_demo, use_container_width=True)
    else:
        st.info(f"Demographic data for '{demo_file}' is not yet available for {platform}.")

# --- TAB 3: TRAFFIC & GROWTH ---
with tab3:
    if not df_visitors.empty:
        st.subheader("Page Traffic (Desktop vs Mobile)")
        fig_traffic = px.area(df_visitors, x="Date", y=["Total page views (mobile)", "Total page views (desktop)"], 
                              color_discrete_sequence=['#005B5C', '#A3D9D3'])
        st.plotly_chart(fig_traffic, use_container_width=True)
    else:
        st.info("Traffic data not available.")

# --- TAB 4: COMPETITORS ---
with tab4:
    if not df_competitors.empty:
        st.subheader("How do we stack up?")
        fig_comp = px.bar(df_competitors, x="Page", y="New Followers", color="Page", 
                          title="New Followers vs Competitors", color_discrete_sequence=['#005B5C', '#6c757d'])
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Competitor data not available.")
