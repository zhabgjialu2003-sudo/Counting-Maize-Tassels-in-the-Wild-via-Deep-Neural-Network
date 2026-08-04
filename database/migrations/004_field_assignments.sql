BEGIN;

CREATE TABLE IF NOT EXISTS field_assignments (
    field_id INTEGER NOT NULL REFERENCES fields(field_id) ON DELETE CASCADE,
    agronomist_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (field_id, agronomist_user_id)
);

CREATE INDEX IF NOT EXISTS idx_field_assignments_agronomist
    ON field_assignments (agronomist_user_id, field_id);

-- Preserve the existing prototype workflow by assigning legacy fields to the
-- earliest active Agronomist. Future assignments are managed explicitly.
INSERT INTO field_assignments (field_id, agronomist_user_id)
SELECT f.field_id, agronomist.user_id
FROM fields f
CROSS JOIN LATERAL (
    SELECT u.user_id
    FROM users u
    JOIN roles r ON r.role_id = u.role_id
    WHERE r.role_name = 'Agronomist' AND u.status = 'active'
    ORDER BY u.user_id
    LIMIT 1
) agronomist
ON CONFLICT DO NOTHING;

COMMIT;
