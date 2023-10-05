import time

import pandas as pd
import structlog
from base import DataStorage
from parsers.lzvcup import LZVCupParser

log = structlog.get_logger()


def scrape(config):
    dict_out, list_stats = {}, []

    base_url = config["base_url"]
    dict_areas = config["areas"]

    for area_name, area_url in dict_areas.items():
        config = {"base_url": base_url, "area_name": area_name, "area_url": area_url}

        # initialize scraper instance
        scraper = LZVCupParser(config)

        # get all regions within area
        region_cards = scraper.parse_region_cards()
        regions = list(region_cards.keys())

        dict_regions = {}
        for region in regions:
            # get all teams for all competitions within a single region
            # note: some competitions appear duplicated across regions (e.g. 4E KLASSE C GENT <> 1E KLASSE DENDERSTREEK, cf. teams Balls & Glory)
            competitions = scraper.parse_competitions_from_region_card(
                region_cards[region]
            )
            dict_regions[region] = competitions

            # get players and their statistics per team
            df_stats = scraper.parse_teams(competitions["competitions"], region)
            list_stats.append(df_stats)

        dict_out.update({area_name: dict_regions})

    # gather DataFrames into one
    df_stats_all = pd.concat(list_stats, axis=0)

    return dict_out, df_stats_all


def store(config):
    dir_competitions_teams = config["output"]["dir_competitions_teams"]
    dir_stats = config["output"]["dir_stats"]

    DataStorage.store_json(dict_out, dir=dir_competitions_teams)
    DataStorage.store_csv(df_stats_all, dir=dir_stats, index=False)


if __name__ == "__name__":
    config = DataStorage.load_json("config.json")
    log.info(f"Config loaded", time=time.time())

    dict_out, df_stats_all = scrape(config)
    log.info(f"Data scraped", time=time.time())

    store(config)
    log.info(f"Data stored", time=time.time())
