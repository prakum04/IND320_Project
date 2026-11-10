import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
import json
import time
from pathlib import Path

import requests




def plot_precipitation_spc(weather_hourly, cutoff=30, n_std=3):
    """Return the precipitation SPC plot, flagged hours, and summary."""
    series = weather_hourly["precipitation"].sort_index()
    values = series.to_numpy(dtype=float)

    if not 1 <= cutoff < len(values):
        raise ValueError("cutoff must be between 1 and the series length minus 1.")
    if n_std <= 0:
        raise ValueError("n_std must be positive.")

    # Remove the lowest-frequency DCT coefficients.
    coefficients = dct(values, type=1, norm="forward")
    coefficients[:cutoff] = 0
    variations = idct(coefficients, type=1, norm="forward")
    smooth_component = values - variations

    # Estimate the centre and spread from the whole year.
    centre = stats.trim_mean(variations, proportiontocut=0.05)
    robust_sd = stats.median_abs_deviation(variations) * 1.4826
    half_width = n_std * robust_sd

    # Flag outliers and shift the limits onto the original precipitation scale.
    outlier_mask = np.abs(variations - centre) > half_width
    lower = smooth_component + centre - half_width
    upper = smooth_component + centre + half_width
    outliers = series.loc[outlier_mask].to_frame()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, values, linewidth=0.7, label="Average precipitation")
    ax.plot(series.index, lower, "--", color="orange", label="Lower SPC limit")
    ax.plot(series.index, upper, "--", color="green", label="Upper SPC limit")
    ax.scatter(
        outliers.index, outliers["precipitation"],
        color="red", s=12, zorder=3, label="Outliers"
    )
    ax.set(
        title="Average hourly precipitation with robust SPC limits",
        xlabel="Date",
        ylabel="Precipitation (mm)"
    )
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()

    summary = {
        "Outlier hours": len(outliers),
        "Outlier percentage": round(100 * outlier_mask.mean(), 2),
        "Robust standard deviation": robust_sd,
    }
    return fig, outliers, summary


def plot_temperature_lof(weather_hourly, outlier_fraction=0.01, n_neighbors=20):
    """Plot average temperature and highlight LOF anomalies."""
    series = weather_hourly["temperature_2m"].sort_index()
    values = series.to_numpy(dtype=float)

    # Validate the data and adjustable parameters.
    if len(values) < 3 or not np.isfinite(values).all():
        raise ValueError("Provide at least three finite temperature values.")

    if not 0 < outlier_fraction <= 0.5:
        raise ValueError("outlier_fraction must be between 0 and 0.5.")

    if not isinstance(n_neighbors, (int, np.integer)) or n_neighbors < 2:
        raise ValueError("n_neighbors must be an integer of at least 2.")

    # Scikit-learn expects rows of observations and columns of features.
    X = values.reshape(-1, 1)

    model = LocalOutlierFactor(
        n_neighbors=min(n_neighbors, len(values) - 1),
        contamination=outlier_fraction
    )

    # LOF returns -1 for anomalies and 1 for ordinary observations.
    labels = model.fit_predict(X)
    anomaly_mask = labels == -1

    results = pd.DataFrame({
        "temperature_2m": values,
        # Reverse the sign so larger scores indicate stronger anomalies.
        "lof_score": -model.negative_outlier_factor_,
        "is_anomaly": anomaly_mask
    }, index=series.index)

    anomalies = results.loc[anomaly_mask].copy()

    summary = {
        "observations": len(values),
        "anomaly_hours": int(anomaly_mask.sum()),
        "anomaly_percentage": float(anomaly_mask.mean() * 100),
        "requested_outlier_fraction": outlier_fraction,
        "n_neighbors": model.n_neighbors_
    }

    # Show anomalies on the original temperature time series.
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(
        series.index, values,
        linewidth=0.7, label="Average temperature"
    )
    ax.scatter(
        anomalies.index, anomalies["temperature_2m"],
        color="red", s=18, label="LOF anomalies", zorder=3
    )

    ax.set(
        title="Temperature — Local Outlier Factor",
        xlabel="Date",
        ylabel="Temperature (°C)"
    )
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    return fig, anomalies, summary



def download_weather(region_id, start_date, end_date, max_locations=2):
    # Look up the sampled longitude–latitude pairs.
    

    coordinates_path = (
    Path(__file__).resolve().parents[1] / "data" / "weather_coordinates.json"
    )
    coordinates_by_region = json.loads(coordinates_path.read_text(encoding="utf-8"))
    coordinates = coordinates_by_region[region_id]


    

    if max_locations is not None:
        coordinates = coordinates[:max_locations]

    url = "https://archive-api.open-meteo.com/v1/archive"
    tables = []

    # Create a folder for this region and time interval.
    folder = Path("weather_downloads") / f"{region_id}_{start_date}_{end_date}"
    folder.mkdir(parents=True, exist_ok=True)

    for location_id, (longitude, latitude) in enumerate(coordinates):
        file_path = folder / f"location_{location_id}.csv"

        # Load an existing file and skip downloading this location.
        if file_path.exists():
            weather_df = pd.read_csv(file_path)
            weather_df["time"] = pd.to_datetime(weather_df["time"], utc=True)
            tables.append(weather_df)
            print(f"Loaded saved location {location_id + 1}")
            continue

        # Request hourly ERA5 temperature and precipitation.
        params = {
            "longitude": longitude,
            "latitude": latitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,precipitation",
            "models": "era5",
            "timezone": "UTC"
        }

                # Try at most five times if the API rate limit is reached.
        for attempt in range(5):
            response = requests.get(url, params=params, timeout=120)

            # Other responses leave the retry loop.
            if response.status_code != 429:
                break

            # On the last attempt, raise the error instead of waiting again.
            if attempt == 4:
                response.raise_for_status()

            # Increase the wait after each rate-limit response.
            wait_seconds = 60 * (2 ** attempt)
            print(f"Rate limit reached. Waiting {wait_seconds} seconds.")
            time.sleep(wait_seconds)

        # Report HTTP errors and decode successful responses.
        response.raise_for_status()
        data = response.json()

        # Convert the response to a table.
        weather_df = pd.DataFrame(data["hourly"])
        weather_df["time"] = pd.to_datetime(weather_df["time"], utc=True)

        # Identify the region and requested location.
        weather_df["region"] = region_id
        weather_df["location_id"] = location_id
        weather_df["longitude"] = longitude
        weather_df["latitude"] = latitude

        # Save each completed download before moving to the next location.
        weather_df.to_csv(file_path, index=False)
        tables.append(weather_df)
        print(f"Downloaded location {location_id + 1}/{len(coordinates)}")

    return pd.concat(tables, ignore_index=True)