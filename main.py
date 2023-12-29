import asyncio
from app import App

GROUP_ID = "C44a80181a9d0ded2f6c3093adbbd6a8a"
GAMEWEEK = 17


async def main() -> None:
    app = App()

    gameweek_fixtures = await app.fpl_service.list_gameweek_fixtures(gameweek=20)
    app.message_service.send_gameweek_fixtures_message(
        group_id=GROUP_ID,
        fixtures=gameweek_fixtures,
        gameweek=20,
    )


if __name__ == "__main__":
    asyncio.run(main())
