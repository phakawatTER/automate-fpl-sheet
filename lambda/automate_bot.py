import os
import sys
import asyncio

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from app import App


async def execute():
    app = App()
    gw_status = await app.fpl_service.get_current_gameweek()
    line_channel_ids = app.firebase_repo.list_line_channels()
    for group_id in line_channel_ids:
        league_id = app.firebase_repo.list_leagues_by_line_group_id(group_id)[0]
        league_sheet = app.firebase_repo.get_league_google_sheet(league_id)
        players = await app.fpl_service.get_or_update_fpl_gameweek_table(
            gw_status.event,
            league_id,
        )
        app.message_service.send_gameweek_result_message(
            gw_status.event,
            players,
            group_id=group_id,
            sheet_url=league_sheet.url,
        )

    return 0


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute())
