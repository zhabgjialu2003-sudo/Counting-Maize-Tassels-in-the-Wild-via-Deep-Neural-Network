// Maize Detector - server-validated role-based authentication.
const AUTH_KEY = 'maize_user';
const TOKEN_KEY = 'maize_access_token';

const ROLE_PAGES = {
  Farmer: ['mobile.html', 'dashboard.html', 'upload.html', 'leaf.html', 'result.html', 'history.html', 'profile.html'],
  Researcher: ['researcher.html', 'history.html', 'report.html', 'export.html'],
  Agronomist: ['agronomist.html'],
  Admin: ['admin.html', 'system.html'],
};

function getSession() {
  try {
    return JSON.parse(sessionStorage.getItem(AUTH_KEY));
  } catch (error) {
    clearSession();
    return null;
  }
}

function setSession(user, accessToken) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(normalizeSessionUser(user)));
  if (accessToken) sessionStorage.setItem(TOKEN_KEY, accessToken);
}

function clearSession() {
  sessionStorage.removeItem(AUTH_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

function accessToken() {
  return sessionStorage.getItem(TOKEN_KEY) || '';
}

function isLoggedIn() {
  return Boolean(getSession() && accessToken());
}

function currentRole() {
  const session = getSession();
  return session ? session.role : null;
}

function currentUser() {
  return getSession();
}

async function validateSession() {
  if (!isLoggedIn()) return false;
  const result = await apiGet('/api/auth/me');
  if (!result.ok || !result.data.user) {
    clearSession();
    location.href = 'login.html';
    return false;
  }
  setSession(result.data.user, accessToken());
  return true;
}

function defaultPageForRole(role) {
  if (role === 'Farmer' && window.matchMedia('(max-width: 768px)').matches) {
    return 'mobile.html';
  }
  const pages = ROLE_PAGES[role] || [];
  return role === 'Farmer' ? 'dashboard.html' : (pages[0] || 'login.html');
}

function normalizeSessionUser(user = {}) {
  return {
    user_id: user.user_id ?? user.userId ?? user.id ?? null,
    name: user.name ?? user.full_name ?? user.email ?? 'User',
    email: user.email ?? '',
    role: user.role ?? user.role_name ?? user.roleName ?? '',
    status: user.status ?? 'active',
    permissions: user.permissions ?? [],
  };
}

function requireRole(allowedRoles) {
  const session = getSession();
  if (!session || !accessToken()) {
    clearSession();
    location.href = 'login.html';
    return false;
  }
  if (allowedRoles && !allowedRoles.includes(session.role)) {
    location.href = defaultPageForRole(session.role);
    return false;
  }
  return true;
}

function buildNav() {
  const session = getSession();
  if (!session) return '<a href="login.html">Login</a>';

  const isMobileFarmer =
    session.role === 'Farmer' && window.matchMedia('(max-width: 768px)').matches;
  const pages = isMobileFarmer
    ? ['mobile.html', 'upload.html', 'leaf.html', 'history.html', 'profile.html']
    : (session.role === 'Farmer'
      ? ['dashboard.html', 'upload.html', 'result.html']
      : (ROLE_PAGES[session.role] || []));
  const navMap = {
    'mobile.html': 'Home',
    'dashboard.html': 'Home',
    'researcher.html': 'Dashboard',
    'upload.html': 'Upload',
    'leaf.html': 'Leaf Assistant',
    'result.html': 'Result',
    'history.html': 'History',
    'profile.html': 'My account',
    'report.html': 'Report',
    'export.html': 'Export',
    'agronomist.html': 'Agronomist',
    'admin.html': 'Admin',
    'system.html': 'AI System',
  };
  const links = pages.map(page =>
    `<a href="${page}">${navMap[page] || page}</a>`
  ).join('\n        ');

  return `<a class="nav-brand" href="${defaultPageForRole(session.role)}">Maize Detector</a>
      <div class="nav-links">
        ${links}
        <a href="#" onclick="logout();return false;" style="opacity:0.75;">Logout (${esc(session.name)} - ${esc(session.role)})</a>
      </div>`;
}

function initNav() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  nav.innerHTML = buildNav();
  if (typeof setActiveNav === 'function') setActiveNav();
}

function logout() {
  clearSession();
  location.href = 'login.html';
}

function confirmLogout(language = 'en') {
  const zh = language === 'zh-CN';
  const message = zh
    ? '确定要退出登录吗？退出后需要重新输入邮箱和密码。'
    : 'Sign out now? You will need your email and password to sign in again.';
  if (window.confirm(message)) logout();
}

async function doLogin(email, password) {
  const result = await apiPost('/api/auth/login', { email, password });
  if (!result.ok || result.data.status !== 'success') {
    return { ok: false, error: result.error || result.data.message || 'Login failed' };
  }
  const user = normalizeSessionUser(result.data.user);
  setSession(user, result.data.access_token);
  return { ok: true, user };
}

async function createAccount(name, email, password) {
  const result = await apiPost('/api/auth/register', { name, email, password });
  if (!result.ok || result.data.status !== 'success') {
    const message = result.status === 409
      ? 'This email already exists. Please sign in instead.'
      : result.error || result.data.message || 'Account creation failed';
    return { ok: false, error: message };
  }
  const user = normalizeSessionUser(result.data.user);
  setSession(user, result.data.access_token);
  return { ok: true, user };
}
