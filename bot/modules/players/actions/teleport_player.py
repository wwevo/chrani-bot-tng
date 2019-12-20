from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 5  # [seconds]
    timeout_start = time()

    target_coordinates = event_data[1].get("coordinates", None)
    player_to_be_teleported_steamid = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_environment", {}).get("active_dataset", None)
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
        # don't try to teleport a player that's already being handled by something
        # player_to_be_teleported_dict.get("skip_processing", False) is False,
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
            r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        )
        regex +=(
            r"INF\sPlayerSpawnedInWorld\s"
            r"\(reason:\sTeleport,\sposition:\s(?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)\):\s"
            r"EntityID={entity_id},\sPlayerID='{player_to_be_teleported}',\sOwnerID='{player_to_be_teleported}',\s"
            r"PlayerName='(?P<player_name>.*)'"
        ).format(
            player_to_be_teleported=player_to_be_teleported_dict.get("steamid"),
            entity_id=player_to_be_teleported_dict.get("id")
        )

        while not poll_is_finished and (time() < timeout_start + timeout):
            sleep(0.25)
            match = False
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                poll_is_finished = True

            if match:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                return

        event_data[1]["fail_reason"] = "action timed out"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    event_data[1]["fail_reason"] = "insufficient data for execution"
    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_to_be_teleported = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_environment", {}).get("active_dataset", None)


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
