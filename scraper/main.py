import os
import sys

import pandas as pd

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(DIR_SCRIPT))  # so we can keep main.py in scraper/

from scraper.parsers.lzvcup import LZVCupParser
from scraper.utils.base import DataStorage
from scraper.utils.logger import Logger
from scraper.utils.utils import postproces_df, ymd

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

        # get all regions within area
        df_sportshalls_urls, df_competitions_urls = parser.parse_region_cards()
        list_competitions.append(df_competitions_urls)

        # get competition teams, schedule & standings, and team player statistics & palmares
        # note: some competitions appear duplicated across regions,
        # for instance 4E KLASSE C GENT <> 1E KLASSE DENDERSTREEK
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
    df_competitions_urls_all = pd.concat(list_competitions, axis=0)
    df_teams_all = pd.concat(list_teams, axis=0)
    df_schedules_all = pd.concat(list_schedules, axis=0)
    df_standings_all = pd.concat(list_standings, axis=0)
    df_stats_players_all = pd.concat(list_stats, axis=0)
    df_palmares_all = pd.concat(list_palmares, axis=0)
    df_sportshalls_all = pd.concat(list_sportshalls, axis=0)

    # get historical player statistics if enabled in config
    if config["steps"]["historical_players"] is True:
        log_main.info(f"Processing all historical player statistics")
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


def process_data(config, dict_out):
    for data_name, cols in config["postprocessing"].items():
        data = dict_out[data_name]
        data = postproces_df(data, first_cols=cols[0], drop_cols=cols[1])
        dict_out.update({data_name: data})  # overwrite modified DataFrame

    # create a new DataFrame with the sportshall(s) each team plays in
    df_locations = (
        dict_out["schedules"][["team1", "sportshall"]]
        .drop_duplicates()
        .rename(columns={"team1": "team"})
        .sort_values("team")
        .reset_index(drop=True)
    )  # note: some teams have multiple sportshalls
    dict_out.update({"locations": df_locations})

    return dict_out


def store(config, dict_tables):
    root = config["dir_output"]
    for data_name, data in dict_tables.items():
        output_dir = f"{root}/{data_name}.csv"
        if data is not None:
            DataStorage.store_csv(data, dir=output_dir, index=False)


if __name__ == "__main__":
    if not os.path.isdir(DIR_LOGS):
        os.makedirs(DIR_LOGS)

    log = Logger.get_logger(
        log_name="scraper", log_file=f"{DIR_LOGS}/_main.log"
    )  # logger for main steps

    log.info(f"Running script from {DIR_SCRIPT}")

    config = DataStorage.load_json(f"{DIR_SCRIPT}/config/config.json")
    log.info("Config loaded")

    dict_out = scrape(config, log_main=log)
    log.info("Data scraped")

    dict_out = process_data(config, dict_out)
    log.info("Data processed into tables")

    store(config, dict_out)
    log.info("Data stored")
