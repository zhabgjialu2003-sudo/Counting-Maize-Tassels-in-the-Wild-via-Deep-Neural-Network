// Maize Detector — Role-based Auth (Week 10)
// Works within existing BCE: A.7 access, D.1 user management, D.5 permissions

const AUTH_KEY = 'maize_user';

// BCE-defined role → page mapping (A Farmer, B Researcher, C Agronomist, D Admin)
var ROLE_PAGES = {
  Farmer:     ['dashboard.html', 'upload.html', 'result.html'],
  Researcher: ['history.html', 'report.html', 'export.html'],
  Agronomist: ['agronomist.html'],
  Admin:      ['admin.html'],
};

// Shared pages everyone can see
var SHARED_PAGES = [];

function getSession() {
  try { return JSON.parse(sessionStorage.getItem(AUTH_KEY)); } catch(e) { return null; }
}

function setSession(user) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

function clearSession() {
  sessionStorage.removeItem(AUTH_KEY);
}

function isLoggedIn() {
  return !!getSession();
}

function currentRole() {
  var s = getSession();
  return s ? s.role : null;
}

function currentUser() {
  return getSession();
}

// Redirect if not logged in or wrong role
function requireRole(allowedRoles) {
  var s = getSession();
  if (!s) { location.href = 'login.html'; return false; }
  if (allowedRoles && allowedRoles.indexOf(s.role) === -1) {
    location.href = 'login.html';
    return false;
  }
  return true;
}

// Build filtered navigation based on user role
function buildNav() {
  var s = getSession();
  if (!s) return '<a href="login.html">Login</a>';

  var role = s.role;
  var pages = ROLE_PAGES[role] || [];
  var links = '';

  // Build nav links for current role only
  var navMap = {
    'dashboard.html':  'Home',
    'upload.html':     'Upload',
    'result.html':     'Result',
    'history.html':    'History',
    'report.html':     'Report',
    'export.html':     'Export',
    'agronomist.html': 'Agronomist',
    'admin.html':      'Admin',
  };

  links = pages.map(function(p) {
    var label = navMap[p] || p;
    return '<a href="' + p + '">' + label + '</a>';
  }).join('\n        ');

  return '<a class="nav-brand" href="' + (pages[0] || '#') + '">Maize Detector</a>\n' +
    '      <div class="nav-links">\n' +
    '        ' + links + '\n' +
    '        <a href="#" onclick="logout()" style="opacity:0.7;">Logout (' + esc(s.name) + ')</a>\n' +
    '      </div>';
}

function logout() {
  clearSession();
  location.href = 'login.html';
}

// Auto-insert navigation bar into current page
function initNav() {
  var navEl = document.getElementById('mainNav');
  if (navEl) {
    navEl.innerHTML = buildNav();
  }
}

async function doLogin(email, password) {
  try {
    var res = await fetch(API_BASE + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password }),
    });
    if (!res.ok) throw new Error(res.statusText);
    var data = await res.json();
    if (data.status === 'success') {
      setSession(data.user);
      return { ok: true, user: data.user };
    }
    return { ok: false, error: data.message || 'Login failed' };
  } catch (e) {
    return { ok: false, error: 'Cannot connect to server. Is the backend running?' };
  }
}
