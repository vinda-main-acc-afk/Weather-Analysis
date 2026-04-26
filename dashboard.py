import sys
import subprocess
import importlib.util
from pathlib import Path

# =========================================================
# AUTO INSTALL PLOTLY
# Ini dibuat supaya error "ModuleNotFoundError: plotly" tidak muncul
# meskipun Streamlit Cloud gagal membaca requirements.txt.
# =========================================================
def install_if_missing(package_name, import_name=None):
    if import_name is None:
        import_name = package_name

    if importlib.util.find_spec(import_name) is None:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            package_name
        ])

install_if_missing("plotly==5.24.1", "plotly")

import streamlit as st
import pandas as pd
import plotly.express as px

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
    file_path = Path(__file__).parent / csv_name

    if not file_path.exists():
        st.error(
            f"File data tidak ditemukan: {csv_name}. "
            "Pastikan file CSV berada di folder yang sama dengan dashboard.py."
        )
        st.stop()

    df = pd.read_csv(file_path)

    if "No" in df.columns:
        df = df.drop(columns=["No"])

    required_cols = ["year", "month", "day", "hour", "PM2.5", "PM10", "TEMP"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Kolom berikut tidak ditemukan di CSV: {missing_cols}")
        st.stop()

    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()

    def get_season(month):
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    df["season"] = df["month"].apply(get_season)
    df["year_month"] = df["datetime"].dt.to_period("M").astype(str)

    return df


df = load_data()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("💜 Filter Dashboard")

year_list = sorted(df["year"].unique().tolist())
selected_year = st.sidebar.multiselect(
    "Pilih Tahun",
    options=year_list,
    default=year_list
)

season_list = ["Spring", "Summer", "Fall", "Winter"]
selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=season_list,
    default=season_list
)

df_filtered = df[
    (df["year"].isin(selected_year)) &
    (df["season"].isin(selected_season))
].copy()

if df_filtered.empty:
    st.warning("Data kosong berdasarkan filter yang dipilih.")
    st.stop()

# =========================
# HEADER
# =========================
st.title("💜 Dashboard Analisis Kualitas Udara Nongzhanguan")
st.markdown("**Berdasarkan Analisis Data di Proyek Analisis Data Vinda**")

# =========================
# METRICS
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.2f}")
with col2:
    st.metric("Rata-rata PM10", f"{df_filtered['PM10'].mean():.2f}")
with col3:
    st.metric("Rata-rata TEMP", f"{df_filtered['TEMP'].mean():.2f}°C")
with col4:
    st.metric("Total Baris Data", f"{len(df_filtered):,}")

st.markdown("---")

# =========================
# CHART 1
# =========================
st.subheader("1. Rata-rata PM2.5 berdasarkan jam")

pm25_hourly = df_filtered.groupby("hour", as_index=False)["PM2.5"].mean()

fig1 = px.line(
    pm25_hourly,
    x="hour",
    y="PM2.5",
    markers=True,
    title="Rata-rata Konsentrasi PM2.5 per Jam",
    color_discrete_sequence=["#6a1b9a"]
)
fig1.update_layout(
    xaxis_title="Jam",
    yaxis_title="Rata-rata PM2.5",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#4a148c")
)
st.plotly_chart(fig1, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 1"):
    max_hour = pm25_hourly.loc[pm25_hourly["PM2.5"].idxmax(), "hour"]
    st.write(f"Konsentrasi PM2.5 tertinggi terjadi sekitar pukul {int(max_hour):02d}:00.")

# =========================
# CHART 2
# =========================
st.subheader("2. Tren bulanan rata-rata PM2.5")

pm25_monthly = df_filtered.groupby("year_month", as_index=False)["PM2.5"].mean()

fig2 = px.line(
    pm25_monthly,
    x="year_month",
    y="PM2.5",
    markers=True,
    title="Tren Bulanan PM2.5",
    color_discrete_sequence=["#8e24aa"]
)
fig2.update_layout(
    xaxis_title="Bulan",
    yaxis_title="Rata-rata PM2.5",
    xaxis_tickangle=-45,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#4a148c")
)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 2"):
    max_month = pm25_monthly.loc[pm25_monthly["PM2.5"].idxmax(), "year_month"]
    min_month = pm25_monthly.loc[pm25_monthly["PM2.5"].idxmin(), "year_month"]
    st.write(f"PM2.5 tertinggi terjadi pada {max_month}, sedangkan terendah pada {min_month}.")

# =========================
# CHART 3
# =========================
st.subheader("3. Korelasi variabel terhadap PM2.5 pada musim dingin")

df_winter = df_filtered[df_filtered["season"] == "Winter"]

if not df_winter.empty:
    corr_cols = [
        "PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
        "TEMP", "PRES", "DEWP", "RAIN", "WSPM"
    ]
    corr_cols = [col for col in corr_cols if col in df_winter.columns]

    corr_matrix = df_winter[corr_cols].corr(numeric_only=True)
    corr_pm25 = (
        corr_matrix["PM2.5"]
        .drop("PM2.5")
        .sort_values(ascending=False)
        .reset_index()
    )
    corr_pm25.columns = ["Variabel", "Korelasi"]

    fig3 = px.bar(
        corr_pm25,
        x="Variabel",
        y="Korelasi",
        title="Korelasi Variabel terhadap PM2.5 di Musim Dingin",
        color="Korelasi",
        color_continuous_scale=["#e1bee7", "#4a148c"]
    )
    fig3.update_layout(
        xaxis_title="Variabel",
        yaxis_title="Nilai Korelasi",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#4a148c")
    )
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("💡 Lihat Insight Pertanyaan 3"):
        top_factor = corr_pm25.iloc[0]
        st.write(
            f"Variabel dengan korelasi positif terkuat terhadap PM2.5 "
            f"di musim dingin adalah {top_factor['Variabel']} "
            f"dengan nilai korelasi {top_factor['Korelasi']:.2f}."
        )
else:
    st.info("Pilih 'Winter' pada sidebar untuk melihat analisis korelasi musim dingin.")

# =========================
# CHART 4
# =========================
st.subheader("4. Rata-rata PM2.5 berdasarkan musim")

pm25_season = df_filtered.groupby("season", as_index=False)["PM2.5"].mean()

season_order = ["Spring", "Summer", "Fall", "Winter"]
pm25_season["season"] = pd.Categorical(
    pm25_season["season"],
    categories=season_order,
    ordered=True
)
pm25_season = pm25_season.sort_values("season")

fig4 = px.bar(
    pm25_season,
    x="season",
    y="PM2.5",
    title="Rata-rata PM2.5 Berdasarkan Musim",
    color="season",
    color_discrete_map={
        "Spring": "#d1c4e9",
        "Summer": "#ba68c8",
        "Fall": "#8e24aa",
        "Winter": "#4a148c"
    }
)
fig4.update_layout(
    xaxis_title="Musim",
    yaxis_title="Rata-rata PM2.5",
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#4a148c")
)
st.plotly_chart(fig4, use_container_width=True)

with st.expander("💡 Lihat Insight Pertanyaan 4"):
    worst_season = pm25_season.loc[pm25_season["PM2.5"].idxmax(), "season"]
    st.write(f"Musim dengan rata-rata PM2.5 tertinggi adalah {worst_season}.")

# =========================
# CONCLUSION
# =========================
st.markdown("---")
st.subheader("📌 Kesimpulan Akhir")
st.success(
    "Dashboard ini menggunakan Plotly dan menampilkan analisis kualitas udara "
    "berdasarkan jam, bulan, musim, serta korelasi variabel terhadap PM2.5."
)

st.caption("Dashboard by Vinda Karunia Surya | Analisis Data Kualitas Udara Nongzhanguan")
