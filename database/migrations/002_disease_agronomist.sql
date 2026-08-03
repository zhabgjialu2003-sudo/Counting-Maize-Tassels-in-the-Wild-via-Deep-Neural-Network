-- Human-centred maize leaf-disease assistance.
-- Safe to run repeatedly after schema_postgresql.sql.

BEGIN;

CREATE TABLE IF NOT EXISTS disease_diagnoses (
    diagnosis_id        BIGSERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(user_id),
    field_id            INTEGER REFERENCES fields(field_id) ON DELETE SET NULL,
    image_id            INTEGER REFERENCES images(image_id) ON DELETE SET NULL,
    model_version       VARCHAR(100),
    knowledge_version   VARCHAR(50) NOT NULL,
    status              VARCHAR(30) NOT NULL CHECK (
        status IN ('supported', 'uncertain', 'retake_required', 'unsupported')
    ),
    predicted_condition VARCHAR(80),
    confidence          NUMERIC(8,7),
    entropy             NUMERIC(8,7),
    rejection_reason    VARCHAR(100),
    quality_findings    JSONB NOT NULL DEFAULT '{}'::jsonb,
    context_data        JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_data       JSONB NOT NULL,
    reviewer_user_id    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    reviewer_decision   VARCHAR(30) CHECK (
        reviewer_decision IS NULL
        OR reviewer_decision IN ('confirmed', 'corrected', 'inconclusive')
    ),
    reviewed_condition  VARCHAR(80),
    reviewer_note       TEXT,
    reviewed_at         TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE disease_diagnoses
    ADD COLUMN IF NOT EXISTS reviewed_condition VARCHAR(80);

CREATE INDEX IF NOT EXISTS idx_disease_diagnoses_user_date
    ON disease_diagnoses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_disease_diagnoses_field_date
    ON disease_diagnoses(field_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_disease_diagnoses_status
    ON disease_diagnoses(status);

COMMENT ON TABLE disease_diagnoses IS
    'Versioned maize leaf-disease screening results and agronomist review trail';
COMMENT ON COLUMN disease_diagnoses.response_data IS
    'Complete bilingual-ready structured response; display language is stored inside the JSON';
COMMENT ON COLUMN disease_diagnoses.confidence IS
    'Calibrated model confidence; never equivalent to a confirmed diagnosis';

COMMIT;
