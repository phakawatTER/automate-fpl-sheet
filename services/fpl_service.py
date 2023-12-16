import sys
import random
import json
from typing import Dict,List,Optional

from tqdm import tqdm
from gspread import Worksheet
from loguru import logger

from adapter import FPLAdapter,GoogleSheet,DynamoDB
from config import Config
from models import PlayerResultData,PlayerRevenue,FPLEventStatus




CACHE_TABLE_NAME = "FPLCacheTable"
# F4
START_SCORE_COL = 6
START_SCORE_ROW = 4

def add_noise(value, noise_factor=0.0000000099):
    noise = random.uniform(0, noise_factor)
    noisy_value = value + noise
    return noisy_value

def is_equal(a:float,b:float,precision=6):
    difference = abs(a - b)
    threshold = 10 ** -precision
    return difference < threshold

def expand_check_dupl_score(players:List[PlayerResultData]):
    player_scores = [p.score for p in players]
    for i,p in enumerate(players):
        for j,score in enumerate(player_scores):
            if i == j:
                continue
            if is_equal(score,p.score):
                p.reward_division += 1
                p.shared_reward_player_ids.append(players[j].player_id)

    return players

def _update_players_reward_from_sheet(
    players:List[PlayerResultData],
    worksheet:Worksheet,
    start_score_row:int,
    current_reward_col:int,
    config:Config,
):
    player_ids = [t[0] for t in  worksheet.get(config.player_ids_range)]
    player_bank_accounts = [t[0] for t in  worksheet.get(config.player_bank_account_range)]
    # update reward of each players
    for i,player_id in enumerate(player_ids):
        bank_account = player_bank_accounts[i]
        for player in players:
            if player.player_id == int(player_id):
                player.bank_account = bank_account
                current_score_row = start_score_row + i
                cv = worksheet.cell(current_score_row,current_reward_col)
                player.reward = int(cv.value)
                player.sheet_row = current_score_row
                break

def _update_players_shared_reward(
    players:List[PlayerResultData],
    worksheet:Worksheet,
    current_reward_col:int
):
    players_with_shared_reward:List[PlayerResultData] = [player for player in players if player.reward_division > 1]
    player_new_reward_map:Dict[int,float] = {}
    for player in players_with_shared_reward:
        sum_reward_amount = 0
        for _player in players:
            if _player.player_id in player.shared_reward_player_ids:
                sum_reward_amount += _player.reward
        new_reward = sum_reward_amount / player.reward_division
        worksheet.update_cell(player.sheet_row,current_reward_col,new_reward)
        player_new_reward_map[player.player_id] = new_reward
        
    for player in players_with_shared_reward:
        player.reward = player_new_reward_map[player.player_id]

def _update_player_score_in_sheet(
    players:List[PlayerResultData],
    worksheet:Worksheet,
    start_score_row:int,
    current_score_col:int,
    config:Config,
):
    player_ids = [t[0] for t in  worksheet.get(config.player_ids_range)]
    for i, player_id in enumerate(player_ids):
        for player in players:
            if player.player_id == int(player_id):
                current_score_row = start_score_row + i
                worksheet.update_cell(current_score_row,current_score_col, player.score)
                break
            
class Service:
    def __init__(self,google_sheet:GoogleSheet,config:Config):
        self.config = config
        self.google_sheet = google_sheet
        self.fpl_adapter = FPLAdapter(league_id=config.league_id,cookies=config.cookies)
        self.dynamodb = DynamoDB(table_name=CACHE_TABLE_NAME)

    def _lookup_gameweek_result_cache(self,game_week:int)-> Optional[List[PlayerResultData]]:
        response = self.dynamodb.get_item_by_hash_key(key=f"gameweek-{game_week}")
        item = response.get("Item")
        if item is None:
            return None

        logger.info(f"cache hit for gameweek {game_week}")

        data = item.get("DATA").get("S")
        players_objs = json.loads(data)
        player_data_dict = dict.fromkeys(PlayerResultData().__dict__.keys())
        players:List[PlayerResultData] = []
        for player_obj in players_objs:
            init_dict = {}
            for key in player_data_dict:
                init_dict[key] = player_obj[key]
            player = PlayerResultData(**init_dict)
            players.append(player)
        return players
    
    def update_gameweek(self,gameweek:int):
        response = self.dynamodb.put_json_item(key="gameweek",data={
            "gameweek": gameweek
        })
        return response

    def _put_cache_item(self,key:str,item:any):
        response = self.dynamodb.put_json_item(key=key,data=item)
        return response

    def update_fpl_table(self,gw:int):
        if not self.is_current_gameweek(gameweek=gw):
            cache = self._lookup_gameweek_result_cache(gw)   
            if cache is not None:
                return cache

        h2h_result = self.fpl_adapter.get_h2h_results(game_week=gw)

        player_score:Dict[int, PlayerResultData] = {}
        results = h2h_result.results

        players:List[PlayerResultData] = []
        for result in results:
            # player 1
            p1_name = result.entry_1_name
            p1_score = add_noise(result.entry_1_points)
            p1_id = result.entry_1_entry
            # player 2
            p2_name = result.entry_2_name
            p2_score = add_noise(result.entry_2_points)
            p2_id = result.entry_2_entry

            if p1_name not in self.config.ignore_players:
                player_score[p1_id] = PlayerResultData(p1_name,p1_id,p1_score)
            if p2_name not in self.config.ignore_players:
                player_score[p2_id] = PlayerResultData(p2_name,p2_id,p2_score)

        for player_id in tqdm(player_score, total=len(player_score), desc="Processing", unit="item",file=sys.stdout):
            player_team = self.fpl_adapter.get_player_team_by_id(player_id,game_week=gw)
            for pick in player_team.picks:
                if pick.is_captain:
                    c = self.fpl_adapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                    player_score[player_id].score += c.total_points / 10000 * pick.multiplier
                    player_score[player_id].captain_points = c.total_points * pick.multiplier
                if pick.is_vice_captain:
                    c = self.fpl_adapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                    player_score[player_id].score += c.total_points / 1000000 * pick.multiplier
                    player_score[player_id].vice_captain_points = c.total_points * pick.multiplier
            player = player_score[player_id]
            players.append(player)
        # Sorting the list of PlayerResultData instances by the 'score' attribute
        players = sorted(players, key=lambda player: player.score, reverse=True)
        players = expand_check_dupl_score(players=players)
        
        worksheet = self.google_sheet.open_worksheet_from_default_sheet(self.config.worksheet_name)
        

        current_score_col = START_SCORE_COL + ( (gw - 1) * 3 )
        current_reward_col = current_score_col + 2
        
        # update score in sheet
        _update_player_score_in_sheet(current_score_col=current_score_col,start_score_row=START_SCORE_ROW,players=players,worksheet=worksheet,config=self.config)
        # update players's reward from sheet           
        _update_players_reward_from_sheet(current_reward_col=current_reward_col,players=players,worksheet=worksheet,start_score_row=START_SCORE_ROW,config=self.config)
        # update player's shared reward (duplicated)
        _update_players_shared_reward(current_reward_col=current_reward_col,players=players,worksheet=worksheet)
            
        player_cache_items = [player.__dict__ for player in players]
        self._put_cache_item(key=f"gameweek-{gw}",item=player_cache_items)
        
        return players

    def list_players_revenues(self):
        standing_result = self.fpl_adapter.get_h2h_league_standing()
        standings = standing_result.standings
        
        worksheet = self.google_sheet.open_worksheet_from_default_sheet(self.config.worksheet_name)
        
        player_ids = [x.value for x in worksheet.range(self.config.player_ids_range)]
        revenue_col = START_SCORE_COL + (37 * 3) + 4
        players:List[PlayerRevenue] = []
        for i,player_id in enumerate(player_ids):
            for standing in standings:
                if standing.entry == int(player_id):
                    sheet_row = START_SCORE_ROW + i
                    cell_value = worksheet.cell(sheet_row,revenue_col).numeric_value
                    player = PlayerRevenue(name=standing.entry_name,revenue=cell_value)
                    players.append(player)
                    
        players = sorted(players, key=lambda player: player.revenue, reverse=True)
            
        
        return players
    
    
    def get_current_gameweek_from_dynamodb(self):
        item = self.dynamodb.get_item_by_hash_key("gameweek")
        print(item)
        data = item.get("Item").get("DATA").get("S")
        gameweek_data = json.loads(data)
        return gameweek_data.get("gameweek")
    
    def get_current_gameweek(self) -> FPLEventStatus:
        result = self.fpl_adapter.get_current_gameweek()
        if len(result.status) == 0:
            raise Exception("gameweek not found")
        gameweek_status = result.status[0]
        
        return gameweek_status
    
    def is_current_gameweek(self,gameweek:int)->bool:
        current_gameweek = self.get_current_gameweek_from_dynamodb()
        return current_gameweek == gameweek
    
    def list_gameweek_fixtures(self,gameweek:int):
        gameweek_fixtures = self.fpl_adapter.list_gameweek_fixtures(gameweek=gameweek)
        return gameweek_fixtures
