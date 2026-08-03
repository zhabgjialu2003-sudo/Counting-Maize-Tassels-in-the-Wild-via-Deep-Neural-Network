# Project Deliverables

This document is a privacy-safe summary of the supplied CSCI321 Supervisor
Project Plan. It omits student identifiers, personal email addresses, and phone
details while retaining the requirements that govern this repository.

## Project objective

Develop a reasonably complex software application that uses a robust deep
neural network to read maize-field images, count maize tassels automatically,
and visualize the result with acceptable accuracy. The system should reduce
manual counting effort and support large-scale agricultural phenotype analysis.

The solution may be delivered as a web or mobile application and must provide
secure transfer and storage of sensitive application data.

## Required technical areas

- Deep learning and maize-image analysis.
- Data analysis and experiment evaluation.
- Web or mobile application development.
- Functional, non-functional, interface, and security requirements.
- System architecture and detailed module design.
- AI logic and model design.
- Database design where applicable.
- Unit, integration, and system testing.
- Clear technical and user documentation.

## Project stages and expected evidence

| Stage | Required work | Repository evidence |
|---|---|---|
| Research and requirements | Literature review, related systems, SWOT analysis, requirements specification | `docs/requirements/` |
| Analysis and design | Architecture, AI logic, database design, detailed interactions | `docs/design/` |
| Prototype | Website and working implementation of planned functionality | `backend/`, `frontend/`, `index.html` |
| Implementation | Completed modules with maintained documentation | Source directories and Git history |
| Testing | Unit, integration and system tests, test cases and logs | `tests/`, `docs/testing/` |
| Final documentation | Current technical manual and user manual | `docs/manuals/` |
| Results | Functional evidence, metrics, discussion, limitations and objective comparison | `training/results/`, `docs/evidence/` |
| Presentation | Slides, demonstration evidence and prepared project website | `docs/presentations/`, `index.html` |
| Final product | Source code, executable model artefacts and evidence of implemented functions | Repository, Git LFS models and examples |

## Technical report coverage

The final technical documentation should include:

- title and project context;
- abstract, problem statement, objectives and scope;
- literature review and identified gaps;
- methodology, tools and development process;
- system architecture;
- functional requirements and user stories;
- test strategy and test results;
- implementation details, UI and module interactions;
- challenges, constraints and solutions;
- results, objective comparison and limitations;
- conclusion, references and supporting appendices.

## Demonstration expectations

The live demonstration should prioritize the core workflow:

1. Open the project website or application.
2. Authenticate with a demonstration account.
3. Upload a valid maize image.
4. Run real model inference.
5. Display the tassel count and annotated image.
6. Show stored history and role-appropriate functions.
7. Demonstrate mobile access and the Agronomist extension where time permits.

## Repository interpretation

Maize tassel counting remains the primary assessed objective. Leaf-disease
screening is an additional Agronomist capability that demonstrates extensible
AI design and human-centred field support. It does not replace or obscure the
core tassel-counting workflow.

