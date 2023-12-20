from dataclasses import dataclass, field
from typing import List


@dataclass
class PlayerGameweekData:
    name: str = ""
    player_id: int = 0
    points: float = 0
    reward_division: int = 1
    shared_reward_player_ids: List[int] = field(default_factory=list)
    reward: float = 0
    sheet_row: int = -1
    captain_points: int = 0
    vice_captain_points: int = 0
    bank_account: str = ""
    cummulative_revenue: float = 0


@dataclass
class PlayerRevenue:
    name: str
    revenue: float
