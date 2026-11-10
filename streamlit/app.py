
import streamlit as st

pages = {
    "Home": [
        st.Page("home.py", title="Home"),
    ],
    "NVE Reservoir Data": [
        st.Page("table.py", title="Data Table"),
        st.Page("plot.py", title="Reservoir Plots"),
        st.Page("reservoir_analysis.py", title="Reservoir Analysis"),
    ],
    "ENTSO-E Electricity Data": [
        st.Page("entsoe.py", title="Electricity Transfers"),
    ],
    "Weather": [
    st.Page("weather_analysis.py", title="Weather Analysis"),
],
}

st.sidebar.radio(
    "Reservoir area type",
    ["EL", "NO", "VASS"],
    key="reservoir_area_type",
)

pg = st.navigation(pages, position="sidebar")
pg.run()
