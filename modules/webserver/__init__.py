""" some IDE's will throw 'PEP 8' warnings for imports, but this has to happen early, I think """
from gevent import monkey
monkey.patch_all()

from os import path, chdir
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)

""" standard imports """
from modules.module import Module
from modules import loaded_modules_dict
from .user import User

import re
import functools
from socket import socket, AF_INET, SOCK_DGRAM
from flask import Flask, request, redirect, render_template, Markup
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit, disconnect, send
from requests import post
from urllib.parse import urlencode
from collections import KeysView


class Webserver(Module):
    app = object
    websocket = object

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

        return self

    def start(self):
        Module.start(self)
        return self
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

    def send_data_to_client(self, data={}, target_element=None, clients=None, method="update"):
        with self.app.app_context():
            data_ready_for_emitting = False
            if clients is None:
                emit_options = {
                    "broadcast": True,
                    "namespace": '/chrani-bot-ng'
                }
                self.websocket.emit(
                    'widget',
                    {
                        "method": method,
                        "data": data,
                        "target_element": target_element,
                    },
                    **emit_options
                )
            elif isinstance(clients, KeysView):
                for steamid in clients:
                    try:
                        emit_options = {
                            "room": self.connected_clients[steamid].sid,
                            "namespace": '/chrani-bot-ng'
                        }
                        self.websocket.emit(
                            'widget',
                            {
                                "method": method,
                                "data": data,
                                "target_element": target_element,
                            },
                            **emit_options
                        )
                    except AttributeError as error:
                        # user has got no session id yet
                        pass

    def run(self):
        app = Flask(
            __name__,
            template_folder=path.join(root_dir, 'templates'),
            static_folder=path.join(root_dir, 'static')
        )
        app.config["SECRET_KEY"] = self.options.get("Flask_secret_key", self.default_options.get("Flask_secret_key"))

        login_manager = LoginManager()
        login_manager.init_app(app)

        socketio = SocketIO(
            app,
            async_mode=self.options.get("SocketIO_asynch_mode", self.default_options.get("SocketIO_asynch_mode"))
        )

        self.app = app
        self.websocket = socketio

        # region Management function and routes without any user-display or interaction
        def authenticated_only(f):
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                if not current_user.is_authenticated:
                    disconnect()
                else:
                    return f(*args, **kwargs)

            return wrapped

        @login_manager.user_loader
        def user_loader(steamid):
            user = self.connected_clients.get(steamid, False)
            if not user:
                """ This is where the authentication will happen, see if that user in in your allowed players database or
                 whatever """
                user = User(steamid)
                self.connected_clients[steamid] = user

            return user

        @app.route('/login')
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

        @app.route('/authenticate', methods=['GET'])
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
                    user = User(steamid)
                    login_user(user, remember=True)
                    print("user {} connected...".format(user.id))
                    return redirect("/protected")

            return redirect("/")

        @app.route('/logout')
        @login_required
        def logout():
            del self.connected_clients[current_user.id]
            logout_user()
            return redirect("/")
        # endregion

        # region Actual routes the user gets to see and use
        """ actual pages """
        @app.route('/unauthorized')
        @login_manager.unauthorized_handler
        def unauthorized_handler():
            output = '<div>'
            output += '<p>You are not allowed to view that page :(</p>'
            output += '<p><a href="/">home</a></p>'
            output += "</div>"
            markup = Markup(output)
            return render_template('index.html', content=markup), 401

        @app.errorhandler(404)
        def page_not_found(error):
            output = '<div>'
            output += '<p>{}</p>'.format(error)
            output += '<p><a href="/">home</a></p>'
            output += "</div>"
            markup = Markup(output)
            return render_template('index.html', content=markup), 404

        @app.route('/')
        def index():
            if current_user.is_authenticated is True:
                return redirect("/protected")

            output = '<div>'
            output += '<p>Welcome to the <strong>chrani-bot: the next generation</strong></p>'
            output += '<p>' \
                      'please <a href="/login">log in with your steam account</a> ' \
                      'to get access to the protected stuff' \
                      '</p>'
            output += '</div>'

            markup = Markup(output)
            return render_template('index.html', content=markup)

        @app.route('/protected')
        @login_required
        def protected():
            output = '<div>'
            output += '<p>Welcome to the <strong>chrani-bot: the next generation</strong> (protected)</p>'
            output += '<p>' \
                      'enjoy the telnet-log<br />' \
                      'if you enjoy the logging, you might just as well <a href="/logout">log out</a> again.' \
                      '</p>'
            output += '</div>'

            markup = Markup(output)
            return render_template('index.html', content=markup)
        # endregion

        # region Websocket handling
        @socketio.on('connect', namespace='/chrani-bot-ng')
        @authenticated_only
        def connect_handler():
            if hasattr(request, 'sid'):
                self.connected_clients[current_user.id].sid = request.sid
                emit(
                    'connected',
                    room=request.sid,
                    broadcast=False
                )
            else:
                return False  # not allowed here

        @socketio.on('ding', namespace='/chrani-bot-ng')
        @authenticated_only
        def ding_dong():
            print("got 'ding' from {}".format(current_user.id))
            emit(
                'dong',
                room=current_user.sid
            )
            print("sent 'dong' to {}".format(current_user.id))
        # endregion

        socketio.run(
            app,
            host=self.options.get("host", self.default_options.get("host")),
            port=self.options.get("port", self.default_options.get("port")),
            debug=self.options.get("SocketIO_debug", self.default_options.get("SocketIO_debug")),
            use_reloader=self.options.get("SocketIO_use_reloader", self.default_options.get("SocketIO_use_reloader"))
        )


loaded_modules_dict[Webserver().get_module_identifier()] = Webserver()
