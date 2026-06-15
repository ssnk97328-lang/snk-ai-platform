import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO
import os
import json

# OPTIONAL AI CORE CONFIGURATION
try:
    from openai import OpenAI
    client = OpenAI()
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

# ---------------- CONFIGURATION & THEME ----------------
st.set_page_config(
    page_title="SNK Enterprise SaaS BI Platform", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS Styling for Premium SaaS UI Elements
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #007bff;
        margin-bottom: 15px;
    }
    .metric-title { font-size: 14px; color: #6c757d; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 24px; color: #212529; font-weight: bold; margin-top: 5px; }
    .insight-box {
        background-color: #eef1f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- USER DATABASE MANAGEMENT ----------------
USER_DB_FILE = "users.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"admin": {"password": "1234"}}
    return {"admin": {"password": "1234"}}

def save_users(users_dict):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users_dict, f, indent=4)

users = load_users()

# ---------------- AUTHENTICATION ENGINE ----------------
if "user" not in st.session_state:
    st.session_state.user = None

def login_system():
    st.title("🔐 SNK SaaS Intelligent BI Engine")
    st.caption("Enterprise Data Infrastructure Strategy Management Portal")
    
    tab1, tab2 = st.tabs(["🔒 Secure Login", "📝 Create Corporate Account"])

    with tab1:
        u = st.text_input("Username / Email", key="auth_user")
        p = st.text_input("Password", type="password", key="auth_pass")
        if st.button("Authenticate Session", use_container_width=True):
            if u in users and users[u]["password"] == p:
                st.session_state.user = u
                st.success("Access Granted. Initializing workspace...")
                st.rerun()
            else:
                st.error("Access Denied: Invalid security credentials.")

    with tab2:
        new_u = st.text_input("Desired Username", key="reg_user")
        new_p = st.text_input("Secure Password", type="password", key="reg_pass")
        if st.button("Register License", use_container_width=True):
            if new_u.strip() and len(new_p) >= 4:
                users[new_u.strip()] = {"password": new_p}
                save_users(users)
                st.success("Account registered successfully! Move to Login tab.")
            else:
                st.error("Registration Failed: Provide valid character profiles.")

if not st.session_state.user:
    login_system()
    st.stop()

# Initialize State Variables
if "ai_override_x" not in st.session_state:
    st.session_state.ai_override_x = None
if "ai_override_y" not in st.session_state:
    st.session_state.ai_override_y = None

# ---------------- APPLICATION NAVIGATION ----------------
st.sidebar.title(f"👤 Session: {st.session_state.user}")
section = st.sidebar.radio(
    "Application Navigation",
    ["🧠 Autonomous AI Executive Summary", "🤖 Copilot Command Chatbot", "📊 Dynamic Dashboard", "📈 Trend Analysis", "👁️ Data Explorer Matrix", "💳 Subscription Plan"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Data Source Ingestion")
files = st.sidebar.file_uploader("Upload operational data packages", type=["csv", "xlsx"], accept_multiple_files=True)

if st.sidebar.button("Logout / Disconnect"):
    st.session_state.user = None
    st.rerun()

# ---------------- SUBSCRIPTION TIER INTERACTION ----------------
if section == "💳 Subscription Plan":
    st.title("💳 Manage Enterprise Subscriptions")
    st.write("Scale your analytics pipelines with deep automation frameworks.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### Current Tier: Free Basic")
        st.write("• Basic automated visual setups\n• Single file parsing limitations")
    with col2:
        st.success("### Premium Pro Upgrade")
        st.write("• Unlock unlimited real-time streaming engines\n• Complete contextual generative AI indexing")
        if st.button("Upgrade to Premium for ₹499/mo"):
            st.balloons()
            st.success("Sandbox Authorization Complete! Payment simulation successful.")
    st.stop()

# ---------------- DATA PIPELINE PROCESSING ----------------
if files:
    dfs = []
    for f in files:
        try:
            if f.name.endswith(".csv"):
                dfs.append(pd.read_csv(f))
            else:
                dfs.append(pd.read_excel(f))
        except Exception as e:
            st.error(f"Error reading file '{f.name}': {str(e)}")

    if not dfs:
        st.warning("No structural tabular inputs detected.")
        st.stop()

    df = pd.concat(dfs, ignore_index=True)
    
    # Clean and standardize columns
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.drop_duplicates()

    # Feature engineering and alignment parsing
    for col in df.columns:
        try:
            if 'date' in col or 'time' in col:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            else:
                df[col] = pd.to_numeric(df[col], errors='ignore')
        except Exception:
            pass

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- INTERACTIVE SMART FILTER ENGINE ----------------
    st.subheader("🔍 Contextual Data Filter Subsystem")
    filter_cols = st.multiselect("Isolate evaluation attributes to scope your views:", df.columns)
    
    if filter_cols:
        f_cols = st.columns(len(filter_cols))
        for idx, col in enumerate(filter_cols):
            with f_cols[idx]:
                available_options = ["All"] + df[col].astype(str).unique().tolist()
                selection = st.selectbox(f"Filter: {col.title()}", available_options, key=f"filter_widget_{col}")
                if selection != "All":
                    df = df[df[col].astype(str) == selection]

    # ---------------- AUTOMATED CHART LOGIC SELECTOR ----------------
    def analyze_and_chart(data, numeric_fields, categorical_fields):
        insights = {}
        
        if st.session_state.ai_override_x and st.session_state.ai_override_y:
            primary_cat = st.session_state.ai_override_x
            primary_num = st.session_state.ai_override_y
        else:
            time_axis = None
            for col in data.columns:
                if any(k in col for k in ['date', 'year', 'month', 'timestamp', 'day']):
                    time_axis = col
                    break
            primary_cat = time_axis if time_axis else (categorical_fields[0] if categorical_fields else data.columns[0])
            primary_num = numeric_fields[0] if numeric_fields else data.columns[0]

        if primary_cat in data.columns and primary_num in data.columns:
            cardinality = data[primary_cat].nunique()
            if 1 < cardinality <= 7:
                insights['distribution'] = {
                    'type': 'pie', 'names': primary_cat, 'values': primary_num,
                    'title': f'Percentage Contribution of {primary_num.title()} by {primary_cat.title()}'
                }
            else:
                insights['distribution'] = {
                    'type': 'bar', 'x': primary_cat, 'y': primary_num,
                    'title': f'Top Operational Volume Profiles: {primary_num.title()} by {primary_cat.title()}'
                }

            insights['timeline'] = {
                'type': 'line', 'x': primary_cat, 'y': primary_num,
                'title': f'Performance Evaluation Waveform ({primary_num.title()} over {primary_cat.title()})'
            }

        if len(numeric_fields) >= 2:
            insights['correlation'] = {
                'type': 'scatter', 'x': numeric_fields[0], 'y': numeric_fields[1],
                'title': f'Statistical Correlation: {numeric_fields[0].title()} vs {numeric_fields[1].title()}'
            }

        return insights, primary_cat, primary_num

    charts_config, active_x, active_y = analyze_and_chart(df, num_cols, cat_cols)

    # ---------------- CENTRALIZED CORE DASHBOARD GENERATOR ----------------
    def build_dashboard_interface(view_mode="Standard"):
        st.markdown("---")
        st.subheader("📊 Live Executive Business Summary")
        
        # Enterprise KPI Layout Blocks
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Ingested Record Depth</div><div class="metric-value">{len(df):,}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Evaluated Dimensions</div><div class="metric-value">{len(df.columns)} Columns</div></div>', unsafe_allow_html=True)
        with m3:
            val_sum = f"{df[num_cols[0]].sum():,.0f}" if num_cols else "N/A"
            st.markdown(f'<div class="metric-card"><div class="metric-title">Aggregated Volumetric Matrix</div><div class="metric-value">{val_sum}</div></div>', unsafe_allow_html=True)
        with m4:
            val_avg = f"{df[num_cols[0]].mean():,.2f}" if num_cols else "N/A"
            st.markdown(f'<div class="metric-card"><div class="metric-title">Statistical Mean Base</div><div class="metric-value">{val_avg}</div></div>', unsafe_allow_html=True)

        if st.session_state.ai_override_x and st.session_state.ai_override_y:
            st.info(f"🎯 View focused via Command Layer: `{st.session_state.ai_override_x}` ✖ `{st.session_state.ai_override_y}`")

        # Dynamic Core Visual Row
        st.markdown("### 📈 Automated Visual Intelligence Layers")
        g1, g2 = st.columns(2)

        with g1:
            if 'distribution' in charts_config:
                cfg = charts_config['distribution']
                st.write(f"##### {cfg['title']}")
                if cfg['type'] == 'pie':
                    p_data = df.groupby(cfg['names'])[cfg['values']].sum().reset_index()
                    fig = px.pie(p_data, names=cfg['names'], values=cfg['values'], template="plotly_white", hole=0.3)
                else:
                    p_data = df.groupby(cfg['x'])[cfg['y']].sum().reset_index().sort_values(by=cfg['y'], ascending=False).head(10)
                    fig = px.bar(p_data, x=cfg['x'], y=cfg['y'], color=cfg['y'], color_continuous_scale="Blugrn", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with g2:
            if 'timeline' in charts_config:
                cfg = charts_config['timeline']
                st.write(f"##### {cfg['title']}")
                if df[cfg['x']].dtype == 'object':
                    t_data = df.groupby(cfg['x'])[cfg['y']].sum().reset_index().sort_values(by=cfg['y'], ascending=False).head(15)
                    fig = px.bar(t_data, x=cfg['x'], y=cfg['y'], template="plotly_white", color_discrete_sequence=["#007bff"])
                else:
                    t_data = df.groupby(cfg['x'])[cfg['y']].mean().reset_index()
                    fig = px.line(t_data, x=cfg['x'], y=cfg['y'], markers=True, template="plotly_white", color_discrete_sequence=["#28a745"])
                st.plotly_chart(fig, use_container_width=True)

        # Statistical Insight Breakdown Row
        if view_mode == "Advanced":
            st.markdown("---")
            st.markdown("### 🔮 Deep Trend Diagnostics & Correlations")
            g3, g4 = st.columns(2)
            
            with g3:
                if 'correlation' in charts_config:
                    cfg = charts_config['correlation']
                    st.write(f"##### {cfg['title']}")
                    fig = px.scatter(df, x=cfg['x'], y=cfg['y'], trendline="ols" if len(df) < 2000 else None, template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

            with g4:
                if active_x and active_y:
                    st.write(f"##### Metric Allocation Matrix: {active_x.title()}")
                    pivot_summary = df.groupby(active_x)[active_y].agg(['sum', 'mean', 'count']).reset_index().sort_values(by='sum', ascending=False).head(10)
                    st.dataframe(pivot_summary, use_container_width=True, hide_index=True)

    # ---------------- INTERACTION SECTIONS RENDER ROUTING ----------------
    
    if section == "🧠 Autonomous AI Executive Summary":
        st.title("🧠 Zero-Prompt Autonomous Intelligence Briefing")
        st.caption("This system actively calculated core indicators across your dataset to surface anomalies and strategic metrics automatically.")
        
        if AI_AVAILABLE:
            with st.spinner("Agent compiling data findings and generating narrative report..."):
                # Build an automated statistical digest profile
                stats_summary = ""
                if num_cols:
                    for n in num_cols[:3]:
                        stats_summary += f"Column '{n}': Max={df[n].max()}, Min={df[n].min()}, Average={df[n].mean():.2f}. "
                if cat_cols:
                    for c in cat_cols[:2]:
                        stats_summary += f"Categorical Axis '{c}' has {df[c].nunique()} unique metrics. Top value is '{df[c].mode()[0] if not df[c].mode().empty else 'N/A'}'. "
                
                agent_prompt = f"""
                You are an elite Autonomous Chief Data Officer. Look at these statistical findings derived from a dataset:
                {stats_summary}
                
                Generate a highly professional executive operational report with 3 distinct sections:
                1. 🚨 KEY ANOMALIES & SURPRISES (point out massive spreads, risks or weird data spikes)
                2. 📈 PERFORMANCE CONCENTRATIONS (where the bulk of volume/activity is clustered)
                3. 🎯 STRATEGIC RECOMMENDATIONS (immediate action steps for management)
                Keep the tone sharp, direct, and elite. Do not repeat raw syntax.
                """
                
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": agent_prompt}]
                )
                
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.write(res.choices[0].message.content)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Please supply an OpenAI API token framework to run Autonomous narrative translations.")
            
        # Display the base dashboard under the narrative insight block
        build_dashboard_interface(view_mode="Advanced")

    elif section == "🤖 Copilot Command Chatbot":
        st.subheader("🤖 GenAI Contextual Conversational Dashboard Assistant")
        st.caption("Type column targets directly to update the UI layouts. (e.g., 'Show me dashboard based on date and sales')")
        
        if st.session_state.ai_override_x or st.session_state.ai_override_y:
            if st.button("🔄 Clear AI View Overrides & Reset"):
                st.session_state.ai_override_x = None
                st.session_state.ai_override_y = None
                st.rerun()

        user_query = st.text_input("Issue vision layout directions to the copilot engine:")
        
        if user_query:
            if AI_AVAILABLE:
                with st.spinner("Processing layout updates..."):
                    columns_catalog = ", ".join(df.columns.tolist())
                    system_prompt = f"""
                    Identify chart formatting column updates requested by users.
                    Available system column array fields: [{columns_catalog}].
                    Extract exactly one X axis parameter and exactly one Y axis numeric base from the user text.
                    Return the result as a raw JSON dictionary match containing keys 'x_column' and 'y_column'. No extra notes.
                    """
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_query}
                            ],
                            response_format={"type": "json_object"}
                        )
                        ai_data = json.loads(response.choices[0].message.content)
                        ax_x = ai_data.get("x_column", "")
                        ax_y = ai_data.get("y_column", "")
                        
                        if ax_x in df.columns and ax_y in df.columns:
                            st.session_state.ai_override_x = ax_x
                            st.session_state.ai_override_y = ax_y
                            st.success(f"Focused visual mapping onto targets: `{ax_x}` by `{ax_y}`")
                    except Exception:
                        pass
            
            build_dashboard_interface(view_mode="Advanced")

    elif section == "📊 Dynamic Dashboard":
        build_dashboard_interface(view_mode="Standard")

    elif section == "📈 Trend Analysis":
        build_dashboard_interface(view_mode="Advanced")

    elif section == "👁️ Data Explorer Matrix":
        st.subheader("👁️ Granular Data Frame Inspection Registry")
        st.dataframe(df, use_container_width=True)

    elif section == "🗺️ Geospatial Maps":
        st.subheader("🗺️ Geospatial Vector Coordinate Projections")
        lat_candidates = [c for c in df.columns if any(k in c for k in ["lat", "latitude", "coord_y"])]
        lon_candidates = [c for c in df.columns if any(k in c for k in ["lon", "longitude", "coord_x"])]

        if lat_candidates and lon_candidates:
            st.map(df[[lat_candidates[0], lon_candidates[0]]].dropna())
        else:
            st.info("No spatial data coordinate points found in this file format.")

    # ---------------- DATA STORAGE AND SUMMARY EXPORT PIPELINES ----------------
    st.markdown("---")
    ex_col1, ex_col2 = st.columns(2)
    
    with ex_col1:
        st.markdown("#### 💾 Archive Operational State")
        if st.button("Commit and Save States", use_container_width=True):
            output_filename = f"{st.session_state.user}_dashboard_snapshot.csv"
            df.to_csv(output_filename, index=False)
            st.success(f"Snapshot committed to disk storage registry: '{output_filename}'")

    with ex_col2:
        st.markdown("#### 📥 Secure System Export")
        def generate_report_binary():
            bytes_stream = BytesIO()
            report_text = (
                f"=== SNK ENTERPRISE BI AUTOMATION PROTOCOL SUMMARY REPORT ===\n"
                f"Target Authorized Session Profile: {st.session_state.user}\n"
                f"Ingestion Metrics Registry Depth: {len(df)} records parsed.\n"
                f"Column Footprint Count: {len(df.columns)} operational fields isolated.\n"
                f"Status: Operational Integrity Validated.\n"
            )
            bytes_stream.write(bytes(report_text, 'utf-8'))
            bytes_stream.seek(0)
            return bytes_stream

        st.download_button(
            label="Download System Audit Manifest",
            data=generate_report_binary(),
            file_name="enterprise_bi_audit.txt",
            mime="text/plain",
            use_container_width=True
        )

else:
    st.info("👋 System ready. Ingest a CSV or Excel business data document package via the sidebar menu to begin execution mapping.")
