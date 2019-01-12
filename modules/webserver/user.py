from flask_login import UserMixin


class User(UserMixin, object):
    id = str

    def __init__(self, steamid=None):
        self.id = steamid
