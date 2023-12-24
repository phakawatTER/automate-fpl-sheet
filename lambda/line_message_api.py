# pylint: disable=wrong-import-position
import sys
import os
import awsgi

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from api import LineMessageAPI
from app import App


def handler(event, context):
    app = App()
    app = LineMessageAPI(app=app).initialize()
    return awsgi.response(app, event, context)
