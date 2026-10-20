
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
        st.Page("electricity.py", title="Electricity Prices"),
    ],
    "Other": [
        st.Page("page_4.py", title="Page 4"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
