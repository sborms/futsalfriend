import os

import pandas as pd
from base import DataStorage
from logger import Logger
from parsers.lzvcup import LZVCupParser
from utils import ymd

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def scrape(config):
    dict_competitions_teams = {}
    list_standings, list_stats, list_sportshalls = [], [], []

    base_url = config["base_url"]
    dict_areas = config["areas"]

    for area_name, area_url in dict_areas.items():
        config = {"base_url": base_url, "area_name": area_name, "area_url": area_url}

        # initialize area-specific logger
        log = Logger(
            log_name=f"scraper_{area_name}",
            log_file=f"{DIR_SCRIPT}/logs/log_{ymd()}_{area_name}.log",
        ).get_logger()

        # initialize scraper instance
        scraper = LZVCupParser(config, logger=log)

        # get all regions within area
        region_cards = scraper.parse_region_cards()
        regions = list(region_cards.keys())

        dict_regions = {}
        for region in regions:
            # get all teams for all competitions within a single region
            # note: some competitions appear duplicated across regions,
            # for instance 4E KLASSE C GENT <> 1E KLASSE DENDERSTREEK
            competitions = scraper.parse_competitions_from_region_card(
                region_cards[region]
            )
            dict_regions[region] = competitions

            # get current competition standings and player statistics per team
            df_standings, df_stats = scraper.parse_standings_and_stats(
                dict_competitions=competitions["competitions"], region=region
            )
            list_standings.append(df_standings)
            list_stats.append(df_stats)

            # get sportshalls information
            df_sportshalls = scraper.parse_sporthalls(
                url_sportshalls=competitions["sportshalls"], region=region
            )
            list_sportshalls.append(df_sportshalls)

        dict_competitions_teams.update({area_name: dict_regions})

    # gather DataFrames into one
    df_standings_all = pd.concat(list_standings, axis=0)
    df_stats_all = pd.concat(list_stats, axis=0)
    df_sportshalls_all = pd.concat(list_sportshalls, axis=0)

    return dict_competitions_teams, df_standings_all, df_stats_all, df_sportshalls_all


def store(
    config, dict_competitions_teams, df_standings_all, df_stats_all, df_sportshalls_all
):
    dir_competitions_teams = config["output"]["dir_competitions_teams"]
    dir_standings = config["output"]["dir_standings"]
    dir_stats = config["output"]["dir_stats"]
    dir_sportshalls = config["output"]["dir_sportshalls"]

    DataStorage.store_json(dict_competitions_teams, dir=dir_competitions_teams)
    DataStorage.store_csv(df_standings_all, dir=dir_standings, index=False)
    DataStorage.store_csv(df_stats_all, dir=dir_stats, index=False)
    DataStorage.store_csv(df_sportshalls_all, dir=dir_sportshalls, index=False)


if __name__ == "__main__":
    log = Logger(
        log_name="scraper", log_file=f"{DIR_SCRIPT}/logs/log_{ymd()}.log"
    ).get_logger()  # logger for main steps

    log.info(f"Running script from {DIR_SCRIPT}")

    config = DataStorage.load_json(f"{DIR_SCRIPT}/config/config.json")
    log.info("Config loaded")

    (
        dict_competitions_teams,
        df_stats_all,
        df_sportshalls_all,
        df_standings_all,
    ) = scrape(config)
    log.info("Data scraped")

    store(
        config,
        dict_competitions_teams,
        df_stats_all,
        df_sportshalls_all,
        df_standings_all,
    )
    log.info("Data stored")
