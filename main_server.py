from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials
from config import Config
from api import LineMessageAPI
from adapter import GoogleSheet
from services import MessageService, FPLService

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    sheet = GoogleSheet(credential=credential)
    sheet = sheet.open_sheet_by_url(config.sheet_url)
    fpl_service = FPLService(config=config, google_sheet=sheet)
    message_service = MessageService(config=config)
    sess = Session()
    line_message_api = LineMessageAPI(
        config=config,
        fpl_service=fpl_service,
        message_service=message_service,
    )
    app = line_message_api.initialize()
    app.run(port=5100, debug=True)
