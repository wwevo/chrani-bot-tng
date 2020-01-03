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

    @staticmethod
    def trigger_action_with_permission(*args, **kwargs):
        module = args[0]
        event_data = kwargs.get("event_data", [])
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        if dispatchers_steamid is None:
            # no sense in checking system-calls
            action_result = module.trigger_action(module, event_data=event_data)
            return action_result

        """ Manually for now, this will be handled by a permissions widget. """
        # even_data may contain a "has_permission" data-field.
        # this will be overwritten with the actual permissions, if a rule exists
        # all permissions default to Allowed if no rules are set here
        permission_denied = False
        dispatchers_permission_level = int(
            module.dom.data.get("module_players", {}).get("admins", {}).get(dispatchers_steamid, 2000)
        )
        module_identifier = module.get_module_identifier()

        if all([
            event_data[0].startswith("toggle_"),
            event_data[0].endswith("_widget_view")
        ]):
            if event_data[1]["action"] == "show_options":
                if dispatchers_permission_level >= 1:
                    permission_denied = True

        if module_identifier == "module_dom_management":
            if any([
                event_data[0] == "delete",
                event_data[0] == "select"
            ]):
                if any([
                    event_data[1]["action"] == "select_dom_element",
                    event_data[1]["action"] == "deselect_dom_element"
                ]):
                    if dispatchers_permission_level >= 2:
                        permission_denied = True
                    if str(dispatchers_steamid) == event_data[1]["dom_element_owner"]:
                        permission_denied = False
                if any([
                    event_data[1]["action"] == "delete_selected_dom_elements"
                ]):
                    if dispatchers_permission_level >= 2:
                        permission_denied = True

        if module_identifier == "module_players":
            if any([
                event_data[0] == "manage_players"
            ]):
                if any([
                    event_data[1]["action"] == "kick player"
                ]):
                    if dispatchers_permission_level >= 2:
                        permission_denied = True

        if module_identifier == "module_locations":
            if any([
                event_data[0] == "manage_locations",
                event_data[0] == "management_tools",
                event_data[0] == "toggle_locations_widget_view"
            ]):
                if any([
                    event_data[1]["action"] == "edit_location_entry",
                    event_data[1]["action"] == "enable_location_entry",
                    event_data[1]["action"] == "disable_location_entry"
                ]):
                    if dispatchers_permission_level > 2:
                        permission_denied = True
                    if str(dispatchers_steamid) == event_data[1]["dom_element_owner"]:
                        permission_denied = False
                if any([
                    event_data[1]["action"] == "show_create_new"
                ]):
                    if dispatchers_permission_level > 4:
                        permission_denied = True

        if module_identifier == "module_telnet":
            if any([
                    event_data[0] == "shutdown"
            ]):
                if dispatchers_permission_level > 2:
                    permission_denied = True

        if permission_denied:
            print("permission denied for {} ({})".format(event_data[0], dispatchers_steamid))

        event_data[1]["has_permission"] = not permission_denied
        action_result = module.trigger_action(module, event_data=event_data, dispatchers_steamid=dispatchers_steamid)
        return action_result

    @staticmethod
    def template_render_hook_with_permission(*args, **kwargs):
        module = args[0]
        template = kwargs.get("template", None)
        # print(module_identifier, args, kwargs)
        return module.template_render(*args, **kwargs)

    def set_permission_hooks(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission
            module.template_render_hook = self.template_render_hook_with_permission


loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
