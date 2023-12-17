from typing import List
from line import LineBot
from config import Config
from models import PlayerResultData, PlayerRevenue
from .message_template import (
    GameweekResultMessage,
    RevenueMessage,
    GameweekReminderMessage,
)


class MessageService:
    def __init__(self, config: Config):
        self.bot = LineBot(config=config)
        self.sheet_url = config.sheet_url

    def send_text_message(self, text: str, group_id: str):
        self.bot.send_text_message(group_id, text=text)

    def send_gameweek_result_message(
        self, gameweek: int, players: List[PlayerResultData], group_id: str
    ):
        message = GameweekResultMessage(
            gameweek=gameweek, players=players, sheet_url=self.sheet_url
        )

        self.bot.send_flex_message(
            group_id=group_id,
            flex_message=message.build(),
            alt_text=f"FPL Gameweek {gameweek} Result",
        )

    def send_playeres_revenue_summary(
        self, players_revenues: List[PlayerRevenue], group_id: str
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
