import streamlit as st


def make_page_coachbot():
    st.header("Seek advice from an AI futsal coach")

    st.markdown("**Under construction**")

    user_input = st.text_input("Ask your question here")
    if user_input:
        st.write("Offense is the best defense!")
