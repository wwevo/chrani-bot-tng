""" some IDE's will throw 'PEP 8' warnings for imports, but this has to happen early """
import os
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

from gevent import monkey
monkey.patch_all()

""" standard imports """
import re

from flask import Flask, request, redirect, render_template, Markup
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO

from requests import post
from urllib.parse import urlencode


class User(UserMixin, object):
    def __init__(self, steamid=None):
        self.id = steamid


if __name__ == '__main__':
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, 'templates'),
        static_folder=os.path.join(root_dir, 'static')
    )
    app.config["SECRET_KEY"] = "totallyasecret"

    login_manager = LoginManager()
    login_manager.init_app(app)

    socketio = SocketIO(app, async_mode='gevent')


    @login_manager.user_loader
    def user_loader(steamid):
        """ This is where the authentication will happen, see if that user in in your allowed players database or
         whatever """
        print(steamid)
        return User(steamid)


    @app.route('/login')
    def login():
        steam_openid_url = 'https://steamcommunity.com/openid/login'
        u = {
            'openid.ns': "http://specs.openid.net/auth/2.0",
            'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
            'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
            'openid.mode': 'checkid_setup',
            'openid.return_to': "http://{}:{}/authenticate".format("127.0.0.1", 5000),
            'openid.realm': "http://{}:{}".format("127.0.0.1", 5000)
        }
        query_string = urlencode(u)
        auth_url = "{}?{}".format(steam_openid_url, query_string)
        return redirect(auth_url)


    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect("/")


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

            r = post(steam_login_url_base, data=params_dict)

            if "is_valid:true" in r.text:
                return True

            # this fucntion should always return False if the payload is not valid
            return False

        valid = validate(request.args)
        if valid is True:
            p = re.search(r"/(?P<steamid>([0-9]{17}))", str(request.args["openid.claimed_id"]))
            if p:
                steamid = p.group("steamid")
                player_object = User(steamid)

                login_user(player_object, remember=True)
                return redirect("/protected")

        return redirect("/")


    @app.route('/unauthorized')
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return redirect("/")


    @app.errorhandler(404)
    def page_not_found(error):
        output = '<div class="widget forced">'
        output += '<p>Page not found :(</p>'
        output += '<p><a href="/">home</a></p>'
        output += "</div>"
        markup = Markup(output)
        return render_template('index.html', content=markup), 404


    @app.route('/')
    def index():
        if current_user.is_authenticated is True:
            return redirect("/protected")

        output = '<div class="widget forced">'
        output += '<p>Welcome to the <strong>chrani-bot: the next generation</strong></p>'
        output += '<p>' \
                  'please <a href="/login">log in with your steam account</a> to get access to the protected stuff' \
                  '</p>'
        output += '</div>'

        markup = Markup(output)
        return render_template('index.html', content=markup)


    @app.route('/protected')
    @login_required
    def protected():
        output = '<div class="widget forced">'
        output += '<p>Welcome to the <strong>chrani-bot: the next generation</strong> (protected)</p>'
        output += '<p>' \
                  'Since there is nothing to do here, you might just as well <a href="/logout">log out</a> again.' \
                  '</p>'
        output += '</div>'

        markup = Markup(output)
        return render_template('index.html', content=markup)


    @socketio.on('dummy', namespace='/chrani-bot-ng')
    def dummy(message):
        print("socket answered!")

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False
    )
