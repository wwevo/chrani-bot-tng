import re
from modules import loaded_modules_dict, started_modules_dict
from time import time, sleep
from threading import Thread, Event
from collections import deque
import telnetlib


class Telnet(Thread):
    options = dict
    name = str

    tn = object
    stopped = object

    dom = object
    webserver = object

    run_observer_interval = int  # loop this every run_observers_interval seconds
    last_execution_time = float

    recent_telnet_response = str
    recent_telnet_response_has_valid_start = bool
    recent_telnet_response_has_valid_end = bool

    telnet_buffer = str
    valid_telnet_lines = deque

    def __init__(self):
        self.default_options = {
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
        }

        self.required_modules = [
            "module_dom",
            "module_webserver"
        ]

        self.stopped = Event()
        Thread.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_telnet"

    def setup(self, options=dict):
        self.name = 'telnet'
        self.options = self.default_options
        if isinstance(options, dict):
            print("Telnet: provided options have been set".format(self.name.upper()))
            self.options.update(options)
        else:
            print("Telnet: no options provided, default values are used".format(self.name.upper()))

        self.recent_telnet_response = None
        self.recent_telnet_response_has_valid_start = False
        self.recent_telnet_response_has_valid_end = False

        self.valid_telnet_lines = deque(maxlen=self.default_options["max_queue_length"])
        self.telnet_buffer = ""

        self.run_observer_interval = 0.5
        self.last_execution_time = 0.0

        return self

    def start(self):
        self.setDaemon(daemonic=True)
        self.dom = started_modules_dict["module_dom"]
        self.webserver = started_modules_dict["module_webserver"]

        Thread.start(self)
        return self

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
                telnet_lines.append(self.valid_telnet_lines.popleft())
                current_queue_length += 1
            except IndexError:
                done = True

        if len(telnet_lines) >= 1:
            return telnet_lines
        else:
            return False

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            try:
                telnet_response = self.tn.read_very_eager().decode("utf-8")
            except (AttributeError, EOFError) as error:
                if type(error) == EOFError:
                    print("Telnet: the server has gone dark, possibly a restart. Trying again in 10 seconds!")
                    sleep(10)

                try:
                    self.setup_telnet()
                except (OSError, Exception) as error:
                    print("Telnet: can't reach the server, possibly a restart. Trying again in 10 seconds!")
                    print("Telnet: check if the server is running, it's connectivity and options!")
                    sleep(10)

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
                    if self.is_a_valid_line(component):  # added complete line
                        valid_telnet_line = component.rstrip("\r\n")
                        self.valid_telnet_lines.append(valid_telnet_line)
                        print(valid_telnet_line)
                    else:
                        if response_count == 1:  # not a complete line, might be the remainder of last run
                            if self.recent_telnet_response is not None:
                                combined_line = "{}{}".format(self.recent_telnet_response, component)
                                if self.is_a_valid_line(combined_line):  # "added complete combined line"
                                    valid_telnet_line = combined_line.rstrip("\r\n")
                                    self.valid_telnet_lines.append(valid_telnet_line)
                                    print(valid_telnet_line)
                                else:  # "combined line, it doesnt make sense though"
                                    pass

                                self.recent_telnet_response = None
                            else:
                                if len(telnet_response_components) == 1:
                                    if self.has_valid_start(component):  # "found incomplete line, storing for next run"
                                        self.recent_telnet_response = component
                                    else:  # "what happened?"
                                        pass

                        elif response_count == len(telnet_response_components):
                            if self.has_valid_start(component):  # not a complete line, might be the start of next run
                                self.recent_telnet_response = component
                            else:  # "does not seem to be usable"
                                pass

                        else:  # "found incomplete line smack in the middle"
                            pass

                    response_count += 1

            if len(self.webserver.connected_clients) >= 1:
                self.webserver.send_data_to_client("telnet", self.webserver.connected_clients.keys())

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Telnet().get_module_identifier()] = Telnet()
