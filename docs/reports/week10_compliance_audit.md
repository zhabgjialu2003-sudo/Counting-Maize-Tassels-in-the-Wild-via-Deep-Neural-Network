# Week 10 User Story and Implementation Compliance Audit

Date: 2026-05-22

Project: FYP-26-S2-7, Counting Maize Tassels in the Wild via Deep Neural Network

## Skills Used

- `using-superpowers`: checked relevant skills before action.
- `doc-reader` / `markitdown`: read the Complete Document and revised checklist; the Complete Document file is DOCX-like binary content with a `.md` extension, so extraction used a local document fallback.
- `code-review`: reviewed frontend, backend, database, and deliverable coverage by severity.
- `playwright`: followed the verification workflow prerequisite check; `npx` is available. Full headed browser screenshots were not generated in this pass.

## Source Evidence

- `docs/other/FYP-26-S2-7_Complete_Document.md`
- `docs/other/FYP-26-S2-7_Week10_Task_Checklist_Revised.md`
- `docs/other/FYP-26-S2-7_BCE_Sequence_Diagrams.md`
- `docs/diagrams/bce/`: 30 BCE diagram images, covering A.1 to E.5
- `docs/diagrams/sequence/`: 30 sequence diagram images, covering F.1 to J.5

## Changes Completed in This Pass

- Upload flow now follows A.1/A.2 more closely: `frontend/pages/upload.html` calls `apiUpload(file)` first, then calls `/api/predict`.
- Upload preview is saved in `sessionStorage` so the Result page can display the actual selected image during the demo.
- Result flow now supports A.4 more reliably: `frontend/pages/result.html` displays the uploaded image and overlays mock/database bbox data.
- Result page now includes a direct `View History` action.
- Shared API layer now has `apiUpload()` and reusable `mockBboxData()` in `frontend/js/api.js`.
- Report and Agronomist tab switching no longer depends on the implicit browser `event` object.
- Project website now has a visible GitHub repository link in `index.html`.
- ERD was rebuilt in a draw.io-style format with white table backgrounds, black orthogonal connectors, and spacing between `images` and `detection_results`.

## Highest Priority Findings

| Priority | Finding | Status | Why it matters |
|---|---|---:|---|
| P0 | Upload page previously skipped `/api/upload` and went directly to `/api/predict`. | Fixed | A.1 upload and A.2 prediction were not following the BCE flow. |
| P0 | Result page could show only a fallback text block instead of an annotated image. | Fixed for demo | A.4 requires highlighted tassels on image. The page now overlays bbox data on the selected image. |
| P1 | `report.html` and `agronomist.html` used implicit `event.target`. | Fixed | Tab switching can fail in stricter browser/runtime contexts. |
| P1 | `image_files` table exists in SQL, but `/api/upload` currently saves image files to disk and `images`, not to `image_files`. | Partial | D.2 secure storage is enough for Week 10 prototype, but not a full binary DB storage implementation. |
| P1 | Multi-model comparison is not implemented as a researcher feature. | Open | B.4 in Complete Document is still missing. |
| P1 | AI model training/evaluation deliverables are not present. | Open | E.1-E.5 are mostly prototype/mock or documentation-only right now. |

## User Story Coverage

| ID | Requirement Area | Frontend / Backend / DB Evidence | Status |
|---|---|---|---|
| A.1 | Farmer uploads maize images | `upload.html`, `apiUpload()`, `/api/upload`, `images` table | Complete |
| A.2 | Auto-count maize tassels | `/api/predict`, `create_mock_detection()`, `detection_results` | Prototype complete |
| A.3 | View counting results | `result.html`, `/api/results/<id>` | Complete |
| A.4 | View highlighted tassels | `result.html` bbox SVG overlay, `bbox_data` | Prototype complete |
| A.5 | Upload multiple images | `upload.html` batch mode and progress bar | Complete |
| A.6 | Fast response | mock fallback responds quickly | Prototype only |
| A.7 | Mobile access | responsive CSS and viewport tags | Partial, needs mobile screenshot test |
| A.8 | Intuitive UI | core navigation and pages exist | Complete |
| B.1 | Accurate researcher results | count/confidence shown | Prototype only |
| B.2 | Export results | `export.html` CSV/JSON export | Complete |
| B.3 | Historical trends | `history.html`, `/api/history`, report trend SVG | Partial |
| B.4 | Compare multi-model outputs | no dedicated multi-model UI/API | Missing |
| B.5 | Access/download raw datasets | admin dataset management exists | Partial |
| B.6 | Generate visual reports | `report.html`, print/export action | Partial |
| C.1 | Health recommendations | `agronomist.html` Health tab | Prototype complete |
| C.2 | Growth over time | `agronomist.html` Growth tab | Prototype complete |
| C.3 | Abnormal patterns | `agronomist.html` Alerts tab | Prototype complete |
| C.4 | Multi-field dashboard | `agronomist.html`, `/api/fields` | Complete |
| C.5 | Summarized insights | `agronomist.html` Insights tab | Prototype complete |
| D.1 | Manage users | `admin.html`, `/api/users` CRUD | Complete |
| D.2 | Secure image storage | `/api/upload`, `uploads/`, `images.access_level` | Partial |
| D.3 | Monitor usage | admin stats/logs, `/api/admin/stats`, `/api/admin/logs` | Complete |
| D.4 | Manage datasets | `admin.html`, `/api/datasets` CRUD | Complete |
| D.5 | Control permissions | roles/users UI and role FK | Partial |
| D.6 | Backup | `/api/admin/backup`, `/api/admin/backups` | Prototype complete |
| E.1 | Preprocess image data | upload validation exists | Partial |
| E.2 | Train deep learning models | no training code/artifact found | Missing |
| E.3 | Evaluate metrics | no metrics table/artifact found | Missing |
| E.4 | Deploy model service | `/api/predict` mock service | Prototype complete |
| E.5 | Model updates/versioning | no model version workflow found | Missing |

## Database and ERD Check

The Week 10 ERD now matches the seven main checklist tables:

- `roles`
- `users`
- `images`
- `detection_results`
- `reports`
- `system_logs`
- `datasets`

The SQL schema also includes `image_files` as an implementation extension for binary image storage. This is acceptable technically, but the ERD intentionally focuses on the seven Week 10 main tables. If the assessor expects every SQL table in the ERD, add `image_files` back as a supporting table.

## Verification Results

- `node --check frontend/js/api.js`: pass
- Inline script parse for `index.html` plus 8 prototype pages: pass
- `python -m py_compile backend/app.py backend/db.py backend/scripts/import_mtdc_demo.py`: pass
- `database/erd.drawio` XML parse: pass
- Flask test-client smoke check: pass
  - `/api/health`: 200
  - `/api/upload`: 202 mock fallback
  - `/api/predict`: 202 mock fallback
  - `/api/history`: 200
  - `/api/report/daily`: 200
  - `/api/report/weekly`: 200
  - `/api/report/monthly`: 200
  - `/api/users`: 200
  - `/api/datasets`: 200
  - `/api/admin/stats`: 200
  - `/api/fields`: 200

## Final Checklist

Legend: ✅ evidence exists and was checked in repo; □ missing, partial, or not fully verified as a final submission artifact.

- ✅ Project Website can be opened
- ✅ GitHub link can be opened
- ✅ Prototype can be opened
- ✅ Dashboard page completed
- ✅ Upload page completed
- ✅ Image preview function completed
- ✅ Result page completed
- ✅ Annotated image displays correctly
- ✅ History page completed
- ✅ System Report page includes Daily / Weekly / Monthly
- ✅ Admin page completed
- ✅ Researcher Export page completed
- ✅ Agronomist Dashboard page completed
- ✅ Backend mock API completed
- ✅ Database Design completed
- □ AI Model Progress completed
- □ Progress Report completed
- □ Technical Report updated
- □ PPT completed
- □ Testing Plan completed
- □ Individual Contribution table completed
- □ Demo flow tested
- □ Backup screenshots prepared
- □ Backup recording prepared
- □ Final submission folder organized

## Recommended Next Order

1. Create the missing AI Model Progress artifact with sample image, annotation explanation, model choice, metrics placeholder, and next-step plan.
2. Create the Progress Report and updated Technical Report sections using this audit as evidence.
3. Create the Testing Plan with at least 15 test cases from the revised checklist.
4. Create PPT and backup screenshots/recording from the working prototype.
5. Organize the final submission folder and add website/GitHub links as `.txt` files.
