import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Page Configuration
st.set_page_config(
    page_title="Dashboard Kualitas Udara", 
    page_icon="💜", 
    layout="wide"
)

# 2. Custom CSS (Desain Ungu & Teks Sidebar Hitam)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #f8f0ff 0%, #f3e8ff 100%); }
    h1, h2, h3 { color: #4a148c; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #ede7f6 0%, #d1c4e9 100%); }
    [data-testid="stSidebarContent"] .stWidgetLabel p,
    [data-testid="stSidebarContent"] label p { 
        color: #000000 !important; 
        font-weight: bold !important; 
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] { background-color: #4a148c !important; }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] > span { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# Konfigurasi Grafik Seaborn
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "axes.facecolor": "rgba(0,0,0,0)",
    "figure.facecolor": "rgba(0,0,0,0)",
    "text.color": "#4a148c",
    "axes.labelcolor": "#4a148c",
    "xtick.color": "#4a148c",
    "ytick.color": "#4a148c"
})

# 3. Data Loading
@st.cache_data
def load_data():
    csv_name = "PRSA_Data_Nongzhanguan_20130301-20170228.csv"
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, csv_name)
    
    if not os.path.exists(file_path):
        st.error(f"File {csv_name} tidak ditemukan."); st.stop()
        
    df = pd.read_csv(file_path)
    if "No" in df.columns: 
        df = df.drop(columns=["No"])
        
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    
    # Handling missing values sesuai IPYNB (Interpolasi linear)
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

# 4. Sidebar Filters
st.sidebar.title("💜 Filter Dashboard")
years = sorted(df["year"].unique().tolist())
selected_year = st.sidebar.multiselect("Pilih Tahun", options=years, default=years)
seasons = ["Spring", "Summer", "Fall", "Winter"]
selected_season = st.sidebar.multiselect("Pilih Musim", options=seasons, default=seasons)

df_filtered = df[(df["year"].isin(selected_year)) & (df["season"].isin(selected_season))].copy()

# 5. Dashboard Metrics
st.title("💜 Dashboard Analisis Kualitas Udara Nongzhanguan")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.2f}")
with col2: st.metric("Rata-rata PM10", f"{df_filtered['PM10'].mean():.2f}")
with col3: st.metric("Rata-rata TEMP", f"{df_filtered['TEMP'].mean():.2f}°C")
with col4: st.metric("Total Data", f"{len(df_filtered):,}")
st.markdown("---")

# 6. Visualisasi (Seaborn)
# Grafik 1: Hourly
st.subheader("1. Kapan kualitas udara paling buruk dalam sehari?")
pm25_h = df_filtered.groupby("hour")["PM2.5"].mean().reset_index()
fig1, ax1 = plt.subplots(figsize=(10, 4))
sns.lineplot(data=pm25_h, x="hour", y="PM2.5", marker="o", color="#6a1b9a", ax=ax1)
ax1.set_title("Rata-rata PM2.5 per Jam")
st.pyplot(fig1)

# Grafik 2: Monthly Trend
st.subheader("2. Bagaimana tren kualitas udara per bulan?")
pm25_m = df_filtered.groupby("year_month")["PM2.5"].mean().reset_index()
fig2, ax2 = plt.subplots(figsize=(12, 5))
sns.lineplot(data=pm25_m, x="year_month", y="PM2.5", color="#8e24aa", ax=ax2)
plt.xticks(rotation=45)
ax2.set_title("Tren PM2.5 Bulanan")
st.pyplot(fig2)

# Grafik 3: Winter Correlation
st.subheader("3. Faktor apa yang mempengaruhi polusi di Musim Dingin?")
df_winter = df_filtered[df_filtered["season"] == "Winter"]
if not df_winter.empty:
    corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    corr_vals = df_winter[corr_cols].corr(numeric_only=True)["PM2.5"].drop("PM2.5").sort_values(ascending=False).reset_index()
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    sns.barplot(data=corr_vals, x="index", y="PM2.5", palette="Purples_r", ax=ax3)
    ax3.set_title("Korelasi Variabel terhadap PM2.5 (Winter)")
    st.pyplot(fig3)

# Grafik 4: Seasonal Analysis
st.subheader("4. Apakah tingkat polusi berbeda antar musim?")
pm25_s = df_filtered.groupby("season")["PM2.5"].mean().reset_index()
season_order = ["Spring", "Summer", "Fall", "Winter"]
fig4, ax4 = plt.subplots(figsize=(8, 4))
sns.barplot(data=pm25_s, x="season", y="PM2.5", order=season_order, 
            palette=["#d1c4e9", "#ba68c8", "#8e24aa", "#4a148c"], ax=ax4)
ax4.set_title("Rata-rata PM2.5 per Musim")
st.pyplot(fig4)

st.caption("Dashboard by Vinda Karunia Surya | Analisis Data Kualitas Udara Nongzhanguan")
