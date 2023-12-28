import json
from dataclasses import dataclass
from adapter import SSM


class ConfigParameter:
    cookies = "/dsfpl/config/cookies"
    line_channel_access_token = "/dsfpl/config/line_channel_access_token"
    line_channel_id = "/dsfpl/config/line_channel_id"
    line_channel_secret = "/dsfpl/config/line_channel_secret"
    firebase_db_url = "/dsfpl/config/firebase_db_url"


@dataclass
class Config(object):
    cookies: str
    line_channel_access_token: str
    line_channel_id: str
    line_channel_secret: str
    firebase_db_url: str

    @staticmethod
    def load_from_ssm(ssm: SSM):
        config = {}
        for key, value in ConfigParameter.__dict__.items():
            if not key.startswith("__") and not callable(value):
                param = ssm.get_parameter(value)
                config[key] = param
        return Config(**config)

    @staticmethod
    def load_from_file(path_to_config):
        with open(path_to_config, "r", encoding="utf8") as file:
            config_data: dict = json.load(file)
        return Config(**config_data)
