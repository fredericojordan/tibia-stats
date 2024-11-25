import datetime
import enum
import typing

import bs4
import humanize
import pydantic

from . import utils


class Pvp(enum.StrEnum):
    OPEN = "Open PvP"
    OPEN_RETRO = "Retro Open PvP"
    OPTIONAL = "Optional PvP"
    HARDCORE = "Hardcore PvP"
    HARDCORE_RETRO = "Retro Hardcore PvP"


class Location(enum.StrEnum):
    SA = "South America"
    EU = "Europe"
    NA = "North America"
    OC = "Oceania"


class BattleEye(enum.StrEnum):
    GREEN = enum.auto()
    YELLOW = enum.auto()
    UNSET = ""


class WorldType(enum.StrEnum):
    REGULAR = "Regular"
    EXPERIMENTAL = "Experimental"


class OnlineStatus(enum.StrEnum):
    ONLINE = "Online"
    OFFLINE = "Offline"


class World(pydantic.BaseModel):
    name: str
    online_current: int = pydantic.Field(
        default=None, validation_alias="Players Online"
    )
    location: Location = pydantic.Field(validation_alias="Location")
    pvp: Pvp = pydantic.Field(validation_alias="PvP Type")
    battle_eye: BattleEye = pydantic.Field(validation_alias="BattlEye Status")

    status: OnlineStatus | None = pydantic.Field(
        default=None, validation_alias="Status"
    )
    online_record_count: int | None = pydantic.Field(
        default=None, validation_alias="Online Record"
    )
    online_record_date: datetime.datetime | None = pydantic.Field(default=None)
    created_at: str | None = pydantic.Field(
        default=None, validation_alias="Creation Date"
    )
    world_quests: list[str] | None = pydantic.Field(
        default=None, validation_alias="World Quest Titles"
    )
    world_type: WorldType | None = pydantic.Field(
        default=None, validation_alias="Game World Type"
    )
    additional_info: str | None = pydantic.Field(default=None)

    @classmethod
    def from_world_page(cls, world_page: str, **kw) -> "World":
        soup = bs4.BeautifulSoup(world_page, "html.parser")
        rows = soup.find_all("table", class_="Table1")[1].find("table").find_all("tr")
        data = dict(utils.decode(r.text).split(":", 1) for r in rows)
        return cls(**data, **kw)

    @pydantic.field_validator("battle_eye", mode="before")
    @classmethod
    def parse_battle_eye(cls, value: typing.Any) -> BattleEye:
        if isinstance(value, str):
            if "since its release" in value:
                return BattleEye.GREEN
            elif "Not protected" in value:
                return BattleEye.UNSET
            else:
                return BattleEye.YELLOW

        if image_tag := value.find("image"):
            return (
                BattleEye.GREEN
                if "battleyeinitial" in image_tag["src"]
                else BattleEye.YELLOW
            )
        else:
            return BattleEye.UNSET

    @classmethod
    def from_row(cls, row) -> "World":
        row_fields = [
            "name",
            "Players Online",
            "Location",
            "PvP Type",
            "BattlEye Status",
            "additional_info",
        ]
        instance = cls(**dict(zip(row_fields, [c.text.strip() for c in row.children])))
        instance.battle_eye = cls.parse_battle_eye(list(row.children)[4])
        return instance

    @property
    def color(self):
        colors = {
            Pvp.OPEN: "blue",
            Pvp.OPEN_RETRO: "darkblue",
            Pvp.OPTIONAL: "green",
            Pvp.HARDCORE: "red",
            Pvp.HARDCORE_RETRO: "darkred",
        }
        return colors.get(self.pvp, "blue")

    @pydantic.field_validator("world_quests", mode="before")
    @classmethod
    def split_quests(cls, value: str | list) -> list:
        return (
            [v.strip() for v in value.split(",")] if isinstance(value, str) else value
        )

    @pydantic.model_validator(mode="before")
    @classmethod
    def parse_online_record(cls, data: dict) -> dict:
        """900 players (on Jul 04 2020, 03:34:30 CEST)"""
        if raw_record := data.get("Online Record"):
            count, date_str = raw_record.split(" players (on ")
            data["Online Record"] = int(count.replace(",", ""))
            data["online_record_date"] = utils.parse_tibian_date(date_str.strip(")"))
        return data


class Gender(enum.StrEnum):
    MALE = enum.auto()
    FEMALE = enum.auto()


class Premium(enum.StrEnum):
    PREMIUM = "Premium Account"
    FREE = "Free Account"


class Vocation(enum.StrEnum):
    MS = "Master Sorcerer"
    EK = "Elite Knight"
    RP = "Royal Paladin"
    ED = "Elder Druid"
    S = "Sorcerer"
    K = "Knight"
    P = "Paladin"
    D = "Druid"
    NONE = "None"


class Character(pydantic.BaseModel):
    name: str = pydantic.Field(validation_alias="Name")
    vocation: Vocation = pydantic.Field(validation_alias="Vocation")
    level: int = pydantic.Field(validation_alias="Level")

    title: str | None = pydantic.Field(default=None, validation_alias="Title")
    title_count: int | None = pydantic.Field(default=None)
    gender: Gender | None = pydantic.Field(default=None, validation_alias="Sex")
    achievements: int | None = pydantic.Field(
        default=None, validation_alias="Achievement Points"
    )
    world: str | World | None = pydantic.Field(default=None, validation_alias="World")
    residence: str | None = pydantic.Field(default=None, validation_alias="Residence")
    house: str | None = pydantic.Field(default=None, validation_alias="House")
    guild_membership: str | None = pydantic.Field(
        default=None, validation_alias="Guild Membership"
    )
    last_login: datetime.datetime | None = pydantic.Field(
        default=None, validation_alias="Last Login"
    )
    comment: str | None = pydantic.Field(default=None, validation_alias="Comment")
    premium: Premium | None = pydantic.Field(
        default=None, validation_alias="Account Status"
    )

    @classmethod
    def from_character_page(cls, character_page: str) -> "Character":
        soup = bs4.BeautifulSoup(character_page, "html.parser")
        table = (
            soup.find("table", class_="Table3")
            .find("div", class_="TableContentContainer")
            .find("table")
        )
        rows = table.find_all("tr")
        data = dict(utils.decode(r.text).split(":", 1) for r in rows)
        return cls(**data)

    @pydantic.field_validator("last_login", mode="before")
    @classmethod
    def parse_last_login(cls, last_login: str | None) -> datetime.datetime | None:
        if last_login is None:
            return None

        return utils.parse_tibian_date(last_login)

    @pydantic.model_validator(mode="before")
    @classmethod
    def parse_title(cls, data: dict) -> dict:
        if raw_title := data.get("Title"):
            data["Title"], rest = raw_title.rsplit(" (", 1)
            data["title_count"] = int(rest.split(" ")[0])
        return data

    @property
    def life(self) -> int:
        if self.level < 9:
            return 145 + (self.level * 5)

        if self.vocation in [Vocation.EK, Vocation.K]:
            delta = 15
        elif self.vocation in [Vocation.RP, Vocation.P]:
            delta = 10
        else:
            delta = 5

        return delta * (self.level - 8) + 185

    @property
    def mana(self) -> int:
        if self.level < 9:
            return 50 + (self.level * 5)

        if self.vocation in [Vocation.MS, Vocation.S, Vocation.ED, Vocation.D]:
            delta = 30
        elif self.vocation in [Vocation.RP, Vocation.P]:
            delta = 15
        else:
            delta = 5

        return int(delta * (self.level - 8)) + 90

    @property
    def promotion(self) -> bool:
        return self.vocation in [Vocation.MS, Vocation.ED, Vocation.RP, Vocation.EK]

    @property
    def cap(self) -> int:
        if self.level < 9:
            return 390 + int(self.level * 10)

        if self.vocation in [Vocation.EK, Vocation.K]:
            delta = 25
        elif self.vocation in [Vocation.RP, Vocation.P]:
            delta = 20
        else:
            delta = 10

        return int(delta * (self.level - 8)) + 470

    @property
    def min_sharing_lvl(self) -> int:
        return utils.min_sharer(self.level)

    @property
    def max_sharing_lvl(self) -> int:
        return utils.max_sharer(self.level)

    @property
    def last_login_human(self) -> str:
        return f"last login {humanize.naturaldelta(datetime.datetime.now(datetime.UTC) - self.last_login)} ago"
