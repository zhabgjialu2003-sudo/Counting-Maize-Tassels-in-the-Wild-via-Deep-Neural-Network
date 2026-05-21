# Maize Detector Backend

Flask backend for the Week 10 Maize Detector prototype.

## Run Locally

```powershell
cd backend
python -m pip install -r requirements.txt
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="maize_detector"
$env:PGUSER="postgres"
$env:PGPASSWORD="your-postgres-password"
python app.py
```

The API runs at:

```text
http://localhost:5000
```

## Main Endpoints

- `GET /api/health`
- `POST /api/upload` - accepts JPG/PNG files only
- `POST /api/predict`
- `GET /api/history`
- `GET /api/stats`
- `GET /api/report/daily`
- `GET /api/report/weekly`
- `GET /api/report/monthly`
- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/<user_id>`
- `DELETE /api/users/<user_id>` - disables the user to preserve database history
- `GET /api/datasets`
- `GET /api/logs`
- `GET /api/fields`
- `GET /api/backup`
- `POST /api/backup`

If PostgreSQL is unavailable, the backend falls back to mock data so the prototype remains demonstrable.

`POST /api/backup` uses `pg_dump`. If PostgreSQL is not on `PATH`, set `PG_DUMP_PATH` to the full `pg_dump.exe` path.
