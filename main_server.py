import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from config import Config
from api import LineMessageAPI

if __name__ == "__main__":
    config = Config.initialize("./config.json")
    credential = ServiceAccountCredentials.from_json_keyfile_name("./service_account.json")
    line_message_api = LineMessageAPI(config,credential=credential)
    group_id = "C44a80181a9d0ded2f6c3093adbbd6a8a"
    asyncio.run(line_message_api.handle_update_fpl_table(game_week=17,group_id=group_id))    
    # app = line_message_api.initialize()
    # app.run(port=5100)
