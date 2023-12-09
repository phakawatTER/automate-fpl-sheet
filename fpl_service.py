import sys
import random
from typing import Dict,List
from tqdm import tqdm
from loguru import logger
from gspread import Worksheet

from fpl_adapter import FPLAdapter
from sheet import GoogleSheet

LEAGUE_ID = 1592442
IGNORE_PLAYERS = ["AVERAGE","TON"]
PLAYER_IDS_RANGE = "A4:A11"

class PlayerData:
    def __init__(self,name:str,player_id:int,score:float):
        self.name = name
        self.player_id = player_id
        self.score = score
        self.reward_division:int = 1
        self.shared_reward_player_ids = []
        self.reward = 0
        self.sheet_row = -1
        self.captain_points = 0
        self.vice_captain_points = 0
        
        
    def set_score(self,score:float):
        self.score = score
    
    def set_reward_division(self,division:int):
        self.reward_division = division
        
def add_noise(value, noise_factor=0.0000000099):
    noise = random.uniform(0, noise_factor)
    noisy_value = value + noise
    return noisy_value
        
def is_equal(a:float,b:float,precision=6):
    difference = abs(a - b)
    threshold = 10 ** -precision
    return difference < threshold

def expand_check_dupl_score(players:List[PlayerData]):
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
    players:List[PlayerData],
    worksheet:Worksheet,
    start_score_row:int,
    current_reward_col:int
):
    player_ids = [t[0] for t in  worksheet.get(PLAYER_IDS_RANGE)]
    # update reward of each players
    for i,player_id in enumerate(player_ids):
        for player in players:
            if player.player_id == int(player_id) and player.reward_division > 1:
                current_score_row = start_score_row + i
                cv = worksheet.cell(current_score_row,current_reward_col)
                player.reward = int(cv.value)
                player.sheet_row = current_score_row
                break

def _update_players_shared_reward(
    players:List[PlayerData],
    worksheet:Worksheet,
    current_reward_col:int
):
    players_with_shared_reward:List[PlayerData] = [player for player in players if player.reward_division > 1]
    for player in players_with_shared_reward:
        sum_reward_amount = player.reward
        for _player in players:
            if _player.player_id in player.shared_reward_player_ids:
                sum_reward_amount += _player.reward
        new_reward = sum_reward_amount / player.reward_division
        worksheet.update_cell(player.sheet_row,current_reward_col,new_reward)

def _update_player_score_in_sheet(
    players:List[PlayerData],
    worksheet:Worksheet,
    start_score_row:int,
    current_score_col:int
):
    player_ids = [t[0] for t in  worksheet.get(PLAYER_IDS_RANGE)]
    for i, player_id in enumerate(player_ids):
        for player in players:
            if player.player_id == int(player_id):
                current_score_row = start_score_row + i
                worksheet.update_cell(current_score_row,current_score_col, player.score)
                break
        
def update_fpl_table(gw:int,cookies:str):

    fpl_adapter = FPLAdapter(league_id=LEAGUE_ID,cookies=cookies)

    h2h_result = fpl_adapter.get_h2h_results(game_week=gw)

    player_score:Dict[int, PlayerData] = {}
    results = h2h_result.results

    players:List[PlayerData] = []
    for result in results: 
        # player 1
        p1_name = result.entry_1_name
        p1_score = add_noise(result.entry_1_points)
        p1_id = result.entry_1_entry
        # player 2
        p2_name = result.entry_2_name
        p2_score = add_noise(result.entry_2_points)
        p2_id = result.entry_2_entry
        
        if p1_name not in IGNORE_PLAYERS:
            player_score[p1_id] = PlayerData(p1_name,p1_id,p1_score)
        if p2_name not in IGNORE_PLAYERS:
            player_score[p2_id] = PlayerData(p2_name,p2_id,p2_score)

    for player_id in tqdm(player_score, total=len(player_score), desc="Processing", unit="item",file=sys.stdout):
        player_team = fpl_adapter.get_player_team_by_id(player_id,game_week=gw)
        for pick in player_team.picks:
            if pick.is_captain:
                c = fpl_adapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                player_score[player_id].score += c.total_points / 10000
                player_score[player_id].captain_points = c.total_points
            if pick.is_vice_captain:
                c = fpl_adapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                player_score[player_id].score += c.total_points / 1000000
                player_score[player_id].vice_captain_points = c.total_points
        player = player_score[player_id]
        players.append(player)
    # Sorting the list of PlayerData instances by the 'score' attribute
    players = sorted(players, key=lambda player: player.score, reverse=True)
    players = expand_check_dupl_score(players=players)
    for rank,player in enumerate(players,start=0):
        logger.info(f"({rank+1}){player.name}: {player.score} {player.captain_points} {player.vice_captain_points}")

    sheet = GoogleSheet("./service_account.json")
    sheet = sheet.open_sheet_by_url("https://docs.google.com/spreadsheets/d/1eciOdiGItEkml98jVLyXysGMtpMa06hbiTTJ40lztw4/edit#gid=1315457538")
    worksheet = sheet.open_worksheet_from_default_sheet("Sheet3")
    # E4
    start_score_col = 5
    start_score_row = 4

    current_score_col = start_score_col + ( (gw - 1) * 3 )
    current_reward_col = current_score_col + 2

    
    # update score in sheet
    _update_player_score_in_sheet(current_score_col=current_score_col,start_score_row=start_score_row,players=players,worksheet=worksheet)
    # update players's reward from sheet                
    _update_players_reward_from_sheet(current_reward_col=current_reward_col,players=players,worksheet=worksheet,start_score_row=start_score_row)
    # update player's shared reward (duplicated)
    _update_players_shared_reward(current_reward_col=current_reward_col,players=players,worksheet=worksheet)
        
