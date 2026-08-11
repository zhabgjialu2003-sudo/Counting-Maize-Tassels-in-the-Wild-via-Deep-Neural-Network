# Counting Maize Tassels in the Wild via Deep Neural Network

[![Repository checks](https://github.com/zhabgjialu2003-sudo/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/actions/workflows/quality.yml/badge.svg)](https://github.com/zhabgjialu2003-sudo/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/actions/workflows/quality.yml)
[![Python 3.11–3.12](https://img.shields.io/badge/Python-3.11%E2%80%933.12-3776AB.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-required-4169E1.svg)](https://www.postgresql.org/)
[![Git LFS](https://img.shields.io/badge/models-Git%20LFS-F64935.svg)](https://git-lfs.com/)

An assessment-ready final-year project for detecting and counting maize tassels
in field images. It combines real YOLO inference, calibrated maize leaf-disease
screening, PostgreSQL persistence, secure image handling, role-based workflows,
and an installable mobile Progressive Web App (PWA).

- Project website: [GitHub Pages](https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/)
- Assessment entry point: [Assessment Evidence Index](docs/ASSESSMENT_INDEX.md)
- User instructions: [User Manual](docs/manuals/USER_MANUAL.md)
- Developer instructions: [Technical Manual](docs/manuals/TECHNICAL_MANUAL.md)

## Project scope

| Actor | Implemented workflow |
|---|---|
| Farmer | Capture or upload field images, count and highlight tassels, review history, use the leaf-screening assistant, and manage an email-based account. |
| Researcher | Review and flag results, compare validated models, analyse history, access approved datasets, and export reports. |
| Agronomist | Review assigned field evidence, monitor growth and anomalies, assess disease-screening records, and provide recommendations. |
| Admin | Manage users, permissions, datasets, access policies, storage, logs, backups, and model deployment. |
| System | Validate and preprocess images, run inference, record model provenance, support training/evaluation, and expose health checks. |

The primary research objective is maize-tassel counting. Disease screening is a
human-centred Agronomist extension: uncertain, unsupported, or poor-quality
images produce a safe retake/review response instead of a forced diagnosis.

## Key capabilities

- Single and batch JPG/PNG upload with mobile data-saving preparation.
- Retry-safe, user-scoped upload idempotency for unstable 4G/5G connections.
- Fast and accurate YOLO tassel-counting modes with bounding-box evidence.
- Encrypted image storage and authenticated image delivery.
- PostgreSQL-backed users, images, results, fields, reviews, reports, models,
  datasets, logs, backups, and schema migrations.
- Model comparison guarded by approved directories and SHA-256 verification.
- Auditable results containing model version, inference mode, confidence,
  quality status, and protected asset URLs without server path disclosure.
- Responsive desktop views and an installable mobile PWA.

## Architecture

```text
Desktop browser / Mobile PWA
              |
              v
Flask API: authentication, validation, authorization, rate limits
              |
      +-------+--------------------+
      |                            |
      v                            v
Encrypted image storage     Tassel / disease model
      |                            |
      +-------------+--------------+
                    v
     PostgreSQL results, provenance, reviews and audit logs
                    |
                    v
       Role-specific dashboards, history and reports
```

More detail is available in the [system architecture](docs/design/architecture/system-architecture.md),
[AI logic design](docs/design/ai/ai-logic-design.md), and
[PostgreSQL ERD](docs/design/database/erd.md).

## Repository map

```text
backend/       Flask API, security, persistence, inference and training controls
frontend/      Desktop pages, mobile PWA, shared API and authentication clients
database/      Canonical schema, ordered migrations and privacy-safe demo seeds
models/        Git LFS deployment artefacts, model cards and provenance
training/      Training notebooks, evaluation outputs and dataset manifests
datasets/      Dataset sources, licences and reproducible download guidance
examples/      Small demonstration inputs and expected annotated outputs
tests/         Unit, integration, security, mobile and repository contract tests
docs/          Requirements, designs, test evidence, manuals and reports
coursework/    Archived assessed packages retained for submission history
```

`coursework/` is historical evidence. Current source code, requirements,
verification results, and manuals are linked through
[`docs/ASSESSMENT_INDEX.md`](docs/ASSESSMENT_INDEX.md).

## Prerequisites

- Python 3.11 or 3.12
- PostgreSQL
- Git and Git LFS
- VS Code with the Python extension (recommended)

## Quick start in VS Code

Clone the repository and materialize the deployment models:

```powershell
git clone https://github.com/zhabgjialu2003-sudo/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network.git
Set-Location Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network
git lfs install
git lfs pull
```

Create the environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` locally. Set a PostgreSQL password, a long random
`SECRET_KEY`, and a Fernet `FILE_ENCRYPTION_KEY`. Never commit this file.

Create the database and apply the canonical schema and migrations:

```powershell
createdb -U postgres maize_detector
psql -U postgres -d maize_detector -f database\schema\schema_postgresql.sql
python -m backend.migrations
python -m backend.migrations --check
python -m backend.scripts.bootstrap_admin
```

The bootstrap command prompts for the first administrator email, name, and a
hidden password. The repository contains no deployable default password. Sample
identities remain disabled until an administrator assigns individual passwords.

For a local assessment demonstration, set `DEMO_ACCESS_ENABLED=true` and a
policy-compliant `DEMO_ACCOUNT_PASSWORD` in the ignored `backend/.env`, then run:

```powershell
python -m backend.scripts.configure_demo_accounts
```

This explicit command configures the fixed Farmer, Researcher, Agronomist, and
Admin demo identities. The login-page helper is loopback-only by default. A
controlled same-Wi-Fi demonstration can additionally set
`DEMO_ACCESS_ALLOW_PRIVATE_NETWORK=true`; public hosts never receive the
configured password.

Run the VS Code launch configuration named `Run Maize Detector`, or start the
production-oriented local server directly:

```powershell
python backend\server.py
```

Open the following authenticated entry points:

| Interface | URL |
|---|---|
| Desktop login | `http://127.0.0.1:5000/frontend/pages/login.html` |
| Mobile Farmer interface | `http://127.0.0.1:5000/frontend/pages/mobile.html` |
| API health check | `http://127.0.0.1:5000/api/health` |

The mobile interface does not replace or modify the desktop interface. Both use
the same authenticated API and PostgreSQL data.

## Deployment models

Deployment weights are tracked with Git LFS and verified before use.

| Task | Runtime file | SHA-256 |
|---|---|---|
| Tassel counting | `models/deployment/tassel-best.pt` | `37bca6b8e817d911424dbd22f720f9cbe00248036e0fc6305ef853f8b38d9913` |
| Disease screening | `models/deployment/maize-disease.torchscript.pt` | `4f48a440e2eb35bef220107f9e777f9a3a10dc8fa0b79e0296a022cba700ef17` |

See [tassel model provenance](models/tassel/MODEL_PROVENANCE.md), the
[disease model card](models/disease/MODEL_CARD.md), and
[training and evaluation guidance](training/README.md).

## Dataset policy

Large third-party datasets are not committed as a miscellaneous image dump.
[`datasets/README.md`](datasets/README.md) records sources, licences, expected
layout, and download instructions. Small redistribution-safe examples are kept
under [`examples/`](examples/) for assessment and UI verification.

## Verification

Run the complete local suite against the configured PostgreSQL database:

```powershell
python -m unittest discover -s tests -v
```

The latest verified baseline is **122 automated tests with zero failures**.
Exact environment notes, real-model smoke tests, and SHA-256 evidence are in
[`docs/testing/TEST_RESULTS.md`](docs/testing/TEST_RESULTS.md).

GitHub Actions performs fast deterministic checks on each push and pull request.
The full PostgreSQL- and model-backed suite remains the authoritative local
acceptance run because it uses 103 MB of Git LFS deployment artefacts and the
configured database.

## Assessment deliverables

- [User stories](docs/requirements/user-stories.md)
- [Extension user stories](docs/requirements/user-story-extensions.md)
- [Requirement-to-code guide](docs/requirements/user-story-code-guide.md)
- [Extended technical documentation](docs/reports/technical/preliminary-technical-documentation-extended.docx)
- [Current regression test cases](docs/testing/current-regression-test-cases.md)
- [BCE and sequence diagrams](docs/design/uml/)
- [Extended ERD](docs/design/database/erd-extended.mmd)
- [UI and output evidence](docs/evidence/)

The original 30 user stories are retained. The extension package adds 15
implemented stories across Farmer, Researcher, Agronomist, Admin, and System.

## Responsible use and limitations

- Counts vary with resolution, viewpoint, occlusion, growth stage, lighting,
  camera height, and field density.
- Disease screening supports only the classes and thresholds in its model card.
- Screening is a field decision-support aid, not a laboratory diagnosis or a
  pesticide prescription.
- Results with weak evidence require a better image or Agronomist review.
- Private farmer uploads, database credentials, encryption keys, and local
  environment files must never be committed.

## Project governance

- Contribution workflow: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Repository licence: no open-source licence has been granted

Copyright remains with the project contributors. Public visibility does not by
itself grant permission to copy, redistribute, or reuse the source or models.
