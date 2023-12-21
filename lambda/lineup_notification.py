import os
import sys
import asyncio

from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from services import FPLService, MessageService
from adapter import S3Downloader, GoogleSheet
from config import Config

GROUP_ID = "C6402ad4c1937733c7db4e3ff7181287c"


async def execute(gameweek: int):
    sess = Session()
    s3_downloader = S3Downloader(sess, "ds-fpl", "/tmp")

    file_path = s3_downloader.download_file("config.json")
    config = Config(file_path)

    file_path = s3_downloader.download_file("service_account.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(google_sheet=google_sheet, config=config)
    message_service = MessageService(config=config)
    player_gameweek_picks = await fpl_service.list_player_gameweek_picks(
        gameweek=gameweek
    )
    message_service.send_carousel_players_gameweek_picks(
        gameweek=gameweek,
        player_gameweek_picks=player_gameweek_picks,
        group_id=GROUP_ID,
    )


def handler(event, context):
    gameweek = int(event.get("gameweek"))
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute(gameweek))
