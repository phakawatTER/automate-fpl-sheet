import os
import asyncio
from typing import List, Dict
import matplotlib.pyplot as plt
import util
import models
from adapter import S3Uploader
from .fpl_service import Service as FPLService


COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


class Service:
    def __init__(
        self,
        fpl_service: FPLService,
        s3_uploader: S3Uploader,
    ):
        self.__fpl_service = fpl_service
        self.__s3_uploader = s3_uploader

    def __get_file_name_from_path(self, file_path: str) -> str:
        _, file_name = os.path.split(file_path)
        return file_name

    @util.time_track(description="Generate overall gameweek revenue plot")
    async def generate_overall_gameweeks_plot(
        self, from_gameweek: int, to_gameweek: int
    ) -> List[str]:
        players_dict: Dict[str, List[models.PlayerGameweekData]] = {}
        gameweek_futures = []
        gameweeks: List[str] = []

        for i in range(from_gameweek, to_gameweek + 1, 1):
            future = asyncio.ensure_future(
                self.__fpl_service.get_or_update_fpl_gameweek_table(i)
            )
            gameweek_futures.append(future)
            gameweeks.append(f"GW{i}")

        future_results: List[List[models.PlayerGameweekData]] = await asyncio.gather(
            *gameweek_futures
        )

        for gameweek_players in future_results:
            for player in gameweek_players:
                if player.name not in players_dict:
                    players_dict[player.name] = [player]
                else:
                    players_dict[player.name].append(player)

        player_names = list(players_dict)
        player_points: List[List[int]] = []
        for _, gameweek_results in players_dict.items():
            player_rewards = [gw.reward for gw in gameweek_results]
            cummulative_rewards = []
            for i, _ in enumerate(player_rewards):
                player_reward = 0
                for _reward in player_rewards[: i + 1]:
                    player_reward += _reward
                cummulative_rewards.append(player_reward)
            player_points.append(cummulative_rewards)

        plot_destinations: List[str] = []
        # Plotting the trend graph
        plt.figure(figsize=(12, 6))
        for i, player_name in enumerate(player_names):
            plt.plot(
                gameweeks,
                player_points[i],
                label=player_name,
                marker="o",
                color=COLORS[i % len(COLORS)],
            )
            # Customize the plot
            plt.title("FPL Player Cummulative Revenue Over Weeks")
            plt.xlabel("Weeks")
            plt.ylabel("Points")
            plt.legend()
            plt.grid(True)

            plot_destination = f"/tmp/figure_{i+1}.png"
            plt.savefig(plot_destination, bbox_inches="tight")
            plt.cla()
            plot_destinations.append(plot_destination)

        # generate all
        for i, player_name in enumerate(player_names):
            plt.plot(
                gameweeks,
                player_points[i],
                label=player_name,
                marker="o",
                color=COLORS[i % len(COLORS)],
            )
            # Customize the plot
            plt.title("FPL Player Cummulative Revenue Over Weeks")
            plt.xlabel("Weeks")
            plt.ylabel("Points")
            plt.legend()
            plt.grid(True)

            if i == len(player_names) - 1:
                plot_destination = "/tmp/figure_all.png"
                plt.savefig(plot_destination, bbox_inches="tight")
                plot_destinations.append(plot_destination)

        urls: List[str] = []

        for destination in plot_destinations:
            file_name = self.__get_file_name_from_path(destination)
            key = f"plots/{file_name}"
            self.__s3_uploader.upload_to_default_bucket(
                key=key,
                filename=destination,
                content_type="image/png",
                expires=None,
            )

            presigned_url = self.__s3_uploader.generate_presigned_url(
                key, expiration_time=24 * 3600
            )
            urls.append(presigned_url)

        return urls
