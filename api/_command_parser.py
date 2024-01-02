import sys
import io
import argparse
from typing import Optional
from .handler import LineMessageHandler


class LeagueAction:
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    UPDATE_REWARDS = "update-rewards"


class PlayerAction:
    LIST = "ls"
    UPDATE_BANK_ACCOUNT = "update-bank-account"
    IGNORE = "ignore"
    UNIGNORE = "unignore"


class GameweekAction:
    GET_FIXTURES = "get-fixtures"
    GET_RESULT = "get-result"
    GET_PICKS = "get-picks"


class RevenueAction:
    SUMMARIZE = "summarize"
    PLOT = "plot"


class CacheAction:
    CLEAR = "clear"


class LukaNamespace(argparse.Namespace):
    command: str
    action: str
    id: Optional[str]
    type: Optional[str]
    bank_account: Optional[str]
    gameweek: Optional[int]
    from_gameweek: Optional[int]
    to_gameweek: Optional[int]
    rewards: Optional[list[float]]


def get_luka_command_parser():
    parser = argparse.ArgumentParser(prog="LUKA")
    prog_parser = parser.add_subparsers(dest="prog")
    luka_parser = prog_parser.add_parser("luka")
    subparsers = luka_parser.add_subparsers(dest="command")
    league_parser = subparsers.add_parser("league", aliases=["l"])
    league_parser.add_argument(
        "action",
        choices=[
            LeagueAction.SUBSCRIBE,
            LeagueAction.UNSUBSCRIBE,
            LeagueAction.UPDATE_REWARDS,
        ],
    )
    league_parser.add_argument(
        "--rewards",
        nargs="+",
        type=float,
        help="list of league rewards",
    )
    league_parser.add_argument("--id", type=int)
    league_parser.add_argument("--type", type=str, default="h2h")

    player_parser = subparsers.add_parser("player", aliases=["p"])
    player_parser.add_argument(
        "action",
        choices=[
            PlayerAction.LIST,
            PlayerAction.UPDATE_BANK_ACCOUNT,
            PlayerAction.IGNORE,
            PlayerAction.UNIGNORE,
        ],
        help="Available commands for players",
    )
    player_parser.add_argument("--id", type=int)
    player_parser.add_argument("--bank-account", type=str)

    gameweek_parser = subparsers.add_parser("gameweek", aliases=["gw"])
    gameweek_parser.add_argument(
        "action",
        choices=[
            GameweekAction.GET_FIXTURES,
            GameweekAction.GET_RESULT,
            GameweekAction.GET_PICKS,
        ],
        help="Available commands for FPL gameweeks",
    )
    gameweek_parser.add_argument("gameweek", type=int, nargs="?")
    gameweek_parser.add_argument(
        "--from-gameweek", "-f", type=int, dest="from_gameweek"
    )
    gameweek_parser.add_argument("--to-gameweek", "-t", type=int, dest="to_gameweek")

    revenue_parser = subparsers.add_parser("revenue", aliases=["rev"])
    revenue_parser.add_argument(
        "action", choices=[RevenueAction.SUMMARIZE, RevenueAction.PLOT]
    )
    revenue_parser.add_argument("--from-gameweek", "-f", type=int, dest="from_gameweek")
    revenue_parser.add_argument("--to-gameweek", "-t", type=int, dest="to_gameweek")

    cache_parser = subparsers.add_parser("cache")
    cache_parser.add_argument("action", choices=[CacheAction.CLEAR])

    return parser


class Luka:
    def __init__(self, line_message_handler: LineMessageHandler):
        self.__line_message_handler = line_message_handler

    def parse_command(self, args: Optional[str] = None, allow_sys_exit: bool = False):
        parser = get_luka_command_parser()
        cmd: Optional[list[str]] = None
        if args is not None:
            cmd = args.split()
        if not allow_sys_exit:
            helper_buffer = io.StringIO()
            err_buffer = io.StringIO()
            sys.stdout = helper_buffer
            sys.stderr = err_buffer
            ns: Optional[LukaNamespace] = None
            message: Optional[str] = None
            try:
                ns = parser.parse_args(cmd)
            except SystemExit as e:
                message = None
                if e.code == 0:
                    message = helper_buffer.getvalue()
                else:
                    message = err_buffer.getvalue()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            return ns, message

        args = parser.parse_args(cmd)
        return args, None

    async def map_namespace_to_action(self, namespace: LukaNamespace, group_id: str):
        if namespace.command in ("league", "l"):
            await self.league_action_handler(ns=namespace, group_id=group_id)
        elif namespace.command in ("player", "p"):
            self.player_action_handler(ns=namespace, group_id=group_id)
        elif namespace.command in ("gameweek", "gw"):
            await self.gameweek_action_handler(ns=namespace, group_id=group_id)
        elif namespace.command in ("revenue", "rev"):
            await self.revenue_action_handler(ns=namespace, group_id=group_id)
        elif namespace.command in ("cache"):
            self.cache_action_handler(ns=namespace, group_id=group_id)

    def cache_action_handler(self, ns: LukaNamespace, group_id: str):
        if ns.action == CacheAction.CLEAR:
            self.__line_message_handler.handle_clear_gameweeks_cache(group_id=group_id)

    async def revenue_action_handler(self, ns: LukaNamespace, group_id: str):
        if ns.action == RevenueAction.SUMMARIZE:
            await self.__line_message_handler.handle_get_revenues(group_id=group_id)
        elif ns.action == RevenueAction.PLOT:
            from_gameweek, to_gameweek = ns.from_gameweek, ns.to_gameweek
            if from_gameweek is None or to_gameweek is None:
                raise ValueError("from_gameweek and to_gameweek should be specified")
            await self.__line_message_handler.handle_gameweek_plots(
                from_gameweek=from_gameweek, to_gameweek=to_gameweek, group_id=group_id
            )

    async def league_action_handler(self, ns: LukaNamespace, group_id: str):
        if ns.action == LeagueAction.SUBSCRIBE:
            await self.__line_message_handler.subscribe_league(
                group_id=group_id, league_id=ns.id
            )
        elif ns.action == LeagueAction.UNSUBSCRIBE:
            self.__line_message_handler.unsubscribe_league(group_id=group_id)
        elif ns.action == LeagueAction.UPDATE_REWARDS:
            self.__line_message_handler.handle_update_league_rewards(
                group_id=group_id, rewards=ns.rewards
            )

    def player_action_handler(self, ns: LukaNamespace, group_id: str):
        if ns.action == "ls":
            self.__line_message_handler.handle_list_league_players(group_id=group_id)
        elif ns.action == PlayerAction.LIST:
            self.__line_message_handler.handle_set_league_player_bank_account(
                group_id=group_id, player_index=ns.id
            )
        elif ns.action == PlayerAction.IGNORE:
            self.__line_message_handler.handle_add_ignored_player(
                group_id=group_id, player_index=ns.id
            )
        elif ns.action == PlayerAction.UNIGNORE:
            self.__line_message_handler.handle_remove_ignored_player(
                group_id=group_id, player_index=ns.id
            )

    async def gameweek_action_handler(self, ns: LukaNamespace, group_id: str):
        gameweek, from_gameweek, to_gameweek = (
            ns.gameweek,
            ns.from_gameweek,
            ns.to_gameweek,
        )
        if ns.action == GameweekAction.GET_FIXTURES:
            if ns.from_gameweek is not None and ns.to_gameweek is not None:
                await self.__line_message_handler.handle_list_gameweek_fixtures_by_range(
                    group_id=group_id,
                    start_gameweek=from_gameweek,
                    stop_gameweek=to_gameweek,
                )
                return
            await self.__line_message_handler.handle_list_gameweek_fixtures(
                gameweek=gameweek,
                group_id=group_id,
            )
        elif ns.action == GameweekAction.GET_RESULT:
            if ns.from_gameweek is not None and ns.to_gameweek is not None:
                await self.__line_message_handler.handle_batch_update_fpl_table(
                    from_gameweek=from_gameweek,
                    to_gameweek=to_gameweek,
                    group_id=group_id,
                )
                return
            await self.__line_message_handler.handle_update_fpl_table(
                gameweek=gameweek, group_id=group_id
            )
        elif ns.action == GameweekAction.GET_PICKS:
            if ns.from_gameweek is not None or ns.to_gameweek is not None:
                raise ValueError("get-picks does not support range")
            await self.__line_message_handler.handle_players_gameweek_picks(
                gameweek=gameweek, group_id=group_id
            )

    def validate_gameweek_range(self, ns: LukaNamespace):
        if ns.gameweek is not None:
            return (ns.gameweek, None, None)
        if ns.from_gameweek is not None and ns.to_gameweek is not None:
            return (None, ns.from_gameweek, ns.to_gameweek)

        raise ValueError(
            "either positional gameweek argument or --from and --to should be specified"
        )
