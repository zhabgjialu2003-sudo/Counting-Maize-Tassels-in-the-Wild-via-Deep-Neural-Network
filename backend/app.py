"""Flask controls organized by the FYP-26-S2-7 User Stories.

USER STORY API INDEX
====================
Farmer
  A.1 Upload images              -> POST /api/upload
  A.2 Count tassels              -> POST /api/predict
  A.3 View result                -> GET  /api/results/<result_id>
  A.4 Highlight tassels          -> GET  /api/results/<result_id>
                                      GET  /api/images/<image_id>/file/<file_type>
  A.5 Batch upload               -> repeated A.1 + A.2 requests
  A.6 Quick result               -> POST /api/predict (fast mode and cache)
  A.7 Mobile access              -> shared authenticated A.1 + A.2 APIs
  A.8 Intuitive interface        -> GET   /api/auth/me
                                      PATCH /api/auth/profile
                                      POST  /api/auth/change-password
                                      GET   /api/stats

Researcher
  B.1 Accurate result review     -> POST /api/results/<result_id>/flag
  B.2 Export standard formats    -> GET  /api/history
  B.3 Historical analysis        -> GET  /api/history
  B.4 Compare models             -> POST /api/models/compare
  B.5 Access raw datasets        -> GET  /api/datasets
                                      GET  /api/datasets/<dataset_id>/download
  B.6 Generate visual reports    -> POST /api/reports

Agronomist
  C.1 Evaluate plant health      -> GET  /api/fields/<field_id>/health
                                      GET/POST /api/fields/<field_id>/recommendations
                                      POST /api/agronomy/diagnose
                                      POST /api/agronomy/diagnoses/<diagnosis_id>/review
  C.2 Monitor growth             -> GET  /api/fields/<field_id>/growth
  C.3 Detect anomalies           -> GET  /api/fields/anomalies
                                      POST /api/fields/<field_id>/anomaly
  C.4 View multiple fields       -> GET  /api/fields
  C.5 Summarized insights        -> GET  /api/fields/insights

Admin
  D.1 Manage users               -> /api/users and /api/users/<user_id>
  D.2 Secure image storage       -> /api/access-policies, /api/admin/storage
  D.3 Monitor system usage       -> /api/admin/stats, /api/admin/logs
  D.4 Manage datasets            -> /api/datasets and /api/datasets/upload
  D.5 Control permissions        -> /api/users/<user_id>/permissions
  D.6 Backup data                -> /api/admin/backup and /api/admin/backups

AI System
  E.1 Preprocess images          -> POST /api/system/preprocess/<image_id>
  E.2 Train models               -> GET/POST /api/training-runs
  E.3 Evaluate models            -> POST /api/models/<model_id>/evaluate
  E.4 Deploy model service       -> POST /api/models/<model_id>/deploy
  E.5 Register model updates     -> GET/POST /api/models

Shared helpers, authentication, database access, and security stay above the
routes because they support multiple User Stories.
"""

from __future__ import annotations

import os
import io
import json
from dotenv import load_dotenv
load_dotenv()  # load .env file so PGPASSWORD etc. are always available
import hashlib
import base64
import shutil
import subprocess
import tempfile
import tarfile
import zipfile
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, Response, redirect, send_from_directory
from flask_cors import CORS
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet, InvalidToken

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

try:
    from .inference import activate_predictor, get_predictor
except ImportError:
    try:
        from inference import activate_predictor, get_predictor
    except ImportError:
        activate_predictor = None
        get_predictor = None

try:
    from .advice_engine import build_advice, normalize_language
    from .disease_inference import (
        DiseaseModelUnavailable,
        InvalidDiseaseImage,
        get_disease_predictor,
    )
except ImportError:
    try:
        from advice_engine import build_advice, normalize_language
        from disease_inference import (
            DiseaseModelUnavailable,
            InvalidDiseaseImage,
            get_disease_predictor,
        )
    except ImportError:
        build_advice = None
        normalize_language = None
        DiseaseModelUnavailable = RuntimeError
        InvalidDiseaseImage = ValueError
        get_disease_predictor = None

try:
    from .training import evaluate_model, train_model
except ImportError:
    try:
        from training import evaluate_model, train_model
    except ImportError:
        evaluate_model = None
        train_model = None


app = Flask(__name__)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        (
            "null,http://localhost:8000,http://127.0.0.1:8000,"
            "https://zhabgjialu2003-sudo.github.io"
        ),
    ).split(",")
    if origin.strip()
]
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})
SERVICE_STARTED_AT = datetime.now()
_backup_scheduler_started = False
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "week10-development-key-change-before-production"
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}
VALID_USER_STATUSES = {"active", "disabled"}
TOKEN_MAX_AGE_SECONDS = int(os.getenv("TOKEN_MAX_AGE_SECONDS", "28800"))
ROLE_PERMISSIONS = {
    "Farmer": ["images:upload", "results:read-own", "agronomy:diagnose"],
    "Researcher": [
        "results:read",
        "results:export",
        "datasets:download",
        "models:compare",
        "reports:generate",
        "agronomy:diagnose",
    ],
    "Agronomist": [
        "fields:read",
        "fields:evaluate",
        "fields:recommend",
        "insights:generate",
        "agronomy:diagnose",
    ],
    "Admin": ["*"],
}


def db_config() -> dict[str, str | int]:
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "maize_detector"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
        "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "3")),
        "options": f"-c statement_timeout={int(os.getenv('PGSTATEMENT_TIMEOUT_MS', '5000'))}",
    }


@contextmanager
def db_connection():
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")

    config = db_config()
    if not config["password"]:
        raise RuntimeError("PGPASSWORD is not configured")

    conn = psycopg.connect(**config, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    return value


def ok(data: dict[str, Any], status: int = 200):
    return jsonify(jsonable(data)), status


def fail(message: str, status: int = 400, **extra):
    return ok({"status": "error", "message": message, **extra}, status)


def token_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="maize-auth")


def issue_access_token(user: dict[str, Any]) -> str:
    return token_serializer().dumps(
        {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "status": user.get("status", "active"),
            "permissions": permissions_for(user),
        }
    )


def authenticated_user() -> dict[str, Any] | None:
    header = request.headers.get("Authorization", "")
    token = (
        header.removeprefix("Bearer ").strip()
        if header.startswith("Bearer ")
        else request.args.get("access_token", "")
    )
    if not token:
        return None
    try:
        return token_serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None


def require_roles(*roles: str, permission: str | None = None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = authenticated_user()
            if not user:
                return fail("Authentication required", 401)
            if user.get("status") != "active":
                return fail("Account is disabled", 403)
            if roles and user.get("role") not in roles:
                return fail("You do not have permission to perform this action", 403)
            granted = user.get("permissions") or ROLE_PERMISSIONS.get(user.get("role"), [])
            if permission and "*" not in granted and permission not in granted:
                return fail(f"Missing permission: {permission}", 403)
            request.auth_user = user
            return view(*args, **kwargs)

        return wrapped

    return decorator


def permissions_for(user: dict[str, Any]) -> list[str]:
    custom = user.get("permissions")
    return custom if isinstance(custom, list) else ROLE_PERMISSIONS.get(user.get("role"), [])


def encryption_cipher() -> Fernet:
    configured = os.getenv("FILE_ENCRYPTION_KEY")
    if configured:
        return Fernet(configured.encode("ascii"))
    digest = hashlib.sha256(app.config["SECRET_KEY"].encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypted_path(filename: str) -> Path:
    return UPLOAD_DIR / f"{filename}.enc"


def secure_store_bytes(filename: str, data: bytes) -> Path:
    path = encrypted_path(filename)
    path.write_bytes(encryption_cipher().encrypt(data))
    return path


def secure_read_bytes(filename: str) -> bytes:
    encrypted = encrypted_path(filename)
    if encrypted.exists():
        try:
            return encryption_cipher().decrypt(encrypted.read_bytes())
        except InvalidToken as exc:
            raise RuntimeError("Encrypted image could not be decrypted") from exc
    plain = UPLOAD_DIR / filename
    if plain.exists():
        return plain.read_bytes()
    raise FileNotFoundError(filename)


@contextmanager
def materialized_image(filename: str):
    plain = UPLOAD_DIR / filename
    if plain.exists():
        yield plain
        return
    data = secure_read_bytes(filename)
    suffix = Path(filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


def log_action(conn, action: str, details: str, user_id: int | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO system_logs (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details),
        )


def normalize_model_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_id": row.get("model_id"),
        "model_name": row.get("model_name"),
        "model_version": row.get("model_version"),
        "weights_path": row.get("weights_path"),
        "status": row.get("status"),
        "map50": row.get("map50"),
        "precision": row.get("precision_score", row.get("precision")),
        "recall": row.get("recall_score", row.get("recall")),
        "iou_threshold": row.get("iou_threshold"),
        "parent_model_id": row.get("parent_model_id"),
        "changelog": row.get("changelog"),
        "created_at": row.get("created_at"),
        "activated_at": row.get("activated_at"),
        "comparison_mode": (
            "weights-and-metrics"
            if row.get("weights_path") and Path(str(row["weights_path"])).exists()
            else "metrics-only"
        ),
    }


def find_psql() -> str | None:
    configured = os.getenv("PSQL_PATH")
    if configured and Path(configured).exists():
        return configured
    for candidate in (
        r"C:\PostgreSQL\18\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
    ):
        if Path(candidate).exists():
            return candidate
    return shutil.which("psql")


def find_pg_restore() -> str | None:
    configured = os.getenv("PG_RESTORE_PATH")
    if configured and Path(configured).exists():
        return configured
    for candidate in (
        r"C:\PostgreSQL\18\bin\pg_restore.exe",
        r"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe",
    ):
        if Path(candidate).exists():
            return candidate
    return shutil.which("pg_restore")


def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("sha256$"):
        return stored_hash == f"sha256${hashlib.sha256(password.encode('utf-8')).hexdigest()}"
    try:
        return check_password_hash(stored_hash, password)
    except ValueError:
        return False


def db_ready() -> tuple[bool, str | None]:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                cur.fetchone()
        return True, None
    except Exception as exc:
        return False, str(exc)


def allowed_image_filename(filename: str) -> bool:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix in ALLOWED_IMAGE_EXTENSIONS


def validate_image_upload(filename: str, content_type: str | None = None) -> str | None:
    if not filename:
        return "Image filename is required"
    if not allowed_image_filename(filename):
        return "Only JPG and PNG image files are allowed"
    normalized_type = content_type.split(";", 1)[0].lower() if content_type else None
    if normalized_type and normalized_type not in ALLOWED_IMAGE_MIME_TYPES:
        return "Only image/jpeg and image/png content types are allowed"
    return None


def clean_image_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    clean_name = secure_filename(filename)
    if not clean_name or "." not in clean_name:
        suffix = suffix if suffix.lstrip(".") in ALLOWED_IMAGE_EXTENSIONS else ".jpg"
        return f"uploaded_maize_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    return clean_name


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def normalize_user_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": row.get("user_id"),
        "name": row.get("name"),
        "email": row.get("email"),
        "role_id": row.get("role_id"),
        "role": row.get("role"),
        "status": row.get("status"),
        "created_at": row.get("created_at"),
    }


def fetch_user(conn, user_id: int) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.name, u.email, u.role_id, r.role_name AS role, u.status, u.created_at
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE u.user_id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return normalize_user_row(row) if row else None


def resolve_role_id(conn, payload: dict[str, Any], required: bool = False) -> int | None:
    role_id = payload.get("role_id") or payload.get("roleId")
    role_name = payload.get("role") or payload.get("role_name") or payload.get("roleName")

    with conn.cursor() as cur:
        if role_id is not None:
            cur.execute("SELECT role_id FROM roles WHERE role_id = %s", (int(role_id),))
            row = cur.fetchone()
        elif role_name:
            cur.execute("SELECT role_id FROM roles WHERE LOWER(role_name) = LOWER(%s)", (str(role_name),))
            row = cur.fetchone()
        elif required:
            raise ValueError("role_id or role is required")
        else:
            return None

    if not row:
        raise ValueError("Role does not exist")
    return row["role_id"]


def validate_user_payload(payload: dict[str, Any], creating: bool = False) -> str | None:
    if creating:
        for field in ("name", "email"):
            if not payload.get(field):
                return f"{field} is required"
        if not (payload.get("password") or payload.get("password_hash") or payload.get("passwordHash")):
            return "password or password_hash is required"

    if "email" in payload and payload.get("email"):
        email = str(payload["email"])
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            return "A valid email address is required"

    status = payload.get("status")
    if status and status not in VALID_USER_STATUSES:
        return "status must be active or disabled"

    return None


def db_error_response(exc: Exception, fallback_status: int = 500):
    message = str(exc)
    app.logger.error("Database error: %s", message)
    if "users_email_key" in message:
        return fail("Email already exists", 409)
    if "duplicate key value" in message:
        return fail("Duplicate database key", 409)
    return fail("Database operation failed", fallback_status)


def backup_file_info(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "file_name": path.name,
        "path": f"backups/{path.name}",
        "size_bytes": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def list_backup_files() -> list[dict[str, Any]]:
    files = []
    for pattern in ("*.sql", "*.dump"):
        files.extend(BACKUP_DIR.glob(pattern))
    unique_files = sorted(set(files), key=lambda item: item.stat().st_mtime, reverse=True)
    return [backup_file_info(path) for path in unique_files if path.is_file()]


def find_pg_dump() -> str | None:
    configured = os.getenv("PG_DUMP_PATH")
    if configured and Path(configured).exists():
        return configured

    for candidate in (
        r"C:\PostgreSQL\18\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
    ):
        if Path(candidate).exists():
            return candidate

    return shutil.which("pg_dump")


def create_scheduled_backup() -> Path:
    """Create a PostgreSQL plain-SQL backup for the D.6 scheduler."""
    config = db_config()
    pg_dump = find_pg_dump()
    if not config["password"] or not pg_dump:
        raise RuntimeError("Database password or pg_dump is not configured")
    database_name = secure_filename(str(config["dbname"])) or "maize_detector"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{database_name}_{timestamp}.sql"
    command = [
        pg_dump,
        "-h", str(config["host"]),
        "-p", str(config["port"]),
        "-U", str(config["user"]),
        "-d", str(config["dbname"]),
        "-F", "p",
        "-f", str(backup_path),
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = str(config["password"])
    completed = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=90, check=False
    )
    if completed.returncode != 0:
        backup_path.unlink(missing_ok=True)
        raise RuntimeError((completed.stderr or completed.stdout or "pg_dump failed").strip())
    try:
        with db_connection() as conn:
            log_action(conn, "backup_created", backup_path.name, None)
    except Exception:
        pass
    return backup_path


def start_backup_scheduler() -> None:
    """Start one daemon that creates regular backups while the API is running."""
    global _backup_scheduler_started
    if _backup_scheduler_started:
        return
    _backup_scheduler_started = True
    interval_hours = max(1, int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24")))

    def worker():
        while True:
            time.sleep(interval_hours * 3600)
            try:
                create_scheduled_backup()
            except Exception as exc:
                app.logger.error("Scheduled backup failed: %s", exc)

    threading.Thread(target=worker, name="maize-backup-scheduler", daemon=True).start()


def normalize_detection_row(row: dict[str, Any]) -> dict[str, Any]:
    count = row.get("tassel_count", row.get("count", 0))
    confidence = row.get("confidence_score", row.get("confidence", 0))
    image_path = row.get("image_path")
    return {
        "result_id": row.get("result_id"),
        "image_id": row.get("image_id"),
        "image_name": row.get("image_name"),
        "image_path": image_path,
        "original_image_path": image_path,
        "tassel_count": count,
        "count": count,
        "confidence_score": confidence,
        "confidence": confidence,
        "processing_time": row.get("processing_time"),
        "annotated_image_path": row.get("annotated_image_path"),
        "bbox_data": row.get("bbox_data"),
        "created_at": row.get("created_at"),
        "field_name": row.get("field_name"),
        "quality_status": row.get("quality_status", "unreviewed"),
        "review_note": row.get("review_note"),
        "status": "success",
        "source": "database",
    }


def latest_detection_for_image(conn, image_id: int) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                dr.result_id,
                dr.image_id,
                i.image_name,
                i.image_path,
                dr.tassel_count,
                dr.confidence_score,
                dr.processing_time,
                dr.annotated_image_path,
                dr.bbox_data,
                dr.quality_status,
                dr.review_note,
                f.field_name,
                dr.created_at
            FROM detection_results dr
            JOIN images i ON i.image_id = dr.image_id
            LEFT JOIN fields f ON f.field_id = i.field_id
            WHERE dr.image_id = %s
            ORDER BY dr.created_at DESC, dr.result_id DESC
            LIMIT 1
            """,
            (image_id,),
        )
        row = cur.fetchone()
    return normalize_detection_row(row) if row else None


def create_image_record(conn, image_name: str, file_size: int | None = None, user_id: int | None = None) -> int:
    user_id = user_id or 1
    image_path = f"uploads/{image_name}"
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO images (user_id, image_name, image_path, status, file_size, access_level)
            VALUES (%s, %s, %s, 'processing', %s, 'private')
            RETURNING image_id
            """,
            (user_id, image_name, image_path, file_size),
        )
        return cur.fetchone()["image_id"]


def store_image_blob(
    conn,
    image_id: int,
    file_type: str,
    file_name: str,
    mime_type: str,
    encrypted_data: bytes,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO image_files (
                image_id, file_type, file_name, mime_type, file_size,
                image_data, encrypted
            )
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (image_id, file_type) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                mime_type = EXCLUDED.mime_type,
                file_size = EXCLUDED.file_size,
                image_data = EXCLUDED.image_data,
                encrypted = TRUE,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                image_id,
                file_type,
                file_name,
                mime_type,
                len(encrypted_data),
                encrypted_data,
            ),
        )


def detection_for_result(conn, result_id: int) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                dr.result_id,
                dr.image_id,
                i.image_name,
                i.image_path,
                dr.tassel_count,
                dr.confidence_score,
                dr.processing_time,
                dr.annotated_image_path,
                dr.bbox_data,
                dr.quality_status,
                dr.review_note,
                f.field_name,
                dr.created_at
            FROM detection_results dr
            JOIN images i ON i.image_id = dr.image_id
            LEFT JOIN fields f ON f.field_id = i.field_id
            WHERE dr.result_id = %s
            LIMIT 1
            """,
            (result_id,),
        )
        row = cur.fetchone()
    return normalize_detection_row(row) if row else None


# Shared secure file compatibility route (A.4, D.2).
@app.route("/", methods=["GET"])
def frontend_entry():
    """Use one origin for the installable PWA and API in HTTPS deployments."""
    return redirect("/frontend/pages/login.html")


@app.route("/frontend/<path:filename>", methods=["GET"])
def frontend_asset(filename):
    """Serve only the versioned frontend tree; API and uploads stay separate."""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/favicon.ico", methods=["GET"])
def frontend_favicon():
    return send_from_directory(
        FRONTEND_DIR / "icons",
        "maize-icon-192.png",
        mimetype="image/png",
    )


@app.route("/uploads/<path:filename>", methods=["GET"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def uploaded_file(filename: str):
    try:
        if request.auth_user["role"] in {"Farmer", "Agronomist"}:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT user_id FROM images WHERE image_name = %s ORDER BY image_id DESC LIMIT 1",
                        (Path(filename).name,),
                    )
                    image = cur.fetchone()
                if not image:
                    return fail("Image not found", 404)
                if request.auth_user["role"] == "Agronomist":
                    return fail("Agronomists can access aggregated field data only", 403)
                if image["user_id"] != request.auth_user["user_id"]:
                    return fail("You can only access your own images", 403)
        data = secure_read_bytes(filename)
        mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        return Response(data, mimetype=mime)
    except FileNotFoundError:
        return fail("Image not found", 404)


# Shared service health route (D.3, E.4).
@app.route("/api/health", methods=["GET"])
def health():
    ready, error = db_ready()
    disease_health = {
        "available": False,
        "status": "unavailable",
        "model_version": None,
        "deployment_ready": False,
        "error": "Disease inference module could not be imported",
    }
    if get_disease_predictor is not None:
        try:
            disease_health = get_disease_predictor().health()
        except Exception as exc:
            disease_health["error"] = str(exc)
    payload = {
        "status": "ok" if ready else "degraded",
        "service": "Maize Detector API",
        "version": "1.1.0",
        "database": "connected" if ready else "unavailable",
        "database_error": error if not ready else None,
        "disease_model": disease_health,
    }
    return ok(payload, 200 if ready else 503)


# Shared authentication control (A.7, A.8, D.1, D.5).
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Authenticate user and return role info. BCE A.7 (access), D.1 (user mgmt)."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    password = (payload.get("password") or "").strip()

    if not email or not password:
        return fail("Email and password are required", 400)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT u.user_id, u.name, u.email, u.password_hash, u.status, u.permissions,
                           r.role_name AS role
                    FROM users u
                    JOIN roles r ON r.role_id = u.role_id
                    WHERE u.email = %s
                    """,
                    (email,),
                )
                user = cur.fetchone()

        if not user:
            return fail("Invalid email or password", 401)

        if user["status"] == "disabled":
            return fail("Account is disabled. Contact administrator.", 403)

        stored_hash = user["password_hash"]
        if not verify_password(stored_hash, password):
            return fail("Invalid email or password", 401)

        session_user = {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"],
            "permissions": permissions_for(user),
        }
        return ok({
            "status": "success",
            "message": "Login successful",
            "user": session_user,
            "access_token": issue_access_token(session_user),
            "expires_in": TOKEN_MAX_AGE_SECONDS,
        })
    except Exception as exc:
        return db_error_response(exc, 503)


# Shared account registration control (A.8, D.1).
@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """Create a Farmer account in PostgreSQL."""
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    if not name:
        return fail("Name is required", 400)
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return fail("A valid email address is required", 400)
    if len(password) < 6:
        return fail("Password must be at least 6 characters", 400)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("Farmer",))
                role = cur.fetchone()
                if not role:
                    return fail("Farmer role is not configured", 500)
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role_id, status)
                    VALUES (%s, %s, %s, %s, 'active')
                    RETURNING user_id
                    """,
                    (name, email, hash_password(password), role["role_id"]),
                )
                user_id = cur.fetchone()["user_id"]
            user = fetch_user(conn, user_id)
        return ok({
            "status": "success",
            "message": "Account created",
            "user": user,
            "access_token": issue_access_token(user),
            "expires_in": TOKEN_MAX_AGE_SECONDS,
            "source": "database",
        }, 201)
    except Exception as exc:
        msg = str(exc).lower()
        if "users_email_key" in msg or "duplicate key" in msg or "unique" in msg:
            return fail("Email already exists", 409)
        return db_error_response(exc)


# USER STORY A.8 - Validate the signed session used by the interface.
@app.route("/api/auth/me", methods=["GET"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def auth_me():
    """Validate the signed session and return the current BCE User entity."""
    try:
        with db_connection() as conn:
            user = fetch_user(conn, int(request.auth_user["user_id"]))
        if not user or user.get("status") != "active":
            return fail("Account is unavailable", 401)
        user["permissions"] = request.auth_user.get("permissions", [])
        return ok({"user": user, "permissions": user["permissions"]})
    except Exception as exc:
        return db_error_response(exc, 503)


@app.route("/api/auth/profile", methods=["PATCH"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def auth_update_profile():
    """Update the signed-in user's name/email after password verification."""
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    current_password = str(payload.get("current_password") or payload.get("currentPassword") or "")

    if not name:
        return fail("Name is required", 400)
    if len(name) > 100:
        return fail("Name must be 100 characters or fewer", 400)
    if len(email) > 150 or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return fail("A valid email address is required", 400)
    if not current_password:
        return fail("Current password is required", 400)

    user_id = int(request.auth_user["user_id"])
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password_hash FROM users WHERE user_id = %s AND status = 'active'",
                    (user_id,),
                )
                current_user = cur.fetchone()
                if not current_user or not verify_password(current_user["password_hash"], current_password):
                    return fail("Current password is incorrect", 401)

                cur.execute(
                    "SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s) AND user_id <> %s",
                    (email, user_id),
                )
                if cur.fetchone():
                    return fail("Email already exists", 409)

                cur.execute(
                    "UPDATE users SET name = %s, email = %s WHERE user_id = %s",
                    (name, email, user_id),
                )
            user = fetch_user(conn, user_id)

        if not user:
            return fail("User not found", 404)
        user["permissions"] = request.auth_user.get("permissions", [])
        return ok({
            "status": "success",
            "message": "Profile updated",
            "user": user,
            "access_token": issue_access_token(user),
            "expires_in": TOKEN_MAX_AGE_SECONDS,
        })
    except Exception as exc:
        message = str(exc).lower()
        if "users_email_key" in message or "duplicate key" in message or "unique" in message:
            return fail("Email already exists", 409)
        return db_error_response(exc)


@app.route("/api/auth/change-password", methods=["POST"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def auth_change_password():
    """Change the signed-in user's password after verifying the current password."""
    payload = request.get_json(silent=True) or {}
    current_password = str(payload.get("current_password") or payload.get("currentPassword") or "")
    new_password = str(payload.get("new_password") or payload.get("newPassword") or "")
    confirm_password = str(payload.get("confirm_password") or payload.get("confirmPassword") or "")

    if not current_password:
        return fail("Current password is required", 400)
    if len(new_password) < 6:
        return fail("New password must be at least 6 characters", 400)
    if len(new_password) > 128:
        return fail("New password must be 128 characters or fewer", 400)
    if new_password != confirm_password:
        return fail("New passwords do not match", 400)

    user_id = int(request.auth_user["user_id"])
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password_hash FROM users WHERE user_id = %s AND status = 'active'",
                    (user_id,),
                )
                current_user = cur.fetchone()
                if not current_user or not verify_password(current_user["password_hash"], current_password):
                    return fail("Current password is incorrect", 401)
                if verify_password(current_user["password_hash"], new_password):
                    return fail("New password must be different from the current password", 400)
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE user_id = %s",
                    (hash_password(new_password), user_id),
                )
        return ok({
            "status": "success",
            "message": "Password changed. Please sign in again with your new password.",
        })
    except Exception as exc:
        return db_error_response(exc)


# USER STORIES A.1, A.5, A.7 - Upload one validated image per request.
@app.route("/api/upload", methods=["POST"])
@require_roles("Farmer", "Admin", permission="images:upload")
def upload():
    file = request.files.get("image") or request.files.get("file")
    payload = request.get_json(silent=True) or {}
    user_id = request.auth_user["user_id"]

    if file:
        original_name = file.filename or "uploaded_maize_image.jpg"
        validation_error = validate_image_upload(original_name, file.content_type)
        if validation_error:
            return fail(validation_error, 400)

        image_name = clean_image_filename(original_name)
        raw_image = file.read()
        if not raw_image:
            return fail("Image file is empty", 400)
        file_size = len(raw_image)
        stored_path = secure_store_bytes(image_name, raw_image)
    else:
        image_name = payload.get("image_name") or payload.get("imageName") or "uploaded_maize_image.jpg"
        validation_error = validate_image_upload(image_name)
        if validation_error:
            return fail(validation_error, 400)

        image_name = clean_image_filename(image_name)
        file_size = payload.get("file_size")

    try:
        with db_connection() as conn:
            image_id = create_image_record(conn, image_name=image_name, file_size=file_size, user_id=int(user_id))
            if file:
                store_image_blob(
                    conn,
                    image_id,
                    "original",
                    image_name,
                    file.content_type or "image/jpeg",
                    stored_path.read_bytes(),
                )
                log_action(
                    conn,
                    "secure_image_upload",
                    f"Encrypted upload stored for image {image_id}",
                    int(user_id),
                )
        return ok(
            {
                "status": "success",
                "message": "Image uploaded",
                "image_id": image_id,
                "image_name": image_name,
                "source": "database",
            },
            201,
        )
    except Exception as exc:
        return db_error_response(exc)


# USER STORIES A.2, A.6 - Run real YOLO counting in fast or accurate mode.
@app.route("/api/predict", methods=["POST"])
@require_roles("Farmer", "Researcher", "Admin")
def predict():
    payload = request.get_json(silent=True) or {}
    image_id = payload.get("image_id") or payload.get("imageId")
    if not image_id:
        return fail("image_id is required; upload the image before prediction", 400)
    try:
        image_id = int(image_id)
    except (TypeError, ValueError):
        return fail("image_id must be an integer", 400)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT image_name, user_id FROM images WHERE image_id = %s",
                    (image_id,),
                )
                image = cur.fetchone()
        if not image:
            return fail("Uploaded image not found", 404)
        if (
            request.auth_user["role"] == "Farmer"
            and image["user_id"] != request.auth_user["user_id"]
        ):
            return fail("You can only analyse your own images", 403)
        image_name = image["image_name"]
    except Exception as exc:
        return db_error_response(exc)
    inference_mode = payload.get("mode") or (
        "accurate" if request.auth_user.get("role") == "Researcher" else "fast"
    )
    if inference_mode not in {"fast", "accurate"}:
        return fail("mode must be fast or accurate", 400)

    # ── 1. Try real YOLO inference if model is available ──
    predictor = None
    if get_predictor is not None:
        try:
            predictor = get_predictor()
        except Exception as exc:
            app.logger.exception("Could not initialize the inference runtime")
            return fail("Inference runtime is unavailable", 503, model_error=str(exc))

    if predictor is None or not predictor.available:
        return fail("The trained model is unavailable", 503)

    if predictor is not None and predictor.available and image_name:
        # Resolve image path: try exact name, basename, then cleaned version
        try:
            with materialized_image(Path(image_name).name) as image_path:
                ai_result = predictor.detect(str(image_path), mode=inference_mode)
                # Save detection to database
                try:
                    with db_connection() as conn:
                        if not image_id:
                            image_id = create_image_record(
                                conn,
                                image_name=image_name,
                                file_size=payload.get("file_size"),
                            )
                        bbox_json = json.dumps(ai_result["bbox_data"], ensure_ascii=False)
                        with conn.cursor() as cur:
                            cur.execute("UPDATE images SET status = 'completed' WHERE image_id = %s", (image_id,))
                            cur.execute(
                                """
                                INSERT INTO detection_results
                                    (image_id, tassel_count, confidence_score, processing_time, bbox_data, annotated_image_path)
                                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                                RETURNING result_id
                                """,
                                (
                                    image_id,
                                    ai_result["tassel_count"],
                                    ai_result["confidence_score"],
                                    ai_result["processing_time"],
                                    bbox_json,
                                    f"uploads/annotated_{image_id}.jpg",
                                ),
                            )
                            ai_result["result_id"] = cur.fetchone()["result_id"]
                        conn.commit()
                except Exception as db_err:
                    app.logger.exception("Inference succeeded but result persistence failed")
                    return fail("Detection result could not be saved", 500, database_error=str(db_err))

                return ok({
                    "result_id": ai_result["result_id"],
                    "image_id": image_id,
                    "image_name": image_name,
                    "image_path": f"uploads/{image_name}",
                    "original_image_path": f"uploads/{image_name}",
                    "tassel_count": ai_result["tassel_count"],
                    "count": ai_result["tassel_count"],
                    "confidence_score": ai_result["confidence_score"],
                    "confidence": ai_result["confidence_score"],
                    "processing_time": ai_result["processing_time"],
                    "bbox_data": ai_result["bbox_data"],
                    "inference_mode": ai_result.get("inference_mode", inference_mode),
                    "cache_hit": ai_result.get("cache_hit", False),
                    "created_at": datetime.now().isoformat(),
                    "source": "yolo-inference",
                }, 201)
        except (FileNotFoundError, RuntimeError) as inferr:
            app.logger.exception("Inference image or runtime unavailable")
            return fail("Model inference failed", 500, model_error=str(inferr))
        except Exception as inferr:
            app.logger.exception("Real inference failed")
            return fail("Model inference failed", 500, model_error=str(inferr))

    return fail("Model inference did not produce a result", 500)


# USER STORIES B.2, B.3 - Read exportable and filterable detection history.
@app.route("/api/history", methods=["GET"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def history():
    try:
        limit = min(int(request.args.get("limit", 100)), 200)
    except (ValueError, TypeError):
        limit = 100
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                filters = []
                params: list[Any] = []
                if request.auth_user["role"] == "Farmer":
                    filters.append("i.user_id = %s")
                    params.append(request.auth_user["user_id"])
                if request.args.get("from"):
                    filters.append("dr.created_at::date >= %s")
                    params.append(request.args["from"])
                if request.args.get("to"):
                    filters.append("dr.created_at::date <= %s")
                    params.append(request.args["to"])
                if request.args.get("field"):
                    filters.append("LOWER(COALESCE(f.field_name, '')) LIKE %s")
                    params.append(f"%{request.args['field'].lower()}%")
                where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
                order_by = {
                    "count": "dr.tassel_count DESC",
                    "confidence": "dr.confidence_score DESC NULLS LAST",
                }.get(
                    request.args.get("sort", "date"),
                    "dr.created_at DESC, dr.result_id DESC",
                )
                params.append(limit)
                cur.execute(
                    f"""
                    SELECT
                        dr.result_id,
                        dr.image_id,
                        i.image_name,
                        i.image_path,
                        dr.tassel_count,
                        dr.confidence_score,
                        dr.processing_time,
                        dr.annotated_image_path,
                        dr.bbox_data,
                        dr.quality_status,
                        dr.review_note,
                        f.field_name,
                        dr.created_at
                    FROM detection_results dr
                    JOIN images i ON i.image_id = dr.image_id
                    LEFT JOIN fields f ON f.field_id = i.field_id
                    {where_clause}
                    ORDER BY {order_by}
                    LIMIT %s
                    """,
                    params,
                )
                records = [normalize_detection_row(row) for row in cur.fetchall()]
        return ok({"records": records, "total": len(records), "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORIES A.3, A.4 - Return count, confidence, timing, and bbox data.
@app.route("/api/results/<int:result_id>", methods=["GET"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def result_detail(result_id: int):
    try:
        with db_connection() as conn:
            result = detection_for_result(conn, result_id)
            if result and request.auth_user["role"] == "Farmer":
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM images WHERE image_id = %s AND user_id = %s",
                        (result["image_id"], request.auth_user["user_id"]),
                    )
                    if not cur.fetchone():
                        return fail("You can only view your own results", 403)
        if not result:
            return fail("Detection result not found", 404)
        return ok(result)
    except Exception as exc:
        return db_error_response(exc)


# USER STORY A.8 - Farmer dashboard summary.
@app.route("/api/stats", methods=["GET"])
@require_roles("Farmer", "Researcher", "Admin")
def stats():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                owner_filter = ""
                params: tuple[Any, ...] = ()
                if request.auth_user["role"] == "Farmer":
                    owner_filter = "WHERE i.user_id = %s"
                    params = (request.auth_user["user_id"],)
                cur.execute(
                    f"""
                    SELECT
                        COUNT(DISTINCT i.image_id) AS total_uploaded_images,
                        COALESCE(SUM(dr.tassel_count), 0) AS total_detected_tassels,
                        COALESCE(AVG(dr.tassel_count), 0) AS average_tassel_count
                    FROM images i
                    LEFT JOIN detection_results dr ON dr.image_id = i.image_id
                    {owner_filter}
                    """,
                    params,
                )
                row = cur.fetchone()
        return ok({**row, "model_status": "Active", "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


def report_response(report_type: str):
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM reports
                    WHERE report_type = %s
                    ORDER BY report_date DESC, report_id DESC
                    LIMIT 1
                    """,
                    (report_type,),
                )
                report = cur.fetchone()
        if not report:
            return fail(f"No {report_type} report is available", 404)

        payload = {
            "report_id": report["report_id"],
            "report_type": report["report_type"],
            "report_date": report["report_date"],
            "total_uploads": report["total_uploads"],
            "successful_detections": report["successful_detections"],
            "failed_detections": report["failed_detections"],
            "average_tassel_count": report["average_tassel_count"],
            "chart_data": report["chart_data"],
            "created_at": report["created_at"],
            "system_status": "Normal",
            "source": "database",
        }

        if report_type == "daily":
            payload["date"] = report["report_date"]
        elif report_type == "weekly":
            end = report["report_date"]
            start = end - timedelta(days=6)
            payload["week"] = f"{start.isoformat()} to {end.isoformat()}"
            payload["most_active_day"] = "Friday"
            payload["average_processing_time"] = 2.8
        else:
            payload["month"] = report["report_date"].strftime("%B %Y")
            payload["model_accuracy_estimate"] = 0.88

        return ok(payload)
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/report/daily", methods=["GET"])
@require_roles("Researcher", "Admin")
def report_daily():
    return report_response("daily")


@app.route("/api/report/weekly", methods=["GET"])
@require_roles("Researcher", "Admin")
def report_weekly():
    return report_response("weekly")


@app.route("/api/report/monthly", methods=["GET"])
@require_roles("Researcher", "Admin")
def report_monthly():
    return report_response("monthly")


# USER STORY B.6 - Generate and persist a visual report.
@app.route("/api/reports", methods=["POST"])
@require_roles("Researcher", "Admin")
def generate_report():
    """G.6: select fields/date range, aggregate detections, and save Report."""
    payload = request.get_json(silent=True) or {}
    date_from = str(payload.get("date_from") or "").strip()
    date_to = str(payload.get("date_to") or "").strip()
    field_ids = payload.get("field_ids") or []
    report_type = payload.get("report_type", "weekly")
    if report_type not in {"daily", "weekly", "monthly"}:
        return fail("report_type must be daily, weekly, or monthly", 400)
    try:
        start_date = date.fromisoformat(date_from)
        end_date = date.fromisoformat(date_to)
    except ValueError:
        return fail("date_from and date_to must use YYYY-MM-DD", 400)
    if start_date > end_date:
        return fail("date_from cannot be after date_to", 400)
    if not isinstance(field_ids, list):
        return fail("field_ids must be an array", 400)

    try:
        with db_connection() as conn:
            filters = ["dr.created_at::date BETWEEN %s AND %s"]
            params: list[Any] = [start_date, end_date]
            if field_ids:
                filters.append("i.field_id = ANY(%s)")
                params.append([int(item) for item in field_ids])
            where_clause = " AND ".join(filters)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        dr.created_at::date AS day,
                        COUNT(*) AS detections,
                        COALESCE(AVG(dr.tassel_count), 0) AS average_count
                    FROM detection_results dr
                    JOIN images i ON i.image_id = dr.image_id
                    WHERE {where_clause}
                    GROUP BY dr.created_at::date
                    ORDER BY day
                    """,
                    params,
                )
                daily = cur.fetchall()
            total = sum(int(row["detections"]) for row in daily)
            weighted_count = sum(
                float(row["average_count"]) * int(row["detections"]) for row in daily
            )
            average = round(weighted_count / total, 2) if total else 0
            chart_data = {
                "labels": [row["day"].isoformat() for row in daily],
                "values": [int(row["detections"]) for row in daily],
                "average_counts": [float(row["average_count"]) for row in daily],
                "field_ids": [int(item) for item in field_ids],
                "date_from": start_date.isoformat(),
                "date_to": end_date.isoformat(),
                "summary": (
                    f"{total} detection records were analysed from "
                    f"{start_date.isoformat()} to {end_date.isoformat()}; "
                    f"the average tassel count was {average:.2f}."
                ),
            }
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO reports (
                        report_type, report_date, total_uploads,
                        successful_detections, failed_detections,
                        average_tassel_count, chart_data
                    ) VALUES (%s, %s, %s, %s, 0, %s, %s::jsonb)
                    RETURNING *
                    """,
                    (
                        report_type,
                        end_date,
                        total,
                        total,
                        average,
                        json.dumps(chart_data),
                    ),
                )
                report = cur.fetchone()
            log_action(
                conn,
                "report_generated",
                f"report_id={report['report_id']}, range={start_date}:{end_date}",
                request.auth_user["user_id"],
            )
        return ok({"status": "success", "report": report, "chart_data": chart_data}, 201)
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.1 - User collection management.
@app.route("/api/users", methods=["GET", "POST", "PUT", "DELETE"])
@require_roles("Admin")
def users():
    if request.method in {"PUT", "DELETE"}:
        payload = request.get_json(silent=True) or {}
        user_id = payload.get("user_id") or payload.get("userId") or request.args.get("user_id") or request.args.get("userId")
        if not user_id:
            return fail("user_id is required", 400)
        try:
            return user_detail(int(user_id))
        except ValueError:
            return fail("user_id must be an integer", 400)

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        validation_error = validate_user_payload(payload, creating=True)
        if validation_error:
            return fail(validation_error, 400)

        try:
            with db_connection() as conn:
                role_id = resolve_role_id(conn, payload, required=True)
                password_hash = payload.get("password_hash") or payload.get("passwordHash")
                if not password_hash:
                    password_hash = hash_password(str(payload["password"]))

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO users (name, email, password_hash, role_id, status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING user_id
                        """,
                        (
                            str(payload["name"]).strip(),
                            str(payload["email"]).strip(),
                            password_hash,
                            role_id,
                            payload.get("status", "active"),
                        ),
                    )
                    user_id = cur.fetchone()["user_id"]

                user = fetch_user(conn, user_id)
            return ok({"status": "success", "message": "User created", "user": user, "source": "database"}, 201)
        except ValueError as exc:
            return fail(str(exc), 400)
        except Exception as exc:
            return db_error_response(exc)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT u.user_id, u.name, u.email, u.role_id, r.role_name AS role, u.status, u.created_at
                    FROM users u
                    JOIN roles r ON r.role_id = u.role_id
                    ORDER BY u.user_id
                    """
                )
                rows = [normalize_user_row(row) for row in cur.fetchall()]
        return ok({"users": rows, "total": len(rows), "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.1 - Individual user management.
@app.route("/api/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
@require_roles("Admin")
def user_detail(user_id: int):
    if request.method == "GET":
        try:
            with db_connection() as conn:
                user = fetch_user(conn, user_id)
            if not user:
                return fail("User not found", 404)
            return ok({"user": user, "source": "database"})
        except Exception as exc:
            return db_error_response(exc)

    if request.method == "PUT":
        payload = request.get_json(silent=True) or {}
        validation_error = validate_user_payload(payload)
        if validation_error:
            return fail(validation_error, 400)

        try:
            with db_connection() as conn:
                if not fetch_user(conn, user_id):
                    return fail("User not found", 404)

                updates = []
                params: list[Any] = []

                if "name" in payload:
                    if not payload.get("name"):
                        return fail("name cannot be empty", 400)
                    updates.append("name = %s")
                    params.append(str(payload["name"]).strip())

                if "email" in payload:
                    if not payload.get("email"):
                        return fail("email cannot be empty", 400)
                    updates.append("email = %s")
                    params.append(str(payload["email"]).strip())

                role_id = resolve_role_id(conn, payload, required=False)
                if role_id is not None:
                    if user_id == request.auth_user["user_id"]:
                        with conn.cursor() as cur:
                            cur.execute(
                                "SELECT role_name FROM roles WHERE role_id = %s",
                                (role_id,),
                            )
                            requested_role = cur.fetchone()
                        if not requested_role or requested_role["role_name"] != "Admin":
                            return fail("Administrators cannot remove their own admin role", 400)
                    updates.append("role_id = %s")
                    params.append(role_id)

                if "status" in payload:
                    updates.append("status = %s")
                    params.append(payload["status"])

                password_hash = payload.get("password_hash") or payload.get("passwordHash")
                if payload.get("password"):
                    password_hash = hash_password(str(payload["password"]))
                if password_hash:
                    updates.append("password_hash = %s")
                    params.append(password_hash)

                if not updates:
                    return fail("No user fields provided to update", 400)

                params.append(user_id)
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s", params)

                user = fetch_user(conn, user_id)
            return ok({"status": "success", "message": "User updated", "user": user, "source": "database"})
        except ValueError as exc:
            return fail(str(exc), 400)
        except Exception as exc:
            return db_error_response(exc)

    try:
        with db_connection() as conn:
            user = fetch_user(conn, user_id)
            if not user:
                return fail("User not found", 404)

            with conn.cursor() as cur:
                cur.execute("UPDATE users SET status = 'disabled' WHERE user_id = %s", (user_id,))

            user = fetch_user(conn, user_id)
        return ok(
            {
                "status": "success",
                "message": "User disabled",
                "delete_mode": "soft",
                "user": user,
                "source": "database",
            }
        )
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.1 - Enable or disable a user.
@app.route("/api/users/<int:user_id>/status", methods=["PUT"])
@require_roles("Admin")
def user_status(user_id: int):
    """Toggle user status (active/disabled) — D.1 admin requirement."""
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")
    if new_status not in VALID_USER_STATUSES:
        return fail(f"status must be one of: {', '.join(sorted(VALID_USER_STATUSES))}", 400)

    try:
        with db_connection() as conn:
            user = fetch_user(conn, user_id)
            if not user:
                return fail("User not found", 404)
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET status = %s WHERE user_id = %s", (new_status, user_id))
            user = fetch_user(conn, user_id)
        return ok({"status": "success", "message": f"User {new_status}", "user": user, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.5 - Read and update a user's permissions.
@app.route("/api/users/<int:user_id>/permissions", methods=["GET", "PUT"])
@require_roles("Admin")
def user_permissions(user_id: int):
    try:
        with db_connection() as conn:
            if request.method == "GET":
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT u.user_id, u.name, r.role_name AS role, u.permissions
                        FROM users u JOIN roles r ON r.role_id = u.role_id
                        WHERE u.user_id = %s
                        """,
                        (user_id,),
                    )
                    user = cur.fetchone()
                if not user:
                    return fail("User not found", 404)
                return ok({
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "role": user["role"],
                    "permissions": permissions_for(user),
                    "source": "database",
                })

            payload = request.get_json(silent=True) or {}
            permissions = payload.get("permissions")
            if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
                return fail("permissions must be an array of strings", 400)
            if request.auth_user["user_id"] == user_id and "*" not in permissions:
                return fail("Administrators cannot remove their own full access", 400)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET permissions = %s::jsonb WHERE user_id = %s RETURNING user_id",
                    (json.dumps(permissions), user_id),
                )
                if not cur.fetchone():
                    return fail("User not found", 404)
            log_action(conn, "permissions_updated", f"Updated permissions for user {user_id}", request.auth_user["user_id"])
        return ok({"status": "success", "user_id": user_id, "permissions": permissions})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.2 - Configure secure image access policies.
@app.route("/api/access-policies", methods=["GET", "PUT"])
@require_roles("Admin")
def access_policies():
    try:
        with db_connection() as conn:
            if request.method == "GET":
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM access_policies ORDER BY role_name")
                    policies = cur.fetchall()
                return ok({"policies": policies, "source": "database"})

            payload = request.get_json(silent=True) or {}
            role_name = payload.get("role_name")
            access_level = payload.get("access_level")
            if role_name not in ROLE_PERMISSIONS or not access_level:
                return fail("A valid role_name and access_level are required", 400)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO access_policies (role_name, access_level, updated_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (role_name) DO UPDATE SET
                        access_level = EXCLUDED.access_level,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (role_name, access_level, request.auth_user["user_id"]),
                )
                policy = cur.fetchone()
                cur.execute(
                    """
                    UPDATE images i
                    SET access_level = %s
                    FROM users u
                    JOIN roles r ON r.role_id = u.role_id
                    WHERE i.user_id = u.user_id AND r.role_name = %s
                    """,
                    (access_level, role_name),
                )
            log_action(conn, "access_policy", f"{role_name}={access_level}", request.auth_user["user_id"])
        return ok({"status": "success", "policy": policy})
    except Exception as exc:
        return db_error_response(exc)


# USER STORIES B.5, D.4 - List datasets or create dataset metadata.
@app.route("/api/datasets", methods=["GET", "POST"])
@require_roles("Researcher", "Admin")
def datasets():
    if request.method == "POST" and request.auth_user["role"] != "Admin":
        return fail("Only administrators can create datasets", 403)
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        name = payload.get("dataset_name") or payload.get("datasetName")
        if not name:
            return fail("dataset_name is required", 400)
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO datasets (dataset_name, dataset_path, total_images, annotation_status, annotation_format) "
                        "VALUES (%s, %s, %s, %s, %s) RETURNING dataset_id",
                        (str(name).strip(),
                         payload.get("dataset_path", ""),
                         int(payload.get("total_images", 0)),
                         payload.get("annotation_status", "not_started"),
                         payload.get("annotation_format")),
                    )
                    ds_id = cur.fetchone()["dataset_id"]
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM datasets WHERE dataset_id = %s", (ds_id,))
                    ds = cur.fetchone()
            return ok({"status": "success", "message": "Dataset created", "dataset": ds, "source": "database"}, 201)
        except Exception as exc:
            return db_error_response(exc)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM datasets ORDER BY dataset_id")
                rows = cur.fetchall()
        return ok({"datasets": rows, "total": len(rows), "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.4 - Update or delete a dataset.
@app.route("/api/datasets/<int:dataset_id>", methods=["PUT", "DELETE"])
@require_roles("Admin")
def dataset_detail(dataset_id: int):
    if request.method == "DELETE":
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM datasets WHERE dataset_id = %s", (dataset_id,))
            return ok({"status": "success", "message": "Dataset deleted", "source": "database"})
        except Exception as exc:
            return db_error_response(exc)

    payload = request.get_json(silent=True) or {}
    try:
        with db_connection() as conn:
            updates, params = [], []
            for col in ["dataset_name", "annotation_status", "annotation_format"]:
                if col in payload and payload[col] is not None:
                    updates.append(f"{col} = %s")
                    params.append(str(payload[col]).strip() if col == "dataset_name" else payload[col])
            if "total_images" in payload:
                updates.append("total_images = %s")
                params.append(int(payload["total_images"]))
            if not updates:
                return fail("No fields provided to update", 400)
            params.append(dataset_id)
            with conn.cursor() as cur:
                cur.execute(f"UPDATE datasets SET {', '.join(updates)} WHERE dataset_id = %s", params)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM datasets WHERE dataset_id = %s", (dataset_id,))
                ds = cur.fetchone()
        return ok({"status": "success", "message": "Dataset updated", "dataset": ds, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.4 - Upload a managed dataset package.
@app.route("/api/datasets/upload", methods=["POST"])
@require_roles("Admin")
def dataset_upload():
    file = request.files.get("dataset")
    name = str(request.form.get("dataset_name") or "").strip()
    if not file or not name:
        return fail("dataset file and dataset_name are required", 400)
    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".zip", ".tar", ".gz"}:
        return fail("Dataset package must be ZIP, TAR, or GZ", 400)
    datasets_dir = Path(__file__).resolve().parents[1] / "datasets" / "packages"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file.filename) or f"dataset-{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    target = datasets_dir / filename
    file.save(target)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO datasets (
                        dataset_name, dataset_path, total_images,
                        annotation_status, annotation_format
                    ) VALUES (%s, %s, %s, %s, %s) RETURNING *
                    """,
                    (
                        name,
                        str(target.relative_to(Path(__file__).resolve().parents[1])),
                        int(request.form.get("total_images") or 0),
                        request.form.get("annotation_status") or "not_started",
                        request.form.get("annotation_format") or None,
                    ),
                )
                dataset = cur.fetchone()
            log_action(conn, "dataset_upload", filename, request.auth_user["user_id"])
        return ok({"status": "success", "dataset": dataset}, 201)
    except Exception as exc:
        if target.exists():
            target.unlink()
        return db_error_response(exc)


# USER STORY B.5 - Download a dataset as ZIP or TAR.GZ.
@app.route("/api/datasets/<int:dataset_id>/download", methods=["GET"])
@require_roles("Researcher", "Admin", permission="datasets:download")
def dataset_download(dataset_id: int):
    archive_format = request.args.get("format", "zip").lower()
    if archive_format not in {"zip", "tar", "tar.gz", "tgz"}:
        return fail("format must be zip or tar", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM datasets WHERE dataset_id = %s", (dataset_id,))
                dataset = cur.fetchone()
        if not dataset:
            return fail("Dataset not found", 404)
    except Exception as exc:
        return db_error_response(exc)

    requested = Path(str(dataset.get("dataset_path") or ""))
    project_root = Path(__file__).resolve().parents[1]
    source = requested if requested.is_absolute() else project_root / requested
    memory = tempfile.SpooledTemporaryFile(max_size=20 * 1024 * 1024)
    manifest = json.dumps(jsonable(dataset), indent=2, ensure_ascii=False).encode("utf-8")
    if archive_format == "zip":
        with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("dataset-manifest.json", manifest)
            if source.exists() and source.is_dir():
                for path in source.rglob("*"):
                    if path.is_file() and path.stat().st_size <= 25 * 1024 * 1024:
                        archive.write(path, path.relative_to(source))
            elif source.exists() and source.is_file():
                archive.write(source, source.name)
        mime = "application/zip"
        suffix = "zip"
    else:
        with tarfile.open(fileobj=memory, mode="w:gz") as archive:
            info = tarfile.TarInfo("dataset-manifest.json")
            info.size = len(manifest)
            archive.addfile(info, fileobj=io.BytesIO(manifest))
            if source.exists() and source.is_dir():
                for path in source.rglob("*"):
                    if path.is_file() and path.stat().st_size <= 25 * 1024 * 1024:
                        archive.add(path, arcname=str(path.relative_to(source)))
            elif source.exists() and source.is_file():
                archive.add(source, arcname=source.name)
        mime = "application/gzip"
        suffix = "tar.gz"
    memory.seek(0)
    filename = secure_filename(str(dataset["dataset_name"])) or f"dataset-{dataset_id}"
    return Response(
        memory.read(),
        mimetype=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{suffix}"'},
    )


# USER STORY E.5 - List or register versioned model updates.
@app.route("/api/models", methods=["GET", "POST"])
@require_roles("Researcher", "Admin")
def models():
    if request.method == "POST" and request.auth_user["role"] != "Admin":
        return fail("Only administrators can register models", 403)
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        required = ("model_name", "model_version", "weights_path")
        if any(not payload.get(field) for field in required):
            return fail("model_name, model_version and weights_path are required", 400)
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO models (
                            model_name, model_version, weights_path, status,
                            map50, precision_score, recall_score, iou_threshold,
                            parent_model_id, changelog
                        ) VALUES (%s,%s,%s,'registered',%s,%s,%s,%s,%s,%s)
                        RETURNING *
                        """,
                        (
                            payload["model_name"],
                            payload["model_version"],
                            payload["weights_path"],
                            payload.get("map50"),
                            payload.get("precision"),
                            payload.get("recall"),
                            payload.get("iou_threshold", 0.5),
                            payload.get("parent_model_id"),
                            payload.get("changelog"),
                        ),
                    )
                    model = normalize_model_row(cur.fetchone())
                log_action(conn, "model_registered", payload["model_version"], request.auth_user["user_id"])
            return ok({"status": "success", "model": model}, 201)
        except Exception as exc:
            return db_error_response(exc)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM models ORDER BY created_at DESC, model_id DESC")
                rows = [normalize_model_row(row) for row in cur.fetchall()]
        return ok({"models": rows, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY B.4 - Compare two registered models.
@app.route("/api/models/compare", methods=["POST"])
@require_roles("Researcher", "Admin", permission="models:compare")
def compare_models():
    payload = request.get_json(silent=True) or {}
    model_ids = payload.get("model_ids") or []
    if not isinstance(model_ids, list) or len(model_ids) != 2:
        return fail("Exactly two model_ids are required", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM models WHERE model_id = ANY(%s) ORDER BY model_id",
                    ([int(item) for item in model_ids],),
                )
                selected = [normalize_model_row(row) for row in cur.fetchall()]
    except Exception as exc:
        return db_error_response(exc)
    if len(selected) != 2:
        return fail("Both models must exist", 404)
    dataset_yaml = str(payload.get("dataset_yaml") or "").strip()
    comparison_source = "stored-evaluation"
    if dataset_yaml:
        if evaluate_model is None:
            return fail("Evaluation runtime is unavailable", 503)
        evaluated = []
        for model in selected:
            weights_path = Path(str(model["weights_path"]))
            if not weights_path.is_absolute():
                weights_path = Path(__file__).resolve().parents[1] / weights_path
            if not weights_path.exists():
                return fail(
                    f"Weights are unavailable for {model['model_version']}; "
                    "use stored metrics or register the missing artifact",
                    409,
                )
            metrics_result = evaluate_model(weights_path, dataset_yaml)
            evaluated.append({
                **model,
                "map50": metrics_result["map50"],
                "precision": metrics_result["precision"],
                "recall": metrics_result["recall"],
            })
        selected = evaluated
        comparison_source = "shared-validation-run"
    metrics = ("map50", "precision", "recall")
    winner = max(
        selected,
        key=lambda item: sum(float(item.get(metric) or 0) for metric in metrics),
    )
    return ok({
        "models": selected,
        "winner_model_id": winner["model_id"],
        "dataset_id": payload.get("dataset_id"),
        "comparison_source": comparison_source,
        "basis": (
            "Both models were evaluated against the same validation YAML."
            if comparison_source == "shared-validation-run"
            else "Stored evaluation outputs (mAP, precision, recall) for the selected test dataset."
        ),
    })


# USER STORY E.4 - Health-check and activate a deployable model.
@app.route("/api/models/<int:model_id>/deploy", methods=["POST"])
@require_roles("Admin")
def deploy_model(model_id: int):
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM models WHERE model_id = %s", (model_id,))
                model = cur.fetchone()
                if not model:
                    return fail("Model not found", 404)
                weights_path = Path(str(model["weights_path"]))
                if not weights_path.is_absolute():
                    weights_path = Path(__file__).resolve().parents[1] / weights_path
                if not weights_path.exists():
                    return fail("Model weights file does not exist", 409)
                if activate_predictor is None:
                    return fail("Inference runtime is unavailable", 503)
                try:
                    activate_predictor(weights_path)
                except Exception as exc:
                    return fail("Model warm-up or health check failed", 409, model_error=str(exc))
                cur.execute("UPDATE models SET status = 'archived' WHERE status = 'active'")
                cur.execute(
                    "UPDATE models SET status = 'active', activated_at = CURRENT_TIMESTAMP WHERE model_id = %s",
                    (model_id,),
                )
            log_action(conn, "model_deployed", f"model_id={model_id}", request.auth_user["user_id"])
        return ok({
            "status": "success",
            "message": "Model loaded, health checked, and deployed",
            "model_id": model_id,
            "health_check": "passed",
        })
    except Exception as exc:
        return db_error_response(exc)


# USER STORY E.3 - Evaluate stored metrics or run YOLO validation.
@app.route("/api/models/<int:model_id>/evaluate", methods=["POST"])
@require_roles("Admin", "Researcher")
def evaluate_registered_model(model_id: int):
    payload = request.get_json(silent=True) or {}
    dataset_yaml = str(payload.get("dataset_yaml") or "").strip()
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM models WHERE model_id = %s", (model_id,))
                model = cur.fetchone()
            if not model:
                return fail("Model not found", 404)
            weights_path = Path(str(model["weights_path"]))
            if not weights_path.is_absolute():
                weights_path = Path(__file__).resolve().parents[1] / weights_path
            if dataset_yaml:
                if evaluate_model is None:
                    return fail("Evaluation runtime is unavailable", 503)
                metrics = evaluate_model(weights_path, dataset_yaml)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE models
                        SET map50 = %s, precision_score = %s, recall_score = %s
                        WHERE model_id = %s
                        """,
                        (
                            metrics["map50"],
                            metrics["precision"],
                            metrics["recall"],
                            model_id,
                        ),
                    )
                source = "validation-run"
            else:
                metrics = {
                    "map50": float(model["map50"]) if model["map50"] is not None else None,
                    "precision": (
                        float(model["precision_score"])
                        if model["precision_score"] is not None else None
                    ),
                    "recall": (
                        float(model["recall_score"])
                        if model["recall_score"] is not None else None
                    ),
                }
                source = "stored-evaluation"
            log_action(
                conn,
                "model_evaluated",
                f"model_id={model_id}, source={source}",
                request.auth_user["user_id"],
            )
        return ok({"status": "success", "model_id": model_id, "metrics": metrics, "source": source})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY B.1 - Flag an inaccurate or uncertain result for review.
@app.route("/api/results/<int:result_id>/flag", methods=["POST"])
@require_roles("Researcher", "Admin")
def flag_result(result_id: int):
    payload = request.get_json(silent=True) or {}
    note = str(payload.get("note") or "").strip()
    if not note:
        return fail("A review note is required", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE detection_results
                    SET quality_status = 'flagged', review_note = %s
                    WHERE result_id = %s
                    RETURNING result_id
                    """,
                    (note, result_id),
                )
                if not cur.fetchone():
                    return fail("Detection result not found", 404)
            log_action(conn, "result_flagged", f"result_id={result_id}: {note}", request.auth_user["user_id"])
        return ok({"status": "success", "result_id": result_id, "quality_status": "flagged"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY E.2 - List, queue, or execute a model training run.
@app.route("/api/training-runs", methods=["GET", "POST"])
@require_roles("Admin")
def training_runs():
    if request.method == "GET":
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM training_runs ORDER BY run_id DESC")
                    runs = cur.fetchall()
            return ok({"training_runs": runs, "source": "database"})
        except Exception as exc:
            return db_error_response(exc)

    payload = request.get_json(silent=True) or {}
    if not payload.get("model_id") or not payload.get("dataset_id"):
        return fail("model_id and dataset_id are required", 400)
    if payload.get("execute_local") and not str(payload.get("dataset_yaml") or "").strip():
        return fail("dataset_yaml is required when execute_local is true", 400)
    hyperparameters = payload.get("hyperparameters") or {
        "epochs": 100,
        "image_size": 640,
        "batch": 16,
    }
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO training_runs (
                        model_id, dataset_id, status, hyperparameters, started_at
                    ) VALUES (%s, %s, 'queued', %s::jsonb, CURRENT_TIMESTAMP)
                    RETURNING *
                    """,
                    (payload["model_id"], payload["dataset_id"], json.dumps(hyperparameters)),
                )
                run = cur.fetchone()
            log_action(conn, "training_queued", f"run_id={run['run_id']}", request.auth_user["user_id"])
        if payload.get("execute_local"):
            dataset_yaml = str(payload.get("dataset_yaml") or "").strip()
            threading.Thread(
                target=execute_training_run,
                args=(run["run_id"], dataset_yaml),
                name=f"training-run-{run['run_id']}",
                daemon=True,
            ).start()
        return ok({
            "status": "success",
            "training_run": run,
            "execution": (
                "Local training started in the background."
                if payload.get("execute_local")
                else "Training configuration queued; execute it locally or through the project Colab notebook."
            ),
        }, 202)
    except Exception as exc:
        return db_error_response(exc)


def execute_training_run(run_id: int, dataset_yaml: str) -> None:
    """E.2 worker: load data/model, train epochs, validate, and save best weights."""
    try:
        if train_model is None:
            raise RuntimeError("Training runtime is unavailable")
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tr.*, m.weights_path, m.model_id
                    FROM training_runs tr
                    JOIN models m ON m.model_id = tr.model_id
                    WHERE tr.run_id = %s
                    """,
                    (run_id,),
                )
                run = cur.fetchone()
                if not run:
                    raise RuntimeError("Training run not found")
                cur.execute(
                    "UPDATE training_runs SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE run_id = %s",
                    (run_id,),
                )
                cur.execute(
                    "UPDATE models SET status = 'training' WHERE model_id = %s",
                    (run["model_id"],),
                )
        params = run["hyperparameters"] or {}
        weights = Path(str(run["weights_path"]))
        if not weights.is_absolute():
            weights = Path(__file__).resolve().parents[1] / weights
        result = train_model(
            weights,
            dataset_yaml,
            epochs=int(params.get("epochs", 100)),
            image_size=int(params.get("image_size", 640)),
            batch=int(params.get("batch", 16)),
            project=Path(__file__).resolve().parents[1] / "runs" / "train",
            name=f"run-{run_id}",
        )
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE training_runs
                    SET status = 'completed', metrics = %s::jsonb,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (json.dumps(result), run_id),
                )
                cur.execute(
                    """
                    UPDATE models
                    SET status = 'trained', weights_path = %s
                    WHERE model_id = %s
                    """,
                    (result["best_weights"], run["model_id"]),
                )
    except Exception as exc:
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE training_runs
                        SET status = 'failed', error_message = %s,
                            completed_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                        """,
                        (str(exc), run_id),
                    )
        except Exception:
            app.logger.exception("Could not persist training failure for run %s", run_id)


# USER STORY D.3 - System usage and uptime metrics.
@app.route("/api/admin/stats")
@require_roles("Admin")
def admin_stats():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE status = 'active'")
                active = cur.fetchone()["cnt"]
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM images WHERE status = 'pending' OR status = 'processing'")
                queue = cur.fetchone()["cnt"]
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM detection_results")
                detections = cur.fetchone()["cnt"]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS api_calls,
                           COUNT(*) FILTER (
                               WHERE action ILIKE '%failed%' OR details ILIKE '%error%'
                           ) AS errors
                    FROM system_logs
                    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    """
                )
                log_metrics = cur.fetchone()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(AVG(processing_time), 0) AS average_time FROM detection_results"
                )
                average_time = cur.fetchone()["average_time"]
        api_calls = int(log_metrics["api_calls"])
        errors = int(log_metrics["errors"])
        return ok({
            "active_users": active,
            "queue_length": queue,
            "total_detections": detections,
            "api_calls_24h": api_calls,
            "average_processing_time": round(float(average_time), 2),
            "uptime": str(datetime.now() - SERVICE_STARTED_AT).split(".")[0],
            "error_rate": f"{(errors / api_calls * 100) if api_calls else 0:.1f}%",
            "source": "database",
        })
    except Exception as exc:
        return db_error_response(exc)


# USER STORY D.3 - Administrative audit and error logs.
@app.route("/api/admin/logs")
@require_roles("Admin")
def admin_logs():
    return logs()


# USER STORY D.6 - Create a backup immediately.
@app.route("/api/admin/backup", methods=["POST"])
@require_roles("Admin")
def admin_backup_create():
    return backup()


# USER STORY D.6 - List available backups.
@app.route("/api/admin/backups")
@require_roles("Admin")
def admin_backups():
    return backup()


# USER STORY D.6 - Restore a selected PostgreSQL backup.
@app.route("/api/admin/backups/<path:file_name>/restore", methods=["POST"])
@require_roles("Admin")
def admin_backup_restore(file_name: str):
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") != "RESTORE":
        return fail('Restore requires confirm="RESTORE"', 400)
    safe_name = secure_filename(file_name)
    backup_path = (BACKUP_DIR / safe_name).resolve()
    if backup_path.parent != BACKUP_DIR.resolve() or not backup_path.exists():
        return fail("Backup file not found", 404)
    config = db_config()
    if not config["password"]:
        return fail("Database password is not configured", 503)
    if backup_path.suffix.lower() == ".dump":
        pg_restore = find_pg_restore()
        if not pg_restore:
            return fail("pg_restore is not configured", 503)
        command = [
            pg_restore,
            "-h", str(config["host"]),
            "-p", str(config["port"]),
            "-U", str(config["user"]),
            "-d", str(config["dbname"]),
            "--clean", "--if-exists", "--no-owner", "--single-transaction",
            str(backup_path),
        ]
    else:
        psql = find_psql()
        if not psql:
            return fail("psql is not configured", 503)
        command = [
            psql,
            "-h", str(config["host"]),
            "-p", str(config["port"]),
            "-U", str(config["user"]),
            "-d", str(config["dbname"]),
            "-v", "ON_ERROR_STOP=1",
            "-f", str(backup_path),
        ]
    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]
    completed = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=120, check=False
    )
    if completed.returncode != 0:
        return fail("Database restore failed", 500, restore_error=completed.stderr[-1000:])
    try:
        with db_connection() as conn:
            log_action(conn, "backup_restored", safe_name, request.auth_user["user_id"])
    except Exception:
        pass
    return ok({"status": "success", "message": "Backup restored", "file_name": safe_name})


# USER STORY D.2 - Report secure storage state.
@app.route("/api/admin/storage")
@require_roles("Admin")
def admin_storage():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM images")
                total_images = cur.fetchone()["cnt"]
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM image_files")
                total_files = cur.fetchone()["cnt"]
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(SUM(file_size), 0) AS sum_bytes FROM image_files")
                total_bytes = cur.fetchone()["sum_bytes"]
        return ok({
            "total_images": total_images,
            "total_files": total_files,
            "total_size_bytes": int(total_bytes),
            "total_size_mb": round(int(total_bytes) / (1024 * 1024), 2),
            "encrypted": True,
            "encryption": "Fernet AES-128-CBC + HMAC-SHA256",
            "source": "database",
        })
    except Exception as exc:
        return db_error_response(exc)


# USER STORIES A.4, D.2 - Authorize and decrypt an image for viewing.
@app.route("/api/images/<int:image_id>/file/<string:file_type>")
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def serve_image_file(image_id: int, file_type: str):
    """Serve binary image data from image_files table."""
    if file_type not in ("original", "annotated"):
        return fail("file_type must be original or annotated", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, access_level FROM images WHERE image_id = %s",
                    (image_id,),
                )
                image = cur.fetchone()
            if not image:
                return fail("Image not found", 404)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT access_level FROM access_policies WHERE role_name = %s",
                    (request.auth_user["role"],),
                )
                policy = cur.fetchone()
            access_level = policy["access_level"] if policy else None
            if access_level == "aggregated_field_data":
                return fail("This role can access aggregated field data only", 403)
            if access_level in {"own_images", None} and (
                request.auth_user["role"] == "Farmer"
                and image["user_id"] != request.auth_user["user_id"]
            ):
                return fail("You can only access your own images", 403)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT image_data, mime_type, file_name, encrypted FROM image_files "
                    "WHERE image_id = %s AND file_type = %s",
                    (image_id, file_type),
                )
                row = cur.fetchone()
            if not row:
                return fail("File not found", 404)
            data = bytes(row["image_data"])
            if row.get("encrypted", True):
                data = encryption_cipher().decrypt(data)
            log_action(
                conn,
                "image_accessed",
                f"image_id={image_id}, file_type={file_type}",
                request.auth_user["user_id"],
            )
        return Response(
            data,
            mimetype=row["mime_type"],
            headers={"Content-Disposition": f'inline; filename="{row["file_name"]}"'},
        )
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/logs", methods=["GET"])
@require_roles("Admin")
def logs():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT l.log_id, l.user_id, u.name AS user_name, l.action, l.details, l.created_at
                    FROM system_logs l
                    LEFT JOIN users u ON u.user_id = l.user_id
                    ORDER BY l.created_at DESC, l.log_id DESC
                    LIMIT 50
                    """
                )
                rows = cur.fetchall()
        return ok({"logs": rows, "total": len(rows), "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/backup", methods=["GET", "POST"])
@require_roles("Admin")
def backup():
    if request.method == "GET":
        backups = list_backup_files()
        return ok({"backups": backups, "total": len(backups), "source": "filesystem"})

    config = db_config()
    if not config["password"]:
        return fail("Database password is not configured", 503)

    pg_dump = find_pg_dump()
    if not pg_dump:
        return fail("pg_dump was not found. Set PG_DUMP_PATH or add PostgreSQL bin to PATH.", 503)

    database_name = secure_filename(config["dbname"]) or "maize_detector"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{database_name}_{timestamp}.sql"

    command = [
        pg_dump,
        "-h",
        config["host"],
        "-p",
        config["port"],
        "-U",
        config["user"],
        "-d",
        config["dbname"],
        "-F",
        "p",
        "-f",
        str(backup_path),
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]

    try:
        completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90, check=False)
        if completed.returncode != 0:
            if backup_path.exists():
                backup_path.unlink()
            return fail(
                "Database backup failed",
                500,
                backup_error=(completed.stderr or completed.stdout or "pg_dump returned a non-zero exit code").strip(),
            )

        try:
            with db_connection() as conn:
                log_action(
                    conn,
                    "backup_created",
                    backup_path.name,
                    request.auth_user["user_id"],
                )
        except Exception:
            pass
        return ok(
            {
                "status": "success",
                "message": "Database backup created",
                "backup": backup_file_info(backup_path),
                "source": "pg_dump",
            },
            201,
        )
    except subprocess.TimeoutExpired:
        if backup_path.exists():
            backup_path.unlink()
        return fail("Database backup timed out", 504)


# USER STORY C.4 - List fields with optional region filtering.
@app.route("/api/fields", methods=["GET"])
@require_roles("Researcher", "Agronomist", "Admin")
def fields():
    region = request.args.get("region")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                if region:
                    cur.execute("SELECT * FROM fields WHERE location = %s ORDER BY field_id", (region,))
                else:
                    cur.execute("SELECT * FROM fields ORDER BY field_id")
                rows = cur.fetchall()
        return ok({"fields": rows, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY C.1 - Evaluate one field's plant health.
@app.route("/api/fields/<int:field_id>/health", methods=["GET"])
@require_roles("Agronomist", "Admin")
def field_health(field_id: int):
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM fields WHERE field_id = %s", (field_id,))
                field = cur.fetchone()
            if field:
                count = float(field["latest_avg_count"])
                health = "Warning" if count < float(field["threshold_low"]) else "Healthy"
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE fields SET health_status = %s WHERE field_id = %s",
                        (health, field_id),
                    )
                field["health_status"] = health
    except Exception as exc:
        return db_error_response(exc)
    if not field:
        return fail("Field not found", 404)
    count = float(field["latest_avg_count"])
    baseline = float(field["baseline_count"])
    threshold = float(field["threshold_low"])
    return ok({
        "field": field,
        "health": "Warning" if count < threshold else "Healthy",
        "gap": round(count - baseline, 2),
        "recommendation": (
            "Inspect irrigation, nutrient availability, and image sampling coverage."
            if count < threshold
            else "Continue the current monitoring schedule."
        ),
    })


# AGRONOMIST EXTENSION C.1 - Human-centred maize leaf-disease assistance.
@app.route("/api/agronomy/diagnose", methods=["POST"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def diagnose_maize_leaf():
    if get_disease_predictor is None or build_advice is None:
        return fail("Disease assistance is not installed on this server", 503)

    is_multipart = bool(request.files)
    payload = request.form if is_multipart else (request.get_json(silent=True) or {})
    language = normalize_language(payload.get("language")) if normalize_language else "en"
    field_id = payload.get("field_id") or payload.get("fieldId")
    image_id = payload.get("image_id") or payload.get("imageId")
    uploaded = request.files.get("image") if is_multipart else None

    if not uploaded and not image_id:
        message = (
            "请上传叶片照片，或提供已有的 image_id。"
            if language == "zh-CN"
            else "Upload a leaf image or provide an existing image_id."
        )
        return fail(message, 400)
    if uploaded and image_id:
        return fail("Provide either an uploaded image or image_id, not both", 400)

    if field_id not in (None, ""):
        try:
            field_id = int(field_id)
        except (TypeError, ValueError):
            return fail("field_id must be an integer", 400)
    else:
        field_id = None

    context = {
        "crop_stage": str(payload.get("crop_stage") or payload.get("cropStage") or "").strip()[:200],
        "recent_weather": str(payload.get("recent_weather") or payload.get("recentWeather") or "").strip()[:500],
        "symptom_spread": str(payload.get("symptom_spread") or payload.get("symptomSpread") or "").strip()[:500],
    }
    image_name = None
    image_bytes = None

    if uploaded:
        validation_error = validate_image_upload(uploaded.filename, uploaded.content_type)
        if validation_error:
            return fail(validation_error, 400)
        image_bytes = uploaded.read(10 * 1024 * 1024 + 1)
        if len(image_bytes) > 10 * 1024 * 1024:
            return fail("Image must be 10 MB or smaller", 413)
        image_name = clean_image_filename(uploaded.filename)
    else:
        try:
            image_id = int(image_id)
        except (TypeError, ValueError):
            return fail("image_id must be an integer", 400)
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT image_name, user_id, field_id FROM images WHERE image_id = %s",
                        (image_id,),
                    )
                    image = cur.fetchone()
            if not image:
                return fail("Uploaded image not found", 404)
            if (
                request.auth_user["role"] != "Admin"
                and image["user_id"] != request.auth_user["user_id"]
            ):
                return fail("You can only diagnose images you uploaded", 403)
            image_name = image["image_name"]
            field_id = field_id or image.get("field_id")
            with materialized_image(Path(image_name).name) as image_path:
                image_bytes = image_path.read_bytes()
        except Exception as exc:
            return db_error_response(exc)

    try:
        predictor = get_disease_predictor()
        prediction = predictor.predict_bytes(image_bytes)
        response = build_advice(prediction, language=language, context=context)
    except InvalidDiseaseImage as exc:
        return fail(str(exc), 400)
    except DiseaseModelUnavailable as exc:
        app.logger.info("Disease model unavailable: %s", exc)
        return fail("Disease model is not ready on this server", 503)
    except Exception:
        app.logger.exception("Disease inference failed")
        return fail("Disease analysis could not be completed", 500)

    try:
        with db_connection() as conn:
            if uploaded:
                image_id = create_image_record(
                    conn,
                    image_name=image_name,
                    file_size=len(image_bytes),
                    user_id=int(request.auth_user["user_id"]),
                )
                secure_store_bytes(image_name, image_bytes)
                store_image_blob(
                    conn,
                    image_id,
                    "original",
                    image_name,
                    uploaded.content_type or "image/jpeg",
                    image_bytes,
                )
                if field_id:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE images SET field_id = %s WHERE image_id = %s",
                            (field_id, image_id),
                        )

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO disease_diagnoses
                        (user_id, field_id, image_id, model_version, knowledge_version,
                         status, predicted_condition, confidence, entropy,
                         rejection_reason, quality_findings, context_data, response_data)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                         %s::jsonb, %s::jsonb, %s::jsonb)
                    RETURNING diagnosis_id
                    """,
                    (
                        request.auth_user["user_id"],
                        field_id,
                        image_id,
                        response.get("technical", {}).get("model_version"),
                        response.get("knowledge_version"),
                        response["status"],
                        (response.get("possible_condition") or {}).get("code"),
                        response.get("technical", {}).get("confidence"),
                        response.get("technical", {}).get("entropy"),
                        None if response["status"] == "supported" else response["status"],
                        json.dumps(response.get("quality", {}), ensure_ascii=False),
                        json.dumps(response.get("context_received", {}), ensure_ascii=False),
                        json.dumps(response, ensure_ascii=False),
                    ),
                )
                diagnosis_id = cur.fetchone()["diagnosis_id"]
            log_action(
                conn,
                "maize_leaf_diagnosed",
                f"diagnosis_id={diagnosis_id}; status={response['status']}",
                request.auth_user["user_id"],
            )
        response["diagnosis_id"] = diagnosis_id
        response["image_id"] = image_id
        response["persistence"] = {"status": "saved"}
    except Exception:
        app.logger.exception("Disease result persistence failed")
        response["diagnosis_id"] = None
        response["image_id"] = image_id
        response["persistence"] = {
            "status": "failed",
            "message": (
                "诊断已完成，但这次记录没有保存成功。"
                if language == "zh-CN"
                else "The assessment completed, but this record could not be saved."
            ),
        }

    return ok(response)


@app.route("/api/agronomy/diagnoses", methods=["GET"])
@require_roles("Farmer", "Researcher", "Agronomist", "Admin")
def list_maize_leaf_diagnoses():
    """Return a safe summary of leaf screenings visible to the signed-in user."""
    try:
        limit = min(max(int(request.args.get("limit", "20")), 1), 100)
    except ValueError:
        return fail("limit must be an integer", 400)

    role = request.auth_user["role"]
    own_records_only = role in {"Farmer", "Researcher"}
    query = """
        SELECT diagnosis_id, image_id, status, predicted_condition,
               response_data, created_at
        FROM disease_diagnoses
    """
    params: list[Any] = []
    if own_records_only:
        query += " WHERE user_id = %s"
        params.append(request.auth_user["user_id"])
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
    except Exception as exc:
        return db_error_response(exc)

    records = []
    for row in rows:
        response_data = row.get("response_data") or {}
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError:
                response_data = {}
        condition = response_data.get("possible_condition") or {}
        records.append(
            {
                "diagnosis_id": row["diagnosis_id"],
                "image_id": row.get("image_id"),
                "status": row["status"],
                "condition_code": row.get("predicted_condition"),
                "condition_name": condition.get("display_name"),
                "headline": response_data.get("headline"),
                "created_at": (
                    row["created_at"].isoformat()
                    if row.get("created_at")
                    else None
                ),
            }
        )
    return ok({"records": records})


@app.route("/api/agronomy/diagnoses/<int:diagnosis_id>/review", methods=["POST"])
@require_roles("Agronomist", "Admin")
def review_maize_leaf_diagnosis(diagnosis_id: int):
    payload = request.get_json(silent=True) or {}
    decision = str(payload.get("decision") or "").strip().lower()
    note = str(payload.get("note") or "").strip()[:2000]
    reviewed_condition = str(
        payload.get("reviewed_condition") or payload.get("reviewedCondition") or ""
    ).strip()
    allowed_decisions = {"confirmed", "corrected", "inconclusive"}
    allowed_conditions = {
        "healthy",
        "common_rust",
        "gray_leaf_spot",
        "northern_leaf_blight",
        "other",
    }
    if decision not in allowed_decisions:
        return fail("decision must be confirmed, corrected, or inconclusive", 400)
    if decision == "corrected" and reviewed_condition not in allowed_conditions:
        return fail("A supported reviewed_condition or other is required", 400)
    if decision != "corrected":
        reviewed_condition = None
    if not note:
        return fail("A short review note is required", 400)

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE disease_diagnoses
                    SET reviewer_user_id = %s,
                        reviewer_decision = %s,
                        reviewed_condition = %s,
                        reviewer_note = %s,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE diagnosis_id = %s
                    RETURNING diagnosis_id, status, predicted_condition,
                              reviewer_decision, reviewed_condition,
                              reviewer_note, reviewed_at
                    """,
                    (
                        request.auth_user["user_id"],
                        decision,
                        reviewed_condition,
                        note,
                        diagnosis_id,
                    ),
                )
                reviewed = cur.fetchone()
            if not reviewed:
                return fail("Diagnosis record not found", 404)
            log_action(
                conn,
                "maize_leaf_diagnosis_reviewed",
                f"diagnosis_id={diagnosis_id}; decision={decision}",
                request.auth_user["user_id"],
            )
        return ok({"status": "success", "review": reviewed})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY C.1 - Read or save agronomist recommendations.
@app.route("/api/fields/<int:field_id>/recommendations", methods=["GET", "POST"])
@require_roles("Agronomist", "Admin")
def field_recommendations(field_id: int):
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        note = str(payload.get("note") or "").strip()
        if not note:
            return fail("Recommendation note is required", 400)
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO recommendations (field_id, user_id, note)
                        VALUES (%s, %s, %s) RETURNING *
                        """,
                        (field_id, request.auth_user["user_id"], note),
                    )
                    recommendation = cur.fetchone()
                log_action(conn, "recommendation_added", f"field_id={field_id}", request.auth_user["user_id"])
            return ok({"status": "success", "recommendation": recommendation}, 201)
        except Exception as exc:
            return db_error_response(exc)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM recommendations WHERE field_id = %s ORDER BY created_at DESC",
                    (field_id,),
                )
                rows = cur.fetchall()
        return ok({"recommendations": rows, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY C.2 - Aggregate field growth over time.
@app.route("/api/fields/<int:field_id>/growth", methods=["GET"])
@require_roles("Agronomist", "Admin")
def field_growth(field_id: int):
    try:
        weeks = max(2, min(int(request.args.get("weeks", 4)), 12))
    except (TypeError, ValueError):
        return fail("weeks must be an integer between 2 and 12", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT date_trunc('week', dr.created_at)::date AS week,
                           AVG(dr.tassel_count) AS average_count
                    FROM detection_results dr
                    JOIN images i ON i.image_id = dr.image_id
                    WHERE i.field_id = %s
                      AND dr.created_at >= CURRENT_DATE - (%s * INTERVAL '1 week')
                    GROUP BY date_trunc('week', dr.created_at)
                    ORDER BY week
                    """,
                    (field_id, weeks),
                )
                rows = cur.fetchall()
        labels = [row["week"].isoformat() for row in rows]
        trend = [round(float(row["average_count"]), 2) for row in rows]
    except Exception as exc:
        return db_error_response(exc)
    return ok({
        "field_id": field_id,
        "weeks": weeks,
        "labels": labels,
        "trend": trend,
        "growth_rate": (
            round((trend[-1] - trend[0]) / max(len(trend) - 1, 1), 2)
            if trend
            else 0
        ),
        "source": "database",
    })


# USER STORY C.3 - Scan fields for abnormal tassel patterns.
@app.route("/api/fields/anomalies", methods=["GET"])
@require_roles("Agronomist", "Admin")
def field_anomalies():
    """H.3: scan every Field, compare with its threshold, and persist flags."""
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE fields
                    SET anomaly_flag = latest_avg_count < threshold_low,
                        health_status = CASE
                            WHEN latest_avg_count < threshold_low THEN 'Warning'
                            ELSE 'Healthy'
                        END
                    """
                )
                cur.execute(
                    "SELECT * FROM fields WHERE anomaly_flag = TRUE ORDER BY field_id"
                )
                anomalies = cur.fetchall()
        return ok({"anomalies": anomalies, "source": "database"})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY C.3 - Persist an anomaly review request.
@app.route("/api/fields/<int:field_id>/anomaly", methods=["POST"])
@require_roles("Agronomist", "Admin")
def flag_field_anomaly(field_id: int):
    payload = request.get_json(silent=True) or {}
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        return fail("An anomaly review reason is required", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE fields
                    SET anomaly_flag = TRUE, anomaly_reason = %s, health_status = 'Warning'
                    WHERE field_id = %s
                    RETURNING *
                    """,
                    (reason, field_id),
                )
                field = cur.fetchone()
            if not field:
                return fail("Field not found", 404)
            log_action(
                conn,
                "field_anomaly_review",
                f"field_id={field_id}: {reason}",
                request.auth_user["user_id"],
            )
        return ok({"status": "success", "field": field})
    except Exception as exc:
        return db_error_response(exc)


# USER STORY C.5 - Return summarized agronomy insights.
@app.route("/api/fields/insights", methods=["GET"])
@require_roles("Agronomist", "Admin")
def field_insights():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM fields ORDER BY field_id")
                fields_payload = cur.fetchall()
                cur.execute(
                    """
                    SELECT COALESCE(AVG(dr.tassel_count), 0) AS average_count,
                           COUNT(*) AS result_count
                    FROM detection_results dr
                    WHERE dr.created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """
                )
                aggregate = cur.fetchone()
        source = "database"
    except Exception as exc:
        return db_error_response(exc)
    at_risk = [item for item in fields_payload if item["anomaly_flag"]]
    return ok({
        "insights": [
            f"{len(fields_payload) - len(at_risk)} of {len(fields_payload)} fields are within the healthy range.",
            f"{len(at_risk)} field(s) require review due to low tassel counts.",
            (
                f"{int(aggregate['result_count'])} results from the last 30 days have an "
                f"average count of {float(aggregate['average_count']):.1f}."
            ),
        ],
        "recommendation": "Prioritize follow-up surveys for flagged fields and retain the same camera height for comparable counts.",
        "source": source,
    })


# USER STORY E.1 - Preprocess and securely save an image.
@app.route("/api/system/preprocess/<int:image_id>", methods=["POST"])
@require_roles("Admin")
def preprocess_image(image_id: int):
    payload = request.get_json(silent=True) or {}
    augment = bool(payload.get("augment", False))
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT image_name FROM images WHERE image_id = %s", (image_id,))
                image = cur.fetchone()
        if not image:
            return fail("Image not found", 404)
        from PIL import Image, ImageOps
        with materialized_image(image["image_name"]) as source:
            processed = ImageOps.exif_transpose(Image.open(source).convert("RGB"))
            processed.thumbnail((640, 640))
            if augment:
                processed = ImageOps.mirror(processed)
            output = tempfile.SpooledTemporaryFile()
            processed.save(output, format="JPEG", quality=90)
            output.seek(0)
            data = output.read()
        name = f"preprocessed_{Path(image['image_name']).stem}.jpg"
        stored = secure_store_bytes(name, data)
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE images
                    SET preprocessed = TRUE, preprocessed_path = %s
                    WHERE image_id = %s
                    """,
                    (str(stored), image_id),
                )
            log_action(
                conn,
                "image_preprocessed",
                f"image_id={image_id}, augment={augment}",
                request.auth_user["user_id"],
            )
        steps = ["EXIF orientation", "RGB conversion", "resize within 640x640", "JPEG normalization"]
        if augment:
            steps.append("horizontal augmentation")
        return ok({
            "status": "success",
            "image_id": image_id,
            "preprocessed_name": name,
            "preprocessed": True,
            "steps": steps,
        })
    except Exception as exc:
        return fail("Preprocessing failed", 500, error=str(exc))


# Shared AI system status for E.1-E.5.
@app.route("/api/system/status", methods=["GET"])
@require_roles("Admin", "Researcher")
def system_status():
    predictor = get_predictor() if get_predictor is not None else None
    weights = predictor.model_path if predictor is not None else Path(
        "models/deployment/tassel-best.pt"
    )
    predictor_available = False
    if predictor is not None:
        try:
            predictor_available = predictor.available
        except Exception:
            predictor_available = False
    active_version = None
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT model_version FROM models WHERE status = 'active' ORDER BY activated_at DESC NULLS LAST LIMIT 1"
                )
                active = cur.fetchone()
                active_version = active["model_version"] if active else None
    except Exception:
        active_version = None
    project_root = Path(__file__).resolve().parents[1]
    model_display = str(weights.relative_to(project_root)) if weights.is_relative_to(project_root) else weights.name
    return ok({
        "model_file": model_display,
        "model_file_exists": weights.exists(),
        "inference_available": predictor_available,
        "active_model_version": active_version,
        "training_notebooks": [
            "training/notebooks/tassel/maize_yolo26_colab.ipynb",
            "training/notebooks/tassel/maize_yolo26_final.ipynb",
        ],
    })


if __name__ == "__main__":
    print("Maize Detector API running at http://localhost:5000")
    ready, error = db_ready()
    if not ready:
        raise SystemExit(f"PostgreSQL startup check failed: {error}")
    if get_predictor is None or not get_predictor().available:
        raise SystemExit("AI startup check failed: the configured tassel model is unavailable")
    print("Database: PostgreSQL connected")
    print(f"AI Inference: {get_predictor().model_path.name} loaded")
    from wsgiref.simple_server import make_server
    httpd = make_server("127.0.0.1", 5000, app)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.server_close()
