__all__ = (
    "list_worlds",
    "get_world",
    "get_character",
    "get_online_characters",
    "count_sharers",
    "top_sharer",
    "top_percentage",
)

import typing

import bs4
import requests

from . import objects, utils


def list_worlds() -> typing.Iterator[objects.World]:
    response = requests.get("https://www.tibia.com/community/?subtopic=worlds")
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    rows = list(
        soup.find("table", class_="Table3").find_all("table", class_="TableContent")
    )[2].find_all("tr")[1:]
    for row in rows:
        yield objects.World.from_row(row)


def get_world(world_name: str) -> objects.World:
    response = requests.get(
        f"https://www.tibia.com/community/?subtopic=worlds&world={world_name}"
    )
    return objects.World.from_world_page(response.text, name=world_name)


def get_character(char_name: str) -> objects.Character:
    url = f"https://www.tibia.com/community/?subtopic=characters&name={char_name}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code=}")

    char = objects.Character.from_character_page(response.text)
    char.world = get_world(char.world)
    return char


def get_online_characters(world: str) -> list:
    url = f"https://www.tibia.com/community/?subtopic=worlds&world={world}&order=level_desc"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code=}")

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    table = (
        soup.find("table", class_="Table2")
        .find("div", class_="InnerTableContainer")
        .find("table")
    )
    rows = table.find_all("tr")[1:]
    fields = ["Name", "Level", "Vocation"]
    return [
        objects.Character(
            **dict(zip(fields, [utils.decode(c.text) for c in row.children]))
        )
        for row in rows
    ]


def count_sharers(chars: list, level: int) -> int:
    min_lvl = utils.min_sharer(level)
    max_lvl = utils.max_sharer(level)
    levels = [c.level for c in chars]
    return sum([levels.count(i) for i in range(min_lvl, max_lvl + 1)])


def top_sharer(chars: list) -> tuple:
    max_sharers = (0, 0)
    levels = [c.level for c in chars]
    for lvl in range(min(levels), max(levels)):
        sharers = count_sharers(chars, lvl)
        if sharers > max_sharers[1]:
            max_sharers = (lvl, sharers)
    return max_sharers


def top_percentage(chars: list, my_level: int) -> float:
    for i, c in enumerate(chars):
        if c.level < my_level:
            return i / len(chars)
