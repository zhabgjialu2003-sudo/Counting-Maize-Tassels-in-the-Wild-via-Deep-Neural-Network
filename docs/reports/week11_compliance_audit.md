# FYP-26-S2-7 Week 11 Compliance Audit

Review date: 10 June 2026

Reference: SPP-FYP24S4-7 project plan by Sionggo Japit and the Week 11
documentation supplied by the project team.

## Overall Verdict

**Code and working prototype: compliant after the fixes recorded below.**

**Submission package: not yet ready for Week 11 submission.** The current
binary reports and presentation still describe the earlier Week 10 mock
prototype. They must be replaced with current Week 11 versions before
submission. The local implementation must also be committed and pushed so that
GitHub and GitHub Pages show the reviewed version.

The final-submission folder and AI PDF are excluded from this audit as
previously requested.

## Required Week 11 Deliverables

| Deliverable | Current evidence | Status |
|---|---|---|
| Project Progress Report | Only `Week10_Progress_Report.docx`; content says model integration is future work | Not ready |
| Preliminary Technical Report | Only `Week10_Technical_Report.docx`; implementation/results still describe mock fallback | Not ready |
| Presentation Slides | `Week10_Presentation.pptx`; slide content says `best.pt`, batch, PDF, and model registry are future work | Not ready |
| Project Website | `index.html` updated to Week 11 and real integration | Ready locally |
| Working Prototype | Frontend, Flask, PostgreSQL, encrypted storage, and real YOLO inference | Ready locally |

The required 30% real functional logic threshold is exceeded. The reviewed
prototype uses real logic for authentication, database persistence, AI
inference, reports, exports, role permissions, encrypted files, model
operations, and backup management.

## Working Prototype Evidence

- 11 frontend HTML pages.
- 47 declared Flask route handlers.
- 13 PostgreSQL tables in the current schema.
- `backend/models/best.pt` is tracked and is approximately 20.4 MB.
- 30 BCE diagrams and 30 sequence diagrams are present.
- 30 User Stories are mapped in BCE order from A.1 through E.5.
- The production API returns explicit errors when PostgreSQL operations fail;
  it no longer returns fabricated success data.
- `backend/server.py` checks PostgreSQL, the AI model, `SECRET_KEY`, and
  `FILE_ENCRYPTION_KEY` before starting the assessment demo.

## Verification Results

| Check | Result |
|---|---|
| Python syntax compilation | Pass |
| Automated compliance tests | 15/15 pass |
| PostgreSQL connection | Pass |
| `best.pt` model load | Pass |
| `/api/health` | HTTP 200 |
| Admin login | HTTP 200 |
| Users, fields, models, system, storage APIs | HTTP 200 |
| Real inference on `DJI_0243_2.JPG` | Pass: 123 detections, 0.4595 mean confidence, 2.25 s |
| Git diff whitespace check | Pass after README correction |

## User Story and BCE Order

The detailed mapping is in:

- `docs/other/FYP-26-S2-7_User_Story_Code_Guide.md`
- `docs/reports/bce_sequence_compliance_audit.md`

The implementation follows:

`Actor -> Boundary -> Control/API -> Entity -> response to Boundary`

Frontend role pages display their functions in the required sequence:

- Farmer: A.1-A.8
- Researcher: B.1-B.6
- Agronomist: C.1-C.5
- Administrator: D.1-D.6
- System/model lifecycle: E.1-E.5

## Fixes Made During This Audit

1. Removed remaining fake-success database fallbacks from reports, result
   flagging, training-run listing, administrator statistics, and storage
   statistics.
2. Restricted CORS to configured local and GitHub Pages origins.
3. Added strict production startup checks for signing and encryption keys.
4. Updated the root and backend README files to describe the real Week 11
   architecture.
5. Updated the project website to show YOLO26s, correct supervisor/team details,
   Week 11 evidence, and the real backend requirement.
6. Replaced the Week 10 mock demo script with a Week 11 integrated demo flow.
7. Strengthened the automated test that prevents production mock data from
   returning.

## Blocking Findings Before Submission

### Critical

1. Replace the old Week 10 progress report, technical report, and presentation.
   Their current claims contradict the implementation and would make the
   submission appear incomplete.
2. Commit and push the local working tree. The public GitHub repository and
   GitHub Pages site do not yet contain the reviewed local changes.
3. Configure non-default `SECRET_KEY` and `FILE_ENCRYPTION_KEY` in
   `backend/.env`. The strict server now refuses an insecure startup.

### Important

1. The GitHub Pages prototype is a static frontend whose API points to
   `http://localhost:5000`. The website is publicly viewable, but interactive
   functions require the assessor's browser to have access to the local backend.
   Demonstrate it from the prepared assessment computer or deploy the Flask API.
2. `docs/other/FYP-26-S2-7_Complete_Document.md` begins with a ZIP/DOCX file
   signature and is not a real Markdown file. Rename or regenerate it with the
   correct `.docx` extension.
3. Add activity diagrams to the technical report if they are required literally
   by the Week 11 template. The repository currently contains BCE and sequence
   diagrams, but no separately labelled activity-diagram set.
4. Access tokens are accepted in image URL query strings for browser image
   display. This is workable for a local prototype but may expose tokens in
   browser history or logs; use authenticated blob fetching before production.

## Technical Report Coverage Checklist

| Section | Evidence | Status |
|---|---|---|
| Title/team/supervisor/assessor/date | Available, but old files contain inconsistent details | Update required |
| Abstract and introduction | Present in old report | Update required |
| Literature review | Present | Review citations |
| Methodology and architecture | Present plus current code/ERD | Update required |
| Functional requirements/User Stories/use cases | 30 stories and BCE mapping | Ready |
| Test strategy | Existing plan plus automated tests | Update results |
| Implementation/UI/modules/sequence | Code, screenshots, BCE, sequence | Ready |
| Results and objective comparison | Real model/API evidence available | Rewrite required |
| Conclusion/contributions/limitations | Old limitations are obsolete | Rewrite required |
| References and appendices | Existing base material | Verify |

## Submission Decision

Do not submit the current Week 10 DOCX/PPT files as the Week 11 deliverables.
The implementation is strong enough for Week 11, but the package is only
compliant after the three critical actions above are completed.
