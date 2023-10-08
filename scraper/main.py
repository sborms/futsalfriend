import os

import pandas as pd
from base import DataStorage
from logger import Logger
from parsers.lzvcup import LZVCupParser
from utils import ymd

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIR_LOGS = f"{DIR_SCRIPT}/logs/{ymd()}/"  # create a new log directory for each day


def scrape(config, log_main):
    # initialize output variables
    dict_competitions_teams = {}
    list_standings, list_stats, list_palmares, list_sportshalls = [], [], [], []
    df_stats_historical_players = None

    base_url = config["base_url"]
    dict_areas = config["areas"]

    for area_name, area_url in dict_areas.items():
        config_ = {"base_url": base_url, "area_name": area_name, "area_url": area_url}

        # initialize area-specific logger
        log = Logger.get_logger(
            log_name=f"scraper_{area_name}",
            log_file=f"{DIR_LOGS}/{area_name}.log",
        )

        # initialize parser instance
        parser = LZVCupParser(config_, logger=log)

        # get all regions within area
        region_cards = parser.parse_region_cards()
        regions = list(region_cards.keys())

        dict_regions = {}
        for region in regions:
            # get all teams for all competitions within a single region
            # note: some competitions appear duplicated across regions,
            # for instance 4E KLASSE C GENT <> 1E KLASSE DENDERSTREEK
            competitions = parser.parse_competitions_from_region_card(
                region_cards[region]
            )
            dict_regions[region] = competitions

            # get current competition standings and player statistics per team
            df_standings, df_stats, df_palmares = parser.parse_standings_and_stats(
                dict_competitions=competitions["competitions"], region=region
            )
            list_standings.append(df_standings)
            list_stats.append(df_stats)
            list_palmares.append(df_palmares)

            # get sportshalls information
            df_sportshalls = parser.parse_sporthalls(
                url_sportshalls=competitions["sportshalls"], region=region
            )
            list_sportshalls.append(df_sportshalls)

        dict_competitions_teams.update({area_name: dict_regions})
        log_main.info(f"Area {area_name} successfully processed")

    # gather lists into single DataFrames
    df_standings_all = pd.concat(list_standings, axis=0)
    df_stats_all = pd.concat(list_stats, axis=0)
    df_palmares_all = pd.concat(list_palmares, axis=0)
    df_sportshalls_all = pd.concat(list_sportshalls, axis=0)

    # get historical player statistics
    if config["steps"]["historical_players"] is True:
        log_main.info(f"Processing all historical player statistics")
        df_stats_historical_players = LZVCupParser.parse_player_stats_history(
            df_stats_all
        )

    return (
        dict_competitions_teams,
        df_standings_all,
        df_stats_all,
        df_palmares_all,
        df_sportshalls_all,
        df_stats_historical_players,
    )


def store(
    config,
    dict_competitions_teams,
    df_standings,
    df_stats,
    df_palmares,
    df_sportshalls,
    df_stats_historical_players=None,
):
    dir_competitions_teams = config["output"]["dir_competitions_teams"]
    dir_standings = config["output"]["dir_standings"]
    dir_stats = config["output"]["dir_stats"]
    dir_palmares = config["output"]["dir_palmares"]
    dir_sportshalls = config["output"]["dir_sportshalls"]

    DataStorage.store_json(dict_competitions_teams, dir=dir_competitions_teams)
    DataStorage.store_csv(df_standings, dir=dir_standings, index=False)
    DataStorage.store_csv(df_stats, dir=dir_stats, index=False)
    DataStorage.store_csv(df_palmares, dir=dir_palmares, index=False)
    DataStorage.store_csv(df_sportshalls, dir=dir_sportshalls, index=False)

    if df_stats_historical_players is not None:
        dir_stats_historical_players = config["output"]["dir_stats_historical_players"]
        DataStorage.store_csv(
            df_stats_historical_players, dir=dir_stats_historical_players, index=False
        )


if __name__ == "__main__":
    if not os.path.isdir(DIR_LOGS):
        os.makedirs(DIR_LOGS)

    log = Logger.get_logger(
        log_name="scraper", log_file=f"{DIR_LOGS}/_main.log"
    )  # logger for main steps

    log.info(f"Running script from {DIR_SCRIPT}")

    config = DataStorage.load_json(f"{DIR_SCRIPT}/config/config.json")
    log.info("Config loaded")

    (
        dict_competitions_teams,
        df_standings_all,
        df_stats_all,
        df_palmares_all,
        df_sportshalls_all,
        df_stats_historical_players,
    ) = scrape(config, log_main=log)
    log.info("Data scraped")

    store(
        config,
        dict_competitions_teams,
        df_standings_all,
        df_stats_all,
        df_palmares_all,
        df_sportshalls_all,
        df_stats_historical_players,
    )
    log.info("Data stored")
