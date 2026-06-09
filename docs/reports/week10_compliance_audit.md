# Week 10 User Story Compliance Audit

Date: 2026-06-10

Project: FYP-26-S2-7, Counting Maize Tassels in the Wild via Deep Neural Network

Scope excludes the final-submission folder and AI PDF, as requested.

## Result

All 30 user stories (A.1-E.5) have an implemented frontend flow, protected API,
and supporting data/model contract. The detailed story-by-story mapping is in
`docs/other/FYP-26-S2-7_User_Stories.md`.

| Area | Implemented evidence | Status |
|---|---|---|
| Farmer A.1-A.8 | Camera/batch upload, real prediction, result/boxes, history, responsive UI | Complete |
| Researcher B.1-B.6 | Metrics, export, trends, model comparison, dataset ZIP, printable reports | Complete |
| Agronomist C.1-C.5 | Field health, recommendations, growth, anomaly review, summarized insights | Complete |
| Admin D.1-D.6 | Users, encrypted storage, monitoring, dataset packages, permissions, backup/restore | Complete |
| AI System E.1-E.5 | Preprocess, training-run registry, evaluation metrics, deployment, version registry | Complete |

## Model Evidence

The deployed artifact is `backend/models/best.pt`, trained by the project owner.
The final notebook metrics recorded in the system are:

- Precision: 0.885
- Recall: 0.803
- mAP50: 0.899
- mAP50-95: 0.511
- Validation set: 55 images, 2,210 instances

The API exposes fast and accurate inference modes. A local benchmark on
`DJI_0243 (2).JPG` produced 123 detections in about 1.47 seconds in fast mode;
accurate tiled inference produced 278 detections in about 49.45 seconds.

## Security And Database

- Signed, expiring bearer tokens
- Role and permission checks on protected routes
- Scrypt password hashing with legacy hash migration support
- Fernet encryption for uploaded image storage
- Authenticated image retrieval
- PostgreSQL entities for fields, recommendations, models, training runs,
  access policies, review status, encrypted image files, reports, and logs
- Non-destructive upgrade script:
  `database/migrate_user_story_compliance.sql`

The non-destructive migration was applied successfully to the live
`maize_detector` database on 2026-06-09. A custom-format backup was created
before migration at
`backend/backups/maize_detector-before-compliance-20260609-205247.dump`.

## Verification

- 15 backend compliance tests: pass
- Production runtime contains no MockData or mock-success fallback
- Python compile checks: pass
- All frontend inline JavaScript parse checks: pass
- Flask application import and 48-route registration: pass
- Real `best.pt` load and inference: pass
- Live PostgreSQL migration and API smoke checks: pass
- Browser checks for Farmer, Researcher, Agronomist, Admin, and AI System: pass
- BCE tab order A.1-E.5 and report-generation workflow: pass
- Git diff whitespace validation: pass

## Excluded Deliverables

Per the project owner's instruction, this audit does not require or assess:

- Final submission folder packaging
- AI progress PDF
