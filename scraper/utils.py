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
