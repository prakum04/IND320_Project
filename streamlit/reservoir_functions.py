import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL

def plot_reservoir_stl(
    reservoir_df,
    seasonal_smoother=19,
    trend_smoother=83,
    robust=True
):
    """Decompose weekly filling levels into trend, seasonality and residuals."""

    # Create a weekly time series from the already checked data.
    series = (
        reservoir_df
        .sort_values("date")
        .set_index("date")["fill_level"]
        .asfreq("W-SUN")
    )

    if series.isna().any():
        raise ValueError("The weekly series contains missing values.")

    # STL requires odd smoother lengths and a trend window above the period.
    if seasonal_smoother < 3 or seasonal_smoother % 2 == 0:
        raise ValueError("seasonal_smoother must be odd and at least 3.")

    if trend_smoother <= 52 or trend_smoother % 2 == 0:
        raise ValueError("trend_smoother must be odd and greater than 52.")

    # Approximate annual seasonality with a 52-week cycle.
    result = STL(
        series,
        period=52,
        seasonal=seasonal_smoother,
        trend=trend_smoother,
        robust=robust
    ).fit()

    # Plot the original series and its three components.
    fig = result.plot()
    # Make the residual markers smaller.
    for line in fig.axes[3].lines:
        line.set_markersize(2)
    fig.set_size_inches(12, 9)
    fig.axes[0].set_ylabel("Filling (%)")
    fig.axes[1].set_ylabel("Trend (%)")
    fig.axes[2].set_ylabel("Seasonal\n(pp)")
    fig.axes[3].set_ylabel("Residual\n(pp)")
    fig.suptitle("Reservoir filling — STL decomposition", y=1.02)
    fig.tight_layout()

    return fig



def plot_reservoir_spectrogram(
    reservoir_df, window_length=156, window_overlap=104
):
    """Plot a spectrogram of weekly reservoir filling levels."""
    series = (
        reservoir_df.sort_values("date")
        .set_index("date")["fill_level"]
        .asfreq("W-SUN")
    )

    if not np.isfinite(series.to_numpy()).all():
        raise ValueError("The weekly series must have no missing or infinite values.")

    if not 2 <= window_length <= len(series):
        raise ValueError("Window length must be between 2 and the series length.")

    if not 0 <= window_overlap < window_length:
        raise ValueError("Overlap must be non-negative and smaller than the window.")

    # One observation per week: frequencies are measured in cycles per week.
    frequencies, times, power = spectrogram(
        series.to_numpy(),
        fs=1.0,
        window="hann",
        nperseg=window_length,
        noverlap=window_overlap,
        detrend="constant",
        scaling="density",
        mode="psd"
    )

    # Convert window-centre times from elapsed weeks to calendar dates.
    dates = series.index[0] + pd.to_timedelta(times * 7, unit="D")

    # Express power relative to the strongest value, in decibels.
    relative_power = power / max(power.max(), np.finfo(float).tiny)
    power_db = 10 * np.log10(np.maximum(relative_power, 1e-12))

    fig, ax = plt.subplots(figsize=(12, 5))
    mesh = ax.pcolormesh(
        mdates.date2num(dates.to_pydatetime()),
        frequencies * 52,
        power_db,
        shading="auto",
        cmap="viridis"
    )

    # Focus on slower cycles, including the annual cycle.
    ax.set_ylim(0, 6)
    ax.axhline(1, color="white", linestyle="--", label="52-week cycle")
    ax.set(
        title="Reservoir filling — Spectrogram",
        xlabel="Date",
        ylabel="Cycles per 52 weeks"
    )
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend()
    fig.colorbar(mesh, ax=ax, label="Power relative to maximum (dB)")
    fig.tight_layout()

    return fig