from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union
from datetime import datetime, timezone, date
from .bootstrap import BootstrapTeam
import util


@dataclass
class FPLH2HResponse:
    has_next: bool
    page: int
    results: List["FPLH2HData"]


@dataclass
class FPLH2HData:
    id: int
    entry_1_entry: int
    entry_1_name: str
    entry_1_player_name: str
    entry_1_points: int
    entry_1_win: int
    entry_1_draw: int
    entry_1_loss: int
    entry_1_total: int
    entry_2_entry: int
    entry_2_name: str
    entry_2_player_name: str
    entry_2_points: int
    entry_2_win: int
    entry_2_draw: int
    entry_2_loss: int
    entry_2_total: int
    is_knockout: bool
    league: str
    winner: str
    seed_value: int
    event: str
    tiebreak: str
    is_bye: bool
    knockout_name: str


@dataclass
class FPLFantasyTeam:
    active_chip: str
    automatic_subs: List[int]
    entry_history: "FPLEntryHistory"
    picks: List["FPLPick"]


@dataclass
class FPLEntryHistory:
    event: int
    points: int
    total_points: int
    rank: int
    rank_sort: int
    overall_rank: int
    bank: int
    value: int
    event_transfers: int
    event_transfers_cost: int
    points_on_bench: int


@dataclass
class FPLPick:
    element: int
    position: int
    multiplier: int
    is_captain: bool
    is_vice_captain: bool


@dataclass
class FPLPlayerData:
    history: List["FPLPlayerHistory"]
    history_past: List["FPLPlayerSeasonHistory"]


@dataclass
class FPLPlayerHistory:
    element: int
    fixture: int
    opponent_team: int
    total_points: int
    was_home: bool
    kickoff_time: str
    team_h_score: int
    team_a_score: int
    round: int
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    starts: int
    expected_goals: float
    expected_assists: float
    expected_goal_involvements: float
    expected_goals_conceded: float
    value: float
    transfers_balance: int
    selected: int
    transfers_in: int
    transfers_out: int


@dataclass
class FPLPlayerSeasonHistory:
    season_name: str
    element_code: int
    start_cost: float
    end_cost: float
    total_points: int
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    starts: int
    expected_goals: float
    expected_assists: float
    expected_goal_involvements: float
    expected_goals_conceded: float


@dataclass
class FPLLeagueStandings:
    league_id: int
    league_name: str
    standings: List["FPLTeamStanding"]


@dataclass
class FPLTeamStanding:
    id: int
    division: int
    entry: Optional[int]
    player_name: str
    rank: int
    last_rank: int
    rank_sort: int
    total: int
    entry_name: str
    matches_played: int
    matches_won: int
    matches_drawn: int
    matches_lost: int
    points_for: int


@dataclass
class FPLEventStatusResponse:
    status: List["FPLEventStatus"]
    leagues: bool = field(default=False)


@dataclass
class FPLEventStatus:
    bonus_added: bool
    date: date
    event: int
    points: float

    def __post_init__(self):
        self.date = (
            self.date
            if isinstance(self.date, datetime)
            else datetime.strptime(self.date, "%Y-%m-%d").date()
        )


@dataclass
class FPLMatchFixture:
    code: int
    event: int
    finished: bool
    finished_provisional: bool
    id: int
    kickoff_time: datetime
    minutes: int
    provisional_start_time: bool
    started: bool
    team_a: int
    team_a_score: int
    team_h: int
    team_h_score: int
    stats: List[Dict[str, Union[str, List[Dict[str, Union[int, str]]]]]]
    team_h_difficulty: int
    team_a_difficulty: int
    pulse_id: int

    team_a_data: Optional[BootstrapTeam] = field(default=None)
    team_h_data: Optional[BootstrapTeam] = field(default=None)

    def __post_init__(self):
        self.kickoff_time = (
            self.kickoff_time
            if isinstance(self.kickoff_time, datetime)
            else datetime.strptime(self.kickoff_time, util.RFC3339_FORMAT).replace(
                tzinfo=timezone.utc
            )
        )


@dataclass
class FPLPlayerStats:
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: str
    creativity: str
    threat: str
    ict_index: str
    starts: int
    expected_goals: str
    expected_assists: str
    expected_goal_involvements: str
    expected_goals_conceded: str
    total_points: int
    in_dreamteam: bool

    @staticmethod
    def create_from_dict(data: dict):
        return FPLPlayerStats(**data)


@dataclass
class FPLLiveEventElement:
    id: int
    stats: FPLPlayerStats
    explain: any

    @staticmethod
    def create_from_dict(data: dict):
        return FPLLiveEventElement(
            id=data.get("id"),
            explain=data.get("explain"),
            stats=FPLPlayerStats.create_from_dict(data=data.get("stats")),
        )


@dataclass
class FPLLiveEventResponse:
    elements: List[FPLLiveEventElement]

    @staticmethod
    def create_from_dict(data: List[dict]):
        return FPLLiveEventResponse(
            elements=[FPLLiveEventElement.create_from_dict(d) for d in data]
        )


@dataclass
class FPLLeagueEntry:
    entry: int
    entry_name: str
    player_name: str
