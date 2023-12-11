from typing import List
from line import LineBot
from config import Config
from models import PlayerResultData,PlayerRevenue
from .message_template import GameweekResultMessage,RevenueMessage

        

class MessageService:
    def __init__(self,config:Config):
        self.bot = LineBot(config=config)
        self.group_id = config.line_group_id
        self.sheet_url = config.sheet_url
        
    def send_text_message(self,text:str):
        self.bot.send_text_message(self.group_id,text=text)
        
    def send_gameweek_result_message(self,game_week:int,players:List[PlayerResultData]):
        message = GameweekResultMessage(
            game_week=game_week,
            players=players,
            sheet_url=self.sheet_url
        )
        
        self.bot.send_flex_message(group_id=self.group_id,flex_message=message.build(),alt_text=f"FPL Gameweek {game_week} Result")
        
    def send_playeres_revenue_summary(self,players_revenues:List[PlayerRevenue]):
        message = RevenueMessage(
            players_revenues=players_revenues,
            sheet_url=self.sheet_url,
        )
        
        self.bot.send_flex_message(self.group_id,flex_message=message.build(),alt_text="FPL Players Revenues")
