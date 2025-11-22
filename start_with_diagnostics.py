#!/usr/bin/env python3
"""
Start chrani-bot-tng with diagnostic logging enabled.

This script activates extended logging features:
- File-based logging to diagnostic_logs/ directory
- Raw telnet data logging
- Action execution logging
- Debug-level logging
- All regular log output (errors, warnings, info)

The logs are written to timestamped files in the diagnostic_logs/ directory:
- all_YYYYMMDD_HHMMSS.log: All log messages
- errors_YYYYMMDD_HHMMSS.log: Only error messages
- telnet_raw_YYYYMMDD_HHMMSS.log: Raw telnet data from gameserver
- actions_YYYYMMDD_HHMMSS.log: Bot action executions

Usage:
    python start_with_diagnostics.py

The bot will run normally with all diagnostic features enabled.
Press Ctrl+C to stop the bot and close log files gracefully.
"""

import sys
import signal
from pathlib import Path

# Import logger configuration before anything else
from bot.logger import LogConfig

def setup_diagnostics():
    """Configure diagnostic logging."""
    print("[DIAGNOSTICS] Enabling file logging...")
    
    # Enable file logging (creates diagnostic_logs/ directory)
    LogConfig.enable_file_logging(log_dir="diagnostic_logs")
    
    # Enable debug-level logging
    LogConfig.enable_debug()
    
    print("[DIAGNOSTICS] Debug logging enabled")
    print("[DIAGNOSTICS] Log files created in: diagnostic_logs/")
    print("[DIAGNOSTICS] Starting bot with diagnostics...\n")

def cleanup_on_exit(signum=None, frame=None):
    """Clean up log files on exit."""
    print("\n[DIAGNOSTICS] Shutting down, closing log files...")
    LogConfig.close_log_files()
    print("[DIAGNOSTICS] Log files closed")
    sys.exit(0)

def main():
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup_on_exit)
    signal.signal(signal.SIGTERM, cleanup_on_exit)
    
    # Enable diagnostics before importing the bot
    setup_diagnostics()
    
    # Import and start the bot
    try:
        import app
        # The app.py module will start the bot when imported
        # Keep the main thread alive
        import threading
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                thread.join()
    except KeyboardInterrupt:
        cleanup_on_exit()
    except Exception as e:
        print(f"[DIAGNOSTICS] Error starting bot: {e}")
        LogConfig.close_log_files()
        raise

if __name__ == "__main__":
    main()
