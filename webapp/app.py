import pandas as pd
import streamlit as st
from ui.coach import make_page_coachbot
from ui.friendly import make_page_find_friendly
from ui.home import make_page_home
from ui.stats import make_page_vanity_stats
from ui.team import make_page_join_team

st.set_page_config(
    page_title="Futsal Friend",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


#################
#### startup ####
#################


@st.cache_data
def load_stats(path, **kwargs):
    return pd.read_csv(path, **kwargs)


@st.cache_data
def pre_aggregate_stats(df_p, df_h):
    # merge players and metadata (_p) with historical (_h) stats
    df_agg = df_p.merge(
        df_h.drop(columns=["Reeks", "Stand"]),
        on=["Name", "Team"],
    )

    # overwrite statistics but now grouped by player and team
    # old teams from a player's history are ignored
    num_cols = ["Wedstrijden", "Goals", "Assists"]
    df_agg[num_cols] = df_agg.groupby(["Name", "Team"])[num_cols].transform("sum")

    # add an overall efficiency statistic
    df_agg["(G+A)/W"] = (df_agg["Goals"] + df_agg["Assists"]) / df_agg["Wedstrijden"]

    # remove single-season information
    df_agg = df_agg.drop(columns=["Seizoen"])
    df_agg = df_agg.drop_duplicates()

    return df_agg


df_players = load_stats(
    "data/stats.csv", usecols=["Name", "Team", "_competition", "_region", "_area"]
).drop_duplicates()  # some players appear twice due to errors in the source data
df_stats_historical = load_stats("data/stats_historical_players.csv")

#################
###### app ######
#################

st.title("Futsal Friend")

st.sidebar.title("Services")
NAVBAR_OPTIONS = [
    "Home",
    "🏆 Find Opponent",
    "👫 Find Team",
    "😏 Analyse Stats",
    "📣 Get Advice",
]
page = st.sidebar.selectbox("Navigation", NAVBAR_OPTIONS)

if page == NAVBAR_OPTIONS[0]:
    make_page_home()
elif page == NAVBAR_OPTIONS[1]:
    make_page_find_friendly()
elif page == NAVBAR_OPTIONS[2]:
    make_page_join_team()
elif page == NAVBAR_OPTIONS[3]:
    df_stats_agg = pre_aggregate_stats(df_players, df_stats_historical)
    make_page_vanity_stats(df_players, df_stats_agg)
elif page == NAVBAR_OPTIONS[4]:
    make_page_coachbot()
