from config import Config
from api import LineMessageAPI

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    app = LineMessageAPI(config).initialize()
    app.run(port=5100)
