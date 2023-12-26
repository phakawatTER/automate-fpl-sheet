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
    UPDATE_LEAGUE_REWARD = "UPDATE_LEAGUE_REWARD"
    LIST_LEAGUE_PLAYERS = "LIST_LEAGUE_PLAYERS"
    UPDATE_PLAYER_BANK_ACCOUNT = "UPDATE_PLAYER_BANK_ACCOUNT"

    @staticmethod
    def get_commands():
        return {
            MessageHandlerActionGroup.UPDATE_FPL_TABLE: "Update/Get FPL table of given gameweek",
            MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE: "Batch update/get FPL table",
            MessageHandlerActionGroup.GET_PLAYERS_REVENUES: "Get cummulative revenues",
            MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT: "Generate cummulative revenue over gameweeks",
            MessageHandlerActionGroup.GET_PLAYER_GW_PICKS: "List players's first 11 picks of given gameweek",
            MessageHandlerActionGroup.SUBSCRIBE_LEAGUE: "Subscribe league by league id",
            MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE: "Unsubscribe league by league id",
            MessageHandlerActionGroup.UPDATE_LEAGUE_REWARD: "Update league reward with comma-separated numeric values",
            MessageHandlerActionGroup.LIST_LEAGUE_PLAYERS: "List subscribed league players",
        }


PATTERN_ACTIONS = {
    r"list (cmd|commands)": HelperHandlerActionGroup.LIST_COMMANDS,
    r"subscribe league (\d+)": MessageHandlerActionGroup.SUBSCRIBE_LEAGUE,
    r"\bunsubscribe league\b": MessageHandlerActionGroup.UNSUBSCRIBE_LEAGUE,
    r"get (gw|gameweek) (\d+-\d+)": MessageHandlerActionGroup.BATCH_UPDATE_FPL_TABLE,
    r"get (gw|gameweek) (\d+)": MessageHandlerActionGroup.UPDATE_FPL_TABLE,
    r"get (revenue|rev)": MessageHandlerActionGroup.GET_PLAYERS_REVENUES,
    r"get (plot|plt) (\d+-\d+)": MessageHandlerActionGroup.GENERATE_GAMEWEEKS_PLOT,
    r"get (picks) (\d+)": MessageHandlerActionGroup.GET_PLAYER_GW_PICKS,
    # rewards
    r"update league reward": MessageHandlerActionGroup.UPDATE_LEAGUE_REWARD,
    r"list league players": MessageHandlerActionGroup.LIST_LEAGUE_PLAYERS,
    r"update player (\d+) (bank account|ba) (.+$)": MessageHandlerActionGroup.UPDATE_PLAYER_BANK_ACCOUNT,
}
