from api import LineMessageAPI
from app import App


def main() -> None:
    fpl_app = App()
    line_message_api = LineMessageAPI(app=fpl_app)
    app = line_message_api.initialize()
    app.run(port=5100, debug=True)


if __name__ == "__main__":
    main()
