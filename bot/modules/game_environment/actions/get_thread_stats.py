from bot import loaded_modules_dict
from bot.thread_tracker import thread_tracker
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    # Get current thread stats from tracker
    running_threads = thread_tracker.get_running_threads()

    # Calculate statistics
    active_threads = len([t for t in running_threads if t["status"] == "running"])
    timed_out_threads = len([t for t in running_threads if t["status"] == "timeout"])
    total_threads = len(running_threads)

    # Group threads by action for detailed breakdown
    threads_by_action = {}
    for thread in running_threads:
        action_id = thread["action_id"]
        if action_id not in threads_by_action:
            threads_by_action[action_id] = {
                "count": 0,
                "module": thread["module_name"],
                "statuses": {"running": 0, "timeout": 0}
            }
        threads_by_action[action_id]["count"] += 1
        threads_by_action[action_id]["statuses"][thread["status"]] += 1

    # Store in DOM
    module.dom.data.upsert({
        module.get_module_identifier(): {
            "thread_stats": {
                "active_threads": active_threads,
                "timed_out_threads": timed_out_threads,
                "total_threads": total_threads,
                "by_action": threads_by_action
            }
        }
    })

    module.callback_success(callback_success, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return


def callback_skip(module, action_meta, dispatchers_id=None):
    return


def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "collects thread statistics from ThreadTracker",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail,
        "callback_skip": callback_skip,
    },
    "parameters": {
        "periodic": True,  # Run periodically to update stats
        "requires_telnet_connection": False,  # No telnet needed
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
