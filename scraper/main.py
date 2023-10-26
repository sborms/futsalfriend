import os
import sys

import pandas as pd

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(DIR_SCRIPT))  # so we can keep main.py in scraper/

from scraper.db.update import refresh_database
from scraper.parsers.lzvcup import LZVCupParser
from scraper.utils.base import DataStorage
from scraper.utils.logger import Logger
from scraper.utils.utils import (
    add_coordinates,
    create_levels_table,
    postproces_df,
    write_current_date_to_file,
    ymd,
)

DIR_LOGS = f"{DIR_SCRIPT}/logs/{ymd()}/"  # subdivide logs by day of script execution


def scrape(config, log_main):
    # initialize output variables
    (
        list_competitions,
        list_teams,
        list_schedules,
        list_standings,
        list_stats,
        list_palmares,
        list_sportshalls,
    ) = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    df_stats_players_historical = None

    url_base = config["url_base"]
    dict_areas = config["areas"]

    for area, url_area in dict_areas.items():
        config_ = {"url_base": url_base, "area": area, "url_area": url_area}

        # initialize area-specific logger
        log = Logger.get_logger(
            log_name=f"scraper_{area}",
            log_file=f"{DIR_LOGS}/{area}.log",
        )

        # initialize parser instance
        parser = LZVCupParser(config_, logger=log)

        # get urls for competitions and sportshalls for all regions within area
        df_sportshalls_urls, df_competitions_urls = parser.parse_region_cards()
        list_competitions.append(df_competitions_urls)

        # get competition teams, schedule & standings, and team player stats & palmares
        (
            df_teams,
            df_schedules,
            df_standings,
            df_stats,
            df_palmares,
        ) = parser.parse_competitions_and_teams(df_competitions_urls)
        list_teams.append(df_teams)
        list_schedules.append(df_schedules)
        list_standings.append(df_standings)
        list_stats.append(df_stats)
        list_palmares.append(df_palmares)

        # get sportshalls information
        df_sportshalls = parser.parse_sporthalls(df_sportshalls_urls)
        list_sportshalls.append(df_sportshalls)

        log_main.info(f"Area {area} successfully processed")

    # gather lists into single DataFrames
    df_competitions_urls_all = pd.concat(list_competitions).reset_index(drop=True)
    df_teams_all = pd.concat(list_teams).reset_index(drop=True)
    df_schedules_all = pd.concat(list_schedules).reset_index(drop=True)
    df_standings_all = pd.concat(list_standings).reset_index(drop=True)
    df_stats_players_all = pd.concat(list_stats).reset_index(drop=True)
    df_palmares_all = pd.concat(list_palmares).reset_index(drop=True)
    df_sportshalls_all = pd.concat(list_sportshalls).reset_index(drop=True)

    # get historical player statistics if enabled in config
    if config["steps"]["historical_players"] is True:
        log_main.info("Processing all historical player statistics")
        df_stats_players_historical = LZVCupParser.parse_player_stats_history(
            df_stats_players_all
        )

    return {
        "competitions": df_competitions_urls_all,
        "teams": df_teams_all,
        "sportshalls": df_sportshalls_all,
        "stats_players": df_stats_players_all,
        "stats_players_historical": df_stats_players_historical,
        "schedules": df_schedules_all,
        "standings": df_standings_all,
        "palmares": df_palmares_all,
    }


def process_data(config, dict_tables, log_main):
    # postprocess initial tables
    for data_name, cols in config["postprocessing"].items():
        data = dict_tables[data_name]
        if data_name == "sportshalls":
            log_main.info("Adding coordinates to sportshalls")
            data = add_coordinates(data, dir_coordinates="data/_coordinates.csv")
        data = postproces_df(data, first_cols=cols[0], drop_cols=cols[1])
        dict_tables.update({data_name: data})  # overwrite modified DataFrame

    # create a new table with the sportshall(s) each team plays in
    df_locations = (
        dict_tables["schedules"][["team1", "sportshall"]]
        .rename(columns={"team1": "team"})
        .sort_values("team")
        .reset_index(drop=True)
        .drop_duplicates()
    )
    dict_tables.update({"locations": df_locations})

    # create a new table that estimates each team's competency level
    df_levels = create_levels_table(dict_tables["standings"], dict_tables["palmares"])
    dict_tables.update({"levels": df_levels})

    return dict_tables


def store(config, dict_tables, log_main):
    # refresh SQLite database
    refresh_database(dict_tables, path2db=config["database"], logger=log_main)

    if config["steps"]["csv"]:
        # additionally store all tables as csv files
        root = config["dir_output"]
        for data_name, data in dict_tables.items():
            output_dir = f"{root}/{data_name}.csv"  # overwrites files at every rerun
            if data is not None:
                DataStorage.store_csv(data, dir=output_dir, index=False)


if __name__ == "__main__":
    if not os.path.isdir(DIR_LOGS):
        os.makedirs(DIR_LOGS)

    # initialize logger for main steps
    log = Logger.get_logger(log_name="scraper", log_file=f"{DIR_LOGS}/_main.log")

    log.info(f"Running script from {DIR_SCRIPT}")

    config = DataStorage.load_json(f"{DIR_SCRIPT}/config/config.json")
    log.info("Config loaded")

    dict_tables = scrape(config, log_main=log)
    log.info("Data scraped")

    dict_tables = process_data(config, dict_tables, log_main=log)
    log.info("Data processed into tables")

    store(config, dict_tables, log_main=log)
    log.info("Data stored")

    write_current_date_to_file(config["dir_last_updated"])
    log.info("Refresh date updated.")
