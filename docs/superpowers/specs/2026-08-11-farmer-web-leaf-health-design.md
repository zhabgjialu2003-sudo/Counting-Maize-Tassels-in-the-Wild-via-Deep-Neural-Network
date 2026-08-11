# Farmer Web Leaf Health Design

Date: 2026-08-11
Status: Approved for implementation planning

## 1. Context

The disease-screening backend already accepts Farmer requests through `POST /api/agronomy/diagnose`, and the responsive `frontend/pages/leaf.html` page already provides mobile image preparation, bilingual guidance, and AI screening results. However, the desktop Farmer navigation omits the Leaf Assistant and the Farmer dashboard does not advertise it. This makes an existing Farmer capability appear mobile-only.

The Agronomist page also exposes disease analysis, but it includes professional review controls that must not be available to Farmers.

## 2. Goals

- Give Farmers a clearly discoverable, independent `Leaf Health` workflow on the desktop web application.
- Keep desktop and mobile behavior consistent by adapting the existing `leaf.html` page instead of creating a duplicate page.
- Separate close-up leaf screening from wide-field tassel counting.
- Provide immediate, cautious AI guidance in plain language.
- Allow a Farmer to request Agronomist review when the result is uncertain, indicates possible disease, or causes concern.
- Route review requests only to Agronomists assigned to the relevant field.
- Preserve role-based data isolation and stale-session protection.
- Keep implementation identifiers and documentation in English while retaining an English/Chinese user-interface option.

## 3. Non-Goals

- The AI result will not be presented as a definitive diagnosis or a replacement for an Agronomist.
- Farmers will not receive Agronomist confirmation, correction, or professional review controls.
- The tassel-counting upload flow will not be merged with the leaf-health flow.
- The first implementation will not introduce chat, live messaging, automatic treatment prescriptions, or review assignment outside the existing field-assignment model.

## 4. Chosen Approach

Enhance the existing `frontend/pages/leaf.html` as one responsive Farmer-facing Leaf Health page.

This approach is preferred over a separate desktop page because it prevents duplicated diagnosis logic, translation content, validation rules, and tests. It is preferred over a role-dependent Agronomist page because it keeps professional review controls isolated from the Farmer experience.

## 5. Farmer Experience

### 5.1 Navigation and entry points

For desktop Farmers, the primary navigation will be:

`Home | Tassel Upload | Leaf Health | Results`

The Farmer dashboard will present two clearly differentiated primary actions:

- `Count Maize Tassels` for wide-field images.
- `Check Leaf Health` for a close-up image of one maize leaf.

The mobile navigation will retain its current Leaf Assistant entry.

### 5.2 Responsive page layout

The Leaf Health page will use one responsive document:

- Desktop: two columns. The left column contains capture guidance, upload controls, and field context. The right column contains preview, progress, screening result, and review status.
- Mobile: one column with the existing field-friendly touch targets and bottom navigation.

The page will preserve the selected image and entered context when the language changes or a recoverable upload error occurs.

### 5.3 Input

Required:

- One valid JPG or PNG close-up leaf image.

Optional:

- Farmer-owned field.
- Crop growth stage.
- Observed symptoms.
- Symptom spread.
- Additional note.

The interface will explain how to take a useful image: fill most of the frame with one leaf, include the damaged area, use soft light, avoid glare, and focus before capture.

### 5.4 Result presentation

The primary result will use understandable language and contain:

- Screening outcome and possible condition.
- Confidence expressed as a labelled level, not only a percentage.
- Image-quality result and retake guidance when necessary.
- Visible warning signs and practical next steps.
- A persistent statement that the result is preliminary AI screening.
- An expandable `Technical Details` section for model version, raw confidence, entropy, and trace information.

The interface must not fabricate a disease label when the model reports `uncertain`, `retake_required`, or `unsupported`.

## 6. Agronomist Review Workflow

### 6.1 When review is recommended

The interface will emphasize `Request Agronomist Review` when any of the following applies:

- The screening status is not `supported`.
- Image quality prevents a reliable conclusion.
- A possible disease is reported.
- Confidence is below the shared review threshold. The threshold is configured by `DISEASE_REVIEW_CONFIDENCE_THRESHOLD` and defaults to `0.70`.
- The Farmer chooses to request help regardless of the AI recommendation.

An emphasized recommendation does not automatically create a request. The Farmer remains in control and must explicitly submit it.

### 6.2 Review request requirements

A review request requires a Farmer-owned field so the system can enforce assignment boundaries. If the initial screening was completed without a field, the page will preserve the diagnosis and ask the Farmer to select an owned field before requesting review.

Submitting a request records:

- Diagnosis ID.
- Requesting Farmer ID through the diagnosis owner.
- Field ID.
- Request reason.
- Requested timestamp.
- Review workflow status.

Repeated submissions for the same diagnosis must be idempotent and must not create duplicate pending requests.

### 6.3 Review states

The Farmer-facing state labels are:

- `AI Screening Completed`
- `Review Requested`
- `Under Review`
- `Reviewed`

The stored workflow values will be stable English identifiers such as `not_requested`, `requested`, `in_review`, and `reviewed`.

### 6.4 Agronomist actions

An assigned Agronomist may:

- Confirm the AI result.
- Correct the condition.
- Mark the result inconclusive.
- Add a required practical review note.

The Farmer may read the completed review but may not change the professional decision.

## 7. Backend and Data Design

### 7.1 Existing endpoint reuse

`POST /api/agronomy/diagnose` remains the single screening endpoint. It already supports Farmer authentication, image validation, model inference, advice generation, encrypted image persistence, and a `disease_diagnoses` record.

`GET /api/agronomy/diagnoses` remains the history source but will return the additional review workflow fields required by the Farmer history and Agronomist queue.

### 7.2 Farmer field access

`GET /api/fields` will allow the Farmer role and return only fields whose `owner_user_id` matches the authenticated Farmer. Existing Researcher, Agronomist, and Admin behavior will remain role-scoped. The backend, not a client-provided owner ID, determines ownership.

### 7.3 Review request endpoint

Add:

`POST /api/agronomy/diagnoses/<diagnosis_id>/review-request`

The endpoint will:

1. Require the Farmer role.
2. Verify that the diagnosis belongs to the authenticated Farmer.
3. Verify that the selected field belongs to that Farmer.
4. Verify that at least one active Agronomist is assigned to the field.
5. Create or return the existing pending request idempotently.
6. Add an audit-log entry.

The existing professional review endpoint remains restricted to Agronomist and Admin roles.

Add:

`PATCH /api/agronomy/diagnoses/<diagnosis_id>/review-status`

An assigned Agronomist uses this endpoint to make the idempotent transition from `requested` to `in_review` when starting work. The existing professional review submission changes the state to `reviewed` in the same transaction that stores the decision and note.

### 7.4 Schema migration

Extend `disease_diagnoses` with:

- `review_status VARCHAR(30) NOT NULL DEFAULT 'not_requested'` with allowed values `not_requested`, `requested`, `in_review`, and `reviewed`.
- `review_requested_at TIMESTAMP NULL`.
- `review_request_reason TEXT NULL`, limited to 500 characters by the application.

The existing `reviewer_user_id`, `reviewer_decision`, `reviewed_condition`, `reviewer_note`, and `reviewed_at` columns remain authoritative for the completed professional review.

Add an index covering the Agronomist queue, based on field, review status, and request time. A review-request update is idempotent at the diagnosis-row level, so a separate duplicate-prone request table is unnecessary for this scope.

During migration, existing rows with `reviewed_at IS NOT NULL` are backfilled to `reviewed`; all other existing rows remain `not_requested`.

## 8. Authorization and Privacy

- Farmer: create screenings, list only own diagnoses, request review only for own diagnoses and owned fields, and read completed reviews on own records.
- Agronomist: list only requested diagnoses for assigned fields and submit reviews only within those assignments.
- Admin: inspect all diagnosis and review records and manage field assignments.
- Researcher: retain only the currently authorized diagnosis access; no Farmer account details will be added to research responses.

Client-side visibility is not a security boundary. Every ownership and assignment rule must be enforced in SQL-backed server authorization.

Stored images remain encrypted using the existing secure image persistence flow. History responses expose summaries and authorized protected-image references rather than filesystem paths.

## 9. Failure and Recovery Behavior

- Invalid type, excessive size, or undecodable content: reject before inference with a specific corrective message.
- Blurry, dark, bright, or undersized image: provide retake guidance and do not claim a reliable disease result.
- Offline or interrupted upload: keep the image and form state in the current page so the Farmer can retry.
- Model unavailable: return a service-unavailable result and never manufacture advice.
- Persistence failure after successful inference: show the screening result with an explicit warning that history and review request are unavailable for that attempt.
- Missing field during review request: retain the diagnosis and ask for a Farmer-owned field.
- No assigned Agronomist: keep the screening result, explain that professional review cannot yet be routed, and direct the Farmer to contact the project administrator.
- Duplicate review request: return the current request state rather than creating another record.
- Unauthorized record or field: return `403` or privacy-preserving `404` without exposing another user's data.

## 10. Testing Strategy

### 10.1 Backend tests

- Farmer can diagnose a valid close-up image.
- Farmer field listing returns only owned fields.
- Farmer can request review for an owned diagnosis and owned field.
- Duplicate request is idempotent.
- Cross-user diagnosis and field references are rejected.
- Agronomist queue contains only requested records from assigned fields.
- Unassigned Agronomist review is rejected.
- Completed review is visible to the owning Farmer.
- Existing stale-token, upload validation, encrypted persistence, and review-decision tests remain green.

### 10.2 Frontend and browser tests

- Desktop Farmer navigation contains `Leaf Health`.
- Farmer dashboard contains separate tassel-counting and leaf-health actions.
- Desktop two-column and mobile one-column layouts remain usable at representative viewport sizes.
- Language switching preserves the selected photo and form values.
- Healthy, possible-disease, uncertain, retake-required, unsupported, offline, and unavailable-model states render honestly.
- Farmer can complete login, screening, review request, refresh, and history review.
- Agronomist can complete an assigned review, and the Farmer can see it afterward.
- Tassel counting, mobile navigation, and existing role dashboards show no regression.

## 11. Acceptance Criteria

The feature is complete when:

1. A desktop Farmer can discover Leaf Health from both the main navigation and dashboard.
2. The same responsive Leaf Health page works on desktop and mobile.
3. A Farmer receives a saved, human-readable preliminary screening without seeing professional review controls.
4. A Farmer can explicitly request review for an owned diagnosis linked to an owned field.
5. Only an Agronomist assigned to that field can review the request.
6. The Farmer can see review progress and the completed professional note.
7. Bilingual interaction, upload recovery, truthful uncertainty, and image-quality guidance work as specified.
8. Automated authorization, API, regression, and browser-flow tests pass.
