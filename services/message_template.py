import math
from typing import List, Optional
from models import PlayerGameweekData, PlayerRevenue, FPLEventStatusResponse


class Color:
    TOPIC = "#ffffff"
    SUCCESS = "#62d271"
    DANGER = "#EF4040"
    NORMAL = "#aaaaaa"


EMOJI_NUMBER_MAP = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}


class _CommonMessage:
    def __init__(self, sheet_url: str):
        self.container = {
            "type": "bubble",
            "size": "giga",
            "hero": {
                "type": "image",
                "url": "https://thefirmsport.files.wordpress.com/2021/04/fpl_statement_graphic.png",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": sheet_url},
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "backgroundColor": "#393646",
            },
        }

    def _get_container(self):
        return self.container


class GameweekReminderMessage(_CommonMessage):
    def __init__(self, sheet_url: str, gameweek: int):
        super().__init__(sheet_url=sheet_url)
        self.gameweek = gameweek

    def build(self):
        message = self._get_container()

        message["body"]["contents"] = [
            {
                "type": "text",
                "text": f"GAMEWEEK {self.gameweek} IS COMING",
                "weight": "bold",
                "size": "xxl",
                "color": Color.TOPIC,
            },
            {
                "type": "text",
                "text": "อย่าลืมจัดตัวกันนะจ๊ะ",
                "weight": "regular",
                "margin": "xl",
                "size": "md",
                "color": Color.NORMAL,
            },
        ]

        return message


class GameweekResultCarouselMessage:
    def __init__(self, messages):
        self.messages = messages

    def build(self):
        message = {
            "type": "carousel",
            "contents": self.messages,
        }
        return message


class GameweekResultMessage(_CommonMessage):
    def __init__(
        self,
        players: List[PlayerGameweekData],
        gameweek: int,
        sheet_url: str,
        event_status: Optional[FPLEventStatusResponse] = None,
    ):
        super().__init__(sheet_url=sheet_url)
        self.players = players
        self.gameweek = gameweek
        self.event_status = event_status

    def build(self):
        message = self._get_container()

        message["body"]["contents"].append(
            {
                "type": "text",
                "text": f"GAMEWEEK {self.gameweek}",
                "weight": "bold",
                "size": "xxl",
                "color": Color.TOPIC,
            },
        )

        if self.event_status is not None:
            message["body"]["contents"].append(
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Status: ",
                            "color": Color.TOPIC,
                            "weight": "bold",
                            "size": "xl",
                            "flex": 0,
                        },
                        {
                            "type": "text",
                            "text": self.event_status.leagues,
                            "color": Color.SUCCESS,
                            "size": "xl",
                            "margin": "sm",
                            "flex": 0,
                        },
                    ],
                },
            )

        top3_icons = ["👑", "🎉", "🌝"]

        for i, player in enumerate(self.players):
            point = math.floor(player.points)
            rank_str = str(i + 1)
            rank = ""
            for numb in rank_str:
                rank += EMOJI_NUMBER_MAP[numb]
            player_name = f"{rank} {player.name}"
            is_top_3 = i <= 2
            if is_top_3:
                player_name += f" {top3_icons[i]}"
            else:
                player_name += " 💩"
            content = {
                "type": "box",
                "layout": "vertical",
                "margin": "xl",
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
                                "color": Color.NORMAL,
                                "size": "md",
                                "flex": 5,
                                "weight": "bold",
                            },
                            {
                                "type": "text",
                                "text": f"{point}",
                                "color": Color.NORMAL,
                                "size": "md",
                                "flex": 1,
                                "weight": "bold",
                                "align": "end",
                            },
                        ],
                    }
                ],
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
                            "color": Color.NORMAL,
                            "size": "sm",
                            "flex": 5,
                        },
                        {
                            "type": "text",
                            "text": f"+{player.reward}฿",
                            "color": Color.SUCCESS,
                            "weight": "bold",
                            "size": "sm",
                            "flex": 1,
                            "align": "end",
                        },
                    ],
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
                            "color": Color.DANGER,
                            "weight": "bold",
                            "size": "sm",
                            "flex": 1,
                            "align": "end",
                        }
                    ],
                }
                content["contents"].append(bank_account_box)

            if i < len(self.players) - 1:
                # add separator
                content["contents"].append({"type": "separator"})

            message["body"]["contents"].append(content)

        return message


class RevenueMessage(_CommonMessage):
    def __init__(self, sheet_url: str, players_revenues: List[PlayerRevenue]):
        super().__init__(sheet_url=sheet_url)
        self.players_revenues = players_revenues

    def build(self):
        message = self._get_container()

        message["body"]["contents"].append(
            {
                "type": "text",
                "text": "PLAYERS TOTAL REVENUE",
                "weight": "bold",
                "size": "xxl",
                "color": Color.TOPIC,
            }
        )

        top3_icons = ["👑", "🎉", "🌝"]

        for i, player in enumerate(self.players_revenues):
            revenue = player.revenue
            name = player.name
            is_top_3 = i <= 2
            if is_top_3:
                name += f" {top3_icons[i]}"
            rank_str = str(i + 1)
            rank = ""
            for numb in rank_str:
                rank += EMOJI_NUMBER_MAP[numb]

            content = {
                "type": "box",
                "layout": "vertical",
                "margin": "xl",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{rank} {name}",
                                "color": Color.NORMAL,
                                "size": "md",
                                "flex": 5,
                                "weight": "bold",
                            },
                            {
                                "type": "text",
                                "text": f"{revenue}฿",
                                "color": Color.SUCCESS
                                if revenue > 0
                                else Color.DANGER
                                if revenue < 0
                                else Color.NORMAL,
                                "size": "md",
                                "flex": 1,
                                "weight": "bold",
                                "align": "end",
                            },
                        ],
                    },
                ],
            }

            if i < len(self.players_revenues) - 1:
                content["contents"].append({"type": "separator"})

            message["body"]["contents"].append(content)

        return message
