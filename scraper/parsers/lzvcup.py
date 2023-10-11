import io
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

from scraper.utils.base import BaseScraper
from scraper.utils.utils import add_columns_to_df, chunks


class LZVCupParser(BaseScraper):
    def __init__(self, config, **kwargs) -> None:
        """
        The config dictionary should include 'base_url', 'area_name', and 'area_url'.
        Keys from the config will be stored with a _ prefix as attributes of the class.
        Additional keyword arguments won't have such prefix, except for the optional
        logger= argument, which will be stored as self._logger.
        """
        super().__init__(config, **kwargs)

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

        return {
            "competitions": dict_competitions,
            "sportshalls": sportshalls,
        }

    def parse_competitions_and_teams(self, dict_competitions, region):
        """
        Parses information from each competition page (schedule, standings) and each
        team (player stats, palmares) within the region-specific "competitions"
        output from LZVCupParser.parse_competitions_from_region_card().

        Note: this is slightly inefficient in getting the schedule & standings
        because the same HTML is parsed twice (once to get the team urls in another
        function call and once to get the schedule & standings).
        """
        if len(dict_competitions) == 0:
            self._logger.warning(
                "No competitions in input, returning None", region=region
            )
            return [None for _ in range(4)]

        area = self._area_name

        list_schedules, list_standings, list_stats, list_palmares = [], [], [], []
        for competition, dict_teams in dict_competitions.items():
            self._logger.info(f"Processing {area} - {region} - {competition}")

            # gather metadata into a dict
            metadata = {"_area": area, "_region": region, "_competition": competition}

            # get competition page as HTML
            soup = self.make_soup(dict_teams["url"])

            # retrieve schedule with results
            df_schedule = self._parse_competition_schedule(soup)
            df_schedule = add_columns_to_df(df_schedule, metadata)
            list_schedules.append(df_schedule)

            # retrieve current standings
            df_standings = self._parse_competition_standings(soup)
            df_standings = add_columns_to_df(df_standings, metadata)
            list_standings.append(df_standings)

            # get statistics for all teams
            for team, url_full in dict_teams["teams"].items():
                # update metadata
                metadata.update({"Team": team})

                # parse HTML
                soup = self.make_soup(url_full)

                # get team stats
                try:
                    df_stats_team = self._parse_team_stats(soup)
                    df_stats_team = add_columns_to_df(df_stats_team, metadata)
                    list_stats.append(df_stats_team)
                except AttributeError:
                    self._logger.warning(
                        "No player info available", team=team, url=url_full
                    )

                # get historical team standings
                try:
                    df_palmares_team = self._parse_team_palmares(soup)
                    df_palmares_team = add_columns_to_df(df_palmares_team, metadata)
                    list_palmares.append(df_palmares_team)
                except AttributeError:
                    self._logger.warning(
                        "No palmares info available", team=team, url=url_full
                    )
                    continue

        df_schedules = pd.concat(list_schedules).reset_index(drop=True)
        df_standings = pd.concat(list_standings).reset_index(drop=True)
        df_stats = pd.concat(list_stats).reset_index(drop=True)
        df_palmares = pd.concat(list_palmares).reset_index(drop=True)

        return df_schedules, df_standings, df_stats, df_palmares

    def parse_sporthalls(self, url_sportshalls, region):
        """
        Parses the sportshalls information based on the region-specific "sportshalls"
        output (= url) from LZVCupParser.parse_competitions_from_region_card().
        """
        area = self._area_name

        self._logger.info(f"Processing {area} - {region} > sportshalls")

        # parse HTML
        soup = self.make_soup(url_sportshalls)

        # get all sportshalls cards
        cards_all = soup.find_all("div", class_="card lzv2020card")

        # extract names of sportshalls
        sportshalls_names = [
            self.clean_str(
                card.find("h5", class_="card-title").get_text(strip=True)
            ).split(": ")[1]
            for card in cards_all
        ]

        # extract and clean info of sportshalls
        sportshalls_info = [
            card.find("p", class_="card-text")
            .get_text(strip=True, separator="\n")
            .splitlines()
            for card in cards_all
        ]

        for info in sportshalls_info:
            if len(info) > 3:
                info.pop(2)  # removes likely second occurrence of phone number
            if len(info) == 2:
                if "@" in info[1]:  # if no phone number
                    info.insert(1, None)  # adds None for phone number

        # add together into a DataFrame
        dict_sportshalls = dict(zip(sportshalls_names, sportshalls_info))
        df = (
            pd.DataFrame.from_dict(
                dict_sportshalls, orient="index", columns=["address", "phone", "email"]
            )
            .reset_index()
            .rename(columns={"index": "sportshall"})
        )

        # add metadata
        df = add_columns_to_df(df, {"_region": region, "_area": area})

        return df

    @staticmethod
    def parse_player_stats_history(df_stats, max_workers=10):
        """Parses historical statistics for all players in input DataFrame."""

        # create helper function to parse historical statistics for individual players
        def _parse_player_stats_history(session, name, url_player):
            # get page
            page = session.get(url_player)

            # grab table
            df = pd.read_html(io.StringIO(page.text))[0]

            # reformat table
            initial_cols = [
                "Seizoen",
                "Team",
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

        # drop duplicates first as some players may play in multiple teams
        df_players = df_stats[["Name", "_url"]].drop_duplicates()

        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                res = executor.map(
                    lambda k: _parse_player_stats_history(
                        session,
                        df_players["Name"].iloc[k],
                        df_players["_url"].iloc[k],
                    ),
                    range(len(df_players)),
                )

            df = pd.concat(res)

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

    def _parse_competition_schedule(self, soup):
        """Parses competition schedule and results."""
        # get basic table structure in HTML
        list_games_raw = [
            div.find("ul", class_="item-list striped")
            for div in soup.find_all(
                "div", class_="items calendar-list"
            )  # first of two items is collapsable
        ]

        # grab rows
        rows_all = []
        for games_raw in list_games_raw:
            _, rows = self._parse_rows_from_table(games_raw, drop_header=0)
            rows_all.extend(rows)

        for j, row in enumerate(rows_all):
            if row[0] == "Nog te plannen":
                break
            # refactor match time info into two elements (date, hour)
            dayhour = row.pop(0)[-11:].split(" ")  # [dd/mm, HHuMM]
            row.insert(0, dayhour[1])
            row.insert(0, dayhour[0])

            # refactor score into two elements (home goals, out goals)
            score = row[3]
            if score in ["In behandeling", "-"]:  # match hasn't been played yet
                row[3] = np.nan
                row.insert(5, np.nan)
            else:
                row[3] = int(score[0])
                row.insert(5, int(score[-1]))  # put after away team

            # drop last element which is empty
            row.pop(-1)

        # assemble into a DataFrame
        headers = [
            "date",
            "hour",
            "team_home",
            "goals_home",
            "team_away",
            "goals_away",
            "sportshall",
        ]
        df = pd.DataFrame(rows_all[:j], columns=headers)

        return df

    def _parse_competition_standings(self, soup):
        """Parses current competition standings."""
        # get basic table structure in HTML
        table = soup.find("div", class_="items table-list lzvtable").find(
            "ul", class_="item-list striped"
        )

        # parse column header
        headers = [
            "Team",
            "Gespeeld",
            "Gewonnen",
            "Gelijk",
            "Verloren",
            "DG",
            "DT",
            "DS",
            "Punten",
            "Ptn/M",
        ]
        # headers = [
        #     self.clean_str(d.get_text())
        #     for d in table.find("li", class_="item item-list-header").find_all(
        #         "div", class_="item-col-header"
        #     )
        # ]

        # grab rows
        _, rows = self._parse_rows_from_table(table)

        # assemble into a DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # drop positions in the team names
        df["Team"] = np.where(
            df.index <= 8,  # positions 1-9
            df["Team"].apply(lambda x: x[1:]),
            df["Team"].apply(lambda x: x[2:]),
        )

        # convert all but first column to numeric
        df[headers[1:]] = df[headers[1:]].astype(float)

        return df

    def _parse_team_stats(self, soup):
        """Parses player statistics (games, assists, goals, ...) into a pandas df."""
        # get basic table structure in HTML
        table = soup.find("ul", class_="item-list striped")

        # parse column header
        headers = [
            self.clean_str(d.get_text())
            for d in table.find("li", class_="item item-list-header").find_all(
                "div", class_="item-col-header"
            )
        ]

        # grab rows
        rows_html, rows = self._parse_rows_from_table(table)

        # assemble into a DataFrame
        df = pd.DataFrame(rows, columns=headers).rename(columns={"Teamleden": "Name"})

        # get the url for each player
        dict_players = self._parse_players_url_from_rows(rows_html)
        df_players_url = (
            pd.DataFrame.from_dict(dict_players, orient="index", columns=["_url"])
            .reset_index()
            .rename(columns={"index": "Name"})
        )

        # merge url's with main DataFrame
        df = pd.merge(df, df_players_url, on="Name", how="left")

        # convert certain columns to numeric
        num_cols = ["Wedstrijden", "Goals", "Assists"]
        df[num_cols] = df[num_cols].astype(int)

        return df

    def _parse_team_palmares(self, soup):
        """Parses previous team competition standings (= palmares)."""
        # grab the raw HTML table with the historical standings
        table = soup.find("table", {"class": "lzvtable"})

        # compose the header
        header = [th.get_text() for th in table.find("thead").find_all("th")][
            :-1
        ]  # drops orphan column

        # compose the rows
        rows_html = table.find("tbody").find_all(
            "td"
        )  # tr is not returned in the output...
        rows = chunks(
            [
                el
                for el in [self.clean_str(row_raw.get_text()) for row_raw in rows_html]
                if el != ""
            ],
            3,  # len(header)
        )

        # stitch together into a DataFrame
        df = pd.DataFrame(rows, columns=header)
        df["Seizoen"] = df["Seizoen"].apply(lambda x: x[:9])  # 20xx-20xx
        df["Positie"] = df["Positie"].astype(int)

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

    def _parse_rows_from_table(self, table, drop_header=1):
        # grab rows
        rows_html = [
            li.find_all("div", attrs={"class": lambda x: x.startswith("item-col col-")})
            for li in table.find_all("li", class_="item")[drop_header:]
        ]

        # extract values row-by-row
        rows = []
        for row in rows_html:
            rows.append([self.clean_str(item.get_text()) for item in row])

        return rows_html, rows
