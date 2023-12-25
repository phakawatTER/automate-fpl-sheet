import asyncio
from app import App


async def main() -> None:
    app = App()
    channel_id = app.firebase_repo.list_line_channels()[0]
    league_id = app.firebase_repo.list_leagues_by_line_group_id(channel_id)

    urls = await app.plot_service.generate_overall_gameweeks_plot(
        from_gameweek=1,
        to_gameweek=16,
        league_id=league_id,
    )
    for url in urls:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
