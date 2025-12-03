from flask import request, Response
from requests import post, get
from bot import loaded_modules_dict


class GameServerProxy(object):
    """
    Mixin for proxying game server web API requests.
    Handles authentication with game server and proxying map tiles.
    Requires: Flask app
    """

    game_server_session_id = None

    def __init__(self):
        self.game_server_session_id = None

    def login_to_game_server(self):
        """
        Authenticate with game server web API and store session cookie.
        Uses credentials from telnet module configuration.
        """
        telnet_module = loaded_modules_dict.get("module_telnet")
        if not telnet_module:
            print("game_server_login_telnet_missing")
            return

        game_host = telnet_module.options.get("host")
        telnet_port = telnet_module.options.get("port", 8081)
        web_port = telnet_port + 1

        web_username = telnet_module.options.get("web_username", "")
        web_password = telnet_module.options.get("web_password", "")

        if not web_username or not web_password:
            print("game_server_login_no_credentials")
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
                else:
                    print("game_server_login_no_sid_cookie")
            else:
                print("game_server_login_failed")
        except Exception as e:
            print("game_server_login_exception")

    def _register_proxy_routes(self):
        """
        Register game server proxy routes.
        Must be called during setup after app is initialized.
        """

        @self.app.route('/map_tiles/<int:z>/<x>/<y>.png')
        def map_tile_proxy(z, x, y):
            """Proxy map tiles from game server to avoid CORS issues"""
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print("tile_request_invalid_coords")
                return Response(status=400)

            telnet_module = loaded_modules_dict.get("module_telnet")
            if telnet_module:
                game_host = telnet_module.options.get("host", "localhost")
                telnet_port = telnet_module.options.get("port", 8081)
                web_port = telnet_port + 1
            else:
                game_host = "localhost"
                web_port = 8082

            y_flipped = (-y) - 1
            tile_url = f'http://{game_host}:{web_port}/map/{z}/{x}/{y_flipped}.png'

            headers = {}
            if request.headers.get('User-Agent'):
                headers['User-Agent'] = request.headers.get('User-Agent')
            if request.headers.get('Referer'):
                headers['Referer'] = request.headers.get('Referer')

            cookies = {}
            if self.game_server_session_id:
                cookies['sid'] = self.game_server_session_id

            try:
                response = get(tile_url, headers=headers, cookies=cookies, timeout=5)

                if response.status_code != 200:
                    print("tile_fetch_failed")

                return Response(
                    response.content,
                    status=response.status_code,
                    content_type='image/png'
                )
            except Exception as e:
                print("tile_fetch_exception")
                return Response(status=404)
