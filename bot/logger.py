"""
Structured logging system for chrani-bot-tng

Provides context-aware logging with consistent formatting across the entire application.
Replaces print() statements with structured, grep-able log output.

Usage:
    from bot.logger import get_logger

    logger = get_logger("webserver")

    # Error logging (always shown)
    logger.error("tile_fetch_failed", user="steamid123", z=4, x=-2, y=1, status=404)

    # Warning logging (always shown)
    logger.warn("auth_missing_sid", user="steamid456", action="tile_request")

    # Info logging (startup only, can be disabled)
    logger.info("module_loaded", module="webserver", version="1.0")

    # Debug logging (opt-in via config)
    logger.debug("action_trace", action="select_dom_element", path="/map/owner/id")

Output format:
    [ERROR] [2025-01-19 12:34:56.123] tile_fetch_failed | user=steamid123 z=4 x=-2 y=1 status=404
"""

import sys
from datetime import datetime
from typing import Any, Dict, Optional


class LogLevel:
    """Log level constants"""
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogConfig:
    """Global logging configuration"""
    # Which levels to actually output
    enabled_levels = {
        LogLevel.ERROR,  # Always enabled
        LogLevel.WARN,   # Always enabled
        LogLevel.INFO,   # Enabled (for now, can be disabled after testing)
        # LogLevel.DEBUG  # Disabled by default, uncomment to enable
    }

    # Format settings
    show_timestamps = True
    timestamp_format = "%Y-%m-%d %H:%M:%S.%f"  # Includes microseconds

    @classmethod
    def enable_debug(cls):
        """Enable debug logging (call this from config or command line)"""
        cls.enabled_levels.add(LogLevel.DEBUG)

    @classmethod
    def disable_info(cls):
        """Disable info logging (for production)"""
        cls.enabled_levels.discard(LogLevel.INFO)


class ContextLogger:
    """
    Structured logger with context support

    Provides consistent, grep-able logging across the application.
    Each logger instance is bound to a specific module/component.
    """

    def __init__(self, module_name: str):
        """
        Create a logger for a specific module

        Args:
            module_name: Name of the module (e.g., "webserver", "dom_management")
        """
        self.module_name = module_name

    def _format_context(self, **context) -> str:
        """
        Format context dict as key=value pairs

        Args:
            **context: Arbitrary key-value pairs

        Returns:
            Formatted string: "key1=value1 key2=value2"
        """
        if not context:
            return ""

        # Sort keys for consistent output
        pairs = []
        for key in sorted(context.keys()):
            value = context[key]

            # Format value appropriately
            if value is None:
                formatted_value = "null"
            elif isinstance(value, str):
                # Escape spaces and special chars if needed
                if " " in value or "=" in value:
                    formatted_value = f'"{value}"'
                else:
                    formatted_value = value
            elif isinstance(value, bool):
                formatted_value = str(value).lower()
            elif isinstance(value, (list, dict)):
                # Complex types: just show type and length
                formatted_value = f"{type(value).__name__}[{len(value)}]"
            else:
                formatted_value = str(value)

            pairs.append(f"{key}={formatted_value}")

        return " ".join(pairs)

    def _log(self, level: str, event: str, **context):
        """
        Internal logging method

        Args:
            level: Log level (ERROR, WARN, INFO, DEBUG)
            event: Event name (snake_case, descriptive)
            **context: Additional context as key=value pairs
        """
        # Check if this level is enabled
        if level not in LogConfig.enabled_levels:
            return

        # Always include module in context
        context["module"] = self.module_name

        # Build timestamp
        timestamp = ""
        if LogConfig.show_timestamps:
            now = datetime.now()
            # Truncate microseconds to milliseconds
            timestamp_str = now.strftime(LogConfig.timestamp_format)[:-3]
            timestamp = f"[{timestamp_str}] "

        # Build context string
        context_str = self._format_context(**context)

        # Format: [LEVEL] [TIMESTAMP] event | context
        if context_str:
            message = f"[{level:<5}] {timestamp}{event} | {context_str}"
        else:
            message = f"[{level:<5}] {timestamp}{event}"

        # Output to stderr (standard for logs, keeps stdout clean)
        print(message, file=sys.stderr, flush=True)

    def error(self, event: str, **context):
        """
        Log an error - always shown, indicates something failed

        Use for:
        - Action failures
        - Network errors
        - Parse errors
        - Validation failures
        - Unexpected exceptions

        Args:
            event: Error event name (e.g., "tile_fetch_failed")
            **context: Additional context (user, action, error message, etc.)
        """
        self._log(LogLevel.ERROR, event, **context)

    def warn(self, event: str, **context):
        """
        Log a warning - always shown, indicates something unexpected but handled

        Use for:
        - Fallback behavior activated
        - Deprecated feature used
        - Rate limiting triggered
        - Auth retry needed
        - Missing optional config

        Args:
            event: Warning event name (e.g., "auth_missing_sid")
            **context: Additional context
        """
        self._log(LogLevel.WARN, event, **context)

    def info(self, event: str, **context):
        """
        Log informational message - shown during startup, can be disabled

        Use for:
        - Module loaded
        - Server started
        - Configuration summary
        - Connection established

        Args:
            event: Info event name (e.g., "module_loaded")
            **context: Additional context
        """
        self._log(LogLevel.INFO, event, **context)

    def debug(self, event: str, **context):
        """
        Log debug information - disabled by default, opt-in

        Use for:
        - Action execution traces
        - Data transformations
        - Flow control decisions
        - Detailed state changes

        Enable with: LogConfig.enable_debug()

        Args:
            event: Debug event name (e.g., "action_trace")
            **context: Additional context
        """
        self._log(LogLevel.DEBUG, event, **context)


# Global logger registry
_loggers: Dict[str, ContextLogger] = {}


def get_logger(module_name: str) -> ContextLogger:
    """
    Get or create a logger for a specific module

    Args:
        module_name: Module identifier (e.g., "webserver", "dom_management")

    Returns:
        ContextLogger instance for this module

    Example:
        logger = get_logger("webserver")
        logger.error("connection_failed", host="localhost", port=8080)
    """
    if module_name not in _loggers:
        _loggers[module_name] = ContextLogger(module_name)
    return _loggers[module_name]


# Convenience function for quick usage
def log_error(module: str, event: str, **context):
    """Quick error logging without getting logger instance"""
    get_logger(module).error(event, **context)


def log_warn(module: str, event: str, **context):
    """Quick warning logging without getting logger instance"""
    get_logger(module).warn(event, **context)


def log_info(module: str, event: str, **context):
    """Quick info logging without getting logger instance"""
    get_logger(module).info(event, **context)


def log_debug(module: str, event: str, **context):
    """Quick debug logging without getting logger instance"""
    get_logger(module).debug(event, **context)
