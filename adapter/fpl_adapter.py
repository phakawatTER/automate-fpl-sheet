from http import HTTPStatus
from urllib.parse import urljoin
from typing import List
import httpx
from models import H2HResponse,FantasyTeam,PlayerData,PlayerHistory,FPLLeagueStandings,FPLEventStatusResponse,MatchFixture
import util

class FPLError(Exception):
    def __init__(self,message:str):
        super().__init__(message)
        self.message = message

    def error(self):
        return self.message

class FPLAdapter:

    BASE_URL="https://fantasy.premierleague.com"
    TIMEOUT=10

    def __init__(self,league_id:int,cookies:str):
        self.cookies = cookies
        self.league_id = league_id
        
    async def __get_request(self,url:str):
        async with  httpx.AsyncClient() as client:
            response = await client.get(url,params={"cookies": self.cookies},timeout=FPLAdapter.TIMEOUT,follow_redirects=True)
            return response
    
    @util.time_track(description="FPLAdapter.get_gameweek_event_status")
    async def get_gameweek_event_status(self):
        url = urljoin(FPLAdapter.BASE_URL,"/api/event-status")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")
        data:dict = response.json()
        
        return FPLEventStatusResponse(status=data.get("status"),leagues=data.get("leagues"))
        
    @util.time_track(description="FPLAdapter.get_h2h_league_standing")
    async def get_h2h_league_standing(self):
        url = urljoin(FPLAdapter.BASE_URL,f"/api/leagues-h2h/{self.league_id}/standings/?page_new_entries=1&page_standings=1")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")
        data:dict = response.json()
        
        return FPLLeagueStandings(
            league_id=data.get("league").get("id"),
            league_name=data.get("league").get("name"),
            standings=data.get("standings").get("results")
        )
        
    @util.time_track  (description="FPLAdapter.get_h2h_results")
    async def get_h2h_results(self,game_week:int):
        url = urljoin(FPLAdapter.BASE_URL,f"/api/leagues-h2h-matches/league/{self.league_id}/?page=1&event={game_week}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")
        
        return H2HResponse(response=response.json())
    
    @util.time_track(description="FPLAdapter.get_player_gameweek_info")
    async def get_player_gameweek_info(self,game_week:int,player_id:int):
        url = urljoin(FPLAdapter.BASE_URL,f"/api/element-summary/{player_id}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")
        data:dict = response.json()
        player_data = PlayerData(fixtures=data.get("fixtures"),history=data.get("history"),history_past=data.get("history_past"))
        history: PlayerHistory
        for h in player_data.history:
            if h.round == game_week:
                history = h
        if history is None:
            raise FPLError(f"player data not found on gameweek {game_week}")
        return history
    
    @util.time_track(description="FPLAdapter.get_player_team_by_id")
    async def get_player_team_by_id(self,player_id:int,game_week:int):
        url = urljoin(FPLAdapter.BASE_URL,f"/api/entry/{player_id}/event/{game_week}/picks")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")

        data:dict = response.json()
        return FantasyTeam(
            active_chip=data.get("active_chip"),
            automatic_subs=data.get("automatic_subs"),
            entry_history=data.get("entry_history"),
            picks=data.get("picks"),
        )
        
    @util.time_track  (description="FPLAdapter.list_gameweek_fixtures")
    async def list_gameweek_fixtures(self,gameweek:int)->List[MatchFixture]:
        url = urljoin(FPLAdapter.BASE_URL,f"/api/fixtures?event={gameweek}")
        response = await self.__get_request(url)
        if response.status_code != HTTPStatus.OK:
            raise FPLError(f"unexpected http status code: {response.status_code} with response data: {response.content}")
        data:List[dict] = response.json()
        results:List[MatchFixture] = []
        for d in data:
            fixture = MatchFixture(data=d)
            results.append(fixture)
        return results
