from typing import List
from dataclasses import dataclass
from database import FirebaseRealtimeDatabase


class _Schema:
    LINE_CHANNELS = "line_channels"
    LEAGUES = "leagues"
    LEAGUE_PLAYERS = "league_players"
    LEAGUE_SHEETS = "league_sheets"


BASE_PATH = "fpl_line_bot"


@dataclass
class LeagueSheet:
    url: str
    worksheet: str


@dataclass
class PlayerData:
    bank_account: str
    player_id: int
    season_rank: int
    name: str
    team_name: str


class FirebaseRepo:
    def __init__(self, firebase: FirebaseRealtimeDatabase):
        self.__db = firebase

    def list_line_channels(self) -> List[str]:
        data = self.__db.get_data(f"{BASE_PATH}/{_Schema.LINE_CHANNELS}")
        channels = list(data.keys())
        return channels

    def list_leagues_by_line_group_id(self, group_id: str) -> List[int]:
        data = self.__db.get_data(f"{BASE_PATH}/{_Schema.LINE_CHANNELS}/{group_id}")
        return data

    def list_leagues(self) -> List[int]:
        data = self.__db.get_data(f"{BASE_PATH}/{_Schema.LEAGUES}")
        return data

    def list_league_players(self, league_id: int):
        data = self.__db.get_data(f"{BASE_PATH}/{_Schema.LEAGUE_PLAYERS}/{league_id}")
        return [PlayerData(**d) for d in data]

    def get_league_google_sheet(self, league_id: int):
        data = self.__db.get_data(f"{BASE_PATH}/{_Schema.LEAGUE_SHEETS}/{league_id}")
        return LeagueSheet(**data)
