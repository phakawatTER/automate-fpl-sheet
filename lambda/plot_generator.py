import os
import sys
import asyncio
from typing import List

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from loguru import logger
from boto3.session import Session

import models
from plot import Service as PlotService
from adapter import S3Uploader

SESSION = Session()
S3_UPLOADER = S3Uploader(session=SESSION, bucket="ds-fpl")


def execute(event: dict) -> List[str]:
    start_gw: int = event.get("start_gw")
    end_gw: int = event.get("end_gw")
    data: list[list[models.PlayerGameweekData]] = []
    for gameweek_data in event.get("gameweeks_data"):
        g = [models.PlayerGameweekData(**d) for d in gameweek_data]
        data.append(g)
    plot_service = PlotService(S3_UPLOADER)
    urls = plot_service.generate_overall_gameweeks_plot(
        from_gameweek=start_gw,
        to_gameweek=end_gw,
        gameweeks_data=data,
    )

    for url in urls:
        logger.success(url)

    return urls


def handler(event, context):
    urls = execute(event)

    return urls


if __name__ == "__main__":
    asyncio.run(execute({"start_gw": 1, "end_gw": 16}))
