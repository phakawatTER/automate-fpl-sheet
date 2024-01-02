import os
import sys
import asyncio

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from app import App

_APP = None


async def execute(gameweek: int):
    global _APP
    if _APP is None:
        _APP = App()
    app = _APP
    group_ids = app.firebase_repo.list_line_channels()
    for group_id in group_ids:
        league_id = app.firebase_repo.list_leagues_by_line_group_id(group_id)[0]
        player_gameweek_picks = await app.fpl_service.list_player_gameweek_picks(
            gameweek=gameweek,
            league_id=league_id,
        )
        app.message_service.send_carousel_players_gameweek_picks(
            gameweek=gameweek,
            player_gameweek_picks=player_gameweek_picks,
            group_id=group_id,
        )


def handler(event, context):
    gameweek = int(event.get("gameweek"))
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute(gameweek))
