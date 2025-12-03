# -*- coding: utf-8 -*-
"""
Gunicorn Configuration File for chrani-bot-tng (project root)

This configuration is optimized for running the bot with Flask-SocketIO and gevent.

Note:
- This file intentionally lives in the project root for tooling convenience (e.g., IDE run configs, deployment commands).
- The read-only resources copy is kept as reference documentation.
"""
# Server Socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker Processes
# Using threading mode for WebSocket support
# Multiple workers don't work well with socket.io state
workers = 1
# Use threaded worker for Flask-SocketIO in threading mode
worker_class = "gthread"
threads = 4
worker_connections = 1000
max_requests = 0  # Disable automatic worker restart
max_requests_jitter = 0
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process Naming
proc_name = "chrani-bot-tng"

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if using HTTPS directly with gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ca_certs = "/path/to/ca_certs"
# cert_reqs = 0
# ssl_version = 2
# ciphers = None

# Server Hooks
def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    print("=" * 60)
    print("chrani-bot-tng is starting...")
    print("=" * 60)


def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP.
    """
    print("Reloading workers...")


def when_ready(server):
    """
    Called just after the server is started.
    """
    print("=" * 60)
    print("chrani-bot-tng is ready to accept connections")
    print(f"Listening on: {bind}")
    print("=" * 60)


def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    """
    pass


def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    print(f"Worker spawned (pid: {worker.pid})")


def post_worker_init(worker):
    """
    Called just after a worker has initialized the application.
    """
    print(f"Worker initialized (pid: {worker.pid})")


def worker_int(worker):
    """
    Called just after a worker received the SIGINT or SIGQUIT signal.
    """
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """
    Called when a worker received the SIGABRT signal.
    """
    print(f"Worker received SIGABRT signal (pid: {worker.pid})")


def pre_exec(server):
    """
    Called just before a new master process is forked.
    """
    print("Forking new master process...")


def pre_request(worker, req):
    """
    Called just before a worker processes the request.
    """
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """
    Called after a worker processes the request.
    """
    pass


def child_exit(server, worker):
    """
    Called just after a worker has been exited.
    """
    print(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """
    Called just after a worker has been exited.
    """
    print(f"Worker process exiting (pid: {worker.pid})")


def nworkers_changed(server, new_value, old_value):
    """
    Called just after num_workers has been changed.
    """
    print(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """
    Called just before exiting gunicorn.
    """
    print("=" * 60)
    print("chrani-bot-tng is shutting down...")
    print("=" * 60)
