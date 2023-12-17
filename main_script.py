import argparse
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
from services import FPLService
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
    await fpl_service.update_fpl_table(gameweek)


if __name__ == "__main__":
    asyncio.run(main())
