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
            'module_players',
            'module_webserver'
        ])
        self.next_cycle = 0
        self.run_observer_interval = 5
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_permissions"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    def start(self):
        self.set_permission_hooks()
        self.all_available_actions_dict = self.get_all_available_actions()
        self.all_available_widgets_dict = self.get_all_available_widgets()
        Module.start(self)
    # endregion

    @staticmethod
    def get_all_available_actions():
        all_available_actions_dict = {}
        for loaded_module_identifier, loaded_module in loaded_modules_dict.items():
            if len(loaded_module.available_actions_dict) >= 1:
                all_available_actions_dict[loaded_module_identifier] = loaded_module.available_actions_dict

        return all_available_actions_dict

    @staticmethod
    def get_all_available_widgets():
        all_available_widgets_dict = {}
        for loaded_module_identifier, loaded_module in loaded_modules_dict.items():
            if len(loaded_module.available_widgets_dict) >= 1:
                all_available_widgets_dict[loaded_module_identifier] = loaded_module.available_widgets_dict

        return all_available_widgets_dict

    def trigger_action_with_permission(self, module, event_data, dispatchers_id=None):
        """ Manually for now, this will be handled by a permissions widget. """
        permission_denied = False

        if any([
                event_data[0] == "toggle_player_table_widget_view",
                event_data[0] == "toggle_whitelist_widget_view",
                event_data[0] == "toggle_webserver_status_view",
                event_data[0] == "toggle_permissions_view"
        ]):
            if event_data[1]["action"] == "show_options":
                if int(module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) >= 2:
                    permission_denied = True

        if any([
                event_data[0] == "manage_whitelist",
        ]):
            if any([
                event_data[1]["action"] == "activate_whitelist",
                event_data[1]["action"] == "deactivate_whitelist",
                event_data[1]["action"] == "remove_from_whitelist",
                event_data[1]["action"] == "add_to_whitelist"
            ]):
                if int(module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 2:
                    permission_denied = True

        if any([
                event_data[0] == "shutdown",
                event_data[0] == "switch_data_transfer"
        ]):
            if int(module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 2:
                permission_denied = True

        if not permission_denied:
            return module.trigger_action(module, event_data, dispatchers_id)
        else:
            return False

    def set_permission_hooks(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission
            module.trigger_widget_hook = self.trigger_widget_with_permission
            module.trigger_widget_component_hook = self.trigger_widget_component_with_permission

    def trigger_widget_with_permission(self, module, dispatchers_steamid=None):
        permission_denied = False
        player_access_level = int(
            module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_steamid, 2000)
        )

        if isinstance(module.available_widgets_dict, dict) and len(module.available_widgets_dict) >= 1:
            for name, widget in module.available_widgets_dict.items():
                if widget["main_widget"] is not None:
                    if any([
                        name == "permissions_widget" and player_access_level > 2,
                        name == "gameserver_status_widget" and player_access_level > 2,
                        name == "manage_whitelist_widget" and player_access_level > 4
                    ]):
                        permission_denied = True

        if not permission_denied:
            return module.trigger_widget(module, dispatchers_steamid)
        else:
            return False

    def trigger_widget_component_with_permission(self, module, event_data, dispatchers_steamid=None):
        permission_denied = False
        player_access_level = int(
            module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_steamid, 2000)
        )

        if isinstance(module.available_widgets_dict, dict) and len(module.available_widgets_dict) >= 1:
            for name, widget in module.available_widgets_dict.items():
                if widget["main_widget"] is not None:
                    if any([
                        name == "permissions_widget" and player_access_level > 2,
                        name == "gameserver_status_widget" and player_access_level > 2,
                        name == "manage_whitelist_widget" and player_access_level > 4
                    ]):
                        permission_denied = True

        if not permission_denied:
            return module.trigger_widget_component(module, event_data, dispatchers_steamid)
        else:
            return False

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
