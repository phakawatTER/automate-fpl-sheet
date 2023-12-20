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


async def execute():
    sess = Session()
    s3_downloader = S3Downloader(sess, "ds-fpl", "/tmp")

    file_path = s3_downloader.download_file("config.json")
    config = Config(file_path)

    file_path = s3_downloader.download_file("service_account.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(google_sheet=google_sheet, config=config)
    gw_status = await fpl_service.get_current_gameweek()
    players = await fpl_service.get_or_update_fpl_gameweek_table(gw_status.event)

    message_service = MessageService(config=config)
    # NOTE: group_id here should be fetched from database. hardcode it for now
    message_service.send_gameweek_result_message(
        gw_status.event, players, group_id="C6402ad4c1937733c7db4e3ff7181287c"
    )

    return 0


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute())
