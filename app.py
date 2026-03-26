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

    # CLEANING
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^unnamed")]

    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.replace(",", "").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except:
            pass

    before_rows = df.shape[0]
    df = df.fillna("Unknown").drop_duplicates()
    removed_rows = before_rows - df.shape[0]

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- FILTER ----------------
    st.subheader("🔍 Filters")
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

    # ---------------- ALL VIEW ----------------
    if section == "All View":
        st.dataframe(df.head(200), use_container_width=True)

    # ---------------- DASHBOARD ----------------
    elif section == "Dashboard":
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if cat_cols and num_cols:
            x = st.selectbox("Category", cat_cols)
            y = st.selectbox("Value", num_cols)

            g = df.groupby(x)[y].sum().reset_index().sort_values(by=y, ascending=False).head(10)

            st.subheader("📊 Top 10 Dashboard")
            fig = px.bar(g, x=x, y=y, color=x, text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(g)

        else:
            st.warning("Need numeric + category")

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- SALES ----------------
    elif section == "Sales":
        if num_cols:
            st.plotly_chart(px.line(df, y=num_cols[0]), use_container_width=True)

    # ---------------- AI TOOL ----------------
    elif section == "AI Tool":
        st.subheader("🤖 AI Data Chat")
        q = st.text_input("Ask your data")
        if q and AI_AVAILABLE:
            sample = df.head(50).to_csv(index=False)
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":sample+"\n"+q}]
            )
            st.write(res.choices[0].message.content)

    # ---------------- MAP ----------------
    elif section == "Maps":
        lat = [c for c in df.columns if "lat" in c]
        lon = [c for c in df.columns if "lon" in c]
        if lat and lon:
            fig = px.scatter_mapbox(df, lat=lat[0], lon=lon[0], zoom=5)
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig)

    # ---------------- ANOMALY ----------------
    st.subheader("🚨 Anomaly Detection")
    if num_cols:
        col = st.selectbox("Column", num_cols)
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
        st.write("Outliers:", len(outliers))
        st.dataframe(outliers.head(100))

    # ================= POWER BI DASHBOARD =================
    st.markdown("---")
    st.header("📊 Power BI Style Dashboard")

    if num_cols and cat_cols:
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total", f"{df[num_cols].sum().sum():,.0f}")
        k2.metric("Avg", f"{df[num_cols].mean().mean():.2f}")
        k3.metric("Rows", len(df))
        k4.metric("Cols", len(df.columns))

        x, y = cat_cols[0], num_cols[0]
        g = df.groupby(x)[y].sum().reset_index().sort_values(by=y, ascending=False).head(10)

        cA, cB = st.columns(2)
        cA.plotly_chart(px.bar(g, x=x, y=y), use_container_width=True)
        cB.plotly_chart(px.pie(g, names=x, values=y), use_container_width=True)

        st.plotly_chart(px.line(df, y=y), use_container_width=True)

    # ================= AUTO INSIGHTS =================
    st.markdown("---")
    st.header("🤖 Auto Insights")

    if num_cols and cat_cols:
        top = df[cat_cols[0]].value_counts().idxmax()
        pct = round(df[cat_cols[0]].value_counts(normalize=True).max()*100,2)
        st.write(f"🔹 {top} contributes {pct}%")

        st.write(f"🔹 Max {num_cols[0]} = {df[num_cols[0]].max()}")
        st.write(f"🔹 Min {num_cols[0]} = {df[num_cols[0]].min()}")

    # ================= FORECAST =================
    st.markdown("---")
    st.header("📈 Forecasting")

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

    # ================= PDF =================
    st.markdown("---")
    st.header("📥 Download PDF")

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