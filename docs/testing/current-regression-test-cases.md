# Current Regression Test Cases

This document supplements, and does not rewrite, the historical test-case text in `testing-plan.docx`. The historical Week 10 cases remain an unchanged baseline even where they mention prototype behavior that has since been replaced.

## Test Strategy

The current suite combines unit, API contract, PostgreSQL integration, static PWA, authorization, security, migration, and AI artifact tests. Tests fail closed when a database, model, or authorization dependency is unavailable. Production code has no fabricated detection fallback.

## Extension Test Cases

| ID | Story | Level | Preconditions | Test action | Expected result | Automated evidence |
|---|---|---|---|---|---|---|
| TC-EXT-A09-01 | A.9 | API/AI | Authenticated user; valid leaf PNG; controlled predictor | Submit Chinese screening request | 200; bilingual supported/uncertain/retake response with safety note | `test_disease_assistant.py` |
| TC-EXT-A09-02 | A.9 | Unit | Dark or undersized image | Run quality assessment | `retake` with explicit quality issues | `test_disease_assistant.py` |
| TC-EXT-A10-01 | A.10 | DB/API | Active Farmer | Change email with correct password | Email persists; new token works; old token is rejected | `test_farmer_account.py` |
| TC-EXT-A10-02 | A.10 | DB/API | Active Farmer | Change password | Old login fails; new login succeeds; session revoked | `test_farmer_account.py` |
| TC-EXT-A11-01 | A.11 | PWA/static | Mobile frontend | Inspect protected asset and upload clients | Authorization header used; URL token absent; retry copy retained | `test_mobile_pwa.py` |
| TC-EXT-A11-02 | A.11 | DB/API | Two PNGs with same original name | Upload both images | Unique UUID names, different hashes, isolated encrypted records | `test_farmer_account.py` |
| TC-EXT-B08-01 | B.8 | Security/unit | Approved dataset root and an outside file | Resolve both paths | Inside path accepted; outside path rejected | `test_security_controls.py` |
| TC-EXT-B09-01 | B.9 | Security/unit | Model artifact and expected digest | Validate artifact | Approved path/digest accepted; mismatch rejected | `test_security_controls.py` |
| TC-EXT-C06-01 | C.6 | Authorization/unit | Assigned and unassigned field states | Check Agronomist field access | Assigned field allowed; unassigned field denied | `test_field_authorization.py` |
| TC-EXT-C07-01 | C.7 | API | Agronomist token | Submit invalid review decision | 400 before persistence access | `test_disease_assistant.py` |
| TC-EXT-C08-01 | C.8 | Unit | Two advice requests with different context | Build both responses | Context from request one is absent from request two | `test_disease_assistant.py` |
| TC-EXT-D08-01 | D.8 | DB/API | Active account and issued token | Disable account, reuse old token | 401; stale token cannot access protected route | `test_farmer_account.py` |
| TC-EXT-D08-02 | D.8 | API | Valid token in query string only | Call protected route | 401 because query tokens are disabled | `test_farmer_account.py` |
| TC-EXT-D09-01 | D.9 | Security/unit | Rate limit of two requests | Make three requests in the window | Third request rejected with retry delay; later request allowed | `test_security_controls.py` |
| TC-EXT-D09-02 | D.9 | Security/unit | One-worker, one-pending training executor | Submit two pending jobs | Second pending job is rejected; capacity is bounded | `test_security_controls.py` |
| TC-EXT-E06-01 | E.6 | Unit | Disguised non-image bytes | Validate as JPG | Upload rejected | `test_image_security.py` |
| TC-EXT-E06-02 | E.6 | Unit | PNG bytes declared as JPEG | Validate content/MIME | MIME mismatch rejected | `test_image_security.py` |
| TC-EXT-E07-01 | E.7 | AI contract | Temporary TorchScript disease artifact | Run inference | Stable condition/status/technical contract returned | `test_disease_assistant.py` |
| TC-EXT-E08-01 | E.8 | Unit | Inference cache capacity two | Infer three content variants | Cache remains at capacity two; oldest entry evicted | `test_image_security.py` |
| TC-EXT-E08-02 | E.8 | Migration/unit | Ordered SQL files | Discover and strip transaction markers | Numeric order and SHA-256 records are stable | `test_migrations.py` |
| TC-EXT-E08-03 | E.8 | Integration | PostgreSQL with migration table | Run migration command twice | First run applies; second run reports applied without re-executing | `python -m backend.migrations --check` |

## Latest Verified Result

- Command: `python -m unittest discover -s tests`
- Result: 78 tests passed in 11.695 seconds on 4 August 2026.
- Database: local PostgreSQL `maize_detector`, migrations 001-004 registered.
- Expected log behavior: the persistence-failure contract test intentionally emits one handled error log while still returning the completed bilingual assessment.

## Exit Criteria

1. Full automated suite passes on a clean environment with the configured PostgreSQL database.
2. No production mock fallback marker exists.
3. Original filename collision, stale session, unassigned field access, path traversal, altered artifact digest, and oversized/invalid image cases are rejected.
4. PWA flows remain responsive at mobile viewport and never place an access token in a URL.
5. Word and diagram artifacts render without clipping or unreadable labels.
