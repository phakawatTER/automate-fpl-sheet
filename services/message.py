from typing import List
from line import LineBot
from config import Config
from models import PlayerResultData
import math

class GameweekResultMessage:

    @staticmethod
    def build(players:List[PlayerResultData],game_week:int):
        message = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://www.merlinpcbgroup.com/wp-content/uploads/fpl-logo.jpg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {
                "type": "uri",
                "uri": "http://linecorp.com/"
                }
            },
        }
        
        body = {
                "type": "box",
                "layout": "vertical",
                "contents": []
        }
        
        body["contents"].append({
            "type": "text",
            "text": f"GAMEWEEK {game_week} RESULT",
            "weight": "bold",
            "size": "xl"
        })
        
        top3_icons = ["👑","🎉","🌝"]
        
        for i,player in enumerate(players):
            score = math.floor(player.score)
            rank = i+1
            player_name = f"#{rank} {player.name}"
            if i <= 2:
                player_name += f" {top3_icons[i]}"
            body["contents"].append({
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": player_name,
                                "color": "#aaaaaa",
                                "size": "sm",
                                "flex": 3
                            },
                            {
                                "type": "text",
                                "text": f"{score}",
                                "color": "#aaaaaa",
                                "size": "sm",
                                "flex": 1,
                                "weight": "bold",
                                "align": "end"
                            }
                        ]
                    }
                ]
            })
        
        message["body"] = body
        print(message)
        return message
        

class MessageService:
    def __init__(self,config:Config):
        self.bot = LineBot(config=config)
        self.group_id = config.line_group_id
        
    def send_gameweek_result_message(self,game_week:int,players:List[PlayerResultData]):
        message = GameweekResultMessage.build(players,game_week)
        self.bot.send_flex_message(group_id=self.group_id,flex_message=message)
