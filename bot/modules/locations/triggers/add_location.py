from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")
    player_name = regex_result.group("player_name")
    entity_id = regex_result.group("entity_id")
    steamid = regex_result.group("player_steamid")
    room = regex_result.group("target_room")
    event_data = ['manage_locations', {
                    'location_identifier': "Test",
                    'location_shape': "rectangular",
                    'location_coordinates': {
                        "x": 33,
                        "y": 66,
                        "z": 99
                    },
                    'location_dimensions': {
                        'radius': None,
                        'width': 10,
                        'length': 10,
                        'height': None,
                    },
                    'location_name': "Test",
                    'action': 'create_new'}
                ]
    module.trigger_action_hook(origin_module, event_data, steamid)
    print(player_name, ":", entity_id, ":", command)


trigger_meta = {
    "description": "catches location commands from the players chat and then adds them to the database",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/add location.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
