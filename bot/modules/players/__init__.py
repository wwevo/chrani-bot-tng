from bot.module import Module
from bot import loaded_modules_dict
from bot.logger import get_logger
from time import time

logger = get_logger("players")


class Players(Module):
    dom_element_root = list
    dom_element_select_root = list

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 3,
            "dom_element_root": [],
            "dom_element_select_root": ["selected_by"]
        })

        setattr(self, "required_modules", [
            "module_webserver",
            "module_dom",
            "module_dom_management",
            "module_game_environment",
            "module_telnet"
        ])

        self.next_cycle = 0
        
        # Registry for pending teleports (event-based completion tracking)
        # Format: {steamid: {entity_id, target_pos, timestamp, timeout, callbacks, event_data}}
        self.pending_teleports = {}
        
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_players"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.dom_element_root = self.options.get(
            "dom_element_root", self.default_options.get("dom_element_root", None)
        )
        self.dom_element_select_root = self.options.get(
            "dom_element_select_root", self.default_options.get("dom_element_select_root", None)
        )
    # endregion

    def check_pending_teleports_timeout(self):
        """
        Check for timed-out pending teleports and trigger fail callbacks.
        
        This method is called in the run loop to handle teleports that didn't
        receive a PlayerSpawnedInWorld confirmation within the timeout period.
        """
        current_time = time()
        timed_out_steamids = []
        
        # Find all timed-out teleports
        for steamid, teleport_info in self.pending_teleports.items():
            timestamp = teleport_info.get("timestamp", 0)
            timeout = teleport_info.get("timeout", 8)
            
            if current_time > timestamp + timeout:
                timed_out_steamids.append(steamid)
                
                # Trigger fail callback
                callback_fail = teleport_info.get("callback_fail")
                event_data = teleport_info.get("event_data")
                dispatchers_steamid = teleport_info.get("dispatchers_steamid")
                
                if callback_fail and event_data:
                    event_data[1]["fail_reason"] = "action timed out"
                    try:
                        callback_fail(self, event_data, dispatchers_steamid)
                    except Exception as e:
                        logger.error("teleport_timeout_callback_failed",
                                   steamid=steamid,
                                   error=str(e),
                                   error_type=type(e).__name__)
        
        # Remove timed-out teleports from registry
        for steamid in timed_out_steamids:
            del self.pending_teleports[steamid]
            logger.debug("teleport_timeout_removed", steamid=steamid)

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            # Check for timed-out teleports (non-blocking timeout handling)
            self.check_pending_teleports_timeout()

            self.trigger_action_hook(self, event_data=["getadmins", {
                "disable_after_success": True
            }])
            self.trigger_action_hook(self, event_data=["lp", {}])

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Players().get_module_identifier()] = Players()
