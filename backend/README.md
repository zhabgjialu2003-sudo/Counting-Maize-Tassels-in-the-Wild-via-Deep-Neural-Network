# Maize Detector Backend

Flask, PostgreSQL, and YOLO26s backend for the Week 11 integrated prototype.

## Configuration

Copy `.env.example` to `.env` and configure:

- PostgreSQL connection values
- a long random `SECRET_KEY`
- a valid Fernet `FILE_ENCRYPTION_KEY`
- PostgreSQL command paths when they are not available on `PATH`

## Start

```powershell
python -m pip install -r backend/requirements.txt
python backend/server.py
```

The API runs at `http://localhost:5000`.

`server.py` requires both PostgreSQL and `models/best.pt` to load successfully.
It exits on startup failure instead of switching to fabricated data.

## Capabilities

- signed authentication and role-based authorization
- validated image and batch upload workflows
- real YOLO26s inference and persisted detection results
- encrypted original and annotated image storage
- history, export, report generation, field insights, and anomaly review
- user, permission, dataset, model, training, backup, and restore management
- health and system status endpoints for demo verification

The complete route-to-User-Story mapping is documented in
`docs/other/FYP-26-S2-7_User_Story_Code_Guide.md`.

## Verify

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

Backup and restore use `pg_dump`, `pg_restore`, and `psql`. Configure
`PG_DUMP_PATH`, `PG_RESTORE_PATH`, and `PSQL_PATH` when required.
