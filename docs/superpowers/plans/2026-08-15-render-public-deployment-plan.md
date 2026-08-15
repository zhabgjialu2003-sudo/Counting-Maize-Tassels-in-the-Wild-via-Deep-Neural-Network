# Render Public Deployment Implementation Plan

## Overview

- Goal: Deploy the complete Maize Detector system to a stable Render HTTPS endpoint.
- Source: GitHub repository on the current deployment branch, followed by a controlled merge to `main`.
- Infrastructure: one Standard 2 GB Python web service and one paid PostgreSQL database in Singapore.
- Success criteria: healthy deployment, four-role authentication, tassel counting, leaf screening, persistent results, and no committed secrets.

## Tasks

### Phase 1: Baseline and deployment contracts

- [x] Record the current branch, remote, dirty files, model digests, and passing test baseline.
- [x] Confirm the application supports Render's `PORT`, same-origin frontend serving, private PostgreSQL variables, and production security checks.
- [x] Identify database bootstrap and migration behavior on both empty and existing databases.

### Phase 2: Reproducible build

- [x] Pin the supported Python runtime for Render.
- [x] Add a Render build helper that installs CPU-only PyTorch and application dependencies.
- [x] Replace GUI OpenCV with the headless server package if compatibility tests pass.
- [x] Add a model-materialisation helper that detects Git LFS pointers, downloads only missing public artifacts, and validates exact SHA-256 digests.
- [x] Ensure any model download failure or checksum mismatch stops the build.

### Phase 3: Safe database initialisation

- [x] Add an idempotent deployment initialiser.
- [x] Apply the destructive base schema only when the application schema is absent.
- [x] Apply and verify non-destructive migrations on every release.
- [x] Provision the four assessment accounts from a Render secret.
- [x] Add tests proving an existing schema is not recreated.

### Phase 4: Render Blueprint and runtime configuration

- [x] Add `render.yaml` with a Standard Python web service and paid PostgreSQL database in Singapore.
- [x] Bind Waitress to `0.0.0.0:$PORT` and configure `/api/health`.
- [x] Generate signing and encryption secrets through Render and keep the Demo password unsynchronised.
- [x] Disable public one-click Demo Access while preserving normal fixed-account login.
- [x] Disable filesystem backup scheduling in hosted mode.
- [x] Keep initial automatic deployment disabled until smoke tests pass.

### Phase 5: Verification

- [x] Validate YAML and all deployment scripts.
- [x] Run the full automated test suite.
- [x] Verify Python and JavaScript syntax.
- [x] Scan tracked files for secrets and local credentials.
- [x] Verify both model digests and reject Git LFS pointer files.
- [x] Review the final diff for unrelated user changes.

### Phase 6: Publish and provision

- [ ] Commit only the deployment changes with a Conventional Commit message.
- [ ] Push the deployment branch to GitHub and merge it into `main` after checks pass.
- [ ] Open the Render Blueprint URL for the repository.
- [ ] Have the user authorise Render's GitHub access, select paid resources, and enter the Demo password secret.
- [ ] Apply the Blueprint and monitor the initial build, pre-deploy command, health check, and logs.

### Phase 7: Public smoke test and handoff

- [ ] Verify `/api/health` over HTTPS.
- [ ] Test all four account logins.
- [ ] Run one field-image tassel count and one close-up leaf screening.
- [ ] Confirm persisted results remain available after a restart.
- [ ] Verify desktop and mobile views from an external network.
- [ ] Add the live URL to GitHub Pages and final submission documentation.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Linux build receives Git LFS pointer files | Medium | High | Materialise and checksum both models during the build. |
| PyTorch exceeds build or runtime resources | Medium | High | Install CPU-only wheels and use the Standard 2 GB service. |
| Base schema deletes existing data | Low | Critical | Gate base-schema execution on an empty-schema check and test it. |
| Public Demo login is abused | Medium | Medium | Require the fixed password, disable public one-click access, and retain rate limits. |
| Uploaded files disappear after restart | Low | High | Use PostgreSQL image blobs as the durable copy; treat local files as temporary. |
| Accidental Git push triggers a bad release | Medium | High | Disable automatic deployment until the verified release is live. |
| Secret is committed to GitHub | Low | Critical | Use generated or `sync: false` Blueprint variables and run a secret scan. |
