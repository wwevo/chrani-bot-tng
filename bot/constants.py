"""
Constants for chrani-bot-tng

This module contains all constants used throughout the bot to avoid
magic numbers and improve maintainability.
"""

# =============================================================================
# Permission Levels
# =============================================================================

# Permission levels for player access control
PERMISSION_LEVEL_ADMIN = 0          # Full access
PERMISSION_LEVEL_MODERATOR = 1      # Moderate players
PERMISSION_LEVEL_BUILDER = 2        # Build permissions
PERMISSION_LEVEL_PLAYER = 4         # Regular player
PERMISSION_LEVEL_DEFAULT = 2000     # Default for new/unknown players

# =============================================================================
# Telnet Command Timeouts (seconds)
# =============================================================================

TELNET_TIMEOUT_VERY_SHORT = 1.5     # Quick polls
TELNET_TIMEOUT_SHORT = 2            # Standard commands (lp, gettime)
TELNET_TIMEOUT_NORMAL = 3           # Most commands (listents)
TELNET_TIMEOUT_EXTENDED = 8         # Complex commands (manage entities)
TELNET_TIMEOUT_RECONNECT = 10       # Wait before reconnect attempt

# =============================================================================
# Telnet Buffer Limits
# =============================================================================

TELNET_BUFFER_MAX_SIZE = 12288      # Maximum telnet buffer size (bytes)
TELNET_LINES_MAX_HISTORY = 150      # Maximum telnet lines to keep in history

# =============================================================================
# Server Settings
# =============================================================================

DEFAULT_SERVER_PORT = 5000          # Default webserver port
DEFAULT_OBSERVER_INTERVAL = 0.1     # Default module polling interval (seconds)

# =============================================================================
# WebSocket Settings
# =============================================================================

WEBSOCKET_PING_TIMEOUT = 15         # WebSocket ping timeout (seconds)
WEBSOCKET_PING_INTERVAL = 5         # WebSocket ping interval (seconds)

# =============================================================================
# Thread Pool Settings
# =============================================================================

CALLBACK_THREAD_POOL_SIZE = 10      # Max concurrent callback threads

# =============================================================================
# String/Token Generation
# =============================================================================

DEFAULT_TOKEN_LENGTH = 20           # Default length for random tokens

# =============================================================================
# Helper Functions
# =============================================================================

def get_permission_level_name(level: int) -> str:
    """
    Get human-readable name for a permission level.

    Args:
        level: Permission level integer

    Returns:
        String name of the permission level
    """
    permission_names = {
        PERMISSION_LEVEL_ADMIN: "Admin",
        PERMISSION_LEVEL_MODERATOR: "Moderator",
        PERMISSION_LEVEL_BUILDER: "Builder",
        PERMISSION_LEVEL_PLAYER: "Player",
        PERMISSION_LEVEL_DEFAULT: "Default/Unknown"
    }
    return permission_names.get(level, f"Custom ({level})")


def is_admin(permission_level: int) -> bool:
    """Check if permission level is admin."""
    return permission_level == PERMISSION_LEVEL_ADMIN


def is_moderator_or_higher(permission_level: int) -> bool:
    """Check if permission level is moderator or higher (lower number = higher privilege)."""
    return permission_level <= PERMISSION_LEVEL_MODERATOR


def is_builder_or_higher(permission_level: int) -> bool:
    """Check if permission level is builder or higher."""
    return permission_level <= PERMISSION_LEVEL_BUILDER
