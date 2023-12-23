import asyncio
import json
from oauth2client.service_account import ServiceAccountCredentials
import adapter
import services
from config import Config
from services import message_template
from line import LineBot

GROUP_ID = "C44a80181a9d0ded2f6c3093adbbd6a8a"


async def main() -> None:
    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    config = Config("./config.json")
    sheet = adapter.GoogleSheet(credential=credential)
    sheet = sheet.open_sheet_by_url(config.sheet_url)

    gameweek = 18
    bot = LineBot(config=config)

    fpl_service = services.FPLService(google_sheet=sheet, config=config)
    picks = await fpl_service.list_player_gameweek_picks(gameweek=gameweek)
    messages = []
    for p in picks[:1]:
        message = message_template.PlayerGameweekPickMessageV2(
            player_picks=p, gameweek=gameweek
        ).build()
        messages.append(message)
        print(json.dumps(message, indent=4))
    message = message_template.CarouselMessage(messages=messages)
    bot.send_flex_message(group_id=GROUP_ID, flex_message=message.build())


if __name__ == "__main__":
    asyncio.run(main())
