import asyncio
from services import message_template
from app import App

GROUP_ID = "C44a80181a9d0ded2f6c3093adbbd6a8a"
GAMEWEEK = 17


async def main() -> None:
    app = App()
    data = app.firebase_repo.list_leagues_by_line_group_id(GROUP_ID)
    channel_ids = app.firebase_repo.list_line_channels()
    print(channel_ids)
    picks = await app.fpl_service.list_player_gameweek_picks(
        gameweek=GAMEWEEK,
        league_id=data[0],
    )
    messages = []
    for p in picks[:4]:
        message = message_template.PlayerGameweekPickMessageV2(
            player_picks=p, gameweek=GAMEWEEK
        ).build()
        messages.append(message)
    message = message_template.CarouselMessage(messages=messages)

    app.linebot.send_flex_message(group_id=GROUP_ID, flex_message=message.build())


if __name__ == "__main__":
    asyncio.run(main())
