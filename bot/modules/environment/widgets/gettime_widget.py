from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def update_widget(module, updated_values_dict, old_values_dict):
    gametime = updated_values_dict.get("last_recorded_gametime", None)
    old_gametime = old_values_dict.get("last_recorded_gametime", None)
    if gametime is None:
        module.manually_trigger_action(["gettime", {}])
        return False

    if gametime == old_gametime:
        return

    template_frontend = module.templates.get_template('gametime_widget_frontend.html')
    data_to_emit = template_frontend.render(
        last_recorded_gametime=gametime,
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "gametime_widget",
            "type": "div"
        }
    )
    return gametime


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": None,
    "handlers": {
        "last_recorded_gametime": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
