# User Story Extensions

These stories are additions to the unchanged 30-story baseline in `user-stories.md`. They describe the bilingual disease-assistance, privacy, operational-safety, and deployment controls implemented after the baseline was approved.

## Farmer

### A.9 Bilingual Leaf Screening

**User Story:** As a farmer, I want to screen a maize leaf photo in English or Chinese, so that I can understand visible disease-like signs and decide what to do next.

**Description:** The Farmer may upload a validated maize leaf image and optional field context. The system must communicate observations, uncertainty, retake guidance, and safe next steps without presenting the output as a confirmed diagnosis.

**Acceptance Criteria:**

1. Given an authenticated Farmer and a valid leaf image, when screening succeeds, then the response contains a status, headline, observations, possible condition, confidence band, next steps, safety note, and selected language.
2. Given a dark, blurred, or undersized image, when the quality gate fails, then the system asks for a better photo instead of inventing a condition.
3. Given Chinese is selected, when the result is displayed, then all farmer-facing guidance is returned in Simplified Chinese while technical codes remain stable.

**BCE:** Boundary - Mobile/Web Leaf Assistant; Control - Disease Assistance and Advice Controls; Entity - Image and Disease Diagnosis.

### A.10 Secure Account Maintenance

**User Story:** As a farmer, I want to change my email address or password securely, so that I can keep access when my contact details change.

**Description:** Email is the only account contact identifier. Profile and password changes require the current password and invalidate previously issued sessions.

**Acceptance Criteria:**

1. A duplicate or malformed email is rejected without changing the account.
2. A new password must satisfy policy, match its confirmation, and differ from the current password.
3. After a successful email or password change, the old access token is rejected.

**BCE:** Boundary - Account Page; Control - Authentication and Session Control; Entity - User.

### A.11 Resilient Field Upload

**User Story:** As a farmer using mobile data, I want clear upload progress and recoverable errors, so that an interrupted 4G/5G connection does not make me lose track of my work.

**Description:** The interface shows compression/upload progress, preserves the current screen after network failure, and supports a deliberate retry without silently creating duplicate records.

**Acceptance Criteria:**

1. Upload progress and compressed size are visible before analysis begins.
2. A network interruption produces a human-readable retry message and does not log the Farmer out.
3. Repeated original filenames are isolated by UUID and content digest.

**BCE:** Boundary - Mobile Upload Page; Control - Upload Validation Control; Entity - Image and Image File.

## Researcher

### B.7 Review Uncertainty and Provenance

**User Story:** As a researcher, I want model identity, confidence, uncertainty, and quality metadata with each result, so that I can judge whether a record is suitable for analysis.

**Description:** Each result exposes stable scientific provenance without revealing internal server paths. Researchers can distinguish model evidence, quality findings, inference mode, and human review state before including a record in analysis.

**Acceptance Criteria:** Results identify the model version, inference mode, confidence, quality state, and review status; internal server paths are never exposed.

**BCE:** Boundary - Research Dashboard; Control - Inference Control; Entity - Detection Result, Disease Diagnosis, and Model.

### B.8 Controlled Dataset Retrieval

**User Story:** As a researcher, I want approved datasets exported with a manifest, so that I can reproduce analysis without accessing arbitrary server files.

**Description:** Dataset retrieval is permission-controlled and restricted to configured storage roots. Each generated archive includes metadata that identifies the selected dataset and supports reproducible downstream work.

**Acceptance Criteria:** Only authorized roles with `datasets:download` may export; source paths must remain inside configured dataset roots; ZIP/TAR output includes a dataset manifest; oversized source files are excluded.

**BCE:** Boundary - Dataset Page; Control - Dataset Export Control; Entity - Dataset and System Log.

### B.9 Reproducible Model Evaluation

**User Story:** As a researcher, I want evaluation to use an integrity-checked model and approved dataset YAML, so that reported metrics are tied to a reproducible artifact.

**Description:** Evaluation is allowed only when both the registered model artifact and dataset configuration remain inside their approved trust boundaries. Stored metrics therefore remain connected to a validated model version and input definition.

**Acceptance Criteria:** Model paths are allowlisted, artifact SHA-256 is checked when recorded, dataset YAML must be inside approved roots, and mAP/precision/recall are persisted with the registered model.

**BCE:** Boundary - Model Evaluation Page; Control - Model Governance; Entity - Model, Dataset, and Training Run.

## Agronomist

### C.6 Review Assigned Field Evidence

**User Story:** As an agronomist, I want to view leaf-screening evidence only for fields assigned to me, so that I can support farmers without seeing unrelated private images.

**Description:** Field Assignment is the explicit authorization link between an Agronomist and agricultural evidence. The same scope is applied to field lists, summaries, diagnoses, review actions, and protected image retrieval.

**Acceptance Criteria:** The field list, diagnosis history, aggregate insight, and image access are filtered through Field Assignment; an unassigned field returns a forbidden response; Admin retains full access.

**BCE:** Boundary - Agronomist Dashboard; Control - Field Assignment and Review Control; Entity - Field Assignment, Image, and Disease Diagnosis.

### C.7 Confirm or Correct Screening

**User Story:** As an agronomist, I want to confirm, correct, or mark a disease screening inconclusive, so that the farmer-facing record includes accountable expert review.

**Description:** Expert review never overwrites the original model evidence. It adds a named reviewer decision, reviewed condition where applicable, note, and timestamp so the automated and human interpretations remain traceable.

**Acceptance Criteria:** A review requires an allowed decision and note; corrections require a supported condition or `other`; reviewer identity and time are persisted; the action is audited.

**BCE:** Boundary - Diagnosis Review Panel; Control - Review Control; Entity - Disease Diagnosis and System Log.

### C.8 Context-Aware Human Guidance

**User Story:** As an agronomist, I want the system to keep field context separate from model evidence, so that advice is useful without overstating diagnostic certainty.

**Description:** Farmer-provided crop stage, weather, and spread information enriches the explanation but is stored separately from raw probabilities and quality measurements. This preserves scientific clarity and prevents context from leaking between requests.

**Acceptance Criteria:** Crop stage, recent weather, and symptom spread are stored as context; model probabilities remain technical evidence; wording explicitly states that screening is not a confirmed diagnosis; request context never leaks into another user's response.

**BCE:** Boundary - Leaf Assistant; Control - Advice Engine; Entity - Disease Diagnosis.

## Admin

### D.7 Assign Agronomists to Fields

**User Story:** As an admin, I want to assign or remove Agronomists from fields, so that evidence access follows operational responsibility.

**Description:** The Admin maintains a many-to-many assignment boundary between active Agronomists and fields. Assignment changes are idempotent, auditable, and immediately reflected by server-side authorization.

**Acceptance Criteria:** Only Admin can manage assignments; only active Agronomist accounts can be assigned; assignments are unique per field/user pair; changes are audited.

**BCE:** Boundary - Admin Console; Control - Field Assignment Control; Entity - User, Field, Field Assignment, and System Log.

### D.8 Revoke Stale Sessions

**User Story:** As an admin, I want role, status, permission, email, and password changes to invalidate old sessions, so that revoked access cannot continue until token expiry.

**Description:** Tokens carry only stable identity and a session version. Every protected request reloads current account state and rejects a token when the database version, role, permission, or active status no longer authorizes access.

**Acceptance Criteria:** Every protected request reloads current account state; disabled accounts and session-version mismatches are rejected; tokens are accepted only from the Authorization header by default.

**BCE:** Boundary - Admin/User Account Pages; Control - Authentication and Session Control; Entity - User and Role.

### D.9 Govern Storage and Deployment

**User Story:** As an admin, I want uploaded images, model artifacts, migrations, and background workloads governed by explicit limits, so that the service remains auditable and stable.

**Description:** Administrative governance covers the complete evidence and model lifecycle: validated encrypted storage, allowlisted artifacts, checksum-tracked schema changes, bounded workers, rate limits, safe errors, and operational audit logs.

**Acceptance Criteria:** Image content is validated and encrypted; model paths and digests are verified; migrations are checksummed; rate limits and bounded workers are active; public errors do not expose internal exception details.

**BCE:** Boundary - Admin/System Console; Control - Upload, Model, Migration, and Rate Controls; Entity - Image File, Model, Schema Migration, and System Log.

## System

### E.6 Validate and Isolate Every Upload

**User Story:** As a system, I want to validate actual image content and assign collision-resistant storage names, so that unsafe or duplicate filenames cannot corrupt another user's data.

**Description:** The server distrusts filenames and client content types. It decodes supported formats, enforces byte and pixel limits, generates a UUID storage name, records the original name and digest, and encrypts the validated bytes.

**Acceptance Criteria:** Byte, MIME, decode, dimension, and pixel limits are enforced; server names use UUIDs; SHA-256 and original names are recorded; encrypted database bytes decrypt to the validated original.

**BCE:** Boundary - Upload API; Control - Image Validation Control; Entity - Image and Image File.

### E.7 Operate Dual AI Pipelines Safely

**User Story:** As a system, I want tassel counting and leaf screening to run as separate governed pipelines, so that each task returns appropriate evidence and neither silently substitutes fabricated output.

**Description:** Each AI task has its own model contract, output schema, quality controls, and persistence entity. A missing or invalid model produces a controlled unavailable state instead of a fabricated result.

**Acceptance Criteria:** Tassel inference returns count/boxes; disease inference returns calibrated status/quality/uncertainty; missing artifacts return a controlled unavailable response; no production mock fallback is permitted.

**BCE:** Boundary - Prediction APIs; Control - Tassel and Disease Inference Controls; Entity - Model, Detection Result, and Disease Diagnosis.

### E.8 Bound Resources and Apply Reproducible Migrations

**User Story:** As a system, I want bounded caches, bounded training queues, rate limits, and tracked database migrations, so that load and schema changes remain controlled.

**Description:** Expensive work has explicit capacity and concurrency boundaries. Database migrations are numbered, checksummed, and serialized under an advisory lock so repeated startup is safe and altered applied files are detected.

**Acceptance Criteria:** Inference cache size is configurable and uses content/model identity; model access is lock-protected; local training rejects excess pending work; migration names/checksums are recorded and altered applied files are rejected; Waitress uses a bounded thread pool.

**BCE:** Boundary - Health/Startup Interfaces; Control - Workload and Migration Controls; Entity - Training Run, Model, Schema Migration, and System Log.

## Extension Traceability Summary

| Story | Primary API or component | Automated evidence |
|---|---|---|
| A.9 | `POST /api/agronomy/diagnose` | `test_disease_assistant.py` |
| A.10 | `/api/auth/profile`, `/api/auth/change-password` | `test_farmer_account.py` |
| A.11 | Multipart upload and PWA progress | `test_farmer_account.py`, `test_mobile_pwa.py` |
| B.7 | Results, diagnoses, model metadata | `test_disease_assistant.py`, `test_compliance.py` |
| B.8 | `GET /api/datasets/<id>/download` | `test_security_controls.py` |
| B.9 | `POST /api/models/<id>/evaluate` | `test_security_controls.py` |
| C.6 | Field-scoped routes and image service | `test_field_authorization.py` |
| C.7 | `POST /api/agronomy/diagnoses/<id>/review` | `test_disease_assistant.py` |
| C.8 | `backend/advice_engine.py` | `test_disease_assistant.py` |
| D.7 | `/api/fields/<id>/assignment` | `test_field_authorization.py` |
| D.8 | Session-version authentication | `test_farmer_account.py` |
| D.9 | Storage, model, migration, and workload controls | Security test suite |
| E.6 | `backend/image_security.py` | `test_image_security.py` |
| E.7 | `backend/inference.py`, `backend/disease_inference.py` | Inference and disease suites |
| E.8 | Cache, rate, training, migration, Waitress controls | `test_security_controls.py`, `test_migrations.py` |
