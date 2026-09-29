import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler


# --------------------------------------------------
# 1. Read the local CSV file using caching
# --------------------------------------------------

@st.cache_data
def load_data():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "reservoirs.csv"
    )

    df = pd.read_csv(file_path)

    # Rename columns to English
    df = df.rename(columns={
        "dato_Id": "date_id",
        "omrType": "area_type",
        "omrnr": "area_number",
        "iso_aar": "iso_year",
        "iso_uke": "iso_week",
        "fyllingsgrad": "fill_level",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "stored_energy_Twh",
        "neste_Publiseringsdato": "next_publishing_date",
        "fyllingsgrad_forrige_uke": "fill_level_last_week",
        "endring_fyllingsgrad": "change_in_fill_level"
    })

    return df


df = load_data()


# --------------------------------------------------
# 2. Page header
# --------------------------------------------------

st.header("Reservoir Data Plot")


# --------------------------------------------------
# 3. Create month variable
# --------------------------------------------------

# Convert date column to datetime
df["date_id"] = pd.to_datetime(df["date_id"])

# Create a month column for the slider
df["month"] = df["date_id"].dt.to_period("M").astype(str)

# Get all available months
months = sorted(df["month"].unique())


# --------------------------------------------------
# 4. Select column
# --------------------------------------------------

# Allow selection of any CSV column or all columns
column_options = ["All columns"] + df.columns.drop("month").tolist()

selected_column = st.selectbox(
    "Select column",
    column_options
)


# --------------------------------------------------
# 5. Select month range
# --------------------------------------------------

selected_months = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[0])
)

start_month, end_month = selected_months


# Keep only rows within the selected months
filtered_df = df[
    (df["month"] >= start_month)
    & (df["month"] <= end_month)
].copy()


# --------------------------------------------------
# 6. Create plot
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 6))


if selected_column == "All columns":

    # Measurement columns that are meaningful to compare
    measurement_columns = [
        "fill_level",
        "capacity_TWh",
        "stored_energy_Twh",
        "fill_level_last_week",
        "change_in_fill_level"
    ]

    # Scale variables between 0 and 1 because
    # the original variables have different scales
    scaler = MinMaxScaler()

    scaled_df = filtered_df.copy()

    scaled_df[measurement_columns] = scaler.fit_transform(
        filtered_df[measurement_columns]
    )

    # Calculate mean across reservoir areas for each date
    plot_df = (
        scaled_df
        .groupby("date_id")[measurement_columns]
        .mean()
    )

    # Plot all measurement columns together
    plot_df.plot(
        ax=ax,
        style=["-", "-", "-", "--", "-"]
    )

    ax.set_title("Scaled Reservoir Data Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Scaled Value (0–1)")
    ax.legend(title="Variable")


else:

    # Numeric columns
    if pd.api.types.is_numeric_dtype(filtered_df[selected_column]):

        # Calculate mean for each date
        plot_df = (
            filtered_df
            .groupby("date_id")[selected_column]
            .mean()
        )

        ax.plot(
            plot_df.index,
            plot_df.values
        )

        ax.set_title(f"{selected_column} Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel(selected_column)


    # Date column
    elif selected_column == "date_id":

        counts = filtered_df["date_id"].value_counts().sort_index()

        ax.plot(
            counts.index,
            counts.values
        )

        ax.set_title("Observations Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Observations")


    # Categorical columns
    else:

        counts = filtered_df[selected_column].value_counts()

        counts.plot(
            kind="bar",
            ax=ax
        )

        ax.set_title(f"Distribution of {selected_column}")
        ax.set_xlabel(selected_column)
        ax.set_ylabel("Count")


# --------------------------------------------------
# 7. Plot formatting
# --------------------------------------------------

ax.grid(alpha=0.3)

plt.xticks(rotation=45)

plt.tight_layout()


# --------------------------------------------------
# 8. Display plot
# --------------------------------------------------

st.pyplot(fig)