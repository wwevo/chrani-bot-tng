from webserver import Webserver
from time import sleep

webserver_options = {
    "host": "127.0.0.1",
    "port": 5000,
    "Flask_secret_key": "thisissecret",
    "SocketIO_debug": True
}

webserver = Webserver(webserver_options)
webserver.start()

while True:
    sleep(5)
