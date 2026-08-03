# FYP-26-S2-7 Week 11 Demo Flow and Backup Plan

## Pre-Demo Startup

1. Start PostgreSQL and confirm the `maize_detector` database is available.
2. Run `python backend/server.py`.
3. Confirm the startup output reports PostgreSQL connected and `best.pt` loaded.
4. Serve the repository with `python -m http.server 8000`.
5. Open `http://localhost:8000/frontend/pages/login.html`.

The strict server exits when the database or trained model is unavailable. The
demo does not silently replace failed operations with fabricated results.

## Primary Demo Flow

| Step | Action | Evidence |
|---|---|---|
| 1 | Open the project website | Week 11 status, team, documentation, GitHub |
| 2 | Sign in as Farmer | Signed session and role-specific dashboard |
| 3 | Upload one or multiple JPG/PNG images | Validation, preview, progress, encrypted persistence |
| 4 | Run analysis | Real YOLO26s inference from `models/deployment/tassel-best.pt` |
| 5 | Open the result | Count, confidence, processing time, bounding boxes |
| 6 | Open history and export | PostgreSQL records, filtering, CSV/JSON export |
| 7 | Sign in as Researcher | Result review, model comparison, datasets, reports |
| 8 | Sign in as Agronomist | Health, growth, anomaly, multi-field, insights |
| 9 | Sign in as Admin | Users, secure storage, monitoring, datasets, permissions, backups |
| 10 | Open System page | Preprocess, train, evaluate, deploy, version workflows |

## Key Talking Points

- AI: the team's trained `best.pt` is loaded by Ultralytics for live inference.
- Database: PostgreSQL persists users, images, encrypted files, detections,
  reports, logs, datasets, fields, recommendations, models, and training runs.
- Traceability: 30 User Stories map to 30 BCE and 30 sequence diagrams.
- Security: signed authentication, role checks, encrypted image bytes, access
  policies, audit logging, and protected backup/restore operations.
- Validation: automated compliance tests plus live database/model smoke checks.

## Backup Evidence

If the live display fails, show evidence without claiming that a failed service
is working:

- screenshots in `docs/evidence/ui/`
- BCE and sequence diagrams in `docs/design/uml/`
- the User Story code guide
- the Week 11 compliance audit and test output
- sample annotated model results

## Final Checklist

- [ ] `python backend/server.py` starts without an error
- [ ] `/api/health` reports the database and model as ready
- [ ] all compliance tests pass
- [ ] each demo account can access only its permitted pages
- [ ] upload, inference, result persistence, history, and export work
- [ ] report generation creates a PostgreSQL record
- [ ] admin backup creation is tested
- [ ] browser viewport is tested at desktop and 375 px mobile width
- [ ] current Week 11 report and presentation describe real integration
- [ ] local changes are committed and pushed before the website is assessed

## Short Script

> Our Week 11 prototype is fully integrated. A role-authorized user uploads a
> maize image, the backend runs the team's trained YOLO26s `best.pt`, and the
> result is stored in PostgreSQL with encrypted image data. The interface then
> presents the count, confidence, processing time, bounding boxes, history, and
> export or reporting workflows. The implementation is traceable through all
> 30 User Stories in BCE order.
