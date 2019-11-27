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
            'module_locations',
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
        """ all modules have been loaded and initialized by now. we can bend the rules here."""
        self.set_permission_hooks()
        self.all_available_actions_dict = self.get_all_available_actions_dict()
        self.all_available_widgets_dict = self.get_all_available_widgets_dict()
        Module.start(self)
    # endregion

    def trigger_action_with_permission(self, module, event_data, dispatchers_id=None):
        """ Manually for now, this will be handled by a permissions widget. """
        # even_data may contain a "has_permission" data-field.
        # this will be overwritten with the actual permissions, if a rule exists
        # all permissions default to Allowed if no rules are set here
        permission_denied = False

        if any([
            event_data[0] == "toggle_telnet_widget_view",
            event_data[0] == "toggle_locations_widget_view",
            event_data[0] == "toggle_entities_widget_view",
            event_data[0] == "toggle_players_widget_view",
            event_data[0] == "toggle_webserver_status_widget_view",
        ]):
            if event_data[1]["action"] == "show_options":
                if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) >= 2:
                    permission_denied = True
            if event_data[1]["action"] == "edit_location_entry":
                if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) >= 2:
                    permission_denied = True
                if str(dispatchers_id) == event_data[1]["dom_element_owner"]:
                    permission_denied = False
            if event_data[1]["action"] == "show_create_new":
                if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 4:
                    permission_denied = True

        if module.get_module_identifier() == "module_dom_management":
            if any([
                event_data[0] == "sed",
            ]):
                if any([
                    event_data[1]["action"] == "edit_location_entry",
                    event_data[1]["action"] == "select_dom_element",
                    event_data[1]["action"] == "deselect_dom_element",
                    event_data[1]["action"] == "enable_location_entry",
                    event_data[1]["action"] == "disable_location_entry",
                    event_data[1]["action"] == "delete_selected_dom_elements"
                ]):
                    if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 2:
                        permission_denied = True
                    if str(dispatchers_id) == event_data[1]["dom_element_owner"]:
                        permission_denied = False

        if module.get_module_identifier() == "module_players":
            if any([
                event_data[0] == "manage_players",
            ]):
                if any([
                    event_data[1]["action"] == "kick player",
                ]):
                    if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) >= 2:
                        permission_denied = True

        if module.get_module_identifier() == "module_locations":
            if any([
                event_data[0] == "manage_locations",
                event_data[0] == "management_tools",
                event_data[0] == "sed",
                event_data[0] == "toggle_locations_view"
            ]):
                if any([
                    event_data[1]["action"] == "edit_location_entry",
                    event_data[1]["action"] == "select_dom_element",
                    event_data[1]["action"] == "deselect_dom_element",
                    event_data[1]["action"] == "enable_location_entry",
                    event_data[1]["action"] == "disable_location_entry"
                ]):
                    if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 2:
                        permission_denied = True
                    if str(dispatchers_id) == event_data[1]["dom_element_owner"]:
                        permission_denied = False
                if any([
                    event_data[1]["action"] == "show_create_new",
                ]):
                    if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 4:
                        permission_denied = True

        if module.get_module_identifier() == "module_telnet":
            if any([
                    event_data[0] == "shutdown"
            ]):
                if int(self.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_id, 2000)) > 2:
                    permission_denied = True


        if permission_denied:
            print("permission denied for {} ({})".format(event_data[0], dispatchers_id))

        event_data[1]["has_permission"] = not permission_denied
        return module.trigger_action(module, event_data, dispatchers_id)

    @staticmethod
    def template_render_hook_with_permission(module, template, **kwargs):
        # print(module.get_module_identifier(), template.name)
        return module.template_render(module, template, **kwargs)

    def set_permission_hooks(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission
            module.template_render_hook = self.template_render_hook_with_permission

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
