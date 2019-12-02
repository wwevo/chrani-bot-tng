from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 5  # [seconds]
    timeout_start = time()

    coordinates = event_data[1].get("coordinates", None)
    player_to_be_teleported = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_environment", {}).get("active_dataset", None)
    player_is_in_transit = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(dataset, {})
        .get(player_to_be_teleported, {})
        .get("in_transit", False)
    )

    if all([
        dataset is not None,
        coordinates is not None,
        player_is_in_transit is False
    ]):
        """ setting a flag that the player in question is currently being teleported """
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    dataset: {
                        player_to_be_teleported: {
                            "in_transit": True
                        }
                    }
                }
            }
        })

        command = (
            "teleportplayer {player_to_be_teleported} {pos_x} {pos_y} {pos_z}"
        ).format(
            player_to_be_teleported=player_to_be_teleported,
            pos_x=coordinates["x"],
            pos_y=coordinates["y"],
            pos_z=coordinates["z"]
        )
        module.telnet.add_telnet_command_to_queue(command)

        poll_is_finished = False
        regex = (
            r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        )
        regex +=(
            r"INF\sPlayerSpawnedInWorld\s"
            r"\(reason:\sTeleport,\sposition:\s(?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)\):\s"
            r"EntityID=3415,\sPlayerID='{player_to_be_teleported}',\sOwnerID='{player_to_be_teleported}',\s"
            r"PlayerName='(?P<player_name>.*)'"
        ).format(
            player_to_be_teleported=player_to_be_teleported
        )

        while not poll_is_finished and (time() < timeout_start + timeout):
            sleep(0.25)
            match = False
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                poll_is_finished = True

            if match:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_to_be_teleported = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_environment", {}).get("active_dataset", None)

    """ the porting was successful, we can now remove the in_transit flag """
    module.dom.data.upsert({
        "module_players": {
            "elements": {
                dataset: {
                    player_to_be_teleported: {
                        "in_transit": False
                    }
                }
            }
        }
    })


def callback_fail(module, event_data, dispatchers_steamid):
    print("teleport failed!")


action_meta = {
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
