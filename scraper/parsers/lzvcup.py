import io

import pandas as pd
import requests
from base import BaseScraper


class LZVCupParser(BaseScraper):
    def __init__(self, config):
        """Config should minimally include: 'base_url', 'area_name', and 'area_url'."""
        super().__init__(config)

        # complete area url
        if "_area_url" in dir(self):
            self._area_url = self.convert_to_full_url(self._area_url)

    def parse_region_cards(self):
        """Parses the region cards which display the competitions for each region."""
        # get HTML
        soup = self.make_soup(self._area_url)

        # get regions in specific area (e.g. Regio Lier in Antwerpen)
        regions_names = [
            self.clean_str(s.get_text())
            for s in soup.find_all(
                "button", class_="btn btn-link btn-block text-left collapsed"
            )
        ]

        # get cards with the information about the competitions in each region
        regions_competitions_cards = soup.find_all("div", class_="card-body row")

        # check that regions found correspond to parsed cards
        assert len(regions_names) == len(
            regions_competitions_cards
        ), "Number of regions is inconsistent"

        return dict(zip(regions_names, regions_competitions_cards))

    def parse_competitions_from_region_card(self, region_competition_card):
        """Parses each competition and the respective teams for given region."""
        # get the name sof the competition (e.g. 2e Klasse)
        # or the sporthalls locations together with the respective page url
        card_elements = region_competition_card.find_all(
            "a", class_="btn btn-outline-primary"
        )
        competitions, sportshalls = {}, None
        for a in card_elements:
            key, url_end = self.clean_str(a.get_text()), a.get(
                "href"
            )  # e.g. "2e Klasse", "results/1/13/2"
            url_full = self.convert_to_full_url(url_end)
            if key == "Sporthallen":
                sportshalls = url_full
            else:
                competitions[key] = url_full

        # get the teams for each competition
        dict_competitions = {}
        for competition, url_full in competitions.items():
            # get HTML
            soup = self.make_soup(url_full)

            # get teams from table and associate it to competition key
            dict_teams = self._parse_urls_teams(soup)
            dict_competitions[competition] = {"url": url_full, "teams": dict_teams}

        return {"competitions": dict_competitions, "sportshalls": sportshalls}

    def parse_teams(self, dict_competitions, region):
        """
        Parses the teams based on the region-specific "competitions" output
        from LZVCupScraper.parse_competitions_from_region_card().
        """
        if len(dict_competitions) == 0:
            print("No competitions found in input, returning None")
            return None

        area = self._area_name
        list_of_dfs = []
        for competition, dict_teams in dict_competitions.items():
            for team, url_full in dict_teams["teams"].items():
                print(f"Processing {area} - {region} - {competition} - {team}")

                # parse HTML
                soup = self.make_soup(url_full)

                # get team stats
                try:
                    df = self._parse_team_stats(soup)
                except AttributeError:
                    print(f"Error: {team} at {url_full} probably has no player info")
                    continue

                # add metadata
                df["_team"] = team
                df["_competition"] = competition
                df["_region"] = region
                df["_area"] = area

                # add to master list
                list_of_dfs.append(df)

        df_teams = pd.concat(list_of_dfs).reset_index(drop=True)

        return df_teams

    def parse_sporthalls(self):  # TODO: sporthalls information
        """Parses the sportshalls information."""
        pass

    def parse_competitions_standings(self):  # TODO: current competition standings
        """Parses current historical competitions standings."""
        pass

    def parse_team_stats_history(self):  # TODO: historical team standings
        """Parses previous team competition standings."""
        pass

    @staticmethod
    def parse_player_stats_history(name, url_full):
        """
        Parses the historical statistics for a given player url into a pandas df.

        Example usage:
            df_stats.apply(
                lambda x: LZVCupScraper.parse_player_stats_history(x.Teamleden, x._url),
                axis=1
            ).tolist()
        """
        print(f"Parsing historical stats from {name} at {url_full}")

        # get page
        page = requests.get(url_full)

        # grab table
        df = pd.read_html(io.StringIO(page.text))[0]

        # reformat table
        initial_cols = [
            "Seizoen",
            "Ploeg",
            "Wedstrijden",
            "Goals",
            "Assists",
            "Reeks",
            "Stand",
        ]
        df.columns = initial_cols

        # add name
        df["Name"] = name

        # reorder columns
        df = df[["Name"] + initial_cols]

        return df

    ############################
    #### PRIVATE METHODS     ###
    ############################

    def _parse_urls_teams(self, soup):
        """Parses the urls for each team as {team_name: url, ...}."""
        tags_teams = [
            s.find("a") for s in soup.find_all("div", class_="col-10 text-nowrap")
        ]
        dict_teams = dict(
            zip(
                [t.get_text() for t in tags_teams],
                [self.convert_to_full_url(t.get("href")) for t in tags_teams],
            )
        )
        return dict_teams

    def _parse_team_stats(self, soup):
        """Parses player statistics (games, assists, goals, ...) into a pandas df."""
        # get basic table HTML
        table = soup.find("ul", class_="item-list striped")

        # parse column header
        headers = [
            self.clean_str(d.get_text())
            for d in table.find("li", class_="item item-list-header").find_all(
                "div", class_="item-col-header"
            )
        ]

        # grab rows
        rows_html = [
            li.find_all("div", attrs={"class": lambda x: x.startswith("item-col col-")})
            for li in table.find_all("li", class_="item")[1:]
        ]  # drops the header

        # extract values row-by-row
        rows = []
        for player in rows_html:
            rows.append([self.clean_str(item.get_text()) for item in player])

        # assemble into a DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # get the url for each player
        dict_players = self._parse_players_url_from_rows(rows_html)
        df_players_url = (
            pd.DataFrame.from_dict(dict_players, orient="index", columns=["_url"])
            .reset_index()
            .rename(columns={"index": "Teamleden"})
        )

        # merge url's with main DataFrame
        df = pd.merge(df, df_players_url, on="Teamleden", how="left")

        # convert certain columns to numeric
        num_cols = ["Wedstrijden", "Goals", "Assists"]
        df[num_cols] = df[num_cols].astype(int)

        return df

    def _parse_players_url_from_rows(self, rows_html):
        """Parses the player urls for given team as {player_name: url, ...}."""
        dict_players = {}
        for player in rows_html:
            player_info = player[1]
            dict_players.update(
                {
                    self.clean_str(player_info.get_text()): self.convert_to_full_url(
                        player_info.find("a").get("href")
                    )
                }
            )
        return dict_players
