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

# ---------------- MULTI USER LOGIN ----------------
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
    "📂 Upload Files (Large Supported)",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

section = st.radio(
    "Navigation",
    ["All View", "Dashboard", "Sales", "Maps"],
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

    # ADVANCED CLEANING
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
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

    # ---------------- SALES ----------------
    elif section == "Sales":
        st.subheader("📊 Sales Trends")

        if date_cols and num_cols:
            date_col = st.selectbox("Date Column", date_cols)
            value_col = st.selectbox("Sales Column", num_cols)

            df["year"] = df[date_col].dt.year
            df["month"] = df[date_col].dt.month
            df["week"] = df[date_col].dt.isocalendar().week
            df["quarter"] = df[date_col].dt.quarter

            view = st.radio("Trend Type", ["Weekly", "Monthly", "Quarterly", "Yearly"], horizontal=True)

            if view == "Weekly":
                g = df.groupby("week")[value_col].sum().reset_index()
            elif view == "Monthly":
                g = df.groupby("month")[value_col].sum().reset_index()
            elif view == "Quarterly":
                g = df.groupby("quarter")[value_col].sum().reset_index()
            else:
                g = df.groupby("year")[value_col].sum().reset_index()

            fig = px.line(g, x=g.columns[0], y=value_col, title="Sales Trend")
            st.plotly_chart(fig, use_container_width=True)

            # Growth
            g["growth_%"] = g[value_col].pct_change() * 100
            st.subheader("📈 Growth (WoW / MoM)")
            st.dataframe(g)

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

    # ---------------- COLOR TABLE ----------------
    st.subheader("🎨 Highlight Data")
    if num_cols:
        st.dataframe(df.style.background_gradient(cmap="Blues"))

    # ---------------- EXPORT ----------------
    st.subheader("📥 Export")

    st.download_button("Download CSV", df.to_csv(index=False))

    out = BytesIO()
    df.to_excel(out, index=False)
    st.download_button("Download Excel", out.getvalue())

    # PDF
    report = f"Rows: {len(df)} | Columns: {len(df.columns)}"

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

# ---------------- FOOTER ----------------
st.markdown("""
<hr>
<p style='text-align:center;'>🚀 SNK Data Platform | Advanced Analytics Dashboard</p>
""", unsafe_allow_html=True)