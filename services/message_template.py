import math
from datetime import datetime
from typing import List, Optional, Dict
from models import (
    PlayerGameweekData,
    PlayerRevenue,
    FPLEventStatusResponse,
    PlayerGameweekPicksData,
    PlayerPosition,
    BootstrapElement,
    FPLMatchFixture,
    BootstrapTeam,
)
from adapter import FPLAdapter
from util import TIMEZONE


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


BACKGROUND_COLOR = "#37003C"
FPL_TEXT_COLOR = "#37003C"
FPL_PRIMARY_COLOR = "#00FF87"
FPL_SECONDARY_COLOR = "#02EFFF"
FPL_TERTIARY_COLOR = "#FF2882"

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


class _CommonMessageTemplate:
    def __init__(self):
        self.container = {
            "type": "bubble",
            "size": "giga",
            "hero": {
                "type": "image",
                "url": "https://thefirmsport.files.wordpress.com/2021/04/fpl_statement_graphic.png",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "backgroundColor": BACKGROUND_COLOR,
            },
            "footer": COMMON_FOOTER,
        }

    def _get_container(self):
        return self.container


class GameweekReminderMessage(_CommonMessageTemplate):
    def __init__(self, gameweek: int):
        super().__init__()
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


class GameweekResultMessage(_CommonMessageTemplate):
    def __init__(
        self,
        players: List[PlayerGameweekData],
        gameweek: int,
        event_status: Optional[FPLEventStatusResponse] = None,
    ):
        super().__init__()
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

        if self.event_status is not None and self.event_status.leagues != "":
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
            player_name = f"{rank} {player.team_name}"
            is_top_3 = i <= 2
            if is_top_3:
                player_name += f" {top3_icons[i]}"
            else:
                player_name += " 💩"
            subsitution_cost = (
                f" ({player.subsitution_cost})" if player.subsitution_cost < 0 else ""
            )
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
                                "text": f"{point}{subsitution_cost}",
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
                            "text": (
                                player.bank_account
                                if player.bank_account is not None
                                and player.bank_account != ""
                                else player.name
                            ),
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


class RevenueMessage(_CommonMessageTemplate):
    def __init__(self, players_revenues: List[PlayerRevenue]):
        super().__init__()
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
            name = player.team_name
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
                                "color": (
                                    Color.SUCCESS
                                    if revenue > 0
                                    else Color.DANGER if revenue < 0 else Color.NORMAL
                                ),
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
                                "text": (
                                    pick.news
                                    if pick.news is not None and pick.news != ""
                                    else "-"
                                ),
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

    def __create_background(self):
        background_url = "https://cdn5.vectorstock.com/i/1000x1000/61/29/football-soccer-field-aerial-view-vector-6886129.jpg"
        contents = [
            # top
            {
                "type": "image",
                "url": background_url,
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "1:3",
                "position": "absolute",
                "align": "start",
                "gravity": "top",
                "offsetStart": "0px",
                "offsetTop": "0px",
            },
            {
                "type": "image",
                "url": background_url,
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "1:3",
                "position": "absolute",
                "align": "start",
                "gravity": "top",
                "offsetEnd": "0px",
                "offsetTop": "0px",
            },
            {
                "type": "image",
                "url": background_url,
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "1:3",
                "position": "absolute",
                "align": "start",
                "gravity": "top",
                "offsetEnd": "15px",
                "offsetTop": "0px",
            },
        ]
        return contents

    def __construct_header(self):
        total_points = 0
        transfer_cost = self.player_picks.event_transfers_cost
        transfer_count = self.player_picks.event_transfers
        for p in self.player_picks.picked_elements:
            if not p.is_subsituition:
                total_points += (
                    p.gameweek_points if p.gameweek_points is not None else 0
                )
        total_points = total_points - transfer_cost
        return {
            "type": "box",
            "layout": "horizontal",
            "background": {
                "type": "linearGradient",
                "angle": "90deg",
                "startColor": FPL_PRIMARY_COLOR,
                "endColor": FPL_SECONDARY_COLOR,
            },
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 1,
                    "justifyContent": "flex-start",
                    "contents": [
                        {
                            "type": "image",
                            "url": "https://www.premierleague.com/resources/rebrand/v7.129.2/i/elements/pl-main-logo.png",
                            "size": "xs",
                        },
                    ],
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 4,
                    "contents": [
                        {
                            "type": "text",
                            "size": "xl",
                            "text": f"Gameweek {self.gameweek}",
                            "weight": "bold",
                            "color": FPL_TEXT_COLOR,
                        },
                        {
                            "type": "text",
                            "size": "md",
                            "text": self.player_picks.player.team_name,
                            "color": FPL_TEXT_COLOR,
                        },
                    ],
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 2,
                    "justifyContent": "center",
                    "contents": [
                        {
                            "type": "text",
                            "align": "end",
                            "text": "Final Points",
                            "size": "xxs",
                            "color": FPL_TEXT_COLOR,
                        },
                        {
                            "type": "text",
                            "align": "end",
                            "text": f"{total_points}",
                            "size": "xxl",
                            "weight": "bold",
                            "color": (
                                FPL_TEXT_COLOR if total_points >= 0 else Color.DANGER
                            ),
                        },
                        {
                            "type": "text",
                            "align": "end",
                            "text": "Transfers",
                            "size": "xxs",
                            "color": FPL_TEXT_COLOR,
                        },
                        {
                            "type": "text",
                            "align": "end",
                            "text": f"{transfer_count} ({-transfer_cost})",
                            "size": "md",
                            "color": (
                                FPL_TEXT_COLOR if total_points >= 0 else Color.DANGER
                            ),
                        },
                    ],
                },
            ],
        }

    def build(self):
        container = {
            "type": "bubble",
            "size": "giga",
            "header": self.__construct_header(),
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": BACKGROUND_COLOR,
                "contents": [
                    *self.__create_background(),
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
                    "weight": "bold",
                    "size": "md",
                    "color": Color.TOPIC,
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
            "backgroundColor": "#ff000000",
            "contents": [],
        }
        contents = content["contents"]
        for p in players:
            level = _get_chance_of_playing_level(p.chance_of_playing_this_round)
            colors = [
                # Color.SUCCESS,
                "#37003C",
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
                "position": "relative",
                "cornerRadius": "md",
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
                        "contents": [
                            {
                                "type": "text",
                                "text": p.web_name,
                                "size": "xxs",
                                "align": "center",
                                "color": "#FFFFFF" if level == 0 else "#000000",
                            }
                        ],
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "justifyContent": "center",
                        "backgroundColor": "#FFFFFFAA",
                        "contents": [
                            {
                                "type": "text",
                                "text": (
                                    f"{p.gameweek_points}"
                                    if p.gameweek_points is not None
                                    else "-"
                                ),
                                "weight": "bold",
                                "size": "xs",
                                "align": "center",
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


class BotInstructionMessage(_CommonMessageTemplate):
    def __init__(self, commands_map_list: List[tuple[str]], page: int = 1):
        super().__init__()
        self.commands_map_list = commands_map_list
        self.page = page

    def build(self):
        message = self.container["body"]["contents"]
        if self.page == 1:
            message.append(
                {
                    "type": "text",
                    "text": "🚀Bot Luka CMD Instructions",
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
                    "color": Color.TOPIC,
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
                "margin": "xl",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{desc}:",
                        "wrap": True,
                        "weight": "bold",
                        "flex": 0,
                        "color": Color.TOPIC,
                    },
                    {
                        "type": "text",
                        "wrap": True,
                        "text": "🤖 " + pattern,
                        "flex": 0,
                        "color": Color.SUCCESS,
                    },
                ],
            }
            message.append(m)

        return self.container


class GameweekFixtures(_CommonMessageTemplate):
    def __init__(self, gameweek: int, fixtures: List[FPLMatchFixture]):
        super().__init__()
        self.gameweek = gameweek
        self.fixtures = fixtures

    def build(self):
        container = self._get_container()
        body_contents = container["body"]["contents"]
        body_contents.append(
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"Gameweek {self.gameweek}",
                        "weight": "bold",
                        "color": Color.TOPIC,
                        "size": "xxl",
                    }
                ],
            }
        )
        group: Dict[str, List[FPLMatchFixture]] = {}

        for fixture in self.fixtures:
            kickoff_time = fixture.kickoff_time.astimezone(TIMEZONE)
            key = kickoff_time.strftime("%Y-%m-%d")
            if key not in group:
                group[key] = []
            group[key].append(fixture)

        for _, fixtures in group.items():
            body_contents.append(self.__build_date_box(fixtures[0].kickoff_time))
            for fixture in fixtures:
                body_contents.append(self.__build_fixture_box(fixture))

        return self.container

    def __build_date_box(self, dt: datetime):
        kickoff_date = dt.astimezone(TIMEZONE).strftime("%A %d %B %Y")
        return {
            "type": "box",
            "layout": "vertical",
            "cornerRadius": "xl",
            "justifyContent": "flex-end",
            "height": "30px",
            "flex": 0,
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "background": {
                        "type": "linearGradient",
                        "angle": "90deg",
                        "startColor": FPL_PRIMARY_COLOR,
                        "endColor": FPL_SECONDARY_COLOR,
                    },
                    "contents": [
                        {
                            "type": "text",
                            "color": FPL_TEXT_COLOR,
                            "align": "center",
                            "text": kickoff_date,
                        },
                    ],
                }
            ],
        }

    def __build_fixture_box(self, fixture: FPLMatchFixture):
        return {
            "type": "box",
            "layout": "horizontal",
            "justifyContent": "center",
            "margin": "xl",
            "contents": [
                self.__build_team_box(team=fixture.team_h_data, is_team_a=False),
                self.__build_score_box(fixture=fixture),
                self.__build_team_box(team=fixture.team_a_data, is_team_a=True),
            ],
        }

    def __build_score_box(self, fixture: FPLMatchFixture):
        is_played = fixture.minutes > 0
        kickoff_time = fixture.kickoff_time.astimezone(TIMEZONE).strftime("%H:%M")
        return {
            "type": "box",
            "cornerRadius": "sm",
            "flex": 0,
            "backgroundColor": FPL_TERTIARY_COLOR if is_played else Color.TOPIC,
            "layout": "horizontal",
            "alignItems": "center",
            "width": "60px",
            "justifyContent": "space-around",
            "margin": "md",
            "contents": (
                [
                    {
                        "type": "text",
                        "flex": 0,
                        "weight": "bold",
                        "size": "md",
                        "text": f"{fixture.team_h_score}",
                        "color": Color.TOPIC if is_played else FPL_TEXT_COLOR,
                    },
                    {
                        "type": "text",
                        "flex": 0,
                        "size": "md",
                        "text": "|",
                        "color": Color.TOPIC if is_played else FPL_TEXT_COLOR,
                    },
                    {
                        "type": "text",
                        "flex": 0,
                        "weight": "bold",
                        "size": "md",
                        "text": f"{fixture.team_a_score}",
                        "color": Color.TOPIC if is_played else FPL_TEXT_COLOR,
                    },
                ]
                if is_played
                else [
                    {
                        "type": "text",
                        "flex": 0,
                        "size": "xs",
                        "text": kickoff_time,
                    },
                ]
            ),
        }

    def __build_team_box(self, team: BootstrapTeam, is_team_a: bool = False):
        badge_url = FPLAdapter.get_team_badge_image_url(team.code)
        contents = [
            {
                "type": "text",
                "flex": 0,
                "text": team.name,
                "color": Color.TOPIC,
                "size": "sm",
                "margin": "sm",
            },
            {
                "type": "image",
                "flex": 0,
                "url": badge_url,
                "size": "35px",
                "gravity": "center",
                "margin": "sm",
            },
        ]
        if is_team_a:
            contents.reverse()
        return {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "justifyContent": "flex-end" if not is_team_a else "flex-start",
            "contents": contents,
        }
