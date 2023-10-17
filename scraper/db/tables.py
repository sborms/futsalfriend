from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # this simply adds a single id at the end of all tables for easy
    # reference; the goal is not to set up a fully relational database
    id = Column(Integer, primary_key=True, autoincrement=True)


class Competitions(Base):
    __tablename__ = "competitions"

    area = Column(String)
    region = Column(String)
    competition = Column(String)
    url = Column(String)


class Locations(Base):
    __tablename__ = "locations"

    # note: some teams play in multiple sportshalls

    team = Column(String)
    sportshall = Column(String)


class Palmares(Base):
    __tablename__ = "palmares"

    team = Column(String)
    seizoen = Column(String)
    reeks = Column(String)
    positie = Column(Integer)


class Schedules(Base):
    __tablename__ = "schedules"

    area = Column(String)
    region = Column(String)
    competition = Column(String)
    sportshall = Column(String)
    day = Column(String)
    date = Column(Date)
    hour = Column(Integer)
    team1 = Column(String)
    goals1 = Column(Integer)
    team2 = Column(String)
    goals2 = Column(Integer)


class Sportshalls(Base):
    __tablename__ = "sportshalls"

    # note: some sportshalls are used in several regions

    area = Column(String)
    region = Column(String)
    sportshall = Column(String)
    url_sportshall = Column(String)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    url_region = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)


class Standings(Base):
    __tablename__ = "standings"

    area = Column(String)
    region = Column(String)
    competition = Column(String)
    team = Column(String)
    gespeeld = Column(Integer)
    gewonnen = Column(Integer)
    gelijk = Column(Integer)
    verloren = Column(Integer)
    dg = Column(Integer)
    dt = Column(Integer)
    ds = Column(Integer)
    punten = Column(Integer)
    ptnm = Column(Float)
    positie = Column(Integer)


class StatsPlayers(Base):
    __tablename__ = "stats_players"

    # note: data source issue > some URLs refer to the same player

    name = Column(String)
    team = Column(String)
    number = Column(Integer)
    url = Column(String)
    fairplay = Column(String)
    wedstrijden = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)


class StatsPlayersHistorical(Base):
    __tablename__ = "stats_players_historical"

    name = Column(String)
    team = Column(String)
    seizoen = Column(String)
    reeks = Column(String)
    stand = Column(String)
    wedstrijden = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)


class Teams(Base):
    __tablename__ = "teams"

    # note: data source issue > some teams are duplicated across multiple
    # competitions and some competitions appear duplicated across regions,
    # for instance 4E KLASSE C GENT <> 1E KLASSE DENDERSTREEK

    area = Column(String)
    region = Column(String)
    competition = Column(String)
    team = Column(String)
    url = Column(String)


class Levels(Base):
    __tablename__ = "levels"

    team = Column(String)
    level = Column(Integer)
    level_name = Column(String)
