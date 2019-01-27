import re
from modules.module import Module
from modules import loaded_modules_dict
from time import time, sleep
from collections import deque
import telnetlib
from itertools import islice


class Telnet(Module):
    tn = object

    telnet_buffer = str
    valid_telnet_lines = deque

    telnet_command_queue = deque

    def __init__(self):
        self.telnet_command_queue = deque()
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "host": "127.0.0.1",
            "port": 8081,
            "password": "thisissecret",
            "max_queue_length": 100,
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

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_telnet"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)
        self.update_gameserver_status_widget_frontend()
        self.update_bunch_of_telnet_log_lines()

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)
        self.update_gameserver_status_widget_frontend()
        self.update_bunch_of_telnet_log_lines()

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.valid_telnet_lines = deque(maxlen=self.default_options["max_queue_length"])
        self.telnet_buffer = ""

        self.run_observer_interval = 0.5
        self.last_execution_time = 0.0
    # endregion

    # region Handling telnet initialization and authentication
    def setup_telnet(self):
        try:
            connection = telnetlib.Telnet(self.options.get("host"), self.options.get("port"), timeout=3)
            self.tn = self.authenticate(connection, self.options.get("password"))
        except Exception as error:
            print('trying to establish telnet connection failed: {}'.format(error))
            raise IOError

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
        start_the_slice = len(self.valid_telnet_lines) - this_many_lines
        if this_many_lines > len(self.valid_telnet_lines):
            return list(reversed(self.valid_telnet_lines))
        if start_the_slice >= 1:
            return list(reversed(list(islice(self.valid_telnet_lines, start_the_slice, len(self.valid_telnet_lines)))))
        else:
            return []
    # endregion

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
            print("processed command '{}'".format(telnet_command))
            command = "{command}{line_end}".format(command=telnet_command, line_end="\r\n")

            try:
                self.tn.write(command.encode('ascii'))
            except Exception as error:
                print("error in telnet write: {}".format(error))

    def update_gameserver_status_widget_frontend(self):
        template_frontend = self.templates.get_template('gameserver_status_widget_frontend.html')
        data_to_emit = template_frontend.render(
            server_is_online=self.dom.data.get("module_telnet").get("server_is_online"),
            shutdown_in_seconds=self.dom.data.get(self.get_module_identifier()).get("shutdown_in_seconds", None)
        )

        self.webserver.send_data_to_client(
            event_data=data_to_emit,
            data_type="widget_content",
            clients=self.webserver.connected_clients.keys(),
            target_element={
                "id": "gameserver_status_widget",
                "type": "div"
            }
        )

    def update_bunch_of_telnet_log_lines(self):
        template_bunch_of_lines = self.templates.get_template('bunch_of_telnet_log_lines.html')
        if len(self.webserver.connected_clients) >= 1:
            data_to_emit = template_bunch_of_lines.render(
                bunch_of_lines=self.get_a_bunch_of_lines(25)
            )
            self.webserver.send_data_to_client(
                method="update",
                data_type="widget_content",
                event_data=data_to_emit,
                clients=self.webserver.connected_clients.keys(),
                target_element={
                    "id": "bunch_of_telnet_log_lines_widget",
                    "type": "ul"
                }
            )

    def run(self):
        next_cycle = 0

        telnet_response = ""
        last_connection_loss = None
        recent_telnet_response = None

        while not self.stopped.wait(next_cycle):
            profile_start = time()

            if last_connection_loss is None or profile_start > last_connection_loss + 10:
                # only execute if server has connection,
                # or if n seconds have passed after last loss,
                # to prevent connect hammering
                try:
                    telnet_response = self.tn.read_very_eager().decode("utf-8")
                except (AttributeError, EOFError, ConnectionAbortedError) as error:
                    self.dom.upsert({
                        self.get_module_identifier(): {
                            "server_is_online": False
                        }
                    })
                    self.telnet_buffer = ""

                    try:
                        self.setup_telnet()
                        self.dom.upsert({
                            self.get_module_identifier(): {
                                "server_is_online": True
                            }
                        })

                    except (OSError, Exception) as error:
                        last_connection_loss = time()
                        print("Telnet: can't reach the server, possibly a restart. Trying again in 10 seconds!")
                        print("Telnet: check if the server is running, it's connectivity and options!")

                    self.update_gameserver_status_widget_frontend()
                    telnet_response = ""

            if len(telnet_response) > 0:
                self.telnet_buffer += telnet_response.lstrip()
                self.telnet_buffer = self.telnet_buffer[-4096:]

                # module_dom needs to be in the required modules list!!
                # let's expose the telnet_buffer to the general module population via our DOM!
                self.dom.upsert({
                    self.get_module_identifier(): {
                        "telnet_lines": self.valid_telnet_lines,
                        "telnet_buffer": self.telnet_buffer
                    }
                })

                """ telnet returned data. let's get some information about it"""
                response_count = 1
                telnet_response_components = self.get_lines(telnet_response)
                for component in telnet_response_components:
                    valid_telnet_line = None
                    if self.is_a_valid_line(component):  # added complete line
                        valid_telnet_line = component.rstrip("\r\n")
                        self.valid_telnet_lines.append(valid_telnet_line)
                        print(valid_telnet_line)
                    else:
                        if response_count == 1:  # not a complete line, might be the remainder of last run
                            if recent_telnet_response is not None:
                                combined_line = "{}{}".format(recent_telnet_response, component)
                                if self.is_a_valid_line(combined_line):  # "added complete combined line"
                                    valid_telnet_line = combined_line.rstrip("\r\n")
                                    self.valid_telnet_lines.append(valid_telnet_line)
                                    print(valid_telnet_line)
                                else:  # "combined line, it doesnt make sense though"
                                    pass

                                recent_telnet_response = None
                            else:
                                if len(telnet_response_components) == 1:
                                    if self.has_valid_start(component):  # "found incomplete line, storing for next run"
                                        recent_telnet_response = component
                                    else:  # "what happened?"
                                        pass

                        elif response_count == len(telnet_response_components):
                            if self.has_valid_start(component):  # not a complete line, might be the start of next run
                                recent_telnet_response = component
                            else:  # "does not seem to be usable"
                                pass

                        else:  # "found incomplete line smack in the middle"
                            pass

                    if valid_telnet_line is not None and len(self.webserver.connected_clients) >= 1:
                        template_bunch_of_lines = self.templates.get_template('bunch_of_telnet_log_lines.html')
                        data_to_emit = template_bunch_of_lines.render(
                            bunch_of_lines=[valid_telnet_line]
                        )
                        self.webserver.send_data_to_client(
                            method="prepend",
                            data_type="widget_content",
                            event_data=data_to_emit,
                            clients=self.webserver.connected_clients.keys(),
                            target_element={
                                "id": "bunch_of_telnet_log_lines_widget",
                                "type": "ul"
                            }
                        )

                    response_count += 1

            self.execute_telnet_command_queue()

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Telnet().get_module_identifier()] = Telnet()
