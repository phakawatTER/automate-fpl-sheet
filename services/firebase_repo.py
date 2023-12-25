from typing import List
from dataclasses import dataclass
from database import FirebaseRealtimeDatabase


class _Schema:
    LINE_CHANNELS = "line_channels"
    LEAGUES = "leagues"
    LEAGUE_PLAYERS = "league_players"
    LEAGUE_SHEETS = "league_sheets"
    LEAGUE_IGNORED_PLAYERS = "league_ignored_players"


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
    DB_NAME = "fpl_line_bot"

    def __init__(self, firebase: FirebaseRealtimeDatabase):
        self.__db = firebase.set_ref(FirebaseRepo.DB_NAME)

    def subscribe_league(self, league_id: int, line_group_id: str):
        return self.__db.put_data(
            f"{_Schema.LINE_CHANNELS}/{line_group_id}", [league_id]
        )

    def unsubscribe_league(self, line_group_id: int):
        return self.__db.delete_data(f"{_Schema.LINE_CHANNELS}/{line_group_id}")

    def list_line_channels(self) -> List[str]:
        data = self.__db.get_data(f"{_Schema.LINE_CHANNELS}")
        channels = list(data.keys())
        return channels

    def list_leagues_by_line_group_id(self, group_id: str) -> List[int]:
        data = self.__db.get_data(f"{_Schema.LINE_CHANNELS}/{group_id}")
        return data

    def list_leagues(self) -> List[int]:
        data = self.__db.get_data(f"{_Schema.LEAGUES}")
        return data

    def list_league_players(self, league_id: int):
        data = self.__db.get_data(f"{_Schema.LEAGUE_PLAYERS}/{league_id}")
        return [PlayerData(**d) for d in data]

    def get_league_google_sheet(self, league_id: int):
        data = self.__db.get_data(f"{_Schema.LEAGUE_SHEETS}/{league_id}")
        return LeagueSheet(**data)

    def list_league_ignored_players(self, league_id: int) -> List[int]:
        data = self.__db.get_data(f"{_Schema.LEAGUE_IGNORED_PLAYERS}/{league_id}")
        return data
