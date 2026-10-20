
import streamlit as st
import pandas as pd
import requests

API_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"

# Download data from NVE
@st.cache_data(ttl=3600)
def load_data():
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json()).rename(columns={
        "dato_Id": "date",
        "omrType": "area_type",
        "omrnr": "area_number",
        "iso_aar": "year",
        "iso_uke": "week",
        "fyllingsgrad": "fill_level",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "stored_energy_TWh",
        "fyllingsgrad_forrige_uke": "fill_level_previous_week",
        "endring_fyllingsgrad": "change_in_fill_level",
        "neste_Publiseringsdato": "next_publication_date"
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date")


st.title("Reservoir Data — NVE API")

try:
    df = load_data()
except requests.RequestException as e:
    st.error(f"Could not download NVE data: {e}")
    st.stop()

if df.empty:
    st.warning("No reservoir data available.")
    st.stop()

# Select date interval
min_date = df["date"].min().date()
max_date = df["date"].max().date()
default_start = max(min_date, max_date - pd.Timedelta(days=365))

start_date, end_date = st.slider(
    "Select date interval",
    min_value=min_date,
    max_value=max_date,
    value=(default_start, max_date),
    format="YYYY-MM-DD"
)

df = df[df["date"].dt.date.between(start_date, end_date)]

# Select area type and measurement
area = st.radio("Select area type", ["EL", "NO", "VASS"], horizontal=True)
df = df[df["area_type"].astype(str).str.upper() == area].copy()

measurements = [
    "fill_level",
    "capacity_TWh",
    "stored_energy_TWh",
    "fill_level_previous_week",
    "change_in_fill_level"
]

measurement = st.selectbox("Select measurement", measurements)

if df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# Build a line chart for each area number
rows = []

for number, group in df.groupby("area_number"):
    group = group.sort_values("date")
    values = pd.to_numeric(group[measurement], errors="coerce")

    if measurement in [
        "fill_level",
        "fill_level_previous_week",
        "change_in_fill_level"
    ]:
        values = values * 100

    rows.append({
        "Area number": number,
        "Development": values.tolist()
    })

st.dataframe(
    pd.DataFrame(rows),
    column_config={
        "Development": st.column_config.LineChartColumn(
            "Development over selected period"
        )
    },
    hide_index=True,
    use_container_width=True
)

with st.expander("View source data"):
    st.dataframe(df, hide_index=True, use_container_width=True)
