import os
import json
from datetime import datetime
from collections import defaultdict


class CommandTracker:
    def __init__(self):
        self._enabled = os.getenv('PROFILING_ENABLED', '').lower() == 'true'
        self._command_to_id = {}  # {"lp": "A4B2C1D3"}
        self._tracking_commands = {}  # {"lp": True}
        self._events = []
        self._stats = defaultdict(int)
        self._test_start = None
        self._log_file = None
        self._debug_id = None

    def should_track(self, debug_id):
        return self._enabled and debug_id in self._tracking_commands

    def start_tracking(self, debug_id):
        """Called when first command with debug_id is queued."""
        if not self._enabled:
            return

        self._debug_id = debug_id
        self._tracking_commands[debug_id] = True
        self._test_start = datetime.now()

        timestamp = self._test_start.strftime('%Y%m%d_%H%M%S')
        log_dir = os.path.join(os.path.dirname(__file__), 'diagnostic_logs')
        os.makedirs(log_dir, exist_ok=True)
        self._log_file = os.path.join(log_dir, f'command_tracking_{debug_id}_{timestamp}.json')

    def register_command(self, command, tracking_id):
        """Store tracking_id for command string."""
        self._command_to_id[command] = tracking_id

    def get_tracking_id(self, command):
        """Get tracking_id for command string."""
        return self._command_to_id.get(command)

    def log_event(self, event_type, tracking_id=None, **kwargs):
        if not self._enabled:
            return

        self._events.append({
            "ts": datetime.now().isoformat(),
            "event": event_type,
            "id": tracking_id,
            **kwargs
        })

    def increment_stat(self, stat_name):
        if self._enabled:
            self._stats[stat_name] += 1

    def write_results(self):
        """Write final results. Call after test completes."""
        if not self._enabled or not self._log_file:
            return

        test_duration = (datetime.now() - self._test_start).total_seconds()

        output = {
            "command": self._debug_id,
            "test_duration": test_duration,
            "commands_queued": self._stats['queued'],
            "commands_sent": self._stats['sent'],
            "command_results_matched": self._stats['matched'],
            "timeline": self._events
        }

        with open(self._log_file, 'w') as f:
            json.dump(output, f, indent=2)


tracker = CommandTracker()
