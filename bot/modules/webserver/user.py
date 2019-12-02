from flask_login import UserMixin
from time import time


class User(UserMixin, object):
    id = str
    last_seen = float
    browser_token = str

    def __init__(self, steamid, last_seen=None):
        self.id = steamid
        self.last_seen = time() if last_seen is None else last_seen
        self.instance_token = "anonymous"
