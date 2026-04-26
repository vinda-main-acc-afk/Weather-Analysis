import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="Dashboard Kualitas Udara", page_icon="💜", layout="wide")

# 2. Custom CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #f8f0ff 0%, #f3e8ff 100%); }
    h1, h2, h3 { color: #4a148c; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #ede7f6 0%, #d1c4e9 100%); }
    [data-testid="stSidebarContent"] .stWidgetLabel p { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] { background-color: #4a148c !important; }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] > span { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Loading
@st.cache_data
def load_data():
    csv_name = "PRSA_Data_Nongzhanguan_20130301-20170228.csv"
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, csv_name)
    if not os.path.exists(file_path):
        st.error(f"File {csv_name} tidak ditemukan."); st.stop()
    df = pd.read_csv(file_path)
    if "No" in df.columns: df = df.drop(columns=["No"])
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()
    def get_season(month):
        if month in [12, 1, 2]: return "Winter"
        elif month in [3, 4, 5]: return "Spring"
        elif month in [6, 7, 8]: return "Summer"
        return "Fall"
    df["season"] = df["month"].apply(get_season)
    df["year_month"] = df["datetime"].dt.to_period("M").astype(str)
    return df

df = load_data()

# 4. Sidebar
st.sidebar.title("💜 Filter Dashboard")
years = sorted(df["year"].unique().tolist())
selected_year = st.sidebar.multiselect("Pilih Tahun", options=years, default=years)
seasons = ["Spring", "Summer", "Fall", "Winter"]
selected_season = st.sidebar.multiselect("Pilih Musim", options=seasons, default=seasons)
df_filtered = df[(df["year"].isin(selected_year)) & (df["season"].isin(selected_season))].copy()

# 5. Dashboard Content
st.title("💜 Dashboard Kualitas Udara Nongzhanguan")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.2f}")
with col2: st.metric("Rata-rata PM10", f"{df_filtered['PM10'].mean():.2f}")
with col3: st.metric("Rata-rata TEMP", f"{df_filtered['TEMP'].mean():.2f}°C")
with col4: st.metric("Total Data", f"{len(df_filtered):,}")

st.markdown("---")

# Visualisasi 1 & 2
st.subheader("1. Rata-rata PM2.5 per Jam")
pm25_h = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()
f1 = px.line(pm25_h, x="hour", y="PM2.5", markers=True, color_discrete_sequence=["#6a1b9a"])
f1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(f1, use_container_width=True)

st.subheader("2. Tren PM2.5 per Bulan")
pm25_m = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()
f2 = px.line(pm25_m, x="year_month", y="PM2.5", color_discrete_sequence=["#8e24aa"])
f2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(f2, use_container_width=True)

st.caption("Dashboard by Vinda Karunia Surya")
