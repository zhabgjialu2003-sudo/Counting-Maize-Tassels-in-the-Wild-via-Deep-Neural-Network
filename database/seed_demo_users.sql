-- ============================================================
-- Maize Detector App - Demo User Seed
-- FYP-26-S2-7 | Week 10
--
-- Purpose:
--   Add 100 stable demo accounts for role/login/Admin CRUD testing without
--   dropping existing project data.
--
-- Demo password:
--   Existing prototype bcrypt placeholders accept any password.
--   Newly registered accounts use a real SHA-256 hash through the backend.
-- ============================================================

INSERT INTO roles (role_name) VALUES
    ('Farmer'),
    ('Researcher'),
    ('Agronomist'),
    ('Admin')
ON CONFLICT (role_name) DO NOTHING;

WITH fixed_users(name, email, password_hash, role_name, status) AS (
    VALUES
        ('John Smith',   'john@farm.com',      '$2b$12$hash_placeholder_01', 'Farmer',     'active'::user_status),
        ('Dr. Li Wei',   'liwei@research.org', '$2b$12$hash_placeholder_02', 'Researcher', 'active'::user_status),
        ('Maria Garcia', 'maria@agro.com',     '$2b$12$hash_placeholder_03', 'Agronomist', 'active'::user_status),
        ('Admin User',   'admin@system.com',   '$2b$12$hash_placeholder_04', 'Admin',      'active'::user_status),
        ('Bob Brown',    'bob@farm.com',       '$2b$12$hash_placeholder_05', 'Farmer',     'disabled'::user_status)
),
generated_users AS (
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
        '$2b$12$hash_placeholder_demo_' || LPAD(n::TEXT, 3, '0') AS password_hash,
        CASE ((n - 1) % 5)
            WHEN 0 THEN 'Farmer'
            WHEN 1 THEN 'Researcher'
            WHEN 2 THEN 'Agronomist'
            WHEN 3 THEN 'Farmer'
            ELSE 'Farmer'
        END AS role_name,
        CASE WHEN n % 17 = 0 THEN 'disabled'::user_status ELSE 'active'::user_status END AS status
    FROM generate_series(1, 95) AS n
),
all_users AS (
    SELECT * FROM fixed_users
    UNION ALL
    SELECT * FROM generated_users
)
INSERT INTO users (name, email, password_hash, role_id, status)
SELECT u.name, u.email, u.password_hash, r.role_id, u.status
FROM all_users u
JOIN roles r ON r.role_name = u.role_name
ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

SELECT setval(pg_get_serial_sequence('users', 'user_id'), COALESCE((SELECT MAX(user_id) FROM users), 1), true);

SELECT
    r.role_name,
    COUNT(*) AS account_count
FROM users u
JOIN roles r ON r.role_id = u.role_id
GROUP BY r.role_name
ORDER BY r.role_name;
