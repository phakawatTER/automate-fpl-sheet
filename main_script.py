import argparse
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
from services import FPLService, MessageService
from config import Config
from adapter import GoogleSheet


class InvalidInputException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


async def main():
    parser = argparse.ArgumentParser(
        description="Process the gameweek integer argument."
    )

    # Add the argument for gameweek
    parser.add_argument(
        "--gameweek", type=int, help="Specify the gameweek as an integer"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the value of the gameweek argument
    gameweek: int = args.gameweek
    if gameweek is None:
        raise InvalidInputException("invalid gameweek value")
    if gameweek < 1 or gameweek > 38:
        raise InvalidInputException("invalid gameweek value. should be in range 1-38")

    logger.info(f"processing gameweek {gameweek}")

    # initialize config
    config = Config.initialize("./config.json")

    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(config=config, google_sheet=google_sheet)
    players = await fpl_service.update_fpl_table(gameweek)
    group_id = "C44a80181a9d0ded2f6c3093adbbd6a8a"
    message_service = MessageService(config)
    event_status = await fpl_service.get_gameweek_event_status(gameweek)
    message_service.send_gameweek_result_message(
        gameweek, players, group_id=group_id, event_status=event_status
    )
    # players_revenues = await fpl_service.list_players_revenues()
    # message_service.send_playeres_revenue_summary(players_revenues, group_id)
    # message_service.send_gameweek_reminder_message(gameweek, group_id)


if __name__ == "__main__":
    asyncio.run(main())
