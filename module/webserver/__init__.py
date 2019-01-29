""" some IDE's will throw 'PEP 8' warnings for imports, but this has to happen early, I think """
from gevent import monkey
monkey.patch_all()

from os import path, chdir
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)

""" standard imports """
from module.common import dispatch_socket_event, authenticated_only
from module.module import Module
from module import loaded_modules_dict
from .user import User

import re
from time import time
from socket import socket, AF_INET, SOCK_DGRAM
from flask import Flask, request, redirect, Markup
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit, disconnect
from requests import post
from urllib.parse import urlencode
from collections import KeysView


class Webserver(Module):
    app = object
    websocket = object
    login_manager = object

    connected_clients = dict
    broadcast_queue = dict

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "host": "127.0.0.1",
            "port": 5000,
            "Flask_secret_key": "thisissecret",
            "SocketIO_asynch_mode": None,
            "SocketIO_use_reloader": False,
            "SocketIO_debug": False
        })
        setattr(self, "required_modules", [])
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_webserver"

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

        socketio = SocketIO(
            app,
            async_mode=self.options.get("SocketIO_asynch_mode", self.default_options.get("SocketIO_asynch_mode"))
        )

        self.app = app
        self.websocket = socketio
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

    def send_data_to_client(self, event_data, data_type="widget_content", target_element=None, clients=None, method="update", status=""):
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
                    "broadcast": True,
                    "namespace": '/chrani-bot-ng'
                }
                data_packages_to_send.append([widget_options, emit_options])
            elif isinstance(clients, KeysView) or isinstance(clients, list):
                for steamid in clients:
                    try:
                        emit_options = {
                            "room": self.connected_clients[steamid].sid,
                            "namespace": '/chrani-bot-ng'
                        }
                        data_packages_to_send.append([widget_options, emit_options])
                    except AttributeError as error:
                        # user has got no session id yet
                        pass

            for data_package in data_packages_to_send:
                self.websocket.emit(
                    'data',
                    data_package[0],
                    **data_package[1]
                )

    def run(self):
        template_frontend = self.templates.get_template('index.html')

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
                    host=self.options.get("host",self.default_options.get("host")),
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
                    print("user {} connected...".format(webserver_user.id))
                    return redirect("/protected")

            return redirect("/")

        @self.app.route('/logout')
        @login_required
        def logout():
            disconnect(sid=current_user.sid, namespace='/chrani-bot-ng')
            del self.connected_clients[current_user.id]
            print("user {} disconnected...".format(current_user.id))
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

        @self.app.errorhandler(404)
        def page_not_found(error):
            header_output  = '<h1>chrani-bot tng</h1> (public area)'
            header_output += '<aside>'
            header_output += '<a href="/login">log in</a>'
            header_output += '</aside>'
            output  = '<p>{}</p>'.format(error)
            output += '<p><a href="/">home</a></p>'

            header_markup = Markup(header_output)
            markup = Markup(output)
            return template_frontend.render(main=markup, header=header_markup), 404

        @self.app.route('/')
        def index():
            if current_user.is_authenticated is True:
                return redirect("/protected")

            header_output  = '<h1>chrani-bot tng</h1> (public area)'
            header_output += '<aside>'
            header_output += '<a href="/login">log in</a>'
            header_output += '</aside>'
            main_output  = '<p>Welcome to the <strong>chrani-bot: the next generation</strong></p>'
            main_output += '<p>You can use your steam-account to log in!</p>'

            header_markup = Markup(header_output)
            main_markup = Markup(main_output)
            return template_frontend.render(main=main_markup, header=header_markup)

        @self.app.route('/protected')
        @login_required
        def protected():
            header_output  = '<h1>chrani-bot tng</h1> (protected area)'
            header_output += '<aside>'
            header_output += '<a href="/logout">log out</a>'
            header_output += '</aside>'

            header_markup = Markup(header_output)
            return template_frontend.render(header=header_markup)
        # endregion

        # region Websocket handling
        @self.websocket.on('connect', namespace='/chrani-bot-ng')
        @authenticated_only
        def connect_handler():
            if hasattr(request, 'sid'):
                self.connected_clients[current_user.id].sid = request.sid
                emit(
                    'connected',
                    room=request.sid,
                    broadcast=False
                )
                for module in loaded_modules_dict.values():
                    module.on_socket_connect(current_user.id)
            else:
                return False  # not allowed here

        @self.websocket.on('ding', namespace='/chrani-bot-ng')
        @authenticated_only
        def ding_dong():
            current_user.last_seen = time()
            print("got 'ding' from {}".format(current_user.id))
            emit(
                'dong',
                room=current_user.sid
            )
            print("sent 'dong' to {}".format(current_user.id))

        @self.websocket.on('widget_event', namespace='/chrani-bot-ng')
        @authenticated_only
        def widget_event(data):
            dispatch_socket_event(data[0], data[1], current_user.id)
        # endregion

        self.websocket.run(
            self.app,
            host=self.options.get("host", self.default_options.get("host")),
            port=self.options.get("port", self.default_options.get("port")),
            debug=self.options.get("SocketIO_debug", self.default_options.get("SocketIO_debug")),
            use_reloader=self.options.get("SocketIO_use_reloader", self.default_options.get("SocketIO_use_reloader"))
        )


loaded_modules_dict[Webserver().get_module_identifier()] = Webserver()
