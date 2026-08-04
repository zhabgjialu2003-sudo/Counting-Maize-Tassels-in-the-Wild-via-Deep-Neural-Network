# Contributing

This repository is an assessed final-year project. Contributions must preserve
reproducibility, privacy, model provenance, and the traceability between user
stories, code, tests, and technical documentation.

## Development setup

1. Install Git LFS and materialize the deployment models with `git lfs pull`.
2. Use Python 3.11 or 3.12 in a local virtual environment.
3. Install `backend/requirements.txt`.
4. Copy `backend/.env.example` to `backend/.env` and provide local secrets.
5. Create PostgreSQL database `maize_detector`, apply
   `database/schema/schema_postgresql.sql`, and run `python -m backend.migrations`.

Never commit `.env`, database dumps, farmer uploads, private datasets, access
tokens, passwords, or encryption keys.

## Branch and commit conventions

- Create a focused branch from the current `main` branch.
- Use Conventional Commits, for example `fix(upload): preserve retry intent`.
- Keep commits small enough to review and explain why the change is needed.
- Do not rewrite another contributor's authorship.
- Do not add AI co-author trailers or claim that generated work was authored by
  a person who did not review it.

## Required verification

Before opening a pull request, run:

```powershell
python -m py_compile backend\app.py backend\migrations.py
node --check frontend\js\api.js
python -m backend.migrations --check
python -m unittest discover -s tests -v
```

Changes to schema or persistent entities require a new ordered migration.
Never edit an already applied migration. Changes to a user-facing workflow must
update its automated test or explain the manual acceptance evidence.

## Pull requests

Complete the repository pull request template. A pull request must identify:

- the affected user story or system requirement;
- security, privacy, data, model, and migration impact;
- commands used for verification;
- documentation or diagrams updated; and
- any acceptance step that still requires manual hardware, long-running
  training, or an external service.

Large model files belong under `models/deployment/` and must use Git LFS. Dataset
archives are not accepted without redistribution permission and provenance.
