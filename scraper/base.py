import json

import pandas as pd
import requests
from bs4 import BeautifulSoup


class DataStorage:
    def __init__(self):
        pass

    @staticmethod
    def store_json(dictionary, dir):
        """Stores a dict as a JSON file."""
        with open(dir, "w+") as f:
            json.dump(
                dictionary, f
            )  # note: not always properly encoded but input-output works

    @staticmethod
    def load_json(dir):
        """Loads a JSON file as a dict."""
        with open(dir, "r") as f:
            dictionary = json.load(f)
        return dictionary

    @staticmethod
    def store_csv(df, dir, **kwargs):
        """Stores a pandas df as a csv file."""
        df.to_csv(dir, **kwargs)

    @staticmethod
    def load_csv(dir):
        """Loads csv file from location into a pandas df."""
        df = pd.read_csv(dir)
        return df


class BaseScraper(DataStorage):
    def __init__(self, config):
        """Assigns config keys as separate attributes prefixed with _."""
        for name, value in config.items():
            setattr(self, f"_{name}", value)

    def convert_to_full_url(self, url_end):
        """Joins 'url_end' with self._base_url."""
        if url_end[0] == "/":
            url_end = url_end[1:]
        url_full = f"{self._base_url}/{url_end}"
        return url_full

    def make_soup(self, url):
        """Gets page via requests and parses into HTML via BeautifulSoup."""
        page = requests.get(url)
        if page.status_code == 200:
            return BeautifulSoup(page.text, "html.parser")

    def clean_str(self, string):
        """Strips whitespaces and alike from a string."""
        return string.replace("\n", "").replace("\t", "").strip()
