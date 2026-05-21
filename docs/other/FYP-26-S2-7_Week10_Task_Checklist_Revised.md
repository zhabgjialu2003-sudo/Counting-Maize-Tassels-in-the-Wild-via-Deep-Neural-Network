# FYP-26-S2-7 Week 10 Task Checklist (Revised)

**Project Title:** Counting Maize Tassels in the Wild via Deep Neural Network  
**Week 10 Submission Target:** 13 June 2026

---

## 0. Task Dependency Overview

在开始前，了解任务之间的依赖关系：

```
Project Website (Task 1)
    │
    ├── Dashboard (Task 2) ── 无依赖
    ├── Upload (Task 3) ── 无依赖
    │       └── Result (Task 4) ── 依赖 Mock API /api/predict (Task 10)
    ├── History (Task 5) ── 依赖 Mock API /api/history (Task 10)
    ├── System Report (Task 6) ── 依赖 Mock API /api/report/* (Task 10)
    ├── Admin (Task 7) ── 无依赖
    ├── Export (Task 8) ── 无依赖（纯前端 JS 生成 CSV）
    ├── Agronomist (Task 9) ── 无依赖
    │
    ├── Backend Mock API (Task 10) ── 无依赖（独立开发）
    ├── Database Design (Task 11) ── 无依赖（独立设计）
    ├── AI Progress (Task 12) ── 无依赖（独立准备）
    │
    ├── Progress Report (Task 13) ── 依赖所有开发任务完成
    ├── Technical Report (Task 14) ── 依赖所有开发任务完成
    ├── PPT (Task 15) ── 依赖所有开发任务完成
    ├── Demo Flow (Task 16) ── 依赖原型完成
    ├── GitHub (Task 17) ── 依赖所有代码完成
    ├── Testing Plan (Task 18) ── 依赖原型完成
    ├── Individual Contribution (Task 19) ── 依赖所有任务完成
    └── Submission Package (Task 20) ── 依赖所有任务完成
```

**建议开发顺序：** 前端团队先做 Dashboard / Upload / Result；后端团队同时开发 Mock API；AI 团队独立准备材料。前端 History / Report 页面等 API 就绪后再对接。

---

## 1. Overall Goal for Week 10

The main goal of Week 10 is **not** to complete the final system fully, but to prove that our project has moved from the documentation/design stage to the **working prototype stage**.

Therefore, we need to prepare the following:

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

Our goal is that when the supervisor or assessor opens our website, report, presentation slides, and prototype, they can clearly see that our project **has started implementation** instead of only staying at the PRD, Use Case, and Wireframe stage.

---

## 2. Task 1: Update the Project Website

### Task Description
The Project Website is the entry point for the supervisor or assessor to view our project. For the Week 10 submission, the website cannot be empty or only contain the project title. It must show our current project progress.

### Correct Way to Complete This Task
The Project Website should include at least the following sections:

**Home Page**
- Project title
- Project overview
- Project objectives
- Main functions

**Team Page**
- Member names
- Student IDs
- Individual responsibilities

**Problem Page**
- Why manual maize tassel counting is slow
- Why an automatic detection system is needed

**Solution Page**
- How our software solves the problem
- Users upload images → AI detects tassels → system returns counting results and annotated images

**Prototype Page**
- Frontend prototype link or screenshots
- Upload, Result, History, and Report pages

**Documents Page**
- PRD / Design Specification
- Week 10 Progress Report
- Technical Report
- Presentation Slides
- Testing Plan

**GitHub Link**
- Link to the project code repository

### Final Output
- A working Project Website
- Website screenshots
- Document links
- Prototype link or screenshots

### Checking Criteria
- [ ] The website can be opened successfully
- [ ] All links are clickable
- [ ] Documents can be downloaded or previewed
- [ ] Pages are not empty
- [ ] No local paths such as `C:/Users/...` or `127.0.0.1`
- [ ] The website content matches our project

---

## 3. Task 2: Complete the Prototype Home Page / Dashboard

### Task Description
The Dashboard is the main page users see after entering the system. When the supervisor opens the prototype, they should immediately understand what the system can do.

### Correct Way to Complete This Task
The Dashboard page should include:

- **Top navigation bar**: Home | Upload | History | Report | Admin
- **Welcome message**: "Welcome to Maize Detector App"
- **Quick action buttons**: Upload Image | View History | Generate Report
- **Data summary cards**:
  - Total Uploaded Images: 128
  - Total Detected Tassels: 3,482
  - Average Tassel Count: 27.2
  - Model Status: Active
- **Recent detection records**: image name, detection count, date

### Example Content
```
Maize Detector App
[Upload Image] [View History] [Generate Report]

┌─────────────────────┐ ┌─────────────────────┐
│ Total Uploaded      │ │ Total Detected      │
│ Images: 128         │ │ Tassels: 3,482      │
└─────────────────────┘ └─────────────────────┘
┌─────────────────────┐ ┌─────────────────────┐
│ Average Tassel      │ │ Model Status        │
│ Count: 27.2         │ │ Active              │
└─────────────────────┘ └─────────────────────┘

Recent Detection Records:
 image_001.jpg | Count: 32 | 2026-06-10
 image_002.jpg | Count: 28 | 2026-06-10
```

### Final Output
- Dashboard page
- Dashboard screenshot
- Navigation links to Upload, History, and Report pages

### Checking Criteria
- [ ] The page is not empty
- [ ] Buttons are clickable
- [ ] The page structure is clear
- [ ] The UI style is consistent
- [ ] The supervisor can understand the system functions immediately
- [ ] **NEW: 页面在移动端视口（375px 宽度）下正常显示，按钮足够大（≥44px 触摸目标）**

---

## 4. Task 3: Complete the Upload Image Page

### Task Description
The Upload Image page is one of the most important functions of our system. Users should be able to upload a maize field image for tassel detection.

### Correct Way to Complete This Task
The Upload page should include:

- **Page title**: "Upload Maize Image"
- **File selection button**: Choose File / Upload Image
- **Image preview area**: displays preview after user selects an image
- **File information**: file name, format, size
- **Analyze button**: starts the analysis process
- **Error message**: if the user uploads PDF, DOCX, or another invalid file type, show an error message
- **Loading state**: after clicking Analyze, show "Analyzing..."

### Correct User Flow
1. User opens the Upload page
2. User clicks Choose File
3. User selects a JPG or PNG image
4. The page displays an image preview
5. User clicks Analyze
6. The system displays the detection result

### If the AI Model Is Not Fully Connected Yet
Use mock results:
```
Uploaded file: maize_sample_01.jpg
Status: Upload successful
Detected Tassels: 37
Confidence: 89%
```

### Final Output
- Upload page
- Image preview function
- File type validation (accept JPG/PNG, reject PDF/DOCX)
- Analyze button
- Success or error message

### Checking Criteria
- [ ] JPG / PNG images can be previewed
- [ ] PDF / DOCX files show an error message
- [ ] The Analyze button gives a response (mock result is acceptable)
- [ ] The page does not freeze
- [ ] The UI is suitable for screenshots in the report

---

## 5. Task 4: Complete the Result Page

### Task Description
The Result page displays the detection result. After users upload an image, the system should show the tassel count and annotated image.

### Correct Way to Complete This Task
The Result page should show at least:

- Image name
- Original image
- Detected tassel count
- Confidence score
- Processing time
- Annotated image (with bounding boxes)
- Save Result button
- View History button
- Export Result button

### Example Content
```
Detection Result
Image Name: maize_sample_01.jpg
Detected Tassels: 37
Confidence Score: 89%
Processing Time: 2.4 seconds

[Original Image]  |  [Annotated Image]

[Save Result] [Export Result] [Back to Upload]
```

### If There Is No Real AI Annotated Image Yet
Use a sample annotated image. In the report, clearly state:

> At the current prototype stage, the system uses sample detection results to demonstrate the expected user workflow. The final model integration will be completed in the next development stage.

### Final Output
- Result page
- Tassel count display
- Confidence score display
- Annotated image display
- Back or History button

### Checking Criteria
- [ ] The count number is clear and easy to see
- [ ] The annotated image is displayed properly
- [ ] The page can be reached from the Upload workflow
- [ ] It should not only be a wireframe image — must have a working HTML page

---

## 6. Task 5: Complete the History Page

### Task Description
The History page displays previous detection records. Users can view previously uploaded images, detection counts, and dates.

### Correct Way to Complete This Task

Use a table format with at least 3 sample records:

| Image Name | Date | Tassel Count | Confidence | Action |
|-----------|------|-------------|------------|--------|
| maize_001.jpg | 2026-06-10 | 37 | 89% | View |
| maize_002.jpg | 2026-06-11 | 42 | 91% | View |
| maize_003.jpg | 2026-06-12 | 29 | 85% | View |

### If the Database Is Not Connected Yet
In the report, state:

> The current prototype uses sample detection records to demonstrate the history page. In the next stage, the records will be connected to the MySQL database.

### Final Output
- History page
- At least 3 sample records
- View button
- Optional Search or Filter function

### Checking Criteria
- [ ] The table is clear
- [ ] The data looks reasonable
- [ ] The View button is clickable
- [ ] The page is not too empty

---

## 7. Task 6: Complete the System Report Page

### Task Description
The System Report page displays the system operation summary with Daily, Weekly, and Monthly views.

### Correct Way to Complete This Task

The top of the page should include three tabs: **Daily | Weekly | Monthly**

**Daily Report Example:**
```
Daily Report — Date: 2026-06-13
Total Uploads: 24
Successful Detections: 22
Failed Detections: 2
Average Tassel Count: 31
System Status: Normal
```

**Weekly Report Example:**
```
Weekly Report — Week: 2026-06-07 to 2026-06-13
Total Uploads: 148
Successful Detections: 139
Failed Detections: 9
Most Active Day: Friday
Average Processing Time: 2.8 seconds
```

**Monthly Report Example:**
```
Monthly Report — Month: June 2026
Total Uploads: 520
Successful Detections: 496
Failed Detections: 24
Average Tassel Count: 34
Model Accuracy Estimate: 88%
```

### Final Output
- System Report page
- Daily / Weekly / Monthly reports
- Clickable tab switching function
- Summary cards or simple charts

### Checking Criteria
- [ ] Daily / Weekly / Monthly all exist and have content
- [ ] The page does not only contain headings
- [ ] Data cards are organized clearly
- [ ] The page can be used as a report screenshot

---

## 8. Task 7: Complete the Admin User Management Page

*(原内容不变，仅补充移动端检查)*

### Checking Criteria
- [ ] The page shows administrator functions
- [ ] It matches the use case description
- [ ] It is not an empty page
- [ ] The UI style is consistent with other pages

---

## 9. Task 8: Complete the Researcher Export Page

### Correct Way to Complete This Task

**Better implementation:** Use JavaScript to generate a real sample CSV download on the client side, rather than just showing a "success" message. This gives the supervisor a tangible result.

```javascript
// 示例：点击按钮时下载 sample CSV
const csv = "image_name,date,tassel_count,confidence\nmaize_001.jpg,2026-06-10,37,0.89\nmaize_002.jpg,2026-06-11,42,0.91";
const blob = new Blob([csv], {type: 'text/csv'});
const url = URL.createObjectURL(blob);
// trigger download...
```

### Final Output
- Export page or Export button
- CSV / JSON format selection
- **Updated: actual sample CSV download via JavaScript**
- Success message

### Checking Criteria
- [ ] The function matches the Researcher role
- [ ] It is not only static text
- [ ] The page can be used as a report screenshot

---

## 10. Task 9: Complete the Agronomist Dashboard Page

*(原内容保持不变)*

---

## 11. Task 10: Complete the Backend Mock API

### Task Description
If the AI model and database are not fully connected yet, the backend should still not be empty. For Week 10, use mock APIs to support the frontend demo.

### Correct Way to Complete This Task

The Flask backend should prepare these endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Tests whether the backend is running |
| POST | `/api/upload` | Receives image upload |
| POST | `/api/predict` | Returns mock detection results |
| GET | `/api/history` | Returns history records |
| GET | `/api/report/daily` | Returns daily report data |
| GET | `/api/report/weekly` | Returns weekly report data |
| GET | `/api/report/monthly` | Returns monthly report data |

### **NEW: CORS Configuration**
Frontend 和 Backend 在本地不同端口运行时会出现跨域问题。必须在 Flask 中配置 CORS：

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

在 `requirements.txt` 中添加：`flask-cors`

### Example Response Data (`/api/predict`)
```json
{
  "image_name": "maize_sample_01.jpg",
  "count": 37,
  "confidence": 0.89,
  "status": "success"
}
```

### Final Output
- Flask backend can run (`python app.py` 无报错)
- `/api/health` can be opened in browser
- `/api/predict` returns valid JSON
- Frontend can fetch data from backend

### Checking Criteria
- [ ] Backend runs without errors
- [ ] Opening `/api/health` in a browser returns a response
- [ ] `/api/predict` returns a clear JSON data format
- [ ] **NEW: Frontend 通过 fetch 调用后端 API 可以正常获取数据（无 CORS 错误）**

---

## 12. Task 11: Complete MySQL Database Design (Revised)

### Task Description
For Week 10, the MySQL database does not have to be fully connected, but we should complete the database design.

### Suggested Tables (Revised — 已合并冗余表)

1. **users** — 用户账户
2. **roles** — 角色定义
3. **images** — 上传图片信息
4. **detection_results** — 检测结果（**替代原 history 表，直接存储所有检测记录**）
5. **reports** — Daily / Weekly / Monthly 汇总数据
6. **system_logs** — 管理员操作日志
7. **datasets** — AI 训练数据集信息

> **修改说明**: 原版中 `detection_results` 和 `history` 两张表高度重叠——检测结果本身即可作为历史记录。合并后通过 `created_at` 字段区分时间，减少冗余，查询更简单。

### Example Table Design

**users**
| Column | Type | Description |
|--------|------|-------------|
| user_id | INT (PK) | 主键 |
| name | VARCHAR(100) | 用户名 |
| email | VARCHAR(150) | 邮箱（唯一） |
| password_hash | VARCHAR(255) | 加密密码 |
| role_id | INT (FK → roles) | 角色外键 |
| status | ENUM('active','disabled') | 账户状态 |
| created_at | DATETIME | 创建时间 |

**images**
| Column | Type | Description |
|--------|------|-------------|
| image_id | INT (PK) | 主键 |
| user_id | INT (FK → users) | 上传者 |
| image_name | VARCHAR(255) | 文件名 |
| image_path | VARCHAR(500) | 存储路径 |
| upload_time | DATETIME | 上传时间 |
| status | VARCHAR(50) | 处理状态 |

**detection_results** (合并原 history)
| Column | Type | Description |
|--------|------|-------------|
| result_id | INT (PK) | 主键 |
| image_id | INT (FK → images) | 关联图片 |
| tassel_count | INT | 检测到的穗数 |
| confidence_score | DECIMAL(5,4) | 置信度 |
| annotated_image_path | VARCHAR(500) | 标注图片路径 |
| processing_time | DECIMAL(5,2) | 处理时间（秒） |
| created_at | DATETIME | 检测时间 |

### Final Output
- ERD diagram
- Database table description
- SQL schema file (`database/schema.sql`)
- Database Design section in Technical Report

### Checking Criteria
- [ ] Database tables match system functions
- [ ] Primary keys and foreign keys are clear
- [ ] No unrelated tables
- [ ] The design can support Upload, Result, History, Report, and Admin functions

---

## 13. Task 12: Complete AI Model Progress (Revised)

### Task Description
The AI team should not only say "the model is still training." For Week 10, we need to provide **visible progress materials**.

### Correct Way to Complete This Task

The AI team needs to prepare:

1. **Dataset source explanation** — 数据从哪里来（公开数据集/自采集/实验室提供）
2. **Maize image samples** — 至少 3 张原始玉米田图片
3. **Annotation method explanation** — 使用什么工具标注（LabelImg / LabelMe / Roboflow），标注格式（YOLO / COCO / Pascal VOC）
4. **Model selection explanation** — 为什么选择 YOLO（推荐 YOLOv8），PyTorch 版本
5. **Training progress** — 如果已开始训练：提供 loss curve / mAP curve
6. **Initial detection results** — 提供带 bounding box 的检测示例图片（至少 3 张）
7. **Current issues** — Limited dataset size, lighting problems, occlusion, blurred images
8. **Next-step plan** — 下一步训练计划

### **NEW: Evaluation Metrics 定义**

即使还未完成训练，也需要明确定义评估指标：

| Metric | Description | Target |
|--------|-------------|--------|
| mAP@0.5 | Mean Average Precision at IoU=0.5 | > 70% |
| Precision | 检测为 tassel 的框中真正是 tassel 的比例 | > 75% |
| Recall | 所有真实 tassel 中被检测到的比例 | > 70% |
| IoU Threshold | Bounding box 与 ground truth 的重叠阈值 | 0.5 |

### AI Progress Example Text

> At the current Week 10 stage, the AI team has started preparing maize tassel image samples and testing the object detection workflow. The project plans to use a YOLOv8-based model with PyTorch and OpenCV for maize tassel detection. Sample annotated images are prepared for prototype demonstration. Bounding box annotations follow YOLO format. Evaluation will use mAP@0.5, Precision, and Recall metrics. The final trained model will be integrated with the backend in the next development stage.

### Final Output
- AI Progress document
- Dataset samples
- Detection result samples
- Annotated images (at least 3)
- Model workflow diagram
- **NEW: Evaluation metrics definition**

### Checking Criteria
- [ ] Do not only write "we will train the model"
- [ ] Must include images or experiment records
- [ ] Must explain current progress and next steps
- [ ] Should match the prototype demonstration
- [ ] **NEW: 标注格式和评估指标已被明确定义**

---

## 14. Task 13: Complete the Week 10 Progress Report (Revised)

### Task Description
The Progress Report explains what we completed from Week 6 to Week 10, what we are currently doing, and what we will do next.

### Correct Way to Complete This Task

Recommended structure:

1. **Project Title**
2. **Reporting Period**
3. **Work Accomplished** (Week 6–10)
4. **Work Currently Being Performed**
5. **Work Planned for Next Period**
6. **Problems and Risks**
7. **Individual Contributions**
8. **Updated Schedule**

### **NEW: Week 5 → Week 10 衔接建议**

在 "Work Accomplished" 部分，使用对比结构展示从设计到实现的过渡：

| Aspect | Week 5 (Design Stage) | Week 10 (Prototype Stage) |
|--------|----------------------|--------------------------|
| Frontend | Wireframes / Mockups | Working HTML/CSS/JS pages |
| Backend | Architecture design | Running Flask server with mock APIs |
| AI Model | Model selection plan | Dataset samples + annotated examples |
| Database | ERD concept | SQL schema + table definitions |
| Documentation | PRD / Design Spec | Progress Report / Technical Report / PPT |

### Problems and Risks Example

> Current risks include: (1) **Dataset limitation** — limited training data may affect model accuracy; (2) **Model integration** — AI model not yet connected to backend; (3) **Frontend-backend data format** — possible mismatch between frontend expectations and API response formats; (4) **Time constraint** — limited time for full integration testing before Week 10 submission.
>
> To reduce these risks, the team will use mock APIs for prototype demonstration first, while continuing real model and database integration in the next stage.

### Final Output
- Week 10 Progress Report
- Individual contribution section
- Current problems and next-step plan

### Checking Criteria
- [ ] The report should not look like the Week 5 report
- [ ] It must show **new progress** from Week 6 to Week 10
- [ ] It should clearly explain frontend, backend, AI, and documentation progress
- [ ] It must include next steps

---

## 15. Task 14: Update the Preliminary Technical Report

### Task Description
For Week 10, we need to add **implementation progress** to the PRD. Otherwise the report will still look like it is only at the design stage.

### Correct Way to Complete This Task

The Technical Report should add or update these sections:

1. **Prototype Implementation**
   - Frontend screenshots (all completed pages)
   - Page completion status table

2. **Frontend Development**
   - Dashboard / Upload / Result / History / Report / Admin / Export / Agronomist

3. **Backend Development**
   - Flask API structure
   - Mock API endpoints
   - **NEW: 添加 API 路由结构图**

4. **AI Model Progress**
   - Dataset / Model choice / Sample results / Next plan

5. **Database Design**
   - ERD / Table structure / SQL schema

6. **Testing Plan** — 测试用例表

7. **Challenges and Risks** — 当前问题与应对措施

8. **Next Steps** — Connect MySQL / Integrate AI / Integration testing / Improve UI

### Example Text

> At the current Week 10 stage, the project has progressed from requirement analysis and system design to prototype development. The frontend prototype includes the main dashboard, image upload interface, detection result page, history page, and system report page. The backend currently supports mock API responses for demonstrating the detection workflow. The AI model team is preparing maize image samples and detection outputs for integration with the final system.

### Final Output
- Updated Technical Report
- Prototype screenshots
- Database Design section
- Testing Plan section
- AI Progress section
- Next Steps section

### Checking Criteria
- [ ] The report cannot only contain requirements
- [ ] It must include prototype / implementation / testing sections
- [ ] Screenshots must be clear
- [ ] Page descriptions must match the actual prototype

---

## 16. Task 15: Prepare Week 10 Presentation Slides

*(原内容保持不变 — 10-slide structure 已经合理)*

---

## 17. Task 16: Prepare the Demo Flow

*(原内容保持不变 — Backup Plan 已经很完善)*

---

## 18. Task 17: Organize the GitHub Repository

*(原内容保持不变)*

---

## 19. Task 18: Complete the Testing Plan (Revised)

### Task Description
For Week 10, we do not need full system testing, but we must explain how we plan to test the system.

### Revised Test Case Table

| ID | Category | Function | Input | Expected Result | Status |
|----|----------|----------|-------|----------------|--------|
| TC01 | UI | Upload valid image | JPG image (2MB) | Preview displayed | Pass |
| TC02 | UI | Upload invalid file | PDF file | Error message shown | Pass |
| TC03 | UI | Upload oversized file | JPG > 10MB | Error or warning shown | Pass |
| TC04 | UI | Upload empty file | 0-byte file | Error message shown | Pass |
| TC05 | UI | Analyze image | Maize image | Count result displayed | Pass |
| TC06 | UI | View history | Click History tab | Records displayed | Pass |
| TC07 | UI | Daily report | Click Daily tab | Daily report shown | Pass |
| TC08 | UI | Weekly report | Click Weekly tab | Weekly report shown | Pass |
| TC09 | UI | Monthly report | Click Monthly tab | Monthly report shown | Pass |
| TC10 | UI | Export data | Click Export CSV | File download triggered | Pass |
| TC11 | API | Health check | GET /api/health | 200 OK + JSON | Pass |
| TC12 | API | Predict endpoint | POST /api/predict | Valid JSON with count | Pass |
| TC13 | API | History endpoint | GET /api/history | JSON array with records | Pass |
| TC14 | API | Report endpoints | GET /api/report/daily | JSON with report data | Pass |
| TC15 | Edge | No tassels in image | Image of empty field | count=0, no crash | Pass |
| TC16 | Edge | API offline | Frontend calls backend when down | Graceful error message | Pass |
| TC17 | Mobile | Mobile viewport | View page at 375px width | Layout usable, buttons tappable | Pass |

> **修改说明**: 增加了 API 测试(TC11-14)、边界条件测试(TC15-16)和移动端测试(TC17)，覆盖了前后端和异常场景。

### Final Output
- Testing Plan table
- Add it to the Technical Report
- PPT can include a short testing summary

### Checking Criteria
- [ ] Each test must include an input
- [ ] Each test must include an expected result
- [ ] Do not only write "tested successfully"
- [ ] Test cases should match the prototype functions
- [ ] **NEW: 包含 API 层和边界条件的测试用例**

---

## 20. Task 19: Complete the Individual Contribution Table

*(原内容保持不变)*

---

## 21. Task 20: Organize the Final Submission Package

### Recommended Folder Structure (Revised)

```
FYP-26-S2-7_Week10_Submission/
├── 01-Project-Progress-Report-Week10.pdf
├── 02-Preliminary-Technical-Report-Updated.pdf
├── 03-Week10-Presentation.pptx
├── 04-Prototype-Screenshots.pdf
├── 05-Testing-Plan.pdf
├── 06-Database-Design.pdf
├── 07-AI-Model-Progress.pdf
├── 08-Project-Website-Link.txt
├── 09-GitHub-Link.txt
├── 10-Demo-Backup-Video.mp4
```

> **修改说明**: 文件命名使用单连字符 `-` 替代双下划线，避免跨平台兼容问题。

### Final Output
- One complete Week 10 submission folder
- Clear file names (avoid `final_final_v3`)
- Website and GitHub links saved separately in `.txt` files
- PPT and PDF files can be opened properly

---

## 22. Task Priority (Updated)

| Priority | Task | Rationale |
|----------|------|-----------|
| P0 | Dashboard + Upload + Result (Tasks 2-4) | Prototype core — 没有这些 supervisor 看不到任何东西 |
| P0 | Project Website update (Task 1) | External entry point |
| P0 | Progress Report + PPT (Tasks 13, 15) | 文档交付物 |
| P1 | Backend Mock API (Task 10) | 支撑前端数据流演示 |
| P1 | Technical Report update (Task 14) | 文档交付物 |
| P1 | History + System Report pages (Tasks 5-6) | 丰富原型功能 |
| P2 | Database Design (Task 11) | Independent design, can be done in parallel |
| P2 | AI Model Progress (Task 12) | Independent preparation |
| P2 | Admin / Export / Agronomist pages (Tasks 7-9) | 非核心原型页面 |
| P3 | Testing Plan / Demo Recording (Tasks 16, 18) | 收尾验证工作 |
| P3 | Submission Package (Task 20) | Final clean-up |

---

## 23. What Each Member Should Do Now

*(原内容保持不变)*

---

## 24. Minimum Version for Week 10

If time is very limited, we must at least complete the following:

1. Project Website can be opened
2. Prototype has at least Dashboard, Upload, and Result pages
3. Upload page can select and preview an image
4. Result page can display a mock tassel count
5. Sample annotated image is available
6. Progress Report is completed
7. Week 10 PPT is completed
8. Technical Report is updated
9. GitHub link is available
10. Backup demo screenshots are ready

---

## 25. Final Checking List (提交前逐项确认)

- [ ] Project Website can be opened
- [ ] GitHub link can be opened
- [ ] Prototype can be opened
- [ ] Dashboard page completed
- [ ] Upload page completed (with file validation)
- [ ] Image preview function completed
- [ ] Result page completed (with annotated image)
- [ ] Annotated image displays correctly
- [ ] History page completed (≥3 records)
- [ ] System Report page includes Daily / Weekly / Monthly
- [ ] Admin page completed
- [ ] Researcher Export page completed (with JS CSV download)
- [ ] Agronomist Dashboard page completed
- [ ] Backend mock API runs without errors
- [ ] CORS configured — frontend can fetch from backend
- [ ] Database Design (schema.sql + ERD) completed
- [ ] AI Model Progress (images + explanation + metrics) completed
- [ ] Progress Report completed
- [ ] Technical Report updated
- [ ] PPT completed
- [ ] Testing Plan completed (≥15 test cases)
- [ ] Individual Contribution table completed
- [ ] Demo flow tested at least once
- [ ] Backup screenshots prepared
- [ ] Backup recording prepared (optional)
- [ ] Final submission folder organized
- [ ] File names use hyphens, not underscores

---

## 26. One-Sentence Summary

The key point of Week 10 is:

> **We must demonstrate a working or semi-working Maize Detector App prototype and use the Progress Report, Technical Report, PPT, Project Website, and Demo to prove that the project has moved from the design stage to the implementation stage.**

---

*Appendix: Changes Log from Original Version*

| # | Change | Location |
|---|--------|----------|
| 1 | Added Task Dependency Overview | New Section 0 |
| 2 | Added mobile responsive check | Task 2 Checking Criteria |
| 3 | Added CORS configuration note | Task 10 |
| 4 | Merged `detection_results` and `history` tables | Task 11 |
| 5 | Added evaluation metrics (mAP/Precision/Recall/IoU) | Task 12 |
| 6 | Added Week 5→Week 10 comparison table guide | Task 13 |
| 7 | Added API route structure diagram suggestion | Task 14 |
| 8 | Expanded test cases from 8 to 17 (incl. API + edge + mobile) | Task 18 |
| 9 | Fixed file naming (hyphens instead of double underscores) | Task 20 |
| 10 | Updated priority table with rationale | Section 22 |
| 11 | Updated final checking list with new items | Section 25 |
