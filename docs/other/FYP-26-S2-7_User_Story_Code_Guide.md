# FYP-26-S2-7 User Story Code Guide

This guide reorganizes the frontend, backend, database, and AI implementation
by User Story. It follows the BCE order:

`Actor -> Boundary (frontend) -> Control (backend API) -> Entity (database/model)`

The source files are not physically duplicated or moved. The paths and line
numbers below point to the canonical implementation so that future fixes remain
in one place.

## Shared Code

These modules are reused by several User Stories:

| Layer | Code |
|---|---|
| Frontend API client | `frontend/js/api.js:95-265` |
| Frontend authentication and RBAC | `frontend/js/auth.js:14-183` |
| Backend authentication and RBAC | `backend/app.py:270-327` |
| Secure image storage | `backend/app.py:328-375` |
| Database connection helpers | `backend/db.py:18-48` |
| PostgreSQL schema | `database/schema_postgresql.sql` |
| Non-destructive migration | `database/migrate_user_story_compliance.sql` |
| Active trained weights | `backend/models/best.pt` |

# Farmer User Stories

## User Story A.1 - Upload Maize Images

**Boundary - frontend**

- File selection, preview, validation and submission:
  `frontend/pages/upload.html:64-201`
- Shared multipart upload client: `frontend/js/api.js:121-137`

```javascript
const uploadResult = await apiUpload(file);
const prediction = await apiPost('/api/predict', {
  image_id: uploadResult.image_id,
  mode: 'fast'
});
```

**Control - backend**

- Route: `POST /api/upload`
- Code: `backend/app.py:1039-1108`
- Supporting validation: `backend/app.py:482-505`

```python
@app.route("/api/upload", methods=["POST"])
@require_roles("Farmer", "Researcher", "Admin")
def upload():
    # Validate the image and bind it to the authenticated user.
    ...
```

**Entity**

- `images`: `database/schema_postgresql.sql:65-80`
- `image_files`: `database/schema_postgresql.sql:129-145`

## User Story A.2 - Automatically Count Tassels

**Boundary - frontend**

- Analyse action and progress: `frontend/pages/upload.html:124-201`

```javascript
const result = await apiPost('/api/predict', {
  image_id: imageId,
  mode: 'fast'
});
```

**Control - backend**

- Route: `POST /api/predict`
- Code: `backend/app.py:1109-1204`
- YOLO inference: `backend/inference.py:88-219`

```python
predictor = get_predictor()
prediction = predictor.detect(image_path, mode=mode)
```

**Entity**

- `detection_results`: `database/schema_postgresql.sql:82-99`
- Trained model: `backend/models/best.pt`

## User Story A.3 - View Clear Counting Results

**Boundary - frontend**

- Result loading and summary cards: `frontend/pages/result.html:75-159`

```javascript
const data = await apiGet(`/api/results/${resultId}`);
displayResult(data);
```

**Control - backend**

- Route: `GET /api/results/<result_id>`
- Code: `backend/app.py:1269-1289`

```python
@app.route("/api/results/<int:result_id>", methods=["GET"])
def result_detail(result_id):
    ...
```

**Entity**

- Count, confidence and processing time come from `detection_results`.

## User Story A.4 - See Highlighted Tassels

**Boundary - frontend**

- SVG bounding-box overlay: `frontend/pages/result.html:161-193`
- Original/annotated comparison: `frontend/pages/result.html:194-199`

```javascript
boxes.forEach(box => {
  // Convert model coordinates and render an SVG rectangle.
});
```

**Control - backend**

- Result bbox response: `backend/app.py:1269-1289`
- Protected image route: `backend/app.py:2543-2599`

**Entity**

- Bounding boxes are stored in `detection_results.bbox_data`.
- Original and processed files are represented by `image_files`.

## User Story A.5 - Upload Multiple Images

**Boundary - frontend**

- Batch-mode toggle and file queue: `frontend/pages/upload.html:64-109`
- Sequential upload and progress totals: `frontend/pages/upload.html:142-201`

```javascript
for (const file of selectedFiles) {
  await uploadAndPredict(file);
}
```

**Control - backend**

- Every file passes through `POST /api/upload` and `POST /api/predict`.
- The backend validates each item independently.

**Entity**

- Each file creates one `images` record and one corresponding detection result.

## User Story A.6 - Receive Quick Results

**Boundary - frontend**

- Processing state, estimated time and final timing:
  `frontend/pages/upload.html:142-201`

**Control / AI**

- Fast inference mode: `backend/inference.py:120-139`
- SHA-256 result cache: `backend/inference.py:126-132`

```python
cache_key = hashlib.sha256(image_path.read_bytes()).hexdigest() + f":{mode}"
if cache_key in self._cache:
    return cached_result
```

**Entity**

- Actual runtime is stored in `detection_results.processing_time`.

## User Story A.7 - Use Mobile Devices

**Boundary - frontend**

- Responsive upload layout: `frontend/pages/upload.html`
- Mobile camera input uses `accept="image/*"` and `capture="environment"`.
- Shared responsive styles: `frontend/css/style.css`

**Control - backend**

- Mobile and desktop clients use the same authenticated upload/predict APIs.

**Entity**

- No separate mobile entity is required; results are stored normally.

## User Story A.8 - Use an Intuitive Interface

**Boundary - frontend**

- Quick actions and summary cards: `frontend/pages/dashboard.html:17-64`
- Dashboard data loading: `frontend/pages/dashboard.html:65-92`
- Navigation and role handling: `frontend/js/auth.js:68-140`

**Control - backend**

- Session validation route: `GET /api/auth/me`
- Code: `backend/app.py:1029-1038`

```javascript
const sessionUser = await apiGet('/api/auth/me');
```

**Entity**

- User identity and role come from `users` and `roles`.

# Researcher User Stories

## User Story B.1 - Obtain Accurate Results

**Boundary - frontend**

- Accurate result review: `frontend/pages/researcher.html:17-37`
- Flag action: `frontend/pages/result.html:205-231`

**Control / AI**

- Accurate SAHI inference: `backend/inference.py:140-186`
- Result review route: `backend/app.py:2229-2255`

```python
@app.route("/api/results/<int:result_id>/flag", methods=["POST"])
@require_roles("Researcher", "Admin")
def flag_result(result_id):
    ...
```

**Entity**

- `quality_status` and `review_note` are stored in `detection_results`.

## User Story B.2 - Export Standard Formats

**Boundary - frontend**

- Date range, record selection and format controls:
  `frontend/pages/export.html:17-64`
- CSV/JSON generation and download: `frontend/pages/export.html:66-127`

```javascript
const selected = records.filter(record => record.selected && inDateRange(record));
const output = format === 'json' ? JSON.stringify(selected) : buildCsv(selected);
```

**Control - backend**

- Source records are retrieved through `GET /api/history`.

**Entity**

- Export data comes from `images` joined with `detection_results`.

## User Story B.3 - Analyse Historical Data

**Boundary - frontend**

- Filters, sorting and trend chart: `frontend/pages/history.html:63-128`
- Researcher shortcut: `frontend/pages/researcher.html:40-44`

**Control - backend**

- Route: `GET /api/history`
- Date, field, search, sort and limit handling:
  `backend/app.py:1205-1268`

```javascript
const records = await apiGet(
  `/api/history?from=${from}&to=${to}&field=${field}&sort=${sort}`
);
```

**Entity**

- Historical timeline uses `detection_results.created_at`.
- Field filtering uses `images.field_id`.

## User Story B.4 - Compare Model Outputs

**Boundary - frontend**

- Model, dataset and YAML selectors:
  `frontend/pages/researcher.html:46-63`
- Comparison action: `frontend/pages/researcher.html:156-175`

**Control / AI**

- Route: `POST /api/models/compare`
- Code: `backend/app.py:2072-2133`
- Shared validation uses `evaluate_model()`:
  `backend/training.py:40-55`

**Entity**

- Registered metrics and weight paths come from `models`.
- The historical v0.9 entry is metrics-only and is not treated as real weights.

## User Story B.5 - Access Raw Datasets

**Boundary - frontend**

- Dataset list: `frontend/pages/researcher.html:64-74`
- ZIP/TAR.GZ selection and download:
  `frontend/pages/researcher.html:177-190`

**Control - backend**

- Dataset list: `backend/app.py:1835-1882`
- Authenticated package download: `backend/app.py:1966-2021`

```javascript
window.location.href =
  `${API_BASE}/api/datasets/${datasetId}/download?format=${format}`;
```

**Entity**

- Dataset metadata is stored in `datasets`.

## User Story B.6 - Generate Visual Reports

**Boundary - frontend**

- Date, field and report-type form: `frontend/pages/report.html:1-57`
- Generate and render report: `frontend/pages/report.html:58-96`

**Control - backend**

- Route: `POST /api/reports`
- Query, aggregation and persistence: `backend/app.py:1426-1519`

```javascript
const report = await apiPost('/api/reports', {
  date_from: from,
  date_to: to,
  field_ids: selectedFields,
  report_type: type
});
```

**Entity**

- Generated summaries are persisted in `reports`.

# Agronomist User Stories

## User Story C.1 - Evaluate Plant Health

**Boundary - frontend**

- Health tab and recommendation controls:
  `frontend/pages/agronomist.html:15,113-138`

**Control - backend**

- Health route: `backend/app.py:2712-2747`
- Recommendation route: `backend/app.py:2748-2783`

**Entity**

- Health values are stored in `fields`.
- Agronomist notes are stored in `recommendations`.

## User Story C.2 - Monitor Growth over Time

**Boundary - frontend**

- Field/period chart controls: `frontend/pages/agronomist.html:140-153`

**Control - backend**

- Route: `GET /api/fields/<field_id>/growth`
- Weekly database aggregation: `backend/app.py:2784-2832`

```javascript
const growth = await apiGet(`/api/fields/${fieldId}/growth?period=${period}`);
```

**Entity**

- Aggregation uses `images.field_id` and `detection_results.created_at`.

## User Story C.3 - Detect Abnormal Patterns

**Boundary - frontend**

- Alert scan and review request: `frontend/pages/agronomist.html:155-172`

**Control - backend**

- Anomaly scan: `backend/app.py:2833-2859`
- Persisted review reason: `backend/app.py:2860-2892`

**Entity**

- `fields.anomaly_flag`
- `fields.anomaly_reason`

## User Story C.4 - View Multiple Fields

**Boundary - frontend**

- Multi-field tab, region filter and cards:
  `frontend/pages/agronomist.html:18,58-111`

**Control - backend**

- Route: `GET /api/fields?region=<region>`
- Code: `backend/app.py:2694-2711`

**Entity**

- The dashboard reads all matching records from `fields`.

## User Story C.5 - Receive Summarized Insights

**Boundary - frontend**

- Insight display and text export:
  `frontend/pages/agronomist.html:174-187`

**Control - backend**

- Route: `GET /api/fields/insights`
- 30-day summary: `backend/app.py:2893-2929`

**Entity**

- Insights combine `fields`, `images` and `detection_results`.

# Admin User Stories

## User Story D.1 - Manage User Accounts

**Boundary - frontend**

- User list and CRUD controls: `frontend/pages/admin.html:84-193`

**Control - backend**

- Collection route: `backend/app.py:1520-1596`
- Individual user route: `backend/app.py:1597-1711`
- Status route: `backend/app.py:1712-1735`

**Entity**

- Accounts are stored in `users`; role definitions are stored in `roles`.

## User Story D.2 - Store Images Securely

**Boundary - frontend**

- Storage status and policy controls:
  `frontend/pages/admin.html:195-228`

**Control - backend**

- Fernet storage helpers: `backend/app.py:328-375`
- Access policies: `backend/app.py:1789-1834`
- Storage metrics: `backend/app.py:2513-2542`
- Protected retrieval: `backend/app.py:2543-2599`

**Entity**

- Encrypted bytes and metadata: `image_files`
- Role policy: `access_policies`
- Audit records: `system_logs`

## User Story D.3 - Monitor System Usage

**Boundary - frontend**

- System monitoring panel: `frontend/pages/admin.html:229-253`

**Control - backend**

- Statistics: `backend/app.py:2390-2440`
- Logs: `backend/app.py:2441-2446`

**Entity**

- Metrics are derived from `users`, `images`, `detection_results` and
  `system_logs`.

## User Story D.4 - Manage Datasets

**Boundary - frontend**

- Dataset upload/edit/delete/list:
  `frontend/pages/admin.html:254-342`

**Control - backend**

- Dataset collection: `backend/app.py:1835-1882`
- Update/delete: `backend/app.py:1883-1920`
- Package upload: `backend/app.py:1921-1965`

**Entity**

- Dataset metadata and package paths are stored in `datasets`.

## User Story D.5 - Control Permissions

**Boundary - frontend**

- User, role and permission matrix:
  `frontend/pages/admin.html:343-401`

**Control - backend**

- Permission guard: `backend/app.py:301-327`
- Permission API: `backend/app.py:1736-1788`

```python
@require_roles("Admin", permission="manage_users")
def protected_admin_action():
    ...
```

**Entity**

- Per-user permission arrays are stored in `users.permissions`.

## User Story D.6 - Back Up Data Regularly

**Boundary - frontend**

- Backup history, manual backup and restore:
  `frontend/pages/admin.html:402-469`

**Control - backend**

- Backup creation: `backend/app.py:608-656`
- 24-hour scheduler: `backend/app.py:657-675`
- Admin backup APIs: `backend/app.py:2447-2512`

**Entity**

- Backup files are stored under `backend/backups/`.
- Backup and restore actions are recorded in `system_logs`.

# AI System User Stories

## User Story E.1 - Preprocess Image Data

**Boundary - frontend**

- Preprocess controls: `frontend/pages/system.html:17-26`
- Action handler: `frontend/pages/system.html:106-113`

**Control - backend**

- Route: `POST /api/system/preprocess/<image_id>`
- RGB conversion, resize, normalization and optional augmentation:
  `backend/app.py:2930-2983`

**Entity**

- `images.preprocessed`
- `images.preprocessed_path`
- Encrypted processed file in `image_files`

## User Story E.2 - Train Deep Learning Models

**Boundary - frontend**

- Model, dataset, YAML and hyperparameters:
  `frontend/pages/system.html:27-39`
- Queue/start handler: `frontend/pages/system.html:114-125`

**Control / AI**

- Training run API: `backend/app.py:2256-2313`
- Background execution: `backend/app.py:2314-2389`
- Ultralytics training loop: `backend/training.py:9-37`

```python
result = model.train(
    data=str(dataset_yaml),
    epochs=epochs,
    imgsz=image_size,
    batch=batch,
)
```

**Entity**

- Job status and hyperparameters: `training_runs`
- Produced version and weights path: `models`

## User Story E.3 - Evaluate Model Performance

**Boundary - frontend**

- Metrics table and evaluate action:
  `frontend/pages/system.html:40-49,126-136`

**Control / AI**

- Route: `POST /api/models/<model_id>/evaluate`
- Code: `backend/app.py:2171-2228`
- Ultralytics validation: `backend/training.py:40-55`

**Entity**

- mAP50, precision and recall are stored in `models`.
- mAP50-95 is returned by the evaluation function.

## User Story E.4 - Deploy the Trained Model as a Service

**Boundary - frontend**

- Deployment panel and action:
  `frontend/pages/system.html:50-55,138-143`

**Control / AI**

- Deploy route: `backend/app.py:2134-2170`
- Health-checked live predictor switch:
  `backend/inference.py:230-245`
- Service startup: `backend/server.py`

```python
candidate = activate_predictor(model_path)
# Only after successful loading is the model marked active.
```

**Entity**

- Active/archived deployment state is stored in `models.status`.

## User Story E.5 - Support System and Model Updates

**Boundary - frontend**

- Version, path, parent and changelog form:
  `frontend/pages/system.html:56-68`
- Registration handler: `frontend/pages/system.html:144-161`

**Control - backend**

- Model registration: `POST /api/models`
- Code: `backend/app.py:2022-2071`
- Deployment reuses `POST /api/models/<model_id>/deploy`.

**Entity**

- Version history, parent model and changelog are stored in `models`.

# Presentation Order

For a demonstration or code walkthrough, use this order:

1. Open the relevant BCE/sequence diagram.
2. Show the Boundary section in the frontend page.
3. Show the API route in `backend/app.py`.
4. Show the database table in `database/schema_postgresql.sql`.
5. For AI stories, finish with `backend/inference.py` or
   `backend/training.py`.

This keeps the code demonstration aligned with A.1 through E.5 and prevents
shared code from being presented as unrelated duplicate implementations.
