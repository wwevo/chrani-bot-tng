from bot import loaded_modules_dict
from bot.constants import (
    PERMISSION_LEVEL_DEFAULT,
    PERMISSION_LEVEL_BUILDER,
    PERMISSION_LEVEL_PLAYER,
    is_moderator_or_higher
)
from bot.module import Module


class Permissions(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "default_player_password": None,
            "run_observer_interval": 5
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_players',
            'module_telnet',
            'module_webserver'
        ])

        self.next_cycle = 0
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_permissions"

    def setup(self, options=None):
        Module.setup(self, options)
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )

    def on_start(self):
        """ all modules have been loaded and initialized by now. we can bend the rules here."""
        self.set_permission_hooks()
        self.all_available_actions_dict = self.get_all_available_actions_dict()
        self.all_available_widgets_dict = self.get_all_available_widgets_dict()

    def trigger_action_with_permission(self, module, action_meta, dispatchers_id=None):
        action_id = action_meta.get("id")
        action_meta = module.available_actions_dict[action_id]
        if dispatchers_id is not None:
            permission_level = int(
                module.dom.data.get("module_players", {}).get("admins", {}).get(
                    dispatchers_id, PERMISSION_LEVEL_DEFAULT
                )
            )
            module_identifier = module.get_module_identifier()

            permission_denied = (
                    Permissions._check_toggle_flag_permission(permission_level, dispatchers_id, action_id) or
                    Permissions._check_widget_options_permission(permission_level, action_id) or
                    Permissions._check_dom_management_permission(permission_level, action_meta, dispatchers_id) or
                    (module_identifier == "module_players" and
                     Permissions._check_players_permission(permission_level, action_id)) or
                    (module_identifier == "module_telnet" and
                     Permissions._check_telnet_permission(permission_level, action_id))
            )

            if permission_denied:
                print("permission_denied")

            action_meta["has_permission"] = not permission_denied

        return module.trigger_action(module, action_meta, dispatchers_id)

    @staticmethod
    def _is_owner(steamid: str, event_data: list) -> bool:
        """Check if user is the owner of the element being modified."""
        return str(steamid) == event_data[1].get("owner_id", "")

    @staticmethod
    def _check_toggle_flag_permission(permission_level: int, steamid: str, event_data: list) -> bool:
        """Check permission for toggle_enabled_flag action."""
        if event_data[0] != "toggle_enabled_flag":
            return False

        # Builders and below can only edit their own elements
        if permission_level >= PERMISSION_LEVEL_BUILDER:
            return not Permissions._is_owner(steamid, event_data)
        return False

    @staticmethod
    def _check_widget_options_permission(permission_level: int, event_data: list) -> bool:
        """Check permission for widget options view."""
        if not (event_data[0].startswith("toggle_") and event_data[0].endswith("_widget_view")):
            return False

        if event_data[1].get("action") == "show_options":
            # Only moderators and admins can see options
            return not is_moderator_or_higher(permission_level)
        return False

    @staticmethod
    def _check_dom_management_permission(permission_level: int, action_meta, dispatchers_id=None) -> bool:
        action_id = action_meta.get("id")
        dom_action_id = action_meta.get("action_data").get("action")
        if dom_action_id not in ["delete", "select"]:
            return False

        try:
            sub_action = action_id[1].get("action")
        except AttributeError as error:
            return False

        # Select/deselect: builders and below can only modify their own elements
        if sub_action in ["select_dom_element", "deselect_dom_element"]:
            if permission_level >= PERMISSION_LEVEL_BUILDER:
                return not Permissions._is_owner(dispatchers_id, action_id)
            return False

        # Delete: only moderators and admins
        if sub_action == "delete_selected_dom_elements":
            return permission_level >= PERMISSION_LEVEL_BUILDER

        return False

    @staticmethod
    def _check_players_permission(permission_level: int, event_data: list) -> bool:
        """Check permissions for player management actions."""
        if event_data[0] == "kick_player":
            # Only builder and above can kick players
            return permission_level > PERMISSION_LEVEL_BUILDER
        return False

    @staticmethod
    def _check_locations_permission(permission_level: int, steamid: str, event_data: list) -> bool:
        """Check permissions for location management actions."""
        action_name = event_data[0]
        sub_action = event_data[1].get("action", "")

        if action_name not in ["edit_location", "management_tools", "toggle_locations_widget_view"]:
            return False

        # Edit/enable/disable: builders and below can only modify their own locations
        if sub_action in ["edit_location_entry", "enable_location_entry", "disable_location_entry"]:
            if permission_level >= PERMISSION_LEVEL_BUILDER:
                return not Permissions._is_owner(steamid, event_data)
            return False

        # Create new: only players and above
        if sub_action == "show_create_new":
            return permission_level > PERMISSION_LEVEL_PLAYER

        return False

    @staticmethod
    def _check_telnet_permission(permission_level: int, event_data: list) -> bool:
        """Check permissions for telnet actions."""
        if event_data[0] == "shutdown":
            # Only moderators and admins can shutdown server
            return permission_level >= PERMISSION_LEVEL_BUILDER
        return False

    @staticmethod
    def template_render_hook_with_permission(*args, **kwargs):
        module = args[0]
        return module.template_render(*args, **kwargs)

    def set_permission_hooks(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission
            module.template_render_hook = self.template_render_hook_with_permission

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
