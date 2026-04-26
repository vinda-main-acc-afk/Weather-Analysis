import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(
    page_title="Dashboard Analisis Kualitas Udara",
    page_icon="💜",
    layout="wide"
)

# 2. Custom CSS for Styling
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #f8f0ff 0%, #f3e8ff 100%);
    }
    h1, h2, h3 {
        color: #4a148c;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ede7f6 0%, #d1c4e9 100%);
    }
    /* Teks label filter (Pilih Tahun, Pilih Musim) jadi Hitam */
    [data-testid="stSidebarContent"] .stWidgetLabel p, 
    [data-testid="stSidebarContent"] label p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    /* Judul Filter Dashboard jadi Hitam */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #000000 !important;
    }
    /* Box Filter (Tags) warna Ungu Tua, Teks Putih */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #4a148c !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] > span {
        color: #ffffff !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
        fill: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. Data Loading and Preprocessing (Sesuai tahap Data Wrangling di IPYNB)
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "PRSA_Data_Nongzhanguan_20130301-20170228.csv")
    
    if not os.path.exists(file_path):
        file_path = "PRSA_Data_Nongzhanguan_20130301-20170228.csv"

    df = pd.read_csv(file_path)
    
    if "No" in df.columns:
        df = df.drop(columns="No")

    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    # Handling missing values sesuai IPYNB (Interpolasi linear)
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()

    def get_season(month):
        if month in [12, 1, 2]: return "Winter"
        elif month in [3, 4, 5]: return "Spring"
        elif month in [6, 7, 8]: return "Summer"
        return "Fall"

    df["season"] = df["month"].apply(get_season)
    df["year_month"] = df["datetime"].dt.to_period("M").astype(str)
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# 4. Sidebar Filters
st.sidebar.title("💜 Filter Dashboard")
year_list = sorted(df["year"].unique().tolist())
selected_year = st.sidebar.multiselect("Pilih Tahun", options=year_list, default=year_list)

season_list = ["Spring", "Summer", "Fall", "Winter"]
selected_season = st.sidebar.multiselect("Pilih Musim", options=season_list, default=season_list)

# Filter Data
df_filtered = df[(df["year"].isin(selected_year)) & (df["season"].isin(selected_season))].copy()

# 5. Header
st.title("💜 Dashboard Analisis Kualitas Udara Nongzhanguan")
st.markdown("**Berdasarkan Analisis Data di Proyek Analisis Data Vinda**")

# 6. Main Metrics
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.2f}")
with col2: st.metric("Rata-rata PM10", f"{df_filtered['PM10'].mean():.2f}")
with col3: st.metric("Rata-rata TEMP", f"{df_filtered['TEMP'].mean():.2f}°C")
with col4: st.metric("Total Baris Data", f"{len(df_filtered):,}")

st.markdown("---")

# 7. Analysis 1: Polusi per Jam
st.subheader("1. Kapan kualitas udara paling buruk dalam sehari?")
pm25_hourly = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()
fig1 = px.line(pm25_hourly, x="hour", y="PM2.5", markers=True, 
               title="Rata-rata PM2.5 per Jam", color_discrete_sequence=["#6a1b9a"])
fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig1, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 1"):
    st.write("Konsentrasi PM2.5 cenderung meningkat pada malam hari (20:00 - 23:00).")

# 8. Analysis 2: Tren per Bulan
st.subheader("2. Bagaimana tren kualitas udara per bulan selama periode pengamatan?")
pm25_monthly = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()
fig2 = px.line(pm25_monthly, x="year_month", y="PM2.5", 
               title="Tren Bulanan PM2.5", color_discrete_sequence=["#8e24aa"])
fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig2, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 2"):
    st.write("Tingkat polusi tertinggi secara konsisten terjadi di akhir tahun (Desember).")

# 9. Analysis 3: Faktor Musim Dingin
st.subheader("3. Faktor apa yang paling mempengaruhi polusi udara pada musim dingin?")
df_winter = df_filtered[df_filtered["season"] == "Winter"]
if not df_winter.empty:
    corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    corr_pm25 = df_winter[corr_cols].corr()["PM2.5"].drop("PM2.5").sort_values(ascending=False).reset_index()
    fig3 = px.bar(corr_pm25, x="index", y="PM2.5", color="PM2.5", color_continuous_scale=["#e1bee7", "#4a148c"])
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Pilih 'Winter' untuk melihat analisis korelasi.")

# 10. Analysis 4: Perbandingan Musim
st.subheader("4. Apakah tingkat polusi berbeda signifikan antar musim?")
pm25_season = df_filtered.groupby("season", as_index=False)["PM2.5"].mean()
fig4 = px.bar(pm25_season, x="season", y="PM2.5", color="season", 
             color_discrete_map={"Spring": "#d1c4e9", "Summer": "#ba68c8", "Fall": "#8e24aa", "Winter": "#4a148c"})
fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"), showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.success("📌 Kesimpulan: Malam hari paling berpolusi dan musim dingin mengalami lonjakan PM2.5 tahunan.")
st.caption("Dashboard by Vinda Karunia Surya")
