# Codex Context Pack - FYP-26-S2-7 Week 10

## Project
Project Title: Counting Maize Tassels in the Wild via Deep Neural Network
App Name: Maize Detector App
Week 10 Submission Target: 13 June

## Important Rule for Codex
Before writing code, read the existing repository file tree first. Do not invent missing files. Use the current project structure. When editing a file, return the full updated file content.

## Current Project Website
https://zhabgjialu2003-sudo.github.io/Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/

## Week 10 Goal
The goal is not to finish the final system, but to prove that the project has moved from documentation/design to a working or semi-working prototype.

Week 10 should demonstrate:
1. Updated Project Website
2. Demonstrable Prototype
3. Basic Frontend Pages
4. Backend Mock API or Basic Backend Interfaces
5. Initial AI Model Progress
6. Database Design
7. Progress Report
8. Updated Preliminary Technical Report
9. Week 10 Presentation Slides
10. Demo Flow and Backup Plan

## Technology Stack
Frontend: HTML, CSS, JavaScript
Backend: Python Flask
Database: MySQL
AI Model: PyTorch, YOLO, OpenCV
Version Control: GitHub
Diagram Tool: Draw.io

## Main User Roles
1. Farmer
- Upload maize images
- View tassel count results
- View highlighted tassels on annotated images
- Upload multiple images
- Access system through mobile device

2. Researcher
- Retrieve accurate tassel counting results
- Export data in CSV/JSON format
- Analyze historical data
- Compare model outputs
- Generate visual reports

3. Agronomist
- Evaluate plant health based on tassel count
- Monitor crop growth over time
- Detect abnormal patterns
- View multi-field dashboard
- Generate summarized insights

4. Admin
- Manage user accounts
- Store uploaded images securely
- Monitor system usage
- Manage datasets
- Control user permissions
- Back up system data

5. System
- Preprocess images
- Train deep learning models
- Evaluate model performance
- Deploy trained model as an online service
- Support system updates

## Frontend Pages Required for Week 10

### Task 2: Dashboard Page
Required elements:
- Top navigation bar: Home, Upload, History, Report, Admin
- Welcome message: Welcome to Maize Detector App
- Quick action buttons: Upload Image, View History, Generate Report
- Summary cards: Total Uploaded Images, Total Detected Tassels, Average Tassel Count, Model Status
- Recent detection records: image name, detection count, date

Example data:
- Total Uploaded Images: 128
- Total Detected Tassels: 3482
- Average Tassel Count: 27.2
- Model Status: Active

### Task 3: Upload Image Page
Required elements:
- Page title: Upload Maize Image
- File selection button
- Image preview area
- File information: file name, format, size
- Analyze button
- Error message for invalid file types such as PDF/DOCX
- Loading state: Analyzing...

Expected flow:
1. User opens Upload page
2. User selects JPG/PNG image
3. Image preview is displayed
4. User clicks Analyze
5. Mock detection result is shown

Mock result example:
- Uploaded file: maize_sample_01.jpg
- Status: Upload successful
- Detected Tassels: 37
- Confidence: 89%

### Task 4: Result Page
Required elements:
- Image name
- Original image
- Detected tassel count
- Confidence score
- Processing time
- Annotated image
- Save Result button
- View History button
- Export Result button

Example content:
- Image Name: maize_sample_01.jpg
- Detected Tassels: 37
- Confidence Score: 89%
- Processing Time: 2.4 seconds

If no real AI image is connected, use sample annotated image and state that it is mock data for prototype demonstration.

### Task 5: History Page
Required table columns:
- Image Name
- Date
- Tassel Count
- Confidence
- Action

Example records:
- maize_001.jpg | 2026-06-10 | 37 | 89% | View
- maize_002.jpg | 2026-06-11 | 42 | 91% | View
- maize_003.jpg | 2026-06-12 | 29 | 85% | View

### Task 6: System Report Page
Required tabs/buttons:
- Daily
- Weekly
- Monthly

Daily example:
- Date: 2026-06-13
- Total Uploads: 24
- Successful Detections: 22
- Failed Detections: 2
- Average Tassel Count: 31
- System Status: Normal

Weekly example:
- Week: 2026-06-07 to 2026-06-13
- Total Uploads: 148
- Successful Detections: 139
- Failed Detections: 9
- Most Active Day: Friday
- Average Processing Time: 2.8 seconds

Monthly example:
- Month: June 2026
- Total Uploads: 520
- Successful Detections: 496
- Failed Detections: 24
- Average Tassel Count: 34
- Model Accuracy Estimate: 88%

### Task 7: Admin User Management Page
Required elements:
- User Management title
- Search box
- Add User button
- User list table
- Edit button
- Disable button
- Role display
- Status display

Example users:
- John Farmer | john@test.com | Farmer | Active | Edit / Disable
- Amy Research | amy@test.com | Researcher | Active | Edit / Disable
- Admin User | admin@test.com | Admin | Active | Edit / Disable

### Task 8: Researcher Export Page
Required elements:
- Export Detection Results title
- Date range selection
- Format selection: CSV / JSON
- Number of selected records
- Export Data button
- Success message after clicking export

Example:
- From: 2026-06-01
- To: 2026-06-13
- Format: CSV / JSON
- Selected Records: 24

Better option: use JavaScript to generate a sample CSV download.

### Task 9: Agronomist Dashboard Page
Required elements:
- Multiple field cards
- Healthy / Warning status
- Simple trend chart or trend data

Example:
- Field A: Average Tassel Count 35, Status Healthy
- Field B: Average Tassel Count 18, Status Warning
- Field C: Average Tassel Count 42, Status Healthy

Weekly trend example:
- Mon: 20
- Tue: 23
- Wed: 29
- Thu: 35
- Fri: 37

## Backend Mock API Required for Week 10
Use Flask. Required endpoints:

1. GET /api/health
Returns backend status.

2. POST /api/upload
Receives image upload.

3. POST or GET /api/predict
Returns mock detection result.

Example response:
```json
{
  "image_name": "maize_sample_01.jpg",
  "count": 37,
  "confidence": 0.89,
  "status": "success"
}
```

4. GET /api/history
Returns sample history records.

5. GET /api/report/daily
Returns daily report data.

6. GET /api/report/weekly
Returns weekly report data.

7. GET /api/report/monthly
Returns monthly report data.

## MySQL Database Design Required for Week 10
Database does not need to be fully connected yet, but should include ERD, table descriptions, and SQL schema.

Suggested tables:
1. users
2. roles
3. images
4. detection_results
5. history
6. reports
7. system_logs
8. datasets

Important example fields:

### users
- user_id
- name
- email
- password_hash
- role
- status
- created_at

### images
- image_id
- user_id
- image_name
- image_path
- upload_time
- status

### detection_results
- result_id
- image_id
- tassel_count
- confidence_score
- annotated_image_path
- processing_time
- created_at

## AI Model Progress Required for Week 10
AI team should prepare visible progress materials:
- Dataset source explanation
- Maize image samples
- Annotation method explanation
- Model selection explanation: YOLO / PyTorch / OpenCV
- Training progress
- Initial detection results or mock detection output
- Bounding box example images
- Current issues: limited dataset size, lighting problems, occlusion, blurred images
- Next-step plan

Minimum AI evidence:
- 3 original maize images
- 3 annotated images
- 1 model workflow diagram
- 1 AI progress explanation paragraph

Suggested AI progress paragraph:
At the current Week 10 stage, the AI team has started preparing maize tassel image samples and testing the object detection workflow. The project plans to use a YOLO-based model with PyTorch and OpenCV for maize tassel detection. Sample annotated images are prepared for prototype demonstration, while the final trained model will be integrated with the backend in the next development stage.

## Recommended GitHub Repository Structure
Counting-Maize-Tassels/
frontend/
  index.html
  upload.html
  result.html
  history.html
  report.html
  admin.html
  export.html
  agronomist.html
  css/
    style.css
  js/
    main.js
backend/
  app.py
  requirements.txt
  routes/
ai-model/
  dataset-samples/
  training-notes.md
  sample-results/
database/
  schema.sql
  erd.png
documents/
  progress-report-week10.docx
  technical-report.docx
  presentation-week10.pptx
README.md

## Priority Order If Time Is Limited
1. Prototype Home/Dashboard, Upload, and Result pages
2. Project Website update
3. Progress Report
4. Week 10 PPT
5. Technical Report update
6. History page
7. System Report page
8. Backend Mock API
9. Database Design
10. AI Model Progress
11. Testing Plan
12. Demo backup screenshots or recording

## Member Task Allocation

### Zhang Jialu
- Coordinate Week 10 tasks
- Check Project Website
- Write Progress Report
- Update Technical Report
- Prepare PPT
- Organize final submission package
- Check whether all members submitted materials

### Zhang Yixin
- Dashboard page
- Upload page
- Result page
- History page
- System Report page
- Provide UI screenshots for report and PPT

### Li Baichuan
- Flask backend structure
- /api/health
- /api/predict mock result
- /api/history mock data
- Daily / Weekly / Monthly report mock APIs
- MySQL database design

### Philip
- Organize maize tassel dataset
- Prepare sample maize images
- Prepare sample annotated images
- Write AI model progress
- Explain YOLO / PyTorch / OpenCV plan
- Prepare initial model results or mock detection output

### Li Qiankun
- Assist AI model testing
- Organize YOLO training workflow
- Prepare evaluation metrics
- Prepare model detection screenshots
- Explain future model-backend integration

## Minimum Version for Week 10
At least complete:
1. Project Website can be opened
2. Prototype has Dashboard, Upload, and Result pages
3. Upload page can select and preview image
4. Result page can display mock tassel count
5. Sample annotated image is available
6. Progress Report is completed
7. Week 10 PPT is completed
8. Technical Report is updated
9. GitHub link is available
10. Backup demo screenshots are ready

## Instruction for Coding
When implementing frontend, keep it lightweight and avoid browser lag. Use plain HTML/CSS/JavaScript unless the existing project already uses another framework. Keep UI consistent across pages. Use sample/mock data first. Do not add unnecessary heavy libraries.
