# Counting Maize Tassels in the Wild via Deep Neural Network

A final-year project that combines real maize-tassel detection, secure image
handling, PostgreSQL result storage, desktop workflows, and a mobile PWA. The
primary objective is automatic tassel counting from field images. A calibrated
maize leaf-disease screening assistant is included as an Agronomist extension.

## Core capabilities

- Count and highlight maize tassels with the team-trained YOLO26s model.
- Accept single or batch images and preserve analysis history.
- Store uploaded image content securely and record results in PostgreSQL.
- Support Farmer, Researcher, Agronomist, and Admin permissions.
- Provide mobile-friendly capture and upload through an installable PWA.
- Screen close-up maize leaves for four supported disease outcomes.
- Reject low-quality, unfamiliar, or low-confidence leaf images rather than
  forcing a diagnosis.
- Export results and retain model and testing evidence for assessment.

## Evidence preview

| Input | Annotated tassel result |
|---|---|
| [`DJI_0243 (2).JPG`](examples/tassel-counting/input/DJI_0243%20(2).JPG) | [`DJI_0243 (2)_annotated.jpg`](examples/tassel-counting/output/DJI_0243%20(2)_annotated.jpg) |

More inputs and expected outputs are available under [`examples/`](examples/).

## System flow

```text
Desktop or mobile browser
          |
          v
Flask API: authentication, validation and authorization
          |
          +----> encrypted image storage
          |
          +----> tassel detector or disease-screening model
          |
          v
PostgreSQL result, audit and model records
          |
          v
Role-specific result, history, report and export views
```

Detailed architecture, AI logic, database design, tests, reports, and manuals
are indexed in [`docs/ASSESSMENT_INDEX.md`](docs/ASSESSMENT_INDEX.md).

## Final documentation package

- [Final Requirements, Design, and Testing document](docs/reports/technical/final-requirements-design-testing.docx)
- [Extension User Stories](docs/requirements/user-story-extensions.md)
- [Extended system description](docs/design/system-description-extended.md)
- [Editable Use Case, BCE, and Sequence diagrams](docs/design/uml/extensions/)
- [Editable extended ERD](docs/design/database/erd-extended.mmd)
- [Current regression test cases](docs/testing/current-regression-test-cases.md)

The original 30 User Stories remain unchanged. The extension package adds 15
implemented stories grouped under Farmer, Researcher, Agronomist, Admin, and
System.

## Repository structure

```text
backend/       Flask API, security, persistence and inference integration
frontend/      Desktop pages, mobile pages and PWA assets
database/      SQL schema, ordered migrations and demo seeds
models/        Git LFS deployment models, model cards and provenance
training/      Tassel and disease notebooks with evaluation evidence
datasets/      Dataset sources, licences and download guidance
examples/      Small demonstration inputs and expected outputs
tests/         Automated unit, integration and static contract tests
docs/          Requirements, design, testing, manuals, reports and evidence
coursework/    Historical assessed submission packages
```

## Prerequisites

- Windows, macOS or Linux
- Python 3.11 or 3.12
- PostgreSQL
- Git LFS
- VS Code with the Python extension, recommended

## Run in VS Code

```powershell
git lfs install
git lfs pull
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` locally. Set the PostgreSQL password, a long random
`SECRET_KEY`, and a Fernet `FILE_ENCRYPTION_KEY`. Never commit this file.

Create the database and apply the current schema:

```powershell
createdb -U postgres maize_detector
psql -U postgres -d maize_detector -f database\schema\schema_postgresql.sql
python -m backend.migrations
python -m backend.migrations --check
```

Start the application with the VS Code `Run Maize Detector` launch
configuration, or run:

```powershell
python backend\server.py
```

Open:

```text
http://127.0.0.1:5000/frontend/pages/login.html
```

The mobile entry page is:

```text
http://127.0.0.1:5000/frontend/pages/mobile.html
```

See the [User Manual](docs/manuals/USER_MANUAL.md) and
[Technical Manual](docs/manuals/TECHNICAL_MANUAL.md) for complete instructions.

## Deployment models

| Task | Runtime file | SHA-256 |
|---|---|---|
| Tassel counting | `models/deployment/tassel-best.pt` | `37BCA6B8E817D911424DBD22F720F9CBE00248036E0FC6305EF853F8B38D9913` |
| Disease screening | `models/deployment/maize-disease.torchscript.pt` | `4F48A440E2EB35BEF220107F9E777F9A3A10DC8FA0B79E0296A022CBA700EF17` |

Model paths can be overridden with `TASSEL_MODEL_PATH` and
`DISEASE_MODEL_PATH`. Startup checks reject missing files and Git LFS pointer
files. Provenance and model cards are under [`models/`](models/).

## Recorded disease evaluation

| Evaluation set | Samples | Accuracy | Macro F1 | Accepted accuracy | Coverage |
|---|---:|---:|---:|---:|---:|
| Internal test | 794 | 96.85% | 95.70% | 99.61% | 63.85% |
| External field test | 523 | 98.47% | 95.46% | 99.77% | 83.75% |
| PlantDoc field audit | 14 | 71.43% | 69.44% | 87.50% | 57.14% |
| CDS field test | 509 | 99.21% | 99.31% | 100.00% | 84.48% |

The PlantDoc result is advisory because only 14 supported samples were
available. Full thresholds, confidence intervals, dataset revisions, leakage
checks, and deployment gates are in
[`training/results/disease/metadata.json`](training/results/disease/metadata.json).

## Tests

```powershell
python -m unittest discover -s tests -v
```

The current baseline is 78 automated tests. The latest verified result is recorded in
[`docs/testing/TEST_RESULTS.md`](docs/testing/TEST_RESULTS.md).

## Responsible use and limitations

- Tassel counts depend on image resolution, viewpoint, occlusion, lighting and
  field conditions.
- Disease screening supports only the classes listed in its model card.
- A supported output is a field-screening aid, not a laboratory diagnosis or
  pesticide prescription.
- PlantDoc evidence is explicitly marked advisory because of its small supported
  sample count.
- Private farmer uploads, local database credentials and encryption keys must
  never be committed.

## Assessment and project history

- [Assessment Evidence Index](docs/ASSESSMENT_INDEX.md)
- [Privacy-safe Project Deliverables](docs/requirements/PROJECT_DELIVERABLES.md)
- [Training and Evaluation](training/README.md)
- [Database ERD](docs/design/database/erd.md)
- [Historical Coursework Archive](coursework/README.md)
