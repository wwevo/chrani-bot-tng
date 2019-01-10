import socket
from webserver import Webserver
from time import sleep


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


webserver_options = {
    "host": get_ip(),
    "port": 5000,
    "Flask_secret_key": "thisissecret",
    "SocketIO_debug": True
}

webserver = Webserver(webserver_options)
webserver.start()

while True:
    sleep(5)
