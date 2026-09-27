import streamlit as st



#st.sidebar.title("Sidebar")


pages = {
    "HomePage": [
        st.Page("home.py", title="Home"),
        
    ],
    "Page 1": [
        st.Page("table.py", title="Table"),
        
    ],

    "Page 2": [
            st.Page("plot.py", title="Plot"),
            
        ]
   
}

pg = st.navigation(pages, position = "sidebar")
pg.run()