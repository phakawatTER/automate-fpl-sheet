from loguru import logger
import models
from adapter import FPLAdapter
from services import FirebaseRepo


class Service:
    def __init__(self, fpl_adapter: FPLAdapter, firebase_repo: FirebaseRepo):
        self.__fpl_adapter = fpl_adapter
        self.__firebase_repo = firebase_repo

    async def subscribe_league(self, league_id: int, group_id: str):
        try:
            entries = await self.__fpl_adapter.get_league_entries(league_id=league_id)
            players: list[models.PlayerData] = []
            for entry in entries:
                e = models.PlayerData(
                    bank_account="",
                    name=entry.player_name,
                    player_id=entry.entry,
                    season_rank=0,
                    team_name=entry.entry_name,
                )
                players.append(e)

            self.__firebase_repo.put_league_players(
                league_id=league_id,
                players=players,
            )

            self.__firebase_repo.subscribe_league(
                league_id=league_id,
                line_group_id=group_id,
            )
            return True
        except Exception as e:
            logger.error(f"error subscribe league with error: {e}")
            return False

    def update_league_sheet(self, league_id: int, url: str, worksheet_name: str):
        league_sheet = models.LeagueSheet(url=url, worksheet=worksheet_name)
        return self.__firebase_repo.put_league_sheet(
            league_id=league_id,
            league_sheet=league_sheet,
        )
