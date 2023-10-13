from datetime import datetime


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
