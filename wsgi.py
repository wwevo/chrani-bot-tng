#!/usr/bin/env python3
# coding=utf-8
"""
WSGI Entry Point for Gunicorn

This file is used when running the application with gunicorn.
It sets up all modules and exposes the Flask app for the WSGI server.
"""
import os
from bot import setup_modules, start_modules, started_modules_dict

# Signal to modules that we're running under a WSGI server
os.environ['RUNNING_UNDER_WSGI'] = 'true'

# Initialize all modules
setup_modules()
start_modules()

# Get the webserver module and its Flask app
webserver_module = started_modules_dict.get('module_webserver')
if not webserver_module:
    raise RuntimeError("Webserver module not found! Make sure it's properly configured.")

# Expose the Flask WSGI application for gunicorn
# With Socket.IO we serve WebSockets via gunicorn's gevent-websocket worker.
# Therefore the WSGI callable must be the underlying Flask app, not the SocketIO object.
application = webserver_module.app

# For debugging
if __name__ == "__main__":
    print("This file is meant to be run with gunicorn.")
    print("Example: gunicorn -c gunicorn.conf.py wsgi:application")
