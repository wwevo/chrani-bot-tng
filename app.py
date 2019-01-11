from webserver import Webserver
from time import sleep


webserver_options = {
    "Flask_secret_key": "thisissecret",
    "SocketIO_debug": False,
    "SocketIO_use_reloader": False,
    "SocketIO_asynch_mode": "eventlet"
}
""" the webserver will try to discover the public IP if none is set in the options """
webserver = Webserver()
webserver.start(webserver_options)

while True:
    sleep(5)
