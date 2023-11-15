import streamlit as st

TTL = 0  # cache time to live in seconds

CONNECTION = st.connection("futsalfriend_db", type="sql", ttl=0)


def query_nbr_next_games(dates):
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

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_teams():
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

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_players():
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

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_stats_agg():
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

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_list_teams():
    return CONNECTION.query("select distinct team from teams;")


@st.cache_data(show_spinner=False, ttl=TTL)
def query_schedule(team):
    q = f"""
        select
            date,
            team1 as 'team home', 
            team2 as 'team away'
        from schedules
        where (goals1 is NULL) and (team1 = '{team}' or team2 = '{team}');
    """

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_stats_players(team):
    q = f"""
        select
            team,
            name,
            wedstrijden as games,
            goals,
            assists
        from stats_players
        where team = '{team}';
    """

    df = CONNECTION.query(q)

    return df


@st.cache_data(show_spinner=False, ttl=TTL)
def query_standings(team):
    q = f"""
        select
            positie as position,
            team,
            gespeeld as games,
            gewonnen as won,
            gelijk as draw,
            verloren as lost,
            dg as 'goals for',
            dt as 'goals against',
            punten as points
        from standings s
        join (
            select distinct region, competition from teams where team = '{team}'
        ) t
        on s.region = t.region and s.competition = t.competition;
    """

    df = CONNECTION.query(q)

    return df
