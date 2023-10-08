import pytest

from scraper.parsers.lzvcup import LZVCupParser

config_ = {
    "base_url": "https://www.lzvcup.be",
    "area_name": "VLAAMS BRABANT",
    "area_url": "results/5",
}
parser = LZVCupParser(config_, region="Regio Ring Oost")


def test_parse_region_cards_and_competitions_from_region_card():
    region_cards = parser.parse_region_cards()
    regions = list(region_cards.keys())

    assert regions == [
        "Regio Dames Oost-Brabant",
        "Regio Hageland",
        "Regio Leuven",
        "Regio Leuven Studenten",
        "Regio Pajottenland",
        "Regio Ring Noord",
        "Regio Ring Oost",
    ]

    competitions = parser.parse_competitions_from_region_card(
        region_cards[parser.region]
    )

    assert competitions.keys() == {"competitions", "sportshalls"}


def test_parse_standings_and_stats():
    dict_competitions = {
        "1e Klasse": {
            "url": "https://www.lzvcup.be/results/5/16/1",
            "teams": {
                "ZVC Vollentip": "https://www.lzvcup.be/teams/detail/365",
                "Oppem Boys": "https://www.lzvcup.be/teams/detail/1242",
                "The Crows": "https://www.lzvcup.be/teams/detail/1971",
                "Eppegem City": "https://www.lzvcup.be/teams/detail/1970",
                "Tervuren United": "https://www.lzvcup.be/teams/detail/551",
            },
        },
        "2e Klasse": {
            "url": "https://www.lzvcup.be/results/5/16/2",
            "teams": {
                "Aston Birra": "https://www.lzvcup.be/teams/detail/2001",
                "ZVC Copains": "https://www.lzvcup.be/teams/detail/1525",
                "Chiro Mik Mak": "https://www.lzvcup.be/teams/detail/1526",
                "FC Degradé": "https://www.lzvcup.be/teams/detail/2002",
                "The Blinders": "https://www.lzvcup.be/teams/detail/1605",
            },
        },
    }

    df_standings, df_stats, df_palmares = parser.parse_standings_and_stats(
        dict_competitions=dict_competitions, region=parser.region
    )

    assert len(df_standings) > 0
    assert len(df_stats) > 0
    assert len(df_palmares) > 0


@pytest.mark.parametrize(
    "url, region",
    [("https://www.lzvcup.be/sportshalls/16", "Regio Ring Oost")],
)
def test_parse_sporthalls(url, region):
    df = parser.parse_sporthalls(url_sportshalls=url, region=region)

    assert len(df) > 0
