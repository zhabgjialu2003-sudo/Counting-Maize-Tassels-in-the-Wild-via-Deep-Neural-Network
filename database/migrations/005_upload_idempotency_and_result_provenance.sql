BEGIN;

ALTER TABLE images
    ADD COLUMN IF NOT EXISTS upload_idempotency_key VARCHAR(128);

ALTER TABLE detection_results
    ADD COLUMN IF NOT EXISTS model_id INTEGER REFERENCES models(model_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS model_version VARCHAR(50),
    ADD COLUMN IF NOT EXISTS inference_mode VARCHAR(20);

CREATE UNIQUE INDEX IF NOT EXISTS uq_images_user_upload_idempotency_key
    ON images (user_id, upload_idempotency_key)
    WHERE upload_idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_detection_results_model_id
    ON detection_results (model_id);

COMMIT;
