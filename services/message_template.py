import math
from typing import List
from models import PlayerResultData,PlayerRevenue

COLORS = {
    "SUCCESS": "#62d271",
    "DANGER": "#EF4040",
    "NORMAL": "#aaaaaa"
}

class _CommonMessage:
    def __init__(self,sheet_url:str):
        self.container = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://www.merlinpcbgroup.com/wp-content/uploads/fpl-logo.jpg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {
                    "type": "uri",
                    "uri": sheet_url
                }
            },
        }
        
    def _get_container(self):
        return self.container
    
class GameweekReminderMessage(_CommonMessage):
    def __init__(self,sheet_url:str,game_week:int):
        super().__init__(sheet_url=sheet_url)
        self.game_week = game_week
    def build(self):
        message = self._get_container()
        body = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"GAMEWEEK {self.game_week} IS COMING",
                        "weight": "bold",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": "อย่าลืมจัดตัวกันนะจ๊ะ",
                        "weight": "regular",
                        "margin": "xl",
                        "size": "md"
                    },
                ]
        }
        message["body"] = body
        
        return message

class GameweekResultMessage(_CommonMessage):
    def __init__(self,players:List[PlayerResultData],game_week:int,sheet_url:str):
        super().__init__(sheet_url=sheet_url)
        self.players = players
        self.game_week = game_week
        
    def build(self):
        message = self._get_container()
        
        body = {
                "type": "box",
                "layout": "vertical",
                "contents": []
        }
        
        body["contents"].append({
            "type": "text",
            "text": f"GAMEWEEK {self.game_week} RESULT",
            "weight": "bold",
            "size": "xl"
        })
        
        top3_icons = ["👑","🎉","🌝"]
        
        for i,player in enumerate(self.players):
            score = math.floor(player.score)
            rank = i+1
            player_name = f"#{rank} {player.name}"
            is_top_3 = i <= 2
            if is_top_3:
                player_name += f" {top3_icons[i]}"
            else:
                player_name += " 💩"
            content = {
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
                                "color": COLORS["NORMAL"],
                                "size": "sm",
                                "flex": 5,
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": f"{score}",
                                "color": COLORS["NORMAL"],
                                "size": "sm",
                                "flex": 1,
                                "weight": "bold",
                                "align": "end"
                            }
                        ]
                    }
                ]
            }
            if is_top_3:
                bank_account_box = {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": player.bank_account,
                                "color": COLORS["NORMAL"],
                                "size": "xs",
                                "flex": 5
                            },
                            {
                                "type": "text",
                                "text": f"+{player.reward}฿",
                                "color": COLORS["SUCCESS"],
                                "weight": "bold",
                                "size": "xs",
                                "flex": 1,
                                "align": "end",
                            }
                        ]
                    }
                content["contents"].append(bank_account_box)
            else:
                bank_account_box = {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{player.reward}฿",
                                "color": COLORS["DANGER"],
                                "weight": "bold",
                                "size": "xs",
                                "flex": 1,
                                "align": "end",
                            }
                        ]
                    }
                content["contents"].append(bank_account_box)
                
            
            # add separator
            content["contents"].append({
                "type": "separator"
            })
            
            body["contents"].append(content)
        
        message["body"] = body

        return message

class RevenueMessage(_CommonMessage):
    def __init__(self,sheet_url:str,players_revenues:List[PlayerRevenue]):
        super().__init__(sheet_url=sheet_url)
        self.players_revenues = players_revenues
        
    def build(self):
        message = self._get_container()
        
        body = {
                "type": "box",
                "layout": "vertical",
                "contents": []
        }
        
        body["contents"].append({
            "type": "text",
            "text": "PLAYERS TOTAL REVENUE",
            "weight": "bold",
            "size": "md"
        })
        
        
        message["body"] = body
        
        top3_icons = ["👑","🎉","🌝"]
        
        for i,player in enumerate(self.players_revenues):
            revenue = player.revenue
            name = player.name
            is_top_3 = i <= 2
            if is_top_3:
                name += f" {top3_icons[i]}"
            
            content = {
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
                                "text": name,
                                "color": COLORS["NORMAL"],
                                "size": "sm",
                                "flex": 5,
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": f"{revenue}฿",
                                "color": COLORS["SUCCESS"] if revenue > 0  else \
                                            COLORS["DANGER"] if revenue < 0 \
                                                else COLORS["NORMAL"],
                                "size": "sm",
                                "flex": 1,
                                "weight": "bold",
                                "align": "end"
                            }
                        ]
                    },
                    {
                        "type": "separator"
                    },
                ]
            }
            
            
            body["contents"].append(content)
        
        return message
