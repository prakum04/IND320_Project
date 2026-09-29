import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler


# Reading the local CSV file using caching
@st.cache_data
def load_data():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "reservoirs.csv"
    )

    df = pd.read_csv(file_path)

    # Renaming columns to English
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


# Loading the data
df = load_data()


# Adding the page header
st.header("Reservoir Data Plot")


# Converting the date column to datetime
df["date_id"] = pd.to_datetime(df["date_id"])


# Creating a month column for the slider
df["month"] = df["date_id"].dt.to_period("M").astype(str)


# Getting all available months
months = sorted(df["month"].unique())


# Creating options for selecting a single column or all columns
column_options = ["All columns"] + df.columns.drop("month").tolist()


# Creating the column selectbox
selected_column = st.selectbox(
    "Select column",
    column_options
)


# Creating the month range slider
selected_months = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[0])
)

start_month, end_month = selected_months


# Filtering the data using the selected months
filtered_df = df[
    (df["month"] >= start_month)
    & (df["month"] <= end_month)
].copy()


# Creating the plot
fig, ax = plt.subplots(figsize=(12, 6))


if selected_column == "All columns":

    # Selecting the measurement columns to compare
    measurement_columns = [
        "fill_level",
        "capacity_TWh",
        "stored_energy_Twh",
        "fill_level_last_week",
        "change_in_fill_level"
    ]

    # Scaling the measurement variables between 0 and 1
    scaler = MinMaxScaler()

    scaled_df = filtered_df.copy()

    scaled_df[measurement_columns] = scaler.fit_transform(
        filtered_df[measurement_columns]
    )

    # Grouping the data by date and calculating the mean across areas
    plot_df = (
        scaled_df
        .groupby("date_id")[measurement_columns]
        .mean()
    )

    # Plotting all measurement columns together
    plot_df.plot(
        ax=ax,
        style=["-", "-", "-", "--", "-"]
    )

    # Adding the plot title and axis labels
    ax.set_title("Scaled Reservoir Data Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Scaled Value (0–1)")
    ax.legend(title="Variable")


else:

    # Checking if the selected column is numerical
    if pd.api.types.is_numeric_dtype(filtered_df[selected_column]):

        # Grouping the selected variable by date and calculating the mean
        plot_df = (
            filtered_df
            .groupby("date_id")[selected_column]
            .mean()
        )

        # Plotting the selected numerical variable
        ax.plot(
            plot_df.index,
            plot_df.values
        )

        # Adding the plot title and axis labels
        ax.set_title(f"{selected_column} Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel(selected_column)


    # Checking if the selected column is the date column
    elif selected_column == "date_id":

        # Counting the number of observations for each date
        counts = filtered_df["date_id"].value_counts().sort_index()

        # Plotting the number of observations over time
        ax.plot(
            counts.index,
            counts.values
        )

        # Adding the plot title and axis labels
        ax.set_title("Observations Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Observations")


    else:

        # Counting the values in the selected categorical column
        counts = filtered_df[selected_column].value_counts()

        # Plotting the categorical variable
        counts.plot(
            kind="bar",
            ax=ax
        )

        # Adding the plot title and axis labels
        ax.set_title(f"Distribution of {selected_column}")
        ax.set_xlabel(selected_column)
        ax.set_ylabel("Count")


# Adding grid lines to the plot
ax.grid(alpha=0.3)


# Rotating the x-axis labels
plt.xticks(rotation=45)


# Adjusting the plot layout
plt.tight_layout()


# Displaying the plot in Streamlit
st.pyplot(fig)