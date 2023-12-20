# pylint: disable=wrong-import-position
import sys
import os
import awsgi
from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from config import Config
from api import LineMessageAPI
from adapter import S3Downloader, GoogleSheet, S3Uploader
from services import FPLService, MessageService

IS_INIT = False
CONFIG: Config
CREDENTIAL: ServiceAccountCredentials
SESSION: Session


def _init():
    global CONFIG, CREDENTIAL, IS_INIT, SESSION
    SESSION = Session()
    s3_downloader = S3Downloader(SESSION, "ds-fpl", "/tmp")
    file_path = s3_downloader.download_file_from_default_bucket("config.json")
    CONFIG = Config(file_path)
    file_path = s3_downloader.download_file_from_default_bucket("service_account.json")
    CREDENTIAL = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    IS_INIT = True


def handler(event, context):
    if not IS_INIT:
        _init()

    sheet = GoogleSheet(credential=CREDENTIAL)
    sheet = sheet.open_sheet_by_url(CONFIG.sheet_url)
    fpl_service = FPLService(config=CONFIG, google_sheet=sheet)
    message_service = MessageService(config=CONFIG)

    app = LineMessageAPI(
        fpl_service=fpl_service,
        message_service=message_service,
        config=CONFIG,
    ).initialize()
    return awsgi.response(app, event, context)
