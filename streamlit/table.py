import streamlit as st
import pandas as pd
from pathlib import Path


# Reading the reservoir data using caching
@st.cache_data
def load_data():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "reservoirs.csv"
    )

    return pd.read_csv(file_path)


# Loading the data
df = load_data()


# Adding the page title
st.header("Reservoir Data - First Month")


# Converting the date column to datetime
df["dato_Id"] = pd.to_datetime(df["dato_Id"])


# Sorting the data by date
df = df.sort_values("dato_Id")


# Finding the first month in the dataset
first_month = df["dato_Id"].dt.to_period("M").min()


# Filtering the data to keep only the first month
df_first_month = df[
    df["dato_Id"].dt.to_period("M") == first_month
]


# Creating one row for every CSV column
rows = []

for column in df.columns:

    # Checking if the column contains numeric values
    if pd.api.types.is_numeric_dtype(df_first_month[column]):
        values = df_first_month[column].tolist()
    else:
        values = []

    # Adding the column name and values to the table
    rows.append({
        "Variable": column,
        "Values": values
    })


# Creating the table
table = pd.DataFrame(rows)


# Displaying the table with line charts for numeric values
st.dataframe(
    table,
    column_config={
        "Values": st.column_config.LineChartColumn(
            "First month"
        )
    },
    hide_index=True
)