import os
from ast import literal_eval
from datetime import datetime

import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


def ymd():
    """Returns current timestamp as YYYYMMDD."""
    return datetime.now().strftime("%Y%m%d")


def ymdhms():
    """Returns current timestamp as YYYY-MM-DD HH:MM:SS."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def chunks(lst, n):
    """Yields successive n-sized chunks from input list."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def add_columns_to_df(df, dcols={}):
    """Adds columns to input DataFrame using {column_name: value, ...}."""
    for cname, value in dcols.items():
        df[cname] = value
    return df


def postproces_df(df, first_cols=[], drop_cols=[]):
    """Postprocesses DataFrame according to a few simple steps."""
    # convert all columns to lowercase
    df.columns = [c.lower() for c in df.columns]

    # drop columns from 'drop_cols' list
    df = df.drop(columns=drop_cols)

    # put columns in 'first_cols' list at the beginning
    new_cols = first_cols + [c for c in df.columns if c not in first_cols]
    df = df[new_cols]

    # drop duplicate rows
    df = df.drop_duplicates()

    return df


def add_coordinates(df, dir_coordinates="data/_coordinates.csv"):
    """Adds coordinates to DataFrame using address, sportshall and area columns."""
    # try to read in existing coordinates first
    if os.path.exists(dir_coordinates):
        df_coordinates = pd.read_csv(
            dir_coordinates, converters={"coordinates": literal_eval}
        )
        df = df.merge(df_coordinates, on=["sportshall", "address"], how="left")
    else:
        df["coordinates"] = None

    # fill in missing coordinates
    geolocator = RateLimiter(
        Nominatim(user_agent="address_finder").geocode, min_delay_seconds=1
    )  # delay is required by Nominatim usage policy

    def get_coordinates(address, address2, area, country="Belgium"):
        """
        Gets coordinates from an address as (latitude, longitude). Beware, there exist
        addresses with the same name even within the same area and country. Swapping
        address with the name of the location (e.g. sportshall) sometimes helps. If
        using 'address' returns None, a second attempt is done with 'address2'.
        """
        location = geolocator(f"{address}, {area}, {country}")
        if location is None:  # different attempt
            location = geolocator(f"{address2}, {area}, {country}")
        if location is not None:
            return location.latitude, location.longitude

    # fill in missing coordinates
    coordinates_missing = df[df["coordinates"].isnull()].apply(
        lambda x: get_coordinates(x["address"], x["sportshall"], x["area"]), axis=1
    )
    df.loc[coordinates_missing.index, "coordinates"] = coordinates_missing

    print(f"Nbr. of missing coordinates: {df['coordinates'].isnull().sum()}")

    # create or update existing coordinates file
    df_coordinates_new = df[["sportshall", "address", "coordinates"]]
    df_coordinates_new = df_coordinates_new.drop_duplicates(subset=["sportshall"])
    df_coordinates_new = df_coordinates_new[~df_coordinates_new["coordinates"].isna()]
    df_coordinates_new = df_coordinates_new.reset_index(drop=True)
    df_coordinates_new.to_csv(dir_coordinates, index=False)

    # split coordinates into latitude and longitude
    df["latitude"] = df["coordinates"].apply(lambda x: None if x is None else x[0])
    df["longitude"] = df["coordinates"].apply(lambda x: None if x is None else x[1])

    # drop coordinates column
    df = df.drop(columns=["coordinates"])

    return df
