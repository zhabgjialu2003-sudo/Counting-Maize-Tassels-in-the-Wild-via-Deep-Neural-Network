BEGIN;

ALTER TABLE disease_diagnoses
    ADD COLUMN IF NOT EXISTS review_status VARCHAR(30) NOT NULL DEFAULT 'not_requested',
    ADD COLUMN IF NOT EXISTS review_requested_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS review_request_reason TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'disease_diagnoses_review_status_check'
          AND conrelid = 'disease_diagnoses'::regclass
    ) THEN
        ALTER TABLE disease_diagnoses
            ADD CONSTRAINT disease_diagnoses_review_status_check
            CHECK (
                review_status IN (
                    'not_requested',
                    'requested',
                    'in_review',
                    'reviewed'
                )
            );
    END IF;
END
$$;

UPDATE disease_diagnoses
SET review_status = 'reviewed'
WHERE reviewed_at IS NOT NULL
  AND review_status <> 'reviewed';

CREATE INDEX IF NOT EXISTS idx_disease_diagnoses_review_queue
    ON disease_diagnoses (field_id, review_status, review_requested_at DESC);

COMMIT;
