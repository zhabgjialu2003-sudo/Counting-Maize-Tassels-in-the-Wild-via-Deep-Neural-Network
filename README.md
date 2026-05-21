# Counting Maize Tassels in the Wild via Deep Neural Network

**FYP-26-S2-7** | Week 10 Prototype Stage

## Project Overview

An AI-powered web/mobile application that automatically detects and counts maize tassels from field images, replacing slow manual counting with fast deep learning inference.

## Repository Structure

```
├── index.html              # Project Website (GitHub Pages)
├── frontend/
│   ├── pages/              # HTML pages (Dashboard, Upload, Result, History, etc.)
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript modules
│   └── assets/images/      # Static images
├── backend/
│   ├── app.py              # Flask mock API server
│   └── requirements.txt    # Python dependencies
├── database/
│   └── schema.sql          # MySQL schema (7 tables)
├── docs/
│   ├── diagrams/
│   │   ├── bce/            # 30 BCE Class Diagrams
│   │   └── sequence/       # 30 Sequence Diagrams
│   ├── reports/            # Progress Report, Technical Report
│   ├── presentations/      # PPT slides
│   └── other/              # User stories, checklist, diagram source
├── ai/
│   ├── samples/            # Dataset sample images
│   └── results/            # Detection result examples
└── .gitignore
```

## Quick Start

### Backend API

```bash
cd backend
pip install -r requirements.txt
python app.py
# API runs at http://localhost:5000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Upload image |
| POST | `/api/predict` | Get detection result |
| GET | `/api/history` | Get history records |
| GET | `/api/report/daily` | Daily report |
| GET | `/api/report/weekly` | Weekly report |
| GET | `/api/report/monthly` | Monthly report |

### Database

```bash
mysql -u root -p < database/schema.sql
```

## Team

See [Project Website](https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/) for team details.

## Documents

- [User Stories & Diagrams](docs/other/FYP-26-S2-7_Complete_Document.md)
- [Week 10 Task Checklist](docs/other/FYP-26-S2-7_Week10_Task_Checklist_Revised.md)
- [BCE & Sequence Diagram Source](docs/other/FYP-26-S2-7_BCE_Sequence_Diagrams.md)
