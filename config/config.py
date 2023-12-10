import json
from typing import List

class Config:
    def __init__(self,path_to_config:str):
        with open(path_to_config,"r",encoding="utf8") as file:
            config_data:dict = json.load(file)
        self.league_id:int = config_data.get("league_id")
        self.cookies:str = config_data.get("cookies")
        self.player_ids_range:str = config_data.get("player_ids_range")
        self.ignore_players:List[str] = config_data.get("ignore_players")
        self.sheet_url:str = config_data.get("sheet_url")
        self.line_channel_access_token:str = config_data.get("line_channel_access_token")
        self.line_channel_id:str = config_data.get("line_channel_id")
        self.line_channel_secret:str = config_data.get("line_channel_secret")
        self.line_group_id:str = config_data.get("line_group_id")
        
    @staticmethod
    def initialize(path_to_config:str):
        return Config(path_to_config)
    
    def get_config(self):
        return {
            "league_id": self.league_id,
            "cookies": self.cookies,
            "player_ids_range": self.player_ids_range,
            "ignore_players": self.ignore_players
        }
