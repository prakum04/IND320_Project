
import streamlit as st

pages = {
    "Home": [
        st.Page("home.py", title="Home"),
    ],
    "NVE Reservoir Data": [
        st.Page("table.py", title="Data Table"),
        st.Page("plot.py", title="Reservoir Plots"),
    ],
    "ENTSO-E Electricity Data": [
        st.Page("entsoe.py", title="Electricity Transfers"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
