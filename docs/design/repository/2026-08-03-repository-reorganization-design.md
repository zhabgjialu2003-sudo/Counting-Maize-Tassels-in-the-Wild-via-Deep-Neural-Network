# Repository Reorganization Design

Date: 2026-08-03  
Status: Approved for planning  
Primary audience: Project supervisor and assessor

## 1. Purpose

Reorganize the repository so an assessor can quickly locate the source code,
AI training evidence, database design, test evidence, manuals, reports, and
working examples required by the supervisor project plan. The reorganization
must preserve application behaviour, Git history, model integrity, and the
existing bilingual product experience.

The repository documentation and file names will use English. Chinese text may
remain inside the application where it is required by the bilingual user
interface and Agronomist response contract.

## 2. Source of Requirements

The classification follows the supplied CSCI321 Supervisor Project Plan. That
plan requires evidence for requirements analysis, system architecture, AI logic
design, database design, implementation, unit and integration testing, test
logs, user and technical manuals, reports, source code, executable artefacts,
presentation material, and a working demonstration.

The original supervisor workbook will not be committed because it contains
student identifiers, email addresses, and contact information. A sanitized
deliverables summary will be created instead.

## 3. Goals

- Make the core maize-tassel-counting objective immediately visible.
- Present maize leaf disease screening as a relevant extension, not a change of
  project topic.
- Give every major directory one clear responsibility.
- Separate deployable code, model artefacts, experiment evidence, example
  images, database scripts, design diagrams, and coursework submissions.
- Provide one assessment index that maps supervisor requirements to evidence.
- Retain a small, useful set of maize input and expected-output examples.
- Keep full training datasets outside Git while preserving source, revisions,
  manifests, licences, and download instructions.
- Preserve file history with Git-aware moves and descriptive commits.
- Keep the application runnable from VS Code after the reorganization.

## 4. Non-goals

- Redesigning the user interface or inference algorithms.
- Retraining either model.
- Uploading full third-party image datasets.
- Rewriting historical commit timestamps or authorship.
- Publishing local secrets, user uploads, or the original supervisor workbook.
- Removing bilingual functionality from the deployed application.

## 5. Target Repository Structure

```text
project-root/
|-- .vscode/                         Shared launch, test, and workspace settings
|-- backend/                         Flask API and inference services
|-- frontend/                        Desktop interface and mobile PWA
|-- database/
|   |-- schema/                      Database creation scripts
|   |-- migrations/                  Ordered schema changes
|   `-- seeds/                       Explicit demonstration data
|-- models/
|   |-- deployment/                  Git LFS runtime model artefacts
|   |-- tassel/                      Tassel model card, provenance, and checksums
|   `-- disease/                     Disease model card, metadata, and checksums
|-- training/
|   |-- notebooks/
|   |   |-- tassel/                  Tassel training notebooks
|   |   `-- disease/                 Disease training notebooks
|   `-- results/
|       |-- tassel/                  Tassel evaluation artefacts
|       `-- disease/                 Disease evaluation artefacts
|-- datasets/                        Dataset documentation and download metadata
|-- examples/
|   |-- tassel-counting/
|   |   |-- input/                   Small representative maize-field images
|   |   `-- output/                  Corresponding annotated results
|   `-- disease-screening/
|       |-- input/                   Small representative close-up leaf images
|       `-- output/                  Corresponding screening evidence
|-- tests/                           Unit, integration, and static contract tests
|-- docs/
|   |-- ASSESSMENT_INDEX.md          Supervisor requirement-to-evidence map
|   |-- requirements/                SRS, user stories, scope, and traceability
|   |-- design/
|   |   |-- architecture/            System and deployment architecture
|   |   |-- ai/                      AI logic and inference design
|   |   |-- database/                ERD and database design explanation
|   |   |-- repository/              Repository organization specification
|   |   `-- uml/                     BCE, activity, and sequence diagrams
|   |-- testing/                     Test strategy, cases, logs, and acceptance
|   |-- manuals/                     User manual and technical manual
|   |-- reports/                     Progress and technical reports
|   |-- presentations/               Assessed presentation material
|   `-- evidence/                    UI screenshots and result evidence
|-- coursework/                      Historical assessed submission packages
|-- index.html                       Project website entry point
`-- README.md                        Primary project and run guide
```

## 6. Directory Boundaries

### 6.1 Database

`database/` contains only executable database assets: schema scripts,
migrations, and intentional seed data. It does not contain maize images,
screenshots, UML diagrams, or reports.

The ERD is database design documentation and therefore belongs in
`docs/design/database/`. Uploaded maize images are runtime data stored through
the application and must never be committed to the repository.

### 6.2 Datasets and examples

`datasets/` documents the source, licence, pinned revision, expected layout,
download method, class mapping, and split policy for each dataset. Full datasets
remain external unless redistribution is explicitly permitted and necessary.

`examples/` contains only a small, reviewable selection of images needed for
demonstration and smoke tests. Every output example must identify its matching
input. Disease examples should use clear close-up leaf images; tassel examples
should represent the field conditions expected by the counting model.

### 6.3 Models and training

`models/deployment/` contains the exact runtime model files managed by Git LFS.
Documentation is separated by model task under `models/tassel/` and
`models/disease/`.

`training/` contains reproducible notebooks and experiment evidence. Source
notebooks and executed notebooks remain distinct. Evaluation outputs are grouped
by task so an assessor cannot confuse tassel-counting evidence with disease-
screening evidence.

### 6.4 Documentation

UML and BCE images are software-design evidence, not database contents or maize
examples. Reports, manuals, screenshots, presentations, requirements, and test
evidence each have separate documented locations.

Historical Week 10 and Week 11 packages remain available under `coursework/`
but do not control the current source of truth. Current documentation lives in
the relevant `docs/` category.

## 7. Existing File Mapping

| Current location | Target location |
|---|---|
| `maize_yolo26_colab.ipynb` | `training/notebooks/tassel/maize_yolo26_colab.ipynb` |
| `maize_yolo26_final (4).ipynb` | `training/notebooks/tassel/maize_yolo26_final.ipynb` |
| `training/notebooks/maize_disease_*` | `training/notebooks/disease/` |
| `training/results/*` | `training/results/disease/` |
| `ai/samples/*` | `examples/tassel-counting/input/` |
| `ai/results/*` | `examples/tassel-counting/output/` |
| `database/erd.*` | `docs/design/database/` |
| `database/schema*.sql` | `database/schema/` |
| `database/migrate*.sql` | `database/migrations/` |
| `database/seed_demo_users.sql` | `database/seeds/` |
| `docs/diagrams/bce/*` | `docs/design/uml/bce/` |
| `docs/diagrams/sequence/*` | `docs/design/uml/sequence/` |
| Main activity and sequence diagrams | `docs/design/uml/core-flow/` |
| User stories and code guide | `docs/requirements/` |
| Test plans and compliance audits | `docs/testing/` |
| UI screenshots | `docs/evidence/ui/` |
| Progress and technical reports | `docs/reports/` |
| `FYP-26-S2-7_Week10_Submission/` | `coursework/week-10/` |
| `codex_context_week10.md` | `coursework/week-10/notes/` |
| `backend/models/*.pt` | `models/deployment/` |
| Tassel model provenance | `models/tassel/` |
| Disease metadata and model card | `models/disease/` |

`README_CODE_ONLY.md` will be merged into the primary `README.md` and removed
to avoid competing run instructions.

## 8. Naming and Versioning Rules

- Directory and file names use lowercase kebab-case unless a required tool or
  established format uses another convention.
- Ambiguous suffixes such as `(2)` and `(4)` are removed.
- Migration files receive ordered prefixes without changing their SQL content.
- Model files have task-specific names rather than a generic `best.pt` name.
- Renamed files keep their history through Git-aware moves.
- Generated caches, logs, local environments, uploads, secrets, and temporary
  files remain excluded by `.gitignore`.

## 9. Runtime Model Configuration

Runtime model paths are explicit configuration values:

```text
TASSEL_MODEL_PATH=models/deployment/tassel-best.pt
DISEASE_MODEL_PATH=models/deployment/maize-disease.torchscript.pt
```

Defaults resolve from the repository root. Environment variables may override
the defaults for deployment without changing source code. Startup validation
must fail clearly when a path contains a Git LFS pointer instead of a real model
or when a model file is missing.

## 10. Assessment Entry Points

The root `README.md` will present:

1. Project overview and core tassel-counting objective.
2. Disease screening as an extended Agronomist capability.
3. Example inputs and outputs.
4. Architecture and technology stack.
5. VS Code quick start.
6. Model, dataset, and training information.
7. Testing instructions and recorded status.
8. Documentation index, limitations, and responsible-use statement.

`docs/ASSESSMENT_INDEX.md` maps each supervisor requirement to its current
repository evidence. The index covers requirements, architecture, AI logic,
database design, implementation, testing, manuals, reports, presentation, and
working prototype evidence.

## 11. Privacy and Repository Safety

- Do not commit the original supervisor workbook because it contains personal
  and contact information.
- Do not commit `.env`, database passwords, encryption keys, session secrets,
  user uploads, production backups, or private test data.
- Public examples must be licensed for redistribution or created by the team.
- Dataset documentation records licences and redistribution restrictions.
- A repository-wide secret and personal-information scan runs before commit.
- Existing public demo credentials are labelled as demonstration-only and must
  never be reused for a deployed public service.

## 12. Migration Strategy

The reorganization is performed on the existing feature branch and split into
small reviewable commits:

1. Add the target directories and sanitized assessment index.
2. Move database scripts and database design documentation.
3. Move UML, reports, manuals, screenshots, and coursework materials.
4. Move tassel and disease notebooks and result evidence.
5. Move example input and output images.
6. Move runtime models and update configurable path resolution.
7. Consolidate and repair README and documentation links.
8. Add repository-structure and link-integrity tests.

Each commit uses Git moves where possible. No historical commit metadata is
fabricated or rewritten.

## 13. Verification

The completed reorganization must pass all of the following checks:

- All 44 existing automated tests pass.
- New path and documentation-link tests pass.
- Both deployment models load from their new configured paths.
- The model files match their recorded SHA-256 values.
- Git LFS provides the full disease model rather than a pointer file.
- The backend health endpoint reports both inference services accurately.
- One tassel example completes an inference smoke test.
- One disease example completes a screening smoke test.
- All links in `README.md` and `docs/ASSESSMENT_INDEX.md` resolve.
- VS Code launch and test tasks work from the repository root.
- No local secret, personal-information workbook, cache, log, or user upload is
  tracked.
- `git status` is clean after verification.

## 14. Acceptance Criteria

The work is accepted when an assessor can start from `README.md`, locate every
required deliverable through `docs/ASSESSMENT_INDEX.md`, run the project from VS
Code, inspect both AI pipelines and their evidence, understand the database
design, and reproduce the recorded test command without encountering broken
paths or missing documentation.

The final structure must make clear that maize tassel counting is the primary
project objective and maize disease screening is a human-centred extension.
