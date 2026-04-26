import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Dashboard Analisis Kualitas Udara",
    page_icon="💜",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f8f0ff 0%, #f3e8ff 100%);
    }
    h1, h2, h3 {
        color: #4a148c;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ede7f6 0%, #d1c4e9 100%);
    }
    [data-testid="stSidebarContent"] .stWidgetLabel p,
    [data-testid="stSidebarContent"] label p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #4a148c !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] > span {
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    csv_name = "PRSA_Data_Nongzhanguan_20130301-20170228.csv"
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, csv_name)

    if not os.path.exists(file_path):
        st.error(f"File CSV '{csv_name}' tidak ditemukan di direktori {base_path}.")
        st.stop()

    df = pd.read_csv(file_path)

    if "No" in df.columns:
        df = df.drop(columns=["No"])

    # Interpolasi linear sesuai analisis IPYNB
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()

    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    def get_season(month):
        if month in [12, 1, 2]: return "Winter"
        elif month in [3, 4, 5]: return "Spring"
        elif month in [6, 7, 8]: return "Summer"
        return "Fall"

    df["season"] = df["month"].apply(get_season)
    df["year_month"] = df["datetime"].dt.to_period("M").astype(str)

    return df

df = load_data()

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.title("💜 Filter Dashboard")

year_list = sorted(df["year"].unique().tolist())
selected_year = st.sidebar.multiselect("Pilih Tahun", options=year_list, default=year_list)

season_list = ["Spring", "Summer", "Fall", "Winter"]
selected_season = st.sidebar.multiselect("Pilih Musim", options=season_list, default=season_list)

df_filtered = df[(df["year"].isin(selected_year)) & (df["season"].isin(selected_season))].copy()

if df_filtered.empty:
    st.warning("Data kosong berdasarkan filter.")
    st.stop()

# =========================
# HEADER & METRICS
# =========================
st.title("💜 Dashboard Analisis Kualitas Udara Nongzhanguan")
st.markdown("**Berdasarkan Analisis Data di Proyek Analisis Data Vinda**")

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.2f}")
with col2: st.metric("Rata-rata PM10", f"{df_filtered['PM10'].mean():.2f}")
with col3: st.metric("Rata-rata TEMP", f"{df_filtered['TEMP'].mean():.2f}°C")
with col4: st.metric("Total Data", f"{len(df_filtered):,}")

st.markdown("---")

# =========================
# ANALYSES (1-4)
# =========================
st.subheader("1. Kapan kualitas udara paling buruk dalam sehari?")
pm25_hourly = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()
fig1 = px.line(pm25_hourly, x="hour", y="PM2.5", markers=True, color_discrete_sequence=["#6a1b9a"])
fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig1, use_container_width=True)

st.subheader("2. Bagaimana tren kualitas udara per bulan?")
pm25_monthly = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()
fig2 = px.line(pm25_monthly, x="year_month", y="PM2.5", markers=True, color_discrete_sequence=["#8e24aa"])
fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig2, use_container_width=True)

st.subheader("3. Faktor pengaruh polusi pada musim dingin")
df_winter = df_filtered[df_filtered["season"] == "Winter"]
if not df_winter.empty:
    corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    corr_matrix = df_winter[corr_cols].corr(numeric_only=True)
    corr_pm25 = corr_matrix["PM2.5"].drop("PM2.5").sort_values(ascending=False).reset_index()
    fig3 = px.bar(corr_pm25, x="index", y="PM2.5", color="PM2.5", color_continuous_scale=["#e1bee7", "#4a148c"])
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("4. Rata-rata PM2.5 Berdasarkan Musim")
pm25_season = df_filtered.groupby("season", as_index=False)["PM2.5"].mean()
fig4 = px.bar(pm25_season, x="season", y="PM2.5", color="season", 
             color_discrete_map={"Spring": "#d1c4e9", "Summer": "#ba68c8", "Fall": "#8e24aa", "Winter": "#4a148c"})
fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"), showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.success("Analisis menunjukkan pola PM2.5 dipengaruhi waktu dan musim.")
st.caption("Dashboard by Vinda Karunia Surya")
