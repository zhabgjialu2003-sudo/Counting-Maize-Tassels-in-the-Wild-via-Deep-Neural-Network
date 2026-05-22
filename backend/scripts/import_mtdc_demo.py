from __future__ import annotations

import argparse
import json
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import psycopg
from psycopg.rows import dict_row


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "uploads" / "mtdc-demo"
DEFAULT_ZIP = Path(os.getenv("MTDC_UAV_ZIP", str(Path.home() / "Desktop" / "MTDC-UAV.zip")))


def clean_name(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9_.()-]+", "_", name)


def db_config() -> dict[str, str]:
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "maize_detector"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
    }


def image_mime_type(filename: str) -> str:
    if Path(filename).suffix.lower() == ".png":
        return "image/png"
    return "image/jpeg"


def ensure_image_files_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS image_files (
                file_id    SERIAL PRIMARY KEY,
                image_id   INTEGER NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
                file_type  VARCHAR(30) NOT NULL CHECK (file_type IN ('original', 'annotated')),
                file_name  VARCHAR(255) NOT NULL,
                mime_type  VARCHAR(100) NOT NULL,
                file_size  INTEGER NOT NULL,
                image_data BYTEA NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (image_id, file_type)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_image_files_image ON image_files(image_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_image_files_type ON image_files(file_type)")


def upsert_image_file(cur, image_id: int, file_type: str, file_name: str, mime_type: str, image_bytes: bytes) -> None:
    cur.execute(
        """
        INSERT INTO image_files (image_id, file_type, file_name, mime_type, file_size, image_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (image_id, file_type)
        DO UPDATE SET
            file_name = EXCLUDED.file_name,
            mime_type = EXCLUDED.mime_type,
            file_size = EXCLUDED.file_size,
            image_data = EXCLUDED.image_data,
            created_at = CURRENT_TIMESTAMP
        """,
        (image_id, file_type, file_name, mime_type, len(image_bytes), image_bytes),
    )


def read_detection_label(zip_file: zipfile.ZipFile, label_name: str) -> dict:
    root = ElementTree.fromstring(zip_file.read(label_name))
    width = int(root.findtext("size/width", "0"))
    height = int(root.findtext("size/height", "0"))
    boxes = []
    for obj in root.findall("object"):
        label = obj.findtext("name", "tassel")
        box = obj.find("bndbox")
        if box is None:
            continue
        xmin = int(float(box.findtext("xmin", "0")))
        ymin = int(float(box.findtext("ymin", "0")))
        xmax = int(float(box.findtext("xmax", "0")))
        ymax = int(float(box.findtext("ymax", "0")))
        boxes.append(
            {
                "label": label,
                "x": xmin,
                "y": ymin,
                "width": max(1, xmax - xmin),
                "height": max(1, ymax - ymin),
                "confidence": 0.92,
            }
        )
    return {"type": "boxes", "image_width": width, "image_height": height, "boxes": boxes}


def select_detection_pairs(zip_file: zipfile.ZipFile, limit: int) -> list[tuple[str, str]]:
    names = zip_file.namelist()
    labels = {name.lower(): name for name in names if name.lower().endswith(".xml")}
    pairs = []
    for image_name in sorted(
        name
        for name in names
        if name.lower().startswith("mtdc-uav/detection/images/") and name.lower().endswith((".jpg", ".jpeg", ".png"))
    ):
        label_name = re.sub(r"/images/", "/labels/", image_name, flags=re.IGNORECASE)
        label_name = re.sub(r"\.(jpg|jpeg|png)$", ".xml", label_name, flags=re.IGNORECASE)
        label_name = labels.get(label_name.lower())
        if label_name:
            pairs.append((image_name, label_name))
        if len(pairs) >= limit:
            break
    return pairs


def import_pair(conn, zip_file: zipfile.ZipFile, image_name: str, label_name: str) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest_name = clean_name("mtdc_" + Path(image_name).name)
    dest_path = UPLOAD_DIR / dest_name
    image_bytes = zip_file.read(image_name)
    dest_path.write_bytes(image_bytes)

    bbox_data = read_detection_label(zip_file, label_name)
    tassel_count = len(bbox_data["boxes"])
    relative_path = f"uploads/mtdc-demo/{dest_name}"
    file_size = len(image_bytes)

    with conn.cursor() as cur:
        cur.execute("SELECT image_id FROM images WHERE image_path = %s", (relative_path,))
        existing = cur.fetchone()
        if existing:
            image_id = existing["image_id"]
            cur.execute(
                """
                UPDATE images
                SET image_name = %s, status = 'completed', file_size = %s, access_level = 'public'
                WHERE image_id = %s
                """,
                (dest_name, file_size, image_id),
            )
            cur.execute("DELETE FROM detection_results WHERE image_id = %s", (image_id,))
        else:
            cur.execute(
                """
                INSERT INTO images (user_id, image_name, image_path, status, file_size, access_level)
                VALUES (1, %s, %s, 'completed', %s, 'public')
                RETURNING image_id
                """,
                (dest_name, relative_path, file_size),
            )
            image_id = cur.fetchone()["image_id"]

        upsert_image_file(cur, image_id, "original", dest_name, image_mime_type(dest_name), image_bytes)

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
            VALUES (%s, %s, %s, NULL, %s, %s::jsonb)
            RETURNING result_id
            """,
            (image_id, tassel_count, 0.92, round(1.5 + tassel_count / 120, 2), json.dumps(bbox_data)),
        )
        result_id = cur.fetchone()["result_id"]

    return {"image_id": image_id, "result_id": result_id, "image_name": dest_name, "tassel_count": tassel_count}


def upsert_dataset_log(conn, count: int) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT dataset_id FROM datasets WHERE dataset_name = %s", ("MTDC-UAV Demo Detection Set",))
        if cur.fetchone():
            cur.execute(
                """
                UPDATE datasets
                SET dataset_path = %s,
                    total_images = %s,
                    annotation_status = 'completed',
                    annotation_format = 'Pascal VOC XML'
                WHERE dataset_name = %s
                """,
                ("postgresql:image_files; backend/uploads/mtdc-demo", count, "MTDC-UAV Demo Detection Set"),
            )
        else:
            cur.execute(
                """
                INSERT INTO datasets (dataset_name, dataset_path, total_images, annotation_status, annotation_format)
                VALUES (%s, %s, %s, 'completed', 'Pascal VOC XML')
                """,
                ("MTDC-UAV Demo Detection Set", "postgresql:image_files; backend/uploads/mtdc-demo", count),
            )
        cur.execute(
            """
            INSERT INTO system_logs (user_id, action, details)
            VALUES (4, 'dataset_import', %s)
            """,
            (f"Imported {count} MTDC-UAV demo images with tassel bounding boxes",),
        )
        cur.execute(
            """
            WITH demo_results AS (
                SELECT
                    dr.result_id,
                    ROW_NUMBER() OVER (ORDER BY dr.result_id) - 1 AS offset_index
                FROM detection_results dr
                JOIN images i ON i.image_id = dr.image_id
                WHERE i.image_path LIKE 'uploads/mtdc-demo/%'
            )
            UPDATE detection_results dr
            SET created_at = TIMESTAMP '2026-06-14 09:00:00' + demo_results.offset_index * INTERVAL '10 minutes'
            FROM demo_results
            WHERE dr.result_id = demo_results.result_id
            """
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Import MTDC-UAV demo images into maize_detector.")
    parser.add_argument("--zip", default=str(DEFAULT_ZIP), help="Path to MTDC-UAV.zip")
    parser.add_argument("--limit", type=int, default=30, help="Number of detection images to import")
    args = parser.parse_args()

    zip_path = Path(args.zip)
    if not zip_path.exists():
        raise FileNotFoundError(f"Dataset zip not found: {zip_path}")

    config = db_config()
    if not config["password"]:
        raise RuntimeError("PGPASSWORD is required")

    with zipfile.ZipFile(zip_path) as zip_file:
        pairs = select_detection_pairs(zip_file, args.limit)
        if not pairs:
            raise RuntimeError("No detection image/XML pairs found in MTDC-UAV zip")

        imported = []
        with psycopg.connect(**config, row_factory=dict_row) as conn:
            ensure_image_files_table(conn)
            for image_name, label_name in pairs:
                imported.append(import_pair(conn, zip_file, image_name, label_name))
            upsert_dataset_log(conn, len(imported))
            conn.commit()

    print(json.dumps({"imported": imported, "total": len(imported)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
