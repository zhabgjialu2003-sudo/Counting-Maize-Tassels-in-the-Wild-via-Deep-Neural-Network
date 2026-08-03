# Assessment Evidence Index

This page is the assessor's entry point to the current project evidence. The
root `README.md` explains how to run the system; this index maps the supervisor
requirements to their repository locations.

## Project definition and requirements

| Evidence | Location |
|---|---|
| Privacy-safe supervisor deliverables summary | [Project Deliverables](requirements/PROJECT_DELIVERABLES.md) |
| User stories | [User Stories](requirements/user-stories.md) |
| Requirement-to-code traceability | [User Story Code Guide](requirements/user-story-code-guide.md) |

## Analysis and design

| Evidence | Location |
|---|---|
| System architecture | [System Architecture](design/architecture/system-architecture.md) |
| AI logic design | [AI Logic Design](design/ai/ai-logic-design.md) |
| Database design | [PostgreSQL ERD](design/database/erd.md) |
| BCE diagrams | [BCE diagram directory](design/uml/bce/) |
| Sequence diagrams | [Sequence diagram directory](design/uml/sequence/) |
| Core activity and sequence flow | [Core-flow directory](design/uml/core-flow/) |
| Repository organization | [Repository Reorganization Design](design/repository/2026-08-03-repository-reorganization-design.md) |

## Implementation

| Component | Location |
|---|---|
| Flask API and inference integration | [`backend/`](../backend/) |
| Desktop and mobile PWA | [`frontend/`](../frontend/) |
| PostgreSQL schema and migrations | [`database/`](../database/) |
| Deployment model artefacts | [`models/deployment/`](../models/deployment/) |
| Project website | [`index.html`](../index.html) |

## AI training and evaluation

| Evidence | Location |
|---|---|
| Tassel training notebooks | [`training/notebooks/tassel/`](../training/notebooks/tassel/) |
| Disease training notebooks | [`training/notebooks/disease/`](../training/notebooks/disease/) |
| Tassel model documentation | [`models/tassel/`](../models/tassel/) |
| Disease model documentation | [`models/disease/`](../models/disease/) |
| Disease evaluation evidence | [`training/results/disease/`](../training/results/disease/) |
| Tassel input and annotated examples | [`examples/tassel-counting/`](../examples/tassel-counting/) |
| Disease-screening examples | [`examples/disease-screening/`](../examples/disease-screening/) |

## Testing and acceptance

| Evidence | Location |
|---|---|
| Automated tests | [`tests/`](../tests/) |
| Test strategy and cases | [`docs/testing/`](testing/) |
| Latest verified results | [Test Results](testing/TEST_RESULTS.md) |
| Historical compliance audits | [`docs/testing/audits/`](testing/audits/) |

## Manuals, reports and presentation

| Evidence | Location |
|---|---|
| User manual | [User Manual](manuals/USER_MANUAL.md) |
| Technical manual | [Technical Manual](manuals/TECHNICAL_MANUAL.md) |
| Progress reports | [`docs/reports/progress/`](reports/progress/) |
| Technical reports | [`docs/reports/technical/`](reports/technical/) |
| AI model report | [`docs/reports/model/`](reports/model/) |
| Presentation slides | [`docs/presentations/`](presentations/) |
| UI and output evidence | [`docs/evidence/`](evidence/) |

## Historical coursework

Historical assessed packages are retained in [`coursework/`](../coursework/).
They provide submission history but do not override the current source code,
manuals, tests, or technical documentation linked above.

