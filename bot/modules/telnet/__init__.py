import re
from bot.module import Module
from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL, TELNET_TIMEOUT_RECONNECT, TELNET_LINES_MAX_HISTORY
from time import time
from collections import deque
from queue import Queue, Empty
import telnetlib


class TelnetRequest:
    """Represents a pending telnet command request with its own response buffer."""

    def __init__(self, command, regex, timeout):
        self.command = command
        self.regex = regex
        self.queued_at = time()
        self.timeout = timeout
        self.response_buffer = ""
        self.is_active = False
        self.result_queue = Queue(maxsize=1)
        self.completed = False

    def add_raw_data(self, raw_data):
        """Add raw telnet data to buffer and check if regex matches."""
        self.response_buffer += raw_data

        # Try to match regex against accumulated buffer
        match = re.search(self.regex, self.response_buffer, re.MULTILINE | re.DOTALL)
        if match:
            self.result_queue.put({
                'success': True,
                'buffer': self.response_buffer,
                'match': match
            })
            self.completed = True
            return True
        return False

    def timeout_expired(self):
        """Called when timeout is reached - provides debug buffer."""
        if not self.completed:
            self.result_queue.put({
                'success': False,
                'buffer': self.response_buffer,
                'match': None
            })
            self.completed = True

    def wait(self):
        """Block until result arrives (match or timeout)."""
        try:
            return self.result_queue.get(timeout=self.timeout + 1)
        except Empty:
            # Shouldn't happen as telnet loop handles timeouts, but safety
            return {
                'success': False,
                'buffer': self.response_buffer,
                'match': None
            }


class Telnet(Module):
    tn = object

    valid_telnet_lines = deque
    telnet_lines_to_process = deque
    telnet_command_queue = deque
    pending_requests = list

    dom_element_root = list
    dom_element_select_root = list

    def __init__(self):
        self.telnet_command_queue = deque()
        self.pending_requests = []
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
            "max_command_queue_execution": 15,
            "match_types_generic": {
                'log_start': [
                    r"\A(?P<datetime>\d{4}.+?)\s(?P<gametime_in_seconds>.+?)\s(INF|WRN) .*",
                    r"\ATime:\s(?P<servertime_in_minutes>.*)m\s",
                ],
                'log_end': [
                    r"\r\n$",
                    r"\sby\sTelnet\sfrom\s(.*)\:(\d.*)\s*$"
                ]
            }
        })
        setattr(self, "required_modules", [
            "module_dom",
        ])

        self.next_cycle = 0
        self.telnet_response = ""

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_telnet"

    def setup(self, options=None):
        Module.setup(self, options or {})

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

        self.last_execution_time = 0.0

        setattr(self, "last_connection_loss", None)
        setattr(self, "recent_telnet_response", None)

    def setup_telnet(self):
        try:
            connection = telnetlib.Telnet(
                self.options.get("host"),
                self.options.get("port"),
                timeout=TELNET_TIMEOUT_NORMAL
            )
            self.tn = self.authenticate(connection, self.options.get("password"))
        except Exception as error:
            raise IOError

        return True

    def authenticate(self, connection, password):
        try:
            found_prompt = False
            while found_prompt is not True:
                telnet_response = connection.read_until(b"\r\n", timeout=TELNET_TIMEOUT_NORMAL).decode("utf-8")
                if re.match(r"Please enter password:\r\n", telnet_response):
                    found_prompt = True
                else:
                    raise IOError

            full_auth_response = ''
            authenticated = False
            connection.write(password.encode('ascii') + b"\r\n")
            while authenticated is not True:
                telnet_response = connection.read_until(b"\r\n").decode("utf-8")
                full_auth_response += telnet_response.rstrip()
                if re.match(r"Password incorrect, please enter password:\r\n", telnet_response) is not None:
                    raise ValueError
                if re.match(r"Logon successful.\r\n", telnet_response) is not None:
                    authenticated = True

            full_banner = ''
            displayed_welcome = False
            while displayed_welcome is not True:
                telnet_response = connection.read_until(b"\r\n").decode("utf-8")
                full_banner += telnet_response.rstrip("\r\n")
                if re.match(
                        r"Press 'help' to get a list of all commands. Press 'exit' to end session.",
                        telnet_response
                ):
                    displayed_welcome = True

        except Exception as e:
            raise IOError

        return connection

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

    def send_command(self, command, regex, timeout=TELNET_TIMEOUT_NORMAL):
        """
        New ticket-based API: Send command and get ticket for waiting.

        Args:
            command: Command string to send (e.g., "lp", "sayplayer 171 'Hello'")
            regex: Compiled or string regex to match response
            timeout: Seconds to wait for response

        Returns:
            TelnetRequest ticket object with wait() method
        """
        ticket = TelnetRequest(command, regex, timeout)
        self.pending_requests.append(ticket)
        self.telnet_command_queue.appendleft(command)
        return ticket

    def add_telnet_command_to_queue(self, command):
        """Legacy API - kept for backward compatibility with old actions."""
        if command not in self.telnet_command_queue:
            self.telnet_command_queue.appendleft(command)
            return True

        return False

    def execute_telnet_command_queue(self, this_many_lines):
        telnet_command_list = []
        current_queue_length = 0
        done = False
        while (current_queue_length < this_many_lines) and not done:
            try:
                telnet_command_list.append(self.telnet_command_queue.popleft())
                current_queue_length += 1
            except IndexError:
                done = True

        remaining_queue_length = len(self.telnet_command_queue)

        for telnet_command in reversed(telnet_command_list):
            command = "{command}{line_end}".format(command=telnet_command, line_end="\r\n")

            try:
                self.tn.write(command.encode('ascii'))

            except Exception as error:
                pass

    def _should_exclude_from_logs(self, telnet_line: str) -> bool:
        """Check if a telnet line should be excluded from logs."""
        elements_excluded_from_logs = [
            "'lp'", "'gettime'", "'listents'",  # system calls
            "INF Time: ", "SleeperVolume", " killed by "  # irrelevant lines for now
        ]
        return any(exclude in telnet_line for exclude in elements_excluded_from_logs)

    def _store_valid_line(self, valid_line: str) -> None:
        """Store line for webinterface history."""
        if not self._should_exclude_from_logs(valid_line):
            self.dom.data.append({
                self.get_module_identifier(): {
                    "telnet_lines": valid_line
                }
            }, maxlen=TELNET_LINES_MAX_HISTORY)

        self.valid_telnet_lines.append(valid_line)

    def _extract_timestamp_from_line(self, line: str):
        """Extract timestamp from telnet line for correlation."""
        timestamp_match = re.match(r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
        if timestamp_match:
            # Parse timestamp to float for comparison
            # For now, just return time() as we queue commands with time()
            # Server timestamp would need parsing, using queue time is safer
            return None
        return None

    def _extract_command_from_line(self, line: str):
        """Extract command from 'Executing command' line."""
        match = re.search(r"Executing command '([^']+)'", line)
        if match:
            return match.group(1)
        return None

    def _route_raw_to_tickets(self, raw_data: str) -> None:
        """Route raw telnet data to tickets - they accumulate everything until match or timeout."""

        # Check if any command is starting in this raw data
        if "Executing command" in raw_data:
            for line in raw_data.split('\n'):
                if "Executing command" in line:
                    command = self._extract_command_from_line(line)
                    if command:
                        # Activate all tickets waiting for this command
                        for ticket in self.pending_requests:
                            if ticket.command == command and not ticket.is_active:
                                ticket.is_active = True

        # Send raw data to all active tickets
        for ticket in self.pending_requests:
            if ticket.is_active:
                completed = ticket.add_raw_data(raw_data)
                if completed:
                    ticket.is_active = False

    def _check_expired_tickets(self, current_time: float) -> None:
        """Check for and handle expired ticket timeouts."""
        for ticket in self.pending_requests[:]:  # Copy list for safe removal
            if current_time - ticket.queued_at > ticket.timeout:
                ticket.timeout_expired()
                self.pending_requests.remove(ticket)

        # Also remove completed tickets
        self.pending_requests = [t for t in self.pending_requests if not t.completed]

    def _process_first_component(self, component: str) -> str:
        if self.recent_telnet_response is not None:
            combined_line = f"{self.recent_telnet_response}{component}"
            if self.is_a_valid_line(combined_line):
                self.recent_telnet_response = None
                return combined_line.rstrip("\r\n")
            else:
                stripped = combined_line.rstrip("\r\n")
                print("telnet_invalid_line_combined", line=stripped)
                self.recent_telnet_response = None
                return None
        else:
            if self.has_valid_start(component):
                self.recent_telnet_response = component
            else:
                stripped = component.rstrip("\r\n")
                if len(stripped) != 0:
                    print("telnet_invalid_line_start", line=stripped)
            return None

    def _process_last_component(self, component: str) -> str:
        if self.has_valid_start(component):
            self.recent_telnet_response = component
        return None

    def _process_middle_component(self, component: str) -> str:
        return None

    def _process_line_component(
            self,
            component: str,
            component_index: int,
            total_components: int
    ) -> str:
        if self.is_a_valid_line(component):
            return component.rstrip("\r\n")

        is_first = (component_index == 1)
        is_last = (component_index == total_components)
        is_single = (total_components == 1)

        if is_first and is_single:
            return self._process_first_component(component)
        elif is_first:
            return self._process_first_component(component)
        elif is_last:
            return self._process_last_component(component)
        else:
            return self._process_middle_component(component)

    def _process_telnet_response_lines(self) -> None:
        """Process incoming telnet data - route to tickets and store for history."""
        telnet_response_components = self.extract_lines(self.telnet_response)
        total_components = len(telnet_response_components)

        for index, component in enumerate(telnet_response_components, start=1):
            valid_line = self._process_line_component(
                component,
                index,
                total_components
            )

            if valid_line is not None:
                # Store for webinterface history only
                self.telnet_lines_to_process.append(valid_line)
                self._store_valid_line(valid_line)

    def _handle_connection_error(self, error) -> None:
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
            self.telnet_response = ""
            if self.last_connection_loss is None:
                print("telnet_server_unreachable will retry every 10 seconds")

            self.last_connection_loss = time()

    def on_run_loop_iteration(self, loop_log, profile_start):
        """
        Telnet-specific work done on each loop iteration before periodic actions.
        Reads from telnet connection, processes responses, executes command queue.
        """
        can_attempt_connection = (
                self.last_connection_loss is None or
                profile_start > self.last_connection_loss + TELNET_TIMEOUT_RECONNECT
        )

        if can_attempt_connection:
            try:
                self.telnet_response = self.tn.read_very_eager().decode("utf-8")
                if len(self.telnet_response) > 0:
                    self.logger.log_telnet_raw(self.telnet_response, direction="incoming")

            except (AttributeError, EOFError, ConnectionAbortedError, ConnectionResetError) as error:
                self._handle_connection_error(error)
            except Exception as error:
                pass

        if len(self.telnet_response) > 0:
            # FIRST: Route raw data to tickets (ungefiltert!)
            self._route_raw_to_tickets(self.telnet_response)

            # THEN: Parse valid lines for webinterface logging
            self._process_telnet_response_lines()

        # Check for expired tickets
        self._check_expired_tickets(profile_start)

        if self.dom.data.get(self.get_module_identifier()).get("server_is_online") is True:
            self.execute_telnet_command_queue(self.max_command_queue_execution)

        return loop_log

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Telnet().get_module_identifier()] = Telnet()
