(async function initialiseFarmerDashboard() {
  'use strict';
  if (!requireRole(['Farmer']) || !await validateSession()) return;
  initNav();
  setActiveNav();

  const [statsResponse, historyResponse] = await Promise.all([
    apiGet('/api/stats'),
    apiGet('/api/history'),
  ]);
  const table = document.getElementById('recentTable');
  if (!statsResponse.ok || !historyResponse.ok) {
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 5;
    cell.className = 'info-text';
    cell.textContent = 'Unable to load dashboard data. Check the backend service.';
    return;
  }

  document.getElementById('totalImages').textContent = statsResponse.data.total_uploaded_images ?? 0;
  document.getElementById('totalTassels').textContent = Number(statsResponse.data.total_detected_tassels ?? 0).toLocaleString();
  document.getElementById('avgCount').textContent = Number(statsResponse.data.average_tassel_count ?? 0).toFixed(1);
  const records = Array.isArray(historyResponse.data.records) ? historyResponse.data.records.map(normalizeResult) : [];
  const latestResultLink = document.getElementById('latestResultLink');
  if (!records.length) {
    if (latestResultLink) latestResultLink.href = 'upload.html';
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 5;
    cell.className = 'info-text';
    cell.textContent = 'No tassel-counting records yet.';
    return;
  }
  if (latestResultLink) {
    latestResultLink.href = `result.html?id=${encodeURIComponent(records[0].resultId)}`;
  }
  records.forEach(record => {
    const row = table.insertRow();
    [record.imageName, formatDate(record.createdAt), record.tasselCount, formatPercent(record.confidenceScore)].forEach(value => {
      row.insertCell().textContent = value;
    });
    const link = document.createElement('a');
    link.href = `result.html?id=${encodeURIComponent(record.resultId)}`;
    link.className = 'btn btn-sm btn-outline';
    link.textContent = 'View';
    row.insertCell().append(link);
  });
})();
