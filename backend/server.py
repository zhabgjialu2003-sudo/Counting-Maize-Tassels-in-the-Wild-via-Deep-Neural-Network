"""Production-oriented Waitress entry point for the Maize Detector API.

Preloads the model before accepting requests and runs a bounded WSGI thread
pool. Public HTTPS termination remains the responsibility of the hosting
platform or reverse proxy.

Usage:
    cd backend
    python server.py
"""

import sys
import os
from pathlib import Path

from waitress import serve

# Ensure backend is on Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

# Import app - this loads the YOLO model BEFORE the server starts
from app import app, db_ready, get_predictor, start_backup_scheduler
from migrations import apply_migrations


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
if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
    try:
        apply_migrations()
    except Exception as exc:
        raise SystemExit(f"Database migration failed: {exc}") from exc

if get_predictor is None:
    raise SystemExit("AI startup check failed: inference.py could not be imported")

try:
    predictor = get_predictor()
    if not predictor.available:
        raise RuntimeError("the configured tassel model could not be loaded")
except Exception as exc:
    raise SystemExit(f"AI startup check failed: {exc}") from exc

host = os.getenv("WAITRESS_HOST", os.getenv("HOST", "127.0.0.1"))
port = int(os.getenv("WAITRESS_PORT", os.getenv("PORT", "5000")))
print(f"Maize Detector API running at http://{host}:{port}")
print("Database: PostgreSQL connected")
print(f"AI Inference: {predictor.model_path.name} loaded")
start_backup_scheduler()

serve(
    app,
    host=host,
    port=port,
    threads=max(1, int(os.getenv("WAITRESS_THREADS", os.getenv("WSGI_THREADS", "4")))),
    channel_timeout=max(30, int(os.getenv("WAITRESS_CHANNEL_TIMEOUT", "120"))),
    clear_untrusted_proxy_headers=True,
)
