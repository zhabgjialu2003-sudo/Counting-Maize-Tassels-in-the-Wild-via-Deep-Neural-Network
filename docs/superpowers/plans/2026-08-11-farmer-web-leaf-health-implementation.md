# Farmer Web Leaf Health Implementation Plan

Date: 2026-08-11

Design source: `docs/superpowers/specs/2026-08-11-farmer-web-leaf-health-design.md`

## Objective

Deliver a discoverable, responsive Farmer Leaf Health workflow on desktop and mobile, with truthful AI screening, Farmer-controlled Agronomist review requests, field-scoped professional review, bilingual presentation, and regression protection for existing tassel-counting flows.

## Delivery Rules

- Keep all implementation identifiers, comments, database values, tests, and documentation in English.
- Store valid UTF-8 Chinese only in user-facing bilingual copy; repair the existing mojibake in `frontend/pages/leaf.html` as part of this work.
- Reuse `frontend/pages/leaf.html` and `POST /api/agronomy/diagnose`; do not create a duplicate desktop diagnosis page.
- Enforce ownership and assignment rules in the backend even when the frontend hides an action.
- Add tests before or with each behavior change and keep commits scoped by concern.
- Do not mix the pending authentication fix from PR #5 into feature commits. Rebase the feature branch onto `main` after PR #5 is merged, or merge both PRs independently in dependency order.

## Phase 0: Establish the Integration Baseline

### Files

- Git history and branch state only.

### Steps

1. Confirm the working tree is clean and the current branch contains the approved design and plan only.
2. Confirm PR #5 (`agent/fix-demo-session-token`) remains available and green.
3. Create an implementation branch from the latest intended integration base, named `agent/farmer-web-leaf-health`.
4. If PR #5 has already merged, update from `origin/main` before implementation. Otherwise keep the feature independent and record PR #5 as a merge-order dependency.
5. Run the existing unittest suite once to record the baseline.

### Verification

```powershell
git status -sb
git log --oneline -5
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
Remove-Item Env:PYTHONPATH
```

## Phase 1: Add Review Workflow Persistence

### Files

- Create `database/migrations/007_farmer_leaf_review_workflow.sql`.
- Update `tests/test_migrations.py`.

### Database changes

Add to `disease_diagnoses`:

- `review_status VARCHAR(30) NOT NULL DEFAULT 'not_requested'`.
- A check constraint allowing `not_requested`, `requested`, `in_review`, and `reviewed`.
- `review_requested_at TIMESTAMP NULL`.
- `review_request_reason TEXT NULL`.
- An index on `(field_id, review_status, review_requested_at DESC)`.

Backfill existing rows with `reviewed_at IS NOT NULL` to `reviewed`; retain `not_requested` for other existing rows. Make the migration idempotent and safe to rerun through the existing migration runner.

### Tests

1. Migration applies successfully to the test database.
2. Existing reviewed rows are backfilled correctly.
3. Invalid review states are rejected by the database.
4. Reapplying migrations does not duplicate columns, constraints, or indexes.

## Phase 2: Expose Farmer-Owned Fields Safely

### Files

- Update `backend/app.py` in the `GET /api/fields` route.
- Update `tests/test_field_authorization.py`.

### Behavior

1. Add `Farmer` to the route role guard.
2. For Farmers, query only `fields.owner_user_id = request.auth_user["user_id"]`.
3. Ignore any client-supplied owner ID.
4. Preserve current Agronomist assignment filtering, Researcher access, Admin access, and optional region filtering.

### Tests

1. Farmer sees owned fields.
2. Farmer never sees another Farmer's fields.
3. Region filtering cannot bypass ownership.
4. Existing Agronomist and Admin field tests remain green.

## Phase 3: Implement Review Policy and API Endpoints

### Files

- Update `backend/app.py`.
- Prefer creating `backend/services/disease_review.py` for shared state-transition and recommendation policy.
- Create `tests/test_farmer_leaf_review.py`.
- Update `tests/test_disease_assistant.py` only where existing contracts need additional response fields.

### Shared policy

Implement one function that determines whether review is recommended from:

- Screening status.
- Image-quality status.
- Possible condition.
- Confidence compared with `DISEASE_REVIEW_CONFIDENCE_THRESHOLD`, default `0.70`.

Return the recommendation and machine-readable reasons in the diagnosis response. Do not convert an uncertain or rejected model result into a disease label.

### Farmer review request

Add `POST /api/agronomy/diagnoses/<diagnosis_id>/review-request`:

1. Require Farmer authentication.
2. Accept `field_id` and a reason of at most 500 characters.
3. Lock or atomically update the diagnosis row.
4. Verify diagnosis ownership.
5. Verify field ownership.
6. Verify at least one active assigned Agronomist.
7. Transition `not_requested` to `requested`, recording the field, reason, and timestamp.
8. Return the existing request unchanged for duplicate submissions.
9. Reject incompatible terminal transitions.
10. Write an audit-log entry only for a newly created request.

### Agronomist start-review endpoint

Add `PATCH /api/agronomy/diagnoses/<diagnosis_id>/review-status`:

1. Require Agronomist or Admin authentication.
2. Permit only the `in_review` action for this endpoint.
3. For Agronomists, verify the field assignment.
4. Atomically transition `requested` to `in_review`.
5. Return `in_review` idempotently when already started by an authorized reviewer.

### Existing professional review endpoint

Update `POST /api/agronomy/diagnoses/<diagnosis_id>/review` so the professional decision, note, reviewer identity, timestamp, and `review_status = 'reviewed'` are stored in one transaction. Preserve the existing decision validation and field-assignment restriction.

### History and queue

Extend `GET /api/agronomy/diagnoses` to return safe review summary fields:

- `review_status`
- `review_requested_at`
- `review_request_reason`
- `reviewer_decision`
- `reviewed_condition`
- `reviewer_note`
- `reviewed_at`

Farmer and Researcher records remain owner-scoped. The Agronomist result set must include only requested or active review records from assigned fields. Admin retains full access.

### Tests

Cover successful requests, duplicate requests, missing field, unowned diagnosis, unowned field, no assigned Agronomist, assigned and unassigned Agronomist access, state transitions, completed review visibility, role rejection, reason length, audit logging, and concurrency-safe idempotency.

## Phase 4: Make Leaf Health Discoverable on Farmer Desktop

### Files

- Update `frontend/js/auth.js`.
- Update `frontend/pages/dashboard.html`.
- Update `frontend/pages/leaf.html`.
- Update `frontend/css/style.css` and/or `frontend/css/mobile.css` without duplicating declarations unnecessarily.
- Update `tests/test_mobile_pwa.py` and `tests/test_farmer_account.py` static frontend assertions where appropriate.

### Navigation

1. Include `leaf.html` in the desktop Farmer navigation between Upload and Result.
2. Label the entry `Leaf Health` on desktop and retain a concise mobile label.
3. Keep route authorization limited to the existing allowed roles; do not expose Agronomist review controls to Farmers.

### Dashboard

Replace the ambiguous quick actions with clear task language:

- `Count Maize Tassels` with wide-field photo guidance.
- `Check Leaf Health` with close-up leaf guidance.
- Retain access to the latest tassel result without competing with the two primary tasks.

### Responsive Leaf Health page

1. Repair all mojibake and malformed bilingual markup in `leaf.html` using valid UTF-8.
2. Replace critical inline layout rules with named responsive classes.
3. Render a two-column workspace above the mobile breakpoint and a one-column workflow below it.
4. Preserve large touch targets, accessible labels, keyboard order, status announcements, and sufficient contrast.
5. Preserve the selected image and form inputs when the language changes or a recoverable error occurs.
6. Load Farmer-owned fields and allow screening without a field.
7. Require a field only when the Farmer requests professional review.

### Result and review UI

1. Render plain-language status, possible condition, confidence label, image-quality guidance, warning signs, and next steps.
2. Keep raw model values in an expandable `Technical Details` region.
3. Show the preliminary-screening disclaimer near the main result.
4. Display `Request Agronomist Review` for every saved Farmer diagnosis, emphasizing it when the shared policy recommends review.
5. Show a non-destructive field-selection prompt when review is requested without a linked field.
6. Disable repeated submission while a request is pending and render the server-provided review state.

## Phase 5: Add Farmer History and Agronomist Queue Behavior

### Files

- Update `frontend/pages/leaf.html` or the existing role-appropriate history view without creating a duplicate diagnosis data source.
- Update `frontend/pages/agronomist.html`.
- Update relevant shared JavaScript only when behavior is genuinely shared.
- Extend `tests/test_farmer_leaf_review.py` and frontend static tests.

### Farmer history

Display the Farmer's own recent leaf screenings with:

- Date.
- Condition or uncertainty state.
- Review status.
- Completed professional decision and note when present.

Do not expose reviewer contact details or other users' records.

### Agronomist queue

1. Add a review queue restricted to requested diagnoses for assigned fields.
2. Show field context, Farmer-provided context, safe protected-image access, AI result, and request reason.
3. Mark a request `in_review` when the Agronomist explicitly starts it.
4. Reuse the existing confirm/correct/inconclusive review form.
5. Refresh the queue after completion and prevent a second terminal review from silently overwriting the first.

## Phase 6: Error Handling and Human-Centred Copy

### Files

- Update `frontend/pages/leaf.html`.
- Update `frontend/pages/agronomist.html` where review queue messaging is added.
- Update backend response messages only where a new endpoint requires them.

### Required states

- Invalid image type or size.
- Undecodable image.
- Blurry, dark, bright, or undersized image.
- Offline before upload.
- Interrupted upload with retained local state.
- Model unavailable.
- Analysis completed but persistence failed.
- Missing field for review request.
- No assigned Agronomist.
- Duplicate request.
- Unauthorized or unavailable record.

English and Chinese user-facing strings must express the same meaning. Error copy must state what happened, whether the photo or result was retained, and the next safe action.

## Phase 7: Verification and Regression Testing

### Automated suite

Run the targeted suites first:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m unittest tests.test_migrations
.\.venv\Scripts\python.exe -m unittest tests.test_field_authorization
.\.venv\Scripts\python.exe -m unittest tests.test_disease_assistant
.\.venv\Scripts\python.exe -m unittest tests.test_farmer_leaf_review
Remove-Item Env:PYTHONPATH
```

Then run the complete suite:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
Remove-Item Env:PYTHONPATH
```

### Browser acceptance

Use a real browser at desktop and mobile viewports to verify:

1. Farmer login and session persistence.
2. Desktop navigation and dashboard discovery.
3. Image preview, compression, screening, and result rendering.
4. Language switching without losing state.
5. Review request and duplicate-click handling.
6. Agronomist assigned queue and completed review.
7. Farmer history displaying the completed review.
8. Unauthorized cross-user and cross-field attempts.
9. Existing tassel upload, count result, mobile navigation, and profile flows.

Capture concise evidence screenshots for the final report only after the flow passes.

## Phase 8: Documentation and GitHub Delivery

### Files

- Update `README.md` only if navigation or run instructions change.
- Update relevant user-story, API, user-manual, and test documentation after behavior is verified.

### Delivery

1. Review the final diff for unrelated or generated files.
2. Keep model artifacts, uploads, `.env`, database dumps, browser sessions, and test screenshots out of commits unless explicitly required.
3. Use focused Conventional Commits for migration/backend, Farmer UI, Agronomist workflow, and documentation where practical.
4. Push `agent/farmer-web-leaf-health` and open a Draft PR targeting `main`.
5. Document the dependency on PR #5 if it has not yet merged.
6. Include test commands, browser evidence, schema migration details, user impact, and security boundaries in the PR description.

## Completion Checklist

- [ ] Desktop Farmer navigation and dashboard expose Leaf Health.
- [ ] One responsive Leaf Health page works on desktop and mobile.
- [ ] Existing bilingual mojibake is repaired.
- [ ] Farmer-owned field selection is server-scoped.
- [ ] Screening results remain cautious and human-readable.
- [ ] Farmer-controlled review requests are idempotent.
- [ ] Agronomist review access is field-assignment scoped.
- [ ] Farmer history shows review progress and completed notes.
- [ ] Database migration is idempotent and tested.
- [ ] Targeted and full unittest suites pass.
- [ ] Desktop and mobile browser flows pass.
- [ ] Existing tassel-counting and account flows show no regression.
- [ ] Documentation and Draft PR are complete.
