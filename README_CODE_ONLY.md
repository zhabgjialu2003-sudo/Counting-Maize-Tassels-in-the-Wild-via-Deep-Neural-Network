# Code-only Runtime

This folder contains the files required to run and verify the application:

- `backend/`: Flask API, database access, authorization, tassel inference,
  leaf-disease screening, and both deployed models;
- `frontend/`: desktop interface and bilingual mobile PWA;
- `database/`: PostgreSQL schema and migrations;
- `tests/`: automated regression tests;
- root entry points, dependency guidance, and safe configuration examples.

Training datasets, historical uploads, course-submission artefacts, screenshots,
caches, and local secrets are intentionally excluded. Model files are retained
because they are required to reproduce the same runtime behaviour.

## Run

Python 3.11 or 3.12 is recommended. Configure PostgreSQL, `SECRET_KEY`, and
`FILE_ENCRYPTION_KEY` through local environment variables. Never commit real
passwords or encryption keys.

```powershell
python -m pip install -r backend/requirements.txt
python backend/server.py
```

Open:

```text
http://127.0.0.1:5000/frontend/pages/login.html
```

## Verify

```powershell
python -m unittest discover -s tests -v
```

The completed verification run passed all **44/44 tests**. The deployed model
hashes match the validated training artefacts, so the same model files,
thresholds, environment, and input images reproduce the same inference path.
