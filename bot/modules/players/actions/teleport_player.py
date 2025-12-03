from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    command = (
        "teleportplayer {player_to_be_teleported} {pos_x} {pos_y} {pos_z}"
    ).format(
        player_to_be_teleported=player_entity_id,
        pos_x=int(float(target_coordinates["x"])),
        pos_y=pos_y,
        pos_z=int(float(target_coordinates["z"]))
    )

    if not module.telnet.add_telnet_command_to_queue(command):
        event_data[1]["fail_reason"] = "duplicate command"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return



def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "requires_telnet_connection": True,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
