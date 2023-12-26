from dataclasses import dataclass, field, asdict
from typing import List
from .bootstrap import BootstrapElement


@dataclass
class PlayerGameweekData:
    name: str = ""
    team_name: str = ""
    player_id: int = 0
    points: float = 0
    reward_division: int = 1
    shared_reward_player_ids: List[int] = field(default_factory=list)
    reward: float = 0
    captain_points: int = 0
    vice_captain_points: int = 0
    bank_account: str = ""
    sheet_row: int = -1

    def to_json(self):
        return asdict(self)


@dataclass
class PlayerRevenue:
    team_name: str
    name: str
    revenue: float


@dataclass
class PlayerSheetData:
    player_id: int
    bank_account: str
    season_rank: int
    name: str
    team_name: str


@dataclass
class PlayerGameweekPicksData:
    player: PlayerSheetData
    event_transfers_cost: int
    event_transfers: int
    picked_elements: List[BootstrapElement]


@dataclass
class LeagueSheet:
    url: str
    worksheet: str

    def to_json(self):
        return asdict(self)


@dataclass
class PlayerData:
    bank_account: str
    player_id: int
    season_rank: int
    name: str
    team_name: str

    def to_json(self):
        return asdict(self)
