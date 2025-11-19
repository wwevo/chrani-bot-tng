from bot.module import Module
from bot import loaded_modules_dict
from bot.logger import get_logger
from bot.constants import (
    PERMISSION_LEVEL_DEFAULT,
    PERMISSION_LEVEL_BUILDER,
    PERMISSION_LEVEL_PLAYER,
    is_moderator_or_higher,
    is_builder_or_higher
)

logger = get_logger("permissions")


class Permissions(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "default_player_password": None
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

    # ==================== Permission Check Helpers ====================

    @staticmethod
    def _is_owner(steamid: str, event_data: list) -> bool:
        """Check if user is the owner of the element being modified."""
        return str(steamid) == event_data[1].get("dom_element_owner", "")

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
    def _check_dom_management_permission(permission_level: int, steamid: str, event_data: list) -> bool:
        """Check permissions for DOM management actions."""
        action_name = event_data[0]
        sub_action = event_data[1].get("action", "")

        if action_name not in ["delete", "select"]:
            return False

        # Select/deselect: builders and below can only modify their own elements
        if sub_action in ["select_dom_element", "deselect_dom_element"]:
            if permission_level >= PERMISSION_LEVEL_BUILDER:
                return not Permissions._is_owner(steamid, event_data)
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

    # ==================== Main Permission Check ====================

    @staticmethod
    def trigger_action_with_permission(*args, **kwargs):
        """
        Check permissions before triggering an action.

        Permissions default to allowed if no specific rule matches.
        Module-specific permission checks are delegated to helper methods.
        """
        module = args[0]
        event_data = kwargs.get("event_data", [])
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

        # Default to allowing action
        permission_denied = False

        if dispatchers_steamid is not None:
            # Get user's permission level
            permission_level = int(
                module.dom.data.get("module_players", {}).get("admins", {}).get(
                    dispatchers_steamid, PERMISSION_LEVEL_DEFAULT
                )
            )
            module_identifier = module.get_module_identifier()

            # Run permission checks based on action and module
            permission_denied = (
                Permissions._check_toggle_flag_permission(permission_level, dispatchers_steamid, event_data) or
                Permissions._check_widget_options_permission(permission_level, event_data) or
                (module_identifier == "module_dom_management" and
                 Permissions._check_dom_management_permission(permission_level, dispatchers_steamid, event_data)) or
                (module_identifier == "module_players" and
                 Permissions._check_players_permission(permission_level, event_data)) or
                (module_identifier == "module_locations" and
                 Permissions._check_locations_permission(permission_level, dispatchers_steamid, event_data)) or
                (module_identifier == "module_telnet" and
                 Permissions._check_telnet_permission(permission_level, event_data))
            )

            if permission_denied:
                logger.warn("permission_denied",
                           action=event_data[0],
                           user=dispatchers_steamid,
                           permission_level=permission_level)

            event_data[1]["has_permission"] = not permission_denied

        # Execute the action
        return module.trigger_action(module, event_data=event_data, dispatchers_steamid=dispatchers_steamid)

    @staticmethod
    def template_render_hook_with_permission(*args, **kwargs):
        module = args[0]
        return module.template_render(*args, **kwargs)

    def set_permission_hooks(self):
        for identifier, module in loaded_modules_dict.items():
            module.trigger_action_hook = self.trigger_action_with_permission
            module.template_render_hook = self.template_render_hook_with_permission


loaded_modules_dict[Permissions().get_module_identifier()] = Permissions()
