from bot import loaded_modules_dict, telnet_prefixes
from bot.profiler import profiler
from bot.logger import get_logger
from os import path, pardir
from datetime import datetime
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("players.show_profiling_stats")

# Path for stats file (in bot root directory)
STATS_FILE = path.join(path.dirname(path.abspath(__file__)), '..', '..', '..', 'profiling_stats.txt')


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

    # Sort by average time (slowest first)
    sorted_metrics = sorted(
        all_stats.items(),
        key=lambda x: x[1]['avg'] if x[1] else 0,
        reverse=True
    )

    # Write stats to file
    try:
        with open(STATS_FILE, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Performance Profiling Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            # Top 3 summary
            f.write("TOP 3 SLOWEST OPERATIONS:\n")
            f.write("-" * 70 + "\n")
            for i, (metric_name, stats) in enumerate(sorted_metrics[:3], 1):
                if stats:
                    f.write(f"{i}. {metric_name}\n")
                    f.write(f"   avg: {stats['avg']*1000:7.2f}ms | ")
                    f.write(f"p95: {stats['p95']*1000:7.2f}ms | ")
                    f.write(f"max: {stats['max']*1000:7.2f}ms | ")
                    f.write(f"calls: {stats['count']}\n")
            f.write("\n")

            # All metrics
            f.write("ALL METRICS (sorted by average time):\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Metric':<35} {'Avg':>8} {'Median':>8} {'P95':>8} {'Max':>8} {'Calls':>6}\n")
            f.write("-" * 70 + "\n")

            for metric_name, stats in sorted_metrics:
                if stats:
                    f.write(f"{metric_name:<35} ")
                    f.write(f"{stats['avg']*1000:7.2f}ms ")
                    f.write(f"{stats['median']*1000:7.2f}ms ")
                    f.write(f"{stats['p95']*1000:7.2f}ms ")
                    f.write(f"{stats['max']*1000:7.2f}ms ")
                    f.write(f"{stats['count']:6d}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("LEGEND:\n")
            f.write("  avg    = Average time across all calls\n")
            f.write("  median = Middle value (50th percentile)\n")
            f.write("  p95    = 95th percentile (worst-case excluding outliers)\n")
            f.write("  max    = Maximum time ever recorded\n")
            f.write("  calls  = Number of times this operation was measured\n")
            f.write("\n")
            f.write("DIAGNOSTIC HINTS:\n")
            f.write("  - dom_deepcopy > 50ms: DOM is too large, needs optimization\n")
            f.write("  - dom_submit_callbacks high variance: Thread pool saturated\n")
            f.write("  - player_moved_callback > 5ms: Callback logic needs optimization\n")
            f.write("=" * 70 + "\n")

        logger.info("profiling_report_written", user=player_steamid, file=STATS_FILE)

        # Send confirmation to player with file path
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': f'[66FF66]Stats written to bot/profiling_stats.txt[-]'
        }]
        module.trigger_action_hook(origin_module, event_data=event_data)

    except Exception as e:
        logger.error("profiling_file_write_failed", error=str(e), user=player_steamid)
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': f'[FF0000]Failed to write stats file: {str(e)}[-]'
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
