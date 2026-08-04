# User Story Compliance Fixes - Implementation Tasks

## Objective

Complete the four partially satisfied user stories (A.11, B.4, B.7, and D.9) without changing the behaviour of already completed stories.

## Tasks

- [x] Add a non-destructive PostgreSQL migration for upload idempotency and detection provenance.
- [x] Add shared, fail-closed model and dataset validation to comparison and evaluation flows.
- [x] Make upload retries idempotent per user while retaining backward compatibility.
- [x] Return safe result provenance and protected asset URLs without internal filesystem paths.
- [x] Preserve one idempotency key per deliberate frontend file selection and reuse it on retry.
- [x] Add focused regression and success-path tests.
- [x] Run the complete automated test suite.
- [x] Re-audit the implemented call paths with CodeGraph.
- [x] Commit and push the verified changes to the existing feature branch.

## Success Criteria

- Duplicate retry requests create only one database image record and one encrypted object.
- Model comparison rejects unapproved paths and digest mismatches before inference begins.
- Public result and model responses expose stable identifiers and protected URLs, never server paths.
- Existing clients that omit an idempotency key continue to work.
- All existing and new tests pass.
