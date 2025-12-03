PERMISSION_LEVEL_ADMIN = 0          # Full access
PERMISSION_LEVEL_MODERATOR = 1      # Moderate players
PERMISSION_LEVEL_BUILDER = 2        # Build permissions
PERMISSION_LEVEL_PLAYER = 4         # Regular player
PERMISSION_LEVEL_DEFAULT = 2000     # Default for new/unknown players

TELNET_TIMEOUT_VERY_SHORT = 1.5     # Quick polls
TELNET_TIMEOUT_SHORT = 2            # Standard commands (lp, gettime)
TELNET_TIMEOUT_NORMAL = 3           # Most commands (listents)
TELNET_TIMEOUT_EXTENDED = 8
TELNET_TIMEOUT_RECONNECT = 20
TELNET_BUFFER_MAX_SIZE = 12288      # Maximum telnet buffer size (bytes)
TELNET_LINES_MAX_HISTORY = 150      # Maximum telnet lines to keep in history

DEFAULT_SERVER_PORT = 5000          # Default webserver port
DEFAULT_OBSERVER_INTERVAL = 1       # Default module polling interval (seconds)

WEBSOCKET_PING_TIMEOUT = 10         # WebSocket ping timeout (seconds)
WEBSOCKET_PING_INTERVAL = 3         # WebSocket ping interval (seconds)

CALLBACK_THREAD_POOL_SIZE = 10      # Max concurrent callback threads
DEFAULT_TOKEN_LENGTH = 20           # Default length for random tokens

TELNET_PREFIXES = {
    "telnet_log": {
        "timestamp": r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
    },
    "GMSG": {
        "command": (
            r"GMSG:\s"
            r"Player\s\'"
            r"(?P<player_name>.*)"
            r"\'\s"
            r"(?P<command>.*)$"
        )
    }
}

def get_permission_level_name(level: int) -> str:
    permission_names = {
        PERMISSION_LEVEL_ADMIN: "Admin",
        PERMISSION_LEVEL_MODERATOR: "Moderator",
        PERMISSION_LEVEL_BUILDER: "Builder",
        PERMISSION_LEVEL_PLAYER: "Player",
        PERMISSION_LEVEL_DEFAULT: "None"
    }
    return permission_names.get(level)


def is_admin(permission_level: int) -> bool:
    return permission_level == PERMISSION_LEVEL_ADMIN


def is_moderator_or_higher(permission_level: int) -> bool:
    return permission_level <= PERMISSION_LEVEL_MODERATOR


def is_builder_or_higher(permission_level: int) -> bool:
    return permission_level <= PERMISSION_LEVEL_BUILDER
