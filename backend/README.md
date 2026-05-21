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
- `POST /api/upload`
- `POST /api/predict`
- `GET /api/history`
- `GET /api/stats`
- `GET /api/report/daily`
- `GET /api/report/weekly`
- `GET /api/report/monthly`
- `GET /api/users`
- `GET /api/datasets`
- `GET /api/logs`
- `GET /api/fields`

If PostgreSQL is unavailable, the backend falls back to mock data so the prototype remains demonstrable.
