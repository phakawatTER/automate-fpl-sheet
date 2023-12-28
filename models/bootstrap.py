from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


@dataclass
class ChipPlay:
    chip_name: str
    num_played: int


@dataclass
class TopElementInfo:
    id: int
    points: int


class PlayerPosition(Enum):
    GOAL_KEEPER = "GKP"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    FORWARD = "FWD"


@dataclass
class BootstrapGameweek:
    id: int
    name: str
    deadline_time: str
    average_entry_score: int
    finished: bool
    data_checked: bool
    highest_scoring_entry: int
    deadline_time_epoch: int
    deadline_time_game_offset: int
    highest_score: int
    is_previous: bool
    is_current: bool
    is_next: bool
    cup_leagues_created: bool
    h2h_ko_matches_created: bool
    chip_plays: List[ChipPlay]
    most_selected: int
    most_transferred_in: int
    top_element: int
    top_element_info: TopElementInfo
    transfers_made: int
    most_captained: int
    most_vice_captained: int

    def __post_init__(self):
        if len(self.chip_plays) > 0 and isinstance(self.chip_plays[0], dict):
            self.chip_plays = [ChipPlay(**d) for d in self.chip_plays]

        if isinstance(self.top_element_info, dict):
            self.top_element_info = TopElementInfo(**dict(self.top_element_info))


@dataclass
class BootstrapElement:
    chance_of_playing_next_round: int
    chance_of_playing_this_round: int
    code: int
    cost_change_event: int
    cost_change_event_fall: int
    cost_change_start: int
    cost_change_start_fall: int
    dreamteam_count: int
    element_type: int
    ep_next: str
    ep_this: str
    event_points: int
    first_name: str
    form: str
    id: int
    in_dreamteam: bool
    news: str
    news_added: str
    now_cost: int
    photo: str
    points_per_game: str
    second_name: str
    selected_by_percent: str
    special: bool
    squad_number: Optional[int]
    status: str
    team: int
    team_code: int
    transfers_in: int
    transfers_in_event: int
    transfers_out: int
    transfers_out_event: int
    value_form: str
    value_season: str
    web_name: str
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
    influence_rank: int
    influence_rank_type: int
    creativity_rank: int
    creativity_rank_type: int
    threat_rank: int
    threat_rank_type: int
    ict_index_rank: int
    ict_index_rank_type: int
    corners_and_indirect_freekicks_order: Optional[int]
    corners_and_indirect_freekicks_text: str
    direct_freekicks_order: Optional[int]
    direct_freekicks_text: str
    penalties_order: Optional[int]
    penalties_text: str
    expected_goals_per_90: int
    saves_per_90: int
    expected_assists_per_90: int
    expected_goal_involvements_per_90: int
    expected_goals_conceded_per_90: int
    goals_conceded_per_90: int
    now_cost_rank: int
    now_cost_rank_type: int
    form_rank: int
    form_rank_type: int
    points_per_game_rank: int
    points_per_game_rank_type: int
    selected_rank: int
    selected_rank_type: int
    starts_per_90: int
    clean_sheets_per_90: int
    total_points: int

    # manually constructed fields
    position: Optional[PlayerPosition] = field(default=None)
    is_subsituition: Optional[bool] = field(default=None)
    pick_position: Optional[int] = field(default=None)
    is_captain: Optional[bool] = field(default=None)
    is_vice_captain: Optional[bool] = field(default=None)
    gameweek_points: Optional[int] = field(default=None)

    def __post_init__(self):
        positions = [
            PlayerPosition.GOAL_KEEPER,
            PlayerPosition.DEFENDER,
            PlayerPosition.MIDFIELDER,
            PlayerPosition.FORWARD,
        ]
        self.position = positions[self.element_type - 1]


@dataclass
class BootstrapTeam:
    code: int
    draw: int
    form: Optional[any]
    id: int
    loss: int
    name: str
    played: int
    points: int
    position: int
    short_name: str
    strength: int
    team_division: Optional[int]
    unavailable: bool
    win: int
    strength_overall_home: int
    strength_overall_away: int
    strength_attack_home: int
    strength_attack_away: int
    strength_defence_home: int
    strength_defence_away: int
    pulse_id: int


@dataclass
class Bootstrap:
    events: List[BootstrapGameweek]
    elements: List[BootstrapElement]
    teams: List[BootstrapTeam]
