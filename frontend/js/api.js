// Maize Detector App — Shared API & Data Layer
// v2.0 — MockData matches PostgreSQL database scale (May 2026)
const API_BASE = 'http://localhost:5000';

// === Mock Data (matches PostgreSQL maize_detector database) ===
const MockData = {
  // DetectionResult — 47 rows in DB, sample of all ranges
  results: (() => {
    const imageNames = [
      'maize_field_01.jpg','maize_field_02.jpg','maize_field_03.jpg','maize_field_04.jpg','maize_field_05.jpg',
      'mtdc_DJI_0597_0_0.JPG','mtdc_DJI_0597_0_1.JPG','mtdc_DJI_0597_1_0.JPG','mtdc_DJI_0597_1_1.JPG',
      'mtdc_DJI_0607_0_0.JPG','mtdc_DJI_0607_0_1.JPG','mtdc_DJI_0607_1_0.JPG','mtdc_DJI_0607_1_1.JPG',
      'mtdc_DJI_0617_0_0.JPG','mtdc_DJI_0617_0_1.JPG','mtdc_DJI_0617_1_0.JPG','mtdc_DJI_0617_1_1.JPG',
      'mtdc_DJI_0627_0_0.JPG','mtdc_DJI_0627_0_1.JPG','mtdc_DJI_0627_1_0.JPG','mtdc_DJI_0627_1_1.JPG',
      'mtdc_DJI_0647_(2)_0_0.JPG','mtdc_DJI_0647_(2)_0_1.JPG','mtdc_DJI_0647_(2)_1_0.JPG','mtdc_DJI_0647_(2)_1_1.JPG',
      'mtdc_DJI_0652_(2)_0_0.JPG','mtdc_DJI_0652_(2)_0_1.JPG','mtdc_DJI_0652_(2)_1_0.JPG','mtdc_DJI_0652_(2)_1_1.JPG',
      'mtdc_DJI_0656_0_0.JPG','mtdc_DJI_0656_0_1.JPG','mtdc_DJI_0656_1_0.JPG','mtdc_DJI_0656_1_1.JPG',
      'mtdc_DJI_0661_0_0.JPG','mtdc_DJI_0661_0_1.JPG','mtdc_DJI_0661_1_0.JPG','mtdc_DJI_0661_1_1.JPG',
      'mtdc_DJI_0666_0_0.JPG','mtdc_DJI_0666_0_1.JPG','mtdc_DJI_0666_1_0.JPG','mtdc_DJI_0666_1_1.JPG',
      'mtdc_DJI_0672_(2)_0_0.JPG','mtdc_DJI_0672_(2)_0_1.JPG','mtdc_DJI_0672_(2)_1_0.JPG','mtdc_DJI_0672_(2)_1_1.JPG',
    ];
    return imageNames.map((name, i) => ({
      resultId: i + 1,
      imageName: name,
      imageId: i + 1,
      tasselCount: [37,42,29,35,31, 90,85,95,88, 72,78,82,80, 93,88,91,86, 103,98,105,100, 53,60,58,55, 69,72,66,70, 81,78,84,79, 90,85,93,88, 123,115,121,118, 122,119,120,116][i] || Math.floor(50 + Math.random() * 80),
      confidenceScore: 0.85 + Math.random() * 0.1,
      processingTime: 1.8 + Math.random() * 1.2,
      createdAt: `2026-06-${String(10 + Math.floor(i / 4)).padStart(2, '0')}`,
      annotatedImagePath: null,
    }));
  })(),

  // Users — 7 rows matching DB
  users: [
    { userId: 1, name: 'John Smith',   email: 'john@farm.com',      role: 'Farmer',     status: 'active' },
    { userId: 2, name: 'Dr. Li Wei',   email: 'liwei@research.org', role: 'Researcher', status: 'active' },
    { userId: 3, name: 'Maria Garcia', email: 'maria@agro.com',     role: 'Agronomist', status: 'active' },
    { userId: 4, name: 'Admin User',   email: 'admin@system.com',   role: 'Admin',      status: 'active' },
    { userId: 5, name: 'Bob Brown',    email: 'bob@farm.com',       role: 'Farmer',     status: 'disabled' },
    { userId: 7, name: 'Test Farmer Updated', email: 'test@farm.com',    role: 'Farmer', status: 'disabled' },
    { userId: 9, name: 'Audit Test',   email: 'audit@test.com',     role: 'Farmer',     status: 'active' },
  ],

  // Fields — 10 key MTDC fields from DB images 11-50
  fields: [
    { fieldId: 1,  fieldName: 'Field DJI-0597', location: 'North Region', status: 'Healthy', latestAvgCount: 92, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 2,  fieldName: 'Field DJI-0607', location: 'East Region',  status: 'Healthy', latestAvgCount: 78, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 3,  fieldName: 'Field DJI-0617', location: 'North Region', status: 'Healthy', latestAvgCount: 90, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 4,  fieldName: 'Field DJI-0627', location: 'South Region', status: 'Healthy', latestAvgCount: 102, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 5,  fieldName: 'Field DJI-0647', location: 'North Region', status: 'Warning',  latestAvgCount: 55, baselineCount: 70, healthStatus: 'At-Risk' },
    { fieldId: 6,  fieldName: 'Field DJI-0652', location: 'East Region',  status: 'Healthy', latestAvgCount: 70, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 7,  fieldName: 'Field DJI-0656', location: 'South Region', status: 'Healthy', latestAvgCount: 80, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 8,  fieldName: 'Field DJI-0661', location: 'North Region', status: 'Healthy', latestAvgCount: 88, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 9,  fieldName: 'Field DJI-0666', location: 'East Region',  status: 'Healthy', latestAvgCount: 125, baselineCount: 70, healthStatus: 'Healthy' },
    { fieldId: 10, fieldName: 'Field DJI-0672', location: 'South Region', status: 'Healthy', latestAvgCount: 119, baselineCount: 70, healthStatus: 'Healthy' },
  ],

  // Datasets — 4 rows matching DB
  datasets: [
    { datasetId: 1, datasetName: 'Maize Tassel Train v1',       totalImages: 200, annotationStatus: 'completed',    annotationFormat: 'YOLO' },
    { datasetId: 2, datasetName: 'Maize Tassel Train v2',       totalImages: 500, annotationStatus: 'in_progress',  annotationFormat: 'COCO' },
    { datasetId: 3, datasetName: 'Batch 3 - North Fields',      totalImages: 320, annotationStatus: 'not_started',  annotationFormat: null },
    { datasetId: 4, datasetName: 'MTDC-UAV Demo Detection Set', totalImages: 40,  annotationStatus: 'completed',    annotationFormat: 'Pascal VOC XML' },
  ],

  // System Logs — 7 rows matching DB
  logs: [
    { logId: 1, userId: 4, userName: 'Admin User', action: 'create_user',    details: 'Created user: John Smith (role: Farmer)',                     createdAt: '2026-06-01 08:00:00' },
    { logId: 2, userId: 4, userName: 'Admin User', action: 'backup_created', details: 'Backup completed: 520MB',                                     createdAt: '2026-06-13 23:00:00' },
    { logId: 3, userId: 4, userName: 'Admin User', action: 'access_policy',  details: 'Updated Farmer access level: own_images',                     createdAt: '2026-06-10 12:00:00' },
    { logId: 4, userId: 4, userName: 'Admin User', action: 'role_changed',   details: 'User Bob Brown: Farmer → Researcher',                         createdAt: '2026-06-08 15:30:00' },
    { logId: 5, userId: 4, userName: 'Admin User', action: 'dataset_import', details: 'Imported 40 MTDC-UAV demo images with tassel bounding boxes', createdAt: '2026-05-22 16:31:13' },
    { logId: 6, userId: 4, userName: 'Admin User', action: 'dataset_import', details: 'Imported 40 MTDC-UAV demo images with tassel bounding boxes', createdAt: '2026-05-22 16:36:38' },
    { logId: 7, userId: 4, userName: 'Admin User', action: 'dataset_import', details: 'Imported 40 MTDC-UAV demo images with tassel bounding boxes', createdAt: '2026-05-22 17:00:17' },
  ],
};

// === API Helpers ===
async function apiGet(endpoint) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) throw new Error(res.statusText);
    return { ok: true, data: await res.json() };
  } catch (e) {
    console.warn('API failed, using mock:', e.message);
    return { ok: false, error: e.message };
  }
}

async function apiPost(endpoint, body) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(res.statusText);
    return { ok: true, data: await res.json() };
  } catch (e) {
    console.warn('API failed, using mock:', e.message);
    return { ok: false, error: e.message };
  }
}

async function apiPut(endpoint, body) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(res.statusText);
    return { ok: true, data: await res.json() };
  } catch (e) {
    console.warn('API failed, using mock:', e.message);
    return { ok: false, error: e.message };
  }
}

async function apiDelete(endpoint) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(res.statusText);
    return { ok: true, data: await res.json() };
  } catch (e) {
    console.warn('API failed, using mock:', e.message);
    return { ok: false, error: e.message };
  }
}

// === Field Normalization (snake_case API → camelCase frontend) ===
function normalizeResult(raw) {
  return {
    resultId:   raw.result_id   ?? raw.resultId   ?? Date.now(),
    imageName:  raw.image_name  ?? raw.imageName  ?? 'maize_sample.jpg',
    tasselCount:raw.count       ?? raw.tassel_count ?? raw.tasselCount ?? 0,
    confidenceScore: raw.confidence ?? raw.confidence_score ?? raw.confidenceScore ?? 0.85,
    processingTime: raw.processing_time ?? raw.processingTime ?? raw.time ?? 2.0,
    createdAt:  raw.created_at  ?? raw.createdAt  ?? new Date().toISOString().slice(0,10),
    annotatedImagePath: raw.annotated_image_path ?? raw.annotatedImagePath ?? null,
  };
}

// === Mock Fallback Helpers ===
function mockPredict(imageName) {
  const base = MockData.results[Math.floor(Math.random() * MockData.results.length)];
  return normalizeResult({ ...base, resultId: Date.now(), imageName: imageName || base.imageName });
}

function mockHistory() {
  return { records: MockData.results.map(r => normalizeResult(r)), total: MockData.results.length };
}

// === Navigation Helper ===
function setActiveNav() {
  const page = location.pathname.split('/').pop().replace('.html', '');
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href').includes(page)) a.classList.add('active');
  });
}

// === Formatting ===
function formatDate(d) { return new Date(d).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' }); }
function formatPercent(v) { return (v * 100).toFixed(0) + '%'; }
