from typing import List, Optional
import models
from database import FirebaseRealtimeDatabase


class _Schema:
    LINE_CHANNELS = "line_channels"
    LEAGUE_PLAYERS = "league_players"
    LEAGUE_SHEETS = "league_sheets"
    LEAGUE_IGNORED_PLAYERS = "league_ignored_players"
    LEAGUE_GAMEWEEK_REWARDS = "league_gameweek_rewards"
    LEAGUE_GAMEWEEK_RESULTS = "league_gameweek_results"


class FirebaseRepo:
    DB_NAME = "fpl_line_bot"

    def __init__(self, firebase: FirebaseRealtimeDatabase):
        self.__db = firebase.set_ref(FirebaseRepo.DB_NAME)

    def put_league_gameweek_results(
        self,
        league_id: int,
        player_gameweek_results: List[models.PlayerGameweekData],
        gameweek: int,
    ):
        return self.__db.put_data(
            f"{_Schema.LEAGUE_GAMEWEEK_RESULTS}/{league_id}/{gameweek}",
            [p.to_json() for p in player_gameweek_results],
        )

    def get_league_gameweek_results(
        self, league_id: int, gameweek: int
    ) -> Optional[List[models.PlayerGameweekData]]:
        data = self.__db.get_data(
            f"{_Schema.LEAGUE_GAMEWEEK_RESULTS}/{league_id}/{gameweek}"
        )
        if data is None:
            return None
        return [models.PlayerGameweekData(**d) for d in data]

    def list_league_gameweek_rewards(self, league_id: int) -> Optional[List[float]]:
        data = self.__db.get_data(f"{_Schema.LEAGUE_GAMEWEEK_REWARDS}/{league_id}")
        return data

    def put_league_rewards(self, league_id: int, rewards: List[float]):
        return self.__db.put_data(
            f"{_Schema.LEAGUE_GAMEWEEK_REWARDS}/{league_id}", rewards
        )

    def put_league_players(self, league_id: int, players: List[models.PlayerData]):
        return self.__db.put_data(
            f"{_Schema.LEAGUE_PLAYERS}/{league_id}",
            [p.to_json() for p in players],
        )

    def put_league_sheet(self, league_id, league_sheet: models.LeagueSheet):
        print(league_sheet.to_json())
        return self.__db.put_data(
            f"{_Schema.LEAGUE_SHEETS}/{league_id}", league_sheet.to_json()
        )

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

    def list_league_players(self, league_id: int) -> Optional[List[models.PlayerData]]:
        data = self.__db.get_data(f"{_Schema.LEAGUE_PLAYERS}/{league_id}")
        if data is None:
            return None
        return [models.PlayerData(**d) for d in data]

    def get_league_google_sheet(self, league_id: int) -> models.LeagueSheet:
        data = self.__db.get_data(f"{_Schema.LEAGUE_SHEETS}/{league_id}")
        return models.LeagueSheet(**data)

    def list_league_ignored_players(self, league_id: int) -> List[int]:
        data = self.__db.get_data(f"{_Schema.LEAGUE_IGNORED_PLAYERS}/{league_id}")
        return data if data is not None else []

    def put_league_ignored_players(self, league_id, ignored_player_ids: List[int]):
        return self.__db.put_data(
            f"{_Schema.LEAGUE_IGNORED_PLAYERS}/{league_id}",
            ignored_player_ids,
        )
