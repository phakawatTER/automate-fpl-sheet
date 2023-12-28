import re
import asyncio
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.models import MessageEvent, TextMessage, SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from app import App
from .handler import new_line_message_handler
from ._message_pattern import (
    MessageHandlerActionGroup,
    HelperHandlerActionGroup,
    PATTERN_ACTIONS,
)


class LineMessageAPI:
    def __init__(self, app: App):
        self.__app = Flask(__name__)
        self.__handler = WebhookHandler(app.config.line_channel_secret)
        self.handler = new_line_message_handler(app=app)

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
            for pattern, action in PATTERN_ACTIONS.items():
                match = re.fullmatch(pattern, text.lower())
                if match:
                    loop = asyncio.new_event_loop()
                    if action == MessageHandlerActionGroup.UPDATE_FPL_TABLE:
                        extracted_group = match.group(2)
                        gameweek = int(extracted_group)
                        loop.run_until_complete(
                            self.handler.handle_update_fpl_table(
                                gameweek=gameweek, group_id=source.group_id
                            )
                        )
                    elif action == MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE:
                        extracted_group = match.group(2).split("-")
                        start_gw = int(extracted_group[0])
                        end_gw = int(extracted_group[1])
                        loop.run_until_complete(
                            self.handler.handle_batch_update_fpl_table(
                                from_gameweek=start_gw,
                                to_gameweek=end_gw,
                                group_id=source.group_id,
                            )
                        )

                    elif action == MessageHandlerActionGroup.GET_PLAYERS_REVENUES:
                        extracted_group = match.group(1)
                        loop.run_until_complete(
                            self.handler.handle_get_revenues(group_id=source.group_id)
                        )
                    elif action == MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT:
                        extracted_group = match.group(2).split("-")
                        start_gw = int(extracted_group[0])
                        end_gw = int(extracted_group[1])
                        loop.run_until_complete(
                            self.handler.handle_gameweek_plots(
                                from_gameweek=start_gw,
                                to_gameweek=end_gw,
                                group_id=source.group_id,
                            )
                        )
                    elif action == MessageHandlerActionGroup.GET_PLAYER_GW_PICKS:
                        extracted_group = match.group(2)
                        gameweek = int(extracted_group)
                        loop.run_until_complete(
                            self.handler.handle_players_gameweek_picks(
                                gameweek=gameweek, group_id=source.group_id
                            )
                        )
                    elif action == MessageHandlerActionGroup.SUBSCRIBE_LEAGUE:
                        extracted_group = match.group(1)
                        league_id = int(extracted_group)
                        loop.run_until_complete(
                            self.handler.subscribe_league(
                                group_id=source.group_id,
                                league_id=league_id,
                            )
                        )
                    elif action == MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE:
                        self.handler.unsubscribe_league(source.group_id)

                    elif action == HelperHandlerActionGroup.LIST_COMMANDS:
                        self.handler.handle_list_bot_commands(group_id=source.group_id)

                    elif action == MessageHandlerActionGroup.LIST_LEAGUE_PLAYERS:
                        self.handler.handle_list_league_players(
                            group_id=source.group_id
                        )
                    elif action == MessageHandlerActionGroup.UPDATE_PLAYER_BANK_ACCOUNT:
                        extracted_group = match.group(1)
                        player_index = int(match.group(1)) - 1
                        bank_account = match.group(3)
                        self.handler.handle_set_league_player_bank_account(
                            group_id=source.group_id,
                            bank_account=bank_account,
                            player_index=player_index,
                        )
                    elif action == MessageHandlerActionGroup.CLEAR_ALL_GAMEWEEKS_CACHE:
                        self.handler.handle_clear_gameweeks_cache(source.group_id)
                    elif action == MessageHandlerActionGroup.UPDATE_LEAGUE_REWARDS:
                        extracted_group = match.group(1).split(",")
                        rewards = [float(reward) for reward in extracted_group]
                        self.handler.handle_update_league_rewards(
                            group_id=source.group_id, rewards=rewards
                        )
                    elif action == MessageHandlerActionGroup.ADD_IGNORED_LEAGUE_PLAYER:
                        player_index = int(match.group(1)) - 1
                        self.handler.handle_add_ignored_player(
                            group_id=source.group_id, player_index=player_index
                        )
                    elif (
                        action == MessageHandlerActionGroup.REMOVE_IGNORED_LEAGUE_PLAYER
                    ):
                        player_index = int(match.group(1)) - 1
                        self.handler.handle_remove_ignored_player(
                            group_id=source.group_id, player_index=player_index
                        )

                    elif action == MessageHandlerActionGroup.GET_GAMEWEEK_FIXTURES:
                        gameweek = int(match.group(2))
                        loop.run_until_complete(
                            self.handler.handle_list_gameweek_fixtures(
                                group_id=source.group_id,
                                gameweek=gameweek,
                            )
                        )
                    elif action == MessageHandlerActionGroup.LIST_GAMEWEEK_FIXTURES:
                        gameweek_range = match.group(2).split("-")
                        start_gw, stop_gw = gameweek_range
                        loop.run_until_complete(
                            self.handler.handle_list_gameweek_fixtures_by_range(
                                group_id=source.group_id,
                                start_gameweek=int(start_gw),
                                stop_gameweek=int(stop_gw),
                            )
                        )

        return self.__app
