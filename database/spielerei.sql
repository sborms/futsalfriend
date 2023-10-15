select distinct
    c.name as name,
    c.team as team,
    sum(h.wedstrijden) as wedstrijden,
    sum(h.goals) as goals,
    sum(h.assists) as assists,
    (sum(h.goals * 1.0) + sum(h.assists)) / sum(h.wedstrijden) as '(G+A)/W'
from
(select distinct name, team from stats_players) as c -- some players appear twice due to errors in the source data
join stats_players_historical h on c.name = h.name and c.team = h.team
group by c.name, c.team

select distinct
    t.area as area,
    t.region as region,
    t.competition as competition,
    c.team as team,
    c.name as name
from
(select distinct name, team from stats_players) as c
join teams t on c.team = t.team
order by t.area, t.region, t.competition, c.team