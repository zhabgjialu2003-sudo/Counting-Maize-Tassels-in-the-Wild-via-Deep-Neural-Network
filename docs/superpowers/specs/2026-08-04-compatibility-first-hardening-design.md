# Compatibility-First System Hardening and Documentation Design

**Project:** Counting Maize Tassels in the Wild via Deep Neural Network

**Document status:** Approved direction; implementation specification pending final user review

**Date:** 4 August 2026

**Language policy:** Repository and formal assessment documents are English-only. The product interface remains bilingual.

**Privacy policy:** No student names, student numbers, personal email addresses, supervisor details, passwords, or teacher-workbook personal data may be added to the repository or generated assessment document.

## 1. Objective

Improve the existing application into a maintainable, secure, testable, and deployment-ready maize decision-support system without breaking its current user interface, public API paths, or existing PostgreSQL data. The completed system must continue to count maize tassels and must also support cautious maize disease screening, image-quality guidance, uncertainty handling, and agronomist review.

After the implementation is verified, append new requirements and assessment evidence to the existing documentation. The original 30 user stories and their original test cases must remain unchanged.

## 2. Authoritative Inputs

The following sources control the work, in priority order:

1. The user's explicit requirements in the project discussion.
2. The teacher-provided assessment requirements workbook, used locally and never committed.
3. The existing submitted Word document, used as the visual and structural template but not modified.
4. The final verified code and database schema.
5. Existing repository documentation, retained where it does not conflict with the sources above.

## 3. Approaches Considered

### 3.1 Patch the monolithic application

Apply narrow fixes directly in `backend/app.py`. This has the lowest initial cost but preserves the 3,000-line route module, makes regression risk harder to control, and does not meet the maintainability objective.

### 3.2 Compatibility-first modular refactor — selected

Preserve routes, response contracts, UI behaviour, and data while extracting configuration, authentication, repositories, services, and route groups into focused modules. Introduce only additive or backward-compatible database migrations. This provides the best balance of safety, assessment quality, and long-term maintainability.

### 3.3 Clean rewrite

Rebuild the backend and frontend around a new architecture. This could produce a cleaner system but would create unnecessary compatibility, migration, and schedule risk. It is not selected.

## 4. Compatibility Contract

The implementation must satisfy all of the following:

- Preserve existing browser page URLs and `/api/...` route paths.
- Preserve current successful response fields unless a new optional field is added.
- Preserve the existing bilingual interface and current role navigation.
- Preserve all existing database records through incremental, idempotent migrations.
- Preserve the current model integration entry points while validating artifact locations and integrity.
- Preserve the original 30 user stories, their identifiers, wording, diagrams, and original test-case text.
- Append new documentation after the existing role-specific entries; never renumber the original material.
- Record any mismatch in a separate compatibility note instead of rewriting an original user story.

## 5. Target Backend Architecture

The Flask application will retain a compatibility export for the current startup command while adopting an application factory and focused modules:

```text
backend/
  app.py                    Compatibility entry point and application export
  application.py            Application factory and extension registration
  config.py                 Typed environment configuration and limits
  api/
    auth.py                 Login, account profile, password, and email routes
    uploads.py              Single and batch image-upload routes
    predictions.py          Tassel prediction and result routes
    disease.py              Disease screening and agronomist-review routes
    fields.py               Field access and ownership-aware routes
    datasets.py             Dataset administration routes
    models.py               Training, evaluation, and deployment routes
    admin.py                Users, permissions, logs, backup, and monitoring
  services/
    auth_service.py         Fresh-account authorization and session invalidation
    image_service.py        Decode validation, naming, storage, and encryption
    prediction_service.py   Tassel inference orchestration and bounded caching
    disease_service.py      Quality gates, screening, uncertainty, and advice
    model_service.py        Artifact validation and safe activation
    training_service.py     Bounded training-job orchestration
  repositories/
    users.py
    images.py
    predictions.py
    fields.py
    models.py
  security/
    tokens.py
    rate_limits.py
    paths.py
  migrations/
    ...                     Additive, repeatable schema and data migrations
```

Route modules perform HTTP validation and response formatting. Services contain business rules. Repositories contain SQL. Predictors remain isolated from Flask and database concerns.

## 6. Security and Correctness Changes

### 6.1 Unique uploads and correct inference caching

- Store every upload under a server-generated UUID-based name.
- Retain the sanitized original name as metadata only.
- Calculate a SHA-256 digest after validation.
- Key prediction caches by content digest, model identity, and inference mode rather than the client filename.
- Use a size-bounded least-recently-used cache with explicit invalidation after model activation.
- Serialize access to predictors that are not proven thread-safe.

### 6.2 Real image validation and resource limits

- Configure request and per-file size limits for single, batch, disease, and dataset uploads.
- Decode and verify the image rather than trusting the extension or MIME header.
- Reject decompression bombs, unsupported formats, invalid dimensions, empty files, and unsafe pixel counts.
- Stream uploads to bounded temporary storage where practical instead of reading unlimited bodies into memory.
- Return stable, human-readable bilingual UI messages while keeping formal API documentation in English.

### 6.3 Correct encrypted image storage

- Make the storage method explicit: encrypted bytes must be marked encrypted; plaintext bytes must never be marked encrypted.
- Ensure new disease images follow the same encryption contract as other protected images.
- Add a migration that safely identifies affected historical rows, repairs only verifiable records, and logs records that require manual recovery.
- Never log image contents or encryption keys.

### 6.4 Fresh authorization state

- Treat signed tokens as session identifiers, not permanent copies of role, status, or permission state.
- On protected requests, load the current user state and verify that the account remains enabled.
- Add a session version or credential-change timestamp so password, email, role, status, and security-sensitive permission changes invalidate older sessions.
- Keep bearer-header authentication as the normal mechanism.
- Remove access tokens from frontend query strings. A disabled compatibility fallback may be available only behind an explicit development setting.
- Apply rate limits to login, upload, prediction, password-reset, and expensive administrative operations.
- Strengthen password rules and avoid exposing account-existence details.

### 6.5 Ownership and privacy

- Verify that a farmer owns the selected `field_id` before accepting or revealing associated records.
- Define role-specific record scopes: farmers see their own records; agronomists see explicitly assigned or policy-authorized fields; researchers receive approved and appropriately de-identified data; administrators receive operational access.
- Audit sensitive reads and writes without storing secrets or full image payloads in logs.

### 6.6 Safe model and training operations

- Restrict deployable model paths to configured model roots.
- Reject path traversal, symlinks escaping approved roots, missing files, Git LFS pointers, unexpected extensions, and unapproved artifacts.
- Verify artifact metadata and an optional stored SHA-256 digest before activation.
- Warm up a candidate model before changing the active database status.
- Replace unbounded daemon training threads with a bounded in-process job controller suitable for the local prototype, with explicit concurrency, cancellation, status, and failure handling.
- Document that a persistent external queue is required for horizontally scaled public deployment.

### 6.7 Error handling and production serving

- Log internal exception details with a correlation identifier.
- Return stable public error codes and safe messages without raw exception text or server paths.
- Retain the local development startup path.
- Add a production startup configuration using a supported WSGI server and environment-driven proxy, HTTPS, timeout, and worker guidance.

## 7. Data Migration Strategy

All migrations must be additive, idempotent, testable, and safe to rerun. Planned schema additions include:

- session or credential versioning fields for users;
- upload content digest, original filename, stored filename, media type, byte size, dimensions, and validated state;
- explicit image encryption state and storage version;
- model artifact digest, artifact type, validation state, and activation audit fields;
- training-job lifecycle fields if the existing schema cannot represent queued, running, failed, cancelled, and completed states;
- indexes supporting ownership checks, history queries, digests, and active-model lookups.

No migration may delete existing user, image, prediction, field, dataset, model, or audit records. Historical encryption repair must create a backup/audit trail and must not guess when record state cannot be verified.

## 8. Disease-Screening and Human-Centred Behaviour

The uploaded photograph is meaningful only when the system communicates its limits. The workflow must:

1. verify that the file is a safe, readable image;
2. assess blur, brightness, contrast, resolution, and framing;
3. ask the farmer to retake an unsuitable photograph using concise bilingual guidance;
4. run tassel counting and disease screening when the image is suitable;
5. distinguish supported, uncertain, unsupported, and unavailable results;
6. avoid claiming a confirmed diagnosis from a photograph;
7. provide practical next steps and an agronomist-review path;
8. allow an unknown or unselected field instead of forcing the farmer to guess;
9. request optional context such as visible plant part, approximate location, and observation notes only when it improves advice;
10. preserve the farmer's current page and selected image across retryable mobile-network interruptions.

## 9. Test Design

Existing test-case text remains unchanged. New automated and assessment test cases are appended and mapped to requirements.

### 9.1 Automated regression coverage

- same-filename uploads from different users remain isolated;
- identical and different image bytes generate correct cache behaviour;
- cache capacity and invalidation are enforced;
- invalid image bytes, oversize bodies, decompression bombs, and unsafe dimensions are rejected;
- disease images are stored and retrieved under the correct encryption state;
- disabled, role-changed, permission-changed, password-changed, and email-changed users cannot use stale sessions;
- access tokens are absent from generated URLs and query-token authentication is disabled by default;
- field ownership and role scopes are enforced;
- login and expensive endpoints are rate-limited;
- model paths and digests are validated before deployment;
- training concurrency and job-state transitions are bounded;
- internal exceptions do not appear in client responses;
- migrations are repeatable and preserve pre-migration records;
- existing 54 baseline tests continue to pass unless an obsolete assertion is replaced by a documented compatibility-equivalent assertion.

### 9.2 Functional and usability evidence

Each new user story receives one or more test cases containing:

- test-case ID and linked user-story ID;
- objective and scenario;
- preconditions and test data;
- numbered actions;
- expected results and explicit acceptance threshold;
- actual result backed by execution evidence;
- status of `Pass`, `Fail`, `Blocked`, `Planned`, or `Not Executed`;
- desktop and mobile viewport coverage where applicable;
- normal, alternative, exception, permission, and network-interruption flows.

No unexecuted test may be labelled `Pass`.

## 10. Add-Only Requirements Documentation

The original role sections and 30 stories remain intact:

- Farmer: A.1–A.8
- Researcher: B.1–B.6
- Agronomist: C.1–C.5
- Admin: D.1–D.6
- System: E.1–E.5

New stories will continue from the next role-specific identifier, for example A.9, B.7, C.6, D.7, and E.6. Every new story has exactly one primary classification: Farmer, Researcher, Agronomist, Admin, or System. Cross-role participants are recorded as secondary actors.

Candidate additions, subject to final-code verification, include:

- **Farmer:** disease-screening upload, guided photo retake, unknown-field analysis, uncertainty explanation, mobile upload retry, email/password account maintenance, and agronomist review request.
- **Researcher:** approved disease dataset access, disease-model evaluation, de-identified combined analysis, and reproducible export metadata.
- **Agronomist:** review disease-screening evidence, correct uncertain results, manage farmer recommendations, review unknown-field submissions, and record follow-up outcomes.
- **Admin:** manage disease-model artifacts, configure security limits, review storage-repair status, manage field assignments and data-access policy, and monitor training jobs.
- **System:** safe image validation, dual-model orchestration, uncertainty gating, session invalidation, content-addressed caching, encryption-state enforcement, and auditable model activation.

The exact final additions must reflect implemented and verified behaviour; unsupported aspirational stories must be marked future scope rather than represented as completed.

## 11. Diagrams and Traceability

For every new user story, generate:

- an individual BCE diagram;
- an individual sequence diagram;
- a detailed textual description;
- one or more linked test cases.

Also generate or update, without altering original story text:

- a consolidated use-case diagram covering all five roles;
- a system context and component architecture diagram;
- a deployment diagram for local and public-ready configurations;
- an ERD derived from the final migrated schema;
- an activity diagram for upload, validation, dual analysis, result, and agronomist review;
- a requirements traceability matrix mapping requirement → user story → use case → BCE/sequence diagram → API → entity → test case → evidence.

Each diagram is delivered as a legible PNG and an editable source file. Diagram labels and descriptions are English-only.

## 12. Word Document Design

Create a new all-English assessment document from a retained copy of the supplied Word template. The source template remains unchanged. The final document will:

- use the project title and document metadata without personal information;
- retain the template's restrained blue/green visual language, page size, margins, typography roles, table patterns, and diagram presentation;
- use real Word heading styles and an updateable table of contents;
- preserve the original user-story and test-case content while appending clearly labelled additions;
- include the final architecture, database, API, security, testing, deployment, user manual, and traceability evidence required by the teacher's workbook;
- use readable diagrams, consistent captions, controlled table widths, and deliberate page breaks;
- state test status honestly and distinguish executed evidence from planned work.

The document must be rendered page by page and visually inspected. Section/style audits, image audits, field audits, package-preservation checks, and reference/final render comparisons must pass before delivery.

## 13. Verification and Completion Gates

Implementation is complete only when:

1. all targeted security and correctness regressions have automated tests;
2. all existing compatible tests and all new tests pass;
3. migrations pass on both a fresh database and a representative pre-existing schema/data fixture;
4. desktop and mobile core flows pass browser-based end-to-end checks;
5. tassel and disease predictors report valid health states or fail safely with clear user guidance;
6. CodeGraph is refreshed and used for a final dependency/blast-radius review;
7. formal repository documentation contains no Chinese text or personal information;
8. the original 30 user stories and their original test-case text remain unchanged;
9. every new story is classified under exactly one of the five required roles and has linked evidence;
10. the Word document and every diagram pass visual QA;
11. committed files contain no database passwords, access tokens, private images, teacher workbook data, or local absolute paths;
12. Git history contains intentional, reviewable commits for design, implementation, tests, and documentation.

## 14. Delivery Set

- refactored and verified source code;
- additive database migrations and migration instructions;
- automated test suite and evidence summary;
- English Markdown requirements and technical documentation;
- appended user stories, descriptions, acceptance criteria, test cases, BCE diagrams, sequence diagrams, use-case diagrams, ERD, and traceability matrix;
- PNG diagram exports and editable diagram sources;
- visually verified all-English Word document without personal information;
- teammate run instructions and deployment guidance;
- committed and pushed GitHub history after final review.

## 15. Explicit Non-Goals

- Rewriting, deleting, renumbering, or silently correcting the original 30 user stories.
- Falsifying test results or presenting placeholder metrics as measured results.
- Committing model-training datasets, private farmer images, passwords, the teacher workbook, or personal information.
- Replacing the current interface or breaking existing API paths.
- Purchasing or activating a paid public-hosting service without separate user authorization.
