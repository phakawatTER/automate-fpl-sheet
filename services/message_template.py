import math
from typing import List, Optional, Dict
from models import (
    PlayerGameweekData,
    PlayerRevenue,
    FPLEventStatusResponse,
    PlayerGameweekPicksData,
    PlayerPosition,
    BootstrapElement,
)
from adapter import FPLAdapter


def _get_chance_of_playing_level(chance: int) -> int:
    level = 0
    if chance == 100 or chance is None:
        level = 0
    elif 50 < chance <= 75:
        level = 1
    elif 25 < chance <= 50:
        level = 2
    elif 0 < chance <= 25:
        level = 3
    else:
        level = 4
    return level


class Icon:
    INFO = "https://cdn-icons-png.flaticon.com/128/151/151776.png"
    WARNING = "https://cdn-icons-png.flaticon.com/128/1008/1008769.png"
    WARNING2 = "https://cdn-icons-png.flaticon.com/128/1680/1680012.png"
    DANGER = "https://cdn-icons-png.flaticon.com/128/564/564619.png"


class Color:
    TOPIC = "#ffffff"
    SUCCESS = "#62d271"
    DANGER = "#EF4040"
    NORMAL = "#aaaaaa"
    WARNING = "#FFE65B"
    WARNING2 = "#FFAB1B"


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

COMMON_FOOTER = {
    "type": "box",
    "layout": "vertical",
    "action": {"type": "uri", "uri": "https://github.com/phakawatTER"},
    "contents": [
        {
            "type": "box",
            "layout": "horizontal",
            "justifyContent": "center",
            "margin": "md",
            "contents": [
                {
                    "type": "image",
                    "url": "https://cdn-icons-png.flaticon.com/512/25/25231.png",
                    "size": "20px",
                    "flex": 0,
                },
                {
                    "type": "text",
                    "text": "phakawatTER 🚀",
                    "size": "sm",
                    "margin": "sm",
                    "flex": 0,
                },
            ],
        },
    ],
}


class _CommonHero:
    BACKGROUND_COLOR = "#393646"

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
                "backgroundColor": _CommonHero.BACKGROUND_COLOR,
            },
            "footer": COMMON_FOOTER,
        }

    def _get_container(self):
        return self.container


class GameweekReminderMessage(_CommonHero):
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


class CarouselMessage:
    def __init__(self, messages):
        self.messages = messages

    def build(self):
        message = {
            "type": "carousel",
            "contents": self.messages,
        }
        return message


class GameweekResultMessage(_CommonHero):
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


class RevenueMessage(_CommonHero):
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


class PlayerGameweekPickMessage:
    def __init__(self, gameweek: int, player_data: PlayerGameweekPicksData):
        self.__player_data = player_data
        self.__gameweek = gameweek

    def build(self):
        player = self.__player_data.player
        picks = self.__player_data.picked_elements
        container = {
            "type": "bubble",
            "size": "giga",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "backgroundColor": "#393646",
            },
        }

        contents: List[Dict] = container["body"]["contents"]

        contents.append(
            {
                "type": "text",
                "color": Color.TOPIC,
                "weight": "bold",
                "size": "xxl",
                "text": f"Gameweek {self.__gameweek}",
            }
        )
        contents.append(
            {
                "type": "text",
                "color": Color.TOPIC,
                "weight": "bold",
                "size": "xl",
                "text": player.team_name,
                "margin": "xl",
            }
        )

        # add separator
        contents.append({"type": "separator", "margin": "xxl"})

        for i, pick in enumerate(reversed(picks)):
            image_url = FPLAdapter.get_element_image_url(element_code=pick.code)
            content = {
                "type": "box",
                "layout": "horizontal",
                "margin": "xl" if i == 0 else "sm",
                "contents": [
                    {"type": "image", "url": image_url, "size": "xxs", "flex": 0},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xl",
                        "contents": [
                            {
                                "type": "text",
                                "size": "md",
                                "color": Color.NORMAL,
                                "text": f"{pick.first_name} {pick.second_name}",
                                "flex": 0,
                                "align": "start",
                            },
                            {
                                "type": "text",
                                "size": "xs",
                                "color": Color.NORMAL,
                                "text": pick.news
                                if pick.news is not None and pick.news != ""
                                else "-",
                                "flex": 0,
                                "align": "start",
                            },
                        ],
                    },
                ],
            }
            contents.append(content)
            if i < len(picks) - 1:
                contents.append({"type": "separator"})

        return container


class PlayerGameweekPickMessageV2:
    def __init__(self, gameweek: int, player_picks: PlayerGameweekPicksData):
        self.player_picks = player_picks
        self.gameweek = gameweek

    def build(self):
        container = {
            "type": "bubble",
            "size": "giga",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "size": "xxl",
                        "text": f"Gameweek {self.gameweek}",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "size": "md",
                        "text": self.player_picks.player.team_name,
                        "color": Color.NORMAL,
                    },
                ],
            },
            "footer": COMMON_FOOTER,
        }
        container_contents: List[dict] = container["body"]["contents"]

        position_map: Dict[PlayerPosition, List[BootstrapElement]] = {
            PlayerPosition.GOAL_KEEPER: [],
            PlayerPosition.DEFENDER: [],
            PlayerPosition.MIDFIELDER: [],
            PlayerPosition.FORWARD: [],
        }

        subs: List[BootstrapElement] = []
        for p in self.player_picks.picked_elements:
            if not p.is_subsituition:
                position_map[p.position].append(p)
            else:
                subs.append(p)

        # render by each position on field
        for _, players in position_map.items():
            content = self.__construct_player_position_section(players)
            container_contents.append(content)
        # render subs
        subs_topic = {
            "type": "box",
            "layout": "vertical",
            "margin": "xxl",
            "contents": [
                {
                    "type": "text",
                    "text": "Subsitutions",
                    "size": "md",
                    "color": Color.NORMAL,
                },
            ],
        }
        separator = {"type": "separator"}
        container_contents.append(subs_topic)
        container_contents.append(separator)
        container_contents.append(self.__construct_player_position_section(subs))

        return container

    def __construct_player_position_section(self, players: List[BootstrapElement]):
        content = {
            "type": "box",
            "margin": "xl",
            "layout": "horizontal",
            "justifyContent": "center",
            "contents": [],
        }
        contents = content["contents"]
        for p in players:
            background_color = Color.SUCCESS
            level = _get_chance_of_playing_level(p.chance_of_playing_this_round)
            colors = [
                Color.SUCCESS,
                Color.WARNING,
                Color.WARNING2,
                Color.WARNING2,
                Color.DANGER,
            ]
            background_color = colors[level]

            icon_urls = [
                Icon.INFO,
                Icon.WARNING,
                Icon.WARNING2,
                Icon.WARNING2,
                Icon.DANGER,
            ]
            icon_url = icon_urls[level]

            c = {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "maxWidth": "85px",
                "contents": [
                    {
                        "type": "image",
                        "size": "xs",
                        "url": FPLAdapter.get_element_image_url(p.code),
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "paddingAll": "sm",
                        "backgroundColor": background_color,
                        "cornerRadius": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": p.web_name,
                                "size": "xxs",
                                "align": "center",
                                "color": "#FFFFFF",
                            }
                        ],
                    },
                ],
            }

            if level > 0:
                c["contents"].append(
                    {
                        "type": "image",
                        "url": icon_url,
                        "position": "absolute",
                        "size": "15px",
                        "offsetEnd": "0px",
                    },
                )
            if p.is_captain or p.is_vice_captain:
                c["contents"].append(
                    {
                        "type": "box",
                        "layout": "vertical",
                        "position": "absolute",
                        "offsetEnd": "0px",
                        "offsetTop": "0px" if level == 0 else "20px",
                        "backgroundColor": "#000000",
                        "cornerRadius": "xxl",
                        "width": "17px",
                        "height": "17px",
                        "justifyContent": "center",
                        "contents": [
                            {
                                "type": "text",
                                "align": "center",
                                "text": "C" if p.is_captain else "V",
                                "color": Color.TOPIC,
                                "size": "xxs",
                                "weight": "bold",
                            }
                        ],
                    }
                )
            contents.append(c)

        return content


class BotInstructionMessage(_CommonHero):
    def __init__(self, sheet_url: str, commands_map_list: List[tuple[str]]):
        super().__init__(sheet_url=sheet_url)
        self.commands_map_list = commands_map_list

    def build(self):
        message = self.container["body"]["contents"]
        message.append(
            {
                "type": "text",
                "text": "🚀Luka Bot CMD Instructions",
                "size": "xl",
                "color": Color.TOPIC,
                "weight": "bold",
            }
        )
        info = "These are the available command patterns where '(d+)' represents a positive integer. Please note that the specified integer(s) must be within the range of possible gameweeks, which is from 1 to 38."
        message.append(
            {
                "type": "text",
                "margin": "md",
                "wrap": True,
                "text": info,
                "color": Color.NORMAL,
            }
        )
        message.append(
            {
                "type": "separator",
                "margin": "xl",
            }
        )

        for desc, pattern in self.commands_map_list:
            m = {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{desc}:",
                        "weight": "bold",
                        "flex": 0,
                        "color": Color.TOPIC,
                    },
                    {
                        "type": "text",
                        "wrap": True,
                        "text": " " + pattern,
                        "flex": 0,
                        "color": Color.NORMAL,
                    },
                ],
            }
            message.append(m)

        return self.container
