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
from adapter import S3Downloader

IS_INIT = False
CONFIG: Config
CREDENTIAL: ServiceAccountCredentials


def _init():
    global CONFIG, CREDENTIAL, IS_INIT
    sess = Session()
    s3_downloader = S3Downloader(sess, "ds-fpl", "/tmp")
    file_path = s3_downloader.download_file_from_default_bucket("config.json")
    CONFIG = Config(file_path)
    file_path = s3_downloader.download_file_from_default_bucket("service_account.json")
    CREDENTIAL = ServiceAccountCredentials.from_json_keyfile_name(file_path)
    IS_INIT = True


def handler(event, context):
    if not IS_INIT:
        _init()

    app = LineMessageAPI(config=CONFIG, credential=CREDENTIAL).initialize()
    return awsgi.response(app, event, context)
