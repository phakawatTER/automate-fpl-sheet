import re
import asyncio
from typing import List, Optional
from flask import Flask, request, abort
from oauth2client.service_account import ServiceAccountCredentials
from linebot import WebhookHandler
from linebot.models import MessageEvent, TextMessage, SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from services import FPLService, MessageService
from adapter import GoogleSheet
from config.config import Config
import models


class MessageHandlerActionGroup:
    UPDATE_FPL_TABLE = "update_fpl_table"
    BATCH_UPDATE_FPL_TABLE = "batch_update_fpl_table"
    GET_PLAYERS_REVENUES = "get_players_revenues"


class LineMessageAPI:
    PATTERN_ACTIONS = {
        r"get (gw|gameweek) (\d+-\d+)": MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE,
        r"get (gw|gameweek) (\d+)": MessageHandlerActionGroup.UPDATE_FPL_TABLE,
        r"get (revenue|rev)": MessageHandlerActionGroup.GET_PLAYERS_REVENUES,
    }

    def __init__(self, config: Config, credential: ServiceAccountCredentials):
        self.__app = Flask(__name__)
        self.__handler = WebhookHandler(config.line_channel_secret)
        self.__message_service = MessageService(config=config)
        self.__config = config
        google_sheet = GoogleSheet(credential=credential)
        google_sheet.open_sheet_by_url(config.sheet_url)
        self.__fpl_service = FPLService(config=self.__config, google_sheet=google_sheet)

    def initialize(self):
        @self.__app.route("/health-check", methods=["GET"])
        def health_check():
            return {"message": "OK"}

        @self.__app.route("/callback", methods=["POST"])
        def callback():
            signature = request.headers["X-Line-Signature"]
            body = request.get_data(as_text=True)
            try:
                self.__handler.handle(body, signature)
            except InvalidSignatureError as e:
                logger.error(e)
                abort(400)

            return {"message": "OK"}

        @self.__handler.add(MessageEvent, message=TextMessage)
        def handle_message(event: MessageEvent):
            source: SourceGroup = event.source
            message: TextMessage = event.message

            text: str = message.text
            for pattern, action in LineMessageAPI.PATTERN_ACTIONS.items():
                match = re.search(pattern, text.lower())
                if match:
                    logger.success("math", match)
                    loop = asyncio.new_event_loop()
                    if action == MessageHandlerActionGroup.UPDATE_FPL_TABLE:
                        extracted_group = match.group(2)
                        gameweek = int(extracted_group)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_update_fpl_table)(
                                gameweek=gameweek, group_id=source.group_id
                            )
                        )
                    elif action == MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE:
                        extracted_group = match.group(2).split("-")
                        start_gw = int(extracted_group[0])
                        end_gw = int(extracted_group[1])
                        # Validate if start_gw and end_gw are in the range (1, 38)
                        if 1 <= start_gw <= 38 and 1 <= end_gw <= 38:
                            # Validate if start_gw is less than or equal to end_gw
                            if start_gw > end_gw:
                                self.__message_service.send_text_message(
                                    "Validation error: start_gw should be less than or equal to end_gw",
                                    source.group_id,
                                )
                                abort(403)
                        else:
                            self.__message_service.send_text_message(
                                "Validation error: start_gw and end_gw should be in the range (1, 38)",
                                source.group_id,
                            )
                            abort(403)

                        loop.run_until_complete(
                            self.__handle_batch_update_fpl_table(
                                start_gw, end_gw, source.group_id
                            )
                        )

                    elif action == MessageHandlerActionGroup.GET_PLAYERS_REVENUES:
                        extracted_group = match.group(1)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_get_revenues)(
                                group_id=source.group_id
                            )
                        )
                    else:
                        pass

                    break

        return self.__app

    def __run_in_error_wrapper(self, callback):
        async def wrapped_func(*args, **kwargs):
            try:
                return await callback(*args, **kwargs)
            except Exception as e:
                self.__message_service.send_text_message(
                    f"Oops...something went wrong with error: {e}",
                    group_id=kwargs["group_id"],
                )
                abort(e)

        return wrapped_func

    async def __handle_batch_update_fpl_table(
        self, from_gameweek: int, to_gameweek: int, group_id
    ):
        event_status = await self.__fpl_service.get_gameweek_event_status(
            gameweek=to_gameweek
        )
        current_gameweek_event = (
            None if event_status is None else event_status.status[0].event
        )

        gameweek_players: List[List[models.PlayerResultData]] = []
        event_statuses: List[Optional[models.FPLEventStatusResponse]] = []
        gameweeks: List[int] = []
        self.__message_service.send_text_message(
            text=f"Procesing gameweek {from_gameweek} to {to_gameweek}",
            group_id=group_id,
        )
        for gameweek in range(from_gameweek, to_gameweek + 1):
            players = await self.__fpl_service.update_fpl_table(gameweek)
            gameweek_players.append(players)
            event_statuses.append(
                event_status
                if current_gameweek_event is not None
                and current_gameweek_event == gameweek
                else None
            )
            gameweeks.append(gameweek)

        step_size = 8
        for i in range(0, len(gameweek_players), step_size):
            j = (
                i + step_size
                if i + step_size <= len(gameweek_players) - 1
                else len(gameweek_players)
            )

            data = zip(
                gameweek_players[i:j],
                event_statuses[i:j],
                gameweeks[i:j],
            )

            self.__message_service.send_carousel_gameweek_results_message(
                gameweeks_data=data,
                group_id=group_id,
            )

    async def __handle_update_fpl_table(self, gameweek: int, group_id: str):
        self.__message_service.send_text_message(
            f"Gameweek {gameweek} result is being processed. Please wait for a moment",
            group_id=group_id,
        )
        players = await self.__fpl_service.update_fpl_table(gameweek=gameweek)
        event_status = await self.__fpl_service.get_gameweek_event_status(gameweek)
        self.__message_service.send_gameweek_result_message(
            gameweek=gameweek,
            players=players,
            group_id=group_id,
            event_status=event_status,
        )

    async def __handle_get_revenues(self, group_id: str):
        self.__message_service.send_text_message(
            "Players revenue is being processed. Please wait for a moment",
            group_id=group_id,
        )
        players = await self.__fpl_service.list_players_revenues()
        self.__message_service.send_playeres_revenue_summary(
            players_revenues=players, group_id=group_id
        )
