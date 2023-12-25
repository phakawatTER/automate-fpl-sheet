import os
import sys
import asyncio
from datetime import timedelta, datetime

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from models import FPLMatchFixture
from app import App

LINE_UP_STATEMACHINE_ARN = "arn:aws:states:ap-southeast-1:661296166047:stateMachine:FPLLineUpNotificationStateMachine"


async def execute():
    app = App()
    gw_status = await app.fpl_service.get_current_gameweek()
    current_gameweek = gw_status.event
    current_gameweek_fixtures = await app.fpl_service.list_gameweek_fixtures(
        gameweek=current_gameweek
    )
    earliest_match: FPLMatchFixture = None
    for fixture in current_gameweek_fixtures:
        if earliest_match is None:
            earliest_match = fixture
        elif fixture.kickoff_time < earliest_match.kickoff_time:
            earliest_match = fixture
    time_to_subtract = timedelta(
        hours=8
    )  # should remind 8 hours before the first match of gameweek
    time_to_remind = earliest_match.kickoff_time - time_to_subtract
    now = datetime.utcnow().astimezone()
    should_remind = now >= time_to_remind
    latest_gameweek = app.fpl_service.get_current_gameweek_from_dynamodb()
    if current_gameweek != latest_gameweek and should_remind:
        line_group_ids = app.firebase_repo.list_line_channels()
        for group_id in line_group_ids:
            app.message_service.send_gameweek_reminder_message(
                gameweek=current_gameweek,
                group_id=group_id,
            )
        app.fpl_service.update_gameweek(gameweek=current_gameweek)
        # notify line-up flex message when the first match of gameweek is played
        time_to_remind = earliest_match.kickoff_time
        time_to_remind = time_to_remind.replace(microsecond=0)
        app.sfn.start_execution(
            state_machine_arn=LINE_UP_STATEMACHINE_ARN,
            input_data={
                "gameweek": current_gameweek,
                "timeToNotify": time_to_remind.isoformat(),
            },
        )


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute())


if __name__ == "__main__":
    asyncio.run(execute())
