# Technical Manual

## Environment

Use Python 3.11 or 3.12, PostgreSQL, Git LFS, and the dependencies in
`backend/requirements.txt`. VS Code settings are committed under `.vscode/`.

## Local configuration

Copy `backend/.env.example` to `backend/.env` and configure:

- PostgreSQL host, port, database, user and password;
- a long random Flask `SECRET_KEY`;
- a Fernet `FILE_ENCRYPTION_KEY`;
- optional host, port, backup and CORS settings;
- optional `TASSEL_MODEL_PATH` and `DISEASE_MODEL_PATH` overrides.

The `.env` file is ignored by Git. Do not place real credentials in source,
documentation, tests or screenshots.

## Database initialization

```powershell
createdb -U postgres maize_detector
psql -U postgres -d maize_detector -f database\schema\schema_postgresql.sql
psql -U postgres -d maize_detector -f database\migrations\001_user_story_compliance.sql
psql -U postgres -d maize_detector -f database\migrations\002_disease_agronomist.sql
```

`database/schema/` creates a clean installation. `database/migrations/` updates
an existing installation without replacing user data. `database/seeds/` is for
deliberate local demonstration data.

## Runtime models

Run `git lfs pull` before starting the application. The default files are:

```text
models/deployment/tassel-best.pt
models/deployment/maize-disease.torchscript.pt
```

Model cards, metadata, provenance and checksums are stored in sibling task
directories under `models/`. Startup checks reject missing models and Git LFS
pointer files.

## Start and health checks

```powershell
python backend\server.py
```

Startup validates required security configuration, PostgreSQL connectivity and
the tassel model. `GET /api/health` reports database, tassel and disease service
status without exposing sensitive filesystem paths.

## Main API groups

| Group | Purpose |
|---|---|
| `/api/auth/*` | Login, session validation, profile and password management |
| `/api/upload` | Validate and persist uploaded images |
| `/api/predict` | Run tassel inference for a persisted image |
| `/api/agronomy/diagnose` | Run quality-aware leaf-disease screening |
| `/api/history*` | Retrieve authorized analysis history |
| `/api/reports*` and `/api/export*` | Research reporting and export |
| `/api/admin*` | Account and operational administration |
| `/api/system/status` | Model and system status for privileged roles |

## Security controls

- Passwords are stored as hashes.
- Tokens are signed and expire.
- Roles are checked on the server.
- SQL queries use parameters.
- Uploaded image content is encrypted at rest.
- File type, decoded image and size checks run before inference.
- Secrets and private uploads are excluded from Git.
- Disease responses apply confidence and out-of-distribution rejection.

## Testing

```powershell
python -m unittest discover -s tests -v
```

Database-dependent tests require PostgreSQL configuration in the current
process environment. The test suite covers authorization, encrypted storage,
upload validation, tassel route continuity, disease response contracts, mobile
PWA behaviour and account management.

## Maintenance

- Apply new database changes as ordered migration files.
- Register model replacements with a model card, metadata, metrics and SHA-256.
- Keep source and executed notebooks distinct.
- Update `docs/ASSESSMENT_INDEX.md` when evidence moves.
- Run structure, link, model and full regression checks before merging.
