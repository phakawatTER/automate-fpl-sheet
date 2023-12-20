from typing import List, Optional, Tuple
from line import LineBot
import models
from config import Config
from .message_template import (
    GameweekResultMessage,
    RevenueMessage,
    GameweekReminderMessage,
    GameweekResultCarouselMessage,
)


class MessageService:
    def __init__(self, config: Config):
        self.bot = LineBot(config=config)
        self.sheet_url = config.sheet_url

    def send_text_message(self, text: str, group_id: str):
        self.bot.send_text_message(group_id, text=text)

    def send_image_messsage(self, image_url: str, group_id: str):
        self.bot.send_image_message(image_url=image_url, group_id=group_id)

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
            sheet_url=self.sheet_url,
            event_status=event_status,
        )

        self.bot.send_flex_message(
            group_id=group_id,
            flex_message=message.build(),
            alt_text=f"FPL Gameweek {gameweek} Result",
        )

    def send_playeres_revenue_summary(
        self, players_revenues: List[models.PlayerRevenue], group_id: str
    ):
        message = RevenueMessage(
            players_revenues=players_revenues,
            sheet_url=self.sheet_url,
        )

        self.bot.send_flex_message(
            group_id, flex_message=message.build(), alt_text="FPL Players Revenues"
        )

    def send_gameweek_reminder_message(self, gameweek: int, group_id: str):
        message = GameweekReminderMessage(sheet_url=self.sheet_url, gameweek=gameweek)
        self.bot.send_flex_message(
            group_id,
            flex_message=message.build(),
            alt_text=f"Gameweek {gameweek} is coming",
        )

    def send_carousel_gameweek_results_message(
        self,
        gameweeks_data: List[
            Tuple[List[models.PlayerGameweekData], models.FPLEventStatusResponse, int]
        ],
        group_id: str,
    ):
        messages = []
        for players, event_status, gameweek in gameweeks_data:
            m = GameweekResultMessage(
                players=players,
                event_status=event_status,
                gameweek=gameweek,
                sheet_url=self.sheet_url,
            )
            messages.append(m.build())

        message = GameweekResultCarouselMessage(messages=messages).build()
        self.bot.send_flex_message(
            flex_message=message, alt_text="Gameweek Results", group_id=group_id
        )
