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

# OPTIONAL AI
try:
    from openai import OpenAI
    client = OpenAI()
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False


# ---------------- SAFE LOTTIE ----------------
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

lottie_login = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_6aYlH8.json")
lottie_data = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")


# ---------------- LOGIN ----------------
if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.markdown("<h1 style='text-align:center;'>🔐 SNK Secure Gateway</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        render_lottie(lottie_login, 200)

        with st.container(border=True):
            user = st.text_input("Username", placeholder="admin")
            pwd = st.text_input("Password", type="password")

            if st.button("🚀 Login", use_container_width=True):
                if user == "admin" and pwd == "1234":
                    st.session_state.login = True
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

if not st.session_state.login:
    st.set_page_config(page_title="Login", page_icon="🔐")
    login()
    st.stop()


# ---------------- PAGE ----------------
st.set_page_config(page_title="SNK AI Platform", layout="wide")

# SIDEBAR
st.sidebar.title("🚀 SNK Platform")
theme = st.sidebar.toggle("🌗 Dark Mode", True)

files = st.sidebar.file_uploader(
    "📂 Upload Files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

section = st.radio(
    "Navigation",
    ["All View", "Dashboard", "AI Tool", "Maps"],
    horizontal=True
)

# ---------------- STYLE ----------------
if theme:
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color:white;}
    .hero {background:#0b1a2a;padding:20px;border-radius:20px;margin-bottom:20px;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {background:#f0f2f5;color:black;}
    .hero {background:white;padding:20px;border-radius:20px;margin-bottom:20px;}
    </style>
    """, unsafe_allow_html=True)

px.defaults.template = "plotly_dark"


# ---------------- HERO SECTION (SAFE IMAGE) ----------------
st.markdown('<div class="hero">', unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>🚀 SNK AI Data Platform</h1>", unsafe_allow_html=True)

def load_banner():
    local = "banner.png"
    fallback = "https://images.unsplash.com/photo-1551288049-bebda4e38f71"
    return local if os.path.exists(local) else fallback

st.image(load_banner(), use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


# ---------------- DATA ----------------
if files:
    with st.spinner("Processing data..."):
        dfs = []
        for f in files:
            if f.name.endswith(".csv"):
                for chunk in pd.read_csv(f, chunksize=100000):
                    dfs.append(chunk)
            else:
                dfs.append(pd.read_excel(f))

        df = pd.concat(dfs, ignore_index=True)

    # CLEAN
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^unnamed")]

    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.strip().str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except:
            pass

    before = len(df)
    df = df.fillna("Unknown").drop_duplicates()
    removed = before - len(df)

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    # ---------------- KPI ----------------
    st.subheader("📊 KPIs")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Records", len(df))
    c2.metric("Columns", len(df.columns))
    c3.metric("Duplicates Removed", removed)

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

        if cat_cols and num_cols:
            x = st.selectbox("Category", cat_cols)
            y = st.selectbox("Value", num_cols)
            chart = st.selectbox("Chart", ["Bar","Pie","Line","Scatter","Histogram"])

            g = df.groupby(x)[y].sum().reset_index()

            if chart == "Bar":
                fig = px.bar(g, x=x, y=y)
            elif chart == "Pie":
                fig = px.pie(g, names=x, values=y)
            elif chart == "Line":
                fig = px.line(g, x=x, y=y)
            elif chart == "Scatter":
                fig = px.scatter(df, x=x, y=y)
            else:
                fig = px.histogram(df, x=y)

            st.plotly_chart(fig, use_container_width=True)

    # ---------------- DASHBOARD ----------------
    elif section == "Dashboard":
        if num_cols:
            fig = px.histogram(df, x=num_cols[0])
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- AI TOOL ----------------
    elif section == "AI Tool":
        q = st.text_input("Ask your data")
        if q:
            if AI_AVAILABLE:
                sample = df.head(50).to_csv(index=False)
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role":"system","content":"You are data analyst"},
                        {"role":"user","content":f"{sample}\n\n{q}"}
                    ]
                )
                st.write(res.choices[0].message.content)
            else:
                st.warning("AI not configured")

    # ---------------- MAP ----------------
    elif section == "Maps":
        lat = [c for c in df.columns if "lat" in c]
        lon = [c for c in df.columns if "lon" in c]

        if lat and lon:
            fig = px.scatter_mapbox(df, lat=lat[0], lon=lon[0], zoom=4)
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig)
        else:
            st.warning("No lat/lon columns")

    # ---------------- ANOMALY ----------------
    st.subheader("🚨 Anomaly Detection")
    if num_cols:
        col = st.selectbox("Column", num_cols)
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1-1.5*IQR) | (df[col] > Q3+1.5*IQR)]
        st.write("Outliers:", len(outliers))
        st.dataframe(outliers.head(50))

    # ---------------- EXPORT ----------------
    st.subheader("📥 Export")

    st.download_button("Download CSV", df.to_csv(index=False))

    out = BytesIO()
    df.to_excel(out, index=False)
    st.download_button("Download Excel", out.getvalue())

    # PDF
    report = f"Rows: {len(df)}\nColumns: {len(df.columns)}\nRemoved: {removed}"

    def create_pdf(text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        story = []
        for line in text.split("\n"):
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 10))
        doc.build(story)
        buffer.seek(0)
        return buffer

    st.download_button("Download PDF", create_pdf(report))

else:
    render_lottie(lottie_data, 300)
    st.info("👈 Upload files to start")