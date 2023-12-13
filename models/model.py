from typing import List

class PlayerData:
    def __init__(self,
                 name:str="",
                 player_id:int=0,
                 score:float=0,
                 reward_division:int=1,
                 shared_reward_player_ids:List[int]=[],
                 reward:float=0,
                 sheet_row:int=-1,
                 captain_points:int=0,
                 vice_captain_points:int=0,
                 bank_account:str="",
):
        self.name:str = name
        self.player_id:int = player_id
        self.score:float = score
        self.reward_division:int = reward_division
        self.shared_reward_player_ids:List[int] = shared_reward_player_ids
        self.reward:int = reward
        self.sheet_row:int =  sheet_row
        self.captain_points:int = captain_points
        self.vice_captain_points:int = vice_captain_points
        self.bank_account:str =  bank_account


class PlayerRevenue:
    def __init__(self,name:str,revenue:float):
        self.name = name
        self.revenue = revenue
