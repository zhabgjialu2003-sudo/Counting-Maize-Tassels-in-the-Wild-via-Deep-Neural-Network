BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_images_content_sha256 ON images(content_sha256);
CREATE INDEX IF NOT EXISTS idx_fields_owner_user_id ON fields(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_models_active_status ON models(status) WHERE status = 'active';

COMMIT;
