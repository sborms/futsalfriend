import streamlit as st
from utils import filter_teams, style_table


def make_page_join_team(df_teams):
    st.header("Find a team as a new player")

    # ask for inputs
    col1, col2, col3 = st.columns(3)
    city = col1.text_input("Town", "Brussels")
    address = col2.text_input("Address", "Nieuwstraat")
    km = col3.number_input(
        "Distance (in km)",
        value=2.0,
        min_value=1.0,
        max_value=50.0,
        step=1.0,
        format="%.1f",
    )

    # filter teams based on parameters
    df_out = filter_teams(df_teams, city, address, km)

    if len(df_out) == 0:
        st.warning("No teams found for the specified parameters. Try something else!")
        return

    # style output
    df_out.sort_values("active players", ascending=True, inplace=True)
    df_out = style_table(df_out)

    # display output
    st.markdown("#### Possible teams to join 🤩")
    st.markdown("Reach out by going to the respective team page!")
    st.markdown(df_out.to_html(escape=False, index=False), unsafe_allow_html=True)
