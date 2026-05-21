// Maize Detector App — Shared API & Data Layer
const API_BASE = 'http://localhost:5000';

// === Mock Data (matches BCE Entities) ===
const MockData = {
  // DetectionResult (E: used by A.2, A.3, A.4, B.1, B.3, C.2, C.5)
  results: [
    { resultId: 1, imageName: 'maize_field_01.jpg', tasselCount: 37, confidenceScore: 0.89, processingTime: 2.4,
      createdAt: '2026-06-10', annotatedImagePath: 'data:image/svg+xml,...' },
    { resultId: 2, imageName: 'maize_field_02.jpg', tasselCount: 42, confidenceScore: 0.91, processingTime: 2.1,
      createdAt: '2026-06-11', annotatedImagePath: 'data:image/svg+xml,...' },
    { resultId: 3, imageName: 'maize_field_03.jpg', tasselCount: 29, confidenceScore: 0.85, processingTime: 3.0,
      createdAt: '2026-06-12', annotatedImagePath: 'data:image/svg+xml,...' },
    { resultId: 4, imageName: 'maize_field_04.jpg', tasselCount: 35, confidenceScore: 0.93, processingTime: 1.8,
      createdAt: '2026-06-13', annotatedImagePath: 'data:image/svg+xml,...' },
    { resultId: 5, imageName: 'maize_field_05.jpg', tasselCount: 31, confidenceScore: 0.87, processingTime: 2.6,
      createdAt: '2026-06-13', annotatedImagePath: 'data:image/svg+xml,...' },
  ],
  // User (E: used by A.7, D.1, D.5)
  users: [
    { userId: 1, name: 'John Smith', email: 'john@farm.com', role: 'Farmer', status: 'active' },
    { userId: 2, name: 'Dr. Li Wei', email: 'liwei@research.org', role: 'Researcher', status: 'active' },
    { userId: 3, name: 'Maria Garcia', email: 'maria@agro.com', role: 'Agronomist', status: 'active' },
    { userId: 4, name: 'Admin User', email: 'admin@system.com', role: 'Admin', status: 'active' },
    { userId: 5, name: 'Bob Brown', email: 'bob@farm.com', role: 'Farmer', status: 'disabled' },
  ],
  // Field (E: used by C.1, C.2, C.3, C.4)
  fields: [
    { fieldId: 1, fieldName: 'Field A - North', location: 'North Region', status: 'Healthy', latestAvgCount: 35, baselineCount: 30, healthStatus: 'Healthy' },
    { fieldId: 2, fieldName: 'Field B - East', location: 'East Region', status: 'Warning', latestAvgCount: 18, baselineCount: 30, healthStatus: 'At-Risk' },
    { fieldId: 3, fieldName: 'Field C - South', location: 'South Region', status: 'Healthy', latestAvgCount: 42, baselineCount: 40, healthStatus: 'Healthy' },
  ],
  // Dataset (E: used by B.5, D.4)
  datasets: [
    { datasetId: 1, datasetName: 'Maize Tassel Train v1', totalImages: 200, annotationStatus: 'completed', annotationFormat: 'YOLO' },
    { datasetId: 2, datasetName: 'Maize Tassel Train v2', totalImages: 500, annotationStatus: 'in_progress', annotationFormat: 'COCO' },
    { datasetId: 3, datasetName: 'Batch 3 - North Fields', totalImages: 320, annotationStatus: 'not_started', annotationFormat: null },
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
