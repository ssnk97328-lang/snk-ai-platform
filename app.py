import streamlit as st 
import pandas as pd
import plotly.express as px
from io import BytesIO
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

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SNK AI Platform", layout="wide", page_icon="📊")

# ---------------- LOGIN ----------------
USERS = {
    os.getenv("APP_USER1", "admin"): os.getenv("APP_PASS1", "1234"),
}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.markdown("<h1 style='text-align:center;'>🔐 SNK Data Platform</h1>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user in USERS and USERS[user] == pwd:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Credentials")

if not st.session_state.login:
    login()
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚀 SNK Platform")

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
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color:white;}
.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

px.defaults.template = "plotly_dark"

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>📊 SNK Analytics Platform</h1>", unsafe_allow_html=True)

# ---------------- DATA ----------------
if files:

    dfs = []
    for f in files:
        if f.name.endswith(".csv"):
            dfs.append(pd.read_csv(f))
        else:
            dfs.append(pd.read_excel(f))

    df = pd.concat(dfs, ignore_index=True)

    # CLEAN
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]

    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except:
            pass

    df = df.fillna("Unknown").drop_duplicates()

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- GLOBAL FILTER ----------------
    st.subheader("🔍 Global Filters")

    filter_cols = st.multiselect("Select Filters", df.columns)

    for col in filter_cols:
        val = st.selectbox(col, ["All"] + df[col].astype(str).unique().tolist())
        if val != "All":
            df = df[df[col].astype(str) == val]

    # ---------------- KPI ----------------
    st.subheader("📊 KPIs")
    c1, c2, c3 = st.columns(3)

    c1.metric("Total Records", len(df))
    c2.metric("Columns", len(df.columns))

    if num_cols:
        c3.metric("Total Value", f"{df[num_cols].sum().sum():,.0f}")

    # ---------------- SLICER ----------------
    st.subheader("🎯 Dashboard Slicer")

    col1, col2 = st.columns(2)

    x_axis = col1.selectbox("X Axis (Category)", df.columns)
    y_axis = col2.selectbox("Y Axis (Numeric)", num_cols if num_cols else df.columns)

    # ---------------- DATA PREP ----------------
    def prepare_chart_data(df, x_axis, y_axis):
        try:
            g = (
                df.groupby(x_axis)[y_axis]
                .sum()
                .reset_index()
                .sort_values(by=y_axis, ascending=False)
                .head(10)
            )
            return g
        except:
            return df.head(50)

    chart_df = prepare_chart_data(df, x_axis, y_axis)

    # ---------------- DASHBOARD ----------------
    def render_dashboard():

        st.markdown("### 📊 Dynamic Dashboard")

        c1, c2 = st.columns(2)

        # BAR
        try:
            c1.plotly_chart(px.bar(chart_df, x=x_axis, y=y_axis), use_container_width=True)
        except:
            c1.warning("Bar chart not available")

        # PIE
        try:
            c2.plotly_chart(px.pie(chart_df, names=x_axis, values=y_axis), use_container_width=True)
        except:
            c2.warning("Pie chart not available")

        # LINE
        try:
            st.plotly_chart(px.line(chart_df, x=x_axis, y=y_axis), use_container_width=True)
        except:
            st.warning("Line chart not available")

        st.dataframe(chart_df, use_container_width=True)

    # ---------------- SECTIONS ----------------
    if section == "All View":
        st.dataframe(df.head(200))
        render_dashboard()

    elif section == "Dashboard":
        render_dashboard()

    elif section == "Sales":
        render_dashboard()

    elif section == "AI Tool":
        st.subheader("🤖 AI Tool")

        q = st.text_input("Ask your data")
        if q and AI_AVAILABLE:
            sample = df.head(50).to_csv(index=False)
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":sample+"\n"+q}]
            )
            st.write(res.choices[0].message.content)

    elif section == "Maps":
        lat = [c for c in df.columns if "lat" in c]
        lon = [c for c in df.columns if "lon" in c]

        if lat and lon:
            st.map(df[[lat[0], lon[0]]].dropna())
        else:
            st.warning("No map data")

    # ---------------- ANOMALY ----------------
    st.subheader("🚨 Anomaly Detection")

    if num_cols:
        col = st.selectbox("Column", num_cols)
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1

        outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
        st.write("Outliers:", len(outliers))
        st.dataframe(outliers.head(100))

    # ---------------- AUTO INSIGHTS ----------------
    st.subheader("🤖 Auto Insights")

    if num_cols and cat_cols:
        top = df[cat_cols[0]].value_counts().idxmax()
        pct = round(df[cat_cols[0]].value_counts(normalize=True).max()*100,2)
        st.write(f"🔹 {top} contributes {pct}%")

    # ---------------- FORECAST ----------------
    st.subheader("📈 Forecasting")

    if num_cols:
        col = num_cols[0]
        dff = df[[col]].dropna().reset_index()

        z = np.polyfit(dff.index, dff[col], 1)
        p = np.poly1d(z)

        future = pd.DataFrame({
            "index": range(len(dff), len(dff)+10),
            col: p(range(len(dff), len(dff)+10))
        })

        full = pd.concat([dff, future])
        st.plotly_chart(px.line(full, x="index", y=col), use_container_width=True)

    # ---------------- PDF ----------------
    st.subheader("📥 Download PDF")

    def create_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        story = [
            Paragraph("SNK Dashboard Report", styles["Title"]),
            Spacer(1,20),
            Paragraph(f"Rows: {len(df)}", styles["Normal"]),
            Paragraph(f"Columns: {len(df.columns)}", styles["Normal"])
        ]

        doc.build(story)
        buffer.seek(0)
        return buffer

    st.download_button("Download PDF", create_pdf())

else:
    st.info("👈 Upload files to start")

# ---------------- FOOTER ----------------
st.markdown("<hr><center>🚀 SNK Data Platform</center>", unsafe_allow_html=True)