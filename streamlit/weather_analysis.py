from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from weather_functions import (
    download_weather,
    plot_precipitation_spc,
    plot_temperature_lof,
)

st.title("Weather Analysis")


area_type = st.session_state["reservoir_area_type"]
area_numbers = {"EL": [1, 2, 3, 4, 5], "NO": [0], "VASS": [1, 2, 3]}
numbers = area_numbers[area_type]
area_number = st.selectbox(
    f"Area number ({area_type})",
    numbers,
    index=numbers.index(3) if area_type == "EL" else 0,
)

# Match the saved weather dataset to the selected area.
if area_type == "EL":
    region_id = f"NO {area_number}"
elif area_type == "VASS":
    region_id = {1: "East", 2: "West", 3: "North"}[area_number]
else:
    st.info("Nationwide weather data is unavailable. Select EL or VASS.")
    st.stop()


dates = st.date_input(
    "Weather date range",
    value=(pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-12-31").date()),
)

if len(dates) != 2:
    st.info("Select both a start date and an end date.")
    st.stop()

start_date, end_date = (day.isoformat() for day in dates)

csv_path = Path(__file__).resolve().parents[1] / "data" / "no3_weather_hourly_2024.csv"
use_saved_no3 = (
    (area_number, start_date, end_date) == (3, "2024-01-01", "2024-12-31")
    and csv_path.is_file()
)

if use_saved_no3:
    weather_hourly = pd.read_csv(csv_path)
    weather_hourly["time"] = pd.to_datetime(weather_hourly["time"], utc=True)
    weather_hourly = weather_hourly.set_index("time").sort_index()
    st.caption("NO3 · Hourly ERA5 averages across 1,000 locations · 2024")
else:
    # Reuse the result when a plot control changes and Streamlit reruns the page.
    selection = (region_id, start_date, end_date)
    downloaded = st.session_state.setdefault("downloaded_weather", {})

    if selection not in downloaded:
        if not st.button("Download weather data"):
            st.stop()

        try:
            with st.spinner(f"Downloading weather for {region_id}..."):
                raw = download_weather(
                    region_id, start_date, end_date, max_locations=2
                )
                raw["time"] = pd.to_datetime(raw["time"], utc=True)
                downloaded[selection] = (
                    raw.groupby("time")[["temperature_2m", "precipitation"]]
                    .mean()
                    .sort_index()
                )
        except Exception as exc:
            st.error(f"Weather download failed: {exc}")
            st.stop()

    weather_hourly = downloaded[selection]
    st.caption(f"{region_id} · {start_date} to {end_date} · 2 sampled locations")

spc_tab, lof_tab = st.tabs(["Outlier / SPC", "Anomaly / LOF"])

with spc_tab:
    max_cutoff = len(weather_hourly) - 1
    cutoff = st.number_input(
        "DCT cut-off",
        min_value=1,
        max_value=max_cutoff,
        value=min(30, max_cutoff),
    )

    n_std = st.number_input(
    "Standard deviation multiplier", min_value=0.1, value=3.0
    )

    fig, outliers, summary = plot_precipitation_spc(weather_hourly, cutoff, n_std)
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(pd.Series(summary, name="Value").to_frame())
    st.dataframe(outliers.head(10))

with lof_tab:
    percentage = st.number_input("Outlier percentage", min_value=0.1, max_value=50.0, value=1.0)

    fig, anomalies, summary = plot_temperature_lof(
        weather_hourly, outlier_fraction=percentage / 100
    )
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(pd.Series(summary, name="Value").to_frame())
    st.dataframe(anomalies.sort_values("lof_score", ascending=False).head(10))