import re
import asyncio
from flask import Flask, request, abort
from oauth2client.service_account import ServiceAccountCredentials
from linebot import WebhookHandler
from linebot.models import MessageEvent,TextMessage,SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from services import FPLService,MessageService
from adapter import GoogleSheet
from config.config import Config

class LineMessageAPI:
    
    PATTERN_ACTIONS = {
        r"get (gw|gameweek) (\d+)": "update_fpl_table",
        r"get (revenue|rev)": "get_revenues",
    }

    def __init__(self,config:Config,credential:ServiceAccountCredentials):
        self.app = Flask(__name__)
        self.handler = WebhookHandler(config.line_channel_secret)
        self.message_service = MessageService(config=config)
        self.config = config
        google_sheet = GoogleSheet(credential=credential)
        google_sheet.open_sheet_by_url(config.sheet_url)
        self.fpl_service = FPLService(config=self.config,google_sheet=google_sheet)
        
    def initialize(self):
        handler = WebhookHandler(self.config.line_channel_secret)
        
        @self.app.route("/health-check", methods=["GET"])
        def health_check():
            return {
                "message": "OK"
            }

        @self.app.route("/callback", methods=['POST'])
        def callback():
            signature = request.headers['X-Line-Signature']
            body = request.get_data(as_text=True)
            try:
                handler.handle(body, signature)
            except InvalidSignatureError as e:
                logger.error(e)
                abort(400)
                
            return {
                "message": "OK"
            }

        @handler.add(MessageEvent, message=TextMessage)
        def handle_message(event:MessageEvent):
            source:SourceGroup = event.source
            message:TextMessage = event.message
            
            text:str = message.text
            for pattern,action in LineMessageAPI.PATTERN_ACTIONS.items():
                match = re.search(pattern, text.lower())
                if match:
                    logger.success("math",match)
                    loop = asyncio.new_event_loop()
                    if action == "update_fpl_table":
                        extracted_group = match.group(2)
                        game_week = int(extracted_group)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_update_fpl_table)(game_week=game_week,group_id=source.group_id)
                        )
                    elif action == "get_revenues":
                        extracted_group = match.group(1)
                        loop.run_until_complete(
                            self.__run_in_error_wrapper(self.__handle_get_revenues)(group_id=source.group_id)
                        )
                    else:
                        pass

                    break
                
        
        return self.app
    
    
    def __run_in_error_wrapper(self,callback):
        async def wrapped_func(*args, **kwargs):
            try:
                return await callback(*args, **kwargs)
            except Exception as e:
                logger.error(e)
                self.message_service.send_text_message("Oops...something went wrong",group_id=kwargs["group_id"])
        return wrapped_func
    
    async def __handle_update_fpl_table(self,game_week:int,group_id:str):
        self.message_service.send_text_message(f"Gameweek {game_week} result is being processed. Please wait for a moment",group_id=group_id)
        players = await self.fpl_service.update_fpl_table(gameweek=game_week)
        self.message_service.send_gameweek_result_message(game_week=game_week,players=players,group_id=group_id)
        
    async def __handle_get_revenues(self,group_id:str):
        self.message_service.send_text_message("Players revenue is being processed. Please wait for a moment",group_id=group_id)
        players = self.fpl_service.list_players_revenues()
        self.message_service.send_playeres_revenue_summary(players_revenues=players,group_id=group_id)
