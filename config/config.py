import json


class Config(object):
    def __init__(self, path_to_config: str):
        with open(path_to_config, "r", encoding="utf8") as file:
            config_data: dict = json.load(file)
        self.cookies: str = config_data.get("cookies")
        self.line_channel_access_token: str = config_data.get(
            "line_channel_access_token"
        )
        self.line_channel_id: str = config_data.get("line_channel_id")
        self.line_channel_secret: str = config_data.get("line_channel_secret")
        self.firebase_db_url: str = config_data.get("firebase_db_url")
