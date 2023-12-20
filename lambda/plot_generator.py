import asyncio
from typing import List
from boto3.session import Session
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials
from services import FPLService, PlotService
from config import Config
from adapter import GoogleSheet, S3Uploader, S3Downloader


async def execute(input: dict) -> List[str]:
    start_gw = input.get("start_gw")
    end_gw = input.get("end_gw")

    sess = Session()
    s3_downloader = S3Downloader(sess, "ds-fpl", "/tmp")
    s3_uploader = S3Uploader(session=sess, bucket="ds-fpl")

    file_path = s3_downloader.download_file_from_default_bucket("config.json")
    config = Config(file_path)
    file_path = s3_downloader.download_file_from_default_bucket("service_account.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(file_path)

    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(config=config, google_sheet=google_sheet)

    plot_service = PlotService(fpl_service=fpl_service, s3_uploader=s3_uploader)
    urls = await plot_service.generate_overall_gameweeks_plot(start_gw, end_gw)

    for url in urls:
        logger.success(url)

    return urls


def handler(event, context):
    loop = asyncio.get_event_loop()
    urls = loop.run_until_complete(execute(event))

    return urls


if __name__ == "__main__":
    asyncio.run(execute({"start_gw": 1, "end_gw": 16}))
