# pylint: disable=wrong-import-position
import sys
import os
import awsgi

root_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.dirname(root_directory)
sys.path.append(project_directory)

from api import LineMessageAPI
from app import App

_APP = None


def handler(event, context):
    global _APP
    if _APP is None:
        _APP = App()
    app = LineMessageAPI(app=_APP).initialize()
    return awsgi.response(app, event, context)
