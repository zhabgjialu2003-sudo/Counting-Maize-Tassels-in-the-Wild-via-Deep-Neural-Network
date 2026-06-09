-- Non-destructive PostgreSQL migration for the 30 User Stories.
-- Run this against an existing maize_detector database.

ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB;
ALTER TABLE images ADD COLUMN IF NOT EXISTS preprocessed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE images ADD COLUMN IF NOT EXISTS preprocessed_path VARCHAR(500);
ALTER TABLE image_files ADD COLUMN IF NOT EXISTS encrypted BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS quality_status VARCHAR(30) DEFAULT 'unreviewed';
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS review_note TEXT;

CREATE TABLE IF NOT EXISTS access_policies (
    policy_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    access_level VARCHAR(50) NOT NULL,
    updated_by INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fields (
    field_id SERIAL PRIMARY KEY,
    field_name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NOT NULL,
    baseline_count INTEGER NOT NULL DEFAULT 0,
    threshold_low INTEGER NOT NULL DEFAULT 0,
    latest_avg_count NUMERIC(8,2) DEFAULT 0,
    health_status VARCHAR(30) DEFAULT 'Healthy',
    anomaly_flag BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE fields ADD COLUMN IF NOT EXISTS anomaly_reason TEXT;

ALTER TABLE images ADD COLUMN IF NOT EXISTS field_id INTEGER REFERENCES fields(field_id);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    field_id INTEGER NOT NULL REFERENCES fields(field_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id),
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model_status') THEN
        CREATE TYPE model_status AS ENUM (
            'registered', 'training', 'trained', 'active', 'archived', 'failed'
        );
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'training_status') THEN
        CREATE TYPE training_status AS ENUM ('queued', 'running', 'completed', 'failed');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(150) NOT NULL,
    model_version VARCHAR(50) NOT NULL UNIQUE,
    weights_path VARCHAR(500) NOT NULL,
    status model_status DEFAULT 'registered',
    map50 NUMERIC(6,4),
    precision_score NUMERIC(6,4),
    recall_score NUMERIC(6,4),
    iou_threshold NUMERIC(4,2) DEFAULT 0.50,
    parent_model_id INTEGER REFERENCES models(model_id),
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_runs (
    run_id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES models(model_id),
    dataset_id INTEGER NOT NULL REFERENCES datasets(dataset_id),
    status training_status DEFAULT 'queued',
    hyperparameters JSONB NOT NULL,
    loss_curve JSONB,
    metrics JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

INSERT INTO access_policies (role_name, access_level)
VALUES
    ('Farmer', 'own_images'),
    ('Researcher', 'all_research_images'),
    ('Agronomist', 'aggregated_field_data'),
    ('Admin', 'full_access')
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO fields (
    field_name, location, baseline_count, threshold_low,
    latest_avg_count, health_status, anomaly_flag
)
SELECT *
FROM (VALUES
    ('Field A - North', 'North Region', 30, 20, 35::NUMERIC, 'Healthy', FALSE),
    ('Field B - East', 'East Region', 30, 20, 18::NUMERIC, 'At-Risk', TRUE),
    ('Field C - South', 'South Region', 40, 28, 42::NUMERIC, 'Healthy', FALSE)
) AS seed(field_name, location, baseline_count, threshold_low, latest_avg_count, health_status, anomaly_flag)
WHERE NOT EXISTS (SELECT 1 FROM fields);

INSERT INTO models (
    model_name, model_version, weights_path, status, map50,
    precision_score, recall_score, iou_threshold, changelog, activated_at
)
VALUES (
    'YOLO26s Tassel Detector', 'v1.0', 'backend/models/best.pt',
    'active', 0.899, 0.885, 0.803, 0.50,
    'Team-trained best.pt; validation mAP50-95=0.511', CURRENT_TIMESTAMP
)
ON CONFLICT (model_version) DO NOTHING;

INSERT INTO models (
    model_name, model_version, weights_path, status, map50,
    precision_score, recall_score, iou_threshold, changelog
)
VALUES (
    'Historical Baseline (Metrics Only)', 'v0.9',
    'backend/models/baseline-not-available.pt',
    'archived', 0.820, 0.790, 0.740, 0.50,
    'Comparison-only historical metrics; no deployable weights are stored.'
)
ON CONFLICT (model_version) DO NOTHING;
