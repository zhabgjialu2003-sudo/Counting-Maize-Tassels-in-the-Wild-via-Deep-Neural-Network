// Maize Detector - Role-based Auth (Week 10 prototype)
// Maps the fixed FYP roles to their own workspaces without changing user stories.

const AUTH_KEY = 'maize_user';

var ROLE_PAGES = {
  Farmer: ['dashboard.html', 'upload.html', 'result.html'],
  Researcher: ['researcher.html', 'history.html', 'report.html', 'export.html'],
  Agronomist: ['agronomist.html'],
  Admin: ['admin.html'],
};

function getSession() {
  try {
    return JSON.parse(sessionStorage.getItem(AUTH_KEY));
  } catch (e) {
    return null;
  }
}

function setSession(user) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(normalizeSessionUser(user)));
}

function clearSession() {
  sessionStorage.removeItem(AUTH_KEY);
}

function isLoggedIn() {
  return !!getSession();
}

function currentRole() {
  var session = getSession();
  return session ? session.role : null;
}

function currentUser() {
  return getSession();
}

function defaultPageForRole(role) {
  var pages = ROLE_PAGES[role] || [];
  return pages[0] || 'login.html';
}

function normalizeSessionUser(user) {
  user = user || {};
  return {
    user_id: user.user_id || user.userId || user.id,
    name: user.name || user.full_name || user.email || 'Demo User',
    email: user.email || '',
    role: user.role || user.role_name || user.roleName || 'Farmer',
    status: user.status || 'active',
  };
}

function requireRole(allowedRoles) {
  var session = getSession();
  if (!session) {
    location.href = 'login.html';
    return false;
  }
  if (allowedRoles && allowedRoles.indexOf(session.role) === -1) {
    location.href = defaultPageForRole(session.role);
    return false;
  }
  return true;
}

function buildNav() {
  var session = getSession();
  if (!session) return '<a href="login.html">Login</a>';

  var role = session.role;
  var pages = ROLE_PAGES[role] || [];
  var navMap = {
    'dashboard.html': 'Home',
    'researcher.html': 'Dashboard',
    'upload.html': 'Upload',
    'result.html': 'Result',
    'history.html': 'History',
    'report.html': 'Report',
    'export.html': 'Export',
    'agronomist.html': 'Agronomist',
    'admin.html': 'Admin',
  };

  var links = pages.map(function(page) {
    var label = navMap[page] || page;
    return '<a href="' + page + '">' + label + '</a>';
  }).join('\n        ');

  return '<a class="nav-brand" href="' + defaultPageForRole(role) + '">Maize Detector</a>\n' +
    '      <div class="nav-links">\n' +
    '        ' + links + '\n' +
    '        <a href="#" onclick="logout()" style="opacity:0.75;">Logout (' + esc(session.name) + ' - ' + esc(role) + ')</a>\n' +
    '      </div>';
}

function initNav() {
  var navEl = document.getElementById('mainNav');
  if (navEl) {
    navEl.innerHTML = buildNav();
    if (typeof setActiveNav === 'function') setActiveNav();
  }
}

function logout() {
  clearSession();
  location.href = 'login.html';
}

function fallbackLogin(email) {
  var normalized = String(email || '').trim().toLowerCase();
  var user = MockData.users.find(function(candidate) {
    return String(candidate.email || '').toLowerCase() === normalized;
  });

  if (!user) return { ok: false, error: 'Invalid email or password' };
  if (user.status === 'disabled') return { ok: false, error: 'Account is disabled. Contact administrator.' };

  var sessionUser = {
    user_id: user.userId,
    name: user.name,
    email: user.email,
    role: user.role,
  };
  setSession(sessionUser);
  return { ok: true, user: sessionUser, source: 'mock' };
}

async function doLogin(email, password) {
  try {
    var response = await fetch(API_BASE + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password }),
    });
    var data = await response.json().catch(function() { return {}; });

    if (response.ok && data.status === 'success') {
      var sessionUser = normalizeSessionUser(data.user);
      setSession(sessionUser);
      return { ok: true, user: sessionUser, source: data.source || 'api' };
    }

    var fallback = fallbackLogin(email);
    return fallback.ok ? fallback : { ok: false, error: data.message || 'Login failed' };
  } catch (e) {
    return fallbackLogin(email);
  }
}
