from oauth2client.service_account import ServiceAccountCredentials
from config import Config
from api import LineMessageAPI

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name("./service_account.json")
    app = LineMessageAPI(config,credential=credential).initialize()
    app.run(port=5100)
