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
)

STEP_SIZE = 4


class MessageService:
    def __init__(
        self,
        bot: LineBot,
    ):
        self.bot = bot

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
        step_size = 8
        for i in range(0, len(gameweek_players), step_size):
            j = i + step_size
            if j > len(gameweek_players):
                j = len(gameweek_players)
            data = zip(
                gameweek_players[i:j],
                event_statuses[i:j],
                gameweeks[i:j],
            )
            messages = []
            for players, event_status, gameweek in data:
                m = GameweekResultMessage(
                    players=players,
                    event_status=event_status,
                    gameweek=gameweek,
                )
                messages.append(m.build())

            message = CarouselMessage(messages=messages).build()
            self.bot.send_flex_message(
                flex_message=message, alt_text="Gameweek Results", group_id=group_id
            )

    def send_carousel_players_gameweek_picks(
        self,
        gameweek: int,
        player_gameweek_picks: List[models.PlayerGameweekPicksData],
        group_id: str,
    ):
        for i in range(0, len(player_gameweek_picks), STEP_SIZE):
            j = i + STEP_SIZE
            if j > len(player_gameweek_picks):
                j = len(player_gameweek_picks)
            messages = []
            for p in player_gameweek_picks[i:j]:
                message = PlayerGameweekPickMessageV2(gameweek=gameweek, player_picks=p)
                messages.append(message.build())
            message = CarouselMessage(messages=messages)
            self.bot.send_flex_message(
                flex_message=message.build(),
                alt_text=f"Player Gameweek {gameweek} Picks",
                group_id=group_id,
            )

    def send_bot_instruction_message(
        self,
        group_id: str,
        commands_map_list: List[tuple[str]],
    ):
        message = BotInstructionMessage(commands_map_list=commands_map_list).build()
        self.bot.send_flex_message(
            group_id=group_id, flex_message=message, alt_text="Luka Bot instructions"
        )
