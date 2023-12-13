import os
import sys
from datetime import datetime, timezone


from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from services import FPLService,MessageService
from adapter import S3Downloader,GoogleSheet
from config import Config,TIMEZONE



def handler(_event,_context):
    current_time = datetime.now(timezone.utc).astimezone(TIMEZONE)
    if current_time.hour != 15:
        return

    sess = Session()
    s3_downloader = S3Downloader(sess,"ds-fpl","/tmp")

    file_path = s3_downloader.download_file("config.json")
    config = Config(file_path)

    file_path = s3_downloader.download_file("service_account.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(google_sheet=google_sheet,config=config)
    gw_status = fpl_service.get_current_gameweek()

    worksheet = google_sheet.open_worksheet_from_default_sheet(config.worksheet_name)
    # L:37
    cell_value = worksheet.cell(37,10).numeric_value
    if gw_status.event != cell_value:
        message_service = MessageService(config)
        # NOTE: group_id should be fetched from database
        message_service.send_gameweek_reminder_message(game_week=gw_status.event,group_id="C6402ad4c1937733c7db4e3ff7181287c")
        worksheet.update_cell(37,10,gw_status.event)
