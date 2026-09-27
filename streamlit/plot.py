import streamlit as st
import pandas as pd

# Read reservoir data
df = pd.read_csv("data/reservoirs.csv")

# Page title
st.header("Reservoir Data")

# Display the dataframe
st.dataframe(df)


import streamlit as st
import pandas as pd

# Convert date column to datetime
df["dato_Id"] = pd.to_datetime(df["dato_Id"])

# Sort by date
df = df.sort_values("dato_Id")

# Find the first month in the dataset
first_month = df["dato_Id"].dt.to_period("M").min()

# Keep only data from the first month
df_first_month = df[
    df["dato_Id"].dt.to_period("M") == first_month
]

# Create table
table = pd.DataFrame({
    "Variable": [
        "fyllingsgrad",
        "kapasitet_TWh",
        "fylling_TWh",
        "fyllingsgrad_forrige_uke",
        "endring_fyllingsgrad"
    ],

    "Values": [
        df_first_month["fyllingsgrad"].tolist(),
        df_first_month["kapasitet_TWh"].tolist(),
        df_first_month["fylling_TWh"].tolist(),
        df_first_month["fyllingsgrad_forrige_uke"].tolist(),
        df_first_month["endring_fyllingsgrad"].tolist()
    ]
})

# Display table
st.dataframe(
    table,
    column_config={
        "Values": st.column_config.LineChartColumn("Values")
    },
    hide_index=True
)

