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
    fpl_current_gameweek = gw_status.event + 1
    system_current_gameweek = app.fpl_service.get_current_gameweek_from_dynamodb()

    if system_current_gameweek >= fpl_current_gameweek:
        return

    next_gameweek = system_current_gameweek + 1
    # end of season do nothing
    if next_gameweek > 38:
        return

    next_gameweek_fixtures = await app.fpl_service.list_gameweek_fixtures(
        gameweek=next_gameweek
    )
    earliest_match: FPLMatchFixture = None
    for fixture in next_gameweek_fixtures:
        if earliest_match is None:
            earliest_match = fixture
        elif fixture.kickoff_time < earliest_match.kickoff_time:
            earliest_match = fixture

    time_to_subtract = timedelta(
        hours=16
    )  # should remind 8 hours before the first match of gameweek
    time_to_remind = earliest_match.kickoff_time - time_to_subtract
    now = datetime.utcnow().astimezone()
    should_update_gameweek = now >= time_to_remind

    if should_update_gameweek:
        line_group_ids = app.firebase_repo.list_line_channels()
        for group_id in line_group_ids:
            app.message_service.send_gameweek_fixtures_message(
                group_id=group_id,
                fixtures=next_gameweek_fixtures,
                gameweek=next_gameweek,
            )
            app.message_service.send_gameweek_reminder_message(
                gameweek=next_gameweek,
                group_id=group_id,
            )
        app.fpl_service.update_gameweek(gameweek=next_gameweek)
        # notify line-up flex message when the first match of gameweek is played
        time_to_remind = earliest_match.kickoff_time
        time_to_remind = time_to_remind.replace(microsecond=0)
        app.sfn.start_execution(
            state_machine_arn=LINE_UP_STATEMACHINE_ARN,
            input_data={
                "gameweek": next_gameweek,
                "timeToNotify": time_to_remind.isoformat(),
            },
        )


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute())


if __name__ == "__main__":
    asyncio.run(execute())
