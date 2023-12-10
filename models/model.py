from typing import List

class PlayerData:
    def __init__(self,name:str,player_id:int,score:float):
        self.name:str = name
        self.player_id:int = player_id
        self.score:float = score
        self.reward_division:int = 1
        self.shared_reward_player_ids:List[int] = []
        self.reward:int = 0
        self.sheet_row:int = -1
        self.captain_points:int = 0
        self.vice_captain_points:int = 0
        
        
    def set_score(self,score:float):
        self.score = score
    
    def set_reward_division(self,division:int):
        self.reward_division = division
