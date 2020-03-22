from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 6  # [seconds]
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name

    target_coordinates = event_data[1].get("coordinates", None)
    player_to_be_teleported_steamid = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_to_be_teleported_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(dataset, {})
        .get(player_to_be_teleported_steamid, {})
    )
    player_coordinates = player_to_be_teleported_dict.get("pos", None)

    # print(target_coordinates != player_coordinates)
    # print(target_coordinates, player_coordinates)
    if all([
        dataset is not None,
        target_coordinates is not None,
        player_coordinates is not None
    ]) and all([
        # no sense in porting a player to a place they are already standing on ^^
        target_coordinates != player_coordinates
    ]):
        command = (
            "teleportplayer {player_to_be_teleported} {pos_x} {pos_y} {pos_z}"
        ).format(
            player_to_be_teleported=player_to_be_teleported_dict.get("steamid"),
            pos_x=target_coordinates["x"],
            pos_y=target_coordinates["y"],
            pos_z=target_coordinates["z"]
        )

        if not module.telnet.add_telnet_command_to_queue(command):
            event_data[1]["fail_reason"] = "duplicate command"
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        poll_is_finished = False
        regex = (
            telnet_prefixes["telnet_log"]["timestamp"] +
            r"PlayerSpawnedInWorld\s"
            r"\("
            r"reason: (?P<command>.+?),\s"
            r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
            r"\):\s"
            r"EntityID={entity_id},\s".format(entity_id=player_to_be_teleported_dict.get("id")) +
            r"PlayerID='{player_to_be_teleported}',\s".format(player_to_be_teleported=player_to_be_teleported_dict.get("steamid")) +
            r"OwnerID='{player_to_be_teleported}',\s".format(player_to_be_teleported=player_to_be_teleported_dict.get("steamid")) +
            r"PlayerName='(?P<player_name>.*)'"
        )

        while not poll_is_finished and (time() < timeout_start + timeout):
            match = False
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                poll_is_finished = True

            if match:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                return

            sleep(0.25)

        event_data[1]["fail_reason"] = "action timed out"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    event_data[1]["fail_reason"] = "insufficient data for execution"
    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_to_be_teleported = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)


def callback_fail(module, event_data, dispatchers_steamid):
    print("teleport failed!", event_data[1].get("fail_reason", "no reason known"))


action_meta = {
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
