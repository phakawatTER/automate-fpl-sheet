from http import HTTPStatus
from urllib.parse import urljoin
from typing import List, Optional
import httpx
from models import (
    H2HResponse,
    FantasyTeam,
    PlayerData,
    PlayerHistory,
    FPLLeagueStandings,
    FPLEventStatusResponse,
    MatchFixture,
    H2HData,
    Pick,
    EntryHistory,
    PlayerSeasonHistory,
    FPLTeamStanding,
    FPLEventStatus,
    BootstrapGameweek,
    Bootstrap,
    BootstrapElement,
)
import util


class FPLError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def error(self):
        return self.message


class FPLAdapter:
    BASE_URL = "https://fantasy.premierleague.com"
    TIMEOUT = 10

    def __init__(self, league_id: int, cookies: str):
        self.__cookies = cookies
        self.__league_id = league_id

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
    def get_element_image_url(element_code: str, width: int = 110, height: int = 140):
        return f"https://resources.premierleague.com/premierleague/photos/players/{width}x{height}/p{element_code}.png"

    # TODO: need to create dataclass for the response so we got type hint
    @util.time_track(description="Get FPL Bootstrap")
    async def get_bootstrap(self):
        url = urljoin(FPLAdapter.BASE_URL, "/api/bootstrap-static")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        bootstrap = Bootstrap(
            events=[BootstrapGameweek(**d) for d in data.get("events")],
            elements=[BootstrapElement(**d) for d in data.get("elements")],
        )
        return bootstrap

    @util.time_track(description="FPLAdapter.get_gameweek_event_status")
    async def get_gameweek_event_status(self):
        url = urljoin(FPLAdapter.BASE_URL, "/api/event-status")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()

        return FPLEventStatusResponse(
            leagues=data.get("leagues"),
            status=[FPLEventStatus(**d) for d in data.get("status")],
        )

    @util.time_track(description="FPLAdapter.get_h2h_league_standing")
    async def get_h2h_league_standing(self):
        url = urljoin(
            FPLAdapter.BASE_URL,
            f"/api/leagues-h2h/{self.__league_id}/standings/?page_new_entries=1&page_standings=1",
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()

        return FPLLeagueStandings(
            league_id=data.get("league").get("id"),
            league_name=data.get("league").get("name"),
            standings=[
                FPLTeamStanding(**d) for d in data.get("standings").get("results")
            ],
        )

    @util.time_track(description="FPLAdapter.get_h2h_results")
    async def get_h2h_results(self, gameweek: int):
        url = urljoin(
            FPLAdapter.BASE_URL,
            f"/api/leagues-h2h-matches/league/{self.__league_id}/?page=1&event={gameweek}",
        )
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )

        data = response.json()

        return H2HResponse(
            has_next=data.get("has_next"),
            page=data.get("page"),
            results=[H2HData(**d) for d in data.get("results")],
        )

    @util.time_track(description="FPLAdapter.get_player_gameweek_info")
    async def get_player_gameweek_info(
        self, gameweek: int, player_id: int
    ) -> Optional[PlayerHistory]:
        url = urljoin(FPLAdapter.BASE_URL, f"/api/element-summary/{player_id}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: dict = response.json()
        player_data = PlayerData(
            history=[PlayerHistory(**d) for d in data.get("history")],
            history_past=[PlayerSeasonHistory(**d) for d in data.get("history_past")],
        )
        history: PlayerHistory = None
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
        return FantasyTeam(
            active_chip=data.get("active_chip"),
            automatic_subs=data.get("automatic_subs"),
            entry_history=EntryHistory(**data.get("entry_history")),
            picks=[Pick(**d) for d in data.get("picks")],
        )

    @util.time_track(description="FPLAdapter.list_gameweek_fixtures")
    async def list_gameweek_fixtures(self, gameweek: int) -> List[MatchFixture]:
        url = urljoin(FPLAdapter.BASE_URL, f"/api/fixtures?event={gameweek}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(
                f"unexpected http status code: {response.status_code} with response data: {response.content}"
            )
        data: List[dict] = response.json()
        results = [MatchFixture(**d) for d in data]
        return results
