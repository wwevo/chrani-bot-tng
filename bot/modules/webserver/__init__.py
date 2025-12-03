import os

from bot import loaded_modules_dict
from bot.constants import WEBSOCKET_PING_TIMEOUT, WEBSOCKET_PING_INTERVAL

from bot.module import Module
from bot.mixins.authentication import Authentication
from bot.mixins.socketio_handlers import SocketIOHandlers
from bot.mixins.gameserver_proxy import GameServerProxy
from .user import User

import re
from socket import socket, AF_INET, SOCK_DGRAM
from flask import Flask
from markupsafe import Markup
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from collections.abc import KeysView
from threading import Thread
import string
import random


class Webserver(Module, Authentication, SocketIOHandlers, GameServerProxy):
    app = object
    websocket = object
    login_manager = object

    connected_clients = dict
    broadcast_queue = dict
    send_data_to_client_hook = object

    def __init__(self):
        setattr(self, "default_options", {
            "title": "chrani-bot tng",
            "module_name": self.get_module_identifier()[7:],
            "host": "0.0.0.0",
            "port": 5000,
            "Flask_secret_key": "thisissecret",
            "SocketIO_asynch_mode": "threading",
            "SocketIO_use_reloader": False,
            "SocketIO_debug": False,
            "engineio_logger": False,
            "run_observer_interval": 3,

        })
        setattr(self, "required_modules", [
            'module_dom'
        ])
        self.next_cycle = 0
        self.send_data_to_client_hook = self.send_data_to_client
        self.run_observer_interval = 5
        Authentication.__init__(self)
        SocketIOHandlers.__init__(self)
        GameServerProxy.__init__(self)
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_webserver"

    def setup(self, options=None):
        Module.setup(self, options or {})
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        if self.options.get("host") == self.default_options.get("host"):
            self.options["host"] = self.get_ip()

        self.connected_clients = {}

        app = Flask(__name__)
        app.config["SECRET_KEY"] = self.options.get("Flask_secret_key", self.default_options.get("Flask_secret_key"))

        login_manager = LoginManager()
        login_manager.init_app(app)

        self.app = app
        self.websocket = SocketIO(
            app,
            async_mode=self.options.get("SocketIO_asynch_mode", self.default_options.get("SocketIO_asynch_mode")),
            debug=self.options.get("SocketIO_debug", self.default_options.get("SocketIO_debug")),
            engineio_logger=self.options.get("engineio_logger", self.default_options.get("engineio_logger")),
            use_reloader=self.options.get("SocketIO_use_reloader", self.default_options.get("SocketIO_use_reloader")),
            passthrough_errors=True,
            ping_timeout=WEBSOCKET_PING_TIMEOUT,
            ping_interval=WEBSOCKET_PING_INTERVAL
        )
        self.login_manager = login_manager

        # Login to game server for map tile access (once at setup)
        self.login_to_game_server()

        # Register all routes and handlers BEFORE start() is called
        self._register_routes()
        self._register_socketio_handlers()

    _random = random.SystemRandom()

    @classmethod
    def random_string(cls, length):
        """Generate a random string of given length using uppercase letters and digits."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(cls._random.choice(chars) for _ in range(length))
    def get_ip(self):
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            host = s.getsockname()[0]
            print("ip_discovered: {}".format(host))
        except Exception as error:
            host = self.default_options.get("host")
            print("ip_discovery_failed")
        finally:
            s.close()
        return host

    def _register_routes(self):
        """Register all Flask routes - called once during setup()"""
        template_header = self.templates.get_template('boilerplate/header.html')
        template_frontend = self.templates.get_template('boilerplate/index.html')
        template_footer = self.templates.get_template('boilerplate/footer.html')

        # Register authentication routes from mixin
        self._register_auth_routes()

        # Register game server proxy routes from mixin
        self._register_proxy_routes()

        @self.app.route('/')
        def protected():
            header_markup = self.template_render_hook(
                self,
                template=template_header,
                current_user=current_user,
                title=self.options.get("title", self.default_options.get("title"))
            )
            footer_markup = self.template_render_hook(
                self,
                template=template_footer
            )

            instance_token = self.random_string(20)
            template_options = {
                'current_user': current_user,
                'header': header_markup,
                'footer': footer_markup,
                'instance_token': instance_token
            }

            if not current_user.is_authenticated:
                main_output = (
                    '<div id="unauthorized_disclaimer" class="single_screen">'
                    '<p>Welcome to the <strong>chrani-bot: The Next Generation</strong></p>'
                    '<p>You can <a href="/login">use your steam-account to log in</a>!</p>'
                    '</div>'
                )
                main_markup = Markup(main_output)
                template_options['main'] = main_markup

            return self.template_render_hook(
                self,
                template=template_frontend,
                **template_options
            )

    def on_start(self):
        """Start Flask-SocketIO server before periodic actions loop begins"""
        running_under_wsgi = os.environ.get('RUNNING_UNDER_WSGI', 'false').lower() == 'true'

        if not running_under_wsgi:
            self._server_thread = Thread(
                target=self.websocket.run,
                args=[self.app],
                kwargs={
                    "host": self.options.get("host", self.default_options.get("host")),
                    "port": self.options.get("port", self.default_options.get("port"))
                }
            )
            self._server_thread.daemon = True
            self._server_thread.start()
            print("{} - server_started on {}:{}".format(
                self.get_module_identifier(),
                self.options.get("host"),
                self.options.get("port")
            ))
        else:
            print("{} - wsgi_mode_detected".format(self.get_module_identifier()))

    def send_data_to_client(self, *args, payload=None, **kwargs):
        data_type = kwargs.get("data_type", "widget_content")
        target_element = kwargs.get("target_element", None)
        clients = kwargs.get("clients", None)

        if all([
            clients is not None,
            not isinstance(clients, KeysView),
            not isinstance(clients, list)
        ]):
            if re.match(r"^(\d{17})$", clients):
                clients = [clients]

        method = kwargs.get("method", "update")
        status = kwargs.get("status", "")

        if clients is None:
            clients = "all"

        with self.app.app_context():
            data_packages_to_send = []
            widget_options = {
                "method": method,
                "status": status,
                "payload": payload,
                "data_type": data_type,
                "target_element": target_element,
            }

            if clients == "all":
                clients = list(self.connected_clients.keys())

            if clients is not None and isinstance(clients, list):
                for steamid in clients:
                    try:
                        user = self.connected_clients[steamid]
                        for socket_id in user.socket_ids:
                            emit_options = {
                                "room": socket_id
                            }
                            data_packages_to_send.append([widget_options, emit_options])
                    except (AttributeError, KeyError) as error:
                        print("socket_send_failed_no_client")

            for data_package in data_packages_to_send:
                try:
                    self.websocket.emit(
                        'data',
                        data_package[0],
                        **data_package[1]
                    )
                except Exception as error:
                    print("socket_emit_failed")

    @staticmethod
    def sanitize_for_html_id(value):
        return str(value).replace(" ", "_").lower()

    def occurrences_of_key_in_nested_mapping(self, key, value):
        for k, v in value.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.occurrences_of_key_in_nested_mapping(key, v):
                    yield result

    def get_dict_element_by_path(self, d, l):
        if len(l) == 1:
            return d.get(l[0], [])
        return self.get_dict_element_by_path(d.get(l[0], {}), l[1:])

    def get_navigation_for_widget(self, target_module, widget_meta):
        widget = self.templates.get_template('boilerplate/widget_link.html')
        navigation = ""
        for view_id, view in widget_meta.get("views").items():
            navigation += self.template_render_hook(
                self,
                template=widget,
                active=True,
                text=view_id,
                event={
                    "id": widget_meta.get("id"),
                    "type": "browser_widget_action",
                    "action_module": self.get_module_identifier(),
                    "action": "set_widget_view",
                    "widget_module": target_module.get_module_identifier(),
                    "widget_view": view_id
                }
            )

        return navigation

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Webserver().get_module_identifier()] = Webserver()
