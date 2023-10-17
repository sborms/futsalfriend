import streamlit as st
from ui.coach import make_page_coachbot
from ui.friendly import make_page_spot_friendly
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

CONN = st.experimental_connection("futsalfriend_db", type="sql")


@st.cache_data
def query_players(_conn):
    q = """
        select distinct
            t.area as Area,
            t.region as Region,
            t.competition as Competition,
            c.team as Team,
            c.name as Name
        from
        -- deduplicate because some players appear twice due to errors in source data
        (select distinct name, team from stats_players) c
        join teams t on c.team = t.team
        order by t.area, t.region, t.competition, c.team;
    """

    df = _conn.query(q)

    return df


@st.cache_data
def query_teams(_conn):
    q = """
        select
            t.area,
            t.region,
            t.competition,
            t.team,
            t.url as url_team,
            s.sportshall,
            s.address,
            s.phone,
            s.email,
            s.url_sportshall,
            s.latitude,
            s.longitude,
            p.players as 'total players',
            p.players_active as 'active players'
        from
        teams t 
        inner join locations l on t.team = l.team
        inner join (
            select distinct sportshall, address, phone, email, url_sportshall,
                            latitude, longitude
            from sportshalls
        ) s on l.sportshall = s.sportshall
        left join (
            select team, count(name) as players, sum(wedstrijden > 0) as players_active
            from stats_players
            group by team
        ) p on t.team = p.team
        order by t.team;
    """

    df = _conn.query(q)

    return df


@st.cache_data
def query_stats_agg(_conn):
    q = """
        select distinct
            c.name as Name,
            c.team as Team,
            sum(h.wedstrijden) as Games,
            sum(h.goals) as Goals,
            sum(h.assists) as Assists,
            (sum(h.goals * 1.0) + sum(h.assists)) / sum(h.wedstrijden) as '(G+A)/W'
        from
        (select distinct name, team from stats_players) c
        join stats_players_historical h on c.name = h.name and c.team = h.team
        group by c.name, c.team;
    """

    df = _conn.query(q)

    return df


df_players = query_players(CONN)
df_teams = query_teams(CONN)

#################
###### app ######
#################

st.title("Futsal Friend")

st.sidebar.title("Navigation")
NAVBAR_OPTIONS = [
    "🏠 Home",
    "🏆 Spot Opponent",
    "👫 Find Team",
    "😏 Analyze Stats",
    "📣 Get Advice",
]
page = st.sidebar.selectbox("Pick a service", NAVBAR_OPTIONS)

if page == NAVBAR_OPTIONS[0]:
    make_page_home()
elif page == NAVBAR_OPTIONS[1]:
    make_page_spot_friendly(CONN, df_teams)
elif page == NAVBAR_OPTIONS[2]:
    make_page_join_team(df_teams)
elif page == NAVBAR_OPTIONS[3]:
    df_stats_agg = query_stats_agg(CONN)
    make_page_vanity_stats(df_players, df_stats_agg)
elif page == NAVBAR_OPTIONS[4]:
    make_page_coachbot()
