from config import Config
from line import LineMessageAPI

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    app = LineMessageAPI.initialize_line_bot_app(config)
    app.run(port=5100,host="localhost")
