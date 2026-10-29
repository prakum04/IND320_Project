
import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pathlib import Path

st.title("Cross-Border Electricity Transfers")

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    mongo_uri = st.secrets["MONGODB_URI"]
except (KeyError, FileNotFoundError):
    mongo_uri = os.getenv("MONGODB_URI")

if not mongo_uri:
    st.error("MongoDB connection string is missing.")
    st.stop()

@st.cache_data(ttl=3600)
def load_data(uri):
    client = MongoClient(uri)
    documents = list(
        client["ind320"]["electricity_transfers"].find({}, {"_id": 0})
    )
    client.close()
    return pd.DataFrame(documents)

df = load_data(mongo_uri)

if df.empty:
    st.warning("No electricity transfer data found in MongoDB.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

left, right = st.columns([1, 1.5], gap="large")

with left:
    st.subheader("Annual Imports and Exports")

    connection = st.radio(
        "Select connection",
        sorted(df["connection"].unique())
    )

    available_years = sorted(df["year"].unique(), reverse=True)

    year = st.selectbox("Select year", available_years)

    df_year = df[
        (df["connection"] == connection) &
        (df["year"] == year)
    ]

    pie_data = (
        df_year.groupby("direction", as_index=False)["total_mwh"]
        .sum()
    )

    fig_pie = px.pie(
        pie_data,
        names="direction",
        values="total_mwh",
        title=f"{connection} — {year}"
    )

    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("Monthly Electricity Transfers")

    months = {
        1: "Jan", 2: "Feb", 3: "Mar",
        4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep",
        10: "Oct", 11: "Nov", 12: "Dec"
    }

    selected_months = st.pills(
        "Select months",
        options=list(months.keys()),
        format_func=lambda month: months[month],
        selection_mode="multi",
        default=[1]
    )

    df_month = df[
        (df["connection"] == connection) &
        (df["year"] == year) &
        (df["month"].isin(selected_months or []))
    ]

    if df_month.empty:
        st.info("No data for the selected months.")
    else:
        fig_line = px.line(
            df_month.sort_values("date"),
            x="date",
            y="total_mwh",
            color="direction",
            markers=True,
            title=f"{connection} — {year}",
            labels={
                "date": "Date",
                "total_mwh": "Electricity transferred (MWh)",
                "direction": "Direction"
            }
        )

        st.plotly_chart(fig_line, use_container_width=True)

with st.expander("About the data"):
    st.write(
        "Source: ENTSO-E Transparency Platform. "
        "The data represents physical electricity flows between "
        "Norway and neighboring countries. "
        "Raw observations were stored in Cassandra using Spark, "
        "then aggregated into daily energy totals and uploaded "
        "to MongoDB Atlas."
    )
