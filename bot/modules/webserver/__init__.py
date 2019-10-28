import functools
from bot import started_modules_dict
from flask_socketio import disconnect

from bot.module import Module
from bot import loaded_modules_dict
from .user import User

import re
from time import time
from socket import socket, AF_INET, SOCK_DGRAM
from flask import Flask, request, redirect, Markup
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit
from requests import post
from urllib.parse import urlencode
from collections.abc import KeysView
from threading import Thread


class Webserver(Module):
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
            "SocketIO_asynch_mode": None,
            "SocketIO_use_reloader": False,
            "SocketIO_debug": True,
            "engineio_logger": True
        })
        setattr(self, "required_modules", [
            'module_dom'
        ])
        self.next_cycle = 0
        self.send_data_to_client_hook = self.send_data_to_client
        self.run_observer_interval = 5
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_webserver"

    # region SocketIO stuff
    @staticmethod
    def dispatch_socket_event(target_module, event_data, dispatchers_steamid):
        module_identifier = "module_{}".format(target_module)
        # print("user '{}' tries sending {} to module {}...".format(dispatchers_steamid, event_data, module_identifier))
        try:
            started_modules_dict[module_identifier].on_socket_event(event_data, dispatchers_steamid)
        except KeyError as error:
            print("users '{}' attempt to send data to module {} failed: module not found!".format(
                dispatchers_steamid, module_identifier
            ))

    @staticmethod
    def authenticated_only(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                disconnect()
            else:
                return f(*args, **kwargs)

        return wrapped
    # endregion

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

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
            ping_timeout=15,
            ping_interval=5
        )
        self.login_manager = login_manager
    # endregion

    def get_ip(self):
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            host = s.getsockname()[0]
            print("{}: discovered IP: {}".format(self.options.get("module_name"), host))
        except Exception as error:
            host = self.default_options.get("host")
            print(type(error))
            print("{}: could not find IP, using {} instead!".format(self.options.get("module_name"), host))
        finally:
            s.close()
        return host

    def send_data_to_client(self, *args, **kwargs):
        event_data = kwargs.get("event_data", None)
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
                "event_data": event_data,
                "data_type": data_type,
                "target_element": target_element,
            }
            if clients is "all":
                emit_options = {
                    "broadcast": True
                }
                data_packages_to_send.append([widget_options, emit_options])
            elif clients is not None:
                for steamid in clients:
                    try:
                        emit_options = {
                            "room": self.connected_clients[steamid].sid
                        }
                        data_packages_to_send.append([widget_options, emit_options])
                    except AttributeError as error:
                        # print("user has got no session id yet")
                        pass
                    except KeyError as error:
                        # print("user seems to have disappeared")
                        pass

            for data_package in data_packages_to_send:
                self.websocket.emit(
                    'data',
                    data_package[0],
                    **data_package[1]
                )

    def emit_event_status(self, module, event_data, recipient_steamid, status=None):
        clients = recipient_steamid

        self.send_data_to_client_hook(
            module,
            event_data=event_data,
            data_type="status_message",
            clients=clients,
            status=status
        )

    def run(self):
        template_header = self.templates.get_template('header.html')
        template_frontend = self.templates.get_template('index.html')
        template_footer = self.templates.get_template('footer.html')

        # region Management function and routes without any user-display or interaction
        @self.login_manager.user_loader
        def user_loader(steamid):
            webserver_user = self.connected_clients.get(steamid, False)
            if not webserver_user:
                """ This is where the authentication will happen, see if that user in in your allowed players database or
                 whatever """
                webserver_user = User(steamid, time())
                self.connected_clients[steamid] = webserver_user

            return webserver_user

        @self.app.route('/login')
        def login():
            steam_openid_url = 'https://steamcommunity.com/openid/login'
            u = {
                'openid.ns': "http://specs.openid.net/auth/2.0",
                'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
                'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
                'openid.mode': 'checkid_setup',
                'openid.return_to': "http://{host}:{port}/authenticate".format(
                    host=self.options.get("host", self.default_options.get("host")),
                    port=self.options.get("port", self.default_options.get("port"))
                ),
                'openid.realm': "http://{host}:{port}".format(
                    host=self.options.get("host", self.default_options.get("host")),
                    port=self.options.get("port", self.default_options.get("port"))
                )
            }
            query_string = urlencode(u)
            auth_url = "{url}?{query_string}".format(
                url=steam_openid_url,
                query_string=query_string
            )
            return redirect(auth_url)

        @self.app.route('/authenticate', methods=['GET'])
        def setup():
            def validate(signed_params):
                steam_login_url_base = "https://steamcommunity.com/openid/login"
                params = {
                    "openid.assoc_handle": signed_params["openid.assoc_handle"],
                    "openid.sig": signed_params["openid.sig"],
                    "openid.ns": signed_params["openid.ns"],
                    "openid.mode": "check_authentication"
                }

                params_dict = signed_params.to_dict()
                params_dict.update(params)

                params_dict["openid.mode"] = "check_authentication"
                params_dict["openid.signed"] = params_dict["openid.signed"]

                try:
                    response = post(steam_login_url_base, data=params_dict)
                    valid_response = True if "is_valid:true" in response.text else False
                except TypeError as error:
                    valid_response = False

                return valid_response

            if validate(request.args):
                p = re.search(r"/(?P<steamid>([0-9]{17}))", str(request.args["openid.claimed_id"]))
                if p:
                    steamid = p.group("steamid")
                    webserver_user = User(steamid)
                    login_user(webserver_user, remember=True)
                    # print("user {} connected...".format(webserver_user.id))

            return redirect("/")

        @self.app.route('/logout')
        @login_required
        def logout():
            del self.connected_clients[current_user.id]
            for module in loaded_modules_dict.values():
                module.on_socket_disconnect(current_user.id)
            logout_user()
            return redirect("/")
        # endregion

        # region Actual routes the user gets to see and use
        """ actual pages """
        @self.app.route('/unauthorized')
        @self.login_manager.unauthorized_handler
        def unauthorized_handler():
            return redirect("/")

        @self.app.route('/')
        def protected():
            header_markup = self.template_render_hook(
                self,
                template_header,
                current_user=current_user,
                title=self.options.get("title", self.default_options.get("title"))
            )
            footer_markup = self.template_render_hook(
                self,
                template_footer
            )
            template_options = {
                'current_user': current_user,
                'header': header_markup,
                'footer': footer_markup
            }
            if not current_user.is_authenticated:
                main_output = '<p>Welcome to the <strong>chrani-bot: the next generation</strong></p>'
                main_output += '<p>You can use your steam-account to log in!</p>'
                main_markup = Markup(main_output)
                template_options['main'] = main_markup

            return self.template_render_hook(
                self,
                template_frontend,
                **template_options
            )
        # endregion

        # region Websocket handling
        @self.websocket.on('connect')
        @self.authenticated_only
        def connect_handler():
            if not hasattr(request, 'sid'):
                return False  # not allowed here
            else:
                print("webinterface-client '{}' connected and is ready to roll!".format(current_user.id))
                self.connected_clients[current_user.id].sid = request.sid
                emit('connected', room=request.sid, broadcast=False)
                for module in loaded_modules_dict.values():
                    module.on_socket_connect(current_user.id)

        @self.websocket.on('disconnect')
        def disconnect_handler():
            print("client {} disconnected".format(current_user.id))

        @self.websocket.on('ding')
        def ding_dong():
            current_user.last_seen = time()
            try:
                emit('dong', room=current_user.sid)
                self.connected_clients[current_user.id].sid = request.sid

            except AttributeError as error:
                # user disappeared
                print("client {} (SID:{}) disappeared".format(current_user.id, current_user.sid))

        @self.websocket.on('widget_event')
        @self.authenticated_only
        def widget_event(data):
            self.dispatch_socket_event(data[0], data[1], current_user.id)
        # endregion

        Thread(
            target=self.websocket.run,
            args=[self.app],
            kwargs={
                "host": self.options.get("host", self.default_options.get("host")),
                "port": self.options.get("port", self.default_options.get("port"))
            }
        ).start()

        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.trigger_action_hook(self, ["logged_in_users", {}])

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Webserver().get_module_identifier()] = Webserver()
