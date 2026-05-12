/**
 * attendance.js — history page + manual entry on mark page.
 */
let currentPage = 1;
let selectedStudentId = null;

// ── History page ──────────────────────────────────────────────────────────────

async function loadHistory(page = 1) {
  currentPage = page;
  const start   = document.getElementById('filter-start')?.value || '';
  const end     = document.getElementById('filter-end')?.value || '';
  const session = document.getElementById('filter-session')?.value || '';
  const status  = document.getElementById('filter-status')?.value || '';

  const params = new URLSearchParams({ page, per_page: 50 });
  if (start)   params.append('start_date', start);
  if (end)     params.append('end_date', end);
  if (session) params.append('session', session);
  if (status)  params.append('status', status);

  const tbody = document.getElementById('history-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:40px"><div class="spinner" style="margin:0 auto 12px"></div>Loading records…</td></tr>`;

  try {
    const res = await API.get('/api/v1/attendance/?' + params.toString());
    if (!res.success) { showToast(res.message, 'error'); return; }

    const items = res.data.items;
    const pg    = res.data.pagination;

    // Update summary counts
    const total   = pg.total;
    const present = items.filter(r => r.status === 'Present').length;
    const absent  = items.filter(r => r.status === 'Absent').length;
    const late    = items.filter(r => r.status === 'Late').length;
    const setEl = (id, v) => { const e = document.getElementById(id); if(e) e.textContent = v; };
    setEl('h-total', total); setEl('h-present', present); setEl('h-absent', absent); setEl('h-late', late);

    if (tbody) {
      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><h3>No records found</h3></div></td></tr>`;
      } else {
        tbody.innerHTML = items.map(r => `
          <tr>
            <td>
              <div class="flex items-center gap-2">
                <div class="avatar">${(r.student?.name || '?')[0]}</div>
                <div>
                  <div class="font-semibold text-sm">${r.student?.name || '—'}</div>
                  <div class="text-xs text-muted">${r.student?.student_id || ''}</div>
                </div>
              </div>
            </td>
            <td class="text-sm">${fmtDate(r.date)}</td>
            <td class="text-sm">${fmtTime(r.timestamp)}</td>
            <td><span class="badge badge-gray">${r.session || '—'}</span></td>
            <td>${methodBadge(r.method)}</td>
            <td class="text-sm">${r.confidence ? (r.confidence*100).toFixed(0)+'%' : '—'}</td>
            <td>${statusBadge(r.status)}</td>
            <td>
              <button class="btn btn-danger btn-sm" onclick="deleteAttendance(${r.id})" aria-label="Delete attendance">
                <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 6h18" />
                  <path d="M8 6V4h8v2" />
                  <path d="M19 6l-1 14H6L5 6" />
                  <path d="M10 11v6" />
                  <path d="M14 11v6" />
                </svg>
              </button>
            </td>
          </tr>
        `).join('');
      }
    }

    renderPagination('pagination-area', pg, 'loadHistory');
  } catch(e) { showToast('Failed to load records.', 'error'); }
}

async function deleteAttendance(id) {
  if (!confirm('Delete this attendance record?')) return;
  try {
    const res = await API.delete(`/api/v1/attendance/${id}`);
    if (res.success) { showToast('Record deleted.', 'success'); loadHistory(currentPage); }
    else showToast(res.message, 'error');
  } catch(e) { showToast('Delete failed.', 'error'); }
}

function filterTable(query) {
  const rows = document.querySelectorAll('#history-tbody tr');
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(query.toLowerCase()) ? '' : 'none';
  });
}

function exportCSV() {
  const rows = [...document.querySelectorAll('#history-tbody tr')].filter(r => r.style.display !== 'none');
  if (!rows.length) { showToast('No records available for export.', 'error'); return; }
  const headers = ['Student','Date','Time','Session','Method','Confidence','Status'];
  const csvRows = [headers.join(',')];
  rows.forEach(row => {
    const cells = [...row.querySelectorAll('td')].slice(0, 7).map(td => `"${td.textContent.trim().replace(/"/g,'""')}"`);
    csvRows.push(cells.join(','));
  });
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `attendance_${new Date().toISOString().slice(0,10)}.csv`;
  a.click(); URL.revokeObjectURL(url);
}

// ── Manual attendance on mark page ───────────────────────────────────────────

let studentSuggestionsList = [];

async function searchStudents(query) {
  const container = document.getElementById('student-suggestions');
  if (!query || query.length < 2) { if(container) container.innerHTML = ''; return; }
  try {
    const res = await API.get(`/api/v1/students/?search=${encodeURIComponent(query)}&per_page=8`);
    if (!res.success || !container) return;
    const students = res.data.items;
    if (!students.length) { container.innerHTML = ''; return; }
    container.innerHTML = `<div style="position:absolute;top:4px;left:0;right:0;background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-sm);z-index:100;box-shadow:var(--shadow-md)">
      ${students.map(s => `
        <div style="padding:10px 14px;cursor:pointer;transition:var(--transition)" 
             onmouseover="this.style.background='var(--bg-card)'" 
             onmouseout="this.style.background=''"
             onclick="selectStudent(${s.id}, '${s.name}', '${s.student_id}')">
          <div class="font-semibold text-sm">${s.name}</div>
          <div class="text-xs text-muted">${s.student_id} · ${s.department || ''}</div>
        </div>
      `).join('')}
    </div>`;
  } catch(e) {}
}

function selectStudent(id, name, code) {
  selectedStudentId = id;
  const input = document.getElementById('manual-student-search');
  const container = document.getElementById('student-suggestions');
  if (input) input.value = `${name} (${code})`;
  if (container) container.innerHTML = '';
}

async function submitManual() {
  if (!selectedStudentId) { showToast('Please select a student first.', 'error'); return; }
  const session = document.getElementById('manual-session')?.value || 'Morning';
  const status  = document.getElementById('manual-status')?.value  || 'Present';
  const notes   = document.getElementById('manual-notes')?.value   || '';
  try {
    const res = await API.post('/api/v1/attendance/manual', { student_id: selectedStudentId, session, status, notes });
    if (res.success) {
      showToast(`Manual attendance marked for student.`, 'success');
      selectedStudentId = null;
      document.getElementById('manual-student-search').value = '';
      refreshTodayCount();
    } else {
      showToast(res.message || 'Failed.', 'error');
    }
  } catch(e) { showToast('Error submitting manual attendance.', 'error'); }
}

// Auto-init
if (document.getElementById('history-tbody')) {
  // Set default dates
  const today = new Date().toISOString().slice(0,10);
  const thirtyDaysAgo = new Date(Date.now() - 30*24*60*60*1000).toISOString().slice(0,10);
  const se = document.getElementById('filter-start');
  const ee = document.getElementById('filter-end');
  if (se) se.value = thirtyDaysAgo;
  if (ee) ee.value = today;
  loadHistory();
}
