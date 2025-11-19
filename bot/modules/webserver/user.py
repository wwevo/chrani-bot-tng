from flask_login import UserMixin
from time import time


class User(UserMixin, object):
    id = str
    last_seen = float
    browser_token = str
    socket_ids = list  # Multiple socket IDs for multiple browser sessions

    def __init__(self, steamid, last_seen=None):
        self.id = steamid
        self.last_seen = time() if last_seen is None else last_seen
        self.instance_token = "anonymous"
        self.socket_ids = []  # Track all socket connections for this user

    def add_socket(self, sid):
        """Add a socket ID to this user's connections."""
        if sid not in self.socket_ids:
            self.socket_ids.append(sid)

    def remove_socket(self, sid):
        """Remove a socket ID from this user's connections."""
        if sid in self.socket_ids:
            self.socket_ids.remove(sid)

    @property
    def sid(self):
        """Return the first (primary) socket ID for backward compatibility."""
        return self.socket_ids[0] if self.socket_ids else None
