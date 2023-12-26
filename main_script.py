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
    players = await app.fpl_service.get_or_update_fpl_gameweek_table(
        gameweek,
        league_id=league_id,
        ignore_cache=True,
    )
    for p in players:
        logger.info(p)

    player_revs = await app.fpl_service.list_players_revenues(league_id)
    for p_rev in player_revs:
        logger.info(p_rev)

    player_picks = await app.fpl_service.list_player_gameweek_picks(
        gameweek=gameweek, league_id=league_id
    )
    for pick in player_picks:
        logger.info(pick)


if __name__ == "__main__":
    asyncio.run(main())
