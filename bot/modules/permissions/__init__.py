from bot.module import Module
from bot import loaded_modules_dict
from time import time


class Permissions(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        setattr(self, "required_modules", [
            'module_dom',
            'module_players'
        ])
        self.next_cycle = 0
        self.run_observer_interval = 5
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_permissions"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    def trigger_action_with_permission(self, module, event_data, dispatchers_id=None):
        """ TODO: permission check to be added here!! """
        if any([
                event_data[0] == "toggle_player_table_widget_view",
                event_data[0] == "toggle_whitelist_widget_view",
                event_data[0] == "toggle_webserver_status_view"
        ]):
            if event_data[1]["action"] == "show_options":
                if int(module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) >= 2:
                    return False

        return module.trigger_action(module, event_data, dispatchers_id)

    def run(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission

        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
