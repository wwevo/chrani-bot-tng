"""
Thread tracking system for monitoring action threads and detecting missing callbacks.
"""
from threading import Thread, Lock
from time import time
from datetime import datetime
import string
import random


class ThreadTracker:
    """
    Tracks all spawned action threads and monitors for missing callbacks.

    Actions should call callbacks (success/skip/fail) to mark completion.
    If a thread runs longer than timeout without calling any callback,
    it's logged as a warning (indicates poorly written action).

    Includes breadcrumb tracking for detailed debugging of action execution flow.
    """

    def __init__(self, timeout_seconds=5, check_interval_seconds=5):
        self.registry = {}  # tracking_id -> thread_info
        self.lock = Lock()
        self.timeout_seconds = timeout_seconds
        self.check_interval_seconds = check_interval_seconds
        self.monitor_thread = None
        self.is_running = False

    def start(self):
        """Start the background monitoring thread."""
        if self.is_running:
            return

        self.is_running = True
        self.monitor_thread = Thread(target=self._monitor_timeouts, daemon=True)
        self.monitor_thread.start()
        print("[ThreadTracker] Started monitoring with {}s timeout".format(self.timeout_seconds))

    def stop(self):
        """Stop the background monitoring thread."""
        self.is_running = False

    def register_thread(self, tracking_id, action_id, module_name, thread_obj):
        """
        Register a new action thread.

        Args:
            tracking_id: Unique identifier for this action execution
            action_id: The action's identifier (e.g., "lp", "say_to_player")
            module_name: The module name (e.g., "module_players")
            thread_obj: The Thread object that was created
        """
        with self.lock:
            self.registry[tracking_id] = {
                "tracking_id": tracking_id,
                "action_id": action_id,
                "module_name": module_name,
                "start_time": time(),
                "start_datetime": datetime.now(),
                "status": "running",
                "completed_via": None,
                "thread_obj": thread_obj,
                "breadcrumbs": []  # List of (timestamp, message) tuples
            }

    def update_progress(self, tracking_id, message):
        """
        Add a breadcrumb to track action progress.

        Args:
            tracking_id: The tracking ID from action_meta
            message: Progress message (e.g., "waiting for telnet ticket")
        """
        with self.lock:
            if tracking_id not in self.registry:
                return

            thread_info = self.registry[tracking_id]
            thread_info["breadcrumbs"].append({
                "time": time(),
                "datetime": datetime.now(),
                "message": message
            })

    def mark_completed(self, tracking_id, callback_type):
        """
        Mark a thread as completed via callback.

        Args:
            tracking_id: The tracking ID from action_meta
            callback_type: "callback_success", "callback_skip", or "callback_fail"
        """
        with self.lock:
            if tracking_id not in self.registry:
                # This shouldn't happen, but handle gracefully
                return

            thread_info = self.registry[tracking_id]
            thread_info["status"] = "completed"
            thread_info["completed_via"] = callback_type

            # Add final breadcrumb
            thread_info["breadcrumbs"].append({
                "time": time(),
                "datetime": datetime.now(),
                "message": "marked completed via {}".format(callback_type)
            })

            # Remove from registry after completion
            del self.registry[tracking_id]

    def get_running_threads(self):
        """Get list of currently running threads (for debugging)."""
        with self.lock:
            return list(self.registry.values())

    def _monitor_timeouts(self):
        """Background thread that checks for action threads without callbacks."""
        from time import sleep

        while self.is_running:
            sleep(self.check_interval_seconds)
            current_time = time()

            with self.lock:
                threads_to_warn = []
                for tracking_id, thread_info in list(self.registry.items()):
                    runtime = current_time - thread_info["start_time"]

                    # Check if thread exceeded timeout without callback
                    if runtime > self.timeout_seconds and thread_info["status"] == "running":
                        # Copy thread info for warning (outside lock)
                        threads_to_warn.append({
                            "action_id": thread_info["action_id"],
                            "module_name": thread_info["module_name"],
                            "runtime": runtime,
                            "tracking_id": tracking_id,
                            "start_datetime": thread_info["start_datetime"],
                            "thread_alive": thread_info["thread_obj"].is_alive(),
                            "breadcrumbs": list(thread_info["breadcrumbs"])  # Copy list
                        })
                        # Mark as timeout to avoid repeated warnings
                        thread_info["status"] = "timeout"

            # Print warnings outside the lock
            for warning in threads_to_warn:
                self._print_timeout_warning(warning)

    def _print_timeout_warning(self, warning):
        """Print detailed timeout warning with breadcrumbs."""
        now = datetime.now()
        print("\n" + "="*80)
        print("[{}] [THREAD-TIMEOUT]".format(now.strftime("%Y-%m-%d %H:%M:%S")))
        print("  Action: '{}' from '{}'".format(warning["action_id"], warning["module_name"]))
        print("  Tracking ID: {}".format(warning["tracking_id"]))
        print("  Started at: {}".format(warning["start_datetime"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]))
        print("  Running for: {:.1f}s without callback".format(warning["runtime"]))
        print("  Thread alive: {}".format(warning["thread_alive"]))

        if warning["breadcrumbs"]:
            print("  Breadcrumbs:")
            for crumb in warning["breadcrumbs"]:
                timestamp = crumb["datetime"].strftime("%H:%M:%S.%f")[:-3]
                print("    [{}] {}".format(timestamp, crumb["message"]))
        else:
            print("  Breadcrumbs: (none - action never called update_progress)")

        print("="*80 + "\n")

    @staticmethod
    def generate_tracking_id(size=12):
        """
        Generate a unique tracking ID.

        Args:
            size: Length of the ID (default 12 chars for better uniqueness)

        Returns:
            String with random uppercase letters and digits
        """
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))


# Global singleton instance
thread_tracker = ThreadTracker()
