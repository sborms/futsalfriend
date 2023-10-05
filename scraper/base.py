import json

import pandas as pd
import requests
from bs4 import BeautifulSoup


class DataStorage:
    def __init__(self):
        pass

    @staticmethod
    def store_json(dictionary, dir):
        with open(dir, "w+") as f:
            json.dump(
                dictionary, f
            )  # note: not always properly encoded but input-output works

    @staticmethod
    def load_json(dir):
        with open(dir, "r") as f:
            dictionary = json.load(f)
        return dictionary

    @staticmethod
    def store_csv(df, dir):
        df.to_csv(dir, index=False)

    @staticmethod
    def load_csv(dir):
        df = pd.read_csv(dir)
        return df


class BaseScraper(DataStorage):
    def __init__(self, config):
        for name, value in config.items():
            setattr(self, f"_{name}", value)

    def convert_to_full_url(self, url_end):
        if url_end[0] == "/":
            url_end = url_end[1:]
        url_full = f"{self._base_url}/{url_end}"
        return url_full

    def make_soup(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        return soup

    def clean_str(self, string):
        return string.replace("\n", "").replace("\t", "").strip()
