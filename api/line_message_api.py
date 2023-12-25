import re
import asyncio
import json
from typing import List, Optional
from flask import Flask, request, abort
from werkzeug.exceptions import HTTPException
from boto3.session import Session
from boto3_type_annotations.lambda_ import Client as LambdaClient
from linebot import WebhookHandler
from linebot.models import MessageEvent, TextMessage, SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
import models
import util
from app import App

PLOT_GENERATOR_FUNCTION_NAME = "FPLPlotGenerator"


class HelperHandlerActionGroup:
    LIST_COMMANDS = "LIST_COMMANDS"


class MessageHandlerActionGroup:
    UPDATE_FPL_TABLE = "UPDATE_FPL_TABLE"
    BATCH_UPDATE_FPL_TABLE = "BATCH_UPDATE_FPL_TABLE"
    GET_PLAYERS_REVENUES = "GET_PLAYERS_REVENUES"
    GENERATE_GAMEWEEKS_PLOT = "GENERATE_GAMEWEEKS_PLOT"
    GET_PLAYER_GW_PICKS = "GET_PLAYER_GW_PICKS"
    SUBSCRIBE_LEAGUE = "SUBSCRIBE_LEAGUE"
    UNSUBSCRIBE_LEAGUE = "UNSUBSCRIBE_LEAGUE"

    @staticmethod
    def get_commands():
        return {
            MessageHandlerActionGroup.UPDATE_FPL_TABLE: "Update/Get FPL table of given gameweek",
            MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE: "Batch update/get FPL table",
            MessageHandlerActionGroup.GET_PLAYERS_REVENUES: "Get cummulative revenues",
            MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT: "Generate cummulative revenue over gameweeks",
            MessageHandlerActionGroup.GET_PLAYER_GW_PICKS: "List players's first 11 picks of given gameweek",
            MessageHandlerActionGroup.SUBSCRIBE_LEAGUE: "Subscribe league by league id",
            MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE: "Unsubscribe league by league id",
        }


class LineMessageAPI:
    PATTERN_ACTIONS = {
        r"list (cmd|commands)": HelperHandlerActionGroup.LIST_COMMANDS,
        r"subscribe league (\d+)": MessageHandlerActionGroup.SUBSCRIBE_LEAGUE,
        r"unsubscribe league": MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE,
        r"get (gw|gameweek) (\d+-\d+)": MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE,
        r"get (gw|gameweek) (\d+)": MessageHandlerActionGroup.UPDATE_FPL_TABLE,
        r"get (revenue|rev)": MessageHandlerActionGroup.GET_PLAYERS_REVENUES,
        r"get (plot|plt) (\d+-\d+)": MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT,
        r"get (picks) (\d+)": MessageHandlerActionGroup.GET_PLAYER_GW_PICKS,
    }

    def __init__(self, app: App):
        self.__app = Flask(__name__)
        self.__handler = WebhookHandler(app.config.line_channel_secret)
        self.__message_service = app.message_service
        self.__fpl_service = app.fpl_service
        self.__firebase_repo = app.firebase_repo
        self.__subscription_service = app.subscription_service
        self.__session = Session()
        self.__lambda_client: LambdaClient = self.__session.client("lambda")

    def initialize(self):
        @self.__app.route("/health-check", methods=["GET"])
        def __health_check__():
            return {"message": "OK"}

        @self.__app.route("/callback", methods=["POST"])
        def __callback__():
            signature = request.headers["X-Line-Signature"]
            body = request.get_data(as_text=True)
            try:
                self.__handler.handle(body, signature)
            except InvalidSignatureError as e:
                logger.error(e)
                abort(400)

            return {"message": "OK"}

        @self.__handler.add(MessageEvent, message=TextMessage)
        def __handle_message__(event: MessageEvent):
            source: SourceGroup = event.source
            message: TextMessage = event.message
            text: str = message.text

            for pattern, action in LineMessageAPI.PATTERN_ACTIONS.items():
                match = re.search(pattern, text.lower())
                if match:
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
                        self.__validate_gameweek_range(start_gw, end_gw, source)

                        loop.run_until_complete(
                            self.__run_in_error_wrapper(
                                self.__handle_batch_update_fpl_table
                            )(
                                from_gameweek=start_gw,
                                to_gameweek=end_gw,
                                group_id=source.group_id,
                            )
                        )

                    elif action == MessageHandlerActionGroup.GET_PLAYERS_REVENUES:
                        extracted_group = match.group(1)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_get_revenues)(
                                group_id=source.group_id
                            )
                        )
                    elif action == MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT:
                        extracted_group = match.group(2).split("-")
                        start_gw = int(extracted_group[0])
                        end_gw = int(extracted_group[1])
                        self.__validate_gameweek_range(start_gw, end_gw, source)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_gameweek_plots)(
                                from_gameweek=start_gw,
                                to_gameweek=end_gw,
                                group_id=source.group_id,
                            )
                        )
                    elif action == MessageHandlerActionGroup.GET_PLAYER_GW_PICKS:
                        extracted_group = match.group(2)
                        gameweek = int(extracted_group)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(
                                self.__handle_players_gameweek_picks
                            )(gameweek=gameweek, group_id=source.group_id)
                        )
                    elif action == MessageHandlerActionGroup.SUBSCRIBE_LEAGUE:
                        extracted_group = match.group(1)
                        league_id = int(extracted_group)
                        loop.run_until_complete(
                            self.__subscribe_league(
                                group_id=source.group_id,
                                league_id=league_id,
                            )
                        )
                    elif action == MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE:
                        self.__unsubscribe_league(source.group_id)
                    elif action == HelperHandlerActionGroup.LIST_COMMANDS:
                        self.__run_in_error_wrapper(self.__handle_list_bot_commands)(
                            group_id=source.group_id
                        )

                    break

        return self.__app

    def __unsubscribe_league(self, group_id: str):
        league_id = self.__get_group_league_id(group_id)
        if league_id is None:
            self.__message_service.send_text_message("⚠️ Subscribed league not found")
            return
        self.__firebase_repo.unsubscribe_league(group_id)
        self.__message_service.send_text_message(
            text=f"🥲 You have unsubscribed league ID {league_id}",
            group_id=group_id,
        )

    async def __subscribe_league(self, group_id: str, league_id: int):
        is_ok = await self.__subscription_service.subscribe_league(
            league_id=league_id,
            group_id=group_id,
        )
        text = f"🎉 You have subscribed to league ID {league_id}"
        if is_ok:
            is_ok = self.__subscription_service.update_league_sheet(
                league_id=league_id,
                url="https://docs.google.com/spreadsheets/d/1eciOdiGItEkml98jVLyXysGMtpMa06hbiTTJ40lztw4/edit#gid=1315457538",
                worksheet_name="Sheet3",
            )
        if not is_ok:
            text = f"❌ Unable to subscribe to league ID {league_id}"

        self.__message_service.send_text_message(
            text=text,
            group_id=group_id,
        )

    def __run_in_error_wrapper(self, callback):
        def construct_error_message(e: Exception) -> str:
            return f"❌ Oops...something went wrong with error: {e}"

        def wrapped_sync(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except HTTPException:
                return
            except Exception as e:
                self.__message_service.send_text_message(
                    text=construct_error_message(e),
                    group_id=kwargs["group_id"],
                )
                abort(e)

        async def wrapped_async(*args, **kwargs):
            try:
                return await callback(*args, **kwargs)
            except Exception as e:
                self.__message_service.send_text_message(
                    text=construct_error_message(e),
                    group_id=kwargs["group_id"],
                )
                abort(e)

        if asyncio.iscoroutinefunction(callback):
            return wrapped_async
        return wrapped_sync

    # NOTE: We support only 1 league per channel for now
    def __get_group_league_id(self, group_id: str):
        league_ids = self.__firebase_repo.list_leagues_by_line_group_id(group_id)
        if league_ids is not None and len(league_ids) > 0:
            return league_ids[0]
        self.__message_service.send_text_message(
            text="⚠️ No subscribed league found. Please subscribe to some league",
            group_id=group_id,
        )
        abort(404)

    def __handle_list_bot_commands(self, group_id: str):
        commands = MessageHandlerActionGroup.get_commands()
        commands_map_list: List[tuple[str]] = []
        for cmd, desc in commands.items():
            for pattern, _cmd in LineMessageAPI.PATTERN_ACTIONS.items():
                if cmd == _cmd:
                    commands_map_list.append((desc, pattern.replace("|", " | ")))
                    break
        self.__message_service.send_bot_instruction_message(
            group_id=group_id,
            commands_map_list=commands_map_list,
        )

    async def __handle_batch_update_fpl_table(
        self, from_gameweek: int, to_gameweek: int, group_id
    ):
        event_status = await self.__fpl_service.get_gameweek_event_status(
            gameweek=to_gameweek
        )
        current_gameweek_event = (
            None if event_status is None else event_status.status[0].event
        )

        gameweek_players: List[List[models.PlayerGameweekData]] = []
        event_statuses: List[Optional[models.FPLEventStatusResponse]] = []
        gameweeks: List[int] = []
        league_id = self.__get_group_league_id(group_id)
        self.__message_service.send_text_message(
            text=f"Procesing gameweek {from_gameweek} to {to_gameweek}",
            group_id=group_id,
        )
        for gameweek in range(from_gameweek, to_gameweek + 1):
            players = await self.__fpl_service.get_or_update_fpl_gameweek_table(
                gameweek=gameweek,
                league_id=league_id,
            )
            gameweek_players.append(players)
            event_statuses.append(
                event_status
                if current_gameweek_event is not None
                and current_gameweek_event == gameweek
                else None
            )
            gameweeks.append(gameweek)
        self.__message_service.send_carousel_gameweek_results_message(
            gameweek_players=gameweek_players,
            event_statuses=event_statuses,
            gameweeks=gameweeks,
            group_id=group_id,
        )

    async def __handle_update_fpl_table(self, gameweek: int, group_id: str):
        league_id = self.__get_group_league_id(group_id)
        self.__message_service.send_text_message(
            f"Gameweek {gameweek} result is being processed. Please wait for a moment",
            group_id=group_id,
        )
        players = await self.__fpl_service.get_or_update_fpl_gameweek_table(
            gameweek=gameweek,
            league_id=league_id,
        )
        event_status = await self.__fpl_service.get_gameweek_event_status(gameweek)
        self.__message_service.send_gameweek_result_message(
            gameweek=gameweek,
            players=players,
            group_id=group_id,
            event_status=event_status,
        )

    async def __handle_get_revenues(self, group_id: str):
        league_id = self.__get_group_league_id(group_id)
        self.__message_service.send_text_message(
            "Players revenue is being processed. Please wait for a moment",
            group_id=group_id,
        )
        players = await self.__fpl_service.list_players_revenues(league_id)
        self.__message_service.send_playeres_revenue_summary(
            players_revenues=players,
            group_id=group_id,
        )

    @util.time_track(description="Gameweek plot handler")
    async def __handle_gameweek_plots(
        self, from_gameweek: int, to_gameweek: int, group_id: str
    ):
        self.__message_service.send_text_message(
            text=f"Plots for GW{from_gameweek} to GW{to_gameweek} are being processed. Please wait for a moment...",
            group_id=group_id,
        )
        league_id = self.__get_group_league_id(group_id)
        gameweeks_data: list[list[dict[str, any]]] = []
        for gw in range(from_gameweek, to_gameweek + 1, 1):
            gameweek_data = await self.__fpl_service.get_or_update_fpl_gameweek_table(
                gameweek=gw,
                league_id=league_id,
            )
            gameweeks_data.append([g.to_json() for g in gameweek_data])

        payload = {
            "start_gw": from_gameweek,
            "end_gw": to_gameweek,
            "gameweeks_data": gameweeks_data,
        }
        response = self.__lambda_client.invoke(
            FunctionName=PLOT_GENERATOR_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        logger.success(response)
        if response.get("StatusCode") != 200:
            abort(response.get("StatusCode"))
        payload_bytes = response.get("Payload").read()
        urls: List[str] = json.loads(payload_bytes)
        logger.info(urls)
        for url in urls:
            self.__message_service.send_image_messsage(image_url=url, group_id=group_id)

    async def __handle_players_gameweek_picks(self, gameweek: int, group_id: str):
        league_id = self.__get_group_league_id(group_id)
        player_gameweek_picks = await self.__fpl_service.list_player_gameweek_picks(
            gameweek=gameweek,
            league_id=league_id,
        )
        self.__message_service.send_carousel_players_gameweek_picks(
            gameweek=gameweek,
            player_gameweek_picks=player_gameweek_picks,
            group_id=group_id,
        )

    def __validate_gameweek_range(
        self, start_gw: int, end_gw: int, source: SourceGroup
    ):
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
