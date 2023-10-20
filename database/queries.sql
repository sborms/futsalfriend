/* players */
select distinct
    t.area as Area,
    t.region as Region,
    t.competition as Competition,
    c.team as Team,
    c.name as Name
from
(select distinct name, team from stats_players) c
join teams t on c.team = t.team
order by t.area, t.region, t.competition, c.team;

/* teams basetable */
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
    p.players,
    p.players_active
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

/* aggregated statistics */
select distinct
    c.name as Name,
    c.team as Team,
    sum(h.wedstrijden) as Wedstrijden,
    sum(h.goals) as Goals,
    sum(h.assists) as Assists,
    (sum(h.goals * 1.0) + sum(h.assists)) / sum(h.wedstrijden) as '(G+A)/W'
from
-- deduplicate because some players appear twice due to errors in source data
(select distinct name, team from stats_players) c
join stats_players_historical h on c.name = h.name and c.team = h.team
group by c.name, c.team;

/* schedule - next game date */
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

/* schedule - number of games within horizon */
with 
horizon_set as 
(select
    date,
    team1,
    team2
from
schedules
where goals1 is NULL and date >= '2023-10-16' and date <= '2023-11-05'
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

/* teams */
select
    t.*,
    name,
    wedstrijden as games,
    goals,
    assists
from stats_players s 
join (
    select area, region, competition, team from teams
) t on s.team = t.team;

/* standings */
select
    area,
    region,
    competition,
    positie as position,
    team,
    gespeeld as games,
    gewonnen as won,
    gelijk as draw,
    verloren as lost,
    dg as 'goals for',
    dt as 'goals against',
    punten as points
from standings;
