import asyncio
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.models import MessageEvent, TextMessage, SourceGroup
from linebot.exceptions import InvalidSignatureError
from loguru import logger
from app import App
from .handler import new_line_message_handler
from ._command_parser import Luka


class LineMessageAPI:
    def __init__(self, app: App):
        self.__app = Flask(__name__)
        self.__handler = WebhookHandler(app.config.line_channel_secret)
        self.handler = new_line_message_handler(app=app)
        self.message_service = app.message_service
        self.luka_cli = Luka(self.handler)

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
        def __handle_message_v2__(event: MessageEvent):
            source: SourceGroup = event.source
            message: TextMessage = event.message
            text: str = message.text
            text = text.lstrip().strip()
            is_cmd_message = text.startswith("\\l ")
            if not is_cmd_message:
                return
            text = text.removeprefix("\\l ")
            text = f"luka {text}"
            namespace, message = self.luka_cli.parse_command(args=text)
            if namespace is None and message is None:
                return
            if message is not None:
                self.message_service.send_text_message(
                    group_id=source.group_id, text=message
                )
                return
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.luka_cli.map_namespace_to_action(
                    group_id=source.group_id, namespace=namespace
                )
            )

        return self.__app
