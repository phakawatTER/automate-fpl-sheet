import json
import asyncio
from dataclasses import asdict
from typing import Dict, List, Optional
from loguru import logger
from adapter import FPLAdapter, DynamoDB
from config import Config
from models import (
    PlayerGameweekData,
    PlayerRevenue,
    FPLEventStatus,
    FPLMatchFixture,
    FPLEventStatusResponse,
    FPLPlayerHistory,
    FPLFantasyTeam,
    BootstrapElement,
    PlayerGameweekPicksData,
    FPLLiveEventElement,
    BootstrapTeam,
)
import util
from .firebase_repo import FirebaseRepo


CACHE_TABLE_NAME = "FPLCacheTable"


def _construct_cache_hash(league_id, gameweek):
    return f"{league_id}-gameweek-{gameweek}"


class Service:
    def __init__(
        self,
        config: Config,
        fpl_adapter: FPLAdapter,
        firebase_repo: FirebaseRepo,
    ):
        self.config = config
        self.fpl_adapter = fpl_adapter
        self.dynamodb = DynamoDB(table_name=CACHE_TABLE_NAME)
        self.firebase_repo = firebase_repo

    def update_gameweek(self, gameweek: int):
        response = self.dynamodb.put_json_item(
            key="gameweek", data={"gameweek": gameweek}
        )
        return response

    async def __construct_player_gameweek_pick_data(
        self, player: PlayerGameweekData, gameweek: int
    ):
        player_team = await self.fpl_adapter.get_player_team_by_id(
            player.player_id, gameweek=gameweek
        )
        player.points -= player_team.entry_history.event_transfers_cost
        player.subsitution_cost = -1 * player_team.entry_history.event_transfers_cost
        for pick in player_team.picks:
            player_gameweek_history: Optional[FPLPlayerHistory] = None
            if pick.is_captain or pick.is_vice_captain:
                player_gameweek_history = (
                    await self.fpl_adapter.get_player_gameweek_info(
                        gameweek=gameweek, player_id=pick.element
                    )
                )
            if player_gameweek_history is not None:
                if pick.is_captain:
                    # adding some noise to captain pick
                    player.points += (
                        player_gameweek_history.total_points / 10000 * pick.multiplier
                    )
                    player.captain_points = (
                        player_gameweek_history.total_points * pick.multiplier
                    )
                if pick.is_vice_captain:
                    # adding some noise to vice captain pick
                    player.points += (
                        player_gameweek_history.total_points / 1000000 * pick.multiplier
                    )
                    player.vice_captain_points = (
                        player_gameweek_history.total_points * pick.multiplier
                    )
        return player

    @util.time_track(description="Construct Players Gameweek Data")
    async def __construct_players_gameweek_data(self, gameweek: int, league_id: int):
        classic_standings = await self.fpl_adapter.get_classic_league_standings(
            league_id=league_id
        )
        players_points_map: Dict[int, PlayerGameweekData] = {}
        ignored_players = self.firebase_repo.list_league_ignored_players(league_id)
        ignored_players.append(None)
        league_players = self.firebase_repo.list_league_players(league_id)
        if league_players is None:
            raise Exception(f"league players for {league_id} not found")

        for result in classic_standings.standings.results:
            # player 1
            p1_name = result.entry_name
            p1_point = util.add_noise(result.event_total)
            p1_id = result.entry

            if p1_id not in ignored_players:
                players_points_map[p1_id] = PlayerGameweekData(
                    team_name=p1_name, player_id=p1_id, points=p1_point
                )

        futures = []
        for _, player in players_points_map.items():
            player_result_future = self.__construct_player_gameweek_pick_data(
                player, gameweek=gameweek
            )
            futures.append(player_result_future)

        players: List[PlayerGameweekData] = await asyncio.gather(*futures)

        # Sorting the list of PlayerResultData instances by the 'point' attribute
        players = sorted(players, key=lambda player: player.points, reverse=True)
        players = self.__expand_check_dupl_point(players=players)

        for p in players:
            for fp in league_players:
                if fp.player_id == p.player_id:
                    p.name = fp.name
                    p.bank_account = fp.bank_account

        return players

    @util.time_track(description="Update FPL Table")
    async def get_or_update_fpl_gameweek_table(
        self, gameweek: int, league_id: int, ignore_cache=False
    ):
        if not self.__is_current_gameweek(gameweek=gameweek) and not ignore_cache:
            cache = self.__lookup_gameweek_result_cache(gameweek, league_id)
            if cache is not None:
                return cache

        players = await self.__construct_players_gameweek_data(gameweek, league_id)
        league_gameweek_rewards = self.firebase_repo.list_league_gameweek_rewards(
            league_id
        )
        if league_gameweek_rewards is None:
            return players
        if len(players) != len(league_gameweek_rewards):
            raise Exception("total number of rewards not equal to number of players")

        new_reward_map: dict[int, float] = {}

        players = sorted(players, key=lambda player: player.points, reverse=True)
        for i, p in enumerate(players):
            p.reward = league_gameweek_rewards[i]

        players_with_shared_reward = [
            player for player in players if player.reward_division > 1
        ]

        for p in players_with_shared_reward:
            sum_reward = 0
            for inner_p in players_with_shared_reward:
                sum_reward += inner_p.reward
            new_reward = round(sum_reward / p.reward_division, 2)
            new_reward_map[p.player_id] = new_reward

        for p in players_with_shared_reward:
            p.reward = new_reward_map[p.player_id]

        is_ok = self.firebase_repo.put_league_gameweek_results(
            league_id=league_id,
            player_gameweek_results=players,
            gameweek=gameweek,
        )
        if not is_ok:
            raise Exception("unable to update gameweek result")

        player_cache_items = [player.to_json() for player in players]
        self.__put_cache_item(
            key=_construct_cache_hash(league_id, gameweek), item=player_cache_items
        )

        return players

    async def list_players_revenues(self, league_id: int):
        current_gameweek_status = await self.get_current_gameweek()
        current_gameweek = current_gameweek_status.event
        players = await self.__construct_players_gameweek_data(
            gameweek=current_gameweek, league_id=league_id
        )
        player_revs_map: Dict[int, PlayerRevenue] = {}

        for p in players:
            player_revs_map[p.player_id] = PlayerRevenue(
                name=p.name,
                revenue=0,
                team_name=p.team_name,
            )

        for gw in range(1, current_gameweek + 1, 1):
            gameweek_results = self.firebase_repo.get_league_gameweek_results(
                league_id=league_id,
                gameweek=gw,
            )
            if gameweek_results is None:
                raise Exception(
                    "error when getting revenue with error gameweek results not found"
                )
            for player_result in gameweek_results:
                player_revs_map[player_result.player_id].revenue += player_result.reward

        player_revs = [p_rev for _, p_rev in player_revs_map.items()]
        player_revs = sorted(player_revs, key=lambda p_rev: p_rev.revenue, reverse=True)

        return player_revs

    def get_current_gameweek_from_dynamodb(self) -> int:
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

    def get_gameweek_last_match(self, gameweek: int) -> FPLMatchFixture:
        fixtures = self.list_gameweek_fixtures(gameweek)
        last_match: Optional[FPLMatchFixture] = None
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
        teams = await self.list_league_teams()
        team_map: dict[int, BootstrapTeam] = {}
        for team in teams:
            team_map[team.id] = team
        for fixture in gameweek_fixtures:
            team_a = team_map[fixture.team_a]
            team_h = team_map[fixture.team_h]
            fixture.team_a_data = team_a
            fixture.team_h_data = team_h

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

    def __expand_check_dupl_point(self, players: List[PlayerGameweekData]):
        players_points_map = [p.points for p in players]
        for i, p in enumerate(players):
            for j, point in enumerate(players_points_map):
                if i == j:
                    continue
                if util.is_equal_float(point, p.points) and p.points > 1:
                    p.reward_division += 1
                    p.shared_reward_player_ids.append(players[j].player_id)

        return players

    def __put_cache_item(self, key: str, item: any):
        response = self.dynamodb.put_json_item(key=key, data=item)
        return response

    def __lookup_gameweek_result_cache(
        self,
        gameweek: int,
        league_id: int,
    ) -> Optional[List[PlayerGameweekData]]:
        response = self.dynamodb.get_item_by_hash_key(
            key=_construct_cache_hash(league_id, gameweek)
        )
        item = response.get("Item")
        if item is None:
            return None

        logger.info(f"cache hit for gameweek {gameweek}")

        data = item.get("DATA").get("S")
        players_objs = json.loads(data)
        player_data_dict = dict.fromkeys(PlayerGameweekData().to_json().keys())
        players: List[PlayerGameweekData] = []
        for player_obj in players_objs:
            init_dict = {}
            for key in player_data_dict:
                init_dict[key] = player_obj[key]
            player = PlayerGameweekData(**init_dict)
            players.append(player)
        return players

    async def get_gameweek_live_event(
        self, gameweek: int
    ) -> dict[int, FPLLiveEventElement]:
        response = await self.fpl_adapter.get_gameweek_live_event(gameweek=gameweek)
        element_map: Dict[int, FPLLiveEventElement] = {}
        for element in response.elements:
            element_map[element.id] = element
        return element_map

    async def __list_fantasy_teams(self, gameweek: int, league_id: int):
        ignore_player_ids = self.firebase_repo.list_league_ignored_players(league_id)
        players_data = self.firebase_repo.list_league_players(league_id)
        if players_data is None:
            raise Exception(f"league players for {league_id} not found")
        players_data = [p for p in players_data if p.player_id not in ignore_player_ids]

        player_picks_dict = {}
        futures = []
        for player_data in players_data:
            future = asyncio.ensure_future(
                self.fpl_adapter.get_player_team_by_id(
                    player_id=player_data.player_id, gameweek=gameweek
                )
            )
            futures.append(future)
            player_picks_dict[player_data.team_name] = []

        results: List[FPLFantasyTeam] = await asyncio.gather(*futures)

        return results, players_data

    @util.time_track(description="List player gameweek picks")
    async def list_player_gameweek_picks(self, gameweek: int, league_id: int):
        gameweek_live_event_dict: Dict[int, FPLLiveEventElement] = (
            await self.get_gameweek_live_event(gameweek=gameweek)
        )
        fantasy_teams, players_data = await self.__list_fantasy_teams(
            gameweek=gameweek, league_id=league_id
        )

        bootstrap_data = await self.fpl_adapter.get_bootstrap()
        elements = bootstrap_data.elements
        players_gameweek_picks: List[PlayerGameweekPicksData] = []

        for r, player_data in zip(fantasy_teams, players_data):
            picks: List[BootstrapElement] = []
            for pick in r.picks:
                for element in elements:
                    if element.id == pick.element:
                        # need to create new instance to avoid mutation
                        new_element = BootstrapElement(**asdict(element))
                        new_element.is_subsituition = pick.position > 11
                        new_element.pick_position = pick.position
                        new_element.is_captain = pick.is_captain
                        new_element.is_vice_captain = pick.is_vice_captain
                        gameweek_live_event = gameweek_live_event_dict[element.id]
                        gameweek_minutes_played = gameweek_live_event.stats.minutes
                        gameweek_points = gameweek_live_event.stats.total_points * (
                            pick.multiplier if pick.multiplier > 0 else 1
                        )
                        new_element.gameweek_points = (
                            gameweek_points if gameweek_minutes_played > 0 else None
                        )

                        picks.append(new_element)
            players_gameweek_picks.append(
                PlayerGameweekPicksData(
                    player=player_data,
                    picked_elements=picks,
                    event_transfers=r.entry_history.event_transfers,
                    event_transfers_cost=r.entry_history.event_transfers_cost,
                )
            )

        return players_gameweek_picks

    def clear_gameweek_result_cache(self, gameweek: int, league_id: str):
        return self.dynamodb.delete_item_by_hash_key(
            _construct_cache_hash(league_id, gameweek)
        )

    async def list_league_teams(self):
        bootstrap = await self.fpl_adapter.get_bootstrap()
        return bootstrap.teams
