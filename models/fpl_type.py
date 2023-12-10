from typing import List

class H2HResponse:
    def __init__(self, response:dict):
        self.has_next:bool = response.get("has_next")
        self.page:int = response.get("page")
        self.results:List[H2HData] =  [H2HData(d) for d in response.get("results")]

class H2HData:
    def __init__(self, data:dict):
        self.id = data.get("id")
        self.entry_1_entry = data.get("entry_1_entry")
        self.entry_1_name = data.get("entry_1_name")
        self.entry_1_player_name = data.get("entry_1_player_name")
        self.entry_1_points = data.get("entry_1_points")
        self.entry_1_win = data.get("entry_1_win")
        self.entry_1_draw = data.get("entry_1_draw")
        self.entry_1_loss = data.get("entry_1_loss")
        self.entry_1_total = data.get("entry_1_total")
        self.entry_2_entry = data.get("entry_2_entry")
        self.entry_2_name = data.get("entry_2_name")
        self.entry_2_player_name = data.get("entry_2_player_name")
        self.entry_2_points = data.get("entry_2_points")
        self.entry_2_win = data.get("entry_2_win")
        self.entry_2_draw = data.get("entry_2_draw")
        self.entry_2_loss = data.get("entry_2_loss")
        self.entry_2_total = data.get("entry_2_total")
        self.is_knockout = data.get("is_knockout")
        self.league = data.get("league")
        self.winner = data.get("winner")
        self.seed_value = data.get("seed_value")
        self.event = data.get("event")
        self.tiebreak = data.get("tiebreak")
        self.is_bye = data.get("is_bye")
        self.knockout_name = data.get("knockout_name")


class FantasyTeam:
    def __init__(self, active_chip, automatic_subs, entry_history, picks):
        self.active_chip = active_chip
        self.automatic_subs = automatic_subs
        self.entry_history = EntryHistory(**entry_history)
        self.picks = [Pick(**pick) for pick in picks]

class EntryHistory:
    def __init__(self, event, points, total_points, rank, rank_sort, overall_rank, bank, value,
                 event_transfers, event_transfers_cost, points_on_bench):
        self.event = event
        self.points = points
        self.total_points = total_points
        self.rank = rank
        self.rank_sort = rank_sort
        self.overall_rank = overall_rank
        self.bank = bank
        self.value = value
        self.event_transfers = event_transfers
        self.event_transfers_cost = event_transfers_cost
        self.points_on_bench = points_on_bench

class Pick:
    def __init__(self, element, position, multiplier, is_captain, is_vice_captain):
        self.element = element
        self.position = position
        self.multiplier = multiplier
        self.is_captain = is_captain
        self.is_vice_captain = is_vice_captain


class PlayerData:
    def __init__(self, fixtures, history, history_past):
        # TODO: need to fix error when initialize fixtures ignroe this for now as we dont use it
        # self.fixtures = [Fixture(**fixture) for fixture in fixtures]
        self.history = [PlayerHistory(**h) for h in history]
        self.history_past = [PlayerSeasonHistory(**season) for season in history_past]

class Fixture:
    def __init__(self, id, code, team_h, team_h_score, team_a, team_a_score, event, finished, minutes,
                 provisional_start_time, kickoff_time, event_name, is_home, difficulty):
        print(event_name)
        self.id = id
        self.code = code
        self.team_h = team_h
        self.team_h_score = team_h_score
        self.team_a = team_a
        self.team_a_score = team_a_score
        self.event = event
        self.finished = finished
        self.minutes = minutes
        self.provisional_start_time = provisional_start_time
        self.kickoff_time = kickoff_time
        self.event_name = event_name
        self.is_home = is_home
        self.difficulty = difficulty

class PlayerHistory:
    def __init__(self, element, fixture, opponent_team, total_points, was_home, kickoff_time,
                 team_h_score, team_a_score, round, minutes, goals_scored, assists, clean_sheets,
                 goals_conceded, own_goals, penalties_saved, penalties_missed, yellow_cards, red_cards,
                 saves, bonus, bps, influence, creativity, threat, ict_index, starts,
                 expected_goals, expected_assists, expected_goal_involvements,
                 expected_goals_conceded, value, transfers_balance, selected, transfers_in, transfers_out):
        self.element = element
        self.fixture = fixture
        self.opponent_team = opponent_team
        self.total_points = total_points
        self.was_home = was_home
        self.kickoff_time = kickoff_time
        self.team_h_score = team_h_score
        self.team_a_score = team_a_score
        self.round = round
        self.minutes = minutes
        self.goals_scored = goals_scored
        self.assists = assists
        self.clean_sheets = clean_sheets
        self.goals_conceded = goals_conceded
        self.own_goals = own_goals
        self.penalties_saved = penalties_saved
        self.penalties_missed = penalties_missed
        self.yellow_cards = yellow_cards
        self.red_cards = red_cards
        self.saves = saves
        self.bonus = bonus
        self.bps = bps
        self.influence = influence
        self.creativity = creativity
        self.threat = threat
        self.ict_index = ict_index
        self.starts = starts
        self.expected_goals = expected_goals
        self.expected_assists = expected_assists
        self.expected_goal_involvements = expected_goal_involvements
        self.expected_goals_conceded = expected_goals_conceded
        self.value = value
        self.transfers_balance = transfers_balance
        self.selected = selected
        self.transfers_in = transfers_in
        self.transfers_out = transfers_out

class PlayerSeasonHistory:
    def __init__(self, season_name, element_code, start_cost, end_cost, total_points, minutes,
                 goals_scored, assists, clean_sheets, goals_conceded, own_goals, penalties_saved,
                 penalties_missed, yellow_cards, red_cards, saves, bonus, bps, influence, creativity,
                 threat, ict_index, starts, expected_goals, expected_assists,
                 expected_goal_involvements, expected_goals_conceded):
        self.season_name = season_name
        self.element_code = element_code
        self.start_cost = start_cost
        self.end_cost = end_cost
        self.total_points = total_points
        self.minutes = minutes
        self.goals_scored = goals_scored
        self.assists = assists
        self.clean_sheets = clean_sheets
        self.goals_conceded = goals_conceded
        self.own_goals = own_goals
        self.penalties_saved = penalties_saved
        self.penalties_missed = penalties_missed
        self.yellow_cards = yellow_cards
        self.red_cards = red_cards
        self.saves = saves
        self.bonus = bonus
        self.bps = bps
        self.influence = influence
        self.creativity = creativity
        self.threat = threat
        self.ict_index = ict_index
        self.starts = starts
        self.expected_goals = expected_goals
        self.expected_assists = expected_assists
        self.expected_goal_involvements = expected_goal_involvements
        self.expected_goals_conceded = expected_goals_conceded
