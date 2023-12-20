import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from adapter import FPLAdapter, GoogleSheet, DynamoDB
from config import Config
from models import (
    PlayerGameweekData,
    PlayerRevenue,
    FPLEventStatus,
    MatchFixture,
    FPLEventStatusResponse,
)
import util


CACHE_TABLE_NAME = "FPLCacheTable"
# F4
START_POINT_COL = 6
START_POINT_ROW = 4


class Service:
    def __init__(self, google_sheet: GoogleSheet, config: Config):
        self.config = config
        self.google_sheet = google_sheet
        self.worksheet = self.google_sheet.open_worksheet_from_default_sheet(
            self.config.worksheet_name
        )
        self.fpl_adapter = FPLAdapter(
            league_id=config.league_id, cookies=config.cookies
        )
        self.dynamodb = DynamoDB(table_name=CACHE_TABLE_NAME)

    def update_gameweek(self, gameweek: int):
        response = self.dynamodb.put_json_item(
            key="gameweek", data={"gameweek": gameweek}
        )
        return response

    async def __construct_players_gameweek_pick_data(
        self, player: PlayerGameweekData, gameweek: int
    ):
        player_team = await self.fpl_adapter.get_player_team_by_id(
            player.player_id, gameweek=gameweek
        )
        for pick in player_team.picks:
            if pick.is_captain:
                c = await self.fpl_adapter.get_player_gameweek_info(
                    gameweek=gameweek, player_id=pick.element
                )
                player.points += c.total_points / 10000 * pick.multiplier
                player.captain_points = c.total_points * pick.multiplier
            if pick.is_vice_captain:
                c = await self.fpl_adapter.get_player_gameweek_info(
                    gameweek=gameweek, player_id=pick.element
                )
                player.points += c.total_points / 1000000 * pick.multiplier
                player.vice_captain_points = c.total_points * pick.multiplier
        return player

    @util.time_track(description="Construct Players Gameweek Data")
    async def __construct_players_gameweek_data(self, gameweek: int):
        h2h_result = await self.fpl_adapter.get_h2h_results(gameweek=gameweek)
        players_points_map: Dict[int, PlayerGameweekData] = {}
        results = h2h_result.results

        for result in results:
            # player 1
            p1_name = result.entry_1_name
            p1_point = util.add_noise(result.entry_1_points)
            p1_id = result.entry_1_entry
            # player 2
            p2_name = result.entry_2_name
            p2_point = util.add_noise(result.entry_2_points)
            p2_id = result.entry_2_entry

            if p1_name not in self.config.ignore_players:
                players_points_map[p1_id] = PlayerGameweekData(p1_name, p1_id, p1_point)
            if p2_name not in self.config.ignore_players:
                players_points_map[p2_id] = PlayerGameweekData(p2_name, p2_id, p2_point)

        futures = []
        for _, player in players_points_map.items():
            player_result_future = self.__construct_players_gameweek_pick_data(
                player, gameweek=gameweek
            )
            futures.append(player_result_future)

        players: List[PlayerGameweekData] = await asyncio.gather(*futures)

        # Sorting the list of PlayerResultData instances by the 'point' attribute
        players = sorted(players, key=lambda player: player.points, reverse=True)
        players = self.__expand_check_dupl_point(players=players)
        return players

    @util.time_track(description="Update FPL Table")
    async def get_or_update_fpl_gameweek_table(self, gameweek: int):
        if not self.__is_current_gameweek(gameweek=gameweek):
            cache = self.__lookup_gameweek_result_cache(gameweek)
            if cache is not None:
                return cache

        players = await self.__construct_players_gameweek_data(gameweek)
        current_point_col = START_POINT_COL + ((gameweek - 1) * 3)
        current_reward_col = current_point_col + 2

        # update point in sheet
        self.__update_players_points_map_in_sheet(
            current_point_col=current_point_col,
            start_point_row=START_POINT_ROW,
            players=players,
        )
        # update players's reward from sheet
        self.__update_players_reward_from_sheet(
            current_reward_col=current_reward_col,
            players=players,
            start_point_row=START_POINT_ROW,
        )

        # we should update shared reward only when gameweek is end
        if await self.__should_add_shared_result():
            # update player's shared reward (duplicated)
            self.__update_players_shared_reward(
                current_reward_col=current_reward_col, players=players
            )

        for player in players:
            self.worksheet.range("")
            player.cummulative_revenue = 0

        player_cache_items = [player.__dict__ for player in players]
        self.__put_cache_item(key=f"gameweek-{gameweek}", item=player_cache_items)

        return players

    async def list_players_revenues(self):
        standing_result = await self.fpl_adapter.get_h2h_league_standing()
        standings = standing_result.standings

        worksheet = self.google_sheet.open_worksheet_from_default_sheet(
            self.config.worksheet_name
        )

        player_ids = [x.value for x in worksheet.range(self.config.player_ids_range)]
        revenue_col = START_POINT_COL + (37 * 3) + 4
        players: List[PlayerRevenue] = []
        for i, player_id in enumerate(player_ids):
            for standing in standings:
                if standing.entry == int(player_id):
                    sheet_row = START_POINT_ROW + i
                    cell_value = worksheet.cell(sheet_row, revenue_col).numeric_value
                    player = PlayerRevenue(name=standing.entry_name, revenue=cell_value)
                    players.append(player)

        players = sorted(players, key=lambda player: player.revenue, reverse=True)

        return players

    def get_current_gameweek_from_dynamodb(self):
        item = self.dynamodb.get_item_by_hash_key("gameweek")
        data = item.get("Item").get("DATA").get("S")
        gameweek_data = json.loads(data)
        return gameweek_data.get("gameweek")

    async def get_current_gameweek(self) -> FPLEventStatus:
        result = await self.fpl_adapter.get_gameweek_event_status()
        if len(result.status) == 0:
            raise Exception("gameweek not found")
        gameweek_status = result.status[0]

        return gameweek_status

    def get_gameweek_last_match(self, gameweek: int) -> MatchFixture:
        fixtures = self.list_gameweek_fixtures(gameweek)
        last_match: Optional[MatchFixture] = None
        for fixture in fixtures:
            if last_match is None:
                last_match = fixture
            elif last_match.kickoff_time < fixture.kickoff_time:
                last_match = fixture
        return last_match

    async def list_gameweek_fixtures(self, gameweek: int):
        gameweek_fixtures = await self.fpl_adapter.list_gameweek_fixtures(
            gameweek=gameweek
        )
        return gameweek_fixtures

    def __is_current_gameweek(self, gameweek: int) -> bool:
        current_gameweek = self.get_current_gameweek_from_dynamodb()
        return current_gameweek == gameweek

    async def get_gameweek_event_status(
        self, gameweek: int
    ) -> Optional[FPLEventStatusResponse]:
        status = await self.fpl_adapter.get_gameweek_event_status()
        for s in status.status:
            if gameweek != s.event:
                return None
        return status

    async def __should_add_shared_result(self):
        now_date = datetime.utcnow().date()
        status_result = await self.fpl_adapter.get_gameweek_event_status()
        last_gameweek: Optional[FPLEventStatus] = None

        for s in status_result.status:
            if last_gameweek is None:
                last_gameweek = s
            elif last_gameweek.date < s.date:
                last_gameweek = s

        assert last_gameweek is not None
        if (
            now_date >= last_gameweek.date
            and last_gameweek.bonus_added
            and status_result.leagues == "Updated"
        ):
            return True

        return False

    @util.time_track(description="Update Players Reward from Sheet")
    def __update_players_reward_from_sheet(
        self,
        players: List[PlayerGameweekData],
        start_point_row: int,
        current_reward_col: int,
    ):
        raw_players_data = [
            cell.value for cell in self.worksheet.range(self.config.player_data_range)
        ]
        players_data = [
            raw_players_data[i : i + 2]
            for i in range(
                0,
                len(
                    raw_players_data,
                ),
                2,
            )
        ]
        cell_notations = []
        # update reward of each players
        for i, player_data in enumerate(players_data):
            player_id, bank_account = player_data
            for player in players:
                if player.player_id == int(player_id):
                    player.bank_account = bank_account
                    current_point_row = start_point_row + i
                    cell_notation = util.convert_to_a1_notation(
                        current_point_row, current_reward_col
                    )
                    cell_notations.append(cell_notation)
                    player.sheet_row = current_point_row

        cell_range = f"{cell_notations[0]}:{cell_notations[-1]}"
        cells = self.worksheet.range(cell_range)
        for player in players:
            for row, cell in enumerate(cells, start=start_point_row):
                if row == player.sheet_row:
                    cell_value = cell.numeric_value
                    player.reward = cell_value

    def __update_players_shared_reward(
        self, players: List[PlayerGameweekData], current_reward_col: int
    ):
        players_with_shared_reward: List[PlayerGameweekData] = [
            player for player in players if player.reward_division > 1
        ]
        if len(players_with_shared_reward) == 0:
            return
        player_new_reward_map: Dict[int, float] = {}
        cell_notations: List[str] = []
        cell_values: List[List[float, 1]] = []
        for player in players_with_shared_reward:
            sum_reward_amount = 0
            for _player in players:
                if _player.player_id in player.shared_reward_player_ids:
                    sum_reward_amount += _player.reward
            new_reward = sum_reward_amount / player.reward_division
            cell_notation = util.convert_to_a1_notation(
                player.sheet_row, current_reward_col
            )
            cell_notations.append(cell_notation)
            cell_values.append([new_reward])
            player_new_reward_map[player.player_id] = new_reward

        cell_range = f"{cell_notations[0]}:{cell_notations[-1]}"
        self.worksheet.update(cell_range, cell_values)

        for player in players_with_shared_reward:
            player.reward = player_new_reward_map[player.player_id]

    @util.time_track(description="Update Players point in Sheet")
    def __update_players_points_map_in_sheet(
        self,
        players: List[PlayerGameweekData],
        start_point_row: int,
        current_point_col: int,
    ):
        player_ids = [
            t.value for t in self.worksheet.range(self.config.player_ids_range)
        ]
        cell_notations: List[str] = []
        cell_values: List[List[float]] = []
        for i, player_id in enumerate(player_ids):
            for player in players:
                if player.player_id == int(player_id):
                    current_point_row = start_point_row + i
                    cell_notation = util.convert_to_a1_notation(
                        current_point_row, current_point_col
                    )
                    cell_notations.append(cell_notation)
                    cell_values.append([player.points])
                    break
        cell_range = f"{cell_notations[0]}:{cell_notations[-1]}"
        self.worksheet.update(cell_range, cell_values)

    def __expand_check_dupl_point(self, players: List[PlayerGameweekData]):
        players_points_map = [p.points for p in players]
        for i, p in enumerate(players):
            for j, point in enumerate(players_points_map):
                if i == j:
                    continue
                if util.is_equal_float(point, p.points):
                    p.reward_division += 1
                    p.shared_reward_player_ids.append(players[j].player_id)

        return players

    def __put_cache_item(self, key: str, item: any):
        response = self.dynamodb.put_json_item(key=key, data=item)
        return response

    def __lookup_gameweek_result_cache(
        self, gameweek: int
    ) -> Optional[List[PlayerGameweekData]]:
        response = self.dynamodb.get_item_by_hash_key(key=f"gameweek-{gameweek}")
        item = response.get("Item")
        if item is None:
            return None

        logger.info(f"cache hit for gameweek {gameweek}")

        data = item.get("DATA").get("S")
        players_objs = json.loads(data)
        player_data_dict = dict.fromkeys(PlayerGameweekData().__dict__.keys())
        players: List[PlayerGameweekData] = []
        for player_obj in players_objs:
            init_dict = {}
            for key in player_data_dict:
                init_dict[key] = player_obj[key]
            player = PlayerGameweekData(**init_dict)
            players.append(player)
        return players
