# BCE and Sequence Compliance Audit

Date: 2026-06-10

Review order: A.1-A.8, B.1-B.6, C.1-C.5, D.1-D.6, E.1-E.5.

The implementation follows each diagram as `Actor -> Boundary -> Control ->
Entity -> Control -> Boundary`. Frontend tabs for Agronomist, Admin, and System
are also displayed in BCE number order.

| BCE | Sequence | Boundary | Control/API | Entity | Result |
|---|---|---|---|---|---|
| A.1 | F.1 | `upload.html` select, preview, submit | `POST /api/upload` validates and binds current user | `images`, encrypted `image_files` | Complete |
| A.2 | F.2 | Upload Analyze/progress | `POST /api/predict`, preprocess and YOLO count | `detection_results` | Complete |
| A.3 | F.3 | `result.html` count/confidence/time | `GET /api/results/<id>` | `detection_results` | Complete |
| A.4 | F.4 | Original/annotated toggle | result detail and authenticated image file APIs | bbox JSON, image paths | Complete |
| A.5 | F.5 | Multiple selection and batch progress | sequential validated upload/detection | image status/results | Complete |
| A.6 | F.6 | estimate, loading, processing time | fast mode and SHA-256 cache | processing time/result cache | Complete |
| A.7 | F.7 | responsive camera/gallery input | mobile upload and detection API | detection result | Complete |
| A.8 | F.8 | dashboard quick actions/cards/nav | signed session and `GET /api/auth/me` | `users` | Complete |
| B.1 | G.1 | result quality and flag action | accurate mode, thresholded YOLO, flag API | quality/review fields | Complete |
| B.2 | G.2 | record selection, date range, CSV/JSON | browser export controller and escaped CSV | detection records | Complete |
| B.3 | G.3 | date/field filters, sort, trend | `/api/history` accepts matching filters/order | detection history | Complete |
| B.4 | G.4 | two models, dataset, optional YAML | `/api/models/compare` compares stored or shared validation outputs | `models` metrics | Complete |
| B.5 | G.5 | dataset and ZIP/TAR choice | authenticated package generator | `datasets` and package files | Complete |
| B.6 | G.6 | fields/date/type, charts, PDF | `POST /api/reports` queries, aggregates and saves | `reports` | Complete |
| C.1 | H.1 | field health and recommendation note | health evaluation and recommendation API | `fields`, `recommendations` | Complete |
| C.2 | H.2 | field/period growth chart | weekly database aggregation | `detection_results` | Complete |
| C.3 | H.3 | anomaly scan and request review | scan, compare threshold, persist reason | `fields.anomaly_flag` | Complete |
| C.4 | H.4 | multi-field grid and region filter | server-side region summary | `fields` | Complete |
| C.5 | H.5 | insights, advice, export | 30-day aggregate and summary | detection results/fields | Complete |
| D.1 | I.1 | users table and forms | user CRUD, validation, password hashing | `users` | Complete |
| D.2 | I.2 | storage status/access policy | encrypted storage, policy application, access audit | images/files/policies/logs | Complete |
| D.3 | I.3 | active users, queue, uptime, errors | database/log-derived metrics | `system_logs` | Complete |
| D.4 | I.4 | dataset list/upload/edit/delete | validated dataset CRUD | `datasets` | Complete |
| D.5 | I.5 | user, role and permission matrix | read permissions, protect own Admin, update role then permissions | `users.permissions` | Complete |
| D.6 | I.6 | backup history/create/restore | pg_dump, scheduler, psql restore and logging | backup files/system logs | Complete |
| E.1 | J.1 | preprocessing controls/progress | resize, normalize, optional augment, encrypted save | image preprocessing state | Complete |
| E.2 | J.2 | model/dataset/hyperparameters | queued or local Ultralytics training worker | `training_runs`, `models` | Complete |
| E.3 | J.3 | metrics table/evaluate action | stored metrics or real `YOLO.val` | model metrics | Complete |
| E.4 | J.4 | deploy version action | load weights, health check, activate/archive | model status and live predictor | Complete |
| E.5 | J.5 | version, path, parent, changelog | model registration and deployment workflow | versioned `models` | Complete |

## Important Model Constraint

`backend/models/best.pt` is the real deployable model. The historical v0.9
baseline is metrics-only. A real shared-validation comparison requires a second
weights artifact; the API rejects that mode when weights are unavailable rather
than fabricating predictions.

## Final Verification

- 15 compliance tests pass.
- Production API and pages use PostgreSQL and `best.pt` without MockData fallback.
- The application registers 48 API routes.
- Live PostgreSQL schema migration and role-based API smoke checks pass.
- Browser verification confirms the BCE sections are displayed in A-E order.
- Researcher report generation persists a report and renders its summary/chart.
- The final-submission folder and AI PDF remain excluded as requested.
