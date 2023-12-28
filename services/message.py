import json
from typing import List, Optional
from line import LineBot
import models
from .message_template import (
    GameweekResultMessage,
    RevenueMessage,
    GameweekReminderMessage,
    CarouselMessage,
    PlayerGameweekPickMessageV2,
    BotInstructionMessage,
    GameweekFixtures,
)

STEP_SIZE = 4
CAROUSEL_SIZE_LIMIT = 50  # in KB
BUBBLE_SIZE_LIMIT = 30  # in KB


class MessageService:
    def __init__(
        self,
        bot: LineBot,
    ):
        self.bot = bot

    def __calculate_flex_message_size_bytes(self, message: dict) -> float:
        # Convert Python object to JSON-formatted string
        json_str = json.dumps(message, separators=(",", ":"))

        # Calculate the size of the string in kilobytes
        size_in_kb = len(json_str.encode("utf-8")) / 1024
        return size_in_kb

    def send_text_message(self, text: str, group_id: str):
        self.bot.send_text_message(group_id, text=text)

    def send_image_messsage(self, image_url: str, group_id: str):
        self.bot.send_image_message(image_url=image_url, group_id=group_id)

    def send_flex_message(
        self, flex_message: dict, group_id: str, alt_text: str = "Flex Message"
    ):
        self.bot.send_flex_message(
            flex_message=flex_message, group_id=group_id, alt_text=alt_text
        )

    def send_gameweek_result_message(
        self,
        gameweek: int,
        players: List[models.PlayerGameweekData],
        group_id: str,
        event_status: Optional[models.FPLEventStatusResponse] = None,
    ):
        message = GameweekResultMessage(
            gameweek=gameweek,
            players=players,
            event_status=event_status,
        )

        self.bot.send_flex_message(
            group_id=group_id,
            flex_message=message.build(),
            alt_text=f"FPL Gameweek {gameweek} Result",
        )

    def send_playeres_revenue_summary(
        self,
        players_revenues: List[models.PlayerRevenue],
        group_id: str,
    ):
        message = RevenueMessage(
            players_revenues=players_revenues,
        )

        self.bot.send_flex_message(
            group_id, flex_message=message.build(), alt_text="FPL Players Revenues"
        )

    def send_gameweek_reminder_message(
        self,
        gameweek: int,
        group_id: str,
    ):
        message = GameweekReminderMessage(gameweek=gameweek)
        self.bot.send_flex_message(
            group_id=group_id,
            flex_message=message.build(),
            alt_text=f"Gameweek {gameweek} is coming",
        )

    def send_carousel_gameweek_results_message(
        self,
        gameweek_players: List[List[models.PlayerGameweekData]],
        event_statuses: List[Optional[models.FPLEventStatusResponse]],
        gameweeks: List[int],
        group_id: str,
    ):
        messages = []
        for players, event_status, gameweek in zip(
            gameweek_players, event_statuses, gameweeks
        ):
            m = GameweekResultMessage(
                players=players,
                event_status=event_status,
                gameweek=gameweek,
            )
            messages.append(m.build())
        self.__send_carousel_message(
            group_id=group_id,
            messages=messages,
            alt_text=f"Gameweek {gameweeks[0]} to {gameweeks[-1]} Result",
            sort_by_message_size=False,
        )

    def __send_carousel_message(
        self,
        group_id: str,
        messages: List[dict],
        alt_text: str = "",
        sort_by_message_size: bool = True,
    ):
        # sorted from smallest size to largest message size
        if sort_by_message_size:
            messages = sorted(messages, key=self.__calculate_flex_message_size_bytes)
        message_chunk_size = len(messages)

        while len(messages) > 0:
            messages_to_send = messages[:message_chunk_size]
            message = CarouselMessage(messages=messages_to_send).build()
            message_size = self.__calculate_flex_message_size_bytes(message)
            if message_size > CAROUSEL_SIZE_LIMIT:
                message_chunk_size = message_chunk_size - 1
                continue
            messages = messages[message_chunk_size:]
            message_chunk_size = len(messages)
            self.bot.send_flex_message(
                flex_message=message,
                alt_text=alt_text,
                group_id=group_id,
            )

    def send_carousel_players_gameweek_picks(
        self,
        gameweek: int,
        player_gameweek_picks: List[models.PlayerGameweekPicksData],
        group_id: str,
    ):
        temp_player_gameweek_picks = [*player_gameweek_picks]
        messages = [
            PlayerGameweekPickMessageV2(
                gameweek=gameweek,
                player_picks=p,
            ).build()
            for p in temp_player_gameweek_picks
        ]
        self.__send_carousel_message(
            group_id=group_id, messages=messages, alt_text=f"Gameweek {gameweek} Picks"
        )

    def send_bot_instruction_message(
        self,
        group_id: str,
        commands_map_list: List[tuple[str]],
    ):
        messages = []
        page_count = 1
        page_command_size = 8
        for i in range(0, len(commands_map_list), page_command_size):
            j = i + page_command_size
            if j > len(commands_map_list):
                j = len(commands_map_list) - 1
            message = BotInstructionMessage(
                commands_map_list=commands_map_list[i:j],
                page=page_count,
            ).build()
            messages.append(message)
            page_count += 1

        self.__send_carousel_message(
            group_id=group_id,
            messages=messages,
            alt_text="Luka Bot instructions",
            sort_by_message_size=False,
        )

    def send_gameweek_fixtures_message(
        self, group_id: str, gameweek: int, fixtures: List[models.FPLMatchFixture]
    ):
        message = GameweekFixtures(
            gameweek=gameweek,
            fixtures=fixtures,
        ).build()
        self.bot.send_flex_message(
            flex_message=message,
            alt_text=f"Gameweek{gameweek} Fixtures",
            group_id=group_id,
        )

    def send_carousel_gameweek_fixtures_message(
        self,
        group_id: str,
        fixtures_list: List[List[models.FPLMatchFixture]],
        gameweeks: List[int],
    ):
        messages = []
        for fixtures, gameweek in zip(fixtures_list, gameweeks):
            message = GameweekFixtures(gameweek=gameweek, fixtures=fixtures)
            messages.append(message.build())
        self.__send_carousel_message(
            group_id=group_id,
            messages=messages,
            alt_text=f"Gameweek {gameweeks[0]} to {gameweeks[1]} Fixtures",
            sort_by_message_size=False,
        )
