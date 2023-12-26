import asyncio
import models
from app import App
from plot import Service as PlotService


async def main() -> None:
    app = App()
    channel_id = app.firebase_repo.list_line_channels()[0]
    league_id = app.firebase_repo.list_leagues_by_line_group_id(channel_id)
    data: list[list[models.PlayerGameweekData]] = []
    start_gw = 1
    end_gw = 17
    for gw in range(start_gw, end_gw + 1, 1):
        gameweek_data = await app.fpl_service.get_or_update_fpl_gameweek_table(
            gw,
            league_id,
        )
        data.append(gameweek_data)
    plot_service = PlotService(app.s3_uploader)
    urls = plot_service.generate_overall_gameweeks_plot(
        from_gameweek=start_gw,
        to_gameweek=end_gw,
        gameweeks_data=data,
    )
    for url in urls:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
