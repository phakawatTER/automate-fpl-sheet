from dataclasses import dataclass, field, fields
from typing import List, Optional, Dict, Union
from datetime import datetime, timezone, date
import util
from .bootstrap import BootstrapTeam


@dataclass
class FPLH2HResponse:
    has_next: bool
    page: int
    results: List["FPLH2HData"]

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLFantasyTeam:
    active_chip: str
    automatic_subs: List[int]
    entry_history: "FPLEntryHistory"
    picks: List["FPLPick"]

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLPick:
    element: int
    position: int
    multiplier: int
    is_captain: bool
    is_vice_captain: bool

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLPlayerData:
    history: List["FPLPlayerHistory"]
    history_past: List["FPLPlayerSeasonHistory"]

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLLeagueStandings:
    league_id: int
    league_name: str
    standings: List["FPLTeamStanding"]

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLEventStatusResponse:
    status: List["FPLEventStatus"]
    leagues: bool = field(default=False)

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLEventStatus:
    bonus_added: bool
    date: date
    event: int
    points: float

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)

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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)

    @staticmethod
    def create_from_dict(data: dict):
        return FPLPlayerStats(**data)


@dataclass
class FPLLiveEventElement:
    id: int
    stats: FPLPlayerStats
    explain: any

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)

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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)

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

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLPlayerGameweekPick:
    element: int
    position: int
    multiplier: int
    is_captain: bool
    is_vice_captain: bool


@dataclass
class FPLPlayerGameweekPickEntryHistory:
    event: int
    points: int
    total_points: int
    rank: int
    rank_sort: int
    overall_rank: int
    percentile_rank: int
    bank: int
    value: int
    event_transfers: int
    event_transfers_cost: int
    points_on_bench: int


@dataclass
class FPLPlayerGameweekPicksData:
    active_chip: Optional[str]
    entry_history: FPLPlayerGameweekPickEntryHistory
    picks: List[FPLPlayerGameweekPick]

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class FPLClassicLeagueStandingResult:
    id: int
    event_total: int
    player_name: str
    rank: int
    last_rank: int
    rank_sort: int
    total: int
    entry: int
    entry_name: str


@dataclass
class FPLClassicLeagueStandings:
    has_next: bool
    page: int
    results: List[FPLClassicLeagueStandingResult]


@dataclass
class FPLClassicLeagueInfo:
    id: int
    name: str
    created: str
    closed: bool
    max_entries: Optional[int]
    league_type: str
    scoring: str
    admin_entry: int
    start_event: int
    code_privacy: str
    has_cup: bool
    cup_league: Optional[int]
    rank: Optional[int]


@dataclass
class FPLClassicLeagueStandingData:
    league: FPLClassicLeagueInfo
    standings: FPLClassicLeagueStandings
