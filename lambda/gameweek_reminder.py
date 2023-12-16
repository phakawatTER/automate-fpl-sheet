import os
import sys
from datetime import timedelta,datetime

from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from services import FPLService,MessageService
from adapter import S3Downloader,GoogleSheet
from config import Config
from models import MatchFixture



def handler(_event,_context):
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
    current_gameweek = gw_status.event
    current_gameweek_fixtures = fpl_service.list_gameweek_fixtures(gameweek=current_gameweek)
    earliest_match:MatchFixture = None
    for fixture in current_gameweek_fixtures:
        if earliest_match is None:
            earliest_match = fixture
        elif fixture.kickoff_time < earliest_match.kickoff_time:
            earliest_match = fixture
    time_to_subtract = timedelta(hours=5)
    time_to_remind = earliest_match.kickoff_time - time_to_subtract
    now = datetime.utcnow()
    should_remind = now >= time_to_remind

    worksheet = google_sheet.open_worksheet_from_default_sheet(config.worksheet_name)
    # L:37
    cell_value = worksheet.cell(37,10).numeric_value
    if current_gameweek != cell_value and should_remind:
        message_service = MessageService(config)
        # NOTE: group_id should be fetched from database
        message_service.send_gameweek_reminder_message(game_week=current_gameweek,group_id="C44a80181a9d0ded2f6c3093adbbd6a8a")
        worksheet.update_cell(37,10,current_gameweek)
        
if __name__ == "__main__":
    handler(None,None)
