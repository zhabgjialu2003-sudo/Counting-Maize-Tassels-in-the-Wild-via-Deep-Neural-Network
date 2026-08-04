-- ============================================================
-- Maize Detector App -- PostgreSQL Schema (pgAdmin4)
-- FYP-26-S2-7 | Week 10
-- Run this entire file in pgAdmin4 Query Tool
-- ============================================================

-- 1. Drop existing types/tables (safe cleanup for re-run)
DROP TABLE IF EXISTS datasets       CASCADE;
DROP TABLE IF EXISTS training_runs  CASCADE;
DROP TABLE IF EXISTS models         CASCADE;
DROP TABLE IF EXISTS recommendations CASCADE;
DROP TABLE IF EXISTS fields         CASCADE;
DROP TABLE IF EXISTS access_policies CASCADE;
DROP TABLE IF EXISTS system_logs    CASCADE;
DROP TABLE IF EXISTS reports        CASCADE;
DROP TABLE IF EXISTS image_files    CASCADE;
DROP TABLE IF EXISTS detection_results CASCADE;
DROP TABLE IF EXISTS images         CASCADE;
DROP TABLE IF EXISTS users          CASCADE;
DROP TABLE IF EXISTS roles          CASCADE;
DROP TYPE  IF EXISTS user_status    CASCADE;
DROP TYPE  IF EXISTS report_type    CASCADE;
DROP TYPE  IF EXISTS annotation_status CASCADE;
DROP TYPE  IF EXISTS image_status   CASCADE;
DROP TYPE  IF EXISTS model_status   CASCADE;
DROP TYPE  IF EXISTS training_status CASCADE;

-- ============================================================
-- 2. Custom ENUM Types
-- ============================================================
CREATE TYPE user_status       AS ENUM ('active', 'disabled');
CREATE TYPE report_type       AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE annotation_status AS ENUM ('not_started', 'in_progress', 'completed');
CREATE TYPE image_status      AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE model_status      AS ENUM ('registered', 'training', 'trained', 'active', 'archived', 'failed');
CREATE TYPE training_status   AS ENUM ('queued', 'running', 'completed', 'failed');

-- ============================================================
-- 3. Tables (matching BCE Entities)
-- ============================================================

-- roles (D.1 Entity)
CREATE TABLE roles (
    role_id   SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE roles IS 'User roles: Farmer, Researcher, Agronomist, Admin, System';

-- users (A.7, D.1, D.5 Entity)
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id       INTEGER NOT NULL REFERENCES roles(role_id),
    status        user_status DEFAULT 'active',
    permissions   JSONB,
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE users IS 'System users across all roles';
CREATE INDEX idx_users_role   ON users(role_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_email  ON users(email);

-- images (A.1, A.5, D.2 Entity)
CREATE TABLE images (
    image_id    SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES users(user_id),
    image_name  VARCHAR(255) NOT NULL,
    image_path  VARCHAR(500) NOT NULL,
    upload_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    status      image_status DEFAULT 'pending',
    file_size   INTEGER,            -- bytes
    access_level VARCHAR(50) DEFAULT 'private',  -- D.2: secure storage access control
    preprocessed BOOLEAN NOT NULL DEFAULT FALSE,
    preprocessed_path VARCHAR(500)
);
COMMENT ON TABLE images IS 'Uploaded maize field images';
CREATE INDEX idx_images_user   ON images(user_id);
CREATE INDEX idx_images_status ON images(status);

-- detection_results (A.2, A.3, A.4, B.1, B.3, C.2 Entity)
-- Replaces both detection_results and history -- queried by created_at for timeline
CREATE TABLE detection_results (
    result_id             SERIAL PRIMARY KEY,
    image_id              INTEGER NOT NULL REFERENCES images(image_id),
    tassel_count          INTEGER NOT NULL DEFAULT 0,
    confidence_score      NUMERIC(5,4),       -- e.g. 0.8921
    annotated_image_path  VARCHAR(500),
    processing_time       NUMERIC(5,2),       -- seconds
    bbox_data             JSONB,              -- bounding boxes array
    quality_status        VARCHAR(30) DEFAULT 'unreviewed',
    review_note           TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE detection_results IS 'AI detection output -- also serves as history via created_at';
CREATE INDEX idx_detection_image  ON detection_results(image_id);
CREATE INDEX idx_detection_date   ON detection_results(created_at);
CREATE INDEX idx_detection_count  ON detection_results(tassel_count);

-- reports (B.5, C.5 Entity)
CREATE TABLE reports (
    report_id             SERIAL PRIMARY KEY,
    report_type           report_type NOT NULL,
    report_date           DATE NOT NULL,
    total_uploads         INTEGER DEFAULT 0,
    successful_detections INTEGER DEFAULT 0,
    failed_detections     INTEGER DEFAULT 0,
    average_tassel_count  NUMERIC(6,2),
    chart_data            JSONB,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE reports IS 'Daily/Weekly/Monthly aggregated system reports';
CREATE INDEX idx_reports_type_date ON reports(report_type, report_date);

-- system_logs (D.3, D.6 Entity)
CREATE TABLE system_logs (
    log_id     SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(user_id),
    action     VARCHAR(100) NOT NULL,
    details    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE system_logs IS 'Admin audit trail: user actions, backups, access changes';
CREATE INDEX idx_logs_user ON system_logs(user_id);
CREATE INDEX idx_logs_date ON system_logs(created_at);
CREATE INDEX idx_logs_action ON system_logs(action);

-- image_files (stores actual binary image data as bytea)
-- One image can have 0-2 file records: one 'original' + one 'annotated'
CREATE TABLE image_files (
    file_id    SERIAL PRIMARY KEY,
    image_id   INTEGER      NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
    file_type  VARCHAR(30)  NOT NULL CHECK (file_type IN ('original', 'annotated')),
    file_name  VARCHAR(255) NOT NULL,
    mime_type  VARCHAR(100) NOT NULL,
    file_size  INTEGER      NOT NULL,
    image_data BYTEA        NOT NULL,
    encrypted  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (image_id, file_type)
);
COMMENT ON TABLE image_files IS 'Binary image storage: original uploads and AI-annotated outputs';
CREATE INDEX idx_image_files_image ON image_files(image_id);
CREATE INDEX idx_image_files_type   ON image_files(file_type);

-- datasets (B.5, D.4 Entity)
CREATE TABLE datasets (
    dataset_id        SERIAL PRIMARY KEY,
    dataset_name      VARCHAR(255) NOT NULL,
    dataset_path      VARCHAR(500),
    total_images      INTEGER DEFAULT 0,
    annotation_status annotation_status DEFAULT 'not_started',
    annotation_format VARCHAR(50),          -- YOLO, COCO, Pascal VOC
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE datasets IS 'AI training datasets -- managed by Admin (D.4), accessed by Researcher (B.5)';

CREATE TABLE access_policies (
    policy_id    SERIAL PRIMARY KEY,
    role_name    VARCHAR(50) NOT NULL UNIQUE,
    access_level VARCHAR(50) NOT NULL,
    updated_by   INTEGER REFERENCES users(user_id),
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fields (
    field_id          SERIAL PRIMARY KEY,
    field_name        VARCHAR(150) NOT NULL,
    location          VARCHAR(150) NOT NULL,
    baseline_count    INTEGER NOT NULL DEFAULT 0,
    threshold_low     INTEGER NOT NULL DEFAULT 0,
    latest_avg_count  NUMERIC(8,2) DEFAULT 0,
    health_status     VARCHAR(30) DEFAULT 'Healthy',
    anomaly_flag      BOOLEAN DEFAULT FALSE,
    anomaly_reason    TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE images
    ADD COLUMN field_id INTEGER REFERENCES fields(field_id);

CREATE TABLE recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    field_id           INTEGER NOT NULL REFERENCES fields(field_id) ON DELETE CASCADE,
    user_id            INTEGER REFERENCES users(user_id),
    note               TEXT NOT NULL,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    model_id        SERIAL PRIMARY KEY,
    model_name      VARCHAR(150) NOT NULL,
    model_version   VARCHAR(50) NOT NULL UNIQUE,
    weights_path    VARCHAR(500) NOT NULL,
    status          model_status DEFAULT 'registered',
    map50           NUMERIC(6,4),
    precision_score NUMERIC(6,4),
    recall_score    NUMERIC(6,4),
    iou_threshold   NUMERIC(4,2) DEFAULT 0.50,
    parent_model_id INTEGER REFERENCES models(model_id),
    changelog       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at    TIMESTAMP
);

CREATE TABLE training_runs (
    run_id           SERIAL PRIMARY KEY,
    model_id         INTEGER NOT NULL REFERENCES models(model_id),
    dataset_id       INTEGER NOT NULL REFERENCES datasets(dataset_id),
    status           training_status DEFAULT 'queued',
    hyperparameters  JSONB NOT NULL,
    loss_curve       JSONB,
    metrics          JSONB,
    started_at       TIMESTAMP,
    completed_at     TIMESTAMP,
    error_message    TEXT
);

-- ============================================================
-- 4. Sample Data (matches Frontend MockData in js/api.js)
-- ============================================================

-- Roles
INSERT INTO roles (role_name) VALUES
    ('Farmer'),
    ('Researcher'),
    ('Agronomist'),
    ('Admin');

-- Users
-- The first five accounts are fixed demo logins. The generated rows bring
-- the table to exactly 100 stable accounts for Admin user-management demos.
INSERT INTO users (name, email, password_hash, role_id, status) VALUES
    ('John Smith',    'john@farm.com',        'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 1, 'active'),
    ('Dr. Li Wei',    'liwei@research.org',   'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 2, 'active'),
    ('Maria Garcia',  'maria@agro.com',       'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 3, 'active'),
    ('Admin User',    'admin@system.com',     'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 4, 'active'),
    ('Bob Brown',     'bob@farm.com',         'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 1, 'disabled');

INSERT INTO users (name, email, password_hash, role_id, status)
SELECT
    'Demo ' ||
    CASE ((n - 1) % 5)
        WHEN 0 THEN 'Farmer'
        WHEN 1 THEN 'Researcher'
        WHEN 2 THEN 'Agronomist'
        WHEN 3 THEN 'Farmer'
        ELSE 'Farmer'
    END || ' ' || LPAD(n::TEXT, 3, '0') AS name,
    LOWER(
        CASE ((n - 1) % 5)
            WHEN 0 THEN 'farmer'
            WHEN 1 THEN 'researcher'
            WHEN 2 THEN 'agronomist'
            WHEN 3 THEN 'farmer'
            ELSE 'farmer'
        END
    ) || LPAD(n::TEXT, 3, '0') || '@' ||
    CASE ((n - 1) % 5)
        WHEN 0 THEN 'farm.com'
        WHEN 1 THEN 'research.org'
        WHEN 2 THEN 'agro.com'
        WHEN 3 THEN 'farm.com'
        ELSE 'farm.com'
    END AS email,
    'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' AS password_hash,
    CASE ((n - 1) % 5)
        WHEN 0 THEN 1
        WHEN 1 THEN 2
        WHEN 2 THEN 3
        WHEN 3 THEN 1
        ELSE 1
    END AS role_id,
    CASE WHEN n % 17 = 0 THEN 'disabled'::user_status ELSE 'active'::user_status END AS status
FROM generate_series(1, 95) AS n;

-- Images (sample uploads)
INSERT INTO images (image_id, user_id, image_name, image_path, status, file_size) VALUES
    (1, 1, 'maize_field_01.jpg', '/storage/uploads/maize_field_01.jpg', 'completed', 2450000),
    (2, 1, 'maize_field_02.jpg', '/storage/uploads/maize_field_02.jpg', 'completed', 3120000),
    (3, 2, 'maize_field_03.jpg', '/storage/uploads/maize_field_03.jpg', 'completed', 1890000),
    (4, 1, 'maize_field_04.jpg', '/storage/uploads/maize_field_04.jpg', 'completed', 2780000),
    (5, 2, 'maize_field_05.jpg', '/storage/uploads/maize_field_05.jpg', 'completed', 3500000);

-- Detection Results (matching frontend MockData.results)
INSERT INTO detection_results (result_id, image_id, tassel_count, confidence_score, processing_time, bbox_data, created_at) VALUES
    (1, 1, 37, 0.89, 2.4, '[{"x":100,"y":60,"w":80,"h":80,"conf":0.92},{"x":250,"y":120,"w":80,"h":80,"conf":0.88},{"x":400,"y":80,"w":80,"h":80,"conf":0.85}]', '2026-06-10 10:30:00'),
    (2, 2, 42, 0.91, 2.1, '[{"x":120,"y":80,"w":80,"h":80,"conf":0.94},{"x":300,"y":100,"w":80,"h":80,"conf":0.91}]',                         '2026-06-11 14:15:00'),
    (3, 3, 29, 0.85, 3.0, '[{"x":90,"y":50,"w":80,"h":80,"conf":0.87},{"x":350,"y":180,"w":80,"h":80,"conf":0.82}]',                       '2026-06-12 09:00:00'),
    (4, 4, 35, 0.93, 1.8, '[{"x":150,"y":70,"w":80,"h":80,"conf":0.95},{"x":280,"y":140,"w":80,"h":80,"conf":0.92}]',                      '2026-06-13 11:45:00'),
    (5, 5, 31, 0.87, 2.6, '[{"x":110,"y":90,"w":80,"h":80,"conf":0.88},{"x":380,"y":160,"w":80,"h":80,"conf":0.84}]',                      '2026-06-13 16:20:00');

-- Reports
INSERT INTO reports (report_type, report_date, total_uploads, successful_detections, failed_detections, average_tassel_count) VALUES
    ('daily',   '2026-06-13', 24,  22,  2,  31),
    ('weekly',  '2026-06-13', 148, 139, 9,  33),
    ('monthly', '2026-06-01', 520, 496, 24, 34);

-- Datasets
INSERT INTO datasets (dataset_name, total_images, annotation_status, annotation_format) VALUES
    ('Maize Tassel Train v1',      200, 'completed',    'YOLO'),
    ('Maize Tassel Train v2',      500, 'in_progress',  'COCO'),
    ('Batch 3 - North Fields',     320, 'not_started',  NULL);

INSERT INTO access_policies (role_name, access_level, updated_by) VALUES
    ('Farmer', 'own_images', 4),
    ('Researcher', 'all_research_images', 4),
    ('Agronomist', 'aggregated_field_data', 4),
    ('Admin', 'full_access', 4);

INSERT INTO fields (field_name, location, baseline_count, threshold_low, latest_avg_count, health_status, anomaly_flag) VALUES
    ('Field A - North', 'North Region', 30, 20, 35, 'Healthy', FALSE),
    ('Field B - East', 'East Region', 30, 20, 18, 'At-Risk', TRUE),
    ('Field C - South', 'South Region', 40, 28, 42, 'Healthy', FALSE);

INSERT INTO models (
    model_name, model_version, weights_path, status, map50,
    precision_score, recall_score, iou_threshold, changelog, activated_at
) VALUES
    ('YOLO26s Tassel Detector', 'v1.0', 'models/deployment/tassel-best.pt', 'active', 0.899, 0.885, 0.803, 0.50, 'Team-trained best.pt; mAP50-95=0.511', CURRENT_TIMESTAMP),
    ('Baseline Model Record', 'v0.9', 'models/baseline-not-provided.pt', 'archived', NULL, NULL, NULL, 0.50, 'Awaiting a second trained weight file and evaluation record', NULL);

-- System Logs (sample admin actions)
INSERT INTO system_logs (user_id, action, details, created_at) VALUES
    (4, 'create_user',      'Created user: John Smith (role: Farmer)',  '2026-06-01 08:00:00'),
    (4, 'backup_created',   'Backup completed: 520MB',                  '2026-06-13 23:00:00'),
    (4, 'access_policy',    'Updated Farmer access level: own_images',  '2026-06-10 12:00:00'),
    (4, 'role_changed',     'User Bob Brown: Farmer -> Researcher',      '2026-06-08 15:30:00');

-- Keep SERIAL sequences aligned after explicit sample IDs.
SELECT setval(pg_get_serial_sequence('roles', 'role_id'), COALESCE((SELECT MAX(role_id) FROM roles), 1), true);
SELECT setval(pg_get_serial_sequence('users', 'user_id'), COALESCE((SELECT MAX(user_id) FROM users), 1), true);
SELECT setval(pg_get_serial_sequence('images', 'image_id'), COALESCE((SELECT MAX(image_id) FROM images), 1), true);
SELECT setval(pg_get_serial_sequence('detection_results', 'result_id'), COALESCE((SELECT MAX(result_id) FROM detection_results), 1), true);
SELECT setval(pg_get_serial_sequence('reports', 'report_id'), COALESCE((SELECT MAX(report_id) FROM reports), 1), true);
SELECT setval(pg_get_serial_sequence('datasets', 'dataset_id'), COALESCE((SELECT MAX(dataset_id) FROM datasets), 1), true);
SELECT setval(pg_get_serial_sequence('system_logs', 'log_id'), COALESCE((SELECT MAX(log_id) FROM system_logs), 1), true);

-- ============================================================
-- 5. Verify (run after execution to confirm)
-- ============================================================
SELECT 'roles'              AS table_name, COUNT(*) AS row_count FROM roles
UNION ALL SELECT 'users',              COUNT(*) FROM users
UNION ALL SELECT 'images',             COUNT(*) FROM images
UNION ALL SELECT 'detection_results',  COUNT(*) FROM detection_results
UNION ALL SELECT 'reports',            COUNT(*) FROM reports
UNION ALL SELECT 'datasets',           COUNT(*) FROM datasets
UNION ALL SELECT 'system_logs',        COUNT(*) FROM system_logs
ORDER BY table_name;

-- Quick query: recent detection history (matching frontend HistoryPage)
SELECT
    i.image_name,
    d.tassel_count,
    d.confidence_score,
    d.processing_time,
    d.created_at
FROM detection_results d
JOIN images i ON i.image_id = d.image_id
ORDER BY d.created_at DESC;

-- ============================================================
-- pgAdmin4 usage:
-- 1. Open pgAdmin4 and connect to your PostgreSQL server
-- 2. Right-click Databases -> Create -> Database, name it maize_detector
-- 3. Right-click maize_detector -> Query Tool
-- 4. Open this file and click Execute (F5) to run everything
-- 5. Refresh Schemas -> public -> Tables to see all 7 tables
-- ============================================================

-- Compatibility-first hardening fields (migration 003).
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS session_version BIGINT NOT NULL DEFAULT 1;

ALTER TABLE images
    ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
    ADD COLUMN IF NOT EXISTS content_sha256 CHAR(64),
    ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
    ADD COLUMN IF NOT EXISTS image_width INTEGER,
    ADD COLUMN IF NOT EXISTS image_height INTEGER,
    ADD COLUMN IF NOT EXISTS validated BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE fields
    ADD COLUMN IF NOT EXISTS owner_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

ALTER TABLE models
    ADD COLUMN IF NOT EXISTS artifact_sha256 CHAR(64),
    ADD COLUMN IF NOT EXISTS artifact_validated_at TIMESTAMP;

-- Retry-safe uploads and auditable inference provenance (migration 005).
ALTER TABLE images
    ADD COLUMN IF NOT EXISTS upload_idempotency_key VARCHAR(128);

ALTER TABLE detection_results
    ADD COLUMN IF NOT EXISTS model_id INTEGER REFERENCES models(model_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS model_version VARCHAR(50),
    ADD COLUMN IF NOT EXISTS inference_mode VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_images_content_sha256 ON images(content_sha256);
CREATE INDEX IF NOT EXISTS idx_fields_owner_user_id ON fields(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_models_active_status ON models(status) WHERE status = 'active';
CREATE UNIQUE INDEX IF NOT EXISTS uq_images_user_upload_idempotency_key
    ON images (user_id, upload_idempotency_key)
    WHERE upload_idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_detection_results_model_id ON detection_results(model_id);

CREATE TABLE IF NOT EXISTS field_assignments (
    field_id INTEGER NOT NULL REFERENCES fields(field_id) ON DELETE CASCADE,
    agronomist_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (field_id, agronomist_user_id)
);

CREATE INDEX IF NOT EXISTS idx_field_assignments_agronomist
    ON field_assignments (agronomist_user_id, field_id);
