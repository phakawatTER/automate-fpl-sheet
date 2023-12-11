import re
import time
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.models import MessageEvent,TextMessage,SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from services import FPLService,MessageService
from config.config import Config

SECOND = 1000

def _get_timestamp():
    return int(time.time()) * 1000

class LineMessageAPI:
    
    PATTERN_ACTIONS = {
        r"get (gw|gameweek) (\d+)": "update_fpl_table",
        r"get (revenue|rev)": "get_revenues",
    }

    def __init__(self,config:Config):
        self.app = Flask(__name__)
        self.handler = WebhookHandler(config.line_channel_secret)
        self.message_service = MessageService(config=config)
        self.config = config
        
    def initialize(self):
        handler = WebhookHandler(self.config.line_channel_secret)

        @self.app.route("/callback", methods=['POST'])
        def callback():
            signature = request.headers['X-Line-Signature']
            body = request.get_data(as_text=True)
            try:
                handler.handle(body, signature)
            except InvalidSignatureError as e:
                logger.error(e)
                abort(400)
                
            return 'OK'

        @handler.add(MessageEvent, message=TextMessage)
        def handle_message(event:MessageEvent):
            source:SourceGroup = event.source
            if source.group_id != self.config.line_group_id:
                return
            message:TextMessage = event.message
            now = _get_timestamp()
            if now - event.timestamp > 1 * SECOND:
                return
            
            text:str = message.text
            print(LineMessageAPI.PATTERN_ACTIONS)
            for pattern,action in LineMessageAPI.PATTERN_ACTIONS.items():
                print(pattern,action)
                match = re.search(pattern, text.lower())
                print("math",match)
                if match:
                    if action == "update_fpl_table":
                        extracted_group = match.group(2)
                        game_week = int(extracted_group)
                        self._handle_update_fpl_table(game_week=game_week)
                    elif action == "get_revenues":
                        extracted_group = match.group(1)
                        self._handle_get_revenues()
                    else:
                        pass

                    break
                
        
        return self.app
    
    def _handle_update_fpl_table(self,game_week:int):
        players = FPLService.update_fpl_table(gw=game_week,config=self.config)
        self.message_service.send_gameweek_result_message(game_week=game_week,players=players)
        
    def _handle_get_revenues(self):
        players = FPLService.list_players_revenues(self.config)
        self.message_service.send_playeres_revenue_summary(players_revenues=players)
        
