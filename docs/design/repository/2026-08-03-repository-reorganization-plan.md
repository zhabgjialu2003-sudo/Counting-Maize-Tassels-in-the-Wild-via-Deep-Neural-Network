# Repository Reorganization Implementation Plan

Date: 2026-08-03  
Design source: `2026-08-03-repository-reorganization-design.md`

## Objective

Implement the assessor-oriented repository structure without changing the
application's behaviour, model outputs, training evidence, or bilingual product
contract.

## Phase 1: Assessment entry points

- Add `docs/ASSESSMENT_INDEX.md` with direct links to requirements, design,
  implementation, testing, manuals, reports, model evidence, and examples.
- Add `docs/requirements/PROJECT_DELIVERABLES.md`, a sanitized summary of the
  supervisor plan without student IDs, personal email addresses, or phone data.
- Add README files where a directory boundary would otherwise be ambiguous.

Verification:

- New documentation is English-only.
- No source workbook or personal information is added.
- Every assessment-index target exists by the end of the migration.

## Phase 2: Database and design documentation

- Move schemas to `database/schema/`.
- Move migrations to `database/migrations/` and assign stable ordered names.
- Move the demo seed to `database/seeds/`.
- Move ERD files to `docs/design/database/`.
- Move BCE, sequence, activity, and core-flow diagrams to
  `docs/design/uml/` subdirectories.
- Repair SQL paths in README, backend metadata, the project website, and design
  documentation.

Verification:

- SQL file contents remain unchanged apart from path strings where required.
- PostgreSQL setup commands reference the new paths.
- `database/` contains no images or design diagrams.

## Phase 3: Requirements, reports, testing, and coursework

- Move user stories and traceability material to `docs/requirements/`.
- Move demo instructions to `docs/manuals/`.
- Move testing plans and audits to `docs/testing/`.
- Group progress, technical, and model reports under `docs/reports/`.
- Move presentation files to `docs/presentations/`.
- Move UI screenshots to `docs/evidence/ui/`.
- Move Week 10 submission material and historical notes to `coursework/week-10/`.
- Repair project-website and Markdown links.

Verification:

- Current documentation remains separate from historical coursework.
- Binary reports and presentations preserve their bytes.
- No duplicate current source of truth remains in `docs/other/`.

## Phase 4: Training and examples

- Move root tassel notebooks to `training/notebooks/tassel/` and remove
  ambiguous filename suffixes.
- Move disease notebooks to `training/notebooks/disease/`.
- Move disease evaluation evidence to `training/results/disease/`.
- Move `ai/samples/` and `ai/results/` to paired tassel input/output examples.
- Add or select a small paired disease-screening example set when licensing and
  expected outputs are available.
- Update notebook lists, documentation, and provenance references.

Verification:

- The executed disease notebook still has 16 executed code cells and no error
  outputs.
- Existing example-image hashes are unchanged after Git moves.
- Input/output pairing is documented.

## Phase 5: Deployment models and runtime configuration

- Move the tassel and disease runtime files to `models/deployment/`.
- Move provenance and model documentation to `models/tassel/` and
  `models/disease/`.
- Update Git LFS rules for the deployment model location.
- Add `TASSEL_MODEL_PATH` and `DISEASE_MODEL_PATH` examples.
- Update inference, startup checks, system status, SQL registry paths, frontend
  descriptions, and tests.
- Validate that missing files and Git LFS pointer files produce clear startup
  errors.

Verification:

- Tassel SHA-256 remains
  `37BCA6B8E817D911424DBD22F720F9CBE00248036E0FC6305EF853F8B38D9913`.
- Disease SHA-256 remains
  `4F48A440E2EB35BEF220107F9E777F9A3A10DC8FA0B79E0296A022CBA700EF17`.
- Both models load from default and environment-override paths.

## Phase 6: README and automated structure checks

- Replace competing root guidance with one assessor-oriented `README.md`.
- Remove `README_CODE_ONLY.md` after merging unique instructions.
- Add a repository-structure test covering required directories, forbidden
  root artefacts, assessment links, model locations, and ignored runtime files.
- Add a Markdown-link check for README and assessment-index local links.
- Keep application Chinese text while repository guidance remains English.

Verification:

- VS Code launch and test JSON remains valid.
- README quick-start commands use the reorganized paths.
- No broken local links remain in the two primary entry documents.

## Phase 7: Full validation and publication

- Run all existing and new automated tests with PostgreSQL configured only in
  the process environment.
- Run backend health checks.
- Run one tassel-counting example and one disease-screening example when a
  suitable disease input is present.
- Recompute model hashes and verify Git LFS status.
- Scan tracked files for secrets, local `.env` files, the supervisor workbook,
  personal phone data, caches, logs, and uploads.
- Confirm a clean working tree after commits.
- Push reviewable commits to `agent/add-agronomist-training` and verify PR 3.

## Commit sequence

1. `docs: add assessor evidence index`
2. `refactor: organize database and design assets`
3. `docs: classify reports tests and coursework`
4. `refactor: organize training and example artefacts`
5. `refactor: centralize deployment model paths`
6. `docs: consolidate project entry guidance`
7. `test: verify repository structure and links`

## Completion criteria

- The approved target structure is present.
- Primary project functionality and all existing tests remain operational.
- New structure and link checks pass.
- Model identities are unchanged.
- The assessor can reach every required deliverable from README and
  `docs/ASSESSMENT_INDEX.md`.
- No personal-information workbook or local secret is tracked.
