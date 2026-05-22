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
);

CREATE INDEX IF NOT EXISTS idx_image_files_image ON image_files(image_id);
CREATE INDEX IF NOT EXISTS idx_image_files_type ON image_files(file_type);
