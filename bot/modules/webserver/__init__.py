import functools
import os
from bot import started_modules_dict
from bot.constants import WEBSOCKET_PING_TIMEOUT, WEBSOCKET_PING_INTERVAL
from flask_socketio import disconnect

from bot.module import Module
from bot import loaded_modules_dict
from bot.logger import get_logger
from .user import User

import re
from time import time
from socket import socket, AF_INET, SOCK_DGRAM
from flask import Flask, request, redirect, session, Response
from markupsafe import Markup
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit
from requests import post, get
from urllib.parse import urlencode
from collections.abc import KeysView
from threading import Thread
import string
import random

# Initialize logger for webserver module
logger = get_logger("webserver")


class Webserver(Module):
    app = object
    websocket = object
    login_manager = object

    connected_clients = dict
    broadcast_queue = dict
    send_data_to_client_hook = object
    game_server_session_id = None

    def __init__(self):
        setattr(self, "default_options", {
            "title": "chrani-bot tng",
            "module_name": self.get_module_identifier()[7:],
            "host": "0.0.0.0",
            "port": 5000,
            "Flask_secret_key": "thisissecret",
            "SocketIO_asynch_mode": "gevent",
            "SocketIO_use_reloader": False,
            "SocketIO_debug": False,
            "engineio_logger": False
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
        try:
            started_modules_dict[module_identifier].on_socket_event(event_data, dispatchers_steamid)
        except KeyError as error:
            logger.error("socket_event_module_not_found",
                        user=dispatchers_steamid,
                        target_module=module_identifier,
                        error=str(error))

    @staticmethod
    def authenticated_only(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                disconnect()
            else:
                return f(*args, **kwargs)

        return wrapped

    # Reusable SystemRandom instance for efficient token generation
    _random = random.SystemRandom()

    @classmethod
    def random_string(cls, length):
        """Generate a random string of given length using uppercase letters and digits."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(cls._random.choice(chars) for _ in range(length))
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
            ping_timeout=WEBSOCKET_PING_TIMEOUT,
            ping_interval=WEBSOCKET_PING_INTERVAL
        )
        self.login_manager = login_manager
    # endregion

    def get_ip(self):
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            host = s.getsockname()[0]
            logger.info("ip_discovered", ip=host)
        except Exception as error:
            host = self.default_options.get("host")
            logger.warn("ip_discovery_failed", fallback_ip=host, error=str(error))
        finally:
            s.close()
        return host

    def login_to_game_server(self):
        """Login to game server web interface and store session cookie"""
        telnet_module = loaded_modules_dict.get("module_telnet")
        if not telnet_module:
            logger.warn("game_server_login_telnet_missing",
                       reason="telnet module not loaded")
            return

        game_host = telnet_module.options.get("host")
        telnet_port = telnet_module.options.get("port", 8081)
        web_port = telnet_port + 1

        web_username = telnet_module.options.get("web_username", "")
        web_password = telnet_module.options.get("web_password", "")

        if not web_username or not web_password:
            logger.warn("game_server_login_no_credentials",
                       host=game_host,
                       port=web_port,
                       impact="map tiles unavailable")
            return

        login_url = f'http://{game_host}:{web_port}/session/login'

        try:
            response = post(
                login_url,
                json={"username": web_username, "password": web_password},
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                sid_cookie = response.cookies.get('sid')
                if sid_cookie:
                    self.game_server_session_id = sid_cookie
                    # Success - no log needed
                else:
                    logger.warn("game_server_login_no_sid_cookie",
                               host=game_host,
                               port=web_port,
                               status=200)
            else:
                logger.error("game_server_login_failed",
                            host=game_host,
                            port=web_port,
                            status=response.status_code,
                            url=login_url)
        except Exception as e:
            logger.error("game_server_login_exception",
                        host=game_host,
                        port=web_port,
                        error=str(e),
                        error_type=type(e).__name__)

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

            # Determine which clients to send to
            if clients == "all":
                # Send to all connected clients individually
                # Note: broadcast=True doesn't work with self.websocket.emit() in gevent mode
                clients = list(self.connected_clients.keys())

            if clients is not None and isinstance(clients, list):
                for steamid in clients:
                    try:
                        # Send to ALL socket connections for this user (multiple browsers)
                        user = self.connected_clients[steamid]
                        for socket_id in user.socket_ids:
                            emit_options = {
                                "room": socket_id
                            }
                            data_packages_to_send.append([widget_options, emit_options])
                    except (AttributeError, KeyError) as error:
                        # User connection state is inconsistent - log and skip this client
                        logger.debug(
                            "socket_send_failed_no_client",
                            steamid=steamid,
                            data_type=data_type,
                            error_type=type(error).__name__,
                            has_client=steamid in self.connected_clients,
                            has_sockets=len(self.connected_clients.get(steamid, type('obj', (), {'socket_ids': []})).socket_ids) > 0
                        )

            for data_package in data_packages_to_send:
                try:
                    self.websocket.emit(
                        'data',
                        data_package[0],
                        **data_package[1]
                    )
                except Exception as error:
                    # Socket emit failed - log the error
                    logger.error(
                        "socket_emit_failed",
                        data_type=data_type,
                        error=str(error),
                        error_type=type(error).__name__
                    )

    def emit_event_status(self, module, event_data, recipient_steamid, status=None):
        clients = recipient_steamid

        self.send_data_to_client_hook(
            module,
            payload=event_data,
            data_type="status_message",
            clients=clients,
            status=status
        )

    def run(self):
        # Login to game server web interface for map tile access
        self.login_to_game_server()

        template_header = self.templates.get_template('frontpage/header.html')
        template_frontend = self.templates.get_template('frontpage/index.html')
        template_footer = self.templates.get_template('frontpage/footer.html')

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
                    valid_response = "is_valid:true" in response.text
                except TypeError as error:
                    valid_response = False

                return valid_response

            if validate(request.args):
                p = re.search(r"/(?P<steamid>([0-9]{17}))", str(request.args["openid.claimed_id"]))
                if p:
                    steamid = p.group("steamid")
                    webserver_user = User(steamid)
                    login_user(webserver_user, remember=True)

            return redirect("/")

        @self.app.route('/logout')
        @login_required
        def logout():
            # Normal logout - no log needed
            self.connected_clients.pop(current_user.id, None)  # Safe deletion
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

        @self.app.route('/map_tiles/<int:z>/<x>/<y>.png')
        def map_tile_proxy(z, x, y):
            """Proxy map tiles from game server to avoid CORS issues"""
            # Parse x and y as integers (Flask's <int> doesn't support negative numbers)
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                logger.warn("tile_request_invalid_coords",
                           z=z, x=x, y=y,
                           user=current_user.id if current_user.is_authenticated else "anonymous")
                return Response(status=400)

            # Get game server host and port from telnet module config
            telnet_module = loaded_modules_dict.get("module_telnet")
            if telnet_module:
                game_host = telnet_module.options.get("host", "localhost")
                telnet_port = telnet_module.options.get("port", 8081)
                # Web interface port is always telnet port + 1
                web_port = telnet_port + 1
            else:
                game_host = "localhost"
                web_port = 8082  # Default 7D2D web port

            # 7D2D uses inverted Y-axis for tiles
            y_flipped = (-y) - 1
            tile_url = f'http://{game_host}:{web_port}/map/{z}/{x}/{y_flipped}.png'

            # Forward relevant headers from browser to game server
            headers = {}
            if request.headers.get('User-Agent'):
                headers['User-Agent'] = request.headers.get('User-Agent')
            if request.headers.get('Referer'):
                headers['Referer'] = request.headers.get('Referer')

            # Add game server session cookie for authentication
            cookies = {}
            if self.game_server_session_id:
                cookies['sid'] = self.game_server_session_id

            try:
                response = get(tile_url, headers=headers, cookies=cookies, timeout=5)

                # Only log non-200 responses
                if response.status_code != 200:
                    logger.error("tile_fetch_failed",
                                z=z, x=x, y=y,
                                user=current_user.id if current_user.is_authenticated else "anonymous",
                                status=response.status_code,
                                url=tile_url,
                                has_sid=bool(self.game_server_session_id))

                return Response(
                    response.content,
                    status=response.status_code,
                    content_type='image/png'
                )
            except Exception as e:
                logger.error("tile_fetch_exception",
                            z=z, x=x, y=y,
                            user=current_user.id if current_user.is_authenticated else "anonymous",
                            url=tile_url,
                            error=str(e),
                            error_type=type(e).__name__)
                return Response(status=404)

        @self.app.route('/profiling')
        def profiling_stats():
            """Display profiling statistics as plain text"""
            from bot.profiler import profiler
            from datetime import datetime

            all_stats = profiler.get_all_stats()
            sorted_metrics = sorted(
                all_stats.items(),
                key=lambda x: x[1]['avg'] if x[1] else 0,
                reverse=True
            )

            lines = []
            lines.append("=" * 80)
            lines.append("Performance Profiling Statistics")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("=" * 80)
            lines.append("")

            if sorted_metrics:
                lines.append("TOP 3 SLOWEST:")
                for i, (name, stats) in enumerate(sorted_metrics[:3]):
                    if stats:
                        lines.append(f"  {i+1}. {name}: avg={stats['avg']*1000:.2f}ms p95={stats['p95']*1000:.2f}ms")
                lines.append("")

            lines.append(f"{'Metric':<40} {'Count':>8} {'Avg':>10} {'P95':>10} {'Max':>10}")
            lines.append("-" * 80)

            for name, stats in sorted_metrics:
                if stats:
                    lines.append(
                        f"{name:<40} {stats['count']:>8} "
                        f"{stats['avg']*1000:>9.2f}ms {stats['p95']*1000:>9.2f}ms {stats['max']*1000:>9.2f}ms"
                    )

            if not sorted_metrics:
                lines.append("No profiling data yet.")

            return Response('\n'.join(lines), mimetype='text/plain')

        # endregion

        # region Websocket handling
        @self.websocket.on('connect')
        @self.authenticated_only
        def connect_handler():
            if not hasattr(request, 'sid'):
                return False  # not allowed here
            else:
                user = self.connected_clients[current_user.id]

                # Check if user already has active session(s)
                if len(user.socket_ids) > 0:
                    # User has active session - ask if they want to take over
                    emit('session_conflict', {
                        'existing_sessions': len(user.socket_ids),
                        'message': 'Sie haben bereits eine aktive Session. Möchten Sie diese übernehmen? (Ungespeicherte Daten könnten verloren gehen)'
                    }, room=request.sid)
                    # Don't add socket yet - wait for user response
                else:
                    # First session - connect normally
                    user.add_socket(request.sid)
                    emit('session_accepted', room=request.sid)
                    for module in loaded_modules_dict.values():
                        module.on_socket_connect(current_user.id)
                    return None

        @self.websocket.on('disconnect')
        def disconnect_handler():
            # Remove this socket from the user's socket list
            if current_user.is_authenticated and current_user.id in self.connected_clients:
                user = self.connected_clients[current_user.id]
                user.remove_socket(request.sid)
                
                # If user has no more active sockets, notify modules and clean up
                if len(user.socket_ids) == 0:
                    logger.info("user_fully_disconnected", 
                               user=current_user.id,
                               sid=request.sid)
                    
                    # Notify all modules about disconnection
                    for module in loaded_modules_dict.values():
                        module.on_socket_disconnect(current_user.id)
                else:
                    logger.debug("socket_disconnected_but_user_has_other_sessions",
                                user=current_user.id,
                                sid=request.sid,
                                remaining_sockets=len(user.socket_ids))

        @self.websocket.on('ding')
        def ding_dong():
            current_user.last_seen = time()
            try:
                # Use request.sid (current socket) not current_user.sid (could be another browser!)
                emit('dong', room=request.sid)

            except AttributeError as error:
                # user disappeared
                logger.debug("client_disappeared", user=current_user.id, sid=request.sid)

        @self.websocket.on('session_takeover_accept')
        @self.authenticated_only
        def session_takeover_accept():
            """User accepted to take over existing session - disconnect old sessions."""
            user = self.connected_clients[current_user.id]

            # Disconnect all existing sessions
            old_sockets = user.socket_ids.copy()
            for old_sid in old_sockets:
                # Notify old session that it's being taken over
                emit('session_taken_over', {
                    'message': 'Ihre Session wurde von einem anderen Browser übernommen.'
                }, room=old_sid)
                # Force disconnect old socket
                self.websocket.server.disconnect(old_sid)
                user.remove_socket(old_sid)

            # Add new session
            user.add_socket(request.sid)
            emit('session_accepted', room=request.sid)

            # Initialize widgets for new session
            for module in loaded_modules_dict.values():
                module.on_socket_connect(current_user.id)

            logger.info("session_takeover",
                       user=current_user.id,
                       old_sessions=len(old_sockets),
                       new_sid=request.sid)

        @self.websocket.on('session_takeover_decline')
        @self.authenticated_only
        def session_takeover_decline():
            """User declined to take over - disconnect new session."""
            emit('session_declined', {
                'message': 'Session-Übernahme abgelehnt. Bitte schließen Sie die andere Session zuerst.'
            }, room=request.sid)

            # Disconnect this (new) session
            self.websocket.server.disconnect(request.sid)

            logger.info("session_takeover_declined",
                       user=current_user.id,
                       declined_sid=request.sid)

        @self.websocket.on('widget_event')
        @self.authenticated_only
        def widget_event(data, callback=None):
            try:
                self.dispatch_socket_event(data[0], data[1], current_user.id)
                
                # Acknowledge successful receipt
                if callback:
                    callback({'status': 'received'})
            except Exception as error:
                logger.error("widget_event_error", 
                            user=current_user.id,
                            error=str(error),
                            error_type=type(error).__name__)
                if callback:
                    callback({'status': 'error', 'message': str(error)})
        # endregion

        # Check if we're running under a WSGI server (like gunicorn)
        # If so, don't start our own server thread - the WSGI server will handle it
        running_under_wsgi = os.environ.get('RUNNING_UNDER_WSGI', 'false').lower() == 'true'

        if not running_under_wsgi:
            # Running standalone with Flask development server
            websocket_instance = Thread(
                target=self.websocket.run,
                args=[self.app],
                kwargs={
                    "host": self.options.get("host", self.default_options.get("host")),
                    "port": self.options.get("port", self.default_options.get("port"))
                }
            )
            websocket_instance.start()

            while not self.stopped.wait(self.next_cycle):
                profile_start = time()

                self.trigger_action_hook(self, event_data=["logged_in_users", {}])

                self.last_execution_time = time() - profile_start
                self.next_cycle = self.run_observer_interval - self.last_execution_time
        else:
            # Running under WSGI server - just register routes and return
            # The module will keep running in its thread for background tasks
            logger.info("wsgi_mode_detected")


loaded_modules_dict[Webserver().get_module_identifier()] = Webserver()
