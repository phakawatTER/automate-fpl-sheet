import asyncio
from typing import List
from loguru import logger

from app import App


async def execute(event: dict) -> List[str]:
    app = App()
    start_gw: int = event.get("start_gw")
    end_gw: int = event.get("end_gw")
    league_id: int = event.get("league_id")

    urls = await app.plot_service.generate_overall_gameweeks_plot(
        start_gw,
        end_gw,
        league_id,
    )

    for url in urls:
        logger.success(url)

    return urls


def handler(event, context):
    loop = asyncio.get_event_loop()
    urls = loop.run_until_complete(execute(event))

    return urls


if __name__ == "__main__":
    asyncio.run(execute({"start_gw": 1, "end_gw": 16}))
