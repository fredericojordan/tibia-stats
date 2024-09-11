__all__ = (
    "decode",
    "min_sharer",
    "max_sharer",
    "parse_tibian_date",
)

import datetime


def min_sharer(level: int) -> int:
    return int(level * 2 / 3)


def max_sharer(level: int) -> int:
    return int(level * 3 / 2) + 1


def parse_tibian_date(date: str) -> datetime.datetime:
    cet_timezone = datetime.timezone(datetime.timedelta(hours=2), name="CET")
    no_tz_date = date.rsplit(" ", 1)[0]
    return (
        datetime.datetime.strptime(no_tz_date, "%b %d %Y, %H:%M:%S")
        .replace(tzinfo=cet_timezone)
        .astimezone(datetime.timezone.utc)
    )


def decode(input_str: str) -> str:
    return input_str.replace("\xa0", " ")
