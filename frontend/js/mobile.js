// Shared mobile image preparation utilities. User photos remain in memory only.
function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function loadImageForCompression(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('This photo could not be opened. Please choose another JPG or PNG.'));
    };
    image.src = url;
  });
}

async function prepareImageForUpload(file, options = {}) {
  const validTypes = ['image/jpeg', 'image/png'];
  if (!file || !validTypes.includes(file.type)) {
    throw new Error('Please choose a JPG or PNG photo.');
  }
  if (file.size > 20 * 1024 * 1024) {
    throw new Error('This photo is larger than 20 MB. Please choose a smaller photo.');
  }

  const maxLongEdge = Number(options.maxLongEdge || 2560);
  const quality = Number(options.quality || 0.86);
  const image = await loadImageForCompression(file);
  const longEdge = Math.max(image.naturalWidth, image.naturalHeight);
  const scale = Math.min(1, maxLongEdge / longEdge);
  const width = Math.max(1, Math.round(image.naturalWidth * scale));
  const height = Math.max(1, Math.round(image.naturalHeight * scale));

  // Keep an already efficient JPEG when resizing would provide no benefit.
  if (scale === 1 && file.type === 'image/jpeg' && file.size <= 2.5 * 1024 * 1024) {
    return {
      file,
      originalBytes: file.size,
      preparedBytes: file.size,
      width,
      height,
      compressed: false,
    };
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d', { alpha: false });
  context.fillStyle = '#fff';
  context.fillRect(0, 0, width, height);
  context.drawImage(image, 0, 0, width, height);
  const blob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      value => value ? resolve(value) : reject(new Error('The photo could not be compressed.')),
      'image/jpeg',
      quality
    );
  });
  const baseName = file.name.replace(/\.[^.]+$/, '') || 'maize-photo';
  const prepared = new File([blob], `${baseName}-mobile.jpg`, {
    type: 'image/jpeg',
    lastModified: Date.now(),
  });
  return {
    file: prepared,
    originalBytes: file.size,
    preparedBytes: prepared.size,
    width,
    height,
    compressed: true,
  };
}

function mobileLanguage() {
  const saved = localStorage.getItem('maize_mobile_language');
  if (saved === 'zh-CN' || saved === 'en') return saved;
  const pageLanguage = (document.documentElement.lang || '').toLowerCase();
  return pageLanguage.startsWith('zh') ? 'zh-CN' : 'en';
}

function setMobileLanguage(language) {
  localStorage.setItem('maize_mobile_language', language === 'zh-CN' ? 'zh-CN' : 'en');
}

function bindNetworkStatus() {
  const banner = document.getElementById('networkStatus');
  if (!banner) return;
  const render = () => {
    const zh = mobileLanguage() === 'zh-CN';
    banner.hidden = navigator.onLine;
    banner.textContent = zh
      ? '当前没有网络。照片仍保留在本页；联网后请重新上传。'
      : 'You are offline. Your photo stays on this page; reconnect and try again.';
  };
  window.addEventListener('online', render);
  window.addEventListener('offline', render);
  render();
}

document.addEventListener('DOMContentLoaded', bindNetworkStatus);
