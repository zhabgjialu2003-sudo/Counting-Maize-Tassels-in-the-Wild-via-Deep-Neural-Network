// Maize Detector - shared API client and response normalization.
// Local development keeps frontend/backend on separate ports. A deployed PWA
// uses the same HTTPS origin unless an explicit runtime override is supplied.
const API_BASE = (() => {
  const configured = String(window.MAIZE_API_BASE || '').trim().replace(/\/+$/, '');
  if (configured) return configured;
  if (location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname)) {
    return 'http://127.0.0.1:5000';
  }
  return '';
})();

async function apiRequest(endpoint, options = {}) {
  // Set a generous timeout (2 min) to prevent infinite hang on slow CPU inference
  const timeoutMs = options.timeout || 120000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: authHeaders(options.headers),
      signal: controller.signal,
    });
    clearTimeout(timer);
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
    clearTimeout(timer);
    if (error.name === 'AbortError') {
      console.warn(`Request timed out after ${timeoutMs/1000}s: ${endpoint}`);
      return { ok: false, status: 408, error: 'Analysis is taking longer than expected. The server may be busy. Try a smaller image.' };
    }
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

function apiPatch(endpoint, body) {
  return apiRequest(endpoint, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

function apiUpload(file, idempotencyKey = null) {
  const form = new FormData();
  form.append('image', file);
  const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
  return apiRequest('/api/upload', { method: 'POST', body: form, headers });
}

function apiMultipartWithProgress(endpoint, form, onProgress, timeoutMs = 120000, extraHeaders = {}) {
  return new Promise(resolve => {
    const request = new XMLHttpRequest();
    request.open('POST', `${API_BASE}${endpoint}`);
    request.timeout = timeoutMs;
    const token = sessionStorage.getItem('maize_access_token');
    if (token) request.setRequestHeader('Authorization', `Bearer ${token}`);
    Object.entries(extraHeaders).forEach(([name, value]) => {
      if (value !== undefined && value !== null && String(value) !== '') {
        request.setRequestHeader(name, String(value));
      }
    });
    request.upload.onprogress = event => {
      if (event.lengthComputable && typeof onProgress === 'function') {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    request.onload = () => {
      let data = {};
      try { data = JSON.parse(request.responseText || '{}'); } catch (error) {}
      if (request.status >= 200 && request.status < 300) {
        resolve({ ok: true, status: request.status, data });
        return;
      }
      resolve({
        ok: false,
        status: request.status,
        error: data.message || data.error || request.statusText || 'Upload failed',
      });
    };
    request.onerror = () => resolve({
      ok: false,
      status: 0,
      error: navigator.onLine
        ? 'The connection was interrupted. Your photo is still on this page; try again.'
        : 'You are offline. Reconnect, then try this upload again.',
    });
    request.ontimeout = () => resolve({
      ok: false,
      status: 408,
      error: 'The upload is taking longer than expected. Check your signal and try again.',
    });
    request.send(form);
  });
}

function apiUploadWithProgress(file, onProgress, idempotencyKey = null) {
  const form = new FormData();
  form.append('image', file);
  const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {};
  return apiMultipartWithProgress('/api/upload', form, onProgress, 120000, headers);
}

function apiDiagnoseDisease(file, details = {}) {
  const form = new FormData();
  form.append('image', file);
  Object.entries(details).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      form.append(key, String(value));
    }
  });
  return apiRequest('/api/agronomy/diagnose', {
    method: 'POST',
    body: form,
    timeout: 120000,
  });
}

function apiDiagnoseDiseaseWithProgress(file, details = {}, onProgress) {
  const form = new FormData();
  form.append('image', file);
  Object.entries(details).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      form.append(key, String(value));
    }
  });
  return apiMultipartWithProgress('/api/agronomy/diagnose', form, onProgress);
}

function apiReviewDiseaseDiagnosis(diagnosisId, review) {
  return apiPost(`/api/agronomy/diagnoses/${diagnosisId}/review`, review);
}

function normalizeResult(raw) {
  const bboxData = normalizeBBoxData(raw.bbox_data ?? raw.bboxData ?? null);
  return {
    resultId: raw.result_id ?? raw.resultId ?? null,
    imageId: raw.image_id ?? raw.imageId ?? null,
    imageName: raw.image_name ?? raw.imageName ?? 'Unknown image',
    tasselCount: raw.count ?? raw.tassel_count ?? raw.tasselCount ?? 0,
    confidenceScore: raw.confidence ?? raw.confidence_score ?? raw.confidenceScore ?? 0,
    processingTime: raw.processing_time ?? raw.processingTime ?? raw.time ?? 0,
    createdAt: raw.created_at ?? raw.createdAt ?? null,
    originalAssetUrl: raw.original_asset_url ?? raw.originalAssetUrl ?? null,
    annotatedAssetUrl: raw.annotated_asset_url ?? raw.annotatedAssetUrl ?? null,
    bboxData,
    source: raw.source ?? 'database',
    fieldName: raw.field_name ?? raw.fieldName ?? '',
    qualityStatus: raw.quality_status ?? raw.qualityStatus ?? 'unreviewed',
    reviewNote: raw.review_note ?? raw.reviewNote ?? '',
    modelId: raw.model_id ?? raw.modelId ?? null,
    modelVersion: raw.model_version ?? raw.modelVersion ?? null,
    inferenceMode: raw.inference_mode ?? raw.inferenceMode ?? null,
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
  if (path.startsWith('/storage/uploads/')) {
    return `${API_BASE}${path.replace('/storage', '')}`;
  }
  if (path.startsWith('/uploads/') || path.startsWith('/api/images/')) return `${API_BASE}${path}`;
  if (path.startsWith('uploads/')) return `${API_BASE}/${path}`;
  return path;
}

async function fetchProtectedAssetUrl(path) {
  const url = resolveAssetUrl(path);
  if (!url || url.startsWith('data:')) return url;
  const response = await fetch(url, { headers: authHeaders() });
  if (!response.ok) throw new Error(`Image request failed (${response.status})`);
  return URL.createObjectURL(await response.blob());
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
