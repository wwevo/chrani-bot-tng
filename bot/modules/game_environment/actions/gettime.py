from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


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
    next_bloodmoon_date = int(
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("gamestats", {})
        .get("BloodMoonDay", None)
    )

    daylight_length = int(
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("gamestats", {})
        .get("DayLightLength", None)
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


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 3  # [seconds]
    timeout_start = time()

    if not module.telnet.add_telnet_command_to_queue("gettime"):
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"Day\s(?P<day>\d{1,5}),\s(?P<hour>\d{1,2}):(?P<minute>\d{1,2}).*"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    active_dataset = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("active_dataset", None)
    )

    # we can't save the gametime without knowing the game-name, as each game can have different stats.
    if active_dataset is None:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)

    matched_day = int(match.group("day"))
    matched_hour = int(match.group("hour"))
    matched_minute = int(match.group("minute"))

    is_bloodmoon = (True if is_currently_bloodmoon(module, matched_day, matched_hour) else False)
    is_bloodday = (True if is_currently_bloodmoon(module, matched_day) else False)

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


def callback_fail(module, event_data, dispatchers_steamid):
    pass


def skip_it(module, event_data, dispatchers_steamid=None):
    pass


action_meta = {
    "description": "gets the current gettime readout",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
