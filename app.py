from webserver import Webserver
from time import sleep


webserver_options = {
    "Flask_secret_key": "thisissecret",
    "SocketIO_debug": True,
    "SocketIO_use_reloader": False
}
""" the webserver will try to discover the public IP if none is set in the options """
webserver = Webserver(webserver_options)
webserver.start()

while True:
    sleep(5)
