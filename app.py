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
        return json.load(open(USER_DB_FILE))
    return {"admin": {"password": "1234"}}

def save_users(users):
    json.dump(users, open(USER_DB_FILE, "w"))

users = load_users()

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    st.title("🔐 SNK SaaS Platform")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if u in users and users[u]["password"] == p:
                st.session_state.user = u
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")

        if st.button("Signup"):
            users[new_u] = {"password": new_p}
            save_users(users)
            st.success("User created")

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

# ---------------- DATA ----------------
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

    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except:
            pass

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- FILTER ----------------
    st.subheader("🔍 Filters")

    filter_cols = st.multiselect("Select Filters", df.columns)

    for col in filter_cols:
        val = st.selectbox(col, ["All"] + df[col].astype(str).unique().tolist())
        if val != "All":
            df = df[df[col].astype(str) == val]

    # ---------------- SLICER ----------------
    st.subheader("🎯 Power BI Slicer")

    c1,c2,c3,c4 = st.columns(4)

    x_axis = c1.selectbox("X Axis", df.columns)
    y_axis = c2.selectbox("Y Axis", num_cols if num_cols else df.columns)

    row_field = c3.selectbox("Row", df.columns)
    value_field = c4.selectbox("Value", num_cols if num_cols else df.columns)

    # ---------------- PIVOT ----------------
    try:
        pivot_df = df.groupby(row_field)[value_field].sum().reset_index()
        pivot_df = pivot_df.sort_values(by=value_field, ascending=False).head(10)
    except:
        pivot_df = df.copy()

    # ---------------- DASHBOARD ----------------
    def render_dashboard():

        st.subheader("📊 Power BI Dashboard")

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Rows", len(df))
        k2.metric("Columns", len(df.columns))

        if num_cols:
            k3.metric("Total", f"{df[num_cols].sum().sum():,.0f}")
            k4.metric("Avg", f"{df[num_cols].mean().mean():.2f}")

        cA,cB = st.columns(2)

        with cA:
            fig1 = px.bar(pivot_df, x=row_field, y=value_field)
            st.plotly_chart(fig1, use_container_width=True)

        with cB:
            fig2 = px.pie(pivot_df, names=row_field, values=value_field)
            st.plotly_chart(fig2, use_container_width=True)

        # Drill-down
        st.subheader("📊 Drill Down")
        drill = st.selectbox("Select Drill Column", df.columns)
        fig3 = px.bar(df, x=drill, y=y_axis)
        st.plotly_chart(fig3, use_container_width=True)

        # Trend
        if y_axis in num_cols:
            st.subheader("📈 Trend + Forecast")
            dff = df[[y_axis]].dropna().reset_index()
            z = np.polyfit(dff.index, dff[y_axis], 1)
            p = np.poly1d(z)

            future = pd.DataFrame({
                "index": range(len(dff), len(dff)+10),
                y_axis: p(range(len(dff), len(dff)+10))
            })

            full = pd.concat([dff, future])
            st.plotly_chart(px.line(full, x="index", y=y_axis), use_container_width=True)

        st.dataframe(pivot_df)

    # ---------------- ALL VIEW ----------------
    if section == "All View":
        st.dataframe(df.head(200))
        render_dashboard()

    elif section == "Dashboard":
        render_dashboard()

    elif section == "Sales":
        render_dashboard()

    # ---------------- AI TOOL ----------------
    elif section == "AI Tool":
        st.subheader("🤖 ChatGPT Data Assistant")

        q = st.text_input("Ask question")

        if q:
            if AI_AVAILABLE:
                sample = df.head(50).to_csv(index=False)

                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role":"system","content":"You are a data analyst"},
                        {"role":"user","content":sample + "\n" + q}
                    ]
                )
                st.write(res.choices[0].message.content)
            else:
                st.warning("Add OpenAI API Key")

    # ---------------- MAP ----------------
    elif section == "Maps":
        lat = [c for c in df.columns if "lat" in c]
        lon = [c for c in df.columns if "lon" in c]

        if lat and lon:
            st.map(df[[lat[0], lon[0]]].dropna())

    # ---------------- SAVE DASHBOARD ----------------
    st.markdown("---")
    st.subheader("💾 Save Dashboard")

    if st.button("Save"):
        df.to_csv(f"{st.session_state.user}_dashboard.csv", index=False)
        st.success("Saved!")

    # ---------------- PDF EXPORT ----------------
    st.subheader("📥 Export PDF")

    def create_pdf():
        buffer = BytesIO()
        buffer.write(bytes(f"Dashboard Rows: {len(df)}", 'utf-8'))
        buffer.seek(0)
        return buffer

    st.download_button("Download PDF", create_pdf())

else:
    st.info("Upload files to start")