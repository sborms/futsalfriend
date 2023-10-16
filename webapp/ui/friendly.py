import streamlit as st
from utils import filter_teams, style_table


def make_page_find_friendly(df_teams):
    st.header("Find a team for a friendly")

    # ask for inputs
    col1, col2, col3, col4, col5 = st.columns(5)
    city = col1.text_input("Town", "Dilbeek")
    address = col2.text_input("Address", "Pajottenstraat")
    km = col3.number_input(
        "Distance (in km)",
        value=10.0,
        min_value=1.0,
        max_value=50.0,
        step=1.0,
        format="%.1f",
    )
    level = col4.selectbox("Level", ["Courtois 💪💪💪", "Casteels 💪💪", "Mignolet 💪"])
    horizon = col5.number_input("When (< days)?", 3, max_value=30)

    # filter teams based on parameters
    df_out = filter_teams(df_teams, city, address, km)

    if len(df_out) == 0:
        st.warning("No teams found for the specified parameters. Try something else!")
        return

    # style output
    df_out = style_table(df_out, drop_cols=["players", "players_active"])

    # display output
    st.markdown("#### Potential play partners 🥰")
    st.markdown("Reach out by going to the respective team page!")
    st.markdown(df_out.to_html(escape=False, index=False), unsafe_allow_html=True)
