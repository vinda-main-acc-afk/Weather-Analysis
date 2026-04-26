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

# 2. Custom CSS for Styling (Tetap mempertahankan style ungu & teks hitam)
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

# 3. Data Loading and Preprocessing (Sesuai tahap Data Wrangling di IPYNB)
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "PRSA_Data_Nongzhanguan_20130301-20170228.csv")
    
    if not os.path.exists(file_path):
        file_path = "PRSA_Data_Nongzhanguan_20130301-20170228.csv"

    df = pd.read_csv(file_path)
    
    # Cleaning: Menghilangkan kolom 'No' jika ada
    if "No" in df.columns:
        df = df.drop(columns="No")

    # Membuat kolom datetime
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    # Handling missing values (Interpolasi linear sesuai IPYNB)
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()

    # Penentuan Musim
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

# --- VISUALISASI BERDASARKAN IPYNB ---

# 7. Pertanyaan 1: Jam dengan Polusi Terburuk
st.subheader("1. Kapan kualitas udara paling buruk dalam sehari?")
pm25_hourly = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()
fig1 = px.line(pm25_hourly, x="hour", y="PM2.5", markers=True, 
               title="Rata-rata Konsentrasi PM2.5 per Jam", 
               color_discrete_sequence=["#6a1b9a"])
fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig1, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 1"):
    st.write("""
    Berdasarkan visualisasi, konsentrasi **PM2.5 cenderung meningkat pada malam hari**, puncaknya terjadi sekitar jam **20:00 hingga 23:00**. 
    Hal ini kemungkinan disebabkan oleh penurunan suhu permukaan dan aktivitas pembuangan emisi yang terperangkap di lapisan atmosfer yang lebih rendah pada malam hari.
    """)

# 8. Pertanyaan 2: Tren per Bulan
st.subheader("2. Bagaimana tren kualitas udara per bulan selama periode pengamatan?")
pm25_monthly = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()
fig2 = px.line(pm25_monthly, x="year_month", y="PM2.5", 
               title="Tren Bulanan PM2.5 (2013-2017)", 
               color_discrete_sequence=["#8e24aa"])
fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
st.plotly_chart(fig2, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 2"):
    st.write("""
    Kualitas udara menunjukkan **fluktuasi musiman yang sangat jelas setiap tahunnya**. 
    Tingkat polusi PM2.5 tertinggi secara konsisten terjadi pada **akhir tahun (Desember) hingga awal tahun (Januari)**, 
    menunjukkan adanya pola siklus tahunan yang berkaitan erat dengan musim.
    """)

# 9. Pertanyaan 3: Faktor di Musim Dingin (Winter)
st.subheader("3. Faktor apa yang paling mempengaruhi polusi udara pada musim dingin?")
df_winter = df_filtered[df_filtered["season"] == "Winter"]
if not df_winter.empty:
    corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    corr_matrix = df_winter[corr_cols].corr()
    corr_pm25 = corr_matrix["PM2.5"].drop("PM2.5").sort_values(ascending=False).reset_index()
    corr_pm25.columns = ["Variabel", "Korelasi"]
    
    fig3 = px.bar(corr_pm25, x="Variabel", y="Korelasi", 
                  title="Korelasi Variabel terhadap PM2.5 di Musim Dingin", 
                  color="Korelasi", color_continuous_scale=["#e1bee7", "#4a148c"])
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"))
    st.plotly_chart(fig3, use_container_width=True)
    
    with st.expander("💡 Lihat Insight Pertanyaan 3"):
        st.write("""
        Pada musim dingin, **PM10 dan CO** memiliki korelasi positif paling kuat dengan PM2.5. 
        Selain itu, **Dew Point (DEWP)** juga menunjukkan pengaruh yang signifikan, menandakan bahwa kelembapan dan partikel polutan lain 
        bergerak beriringan meningkatkan polusi di musim dingin.
        """)
else:
    st.info("Pilih 'Winter' pada sidebar untuk melihat analisis korelasi musim dingin.")

# 10. Pertanyaan 4: Perbandingan Musim
st.subheader("4. Apakah tingkat polusi berbeda signifikan antar musim?")
pm25_season = df_filtered.groupby("season", as_index=False)["PM2.5"].mean()
season_order = ["Spring", "Summer", "Fall", "Winter"]
pm25_season["season"] = pd.Categorical(pm25_season["season"], categories=season_order, ordered=True)
pm25_season = pm25_season.sort_values("season")

fig4 = px.bar(pm25_season, x="season", y="PM2.5", 
             title="Rata-rata PM2.5 Berdasarkan Musim", 
             color="season",
             color_discrete_map={"Spring": "#d1c4e9", "Summer": "#ba68c8", "Fall": "#8e24aa", "Winter": "#4a148c"})
fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#4a148c"), showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 4"):
    st.write("""
    **Musim Dingin (Winter) adalah musim dengan tingkat polusi terburuk**, diikuti oleh Musim Semi (Spring). 
    Musim Panas (Summer) cenderung memiliki tingkat PM2.5 yang paling rendah dibandingkan musim lainnya.
    """)

# 11. Final Conclusion (Sesuai Conclusion di IPYNB)
st.markdown("---")
st.subheader("📌 Kesimpulan Akhir")
st.success("""
1. Kualitas udara di Nongzhanguan sangat dipengaruhi oleh waktu, di mana **malam hari adalah waktu paling berpolusi**.
2. Terdapat tren musiman di mana **musim dingin mengalami lonjakan PM2.5 yang signifikan** setiap tahunnya.
3. Faktor seperti PM10, CO, dan DEWP menjadi indikator utama meningkatnya polusi.
""")

st.caption("Dashboard by Vinda Karunia Surya | Analisis Data Kualitas Udara Nongzhanguan")
