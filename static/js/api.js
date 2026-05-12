/**
 * API wrapper — adds JWT token to all requests, handles refresh.
 */
const API = (() => {
  const BASE = '';

  function getToken() {
    return localStorage.getItem('access_token');
  }

  function headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    const tok = getToken();
    if (tok) h['Authorization'] = `Bearer ${tok}`;
    return h;
  }

  async function request(method, path, body = null, isForm = false) {
    const opts = { method, headers: isForm ? { Authorization: `Bearer ${getToken()}` } : headers() };
    if (body && !isForm) opts.body = JSON.stringify(body);
    if (body && isForm)  opts.body = body;

    let res = await fetch(BASE + path, opts);

    // Auto-redirect on 401
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please log in again.');
    }

    const data = await res.json();
    if (!res.ok && !data.success) {
      data.success = false;
      data.message = data.message || data.msg || 'An error occurred';
    }
    return data;
  }

  return {
    get:    (path)        => request('GET',    path),
    post:   (path, body)  => request('POST',   path, body),
    put:    (path, body)  => request('PUT',    path, body),
    delete: (path)        => request('DELETE', path),
    postForm: (path, fd)  => request('POST',   path, fd, true),
  };
})();

/**
 * Toast notifications
 */
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  const icon = type === 'success'
    ? '<svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 13l4 4L19 7" /></svg>'
    : type === 'error'
      ? '<svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12" /><path d="M18 6l-12 12" /></svg>'
      : '<svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 16h.01" /></svg>';
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `${icon}<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Format date/time helpers
 */
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function fmtTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

function fmtDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function confidencePct(c) {
  if (c === null || c === undefined) return '—';
  return (c * 100).toFixed(0) + '%';
}

function statusBadge(status) {
  const map = { Present: 'green', Absent: 'red', Late: 'yellow' };
  return `<span class="badge badge-${map[status] || 'gray'}">${status}</span>`;
}

function methodBadge(m) {
  return `<span class="badge badge-${m === 'Auto' ? 'blue' : 'purple'}">${m}</span>`;
}

/**
 * Debounce helper
 */
function debounce(fn, delay = 400) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

/**
 * Render pagination controls
 */
function renderPagination(containerId, pagination, onPage) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const { page, pages, has_prev, has_next } = pagination;
  if (pages <= 1) { el.innerHTML = ''; return; }
  let html = '';
  if (has_prev) html += `<button class="page-btn" onclick="${onPage}(${page - 1})">‹</button>`;
  for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i++) {
    html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="${onPage}(${i})">${i}</button>`;
  }
  if (has_next) html += `<button class="page-btn" onclick="${onPage}(${page + 1})">›</button>`;
  el.innerHTML = html;
}

// Guard pages that require authentication
(function() {
  const publicPaths = ['/login'];
  if (!publicPaths.includes(window.location.pathname) && !localStorage.getItem('access_token')) {
    window.location.href = '/login';
  }
})();
