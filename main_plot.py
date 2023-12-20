import asyncio
from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials
from services import FPLService, PlotService
from config import Config
from adapter import GoogleSheet, S3Uploader


async def main() -> None:
    # initialize config
    config = Config.initialize("./config.json")

    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    google_sheet = GoogleSheet(credential=credential)
    google_sheet = google_sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(config=config, google_sheet=google_sheet)
    sess = Session()
    s3_uploader = S3Uploader(session=sess, bucket="ds-fpl")
    plot_service = PlotService(fpl_service=fpl_service, s3_uploader=s3_uploader)
    urls = await plot_service.generate_overall_gameweeks_plot(1, 16)
    for url in urls:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
