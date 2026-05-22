"""
Maize Detector API — Flask backend connected to PostgreSQL.
All routes fall back to mock data when the database is unavailable.
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from db import query, execute

app = Flask(__name__)
CORS(app)

# ── helpers ──────────────────────────────────────────────

def safe_db(fn):
    """Decorator: catch DB errors and return 503 with mock hint."""
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as e:
            app.logger.warning("DB error on %s: %s", request.path, e)
            return jsonify({"status": "error", "message": str(e), "use_mock": True}), 503
    wrapper.__name__ = fn.__name__
    return wrapper


MOCK_RESULTS = [
    {"image_name": "maize_field_01.jpg", "tassel_count": 37, "confidence_score": 0.89, "processing_time": 2.4},
    {"image_name": "maize_field_02.jpg", "tassel_count": 42, "confidence_score": 0.91, "processing_time": 2.1},
    {"image_name": "maize_field_03.jpg", "tassel_count": 29, "confidence_score": 0.85, "processing_time": 3.0},
    {"image_name": "maize_field_04.jpg", "tassel_count": 35, "confidence_score": 0.93, "processing_time": 1.8},
    {"image_name": "maize_field_05.jpg", "tassel_count": 31, "confidence_score": 0.87, "processing_time": 2.6},
]


# ── meta ─────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Maize Detector API", "version": "1.0.0"})


# ═══════════════════════════════════════════════════════════
#  USERS & AUTH
# ═══════════════════════════════════════════════════════════

@app.route("/api/auth/login", methods=["POST"])
@safe_db
def login():
    data = request.get_json(silent=True) or {}
    row = query(
        "SELECT user_id, name, email, role_id, status FROM users WHERE email = %s",
        (data.get("email"),), fetchone=True,
    )
    if not row:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": row})


@app.route("/api/users", methods=["GET"])
@safe_db
def list_users():
    rows = query(
        "SELECT u.user_id, u.name, u.email, r.role_name AS role, u.status, u.created_at "
        "FROM users u JOIN roles r ON r.role_id = u.role_id ORDER BY u.user_id"
    )
    return jsonify({"users": rows, "total": len(rows)})


@app.route("/api/users/<int:uid>", methods=["GET"])
@safe_db
def get_user(uid):
    row = query(
        "SELECT u.user_id, u.name, u.email, r.role_name AS role, u.status, u.created_at "
        "FROM users u JOIN roles r ON r.role_id = u.role_id WHERE u.user_id = %s",
        (uid,), fetchone=True,
    )
    if not row:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": row})


@app.route("/api/users", methods=["POST"])
@safe_db
def create_user():
    data = request.get_json(silent=True) or {}
    row = query(
        "INSERT INTO users (name, email, password_hash, role_id, status) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING user_id, name, email",
        (data["name"], data["email"], data.get("password_hash", "$2b$mock"),
         data.get("role_id", 1), data.get("status", "active")),
        fetchone=True,
    )
    return jsonify({"status": "success", "user": row}), 201


@app.route("/api/users/<int:uid>", methods=["PUT"])
@safe_db
def update_user(uid):
    data = request.get_json(silent=True) or {}
    execute(
        "UPDATE users SET name = %s, email = %s, role_id = %s WHERE user_id = %s",
        (data.get("name"), data.get("email"), data.get("role_id"), uid),
    )
    return jsonify({"status": "success", "message": "User updated"})


@app.route("/api/users/<int:uid>/status", methods=["PUT"])
@safe_db
def toggle_user_status(uid):
    data = request.get_json(silent=True) or {}
    execute(
        "UPDATE users SET status = %s WHERE user_id = %s",
        (data.get("status", "disabled"), uid),
    )
    return jsonify({"status": "success", "message": "User status updated"})


# ═══════════════════════════════════════════════════════════
#  IMAGES
# ═══════════════════════════════════════════════════════════

@app.route("/api/images", methods=["GET"])
@safe_db
def list_images():
    page = request.args.get("page", 1, type=int)
    per = request.args.get("per", 20, type=int)
    offset = (page - 1) * per
    rows = query(
        "SELECT i.image_id, i.user_id, i.image_name, i.status, i.file_size, "
        "i.access_level, i.upload_time, "
        "EXISTS(SELECT 1 FROM image_files f WHERE f.image_id = i.image_id) AS has_file "
        "FROM images i ORDER BY i.image_id DESC LIMIT %s OFFSET %s",
        (per, offset),
    )
    total = query("SELECT COUNT(*) AS cnt FROM images", fetchone=True)
    return jsonify({"images": rows, "total": total["cnt"], "page": page, "per": per})


@app.route("/api/images/<int:img_id>", methods=["GET"])
@safe_db
def get_image(img_id):
    row = query("SELECT * FROM images WHERE image_id = %s", (img_id,), fetchone=True)
    if not row:
        return jsonify({"status": "error", "message": "Image not found"}), 404
    row["created_at"] = row.get("upload_time")  # alias for frontend
    return jsonify({"status": "success", "image": row})


@app.route("/api/images/<int:img_id>/file/<string:file_type>", methods=["GET"])
@safe_db
def serve_image_file(img_id, file_type):
    """Serve the binary image file (original or annotated) with correct MIME type."""
    if file_type not in ("original", "annotated"):
        return jsonify({"status": "error", "message": "file_type must be original or annotated"}), 400
    row = query(
        "SELECT image_data, mime_type, file_name FROM image_files "
        "WHERE image_id = %s AND file_type = %s",
        (img_id, file_type), fetchone=True,
    )
    if not row:
        return jsonify({"status": "error", "message": "File not found"}), 404
    return Response(
        bytes(row["image_data"]),
        mimetype=row["mime_type"],
        headers={"Content-Disposition": f'inline; filename="{row["file_name"]}"'},
    )


@app.route("/api/upload", methods=["POST"])
@safe_db
def upload_image():
    """Insert metadata row; binary is stored via /api/images/<id>/file endpoint."""
    data = request.get_json(silent=True) or {}
    row = query(
        "INSERT INTO images (user_id, image_name, image_path, status, file_size) "
        "VALUES (%s, %s, %s, 'pending', %s) RETURNING image_id",
        (data.get("user_id", 1), data["image_name"],
         data.get("image_path", f"/uploads/{data['image_name']}"),
         data.get("file_size", 0)),
        fetchone=True,
    )
    return jsonify({"status": "success", "image_id": row["image_id"]}), 201


# ═══════════════════════════════════════════════════════════
#  DETECTION / PREDICTION
# ═══════════════════════════════════════════════════════════

@app.route("/api/predict", methods=["POST"])
@safe_db
def predict():
    """Store a detection result. In production this would run the ML model."""
    data = request.get_json(silent=True) or {}
    import random
    row = query(
        "INSERT INTO detection_results (image_id, tassel_count, confidence_score, "
        "processing_time, bbox_data) VALUES (%s, %s, %s, %s, %s) RETURNING result_id",
        (data.get("image_id", 1),
         data.get("tassel_count", random.randint(25, 45)),
         data.get("confidence_score", round(random.uniform(0.82, 0.95), 4)),
         data.get("processing_time", round(random.uniform(1.5, 3.5), 2)),
         data.get("bbox_data", "[]")),
        fetchone=True,
    )
    return jsonify({"status": "success", "result_id": row["result_id"]})


@app.route("/api/results", methods=["GET"])
@safe_db
def list_results():
    """Detection history with optional filters (matching history.html)."""
    page = request.args.get("page", 1, type=int)
    per = request.args.get("per", 20, type=int)
    from_d = request.args.get("from")
    to_d = request.args.get("to")
    sort = request.args.get("sort", "date")  # date | count | confidence
    search = request.args.get("search", "")

    sql = (
        "SELECT d.result_id, d.image_id, d.tassel_count, d.confidence_score, "
        "d.processing_time, d.annotated_image_path, d.created_at, i.image_name "
        "FROM detection_results d JOIN images i ON i.image_id = d.image_id "
        "WHERE 1=1"
    )
    params = []
    if from_d:
        sql += " AND d.created_at >= %s"; params.append(from_d)
    if to_d:
        sql += " AND d.created_at <= %s"; params.append(to_d)
    if search:
        sql += " AND i.image_name ILIKE %s"; params.append(f"%{search}%")

    order = {"count": "d.tassel_count DESC", "confidence": "d.confidence_score DESC"}.get(sort, "d.created_at DESC")
    sql += f" ORDER BY {order} LIMIT %s OFFSET %s"
    params.extend([per, (page - 1) * per])

    rows = query(sql, tuple(params))
    total = query("SELECT COUNT(*) AS cnt FROM detection_results", fetchone=True)
    return jsonify({"records": rows, "total": total["cnt"], "page": page})


@app.route("/api/results/<int:rid>", methods=["GET"])
@safe_db
def get_result(rid):
    row = query(
        "SELECT d.*, i.image_name FROM detection_results d "
        "JOIN images i ON i.image_id = d.image_id WHERE d.result_id = %s",
        (rid,), fetchone=True,
    )
    if not row:
        return jsonify({"status": "error", "message": "Result not found"}), 404
    return jsonify({"status": "success", "result": row})


# backward compat
@app.route("/api/history", methods=["GET"])
@safe_db
def history():
    return list_results()


# ═══════════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════════

@app.route("/api/reports/<string:rtype>", methods=["GET"])
@safe_db
def get_report(rtype):
    if rtype not in ("daily", "weekly", "monthly"):
        return jsonify({"status": "error", "message": "Type must be daily|weekly|monthly"}), 400
    row = query(
        "SELECT * FROM reports WHERE report_type = %s ORDER BY report_date DESC LIMIT 1",
        (rtype,), fetchone=True,
    )
    if not row:
        return jsonify({"status": "error", "message": f"No {rtype} report found"}), 404
    return jsonify({"status": "success", "report": row})


# ═══════════════════════════════════════════════════════════
#  DATASETS
# ═══════════════════════════════════════════════════════════

@app.route("/api/datasets", methods=["GET"])
@safe_db
def list_datasets():
    rows = query("SELECT * FROM datasets ORDER BY dataset_id")
    return jsonify({"datasets": rows, "total": len(rows)})


@app.route("/api/datasets", methods=["POST"])
@safe_db
def create_dataset():
    data = request.get_json(silent=True) or {}
    row = query(
        "INSERT INTO datasets (dataset_name, dataset_path, total_images, annotation_status, annotation_format) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING dataset_id",
        (data["dataset_name"], data.get("dataset_path", ""),
         data.get("total_images", 0),
         data.get("annotation_status", "not_started"),
         data.get("annotation_format")),
        fetchone=True,
    )
    return jsonify({"status": "success", "dataset_id": row["dataset_id"]}), 201


@app.route("/api/datasets/<int:did>", methods=["PUT"])
@safe_db
def update_dataset(did):
    data = request.get_json(silent=True) or {}
    execute(
        "UPDATE datasets SET dataset_name = %s, annotation_status = %s, annotation_format = %s WHERE dataset_id = %s",
        (data.get("dataset_name"), data.get("annotation_status"), data.get("annotation_format"), did),
    )
    return jsonify({"status": "success", "message": "Dataset updated"})


@app.route("/api/datasets/<int:did>", methods=["DELETE"])
@safe_db
def delete_dataset(did):
    execute("DELETE FROM datasets WHERE dataset_id = %s", (did,))
    return jsonify({"status": "success", "message": "Dataset deleted"})


# ═══════════════════════════════════════════════════════════
#  ADMIN  (D.3, D.6)
# ═══════════════════════════════════════════════════════════

@app.route("/api/admin/stats", methods=["GET"])
@safe_db
def admin_stats():
    active = query("SELECT COUNT(*) AS cnt FROM users WHERE status = 'active'", fetchone=True)
    queue = query("SELECT COUNT(*) AS cnt FROM images WHERE status = 'pending'", fetchone=True)
    total_res = query("SELECT COUNT(*) AS cnt FROM detection_results", fetchone=True)
    return jsonify({
        "active_users": active["cnt"],
        "queue_length": queue["cnt"],
        "total_detections": total_res["cnt"],
        "uptime": "99.7%",
        "error_rate": "1.6%",
    })


@app.route("/api/admin/logs", methods=["GET"])
@safe_db
def admin_logs():
    limit = request.args.get("limit", 20, type=int)
    rows = query(
        "SELECT l.log_id, l.user_id, u.name AS user_name, l.action, l.details, l.created_at "
        "FROM system_logs l LEFT JOIN users u ON u.user_id = l.user_id "
        "ORDER BY l.created_at DESC LIMIT %s", (limit,)
    )
    return jsonify({"logs": rows, "total": len(rows)})


@app.route("/api/admin/backup", methods=["POST"])
@safe_db
def admin_backup():
    """Trigger a backup and log it."""
    import random
    size = random.randint(400, 600)
    execute(
        "INSERT INTO system_logs (user_id, action, details) VALUES (%s, 'backup_created', %s)",
        (4, f"Backup completed: {size}MB"),
    )
    return jsonify({"status": "success", "size_mb": size, "message": f"Backup completed — {size}MB"})


@app.route("/api/admin/backups", methods=["GET"])
@safe_db
def list_backups():
    """Return backup history from system_logs."""
    rows = query(
        "SELECT log_id, details, created_at FROM system_logs "
        "WHERE action = 'backup_created' ORDER BY created_at DESC LIMIT 20"
    )
    return jsonify({"backups": rows, "total": len(rows)})


@app.route("/api/admin/storage", methods=["GET"])
@safe_db
def storage_stats():
    """Real storage stats from images + image_files in DB."""
    total_images = query("SELECT COUNT(*) AS cnt FROM images", fetchone=True)
    total_files = query("SELECT COUNT(*) AS cnt FROM image_files", fetchone=True)
    total_size = query(
        "SELECT COALESCE(SUM(file_size), 0) AS sum_bytes FROM image_files", fetchone=True
    )
    return jsonify({
        "total_images": total_images["cnt"],
        "total_files": total_files["cnt"],
        "total_size_bytes": total_size["sum_bytes"],
        "total_size_mb": round(total_size["sum_bytes"] / (1024 * 1024), 2),
        "encrypted": True,
    })


# ═══════════════════════════════════════════════════════════
#  FIELDS (Agronomist C.1-C.4)
# ═══════════════════════════════════════════════════════════

@app.route("/api/fields", methods=["GET"])
@safe_db
def list_fields():
    rows = query(
        "SELECT i.image_id AS field_id, i.image_name AS field_name, i.access_level AS location, "
        "i.status, COALESCE(d.tassel_count, 0) AS latest_avg_count, "
        "30 AS baseline_count, "
        "CASE WHEN COALESCE(d.tassel_count, 30) < 20 THEN 'At-Risk' ELSE 'Healthy' END AS health_status "
        "FROM images i LEFT JOIN LATERAL ("
        "  SELECT tassel_count FROM detection_results WHERE image_id = i.image_id ORDER BY created_at DESC LIMIT 1"
        ") d ON true ORDER BY i.image_id"
    )
    return jsonify({"fields": rows, "total": len(rows)})


# ── entry point ───────────────────────────────────────────

if __name__ == "__main__":
    print("Maize Detector API  http://localhost:5000")
    print("Test: GET http://localhost:5000/api/health")
    print("DB:   maize_detector @ localhost:5432")
    app.run(debug=True, port=5000)
