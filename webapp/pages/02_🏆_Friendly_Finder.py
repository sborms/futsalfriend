from datetime import datetime, timedelta

import streamlit as st
import utils

st.set_page_config(page_title="Friendly Finder", page_icon="🏆", layout="wide")

import queries
df_teams = queries.query_teams()

##################
########## UI   ##
##################

st.title("Friendly Finder")
st.markdown("### Score an opponent for a friendly")

# ask for inputs
levels = {"Courtois 💪💪💪": 1, "Casteels 💪💪": 2, "Mignolet 💪": 3}

col1, col2, col3, col4, col5 = st.columns(5)
city = col1.text_input("Town", "Tervuren")
address = col2.text_input("Address", "Lindeboomstraat")
km = col3.number_input(
    "Distance (in km)",
    value=10.0,
    min_value=1.0,
    max_value=50.0,
    step=1.0,
    format="%.1f",
)
level = col4.selectbox("Level", levels.keys(), index=2)
horizon = col5.number_input("When (< days)?", value=14, min_value=3, max_value=30)

today = utils.LAST_UPDATED
max_date = (
    datetime.strptime(today, "%Y-%m-%d").date() + timedelta(days=horizon)
).strftime("%Y-%m-%d")

# show output header
st.markdown("#### Potential play partners 🥰")

with st.spinner("Finding teams..."):
    st.cache_data.clear()

    # query tables for specified parameters
    df_levels = queries.CONNECTION.query(
        f"select team from levels where level = {levels[level]};"
    )
    df_n_games = queries.query_nbr_next_games(dates=[today, max_date])

    # filter teams based on remaining parameters
    df_out = utils.filter_teams(df_teams, city, address, km)

    # join tables together
    df_out = (
        df_out.merge(df_n_games, on="team", how="left")
        .fillna(0)  # set no games to 0
        .merge(df_levels, on="team", how="inner")
    )

    if len(df_out) == 0:
        st.warning("No teams found for the specified parameters. Try something else!")
    else:
        # style output
        df_out.sort_values("games", ascending=True, inplace=True)
        df_out = utils.style_table(
            df_out, drop_cols=["total players", "active players"]
        )

        # display table
        st.write(
            f"_The last column shows the amount of scheduled games between {today} and {max_date}._"
        )
        st.markdown(df_out.to_html(escape=False, index=False), unsafe_allow_html=True)
