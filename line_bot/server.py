import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage,TextSendMessage,FollowEvent
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from config.config import Config


class LineMessageAPI:

    def __init__(self):
        pass
    
    @staticmethod
    def initialize_line_bot_app(config:Config):
        line_bot_api = LineBotApi(config.line_channel_access_token)
        handler = WebhookHandler(config.line_channel_secret)
        app = Flask(__name__)

        @app.route("/callback", methods=['POST'])
        def callback():
            signature = request.headers['X-Line-Signature']
            logger.info(signature)
            body = request.get_data(as_text=True)
            logger.info(json.dumps(body,indent=4))
            try:
                handler.handle(body, signature)
            except InvalidSignatureError as e:
                logger.error(e)
                abort(400)

            return 'OK'

        @handler.add(MessageEvent, message=TextMessage)
        def handle_message(event):
            text = event.message.text
            reply_text = f"Hello, {text}!"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        @handler.add(FollowEvent)
        def handle_follow(event):
            # Handle follow events
            user_id = event.source.user_id
            reply_text = f"Thanks for following! Your user ID is {user_id}"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        
        return app

