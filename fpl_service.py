from typing import Dict,List
from fpl_adapter import FPLAdapter
from tqdm import tqdm
import sys
from sheet import GoogleSheet

LEAGUE_ID = 1592442
IGNORE_PLAYERS = ["AVERAGE","TON"]
PLAYER_IDS_RANGE = "A4:A11"

class PlayerData:
    def __init__(self,name:str,player_id:int,score:float):
        self.name = name
        self.player_id = player_id
        self.score = score
        self.sheet_row = None
        
def update_fpl_table(gw:int):
    with open("./cookies.txt","r") as file:
        cookies = file.read()

    fplAdapter = FPLAdapter(league_id=LEAGUE_ID,cookies=cookies)

    h2h_result = fplAdapter.get_h2h_results(game_week=gw)

    player_score:Dict[int, PlayerData] = {}
    results = h2h_result.results

    players:List[PlayerData] = []
    for result in results: 
        # player 1
        p1_name = result.entry_1_name
        p1_score = result.entry_1_points
        p1_id = result.entry_1_entry
        # player 2
        p2_name = result.entry_2_name
        p2_score = result.entry_2_points
        p2_id = result.entry_2_entry
        
        if p1_name not in IGNORE_PLAYERS:
            player_score[p1_id] = PlayerData(p1_name,p1_id,p1_score)
        if p2_name not in IGNORE_PLAYERS:
            player_score[p2_id] = PlayerData(p2_name,p2_id,p2_score)

    for player_id in tqdm(player_score, total=len(player_score), desc="Processing", unit="item",file=sys.stdout):
        player_team = fplAdapter.get_player_team_by_id(player_id,game_week=gw)
        for pick in player_team.picks:
            if pick.is_captain:
                c = fplAdapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                player_score[player_id].score += c.total_points / 100
            if pick.is_vice_captain:
                c = fplAdapter.get_player_gameweek_info(game_week=gw,player_id=pick.element)
                player_score[player_id].score += c.total_points / 1000
        player = player_score[player_id]
        players.append(player)
    # Sorting the list of PlayerData instances by the 'score' attribute
    sorted_players = sorted(players, key=lambda player: player.score, reverse=True)
    for rank,player in enumerate(sorted_players,start=0):
        print(f"({rank+1}){player.name}: {player.score}")

    sheet = GoogleSheet("./service_account.json")
    sheet = sheet.open_sheet_by_url("https://docs.google.com/spreadsheets/d/1eciOdiGItEkml98jVLyXysGMtpMa06hbiTTJ40lztw4/edit#gid=1315457538")
    worksheet = sheet.open_worksheet_from_default_sheet("Sheet3")
    # E4
    start_score_col = 5
    start_score_row = 4

    current_score_col = start_score_col + ( (gw - 1) * 3 )

    player_ids = [t[0] for t in  worksheet.get("A4:A11")]
    for i, player_id in enumerate(player_ids):
        for player in players:
            if player.player_id == int(player_id):
                current_score_row = start_score_row + i
                worksheet.update_cell(current_score_row,current_score_col, player.score)
                break

