from scraper.parsers.lzvcup import LZVCupParser

# initialize parser setup
config_ = {
    "url_base": "https://www.lzvcup.be",
    "area": "VLAAMS BRABANT",
    "url_area": "results/5",
}
parser = LZVCupParser(config_, region="Regio Ring Oost")

# grab top-level URLs
df_sportshalls_urls, df_competitions_urls = parser.parse_region_cards()


def test_output_region_cards():
    regions = sorted(list(df_competitions_urls["region"].unique()))

    assert regions == [
        "Regio Dames Oost-Brabant",
        "Regio Hageland",
        "Regio Leuven",
        "Regio Leuven Studenten",
        "Regio Pajottenland",
        # "Regio Ring Noord",
        "Regio Ring Oost",
    ]


def test_parse_competitions_and_teams():
    # trim down urls to limit processing time
    df_competitions_urls_ = df_competitions_urls.query(f"region == '{parser.region}'")

    (
        df_teams,
        df_schedules,
        df_standings,
        df_stats,
        df_palmares,
    ) = parser.parse_competitions_and_teams(df_competitions_urls_)

    assert len(df_teams) > 0
    assert len(df_schedules) > 0
    assert len(df_standings) > 0
    assert len(df_stats) > 0
    assert len(df_palmares) > 0


def test_parse_sportshalls():
    df_sportshalls = parser.parse_sportshalls(df_sportshalls_urls)

    assert len(df_sportshalls) > 0
