import sys
import os
import awsgi
from boto3.session import Session

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from config import Config
from api import LineMessageAPI
from adapter import S3Downloader

def handler(event,context):
    print(event)
    print(context)
    sess = Session()
    s3_downloader = S3Downloader(sess,"ds-fpl","/tmp")
    s3_downloader.download_file_from_default_bucket("config.json")
    s3_downloader.download_file_from_default_bucket("service_account.json")
    config = Config("/tmp/config.json")
    app = LineMessageAPI(config=config).initialize()
    return awsgi.response(app,event,context)


