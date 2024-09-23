from http import HTTPStatus
from typing import List, Optional
import httpx
import models
import util


class FPLError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def error(self):
        return self.message


def urljoin(base, path):
    return base + path


class FPLAdapter:
    BASE_URL = "https://fantasy.premierleague.com"
    TIMEOUT = 10

    def __init__(self, cookies: str):
        self.__cookies = cookies

    async def __get_request(self, url: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"cookies": self.__cookies},
                timeout=FPLAdapter.TIMEOUT,
                follow_redirects=True,
            )
            return response

    @staticmethod
    def get_team_badge_image_url(team_code: str):
        return f"https://resources.premierleague.com/premierleague/badges/70/t{team_code}.png"

    @staticmethod
    def get_element_image_url(element_code: str, width: int = 110, height: int = 140):
        return f"https://resources.premierleague.com/premierleague/photos/players/{width}x{height}/p{element_code}.png"

    @util.time_track(description="Get FPL Bootstrap")
    async def get_bootstrap(self):
        url = urljoin(FPLAdapter.BASE_URL, "/api/bootstrap-static")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        bootstrap = models.Bootstrap(
            events=[models.BootstrapGameweek(**d) for d in data.get("events")],
            elements=[models.BootstrapElement(**d) for d in data.get("elements")],
            teams=[models.BootstrapTeam(**d) for d in data.get("teams")],
        )
        return bootstrap

    @util.time_track(description="")
    async def get_league_entries(self, league_id: int) -> List[models.FPLLeagueEntry]:
        url = urljoin(FPLAdapter.BASE_URL, f"/api/league/{league_id}/entries")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data = response.json()
        return [models.FPLLeagueEntry(**d) for d in data]

    @util.time_track(description="FPLAdapter.get_gameweek_event_status")
    async def get_gameweek_event_status(self):
        url = urljoin(FPLAdapter.BASE_URL, "/api/event-status")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()

        return models.FPLEventStatusResponse(
            leagues=data.get("leagues"),
            status=[models.FPLEventStatus(**d) for d in data.get("status")],
        )

    @util.time_track(description="FPLAdapter.get_h2h_league_standing")
    async def get_h2h_league_standing(self, league_id: int):
        url = urljoin(
            FPLAdapter.BASE_URL,
            f"/api/leagues-h2h/{league_id}/standings/?page_new_entries=1&page_standings=1",
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()

        return models.FPLLeagueStandings(
            league_id=data.get("league").get("id"),
            league_name=data.get("league").get("name"),
            standings=[
                models.FPLTeamStanding(**d)
                for d in data.get("standings").get("results")
            ],
        )

    async def get_classic_league_standings(self, league_id: int):
        url = urljoin(
            FPLAdapter.BASE_URL,
            f"/api/leagues-classic/{league_id}/standings",
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        standings = data.get("standings")
        return models.FPLClassicLeagueStandingData(
            league=models.FPLClassicLeagueInfo(**data.get("league")),
            standings=models.FPLClassicLeagueStandings(
                has_next=standings.get("has_next"),
                page=standings.get("page"),
                results=[
                    models.FPLClassicLeagueStandingResult(**d)
                    for d in standings.get("results")
                ],
            ),
        )

    @util.time_track(description="FPLAdapter.get_h2h_results")
    async def get_h2h_results(self, gameweek: int, league_id: int):
        url = urljoin(
            FPLAdapter.BASE_URL,
            f"/api/leagues-h2h-matches/league/{league_id}/?page=1&event={gameweek}",
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )

        data = response.json()

        return models.FPLH2HResponse(
            has_next=data.get("has_next"),
            page=data.get("page"),
            results=[models.FPLH2HData(**d) for d in data.get("results")],
        )

    @util.time_track(description="FPLAdapter.get_player_gameweek_picks")
    async def get_player_gameweek_picks(self, gameweek: int, player_id: int):
        url = urljoin(
            FPLAdapter.BASE_URL, f"/api/entry/{player_id}/event/{gameweek}/picks/"
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data = response.json()

        return models.FPLPlayerGameweekPicksData(
            active_chip=data.get("active_chip"),
            entry_history=models.FPLPlayerGameweekPickEntryHistory(
                **data.get("entry_history"),
            ),
            picks=[models.FPLPlayerGameweekPick(**d) for d in data.get("picks")],
        )

    @util.time_track(description="FPLAdapter.get_player_gameweek_info")
    async def get_player_gameweek_info(
        self, gameweek: int, player_id: int
    ) -> Optional[models.FPLPlayerHistory]:
        url = urljoin(FPLAdapter.BASE_URL, f"/api/element-summary/{player_id}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        player_data = models.FPLPlayerData(
            history=[models.FPLPlayerHistory(**d) for d in data.get("history")],
            history_past=[
                models.FPLPlayerSeasonHistory(**d) for d in data.get("history_past")
            ],
        )
        history: models.FPLPlayerHistory = None
        for h in player_data.history:
            if h.round == gameweek:
                history = h
        return history

    @util.time_track(description="FPLAdapter.get_player_team_by_id")
    async def get_player_team_by_id(self, player_id: int, gameweek: int):
        url = urljoin(
            FPLAdapter.BASE_URL, f"/api/entry/{player_id}/event/{gameweek}/picks"
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        return models.FPLFantasyTeam(
            active_chip=data.get("active_chip"),
            automatic_subs=data.get("automatic_subs"),
            entry_history=models.FPLEntryHistory(**data.get("entry_history")),
            picks=[models.FPLPick(**d) for d in data.get("picks")],
        )

    @util.time_track(description="FPLAdapter.list_gameweek_fixtures")
    async def list_gameweek_fixtures(
        self, gameweek: int
    ) -> List[models.FPLMatchFixture]:
        url = urljoin(FPLAdapter.BASE_URL, f"/api/fixtures?event={gameweek}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: List[dict] = response.json()
        results = [models.FPLMatchFixture(**d) for d in data]
        return results

    @util.time_track(description="FPLAdapter.get_gameweek_live_score")
    async def get_gameweek_live_event(self, gameweek: int):
        url = urljoin(FPLAdapter.BASE_URL, f"/api/event/{gameweek}/live")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        return models.FPLLiveEventResponse.create_from_dict(data=data.get("elements"))
