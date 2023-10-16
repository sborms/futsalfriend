import streamlit as st


def make_page_home():
    st.header("Welcome to Futsal Friend, your digital futsal companion")

    st.write(
        """
        _This app is still in early stage of development._
        """
    )

    st.write(
        """
        We currently source data solely from the amazing Belgian amateur 
        futsal organisation [lzvcup.be](https://www.lzvcup.be/).
        
        It should be seen as a complement, not as a replacement. All data used here 
        is publicly available on the organisation's website.
        """
    )
