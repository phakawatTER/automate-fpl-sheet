import argparse
import asyncio
from loguru import logger
from app import App


GROUP_ID = "C44a80181a9d0ded2f6c3093adbbd6a8a"


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
        raise Exception("invalid gameweek value")
    if gameweek < 1 or gameweek > 38:
        raise Exception("invalid gameweek value. should be in range 1-38")

    logger.info(f"processing gameweek {gameweek}")
    app = App()
    league_ids = app.firebase_repo.list_leagues_by_line_group_id(group_id=GROUP_ID)
    league_id = league_ids[0]
    event_status = await app.fpl_service.get_gameweek_event_status(gameweek=gameweek)
    players = await app.fpl_service.get_or_update_fpl_gameweek_table(
        gameweek,
        league_id=league_id,
        ignore_cache=True,
    )
    app.message_service.send_gameweek_result_message(
        gameweek=gameweek,
        event_status=event_status,
        group_id=GROUP_ID,
        players=players,
    )

    app.message_service.send_gameweek_result_message(
        gameweek=gameweek,
        players=players,
        group_id=GROUP_ID,
        event_status=None,
    )

    player_picks = await app.fpl_service.list_player_gameweek_picks(
        gameweek=gameweek, league_id=league_id
    )
    app.message_service.send_carousel_players_gameweek_picks(
        gameweek=gameweek,
        player_gameweek_picks=player_picks,
        group_id=GROUP_ID,
    )

    fixtures = await app.fpl_service.list_gameweek_fixtures(gameweek=gameweek)
    app.message_service.send_gameweek_fixtures_message(
        group_id=GROUP_ID,
        fixtures=fixtures,
        gameweek=gameweek,
    )


if __name__ == "__main__":
    asyncio.run(main())
