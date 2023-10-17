from enum import Enum

import structlog

from scraper.db.sqlitedb import SQLiteDB
from scraper.db.tables import (
    Competitions,
    Levels,
    Locations,
    Palmares,
    Schedules,
    Sportshalls,
    Standings,
    StatsPlayers,
    StatsPlayersHistorical,
    Teams,
)


class Tables(Enum):
    competitions = Competitions
    locations = Locations
    palmares = Palmares
    schedules = Schedules
    sportshalls = Sportshalls
    standings = Standings
    stats_players = StatsPlayers
    stats_players_historical = StatsPlayersHistorical
    teams = Teams
    levels = Levels


def refresh_database(dict_tables, path2db, logger=structlog.get_logger()):
    # connect to database
    db = SQLiteDB(path2db)

    # remove all rows from table
    db.drop_tables()

    # create empty tables with proper schema
    db.create_db()

    # insert data into all tables
    for table in db.get_table_classes():
        name = table.name
        logger.info(f"Inserting table into db: {table.name}")

        # get DataFrame
        df = dict_tables[name]

        # get table class that defines schema
        table_class = getattr(Tables, name).value

        # insert table into database
        db.insert_table(df, table_class)

    # close connection
    db.close()
