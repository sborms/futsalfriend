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
        The config dictionary should include 'url_base', 'area', and 'url_area'.
        Keys from the config are stored with a _ prefix as attributes of the class.
        Additional keyword arguments won't have such prefix, except for the optional
        logger= argument, which is stored as self._logger.
        """
        super().__init__(config, **kwargs)

        # complete area URL
        if "_url_area" in dir(self):
            self._url_area = self.convert_to_full_url(self._url_area)

    def parse_region_cards(self):
        """Parses the region cards which display the competitions for each region."""
        area = self._area

        # get HTML
        soup = self.make_soup(self._url_area)

        # get regions in specific area (e.g. Regio Lier in Antwerpen)
        region_names = [
            self.clean_str(s.get_text())
            for s in soup.find_all(
                "button", class_="btn btn-link btn-block text-left collapsed"
            )
        ]

        # get cards with the information about the competitions in each region
        region_cards = soup.find_all("div", class_="card-body row")

        # check that regions found correspond to parsed cards
        assert len(region_names) == len(
            region_cards
        ), "Number of regions is inconsistent"

        dict_regions = dict(zip(region_names, region_cards))

        # get the names of the competition (e.g. 2e Klasse)
        # or the sporthalls locations together with the respective page URL
        rows_sportshalls, rows_competitions = [], []
        for region, region_card in dict_regions.items():
            card_elements = region_card.find_all("a", class_="btn btn-outline-primary")

            for a in card_elements:
                key, url_end = self.clean_str(a.get_text()), a.get(
                    "href"
                )  # e.g. "2e Klasse", "results/1/13/2"
                url_full = self.convert_to_full_url(url_end)
                if key == "Sporthallen":
                    rows_sportshalls.append([area, region, url_full])
                else:
                    rows_competitions.append([area, region, key, url_full])

        df_sportshalls_urls = pd.DataFrame(
            rows_sportshalls, columns=["area", "region", "url"]
        )
        df_competitions_urls = pd.DataFrame(
            rows_competitions, columns=["area", "region", "competition", "url"]
        )

        return df_sportshalls_urls, df_competitions_urls

    def parse_competitions_and_teams(self, df_competitions_urls):
        """
        Parses following information from all competitions pages and regions:
        - Teams and their respective URLs
        - Schedule with results
        - Current standings

        Parses following information from each team page in a competition:
        - Player statistics
        - Team palmares

        The input is the area-specific competitions output from
        LZVCupParser.parse_region_cards().
        """
        area = self._area

        list_teams, list_schedules, list_standings, list_stats, list_palmares = (
            [],
            [],
            [],
            [],
            [],
        )
        for (
            _,
            _,  # area
            region,
            competition,
            url_competition,
        ) in df_competitions_urls.itertuples():
            self._logger.info(f"Processing {area} - {region} - {competition}")

            # get competition page as HTML
            soup_competition = self.make_soup(url_competition)

            # get teams for given competition
            dict_teams = self._parse_urls_teams(soup_competition)

            df_teams = (
                pd.DataFrame.from_dict(dict_teams, orient="index", columns=["url"])
                .reset_index()
                .rename(columns={"index": "team"})
            )
            df_teams = add_columns_to_df(
                df_teams, {"area": area, "region": region, "competition": competition}
            )

            # prepare teams output
            list_teams.append(df_teams)

            # gather metadata into a dict
            metadata = {"area": area, "region": region, "competition": competition}

            # retrieve schedule including results and future games
            df_schedule = self._parse_competition_schedule(soup_competition)
            df_schedule = add_columns_to_df(df_schedule, metadata)
            list_schedules.append(df_schedule)

            # retrieve current standings
            df_standings = self._parse_competition_standings(soup_competition)
            df_standings = add_columns_to_df(df_standings, metadata)
            list_standings.append(df_standings)

            # get statistics for all teams
            for team, url_team in dict_teams.items():
                # update metadata
                metadata.update({"team": team})

                # parse HTML
                soup_team = self.make_soup(url_team)

                # get team stats
                try:
                    df_stats_team = self._parse_team_stats(soup_team)
                    df_stats_team = add_columns_to_df(df_stats_team, metadata)
                    list_stats.append(df_stats_team)
                except AttributeError:
                    self._logger.warning(
                        "No player info available", team=team, url=url_team
                    )

                # get historical team standings (= palmares)
                try:
                    df_palmares_team = self._parse_team_palmares(soup_team)
                    df_palmares_team = add_columns_to_df(df_palmares_team, metadata)
                    list_palmares.append(df_palmares_team)
                except AttributeError:
                    self._logger.warning(
                        "No palmares info available", team=team, url=url_team
                    )
                    continue

        # assemble all output into DataFrames
        df_teams = pd.concat(list_teams).reset_index(drop=True)
        df_schedules = pd.concat(list_schedules).reset_index(drop=True)
        df_standings = pd.concat(list_standings).reset_index(drop=True)
        df_stats = pd.concat(list_stats).reset_index(drop=True)
        df_palmares = pd.concat(list_palmares).reset_index(drop=True)

        return df_teams, df_schedules, df_standings, df_stats, df_palmares

    def parse_sporthalls(self, df_sportshalls_urls):
        """
        Parses the sportshalls information based on the area-specific sportshalls
        output from LZVCupParser.parse_region_cards().
        """
        area = self._area

        list_dfs = []
        for _, _, region, url_sportshalls in df_sportshalls_urls.itertuples():
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

            # extract info about sportshalls
            sportshalls_info = [
                card.find("p", class_="card-text")
                .get_text(strip=True, separator="\n")
                .splitlines()
                + [
                    self.convert_to_full_url(
                        card.find("a", class_="btn btn-outline-primary").get("href")
                    )
                ]
                for card in cards_all
            ]

            # clean sportshalls info
            for info in sportshalls_info:
                if len(info) > 4:
                    info.pop(2)  # removes likely second occurrence of phone number
                if len(info) == 3:
                    if "@" in info[1]:  # if no phone number
                        info.insert(1, None)  # adds None for phone number
                    else:  # if no email
                        info.insert(2, None)  # adds None for email

            # add together into a DataFrame
            dict_sportshalls = dict(zip(sportshalls_names, sportshalls_info))
            df = (
                pd.DataFrame.from_dict(
                    dict_sportshalls,
                    orient="index",
                    columns=["address", "phone", "email", "url_sportshall"],
                )
                .reset_index()
                .rename(columns={"index": "sportshall"})
            )

            # add metadata
            df = add_columns_to_df(
                df, {"area": area, "region": region, "url_region": url_sportshalls}
            )

            list_dfs.append(df)

        df_all = pd.concat(list_dfs)

        return df_all

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
                "seizoen",
                "team",
                "wedstrijden",
                "goals",
                "assists",
                "reeks",
                "stand",
            ]
            df.columns = initial_cols

            # add name
            df["name"] = name

            # reorder columns
            df = df[["name"] + initial_cols]

            return df

        # drop duplicates first as some players may play in multiple teams
        df_players = df_stats[["name", "url"]].drop_duplicates()

        # parse historical statistics for each player in parallel
        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                res = executor.map(
                    lambda k: _parse_player_stats_history(
                        session,
                        df_players["name"].iloc[k],
                        df_players["url"].iloc[k],
                    ),
                    range(len(df_players)),
                )

            df = pd.concat(res)

        return df

    ############################
    #### PRIVATE METHODS     ###
    ############################

    def _parse_urls_teams(self, soup):
        """Parses the URLs for each team as {team_name: URL, ...}."""
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
            # refactor match time info into day, date, and hour
            time = row.pop(0)
            row.insert(0, time[14:19].replace("u", ""))  # hour
            row.insert(0, time[3:13])  # date
            row.insert(0, time[:2])  # day

            # refactor score into two elements (home goals, out goals)
            score = row[4]
            if score in ["In behandeling", "-"]:  # match hasn't been played yet
                row[4] = np.nan
                row.insert(6, np.nan)
            else:
                row[4] = int(score[0])
                row.insert(6, int(score[-1]))  # put after away team

            # drop last element which is empty
            row.pop(-1)

        # assemble into a DataFrame
        headers = [
            "day",
            "date",
            "hour",
            "team1",
            "goals1",
            "team2",
            "goals2",
            "sportshall",
        ]
        df = pd.DataFrame(rows_all[:j], columns=headers)

        # convert date to datetime
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")

        return df

    def _parse_competition_standings(self, soup):
        """Parses current competition standings."""
        # get basic table structure in HTML
        table = soup.find("div", class_="items table-list lzvtable").find(
            "ul", class_="item-list striped"
        )

        # define column headers
        headers = [
            "team",
            "gespeeld",
            "gewonnen",
            "gelijk",
            "verloren",
            "dg",  # goals scored
            "dt",  # goals against
            "ds",  # goal difference
            "punten",
            "ptnm",  # points per match
            "positie",
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
        df = pd.DataFrame(rows, columns=headers[:-1])  # "positie" column not there yet

        # add the positions column and drop positions in the team names
        df["positie"] = np.where(
            df.index <= 8,  # positions 1-9
            df["team"].apply(lambda x: x[:1]),
            df["team"].apply(lambda x: x[:2]),
        )
        df["team"] = np.where(
            df.index <= 8,
            df["team"].apply(lambda x: x[1:]),
            df["team"].apply(lambda x: x[2:]),
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
            self.clean_str(d.get_text()).lower()
            for d in table.find("li", class_="item item-list-header").find_all(
                "div", class_="item-col-header"
            )
        ]

        # grab rows
        rows_html, rows = self._parse_rows_from_table(table)

        # assemble into a DataFrame
        df = pd.DataFrame(rows, columns=headers).rename(
            columns={"teamleden": "name", "#": "number"}
        )

        # get the URL for each player
        dict_players = self._parse_players_url_from_rows(rows_html)
        df_players_url = (
            pd.DataFrame.from_dict(dict_players, orient="index", columns=["url"])
            .reset_index()
            .rename(columns={"index": "name"})
        )

        # merge URLs with main DataFrame
        df = pd.merge(df, df_players_url, on="name", how="left")

        # convert certain columns to numeric
        num_cols = ["wedstrijden", "goals", "assists"]
        df[num_cols] = df[num_cols].astype(int)

        # drop fairplay column
        df = df.drop(columns="fairplay")

        return df

    def _parse_team_palmares(self, soup):
        """Parses previous team competition standings (aka palmares)."""
        # grab the raw HTML table with the historical standings
        table = soup.find("table", {"class": "lzvtable"})

        # compose the header
        header = [th.get_text().lower() for th in table.find("thead").find_all("th")][
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
        df["seizoen"] = df["seizoen"].apply(lambda x: x[:9])  # 20xx-20xx
        df["positie"] = df["positie"].astype(int)

        return df

    def _parse_players_url_from_rows(self, rows_html):
        """Parses the player URLs for given team as {player_name: URL, ...}."""
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
        """Parses rows from a table-like HTML structure."""
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
