import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

from reservoir_functions import (
    plot_reservoir_spectrogram,
    plot_reservoir_stl,
)

API_URL = (
    "https://biapi.nve.no/magasinstatistikk/"
    "api/Magasinstatistikk/HentOffentligData"
)

@st.cache_data(ttl=3600)
def load_data():
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()

    data = pd.DataFrame(response.json()).rename(columns={
        "dato_Id": "date",
        "omrType": "area_type",
        "omrnr": "area_number",
        "fyllingsgrad": "fill_level",
    })

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    return data.dropna(subset=["date"]).sort_values("date")


st.title("Reservoir Analysis")

area_type = st.session_state["reservoir_area_type"]
data = load_data()
area_data = data.loc[data["area_type"].astype(str).str.upper() == area_type]

area_numbers = sorted(area_data["area_number"].dropna().unique())
if not area_numbers:
    st.warning(f"No reservoir data available for {area_type}.")
    st.stop()

st.caption(f"Reservoir area type: {area_type}")
area_number = st.selectbox("Area number", area_numbers)

# Use the selected area's full weekly history for both analyses.
series = area_data.loc[
    area_data["area_number"] == area_number, ["date", "fill_level"]
].copy()
series["fill_level"] = pd.to_numeric(series["fill_level"], errors="coerce") * 100

stl_tab, spectrogram_tab = st.tabs(["STL", "Spectrogram"])

with stl_tab:
    seasonal = st.number_input("Seasonal smoother", min_value=3, value=13, step=2)
    trend = st.number_input("Trend smoother", min_value=53, value=83, step=2)
    robust = st.checkbox("Robust STL", value=True)

    try:
        fig = plot_reservoir_stl(series, seasonal, trend, robust)
        st.pyplot(fig)
        plt.close(fig)
    except ValueError as exc:
        st.warning(str(exc))

with spectrogram_tab:
    window = st.number_input("Window length (weeks)", min_value=2, value=156)
    overlap = st.number_input("Window overlap (weeks)", min_value=0, value=104)

    try:
        fig = plot_reservoir_spectrogram(series, window, overlap)
        st.pyplot(fig)
        plt.close(fig)
    except ValueError as exc:
        st.warning(str(exc))