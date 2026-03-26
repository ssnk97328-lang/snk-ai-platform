import streamlit as st 
import pandas as pd
import plotly.express as px
from io import BytesIO
import requests
import numpy as np
import os

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SNK AI Platform", layout="wide", page_icon="📊")

# ---------------- LOGIN ----------------
USERS = {
    os.getenv("APP_USER1", "admin"): os.getenv("APP_PASS1", "1234"),
    os.getenv("APP_USER2", "user"): os.getenv("APP_PASS2", "1111")
}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.markdown("<h1 style='text-align:center;'>🔐 SNK Data Platform</h1>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("🚀 Login", use_container_width=True):
        if user in USERS and USERS[user] == pwd:
            st.session_state.login = True
            st.success("Access Granted")
            st.rerun()
        else:
            st.error("Invalid Credentials")

if not st.session_state.login:
    login()
    st.stop()

# ---------------- LOTTIE ----------------
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        return None

def render_lottie(data, height=200):
    try:
        from streamlit_lottie import st_lottie
        if data:
            st_lottie(data, height=height)
    except:
        pass

lottie_data = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚀 SNK Platform")
theme = st.sidebar.toggle("🌗 Dark Mode", True)

files = st.sidebar.file_uploader(
    "📂 Upload Files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

section = st.radio(
    "Navigation",
    ["All View", "Dashboard", "Sales", "AI Tool", "Maps"],
    horizontal=True
)

# ---------------- STYLE ----------------
if theme:
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color:white;}
    </style>
    """, unsafe_allow_html=True)

px.defaults.template = "plotly_dark"

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>📊 SNK Analytics Platform</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>Advanced Data Dashboard</h4>", unsafe_allow_html=True)

# ---------------- DATA ----------------
if files:
    with st.spinner("Processing data..."):
        dfs = []
        for f in files:
            if f.name.endswith(".csv"):
                for chunk in pd.read_csv(f, chunksize=50000):
                    dfs.append(chunk)
            else:
                dfs.append(pd.read_excel(f))

        df = pd.concat(dfs, ignore_index=True)

    # CLEAN
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.fillna("Unknown").drop_duplicates()

    # ADVANCED CLEAN
    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.replace(",", "").str.strip()
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except:
            pass

    date_cols = []
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col])
            date_cols.append(col)
        except:
            pass

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    # ---------------- KPI ----------------
    st.subheader("📊 Advanced KPIs")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Records", len(df))
    c2.metric("Columns", len(df.columns))

    if num_cols:
        total = df[num_cols].sum().sum()
        avg = df[num_cols].mean().mean()
        c3.metric("Total Value", f"{total:,.0f}")
        c4.metric("Avg Value", f"{avg:.2f}")

    # ---------------- FILTER ----------------
    st.subheader("🔍 Filters")
    filter_cols = st.multiselect("Select Filters", df.columns)

    for col in filter_cols:
        val = st.selectbox(col, ["All"] + df[col].astype(str).unique().tolist())
        if val != "All":
            df = df[df[col].astype(str) == val]

    # ---------------- ALL VIEW ----------------
    if section == "All View":
        st.dataframe(df.head(200), use_container_width=True)

    # ---------------- DASHBOARD ----------------
    elif section == "Dashboard":
        if num_cols:
            fig = px.histogram(df, x=num_cols[0])
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- SALES ----------------
    elif section == "Sales":
        st.subheader("📊 Sales Trends")

    # ---------------- AI TOOL ----------------
    elif section == "AI Tool":
        st.subheader("🤖 AI Data Chat")

    # ---------------- MAP ----------------
    elif section == "Maps":
        lat = [c for c in df.columns if "lat" in c]
        lon = [c for c in df.columns if "lon" in c]

        if lat and lon:
            try:
                df[lat[0]] = pd.to_numeric(df[lat[0]], errors='coerce')
                df[lon[0]] = pd.to_numeric(df[lon[0]], errors='coerce')
                map_df = df.dropna(subset=[lat[0], lon[0]])

                fig = px.scatter_mapbox(map_df, lat=lat[0], lon=lon[0], zoom=3)
                fig.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig)
            except:
                st.error("Map error")
        else:
            st.warning("No lat/lon columns")

    # ================== ALL ADVANCED ADDONS ==================

    st.markdown("---")
    st.header("🚀 Advanced Intelligence Layer")

    # FULL DATA
    with st.expander("📂 Full Data"):
        st.dataframe(df, use_container_width=True)

    # AI AUTO CHART
    with st.expander("🤖 AI Auto Chart"):
        if num_cols and cat_cols:
            x = cat_cols[0]
            y = num_cols[0]
            chart = st.selectbox("Chart Type", ["Bar","Line","Pie","Scatter"])
            g = df.groupby(x)[y].sum().reset_index()

            if chart == "Bar":
                fig = px.bar(g, x=x, y=y)
            elif chart == "Line":
                fig = px.line(g, x=x, y=y)
            elif chart == "Pie":
                fig = px.pie(g, names=x, values=y)
            else:
                fig = px.scatter(df, x=x, y=y)

            st.plotly_chart(fig)

    # VLOOKUP
    with st.expander("🔍 VLOOKUP Engine"):
        col1 = st.selectbox("Lookup Column", df.columns)
        col2 = st.selectbox("Match Column", df.columns)
        col3 = st.selectbox("Return Column", df.columns)
        newcol = st.text_input("New Column Name","vlookup_result")

        if st.button("Run VLOOKUP"):
            d = df.set_index(col2)[col3].to_dict()
            df[newcol] = df[col1].map(d)
            st.success("VLOOKUP Applied")
            st.dataframe(df.head())

    # AI CHAT + AUTO CHART
    with st.expander("🤖 ChatGPT AI Analyst"):
        q = st.text_input("Ask AI about your data")

        if q:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                sample = df.sample(min(100, len(df))).to_csv(index=False)

                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a data analyst"},
                        {"role": "user", "content": f"{sample}\n\n{q}"}
                    ]
                )

                reply = res.choices[0].message.content
                st.success(reply)

                if "chart" in q.lower():
                    g = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index()
                    st.plotly_chart(px.bar(g, x=cat_cols[0], y=num_cols[0]))

            except:
                st.warning("AI not active / limit reached")

    # AUTO FORMULAS
    with st.expander("📊 Excel Formula AI"):
        formula = st.text_input("Enter formula (sum, avg, max, min, vlookup)")

        if formula:
            if "sum" in formula.lower():
                st.write(df[num_cols[0]].sum())
            elif "avg" in formula.lower():
                st.write(df[num_cols[0]].mean())
            elif "max" in formula.lower():
                st.write(df[num_cols[0]].max())
            elif "min" in formula.lower():
                st.write(df[num_cols[0]].min())

    # AUTOMATION
    with st.expander("⚡ Full Automation"):
        if st.button("Run Auto Analysis"):
            st.write("Total:", df[num_cols[0]].sum())

            top10 = df.nlargest(10, num_cols[0])
            st.dataframe(top10)

            st.plotly_chart(px.bar(top10, x=top10.columns[0], y=num_cols[0]))

else:
    render_lottie(lottie_data, 300)
    st.info("👈 Upload files to start")

# ---------------- FOOTER ----------------
st.markdown("""
<hr>
<p style='text-align:center;'>🚀 SNK Data Platform</p>
""", unsafe_allow_html=True)