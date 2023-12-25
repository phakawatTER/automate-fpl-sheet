from api import LineMessageAPI
from app import App

if __name__ == "__main__":
    fpl_app = App()
    line_message_api = LineMessageAPI(app=fpl_app)
    app = line_message_api.initialize()
    app.run(port=5100, debug=True)
