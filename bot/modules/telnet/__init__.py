import re
from bot.module import Module
from bot import loaded_modules_dict
from time import time
from collections import deque
import telnetlib


class Telnet(Module):
    tn = object

    data_transfer_enabled = bool

    telnet_buffer = str
    valid_telnet_lines = deque

    telnet_lines_to_process = deque
    telnet_command_queue = deque

    def __init__(self):
        self.telnet_command_queue = deque()
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "host": "127.0.0.1",
            "port": 8081,
            "password": "thisissecret",
            "max_queue_length": 100,
            "run_observer_interval": 3,
            "run_observer_interval_idle": 10,
            "data_transfer_enabled": True,
            "match_types_generic": {
                'log_start': [
                    r"\A(?P<datetime>\d{4}.+?)\s(?P<gametime_in_seconds>.+?)\sINF .*",
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
        self.data_transfer_enabled = self.options.get(
            "data_transfer_enabled", self.default_options.get("data_transfer_enabled", False)
        )
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.run_observer_interval_idle = self.options.get(
            "run_observer_interval_idle", self.default_options.get("run_observer_interval_idle", None)
        )

        self.telnet_buffer = ""

        self.last_execution_time = 0.0

        setattr(self, "last_connection_loss", None)
        setattr(self, "recent_telnet_response", None)
    # endregion

    # region Handling telnet initialization and authentication
    def setup_telnet(self):
        try:
            connection = telnetlib.Telnet(self.options.get("host"), self.options.get("port"), timeout=3)
            self.tn = self.authenticate(connection, self.options.get("password"))
        except Exception as error:
            print('trying to establish telnet connection failed: {}'.format(error))
            raise IOError

        return True

    def authenticate(self, connection, password):
        try:
            # Waiting for the prompt.
            found_prompt = False
            while found_prompt is not True:
                telnet_response = connection.read_until(b"\r\n", timeout=3).decode("utf-8")
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
                    log_message = 'incorrect telnet password'
                    print(log_message)
                    raise ValueError
                if re.match(r"Logon successful.\r\n", telnet_response) is not None:
                    authenticated = True

            # Waiting for banner.
            full_banner = ''
            displayed_welcome = False
            while displayed_welcome is not True:  # loop until ready, it's required
                telnet_response = connection.read_until(b"\r\n").decode("utf-8")
                full_banner += telnet_response.rstrip("\r\n")
                if re.match(r"Press 'help' to get a list of all commands. Press 'exit' to end session.", telnet_response):
                    displayed_welcome = True

        except Exception as e:
            raise IOError

        print("telnet connection established on {}:{} ".format(self.options.get("host"), self.options.get("port")))
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

    def get_lines(self, telnet_response):
        telnet_lines_list = [telnet_line for telnet_line in telnet_response.splitlines(True)]
        return telnet_lines_list

    def get_a_bunch_of_lines(self, this_many_lines):
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

    def add_telnet_command_to_queue(self, command):
        self.telnet_command_queue.appendleft(command)

    def execute_telnet_command_queue(self):
        telnet_command_list = []
        done = False
        while not done:
            try:
                telnet_command_list.append(self.telnet_command_queue.popleft())
            except IndexError:
                done = True

        for telnet_command in telnet_command_list:
            command = "{command}{line_end}".format(command=telnet_command, line_end="\r\n")

            try:
                if self.data_transfer_enabled:
                    self.tn.write(command.encode('ascii'))
                else:
                    raise ConnectionRefusedError("telnet data transfer has been disabled")

            except Exception as error:
                print("couldn't process command '{command}' due to: '{error}'".format(
                    command=telnet_command,
                    error=error
                ))
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            if self.last_connection_loss is None or profile_start > self.last_connection_loss + 10:
                # only execute if server has connection,
                # or if n seconds have passed after last loss,
                # to prevent connect hammering
                try:
                    self.telnet_response = self.tn.read_very_eager().decode("utf-8")
                except (AttributeError, EOFError, ConnectionAbortedError, ConnectionResetError) as main_error:
                    try:
                        self.setup_telnet()
                        self.dom.data.upsert({
                            self.get_module_identifier(): {
                                "server_is_online": True,
                                "data_transfer_enabled": self.data_transfer_enabled
                            }
                        })

                    except (OSError, Exception, ConnectionRefusedError) as sub_error:
                        self.dom.data.upsert({
                            self.get_module_identifier(): {
                                "server_is_online": False,
                                "data_transfer_enabled": self.data_transfer_enabled
                            }
                        })
                        self.telnet_buffer = ""
                        self.telnet_response = ""
                        self.last_connection_loss = time()
                        print("Telnet: can't reach the server, possibly a restart. Trying again in 10 seconds!")
                        print("Telnet: check if the server is running, it's connectivity and options!")
                except Exception as main_error:
                    print("########### Unforeseen Error: {}".format(type(main_error)))

            if len(self.telnet_response) > 0:
                self.telnet_buffer += self.telnet_response.lstrip()
                self.telnet_buffer = self.telnet_buffer[-8144:]

                # module_dom needs to be in the required modules list!!
                # let's expose the telnet_buffer to the general module population via our DOM!
                self.dom.data.upsert({
                    self.get_module_identifier(): {
                        "telnet_buffer": self.telnet_buffer
                    }
                })

                """ telnet returned data. let's get some information about it"""
                response_count = 1
                telnet_response_components = self.get_lines(self.telnet_response)
                for component in telnet_response_components:
                    valid_telnet_line = None
                    if self.is_a_valid_line(component):  # added complete line
                        valid_telnet_line = component.rstrip("\r\n")
                        self.telnet_lines_to_process.append(valid_telnet_line)
                        # print(valid_telnet_line)
                    else:
                        if response_count == 1:  # not a complete line, might be the remainder of last run
                            if self.recent_telnet_response is not None:
                                combined_line = "{}{}".format(self.recent_telnet_response, component)
                                if self.is_a_valid_line(combined_line):  # "added complete combined line"
                                    valid_telnet_line = combined_line.rstrip("\r\n")
                                    self.telnet_lines_to_process.append(valid_telnet_line)
                                    # print(valid_telnet_line)
                                else:  # "combined line, it doesnt make sense though"
                                    print("WRN {}".format(combined_line.rstrip("\r\n")))

                                self.recent_telnet_response = None
                            else:
                                if len(telnet_response_components) == 1:
                                    if self.has_valid_start(component):  # "found incomplete line, storing for next run"
                                        self.recent_telnet_response = component
                                    else:  # "what happened?"
                                        if len(component.rstrip("\r\n")) != 0:
                                            print("WRN {}".format(component.rstrip("\r\n")))

                        elif response_count == len(telnet_response_components):
                            if self.has_valid_start(component):  # not a complete line, might be the start of next run
                                self.recent_telnet_response = component
                            else:  # part of a telnet-command response
                                # print(component.rstrip("\r\n"))
                                pass

                        else:  # "found incomplete line smack in the middle"
                            # print(component.rstrip("\r\n"))
                            pass

                    if valid_telnet_line is not None:
                        if not any(exclude_element in valid_telnet_line for exclude_element in ["'lp'", "'gettime'"]):
                            print(valid_telnet_line)

                        self.valid_telnet_lines.append(valid_telnet_line)

                        if len(self.webserver.connected_clients) >= 1:
                            self.dom.data.append({
                                self.get_module_identifier(): {
                                    "telnet_lines": valid_telnet_line
                                }
                            }, maxlen=150)

                    response_count += 1

            if self.dom.data.get(self.get_module_identifier()).get("server_is_online") is True:
                self.execute_telnet_command_queue()

            self.last_execution_time = time() - profile_start
            if self.data_transfer_enabled:
                interval = self.run_observer_interval
            else:
                interval = self.run_observer_interval_idle

            self.next_cycle = interval - self.last_execution_time


loaded_modules_dict[Telnet().get_module_identifier()] = Telnet()
