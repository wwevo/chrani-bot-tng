from bot import loaded_modules_dict, telnet_prefixes
from bot.profiler import profiler
from bot.logger import get_logger
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("players.show_profiling_stats")


def main_function(origin_module, module, regex_result):
    """Display performance profiling statistics."""
    command = regex_result.group("command")
    player_steamid = regex_result.group("player_steamid")

    # Check if player is admin
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, {})
    )

    if player_dict.get("permission_level", 2000) != 0:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FF0000]Admin only command[-]'
        }]
        module.trigger_action_hook(origin_module, event_data=event_data)
        return

    # Get profiling stats
    all_stats = profiler.get_all_stats()

    if not all_stats:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FFFF00]No profiling data available yet[-]'
        }]
        module.trigger_action_hook(origin_module, event_data=event_data)
        return

    # Log full stats to server logs
    logger.info("profiling_report_requested", user=player_steamid)
    logger.info("profiling_report_header", message="═══ Performance Profiling Report ═══")

    # Sort by average time (slowest first)
    sorted_metrics = sorted(
        all_stats.items(),
        key=lambda x: x[1]['avg'] if x[1] else 0,
        reverse=True
    )

    # Log all metrics to console/logs
    profiler.log_stats()

    # Also print a summary to logs
    logger.info("profiling_top_3_slowest", message="Top 3 Slowest Operations:")
    for metric_name, stats in sorted_metrics[:3]:
        if stats:
            logger.info("profiling_metric_summary",
                       metric=metric_name,
                       avg_ms=round(stats['avg']*1000, 2),
                       p95_ms=round(stats['p95']*1000, 2),
                       max_ms=round(stats['max']*1000, 2),
                       count=stats['count'])

    # Send confirmation to player
    event_data = ['say_to_player', {
        'steamid': player_steamid,
        'message': '[66FF66]Profiling stats written to server logs![-]'
    }]
    module.trigger_action_hook(origin_module, event_data=event_data)


triggers = {
    "show profiling stats": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/profiling.*)"
}

trigger_meta = {
    "description": "shows performance profiling statistics (admin only)",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "show profiling stats (Alloc)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                triggers["show profiling stats"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
