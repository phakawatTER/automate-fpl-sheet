import asyncio
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials
import adapter
import services
from config import Config
from services import message_template
from line import LineBot


async def main() -> None:
    credential = ServiceAccountCredentials.from_json_keyfile_name(
        "./service_account.json"
    )
    config = Config("./config.json")
    sheet = adapter.GoogleSheet(credential=credential)
    sheet = sheet.open_sheet_by_url(config.sheet_url)

    fpl_adapter = adapter.FPLAdapter(config.league_id, config.cookies)
    element_id = 85
    gameweek = 17
    player_history = await fpl_adapter.get_player_gameweek_info(
        gameweek=gameweek, player_id=element_id
    )
    bootstrap_data = await fpl_adapter.get_bootstrap()
    logger.info(bootstrap_data)
    logger.info(player_history)
    element = None
    for el in bootstrap_data.elements:
        if el.id == element_id:
            element = el.web_name
    logger.info(element)

    fpl_service = services.FPLService(google_sheet=sheet, config=config)
    picks = await fpl_service.list_player_gameweek_picks(gameweek=gameweek)
    logger.info(picks)

    messages = []
    for pick in picks:
        message = message_template.PlayerGameweekPickMessage(
            gameweek=gameweek, player_data=pick
        ).build()
        messages.append(message)

    step_size = 8
    for i in range(0, len(messages), step_size):
        j = i + step_size
        if j > len(messages):
            j = len(messages)
        message = message_template.CarouselMessage(messages=messages[i:j]).build()
        bot = LineBot(config=config)
        bot.send_flex_message(
            group_id="C44a80181a9d0ded2f6c3093adbbd6a8a",
            flex_message=message,
            alt_text="test",
        )


if __name__ == "__main__":
    asyncio.run(main())
