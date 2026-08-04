BEGIN;

-- Public prototype builds once shared one legacy password across demo users.
-- Disable only accounts that still retain that exact legacy hash. Accounts
-- whose owners changed their password are not affected.
UPDATE users
SET status = 'disabled',
    session_version = session_version + 1
WHERE password_hash = 'sha256$8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92';

COMMIT;
