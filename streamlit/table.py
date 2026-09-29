import streamlit as st
import pandas as pd
from pathlib import Path


# Read reservoir data using caching
@st.cache_data
def load_data():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "reservoirs.csv"
    )

    return pd.read_csv(file_path)


df = load_data()


# Page title
st.header("Reservoir Data - First Month")


# Convert date column to datetime
df["dato_Id"] = pd.to_datetime(df["dato_Id"])

# Sort by date
df = df.sort_values("dato_Id")


# Find the first month
first_month = df["dato_Id"].dt.to_period("M").min()


# Keep only data from the first month
df_first_month = df[
    df["dato_Id"].dt.to_period("M") == first_month
]


# Create one row for every CSV column
rows = []

for column in df.columns:

    # Line charts require numeric values
    if pd.api.types.is_numeric_dtype(df_first_month[column]):
        values = df_first_month[column].tolist()
    else:
        values = []

    rows.append({
        "Variable": column,
        "Values": values
    })


table = pd.DataFrame(rows)


# Display table
st.dataframe(
    table,
    column_config={
        "Values": st.column_config.LineChartColumn(
            "First month"
        )
    },
    hide_index=True
)