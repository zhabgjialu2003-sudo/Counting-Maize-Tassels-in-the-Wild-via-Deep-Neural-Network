from __future__ import annotations

import os
import json
import random

from dotenv import load_dotenv
load_dotenv()  # load .env file so PGPASSWORD etc. are always available
import hashlib
import shutil
import subprocess
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # Allows the prototype to run before dependencies are installed.
    psycopg = None
    dict_row = None


app = Flask(__name__)
CORS(app)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}
VALID_USER_STATUSES = {"active", "disabled"}


# --- Mock Data: same domain entities as the frontend BCE prototype ---
MOCK_RESULTS = [
    {"image_name": "maize_001.jpg", "count": 37, "confidence": 0.89, "processing_time": 2.4},
    {"image_name": "maize_002.jpg", "count": 42, "confidence": 0.91, "processing_time": 2.1},
    {"image_name": "maize_003.jpg", "count": 29, "confidence": 0.85, "processing_time": 3.0},
    {"image_name": "maize_004.jpg", "count": 35, "confidence": 0.93, "processing_time": 1.8},
    {"image_name": "maize_005.jpg", "count": 31, "confidence": 0.87, "processing_time": 2.6},
]

MOCK_HISTORY = [
    {
        "result_id": i + 1,
        "image_id": i + 1,
        "image_name": r["image_name"],
        "tassel_count": r["count"],
        "count": r["count"],
        "confidence_score": r["confidence"],
        "confidence": r["confidence"],
        "processing_time": r["processing_time"],
        "created_at": f"2026-06-{10 + i:02d}",
        "annotated_image_path": f"/mock/annotated_{r['image_name']}",
    }
    for i, r in enumerate(MOCK_RESULTS)
]


def db_config() -> dict[str, str]:
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "maize_detector"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
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


def db_ready() -> tuple[bool, str | None]:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                cur.fetchone()
        return True, None
    except Exception as exc:
        return False, str(exc)


def pick_mock_result(image_name: str | None = None) -> dict[str, Any]:
    result = random.choice(MOCK_RESULTS).copy()
    if image_name:
        result["image_name"] = image_name
    return {**result, "status": "success", "source": "mock"}


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
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return f"sha256${digest}"


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
                dr.created_at
            FROM detection_results dr
            JOIN images i ON i.image_id = dr.image_id
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


def create_mock_detection(conn, image_id: int) -> dict[str, Any]:
    mock = random.choice(MOCK_RESULTS)
    tassel_count = mock["count"]
    confidence = mock["confidence"]
    processing_time = mock["processing_time"]
    bbox_data = {
        "model": "prototype-yolo-mock",
        "boxes": [
            {"x": 100, "y": 60, "width": 80, "height": 80, "confidence": round(confidence - 0.02, 2)},
            {"x": 250, "y": 120, "width": 80, "height": 80, "confidence": confidence},
            {"x": 400, "y": 80, "width": 80, "height": 80, "confidence": round(confidence - 0.04, 2)},
        ],
    }

    with conn.cursor() as cur:
        cur.execute("UPDATE images SET status = 'completed' WHERE image_id = %s", (image_id,))
        cur.execute(
            """
            INSERT INTO detection_results (
                image_id,
                tassel_count,
                confidence_score,
                annotated_image_path,
                processing_time,
                bbox_data
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            RETURNING result_id
            """,
            (
                image_id,
                tassel_count,
                confidence,
                f"uploads/annotated_image_{image_id}.jpg",
                processing_time,
                json.dumps(bbox_data),
            ),
        )
        result_id = cur.fetchone()["result_id"]

    result = latest_detection_for_image(conn, image_id)
    result["result_id"] = result_id
    return result


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
                dr.created_at
            FROM detection_results dr
            JOIN images i ON i.image_id = dr.image_id
            WHERE dr.result_id = %s
            LIMIT 1
            """,
            (result_id,),
        )
        row = cur.fetchone()
    return normalize_detection_row(row) if row else None


@app.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/api/health", methods=["GET"])
def health():
    ready, error = db_ready()
    return ok(
        {
            "status": "ok",
            "service": "Maize Detector API",
            "version": "0.2.0",
            "database": "connected" if ready else "mock",
            "database_error": error if not ready else None,
        }
    )


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
                    SELECT u.user_id, u.name, u.email, u.password_hash, u.status,
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

        # Prototype: accept any password or verify hash
        stored_hash = user["password_hash"]
        if stored_hash and not stored_hash.startswith("$2b$"):
            # SHA-256 hash (prototype)
            expected = hash_password(password)
            if expected != stored_hash:
                return fail("Invalid email or password", 401)

        return ok(
            {
                "status": "success",
                "message": "Login successful",
                "user": {
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                },
            }
        )
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("image") or request.files.get("file")
    payload = request.get_json(silent=True) or {}
    user_id = request.form.get("user_id") or payload.get("user_id") or 1

    if file:
        original_name = file.filename or "uploaded_maize_image.jpg"
        validation_error = validate_image_upload(original_name, file.content_type)
        if validation_error:
            return fail(validation_error, 400)

        image_name = clean_image_filename(original_name)
        file_size = request.content_length
        file.save(UPLOAD_DIR / image_name)
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
        return ok(
            {
                "status": "success",
                "message": "Image upload accepted in mock mode",
                "image_id": random.randint(100, 999),
                "image_name": image_name,
                "source": "mock",
                "database_error": str(exc),
            },
            202,
        )


@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}
    image_id = payload.get("image_id") or payload.get("imageId")
    image_name = payload.get("image_name") or payload.get("imageName") or "maize_sample.jpg"

    try:
        with db_connection() as conn:
            if image_id:
                image_id = int(image_id)
                existing = latest_detection_for_image(conn, image_id)
                if existing:
                    return ok(existing)
            else:
                image_id = create_image_record(conn, image_name=image_name, file_size=payload.get("file_size"))

            result = create_mock_detection(conn, image_id)
            return ok(result, 201)
    except Exception as exc:
        return ok({**pick_mock_result(image_name), "database_error": str(exc)}, 202)


@app.route("/api/history", methods=["GET"])
def history():
    try:
        limit = min(int(request.args.get("limit", 100)), 200)
    except (ValueError, TypeError):
        limit = 100
    try:
        with db_connection() as conn:
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
                        dr.created_at
                    FROM detection_results dr
                    JOIN images i ON i.image_id = dr.image_id
                    ORDER BY dr.created_at DESC, dr.result_id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                records = [normalize_detection_row(row) for row in cur.fetchall()]
        return ok({"records": records, "total": len(records), "source": "database"})
    except Exception as exc:
        return ok({"records": MOCK_HISTORY[:limit], "total": len(MOCK_HISTORY[:limit]), "source": "mock", "database_error": str(exc)})


@app.route("/api/results/<int:result_id>", methods=["GET"])
def result_detail(result_id: int):
    try:
        with db_connection() as conn:
            result = detection_for_result(conn, result_id)
        if not result:
            return fail("Detection result not found", 404)
        return ok(result)
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/stats", methods=["GET"])
def stats():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(DISTINCT i.image_id) AS total_uploaded_images,
                        COALESCE(SUM(dr.tassel_count), 0) AS total_detected_tassels,
                        COALESCE(AVG(dr.tassel_count), 0) AS average_tassel_count
                    FROM images i
                    LEFT JOIN detection_results dr ON dr.image_id = i.image_id
                    """
                )
                row = cur.fetchone()
        return ok({**row, "model_status": "Active", "source": "database"})
    except Exception as exc:
        total = sum(r["count"] for r in MOCK_RESULTS)
        return ok(
            {
                "total_uploaded_images": 128,
                "total_detected_tassels": total,
                "average_tassel_count": round(total / len(MOCK_RESULTS), 1),
                "model_status": "Active",
                "source": "mock",
                "database_error": str(exc),
            }
        )


def report_response(report_type: str):
    fallback = {
        "daily": {
            "date": "2026-06-13",
            "total_uploads": 24,
            "successful_detections": 22,
            "failed_detections": 2,
            "average_tassel_count": 31,
            "system_status": "Normal",
        },
        "weekly": {
            "week": "2026-06-07 to 2026-06-13",
            "total_uploads": 148,
            "successful_detections": 139,
            "failed_detections": 9,
            "average_tassel_count": 33,
            "most_active_day": "Friday",
            "average_processing_time": 2.8,
            "system_status": "Normal",
        },
        "monthly": {
            "month": "June 2026",
            "total_uploads": 520,
            "successful_detections": 496,
            "failed_detections": 24,
            "average_tassel_count": 34,
            "model_accuracy_estimate": 0.88,
            "system_status": "Normal",
        },
    }

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
            return ok({**fallback[report_type], "source": "mock"})

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
        return ok({**fallback[report_type], "source": "mock", "database_error": str(exc)})


@app.route("/api/report/daily", methods=["GET"])
def report_daily():
    return report_response("daily")


@app.route("/api/report/weekly", methods=["GET"])
def report_weekly():
    return report_response("weekly")


@app.route("/api/report/monthly", methods=["GET"])
def report_monthly():
    return report_response("monthly")


@app.route("/api/users", methods=["GET", "POST", "PUT", "DELETE"])
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
        return ok({"users": [], "total": 0, "source": "mock", "database_error": str(exc)})


@app.route("/api/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
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


@app.route("/api/users/<int:user_id>/status", methods=["PUT"])
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


@app.route("/api/datasets", methods=["GET", "POST"])
def datasets():
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
        return ok({"datasets": [], "total": 0, "source": "mock", "database_error": str(exc)})


@app.route("/api/datasets/<int:dataset_id>", methods=["PUT", "DELETE"])
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


@app.route("/api/admin/stats")
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
        return ok({
            "active_users": active,
            "queue_length": queue,
            "total_detections": detections,
            "uptime": "99.7%",
            "error_rate": "1.6%",
            "source": "database",
        })
    except Exception as exc:
        return ok({
            "active_users": 6, "queue_length": 11, "total_detections": 1420,
            "uptime": "99.7%", "error_rate": "1.6%",
            "source": "mock", "database_error": str(exc),
        })


@app.route("/api/admin/logs")
def admin_logs():
    return logs()


@app.route("/api/admin/backup", methods=["POST"])
def admin_backup_create():
    return backup()


@app.route("/api/admin/backups")
def admin_backups():
    return backup()


@app.route("/api/admin/storage")
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
            "source": "database",
        })
    except Exception as exc:
        return ok({
            "total_images": 520, "total_size_mb": 1240, "encrypted": True,
            "source": "mock", "database_error": str(exc),
        })


@app.route("/api/images/<int:image_id>/file/<string:file_type>")
def serve_image_file(image_id: int, file_type: str):
    """Serve binary image data from image_files table."""
    if file_type not in ("original", "annotated"):
        return fail("file_type must be original or annotated", 400)
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT image_data, mime_type, file_name FROM image_files "
                    "WHERE image_id = %s AND file_type = %s",
                    (image_id, file_type),
                )
                row = cur.fetchone()
        if not row:
            return fail("File not found", 404)
        return Response(
            bytes(row["image_data"]),
            mimetype=row["mime_type"],
            headers={"Content-Disposition": f'inline; filename="{row["file_name"]}"'},
        )
    except Exception as exc:
        return db_error_response(exc)


@app.route("/api/logs", methods=["GET"])
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
        return ok({"logs": [], "total": 0, "source": "mock", "database_error": str(exc)})


@app.route("/api/backup", methods=["GET", "POST"])
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


@app.route("/api/fields", methods=["GET"])
def fields():
    # The Week 10 database does not yet include a fields table, so this endpoint
    # keeps the Agronomist dashboard demonstrable until the next schema phase.
    return ok(
        {
            "fields": [
                {
                    "field_id": 1,
                    "field_name": "Field A - North",
                    "location": "North Region",
                    "latest_avg_count": 35,
                    "baseline_count": 30,
                    "health_status": "Healthy",
                },
                {
                    "field_id": 2,
                    "field_name": "Field B - East",
                    "location": "East Region",
                    "latest_avg_count": 18,
                    "baseline_count": 30,
                    "health_status": "At-Risk",
                },
                {
                    "field_id": 3,
                    "field_name": "Field C - South",
                    "location": "South Region",
                    "latest_avg_count": 42,
                    "baseline_count": 40,
                    "health_status": "Healthy",
                },
            ],
            "source": "mock",
        }
    )


if __name__ == "__main__":
    print("Maize Detector API running at http://localhost:5000")
    print("Database: PostgreSQL if PGPASSWORD is set, otherwise mock fallback")
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", port=5000)
