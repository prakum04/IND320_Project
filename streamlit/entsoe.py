
import os
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

st.title("Electricity Transfers — ENTSO-E")

# Connect to MongoDB Atlas
@st.cache_resource
def connect_to_mongodb():
    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:
        raise ValueError("MONGODB_URI not found in .env file")

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=15000
    )

    client.admin.command("ping")
    return client


try:
    client = connect_to_mongodb()
    db = client["ind320"]

    st.success("Connected to MongoDB Atlas!")

    # Display available collections
    collections = db.list_collection_names()

    st.subheader("MongoDB Collections")
    st.write(collections)

except Exception as e:
    st.error("Could not connect to MongoDB.")
    st.code(str(e))
