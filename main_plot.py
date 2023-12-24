import asyncio
from app import App


async def main() -> None:
    app = App()
    urls = await app.plot_service.generate_overall_gameweeks_plot(1, 16)
    for url in urls:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
