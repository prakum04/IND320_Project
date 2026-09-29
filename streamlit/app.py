import streamlit as st



pages = {
    "Page 1": [
        st.Page("home.py", title="Home"),
        
    ],
    "Page 2": [
        st.Page("table.py", title="Table"),
        
    ],

    "Page 3": [
            st.Page("plot.py", title="Plot"),
            
        ],

    "Page 4": [
                st.Page("page_4.py", title="Page 4"),
                
            ]
   
}

pg = st.navigation(pages, position = "sidebar")
pg.run()