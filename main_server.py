from oauth2client.service_account import ServiceAccountCredentials
from config import Config
from api import LineMessageAPI

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    line_message_api = LineMessageAPI(config, credential=credential)
    app = line_message_api.initialize()
    app.run(port=5100, debug=True)
