# FYP-26-S2-7 Week 10 Demo Flow & Backup Plan

## Primary Demo Flow (5 minutes)

| Step | Action | Screen | What to Say |
|------|--------|--------|-------------|
| 1 | Open project website | index.html | "This is our project entry point showing the overview, team, and document links." |
| 2 | Click "Live Prototype" → Login | login.html | "We have 4 demo roles: Farmer, Researcher, Agronomist, Admin. Let me log in as Farmer." |
| 3 | Login as john@farm.com / 123456 | dashboard.html | "The Farmer dashboard shows quick actions and recent results." |
| 4 | Click "Upload Image" → Select JPG | upload.html | "Upload a maize field image — JPG/PNG supported, PDF rejected with error message." |
| 5 | Click "Analyze" | loading → result.html | "The system processes the image. If the AI model is connected, it uses YOLO26s; otherwise mock data runs the same flow." |
| 6 | Show result page | result.html | "Tassel count, confidence score, annotated image with bounding boxes, compare toggle." |
| 7 | Switch to Researcher → History | history.html | "Researcher can view historical detection records with trend analysis." |
| 8 | Show Report tabs | report.html | "Daily, Weekly, Monthly reports with aggregated statistics." |
| 9 | Show Export | export.html | "Select records and download as CSV — real Blob download, not fake." |
| 10 | Show Admin → Users | admin.html | "Admin manages 100 users with CRUD, permissions, datasets, backups, and logs." |

## Key Talking Points for Q&A

- **Real AI**: YOLO26s training notebook with mAP50 = 0.899 on ground data. Model weights being integrated.
- **Database**: PostgreSQL 18, 7 tables, 100 seeded users. Graceful mock fallback when DB unavailable.
- **Mobile**: Responsive at 375px, buttons 47px ≥ 44px WCAG requirement.
- **Testing**: 17/17 prototype tests passed, 30 user story test tables with BCE traceability.
- **Architecture**: Frontend → Flask API → YOLO inference → PostgreSQL. Graceful degradation at every layer.

## Backup Plan (if live demo fails)

### Option A: Screenshots Only
- All 11 page screenshots available in `docs/screenshots/` (or captured from running prototype)
- Click through screenshots in presentation order instead of live browser

### Option B: Recorded Video
- Record a walkthrough using OBS or PowerPoint screen recording:
  1. Open project website → navigate to prototype
  2. Login as each role showing different dashboards
  3. Upload → Analyze → Result workflow
  4. History + Report + Export
  5. Admin user management
- Duration: 3-5 minutes
- Include voiceover explaining each step

### Option C: Offline Localhost
- Run backend: `cd backend && python app.py`
- Open frontend pages via `file://` protocol or simple HTTP server
- Demonstrate full Upload → Predict → Result flow with live API response

## Pre-Demo Checklist

- [ ] Backend Flask server starts without errors (`python app.py`)
- [ ] Frontend pages load from GitHub Pages or locally
- [ ] Demo accounts work (john@farm.com, liwei@research.org, etc.)
- [ ] Upload folder has sample images (`backend/uploads/` or `datasets/`)
- [ ] CORS works (frontend can call backend API)
- [ ] Screenshots backup folder ready
- [ ] Recording software installed and tested (if using video backup)
- [ ] Browser cache cleared (clean demo experience)
- [ ] Internet connection (for GitHub Pages demo) or local fallback ready

## Demo Script (Short Version — 3 minutes)

> "Good morning. Our project is Counting Maize Tassels in the Wild via Deep Neural Network.  
> This is our project website. Clicking into the prototype, you can log in with 4 different roles.  
> As a Farmer, I upload a maize field image and click Analyze. The system returns the tassel count, confidence score, and highlights each detected tassel with bounding boxes.  
> Switching to Researcher, you can browse history records and generate daily, weekly, and monthly reports.  
> The Admin panel manages 100 users, datasets, permissions, and backups.  
> The AI model is YOLO26s trained on 1,161 field images — achieving mAP50 of 0.899.  
> All 17 prototype tests passed, the architecture uses Flask + PostgreSQL with graceful fallback, and we're now integrating the trained model for live inference in Weeks 11-14."
