import os
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

st.title("Electricity Prices in Norway")
st.write("Daily electricity price statistics from ENTSO-E.")

@st.cache_data(ttl=600)
def load_data():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI is not configured")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        collection = client["ind320"]["daily_electricity_prices"]
        records = list(collection.find({}, {"_id": 0}).sort("date", 1))
    finally:
        client.close()

    return pd.DataFrame(records)

try:
    df = load_data()

    if df.empty:
        st.warning("No electricity price data found.")
    else:
        st.subheader("Daily Electricity Prices")
        st.dataframe(df, use_container_width=True)

        st.subheader("Average Price (EUR/MWh)")
        st.line_chart(df.set_index("date")["avg_price"])

        st.subheader("Minimum and Maximum Prices")
        st.bar_chart(df.set_index("date")[["min_price", "max_price"]])

except Exception as e:
    st.error(f"Could not load electricity price data: {e}")