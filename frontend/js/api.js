// Maize Detector - shared API client and response normalization.
// Use IPv4 explicitly because some Windows browsers resolve localhost to ::1
// while the local assessment server listens on 127.0.0.1.
const API_BASE = 'http://127.0.0.1:5000';

async function apiRequest(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: authHeaders(options.headers),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error: data.message || data.error || response.statusText || 'Request failed',
      };
    }
    return { ok: true, status: response.status, data };
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    return {
      ok: false,
      status: 0,
      error: `Cannot connect to the backend service at ${API_BASE}. Check that the API is running.`,
    };
  }
}

function apiGet(endpoint) {
  return apiRequest(endpoint);
}

function apiPost(endpoint, body) {
  return apiRequest(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function apiPut(endpoint, body) {
  return apiRequest(endpoint, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

function apiUpload(file) {
  const form = new FormData();
  form.append('image', file);
  return apiRequest('/api/upload', { method: 'POST', body: form });
}

function normalizeResult(raw) {
  const bboxData = normalizeBBoxData(raw.bbox_data ?? raw.bboxData ?? null);
  const imagePath =
    raw.image_path ?? raw.imagePath ?? raw.original_image_path ?? raw.originalImagePath ?? null;
  return {
    resultId: raw.result_id ?? raw.resultId ?? null,
    imageId: raw.image_id ?? raw.imageId ?? null,
    imageName: raw.image_name ?? raw.imageName ?? 'Unknown image',
    tasselCount: raw.count ?? raw.tassel_count ?? raw.tasselCount ?? 0,
    confidenceScore: raw.confidence ?? raw.confidence_score ?? raw.confidenceScore ?? 0,
    processingTime: raw.processing_time ?? raw.processingTime ?? raw.time ?? 0,
    createdAt: raw.created_at ?? raw.createdAt ?? null,
    imagePath,
    originalImagePath: raw.original_image_path ?? raw.originalImagePath ?? imagePath,
    annotatedImagePath: raw.annotated_image_path ?? raw.annotatedImagePath ?? null,
    bboxData,
    source: raw.source ?? 'database',
    fieldName: raw.field_name ?? raw.fieldName ?? '',
    qualityStatus: raw.quality_status ?? raw.qualityStatus ?? 'unreviewed',
    reviewNote: raw.review_note ?? raw.reviewNote ?? '',
  };
}

function normalizeBBoxData(raw) {
  if (!raw) return null;
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.error('Invalid bbox JSON returned by API', error);
      return null;
    }
  }
  return raw;
}

function resolveAssetUrl(path) {
  if (!path) return null;
  if (path.startsWith('data:') || path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const token = sessionStorage.getItem('maize_access_token');
  const authQuery = token ? `?access_token=${encodeURIComponent(token)}` : '';
  if (path.startsWith('/storage/uploads/')) {
    return `${API_BASE}${path.replace('/storage', '')}${authQuery}`;
  }
  if (path.startsWith('/uploads/')) return `${API_BASE}${path}${authQuery}`;
  if (path.startsWith('uploads/')) return `${API_BASE}/${path}${authQuery}`;
  return path;
}

function authHeaders(extra) {
  const headers = Object.assign({}, extra || {});
  const token = sessionStorage.getItem('maize_access_token');
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function setActiveNav() {
  const page = location.pathname.split('/').pop().replace('.html', '');
  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.getAttribute('href').includes(page)) link.classList.add('active');
  });
}

function esc(value) {
  const element = document.createElement('div');
  element.textContent = value ?? '';
  return element.innerHTML;
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(0)}%` : '-';
}
