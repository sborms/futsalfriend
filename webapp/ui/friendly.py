from datetime import datetime, timedelta

import streamlit as st
from utils import filter_teams, style_table


def query_nbr_next_games(conn, dates):
    q = f"""
        with 
        horizon_set as 
        (select
            date,
            team1,
            team2
        from
        schedules
        where goals1 is NULL and date >= '{dates[0]}' and date <= '{dates[1]}'
        order by team1)

        select 
            team,
            sum(n) as games
        from 
        (
        select team1 as team, count(*) as n from horizon_set group by team1
        union all
        select team2 as team, count(*) as n from horizon_set group by team2
        )
        group by team;  
    """

    df = conn.query(q)

    return df


def make_page_find_friendly(conn, df_teams):
    st.header("Find a team for a friendly")

    # ask for inputs
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
    level = col4.selectbox("Level", ["Courtois 💪💪💪", "Casteels 💪💪", "Mignolet 💪"])
    horizon = col5.number_input("When (< days)?", value=14, min_value=3, max_value=30)

    today = datetime.today().strftime("%Y-%m-%d")
    max_date = (datetime.today() + timedelta(days=horizon)).strftime("%Y-%m-%d")

    # filter teams based on parameters
    df_out = filter_teams(df_teams, city, address, km)

    df_n_games = query_nbr_next_games(conn, dates=[today, max_date])
    df_out = df_out.merge(df_n_games, on="team", how="inner")

    if len(df_out) == 0:
        st.warning("No teams found for the specified parameters. Try something else!")
        return

    df_out.sort_values("games", ascending=True, inplace=True)

    # style output
    df_out = style_table(df_out, drop_cols=["total players", "active players"])

    # display output
    st.markdown("#### Potential play partners 🥰")
    st.markdown("Reach out by going to the respective team page!")
    st.write(f"_The last column shows the number of scheduled games until {max_date}._")
    st.markdown(df_out.to_html(escape=False, index=False), unsafe_allow_html=True)
