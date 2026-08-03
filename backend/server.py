"""Simple production server for Maize Detector API.

Uses Python's built-in WSGI server with proper model preloading
to avoid the Flask dev server + YOLO threading issues on Windows.

Usage:
    cd backend
    python server.py
"""

import sys
import os
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server
from pathlib import Path

# Ensure backend is on Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

# Import app - this loads the YOLO model BEFORE the server starts
from app import app, db_ready, get_predictor, start_backup_scheduler


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

configuration_errors = []
if app.config["SECRET_KEY"] == "week10-development-key-change-before-production":
    configuration_errors.append("SECRET_KEY is still using the development default")
if not os.getenv("FILE_ENCRYPTION_KEY"):
    configuration_errors.append("FILE_ENCRYPTION_KEY is not configured")
if configuration_errors:
    raise SystemExit("Security startup check failed: " + "; ".join(configuration_errors))

database_ready, database_error = db_ready()
if not database_ready:
    raise SystemExit(f"PostgreSQL startup check failed: {database_error}")

if get_predictor is None:
    raise SystemExit("AI startup check failed: inference.py could not be imported")

try:
    predictor = get_predictor()
    if not predictor.available:
        raise RuntimeError("backend/models/best.pt could not be loaded")
except Exception as exc:
    raise SystemExit(f"AI startup check failed: {exc}") from exc

host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", "5000"))
print(f"Maize Detector API running at http://{host}:{port}")
print("Database: PostgreSQL connected")
print("AI Inference: backend/models/best.pt loaded")
start_backup_scheduler()

# Use a lightweight threaded WSGI server for the local assessment demo.
httpd = make_server(host, port, app, server_class=ThreadingWSGIServer)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down...")
    httpd.server_close()
