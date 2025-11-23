import re
from bot.module import Module
from bot import loaded_modules_dict
from bot.logger import get_logger, log_telnet_raw
from bot.constants import TELNET_TIMEOUT_NORMAL, TELNET_TIMEOUT_RECONNECT
from time import time
from collections import deque
import telnetlib

logger = get_logger("telnet")


class Telnet(Module):
    tn = object

    telnet_buffer = str
    valid_telnet_lines = deque

    telnet_lines_to_process = deque
    telnet_command_queue = deque

    dom_element_root = list
    dom_element_select_root = list

    def __init__(self):
        self.telnet_command_queue = deque()
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "host": "127.0.0.1",
            "port": 8081,
            "password": "thisissecret",
            "web_username": "",
            "web_password": "",
            "max_queue_length": 100,
            "run_observer_interval": 3,
            "run_observer_interval_idle": 10,
            "max_telnet_buffer": 16384,
            "max_command_queue_execution": 6,
            "match_types_generic": {
                'log_start': [
                    r"\A(?P<datetime>\d{4}.+?)\s(?P<gametime_in_seconds>.+?)\sINF .*",
                    r"\ATime:\s(?P<servertime_in_minutes>.*)m\s",
                ],
                'log_end': [
                    r"\r\n$",
                    r"\sby\sTelnet\sfrom\s(.*)\:(\d.*)\s*$"
                ]
            },
            "dom_element_root": ["%dom_element_identifier%"],
            "dom_element_select_root": ["%dom_element_identifier%", "selected_by"]
        })
        setattr(self, "required_modules", [
            "module_dom",
            "module_dom_management",
            "module_webserver"
        ])

        self.next_cycle = 0
        self.telnet_response = ""

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_telnet"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.telnet_lines_to_process = deque(maxlen=self.options["max_queue_length"])
        self.valid_telnet_lines = deque(maxlen=self.options["max_queue_length"])
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.run_observer_interval_idle = self.options.get(
            "run_observer_interval_idle", self.default_options.get("run_observer_interval_idle", None)
        )
        self.max_command_queue_execution = self.options.get(
            "max_command_queue_execution", self.default_options.get("max_command_queue_execution", None)
        )
        self.dom_element_root = self.options.get(
            "dom_element_root", self.default_options.get("dom_element_root", None)
        )
        self.dom_element_select_root = self.options.get(
            "dom_element_select_root", self.default_options.get("dom_element_select_root", None)
        )
        self.telnet_buffer = ""

        self.last_execution_time = 0.0

        setattr(self, "last_connection_loss", None)
        setattr(self, "recent_telnet_response", None)
    # endregion

    # region Handling telnet initialization and authentication
    def setup_telnet(self):
        try:
            connection = telnetlib.Telnet(
                self.options.get("host"),
                self.options.get("port"),
                timeout=TELNET_TIMEOUT_NORMAL
            )
            self.tn = self.authenticate(connection, self.options.get("password"))
        except Exception as error:
            logger.error("telnet_connection_failed",
                        host=self.options.get("host"),
                        port=self.options.get("port"),
                        error=str(error),
                        error_type=type(error).__name__)
            raise IOError

        return True

    def authenticate(self, connection, password):
        try:
            # Waiting for the prompt.
            found_prompt = False
            while found_prompt is not True:
                telnet_response = connection.read_until(b"\r\n", timeout=TELNET_TIMEOUT_NORMAL).decode("utf-8")
                if re.match(r"Please enter password:\r\n", telnet_response):
                    found_prompt = True
                else:
                    raise IOError

            # Sending password.
            full_auth_response = ''
            authenticated = False
            connection.write(password.encode('ascii') + b"\r\n")
            while authenticated is not True:  # loop until authenticated, it's required
                telnet_response = connection.read_until(b"\r\n").decode("utf-8")
                full_auth_response += telnet_response.rstrip()
                # last 'welcome' line from the games telnet. it might change with a new game-version
                if re.match(r"Password incorrect, please enter password:\r\n", telnet_response) is not None:
                    logger.error("telnet_auth_failed",
                                host=self.options.get("host"),
                                port=self.options.get("port"),
                                reason="incorrect password")
                    raise ValueError
                if re.match(r"Logon successful.\r\n", telnet_response) is not None:
                    authenticated = True

            # Waiting for banner.
            full_banner = ''
            displayed_welcome = False
            while displayed_welcome is not True:  # loop until ready, it's required
                telnet_response = connection.read_until(b"\r\n").decode("utf-8")
                full_banner += telnet_response.rstrip("\r\n")
                if re.match(
                    r"Press 'help' to get a list of all commands. Press 'exit' to end session.",
                    telnet_response
                ):
                    displayed_welcome = True

        except Exception as e:
            raise IOError

        # Connection successful - no log needed
        return connection
    # endregion

    # region handling and preparing telnet-lines
    def is_a_valid_line(self, telnet_line):
        telnet_response_is_a_valid_line = False
        if self.has_valid_start(telnet_line) and self.has_valid_end(telnet_line):
            telnet_response_is_a_valid_line = True

        return telnet_response_is_a_valid_line

    def has_valid_start(self, telnet_response):
        telnet_response_has_valid_start = False
        for match_type in self.options.get("match_types_generic").get("log_start"):
            if re.match(match_type, telnet_response):
                telnet_response_has_valid_start = True

        return telnet_response_has_valid_start

    def has_valid_end(self, telnet_response):
        telnet_response_has_valid_end = False
        for match_type in self.options.get("match_types_generic").get("log_end"):
            if re.search(match_type, telnet_response):
                telnet_response_has_valid_end = True

        return telnet_response_has_valid_end

    def has_mutliple_lines(self, telnet_response):
        telnet_response_has_multiple_lines = False
        telnet_response_count = telnet_response.count(b"\r\n")
        if telnet_response_count >= 1:
            telnet_response_has_multiple_lines = telnet_response_count

        return telnet_response_has_multiple_lines

    @staticmethod
    def extract_lines(telnet_response):
        return [telnet_line for telnet_line in telnet_response.splitlines(True)]

    def get_a_bunch_of_lines_from_queue(self, this_many_lines):
        telnet_lines = []
        current_queue_length = 0
        done = False
        while (current_queue_length < this_many_lines) and not done:
            try:
                telnet_lines.append(self.telnet_lines_to_process.popleft())
                current_queue_length += 1
            except IndexError:
                done = True

        if len(telnet_lines) >= 1:
            return telnet_lines
        else:
            return []

    def add_telnet_command_to_queue(self, command, action_meta=None):
        from bot.tracking import tracker

        # Get tracking info from action_meta (passed through from trigger_action via event_data)
        tracking_id = action_meta.get('tracking_id') if action_meta else None
        debug_id = action_meta.get('debug_id') if action_meta else None

        if command not in self.telnet_command_queue:
            self.telnet_command_queue.appendleft(command)
            added = True
        else:
            added = False

        # Track if enabled
        if added and tracker.should_track(debug_id):
            # First command? Start tracking
            if tracker._test_start is None:
                tracker.start_tracking(debug_id)

            # Register command → tracking_id mapping
            tracker.register_command(command, tracking_id)

            # Log event
            tracker.log_event("QUEUED", tracking_id,
                q_size=len(self.telnet_command_queue)
            )
            tracker.increment_stat('queued')

        return added

    def execute_telnet_command_queue(self, this_many_lines):
        from bot.tracking import tracker

        telnet_command_list = []
        current_queue_length = 0
        done = False
        initial_queue_length = len(self.telnet_command_queue)
        while (current_queue_length < this_many_lines) and not done:
            try:
                telnet_command_list.append(self.telnet_command_queue.popleft())
                current_queue_length += 1
            except IndexError:
                done = True

        remaining_queue_length = len(self.telnet_command_queue)
        # print(initial_queue_length, ":", remaining_queue_length)

        for telnet_command in reversed(telnet_command_list):
            command = "{command}{line_end}".format(command=telnet_command, line_end="\r\n")

            try:
                self.tn.write(command.encode('ascii'))

                # Track if this command is being tracked
                tracking_id = tracker.get_tracking_id(telnet_command)
                if tracking_id:
                    tracker.log_event("SENT_TO_SERVER", tracking_id)
                    tracker.increment_stat('sent')

            except Exception as error:
                logger.error("telnet_command_send_failed",
                            command=telnet_command,
                            error=str(error),
                            error_type=type(error).__name__,
                            queue_size=remaining_queue_length)
    # endregion

    # ==================== Line Processing Helper Methods ====================

    def _should_exclude_from_logs(self, telnet_line: str) -> bool:
        """Check if a telnet line should be excluded from logs."""
        elements_excluded_from_logs = [
            "'lp'", "'gettime'", "'listents'",  # system calls
            "INF Time: ", "SleeperVolume", " killed by "  # irrelevant lines for now
        ]
        return any(exclude in telnet_line for exclude in elements_excluded_from_logs)

    def _store_valid_line(self, valid_line: str) -> None:
        """Store a valid telnet line in DOM."""
        # Store in DOM if clients are connected and line is relevant
        if not self._should_exclude_from_logs(valid_line):
            if len(self.webserver.connected_clients) >= 1:
                self.dom.data.append({
                    self.get_module_identifier(): {
                        "telnet_lines": valid_line
                    }
                }, maxlen=150)

        # Debug log only (disabled by default to avoid spam)
        # Uncomment next line and enable debug logging if needed for troubleshooting
        # logger.debug("telnet_line_received", line=valid_line[:100])

        self.valid_telnet_lines.append(valid_line)

    def _process_first_component(self, component: str) -> str:
        """
        Process the first component of telnet response.

        This might be the remainder of the previous run combined with new data.
        Returns the validated line or None.
        """
        if self.recent_telnet_response is not None:
            # Try to combine with previous incomplete response
            combined_line = f"{self.recent_telnet_response}{component}"
            if self.is_a_valid_line(combined_line):
                self.recent_telnet_response = None
                return combined_line.rstrip("\r\n")
            else:
                # Combined line still doesn't make sense
                stripped = combined_line.rstrip("\r\n")
                logger.warn("telnet_invalid_line_combined", line=stripped)
                self.recent_telnet_response = None
                return None
        else:
            # No previous response - check if this is an incomplete line to store
            if self.has_valid_start(component):
                self.recent_telnet_response = component
            else:
                # Invalid start - warn if not empty
                stripped = component.rstrip("\r\n")
                if len(stripped) != 0:
                    logger.warn("telnet_invalid_line_start", line=stripped)
            return None

    def _process_last_component(self, component: str) -> str:
        """
        Process the last component of telnet response.

        This might be the start of the next run.
        Returns the validated line or None.
        """
        if self.has_valid_start(component):
            # Store for next run
            self.recent_telnet_response = component
        # else: part of a telnet-command response, ignore
        return None

    def _process_middle_component(self, component: str) -> str:
        """
        Process a middle component (neither first nor last).

        These are usually incomplete lines or command responses.
        Returns None as these are typically not valid complete lines.
        """
        # Middle components are usually fragmented, ignore them
        return None

    def _process_line_component(
        self,
        component: str,
        component_index: int,
        total_components: int
    ) -> str:
        """
        Process a single component of the telnet response.

        Args:
            component: The line component to process
            component_index: 1-based index of this component
            total_components: Total number of components

        Returns:
            Validated telnet line or None
        """
        # Check if it's a complete, valid line first
        if self.is_a_valid_line(component):
            return component.rstrip("\r\n")

        # Handle incomplete lines based on position
        is_first = (component_index == 1)
        is_last = (component_index == total_components)
        is_single = (total_components == 1)

        if is_first and is_single:
            # Single incomplete component - special handling
            return self._process_first_component(component)
        elif is_first:
            # First of multiple - might combine with previous
            return self._process_first_component(component)
        elif is_last:
            # Last component - might be start of next
            return self._process_last_component(component)
        else:
            # Middle component - usually fragmented
            return self._process_middle_component(component)

    def _process_telnet_response_lines(self) -> None:
        """
        Process telnet response and extract valid lines.

        Handles line fragmentation across multiple reads and stores
        valid lines for further processing.
        """
        telnet_response_components = self.extract_lines(self.telnet_response)
        total_components = len(telnet_response_components)

        for index, component in enumerate(telnet_response_components, start=1):
            valid_line = self._process_line_component(
                component,
                index,
                total_components
            )

            if valid_line is not None:
                self.telnet_lines_to_process.append(valid_line)
                self._store_valid_line(valid_line)

    def _handle_connection_error(self, error: Exception) -> None:
        """Handle telnet connection errors and attempt reconnection."""
        try:
            self.setup_telnet()
            self.dom.data.upsert({
                self.get_module_identifier(): {
                    "server_is_online": True
                }
            })
        except (OSError, Exception, ConnectionRefusedError) as error:
            self.dom.data.upsert({
                self.get_module_identifier(): {
                    "server_is_online": False
                }
            })
            self.telnet_buffer = ""
            self.telnet_response = ""

            # Only log on first connection loss, not on every retry
            if self.last_connection_loss is None:
                logger.error("telnet_server_unreachable",
                            host=self.options.get("host"),
                            port=self.options.get("port"),
                            error=str(error),
                            error_type=type(error).__name__,
                            note="will retry every 10 seconds")

            self.last_connection_loss = time()

    def _update_telnet_buffer(self) -> None:
        """Update the telnet buffer with new response data."""
        self.telnet_buffer += self.telnet_response.lstrip()
        max_telnet_buffer = self.options.get(
            "max_telnet_buffer",
            self.default_options.get("max_telnet_buffer", 12288)
        )
        # Trim buffer to max size
        self.telnet_buffer = self.telnet_buffer[-max_telnet_buffer:]

        # Expose buffer to other modules via DOM
        self.dom.data.upsert({
            self.get_module_identifier(): {
                "telnet_buffer": self.telnet_buffer
            }
        })

    # ==================== Main Run Loop ====================

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            # Throttle connection attempts: only try if connected or timeout passed since last failure
            can_attempt_connection = (
                self.last_connection_loss is None or
                profile_start > self.last_connection_loss + TELNET_TIMEOUT_RECONNECT
            )

            if can_attempt_connection:
                try:
                    self.telnet_response = self.tn.read_very_eager().decode("utf-8")
                    
                    # Log raw telnet data for diagnostics (only if file logging is enabled)
                    if len(self.telnet_response) > 0:
                        log_telnet_raw(self.telnet_response, direction="incoming")
                        
                except (AttributeError, EOFError, ConnectionAbortedError, ConnectionResetError) as error:
                    self._handle_connection_error(error)
                except Exception as error:
                    logger.error("telnet_unforeseen_error",
                                error=str(error),
                                error_type=type(error).__name__,
                                host=self.options.get("host"),
                                port=self.options.get("port"))

            # Process any telnet response data
            if len(self.telnet_response) > 0:
                self._update_telnet_buffer()
                self._process_telnet_response_lines()

            if self.dom.data.get(self.get_module_identifier()).get("server_is_online") is True:
                self.execute_telnet_command_queue(self.max_command_queue_execution)

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Telnet().get_module_identifier()] = Telnet()
