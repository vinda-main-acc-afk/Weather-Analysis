import streamlit as st
import pandas as pd
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
    [data-testid="stSidebarContent"] .stWidgetLabel p, 
    [data-testid="stSidebarContent"] label p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #000000 !important;
    }
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

# 3. Data Loading and Preprocessing
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

    # Handling missing values sesuai IPYNB
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

# 7. Analysis 1: Jam dengan Polusi Terburuk
st.subheader("1. Pada jam berapa rata-rata konsentrasi PM2.5 tertinggi terjadi di Kota Nongzhanguan selama periode Maret 2013 hingga Februari 2017?")
pm25_hourly = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()
st.line_chart(pm25_hourly.set_index("hour")["PM2.5"], use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 1"):
    st.write("Berdasarkan visualisasi, konsentrasi PM2.5 cenderung meningkat pada malam hari, puncaknya terjadi sekitar jam 20:00 hingga 23:00.")

# 8. Analysis 2: Tren Bulanan
st.subheader("2. Bagaimana tren bulanan rata-rata PM2.5 di Kota Nongzhanguan dari Maret 2013 sampai Februari 2017, dan pada bulan apa terjadi peningkatan atau penurunan signifikan?")
pm25_monthly = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()
st.line_chart(pm25_monthly.set_index("year_month")["PM2.5"], use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 2"):
    st.write("Tingkat polusi PM2.5 tertinggi secara konsisten terjadi pada akhir tahun (Desember) hingga awal tahun (Januari).")

# 9. Analysis 3: Korelasi Musim Dingin
st.subheader("3. Faktor cuaca apa yang paling berkontribusi terhadap lonjakan PM2.5 pada musim dingin (Desember–Februari) di Kota Nongzhanguan selama periode pengamatan?")
df_winter = df_filtered[df_filtered["season"] == "Winter"]
if not df_winter.empty:
    corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    corr_matrix = df_winter[corr_cols].corr()
    corr_pm25 = corr_matrix["PM2.5"].drop("PM2.5").sort_values(ascending=False).reset_index()
    corr_pm25.columns = ["Variabel", "Korelasi"]
    
    st.bar_chart(corr_pm25.set_index("Variabel")["Korelasi"], use_container_width=True)
    
    with st.expander("💡 Lihat Insight Pertanyaan 3"):
        st.write("Pada musim dingin, PM10 dan CO memiliki korelasi positif paling kuat dengan PM2.5.")
else:
    st.info("Pilih 'Winter' pada sidebar untuk melihat analisis korelasi musim dingin.")

# 10. Analysis 4: Perbandingan Musim
st.subheader("4. Apakah terdapat perbedaan signifikan rata-rata PM2.5 antar musim (spring, summer, fall, winter) di Kota Nongzhanguan pada tahun 2013–2017, dan musim mana yang memiliki kualitas udara terburuk?")
pm25_season = df_filtered.groupby("season", as_index=False)["PM2.5"].mean()
season_order = ["Spring", "Summer", "Fall", "Winter"]
pm25_season["season"] = pd.Categorical(pm25_season["season"], categories=season_order, ordered=True)
pm25_season = pm25_season.sort_values("season")

st.bar_chart(pm25_season.set_index("season")["PM2.5"], use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 4"):
    st.write("Musim Dingin (Winter) adalah musim dengan tingkat polusi terburuk.")

# 11. Final Conclusion
st.markdown("---")
st.subheader("📌 Kesimpulan Akhir")
st.success("Malam hari adalah waktu paling berpolusi, dan musim dingin mengalami lonjakan PM2.5 yang signifikan setiap tahunnya.")

st.caption("Dashboard by Vinda Karunia Surya | Analisis Data Kualitas Udara Nongzhanguan")
