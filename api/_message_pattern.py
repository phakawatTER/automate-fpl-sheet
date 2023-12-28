class HelperHandlerActionGroup:
    LIST_COMMANDS = "LIST_COMMANDS"


class MessageHandlerActionGroup:
    UPDATE_FPL_TABLE = "UPDATE_FPL_TABLE"
    BATCH_UPDATE_FPL_TABLE = "BATCH_UPDATE_FPL_TABLE"
    GET_PLAYERS_REVENUES = "GET_PLAYERS_REVENUES"
    GENERATE_GAMEWEEKS_PLOT = "GENERATE_GAMEWEEKS_PLOT"
    GET_PLAYER_GW_PICKS = "GET_PLAYER_GW_PICKS"
    SUBSCRIBE_LEAGUE = "SUBSCRIBE_LEAGUE"
    UNSUBSCRIBE_LEAGUE = "UNSUBSCRIBE_LEAGUE"
    LIST_LEAGUE_PLAYERS = "LIST_LEAGUE_PLAYERS"
    UPDATE_PLAYER_BANK_ACCOUNT = "UPDATE_PLAYER_BANK_ACCOUNT"
    CLEAR_ALL_GAMEWEEKS_CACHE = "CLEAR_ALL_GAMEWEEKS_CACHE"
    # Rewards
    ADD_IGNORED_LEAGUE_PLAYER = "ADD_IGNORED_LEAGUE_PLAYER"
    REMOVE_IGNORED_LEAGUE_PLAYER = "REMOVE_IGNORED_LEAGUE_PLAYER"
    UPDATE_LEAGUE_REWARDS = "UPDATE_LEAGUE_REWARDS"
    # Fixtures
    GET_GAMEWEEK_FIXTURES = "GET_GAMEWEEK_FIXTURES"
    LIST_GAMEWEEK_FIXTURES = "LIST_GAMEWEEK_FIXTURES"

    @staticmethod
    def get_commands():
        return {
            MessageHandlerActionGroup.GET_GAMEWEEK_FIXTURES: "List gameweek fixtures by given gameweek",
            MessageHandlerActionGroup.LIST_GAMEWEEK_FIXTURES: "List gameweek fixtures by given gameweek range",
            MessageHandlerActionGroup.UPDATE_FPL_TABLE: "Update/Get FPL table of given gameweek",
            MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE: "Batch update/get FPL table",
            MessageHandlerActionGroup.GET_PLAYERS_REVENUES: "Get cummulative revenues",
            MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT: "Generate cummulative revenue over gameweeks",
            MessageHandlerActionGroup.GET_PLAYER_GW_PICKS: "List players's first 11 picks of given gameweek",
            MessageHandlerActionGroup.SUBSCRIBE_LEAGUE: "Subscribe league by league id",
            MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE: "Unsubscribe league by league id",
            MessageHandlerActionGroup.LIST_LEAGUE_PLAYERS: "List subscribed league players",
            MessageHandlerActionGroup.UPDATE_PLAYER_BANK_ACCOUNT: "Update player's bank account",
            MessageHandlerActionGroup.CLEAR_ALL_GAMEWEEKS_CACHE: "Clear all gameweeks cache",
            MessageHandlerActionGroup.ADD_IGNORED_LEAGUE_PLAYER: "Add league ignored player",
            MessageHandlerActionGroup.REMOVE_IGNORED_LEAGUE_PLAYER: "Remove league ignored player",
            MessageHandlerActionGroup.UPDATE_LEAGUE_REWARDS: "Update league rewards (should match the number of active players)",
        }


PATTERN_ACTIONS = {
    r"^list (cmd|commands)": HelperHandlerActionGroup.LIST_COMMANDS,
    # subscription
    r"^subscribe league (\d+)": MessageHandlerActionGroup.SUBSCRIBE_LEAGUE,
    r"^unsubscribe league\b": MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE,
    # gameweek
    r"get (gw|gameweek) (\d+) (fixtures)": MessageHandlerActionGroup.GET_GAMEWEEK_FIXTURES,
    r"get (gw|gameweek) (\d+-\d+) (fixtures)": MessageHandlerActionGroup.LIST_GAMEWEEK_FIXTURES,
    r"^get (gw|gameweek) (\d+-\d+)": MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE,
    r"^get (gw|gameweek) (\d+)": MessageHandlerActionGroup.UPDATE_FPL_TABLE,
    r"^get (picks) (\d+)": MessageHandlerActionGroup.GET_PLAYER_GW_PICKS,
    r"^get (revenue|rev)": MessageHandlerActionGroup.GET_PLAYERS_REVENUES,
    r"^get (plot|plt) (\d+-\d+)": MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT,
    # rewards
    r"^list league players": MessageHandlerActionGroup.LIST_LEAGUE_PLAYERS,
    r"^update player (\d+) (bank account|ba) (.+$)": MessageHandlerActionGroup.UPDATE_PLAYER_BANK_ACCOUNT,
    # cache
    r"^clear gw cache": MessageHandlerActionGroup.CLEAR_ALL_GAMEWEEKS_CACHE,
    # rewards and league config
    r"^ignore player (\d+)": MessageHandlerActionGroup.ADD_IGNORED_LEAGUE_PLAYER,
    r"^unignore player (\d+)": MessageHandlerActionGroup.REMOVE_IGNORED_LEAGUE_PLAYER,
    r"^update league rewards (-?\d+(?:,-?\d+)*)$": MessageHandlerActionGroup.UPDATE_LEAGUE_REWARDS,
}
