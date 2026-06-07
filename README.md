# Counting Maize Tassels in the Wild via Deep Neural Network

**FYP-26-S2-7** | Week 10 Prototype Stage

## Project Overview

An AI-powered web application that automatically detects and counts maize tassels from field images using YOLO deep learning, replacing slow manual counting with fast automated inference.

**Live Website:** [Project Page](https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/)  
**Live Prototype:** [Login](https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/frontend/pages/login.html)

## Repository Structure

```
├── index.html                  # Project Website (GitHub Pages)
├── frontend/
│   ├── pages/                  # 11 HTML pages (Login, Dashboard, Upload, Result, etc.)
│   ├── css/style.css           # Shared stylesheet (responsive, 375px touch targets)
│   ├── js/                     # JavaScript modules (api.js, auth.js, upload.js, etc.)
│   └── assets/images/          # Static images and annotated samples
├── backend/
│   ├── app.py                  # Flask API server (17 endpoints + mock fallback)
│   ├── db.py                   # PostgreSQL connection helper (psycopg)
│   ├── requirements.txt        # Python dependencies (Flask, flask-cors, psycopg)
│   ├── .env.example            # Environment variable template
│   ├── scripts/
│   │   └── import_mtdc_demo.py # MTDC-UAV dataset importer
│   └── uploads/                # Uploaded image storage
├── database/
│   ├── schema_postgresql.sql   # PostgreSQL schema (7 tables, indexes, sample data)
│   ├── erd.drawio              # ERD diagram (draw.io)
│   └── seed_demo_users.sql     # Demo account seed script
├── datasets/
│   └── README.md               # Dataset sources (Dryad / OPIA)
├── docs/
│   ├── diagrams/               # 30 BCE + 30 Sequence Diagrams
│   ├── reports/                # Progress Report, Technical Report, Testing Plan
│   ├── presentations/          # PPT slides
│   └── other/                  # Checklist, user stories, diagram source
├── maize_yolo26_final (4).ipynb # YOLO26 training notebook (Colab)
└── .gitignore
```

## Quick Start

### Backend API

```powershell
cd backend
pip install -r requirements.txt
python app.py
# API runs at http://localhost:5000
```

### Database (PostgreSQL 18)

```powershell
# 1. Create database in pgAdmin4: maize_detector
# 2. Run schema in Query Tool:
#    database/schema_postgresql.sql
# 3. Configure backend/.env with your PostgreSQL credentials
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Upload image (JPG/PNG) |
| POST | `/api/predict` | Get detection result |
| GET | `/api/history` | Get history records |
| GET | `/api/report/daily` | Daily report |
| GET | `/api/report/weekly` | Weekly report |
| GET | `/api/report/monthly` | Monthly report |
| GET | `/api/users` | List users |
| POST | `/api/users` | Create user |
| PUT | `/api/users/<id>` | Update user |
| DELETE | `/api/users/<id>` | Disable user |
| GET | `/api/datasets` | List datasets |
| POST | `/api/backup` | Create backup |

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Farmer | john@farm.com | 123456 |
| Researcher | liwei@research.org | 123456 |
| Agronomist | maria@agro.com | 123456 |
| Admin | admin@system.com | 123456 |

## Team

| Member | ID | Role |
|--------|----|------|
| Philip | S8931707 | Team Leader, AI & Backend |
| Li Qiankun | 7912936 | AI Code & Model Training |
| Zhang Yixin | 9107241 | Frontend & Backend Integration |
| Li Baichuan | 9182111 | Frontend UI & Backend Services |
| Zhang Jialu | 9090411 | Frontend UI & Backend Services |

## Documents

- [Week 10 Task Checklist](docs/other/FYP-26-S2-7_Week10_Task_Checklist_Revised.md)
- [User Stories (30)](docs/other/FYP-26-S2-7_User_Stories.md)
- [Testing Plan](docs/reports/testing_plan.docx)
- [Database Schema](database/schema_postgresql.sql)
- [ERD Diagram](database/erd.drawio)
