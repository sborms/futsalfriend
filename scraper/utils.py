from datetime import datetime


def now():
    """Returns current timestamp up to seconds."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
