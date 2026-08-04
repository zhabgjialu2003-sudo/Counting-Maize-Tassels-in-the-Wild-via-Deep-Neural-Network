# GitHub Submission Readiness Design

## Objective

Prepare the public repository for final academic assessment so that an assessor
can understand, run, verify, and trace the project from the default GitHub page.
The reorganization must preserve the existing contribution history and must be
committed under Zhang Jialu's GitHub identity.

## Success Criteria

- The latest verified implementation is visible on the default `main` branch.
- The root README provides a concise assessor-first path through the project.
- Installation, PostgreSQL setup, migrations, application startup, mobile
  access, testing, model provenance, dataset provenance, and limitations are
  documented without exposing credentials.
- The documented automated-test baseline matches a fresh verification run.
- GitHub automatically performs appropriate repository and code checks on
  pushes and pull requests.
- Current deliverables are clearly separated from historical coursework.
- Repository metadata, documentation links, pull requests, and GitHub Pages
  present a coherent final-submission state.
- Existing commits remain attributable to their original authors; new work is
  authored as `Zhang Jialu <zhabgjialu2003@gmail.com>` with no AI co-author
  trailer.

## Chosen Approach

Use a compatibility-preserving standards pass rather than an aggressive
history rewrite. Improve navigation and verification in place, retain the
historical `coursework/` archive, and merge the completed feature branch with a
normal merge commit. This preserves evidence while making the current system
the obvious entry point.

## Repository Entry Point

The root README will lead with the project purpose and its five stakeholder
groups: Farmer, Researcher, Agronomist, Admin, and System. It will then present:

1. implemented tassel-counting and disease-screening capabilities;
2. a compact architecture and request flow;
3. a quick-start path for VS Code and command-line users;
4. desktop and mobile entry URLs;
5. model and dataset provenance;
6. the latest test result and verification command;
7. responsible-use limitations; and
8. direct links to the assessment evidence index and current deliverables.

Historical coursework will remain available but will be labelled as archived
evidence that does not supersede the current source, tests, or documentation.

## GitHub Standards

Add the following repository-level controls:

- a GitHub Actions workflow for deterministic syntax, structure, migration,
  security, and automated-test checks;
- `CONTRIBUTING.md` with setup, branch, test, and commit conventions;
- `SECURITY.md` explaining safe vulnerability reporting and secret handling;
- a pull request template with testing, migration, documentation, and privacy
  checks; and
- repository description, homepage, and relevant topic tags.

No open-source licence will be added because the owner has not selected a legal
licensing model. The repository will not claim permissions that have not been
granted.

## Validation and Evidence

Before merging, the work will be validated by:

- checking every Markdown link in the assessor-facing entry documents;
- checking Python compilation and JavaScript syntax;
- checking migration discovery and applied migration status;
- running the complete local automated test suite against PostgreSQL;
- scanning tracked files for likely credentials and generated runtime data;
- verifying Git LFS model pointers and materialized deployment artefacts;
- synchronizing CodeGraph and reviewing the affected code paths; and
- reviewing the final staged diff before commit.

The latest verified count will be recorded in `docs/testing/TEST_RESULTS.md` and
the README only after the final test run completes.

## Pull Request and Default Branch

Pull request #4 will receive the submission-readiness changes and will be
merged into `main` with a normal merge commit. Squashing and history rewriting
are prohibited for this task. Pull request #2 will be closed with a concise
note that its work is superseded by the integrated final branch. After the
merge, the default branch, GitHub Pages status, CI status, and repository
metadata will be verified.

## Safety and Scope

- Never commit database passwords, API keys, encryption keys, farmer uploads,
  or local environment files.
- Do not remove historical assessed files merely to reduce visual clutter.
- Do not rewrite existing commits or change other contributors' authorship.
- Do not publish a cloud deployment as part of this organization task.
- Do not claim that long-running model training was repeated when verification
  used the recorded training artefacts and automated tests.
