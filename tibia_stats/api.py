__all__ = (
    "list_worlds",
    "get_world",
    "get_character",
    "get_online_characters",
    "plot",
    "count_sharers",
    "top_sharer",
    "top_percentage",
    "view",
)

import typing

import bs4
import matplotlib.pyplot as plt
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
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("table", class_="Table1")[1].find("table").find_all("tr")
    data = dict(r.text.replace("\xa0", " ").split(":", 1) for r in rows)
    return objects.World(name=world_name, **data)


def get_character(char_name: str) -> objects.Character:
    url = f"https://www.tibia.com/community/?subtopic=characters&name={char_name}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code=}")

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    table = (
        soup.find("table", class_="Table3")
        .find("div", class_="TableContentContainer")
        .find("table")
    )
    rows = table.find_all("tr")
    data = dict(r.text.replace("\xa0", " ").split(":", 1) for r in rows)
    char = objects.Character(**data)
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
    characters = [
        objects.Character(
            Name=list(r.children)[0].text.replace("\xa0", " "),
            Level=int(list(r.children)[1].text),
            Vocation=list(r.children)[2].text.replace("\xa0", " "),
        )
        for r in rows
    ]

    return characters


def plot(
    online_chars: list,
    world: objects.World,
    bin_size: int = None,
    my_lvl: int = None,
    share_lvl: int = None,
):
    # fig = plt.figure(figsize = (4, 2))
    fig = plt.figure()
    levels = [c.level for c in online_chars]
    bins = range(0, max(levels) + bin_size, bin_size) if bin_size else "auto"
    plt.hist(levels, bins=bins, color=world.color)
    plt.title(f"{len(online_chars)} Online Characters in {world.name}")
    plt.xticks(range(0, 2800, 200))
    plt.xlabel("Character Level")
    plt.ylabel("No. of characters")

    if my_lvl:
        plt.axvline(x=my_lvl, color="blue")
        plt.axvspan(
            utils.min_sharer(my_lvl), utils.max_sharer(my_lvl), alpha=0.2, color="blue"
        )

    if share_lvl:
        plt.axvline(x=share_lvl, color="lime")

    plt.show()


def count_sharers(chars: list, level: int):
    min_lvl = utils.min_sharer(level)
    max_lvl = utils.max_sharer(level)
    levels = [c.level for c in chars]
    return sum([levels.count(i) for i in range(min_lvl, max_lvl + 1)])


def top_sharer(chars: list):
    max_sharers = (0, 0)
    levels = [c.level for c in chars]
    for lvl in range(min(levels), max(levels)):
        sharers = count_sharers(chars, lvl)
        if sharers > max_sharers[1]:
            max_sharers = (lvl, sharers)
    return max_sharers


def top_percentage(chars: list, my_level: int):
    for i, c in enumerate(chars):
        if c.level < my_level:
            return i / len(chars)


def view(world: objects.World, my_lvl: int = None, bin_size: int = 100):
    chars = get_online_characters(world.name)

    top_lvl = max(chars, key=lambda c: c.level)
    print(
        f"{top_lvl.name!r} ({top_lvl.vocation.name}) is highest online at lvl {top_lvl.level}"
    )

    share_lvl, share_count = top_sharer(chars)
    print(f"Level {share_lvl} has a maximum of {share_count} potential party mates")

    if my_lvl:
        percentage = top_percentage(chars, my_lvl)
        print(
            f"Level {my_lvl} has {count_sharers(chars, my_lvl)} potential party mates and is in top {100 * percentage:.2f} % of characters"
        )

    plot(chars, world, bin_size, my_lvl, share_lvl)
