from geopy.distance import distance
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="address_finder").geocode


def get_coordinates(address, city, country="Belgium"):
    """Gets coordinates from user input address as (latitude, longitude)."""
    location = geolocator(f"{address}, {city}, {country}")
    if location is not None:
        return location.latitude, location.longitude


def compute_distance(lat, lon, address_target: tuple):
    """Computes km distance between a (latitude, longitude) point and target address."""
    try:
        return distance((lat, lon), address_target).km
    except ValueError:
        return None


def make_clickable(url, name):
    """Returns the HTML that makes a named URL clickable."""
    return f"<a href='{url}' rel='noopener noreferrer' target='_blank'>{name}</a>"


def filter_teams(df, city, address, km):
    """Filters teams based on distance from target address."""
    # get coordinates of target address
    address_target = get_coordinates(address, city)

    # filter teams based on distance
    df["distance"] = df.apply(
        lambda x: compute_distance(x["latitude"], x["longitude"], address_target),
        axis=1,
    )
    df_out = df[df["distance"] <= km].copy()

    # finetune team selection
    df_out = (
        df_out.sort_values(["team", "distance"], ascending=True)
        .drop_duplicates(subset=["team"], keep="first")  # keep single closest location
        .sort_values("distance")
        .drop(
            columns=[
                "area",
                "address",
                "phone",
                "email",
                "latitude",
                "longitude",
                "distance",
            ]
        )
    )

    return df_out


def style_table(df, drop_cols=[]):
    """Styles DataFrame for pretty display in Streamlit."""
    # convert all float columns to int
    cols_float = df.select_dtypes(include=["float"]).columns
    df[cols_float] = df[cols_float].astype(int)

    # hide URLs under respective name and make them clickable
    df["team"] = df.apply(lambda x: make_clickable(x["url_team"], x["team"]), axis=1)
    df["sportshall"] = df.apply(
        lambda x: make_clickable(x["url_sportshall"], x["sportshall"]), axis=1
    )

    # remove specified columns and uppercase remaining ones
    drop_cols += ["url_team", "url_sportshall"]
    df = df.drop(columns=drop_cols)
    df.columns = df.columns.str.upper()

    # left-align all columns and values
    df = df.style.map(lambda x: "text-align: left;").hide(axis="index")

    return df
