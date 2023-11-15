import streamlit as st
import utils

st.set_page_config(page_title="Team Finder", page_icon="👫", layout="wide")

import queries
df_teams = queries.query_teams()

##################
########## UI   ##
##################

st.title("Team Finder")
st.markdown("### Find a team as a new player")

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

# show output header
st.markdown("#### Possible teams to join 🤩")

with st.spinner("Finding teams..."):
    st.cache_data.clear()

    # filter teams based on parameters
    df_out = utils.filter_teams(df_teams, city, address, km)
    
    if len(df_out) == 0:
        st.warning("No teams found for the specified parameters. Try something else!")
    else:
        # style output
        df_out.sort_values("active players", ascending=True, inplace=True)
        df_out = utils.style_table(df_out)

        # display table
        st.markdown("Reach out by going to the respective team page!")
        st.markdown(df_out.to_html(escape=False, index=False), unsafe_allow_html=True)
