
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Download reservoir data from NVE API
API_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"

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
        "neste_Publiseringsdato": "next_publication_date",
        "fyllingsgrad_forrige_uke": "fill_level_previous_week",
        "endring_fyllingsgrad": "change_in_fill_level"
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date")


st.title("Reservoir Statistics — NVE")

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

start_date, end_date = st.slider(
    "Select date interval",
    min_value=min_date,
    max_value=max_date,
    value=(max(min_date, max_date - pd.Timedelta(days=365)), max_date),
    format="YYYY-MM-DD"
)

# Filter downloaded data by date and area type
df = df[df["date"].dt.date.between(start_date, end_date)]

area = st.radio("Select area type", ["EL", "NO", "VASS"], horizontal=True)
df = df[df["area_type"].astype(str).str.upper() == area]

if df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# Select measurement
labels = {
    "fill_level": "Filling level (%)",
    "capacity_TWh": "Capacity (TWh)",
    "stored_energy_TWh": "Stored energy (TWh)",
    "fill_level_previous_week": "Previous week (%)",
    "change_in_fill_level": "Change (percentage points)"
}

column = st.selectbox(
    "Select measurement",
    list(labels),
    format_func=lambda x: labels[x]
)

# Plot a separate line for each area number
fig, ax = plt.subplots(figsize=(11, 5))

for number, group in df.groupby("area_number"):
    values = pd.to_numeric(group[column], errors="coerce")

    if column in ["fill_level", "fill_level_previous_week", "change_in_fill_level"]:
        values = values * 100

    ax.plot(group["date"], values, label=f"Area {number}")

ax.set(
    title=f"{labels[column]} — {area}",
    xlabel="Date",
    ylabel="Percentage points" if column == "change_in_fill_level"
           else "%" if column in ["fill_level", "fill_level_previous_week"]
           else "TWh"
)
ax.legend(title="Area number")
ax.grid(alpha=0.3)
fig.autofmt_xdate()
st.pyplot(fig)
plt.close(fig)

# Display data and source information
with st.expander("View filtered data"):
    st.dataframe(df, hide_index=True, use_container_width=True)

with st.expander("About the data"):
    st.write(
        "Source: NVE Magasinstatistikk API. "
        "The API endpoint does not accept date parameters, "
        "so the full dataset is downloaded and cached before "
        "the selected date interval is applied."
    )
