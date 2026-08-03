# FYP-26-S2-7 User Stories

This repository implements the 30 user stories below. The detailed Boundary,
Control, Entity and sequence flows are defined in
`FYP-26-S2-7_BCE_Sequence_Diagrams.md`.

The frontend, backend, database, and AI code for each story is organized in
`FYP-26-S2-7_User_Story_Code_Guide.md`.

## Farmer

| ID | User story | Implementation evidence |
|---|---|---|
| A.1 | Upload maize images | `frontend/pages/upload.html`, `POST /api/upload`, `images` |
| A.2 | Automatically count tassels | `POST /api/predict`, `backend/inference.py`, `detection_results` |
| A.3 | View clear counting results | `frontend/pages/result.html`, `GET /api/results/<id>` |
| A.4 | See highlighted tassels | Result SVG bounding-box overlay and `bbox_data` |
| A.5 | Upload multiple images | Batch mode, progress display and sequential API processing |
| A.6 | Receive quick results | Fast 2560px inference mode plus SHA-256 result cache |
| A.7 | Use mobile devices | Responsive layout, 44px targets and rear-camera capture input |
| A.8 | Use an intuitive interface | Role dashboard, quick actions and server-validated session |

## Researcher

| ID | User story | Implementation evidence |
|---|---|---|
| B.1 | Obtain accurate results | Accurate SAHI mode, confidence, review status and flag endpoint |
| B.2 | Export standard formats | `frontend/pages/export.html` CSV/JSON selection and download |
| B.3 | Analyse historical data | Date/search/field filters, sorting and trend chart |
| B.4 | Compare model outputs | Two model selectors, test dataset/YAML and `POST /api/models/compare` |
| B.5 | Access raw datasets | Dataset list and authenticated ZIP download |
| B.6 | Generate visual reports | Field/date selection, persisted report charts and print-to-PDF |

## Agronomist

| ID | User story | Implementation evidence |
|---|---|---|
| C.1 | Evaluate plant health | Field health endpoint and persisted recommendations |
| C.2 | Monitor growth over time | Database-grouped weekly trend endpoint and chart |
| C.3 | Detect abnormal patterns | Threshold scan, persisted anomaly flags/reasons and review request |
| C.4 | View multiple fields | Region-filtered field grid |
| C.5 | Receive summarized insights | Insight endpoint, recommendation and text export |

## Admin

| ID | User story | Implementation evidence |
|---|---|---|
| D.1 | Manage user accounts | Authenticated user CRUD and soft disable |
| D.2 | Store images securely | Fernet-encrypted files, encrypted `image_files`, access policies |
| D.3 | Monitor system usage | Admin metrics and system log endpoints |
| D.4 | Manage datasets | Dataset package upload, edit, delete and list |
| D.5 | Control permissions | Signed tokens, server RBAC and per-user permission JSON |
| D.6 | Back up data regularly | 24-hour scheduler, `pg_dump`, history/logging and confirmed `psql` restore |

## System

| ID | User story | Implementation evidence |
|---|---|---|
| E.1 | Preprocess image data | Orientation, RGB conversion, resize and normalized JPEG pipeline |
| E.2 | Train deep learning models | Training notebooks, persisted runs and optional local Ultralytics worker |
| E.3 | Evaluate model performance | Stored notebook metrics or real `YOLO.val` evaluation |
| E.4 | Deploy model as a service | Weight loading, health check, active predictor switch and authenticated API |
| E.5 | Support updates | Model registration, parent version, changelog and deployment |

## Model Artifact

`models/deployment/tassel-best.pt` is the team's trained model result. It is the active
inference artifact and is never replaced by mock weights. Baseline models
without a repository weight file are labelled `metrics-only`.

The final validation output stored in `training/notebooks/tassel/maize_yolo26_final.ipynb` reports:
Precision `0.885`, Recall `0.803`, mAP@0.5 `0.899`, and mAP@0.5:0.95 `0.511`
over 55 validation images containing 2,210 instances.
