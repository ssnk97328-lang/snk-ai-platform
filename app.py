import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO
import os
import json

# OPTIONAL AI
try:
    from openai import OpenAI
    client = OpenAI()
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SNK SaaS BI Platform", layout="wide")

# ---------------- USER DATABASE ----------------
USER_DB_FILE = "users.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {"admin": {"password": "1234"}}
    return {"admin": {"password": "1234"}}

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    st.title("🔐 SNK SaaS Platform")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if u in users and users[u]["password"] == p:
                st.session_state.user = u
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_u = st.text_input("New Username", key="signup_user")
        new_p = st.text_input("New Password", type="password", key="signup_pass")
        if st.button("Signup"):
            if new_u:
                users[new_u] = {"password": new_p}
                save_users(users)
                st.success("User created successfully! Please login.")
            else:
                st.error("Username cannot be empty")

if not st.session_state.user:
    login()
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title(f"👤 {st.session_state.user}")

section = st.sidebar.radio(
    "Navigation",
    ["All View", "Dashboard", "Sales", "AI Tool", "Maps", "💳 Upgrade"]
)

files = st.sidebar.file_uploader("Upload Files", type=["csv","xlsx"], accept_multiple_files=True)

# ---------------- PAYMENT MOCK ----------------
if section == "💳 Upgrade":
    st.title("💳 Upgrade Plan")
    st.write("Unlock full features 🚀")
    if st.button("Pay ₹499 (Demo)"):
        st.success("Payment Successful (Mock)")
    st.stop()

# ---------------- DATA PROCESSING ----------------
if files:
    dfs = []
    for f in files:
        if f.name.endswith(".csv"):
            dfs.append(pd.read_csv(f))
        else:
            dfs.append(pd.read_excel(f))

    df = pd.concat(dfs, ignore_index=True)
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
    df = df.fillna("Unknown").drop_duplicates()

    # Smart numeric conversion
    for col in df.columns:
        try:
            converted = pd.to_numeric(df[col], errors="raise")
            df[col] = converted
        except:
            pass

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- GLOBAL FILTERS ----------------
    st.subheader("🔍 Smart Filters")
    filter_cols = st.multiselect("Select Columns to Filter Data", df.columns)
    
    if filter_cols:
        col_layouts = st.columns(len(filter_cols))
        for idx, col in enumerate(filter_cols):
            with col_layouts[idx]:
                val = st.selectbox(f"Filter {col}", ["All"] + df[col].astype(str).unique().tolist(), key=f"filt_{col}")
                if val != "All":
                    df = df[df[col].astype(str) == val]

    # ---------------- SMART AUTO-CHART ENGINE ----------------
    def get_auto_charts(dataframe, numeric_columns, categorical_columns):
        """
        Analyzes dataframe structure and automatically determines the 
        best X, Y fields and chart layouts for the visualization layout.
        """
        suggestions = {}
        
        # Look for potential Date/Time columns first
        time_col = None
        for col in dataframe.columns:
            if 'date' in col or 'year' in col or 'month' in col or 'time' in col:
                time_col = col
                break
                
        # Fallback categorical and numerical setups
        best_cat = categorical_columns[0] if categorical_columns else (dataframe.columns[0] if len(dataframe.columns) > 0 else None)
        best_num = numeric_columns[0] if numeric_columns else None
        
        # Rule 1: Trend Line (Time Series)
        if time_col and best_num:
            suggestions['trend'] = {'x': time_col, 'y': best_num, 'type': 'line', 'title': f'Trend of {best_num.title()} over {time_col.title()}'}
        elif len(numeric_columns) >= 1:
            # Fallback trend line using index sequence
            suggestions['trend'] = {'x': dataframe.index.name if dataframe.index.name else 'Index', 'y': best_num, 'type': 'line', 'title': f'{best_num.title()} Distribution Trend'}

        # Rule 2: Distribution/Composition (Pie or Bar based on unique values)
        if best_cat and best_num:
            unique_count = dataframe[best_cat].nunique()
            # If low unique values (2 to 7), a Pie Chart is clean and perfect
            if 1 < unique_count <= 7:
                suggestions['composition'] = {'names': best_cat, 'values': best_num, 'type': 'pie', 'title': f'Composition Breakup of {best_num.title()} by {best_cat.title()}'}
            else:
                # Top 10 High-impact distribution bar chart
                suggestions['composition'] = {'x': best_cat, 'y': best_num, 'type': 'bar', 'title': f'Top Results of {best_num.title()} by {best_cat.title()}'}

        # Rule 3: Correlation (Scatter Matrix)
        if len(numeric_columns) >= 2:
            suggestions['correlation'] = {'x': numeric_columns[0], 'y': numeric_columns[1], 'type': 'scatter', 'title': f'{numeric_columns[0].title()} vs {numeric_columns[1].title()} Interaction'}
            
        return suggestions, best_cat, best_num

    # Get automated insights
    auto_config, auto_x, auto_y = get_auto_charts(df, num_cols, cat_cols)

    # ---------------- AUTOMATED DASHBOARD RENDERER ----------------
    def render_dashboard():
        st.markdown("---")
        st.subheader("📊 Automated Intelligent Dashboard")
        st.caption("✨ Analytics layouts generated automatically based on your dataset properties.")

        # Key Performance Metrics Row
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Rows", f"{len(df):,}")
        k2.metric("Total Columns", len(df.columns))

        if num_cols:
            k3.metric("Aggregated Volume", f"{df[num_cols[0]].sum():,.0f}")
            k4.metric("Average Value", f"{df[num_cols[0]].mean():,.2f}")
        else:
            k3.metric("Categorical Metrics", len(cat_cols))
            k4.metric("Status", "Operational")

        st.markdown("### 📈 Visual Analytics Insights")
        
        # Dynamic Row 1 layouts based on findings
        cA, cB = st.columns(2)
        
        with cA:
            if 'composition' in auto_config:
                cfg = auto_config['composition']
                st.write(f"##### {cfg['title']}")
                
                # Dynamic Pivot summary setup
                if cfg['type'] == 'pie':
                    pivot_data = df.groupby(cfg['names'])[cfg['values']].sum().reset_index()
                    fig = px.pie(pivot_data, names=cfg['names'], values=cfg['values'], hole=0.4)
                else:
                    pivot_data = df.groupby(cfg['x'])[cfg['y']].sum().reset_index().sort_values(by=cfg['y'], ascending=False).head(10)
                    fig = px.bar(pivot_data, x=cfg['x'], y=cfg['y'], color=cfg['y'], color_continuous_scale="Viridis")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data properties for compositional breakdowns.")

        with cB:
            if 'trend' in auto_config:
                cfg = auto_config['trend']
                st.write(f"##### {cfg['title']}")
                
                if cfg['x'] == 'Index':
                    fig = px.line(df, y=cfg['y'], render_mode="svg")
                else:
                    trend_data = df.groupby(cfg['x'])[cfg['y']].mean().reset_index()
                    fig = px.line(trend_data, x=cfg['x'], y=cfg['y'], markers=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient metrics data detected to map trendlines.")

        # Dynamic Row 2 layout (Advanced Insights)
        st.markdown("---")
        cC, cD = st.columns(2)
        
        with cC:
            if 'correlation' in auto_config:
                cfg = auto_config['correlation']
                st.write(f"##### {cfg['title']}")
                fig = px.scatter(df, x=cfg['x'], y=cfg['y'], trendline="ols" if len(df) < 5000 else None, color=auto_x if auto_x else None)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add multiple numerical columns to unlock dynamic scatter analysis.")

        with cD:
            # Smart Automated Drill-Down Selection Matrix
            if auto_x and auto_y:
                st.write(f"##### Quick Summary Split: {auto_x.title()}")
                drill_summary = df.groupby(auto_x)[auto_y].agg(['sum', 'count']).reset_index().sort_values(by='sum', ascending=False).head(10)
                st.dataframe(drill_summary, use_container_width=True)
            else:
                st.dataframe(df.head(10), use_container_width=True)

    # ---------------- INTERACTION VIEW HANDLERS ----------------
    if section == "All View":
        st.dataframe(df.head(100))
        render_dashboard()

    elif section == "Dashboard":
        render_dashboard()

    elif section == "Sales":
        render_dashboard()

    # ---------------- AI ASSISTANT PANEL ----------------
    elif section == "AI Tool":
        st.subheader("🤖 ChatGPT Data Assistant")
        q = st.text_input("Ask a question about your uploaded dataset:")

        if q:
            if AI_AVAILABLE:
                sample = df.head(50).to_csv(index=False)
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a senior enterprise data analyst. Answer the user comprehensively."},
                        {"role": "user", "content": f"Data Sample:\n{sample}\n\nUser Question: {q}"}
                    ]
                )
                st.write(res.choices[0].message.content)
            else:
                st.warning("⚠️ OpenAI API keys are not detected on this host system environment.")

    # ---------------- GEOGRAPHIC MAP INTERACTION ----------------
    elif section == "Maps":
        lat_fields = [c for c in df.columns if "lat" in c or "latitude" in c]
        lon_fields = [c for c in df.columns if "lon" in c or "longitude" in c]

        if lat_fields and lon_fields:
            st.subheader("📍 Geospatial Metrics Placement Map")
            st.map(df[[lat_fields[0], lon_fields[0]]].dropna())
        else:
            st.warning("No Latitude/Longitude parameters found in the current datasets.")

    # ---------------- DATA PERSISTENCE EXPORTS ----------------
    st.markdown("---")
    ec1, ec2 = st.columns(2)
    
    with ec1:
        st.subheader("💾 Save Session Data")
        if st.button("Save Current View"):
            df.to_csv(f"{st.session_state.user}_dashboard.csv", index=False)
            st.success(f"Successfully cached states to: '{st.session_state.user}_dashboard.csv'")

    with ec2:
        st.subheader("📥 Export Pipeline Summary")
        def create_pdf():
            buffer = BytesIO()
            buffer.write(bytes(f"SNK BI Platform Summary Report\nGenerated for: {st.session_state.user}\nTotal Records Processed: {len(df)} rows across {len(df.columns)} dimensions.", 'utf-8'))
            buffer.seek(0)
            return buffer

        st.download_button("Download Report Abstract", create_pdf(), file_name="bi_summary_report.txt")

else:
    st.info("👋 Welcome! Please upload one or more CSV or Excel data packages in the left sidebar to generate your workspace dashboards.")
