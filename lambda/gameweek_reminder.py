import os
import sys
import asyncio
from datetime import timedelta, datetime, timezone

from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from services import FPLService, MessageService
from adapter import S3Downloader, GoogleSheet, StateMachine
from config import Config
from models import MatchFixture


GROUP_ID = "C6402ad4c1937733c7db4e3ff7181287c"
LINE_UP_STATEMACHINE_ARN = "arn:aws:states:ap-southeast-1:661296166047:stateMachine:FPLLineUpNotificationStateMachine"


async def execute():
    sess = Session()
    s3_downloader = S3Downloader(sess, "ds-fpl", "/tmp")
    sfn = StateMachine(session=sess)

    file_path = s3_downloader.download_file("config.json")
    config = Config(file_path)

    file_path = s3_downloader.download_file("service_account.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(google_sheet=google_sheet, config=config)
    gw_status = await fpl_service.get_current_gameweek()
    current_gameweek = gw_status.event
    current_gameweek_fixtures = await fpl_service.list_gameweek_fixtures(
        gameweek=current_gameweek
    )
    earliest_match: MatchFixture = None
    for fixture in current_gameweek_fixtures:
        if earliest_match is None:
            earliest_match = fixture
        elif fixture.kickoff_time < earliest_match.kickoff_time:
            earliest_match = fixture
    time_to_subtract = timedelta(hours=5)
    time_to_remind = earliest_match.kickoff_time - time_to_subtract
    now = datetime.utcnow()
    should_remind = now >= time_to_remind

    latest_gameweek = fpl_service.get_current_gameweek_from_dynamodb()

    if current_gameweek != latest_gameweek and should_remind:
        message_service = MessageService(config)
        message_service.send_gameweek_reminder_message(
            gameweek=current_gameweek, group_id=GROUP_ID
        )

        fpl_service.update_gameweek(gameweek=current_gameweek)

        time_to_remind = earliest_match.kickoff_time - timedelta(hours=2)
        time_to_remind = time_to_remind.replace(microsecond=0, tzinfo=timezone.utc)
        sfn.start_execution(
            state_machine_arn=LINE_UP_STATEMACHINE_ARN,
            input_data={
                "gameweek": current_gameweek,
                "timeToNotify": time_to_remind.isoformat(),
            },
        )


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute())
