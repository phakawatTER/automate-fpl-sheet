from linebot.models import FlexSendMessage
from linebot.exceptions import LineBotApiError
from linebot import LineBotApi
from loguru import logger
from config import Config


class LineBot:
    def __init__(self,config:Config):
        self.config = config
        self.line_bot_api = LineBotApi(config.line_channel_access_token)

    def send_flex_message(self,group_id:str,flex_message:dict,alt_text:str="Flex Message"):
        try:
            self.line_bot_api.push_message(group_id, FlexSendMessage(alt_text=alt_text, contents=flex_message))
        except LineBotApiError as e:
            logger.error(f"error sending Flex Message: {e}")
