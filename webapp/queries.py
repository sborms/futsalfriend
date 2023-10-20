import streamlit as st


def query_nbr_next_games(_conn, dates):
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


@st.cache_data
def query_next_games(_conn):
    q = """
        with
        first_home_game as
        (select
            team1 as team,
            date as date_home,
            team2 as opponent
        from (
            select *,
                row_number() over(partition by team1 order by date asc) as row_n
            from schedules
            where goals1 is NULL
        )
        where row_n = 1), 

        first_away_game as
        (select
            team2 as team,
            date as date_away,
            team1 as opponent
        from (
            select *,
                row_number() over(partition by team2 order by date asc) as row_n
            from schedules
            where goals1 is NULL
        )
        where row_n = 1)

        select 
            h.team,
            min(h.date_home, a.date_away) as next_game,
            h.opponent
        from
        first_home_game h
        inner join first_away_game a on h.team = a.team;
    """

    df = _conn.query(q)

    return df
