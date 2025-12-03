from pprint import pp

from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    # NEW: Send command with ticket system
    regex = action_meta.get("regex")[0]
    ticket = module.telnet.send_command("gettime", regex, timeout=TELNET_TIMEOUT_NORMAL)
    result = ticket.wait()

    if result['success']:
        module.callback_success(callback_success, action_meta, dispatchers_id, result['match'])
    else:
        action_meta["fail_reason"] = ["[{}] action timeout. buffer received: {}".format(action_name, result['buffer'])]
        module.callback_fail(callback_fail, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    matched_day = int(match.group("day"))
    matched_hour = match.group("hour")
    matched_minute = match.group("minute")

    is_bloodmoon = is_currently_bloodmoon(module, matched_day, int(matched_hour))
    is_bloodday = is_currently_bloodmoon(module, matched_day)

    weekday_string = get_weekday_string(matched_day)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            active_dataset: {
                "last_recorded_gametime": {
                    "day": matched_day,
                    "hour": matched_hour,
                    "minute": matched_minute,
                    "weekday": weekday_string,
                    "is_bloodmoon": is_bloodmoon,
                    "is_bloodday": is_bloodday
                }
            }
        }
    })


def callback_skip(module, action_meta, dispatchers_id=None):
    print("skipped {}".format(action_meta.get("id")))


def callback_fail(module, action_meta, dispatchers_id=None):
    if action_meta.get("fail_reason"):
        print(action_meta.get("fail_reason"))

def get_weekday_string(server_days_passed: int) -> str:
    days_of_the_week = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    current_day_index = int(float(server_days_passed) % 7)
    if 0 <= current_day_index <= 6:
        return days_of_the_week[current_day_index]
    else:
        return ""


def is_currently_bloodmoon(module: object, day: int, hour: int = -1) -> bool:
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    next_bloodmoon_date = int(
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("gamestats", {})
        .get("BloodMoonDay", 0)
    )

    daylight_length = int(
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("gamestats", {})
        .get("DayLightLength", 0)
    )

    night_length = (24 - daylight_length)
    morning_length = (night_length - 2)

    if hour >= 0:  # we want the exact bloodmoon
        if next_bloodmoon_date == day and 23 >= hour >= 22:
            return True
        if (next_bloodmoon_date + 1) == day and 0 <= hour <= morning_length:
            return True
    else:  # we only want the day
        if next_bloodmoon_date == day:
            return True

    return False


action_meta = {
    "id": action_name,
    "description": "gets the current gettime readout",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail,
        "callback_skip": callback_skip,
    },
    "parameters": {
        "periodic": True,
        "requires_telnet_connection": True,
        "enabled": True
    },
    "regex": [
        (
            r"Day\s(?P<day>\d{1,5}),\s(?P<hour>\d{1,2}):(?P<minute>\d{1,2})"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
