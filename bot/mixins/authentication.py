import functools
import re
from flask import request, redirect
from flask_login import login_required, login_user, current_user, logout_user
from flask_socketio import disconnect
from requests import post
from urllib.parse import urlencode
from time import time


class Authentication(object):
    """
    Mixin for Steam OpenID authentication and session management.
    Requires: Flask app, LoginManager, connected_clients dict
    """

    def __init__(self):
        pass

    @staticmethod
    def authenticated_only(f):
        """Decorator to ensure user is authenticated for SocketIO events"""
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                disconnect()
            else:
                return f(*args, **kwargs)
        return wrapped

    def _register_auth_routes(self):
        """
        Register all authentication-related Flask routes.
        Must be called during setup after app and login_manager are initialized.
        """

        # User loader for Flask-Login
        @self.login_manager.user_loader
        def user_loader(steamid):
            webserver_user = self.connected_clients.get(steamid, False)
            if not webserver_user:
                from bot.modules.webserver.user import User
                webserver_user = User(steamid, time())
                self.connected_clients[steamid] = webserver_user
            return webserver_user

        # Steam OpenID login initiation
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

        # Steam OpenID authentication callback
        @self.app.route('/authenticate', methods=['GET'])
        def authenticate():
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
                    from bot.modules.webserver.user import User
                    webserver_user = User(steamid)
                    login_user(webserver_user, remember=True)

            return redirect("/")

        # Logout
        @self.app.route('/logout')
        @login_required
        def logout():
            self.connected_clients.pop(current_user.id, None)
            logout_user()
            return redirect("/")

        # Unauthorized handler
        @self.app.route('/unauthorized')
        @self.login_manager.unauthorized_handler
        def unauthorized_handler():
            return redirect("/")
