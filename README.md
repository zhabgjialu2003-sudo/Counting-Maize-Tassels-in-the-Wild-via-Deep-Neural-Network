# Counting Maize Tassels in the Wild via Deep Neural Network

**FYP-26-S2-7 | Week 11 integrated working prototype**

This project detects and counts maize tassels from field images with the team's
trained YOLO26s model. The web application provides role-based workflows for
Farmers, Researchers, Agronomists, Administrators, and system/model operations.

- Project website: https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/
- Repository: https://github.com/zhabgjialu2003-sudo/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network
- Local API: `http://127.0.0.1:5000`

## Week 11 Status

- Real inference uses `backend/models/best.pt`.
- PostgreSQL is required; production routes do not return fabricated success data.
- 30 User Stories are implemented in BCE order: A.1-A.8, B.1-B.6,
  C.1-C.5, D.1-D.6, and E.1-E.5.
- 30 BCE diagrams and 30 sequence diagrams are included.
- 11 role-oriented frontend pages and 47 declared Flask routes are included.
- Automated compliance tests cover authentication, role permissions, storage,
  validation, BCE ordering, and removal of production mock fallbacks.

## Repository Structure

```text
index.html                         Project website for GitHub Pages
frontend/
  pages/                           Login and role-based application pages
  css/style.css                    Shared responsive styles
  js/api.js                        API client and response normalization
  js/auth.js                       Session and role-based access control
backend/
  app.py                           Flask API and User Story controls
  server.py                        Strict local production-style startup
  db.py                            PostgreSQL connection helpers
  inference.py                     YOLO26s inference using best.pt
  training.py                      Local Ultralytics training workflow
  models/best.pt                   Team-trained deployable weights
database/
  schema_postgresql.sql            Current PostgreSQL schema
  migrate_user_story_compliance.sql Non-destructive compliance migration
  erd.drawio                       Entity relationship diagram
docs/
  diagrams/                        30 BCE and 30 sequence diagrams
  reports/                         Reports, test plan, and compliance audits
  presentations/                   Presentation material
  other/                           User Stories and implementation guide
tests/test_compliance.py           Automated compliance checks
```

## Run Locally

1. Create the PostgreSQL database and run:

```powershell
psql -U postgres -d maize_detector -f database/schema_postgresql.sql
psql -U postgres -d maize_detector -f database/migrate_user_story_compliance.sql
```

2. Copy `backend/.env.example` to `backend/.env` and configure PostgreSQL,
   `SECRET_KEY`, and `FILE_ENCRYPTION_KEY`.

3. Install dependencies and start the strict server:

```powershell
python -m pip install -r backend/requirements.txt
python backend/server.py
```

4. Serve the repository root and open the prototype:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/frontend/pages/login.html`.

Direct `file://` opening is also allowed for the local demo, but serving the
repository over `http://localhost:8000` is recommended for consistent browser
behaviour.

## Verification

```powershell
python -m unittest discover -s tests -v
```

`backend/server.py` stops immediately if PostgreSQL or `best.pt` is unavailable,
preventing an incomplete demo from appearing successful.

## Main Evidence

- [User Stories](docs/other/FYP-26-S2-7_User_Stories.md)
- [User Story Code Guide](docs/other/FYP-26-S2-7_User_Story_Code_Guide.md)
- [BCE and Sequence Source](docs/other/FYP-26-S2-7_BCE_Sequence_Diagrams.md)
- [BCE Compliance Audit](docs/reports/bce_sequence_compliance_audit.md)
- [Week 11 Compliance Audit](docs/reports/week11_compliance_audit.md)
- [PostgreSQL ERD](database/erd.md)

## Team

| Member | Student ID |
|---|---|
| R Philip Abraham | 8931707 |
| Li Qiankun | 7912936 |
| Zhang Yixin | 9107241 |
| Li Baichuan | 9182111 |
| Zhang Jialu | 9090411 |

Supervisor: **Sionggo Japit**

Assessor: **Tian Sion Hui**
