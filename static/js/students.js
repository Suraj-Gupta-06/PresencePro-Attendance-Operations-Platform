/**
 * students.js — student list, registration wizard, and detail page.
 */

// ─── List Page ────────────────────────────────────────────────────────────────

let currentPage = 1;
const debounceSearch = debounce((v) => { currentPage = 1; loadStudents(); }, 400);

async function loadStudents(page = 1) {
  currentPage = page;
  const search = document.getElementById('search-input')?.value || '';
  const dept   = document.getElementById('dept-filter')?.value  || '';
  const active = document.getElementById('active-filter')?.value || '';

  const params = new URLSearchParams({ page, per_page: 50 });
  if (search) params.append('search', search);
  if (dept)   params.append('department', dept);
  if (active) params.append('is_active', active);

  const tbody = document.getElementById('students-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:40px"><div class="spinner" style="margin:0 auto 12px"></div>Loading records…</td></tr>`;

  try {
    const res = await API.get('/api/v1/students/?' + params.toString());
    if (!res.success) return;
    const students = res.data.items;
    const pg       = res.data.pagination;

    const countEl = document.getElementById('student-count');
    if (countEl) countEl.textContent = pg.total + ' students';

    if (tbody) {
      if (!students.length) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><h3>No students found</h3><p>Adjust filters or register a new student.</p></div></td></tr>`;
      } else {
        tbody.innerHTML = students.map(s => {
          const initials = s.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase();
          const pct = s.attendance_count !== undefined ? '—' : '—';
          return `<tr>
            <td>
              <div class="flex items-center gap-3">
                ${s.profile_image
                  ? `<div class="avatar"><img src="/${s.profile_image}" onerror="this.parentNode.textContent='${initials}'"></div>`
                  : `<div class="avatar">${initials}</div>`}
                <div>
                  <div class="font-semibold text-sm"><a href="/students/${s.id}" style="color:var(--text-primary)">${s.name}</a></div>
                  <div class="text-xs text-muted">${s.email}</div>
                </div>
              </div>
            </td>
            <td class="text-sm">${s.student_id}</td>
            <td class="text-sm">${s.department || '—'}</td>
            <td class="text-sm">${s.email}</td>
            <td class="text-sm">—</td>
            <td>${s.is_active ? '<span class="badge badge-green">Active</span>' : '<span class="badge badge-red">Inactive</span>'}</td>
            <td>
              <div class="flex gap-2">
                <a href="/students/${s.id}" class="btn btn-secondary btn-sm">
                  <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  View
                </a>
                <button class="btn btn-danger btn-sm" onclick="deleteStudent(${s.id},'${s.name}')" aria-label="Deactivate student">
                  <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M3 6h18" />
                    <path d="M8 6V4h8v2" />
                    <path d="M19 6l-1 14H6L5 6" />
                    <path d="M10 11v6" />
                    <path d="M14 11v6" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>`;
        }).join('');
      }
    }
    renderPagination('pagination-area', pg, 'loadStudents');
    populateDeptFilter(students);
  } catch(e) { showToast('Failed to load students.', 'error'); }
}

function populateDeptFilter(students) {
  const sel = document.getElementById('dept-filter');
  if (!sel || sel.options.length > 1) return;
  const depts = [...new Set(students.map(s => s.department).filter(Boolean))].sort();
  depts.forEach(d => { const o = document.createElement('option'); o.value = d; o.textContent = d; sel.appendChild(o); });
}

async function deleteStudent(id, name) {
  if (!confirm(`Deactivate student "${name}"?`)) return;
  try {
    const res = await API.delete(`/api/v1/students/${id}`);
    if (res.success) { showToast('Student deactivated.', 'success'); loadStudents(currentPage); }
    else showToast(res.message, 'error');
  } catch(e) { showToast('Error.', 'error'); }
}

// ─── Registration Wizard ──────────────────────────────────────────────────────

let capturedImages = [];
let regCamStream  = null;

function goToStep1() {
  document.getElementById('step-1').style.display = '';
  document.getElementById('step-2').style.display = 'none';
  document.getElementById('step-3').style.display = 'none';
  document.getElementById('step1-num').className = 'step-num active';
  document.getElementById('step2-num').className = 'step-num';
  document.getElementById('step3-num').className = 'step-num';
  stopRegCamera();
}

function goToStep2() {
  const required = ['student_id','name','email'];
  for (const id of required) {
    if (!document.getElementById(id)?.value.trim()) {
      showToast(`Please fill in: ${id.replace('_',' ')}`, 'error'); return;
    }
  }
  document.getElementById('step-1').style.display = 'none';
  document.getElementById('step-2').style.display = '';
  document.getElementById('step-3').style.display = 'none';
  document.getElementById('step1-num').className = 'step-num done';
  document.getElementById('step2-num').className = 'step-num active';
  document.getElementById('step3-num').className = 'step-num';
  document.getElementById('line1').className = 'step-line done';
}

function goToStep3() {
  if (capturedImages.length < 1) { showToast('Capture at least 1 face image.', 'error'); return; }
  document.getElementById('step-1').style.display = 'none';
  document.getElementById('step-2').style.display = 'none';
  document.getElementById('step-3').style.display = '';
  document.getElementById('step2-num').className = 'step-num done';
  document.getElementById('step3-num').className = 'step-num active';
  document.getElementById('line2').className = 'step-line done';
  stopRegCamera();

  const d = document.getElementById('confirm-details');
  if (d) d.innerHTML = `
    <div class="form-row"><div><strong>Student ID</strong><p>${document.getElementById('student_id')?.value}</p></div><div><strong>Name</strong><p>${document.getElementById('name')?.value}</p></div></div>
    <div class="form-row mt-2"><div><strong>Email</strong><p>${document.getElementById('email')?.value}</p></div><div><strong>Department</strong><p>${document.getElementById('department')?.value || '—'}</p></div></div>
    <p class="mt-4 text-sm text-muted"><strong>${capturedImages.length}</strong> face images captured and ready.</p>
  `;
}

async function startRegCamera() {
  try {
    regCamStream = await navigator.mediaDevices.getUserMedia({ video: { width:640, height:480 } });
    const video = document.getElementById('reg-video');
    document.getElementById('reg-placeholder').style.display = 'none';
    video.srcObject = regCamStream; video.style.display = 'block';
    document.getElementById('capture-btn').disabled = false;
    document.getElementById('cam-start-btn').disabled = true;
  } catch(e) { showToast('Camera access denied: ' + e.message, 'error'); }
}

function stopRegCamera() {
  if (regCamStream) { regCamStream.getTracks().forEach(t => t.stop()); regCamStream = null; }
  const video = document.getElementById('reg-video');
  if (video) { video.srcObject = null; video.style.display = 'none'; }
  const placeholder = document.getElementById('reg-placeholder');
  if (placeholder) placeholder.style.display = 'flex';
  const captBtn = document.getElementById('capture-btn');
  if (captBtn) captBtn.disabled = true;
  const startBtn = document.getElementById('cam-start-btn');
  if (startBtn) startBtn.disabled = false;
}

function captureFrame() {
  const video = document.getElementById('reg-video');
  if (!video || !video.videoWidth) return;
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
  capturedImages.push(dataUrl);
  updateCaptureUI();
}

function handleUpload(event) {
  const files = event.target.files;
  [...files].forEach(file => {
    const reader = new FileReader();
    reader.onload = e => { capturedImages.push(e.target.result); updateCaptureUI(); };
    reader.readAsDataURL(file);
  });
}

function updateCaptureUI() {
  const count = capturedImages.length;
  const countEl = document.getElementById('capture-count');
  if (countEl) countEl.textContent = count;
  const grid = document.getElementById('capture-grid');
  if (grid) {
    grid.innerHTML = capturedImages.map((src, i) => `
      <div class="capture-thumb filled">
        <img src="${src}" alt="Face ${i+1}">
        <button type="button" style="position:absolute;top:4px;right:4px;cursor:pointer;background:rgba(0,0,0,0.6);border:0;border-radius:4px;padding:2px 5px" onclick="removeCapture(${i})" aria-label="Remove image">
          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true" style="width:12px;height:12px">
            <path d="M6 6l12 12" />
            <path d="M18 6l-12 12" />
          </svg>
        </button>
      </div>
    `).join('') +
    Array(Math.max(0, 10 - count)).fill(0).map(() => `<div class="capture-thumb empty"></div>`).join('');
  }
  const nextBtn = document.getElementById('step2-next');
  if (nextBtn) nextBtn.disabled = count < 1;
  const alertEl = document.getElementById('capture-alert');
  const alertMsg = document.getElementById('capture-alert-msg');
  if (alertEl && alertMsg) {
    if (count < 5) { alertEl.style.display = 'flex'; alertMsg.textContent = `Tip: capture ${5 - count} more images for better accuracy.`; }
    else { alertEl.style.display = 'none'; }
  }
}

function removeCapture(idx) { capturedImages.splice(idx, 1); updateCaptureUI(); }
function clearCaptures() { capturedImages = []; updateCaptureUI(); }

async function submitRegistration() {
  const btn = document.getElementById('submit-btn');
  const txt = document.getElementById('submit-text');
  const sp  = document.getElementById('submit-spinner');
  const alertEl = document.getElementById('reg-alert');
  btn.disabled = true; txt.textContent = 'Registering…'; sp.style.display = 'inline-block';

  const fd = new FormData();
  fd.append('student_id', document.getElementById('student_id')?.value.trim());
  fd.append('name',       document.getElementById('name')?.value.trim());
  fd.append('email',      document.getElementById('email')?.value.trim());
  fd.append('phone',      document.getElementById('phone')?.value.trim());
  fd.append('department', document.getElementById('department')?.value.trim());
  fd.append('class_id',   document.getElementById('class_id')?.value);
  fd.append('roll_no',    document.getElementById('roll_no')?.value.trim());
  fd.append('dob',        document.getElementById('dob')?.value);
  fd.append('gender',     document.getElementById('gender')?.value);

  // Convert base64 images to blobs
  capturedImages.forEach((dataUrl, i) => {
    const byteStr = atob(dataUrl.split(',')[1]);
    const ab = new ArrayBuffer(byteStr.length);
    const ia = new Uint8Array(ab);
    for (let j=0;j<byteStr.length;j++) ia[j] = byteStr.charCodeAt(j);
    const blob = new Blob([ab], { type: 'image/jpeg' });
    fd.append('images', blob, `face_${i}.jpg`);
  });

  try {
    const res = await API.postForm('/api/v1/students/', fd);
    if (res.success) {
      showToast('Student registered successfully!', 'success');
      if (alertEl) alertEl.innerHTML = `<div class="alert alert-success"><svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 13l4 4L19 7" /></svg> Student <strong>${res.data.name}</strong> registered. <a href="/students/${res.data.id}">View profile</a></div>`;
      setTimeout(() => window.location.href = '/students', 2000);
    } else {
      if (alertEl) alertEl.innerHTML = `<div class="alert alert-error"><svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12" /><path d="M18 6l-12 12" /></svg> ${res.message}</div>`;
    }
  } catch(e) {
    if (alertEl) alertEl.innerHTML = `<div class="alert alert-error"><svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12" /><path d="M18 6l-12 12" /></svg> Registration failed. Please try again.</div>`;
  } finally {
    btn.disabled = false;
    txt.innerHTML = '<svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 13l4 4L19 7" /></svg> Register Student';
    sp.style.display = 'none';
  }
}

// Load classes for registration
async function loadClasses() {
  const sel = document.getElementById('class_id');
  if (!sel) return;
  try {
    const res = await API.get('/api/v1/students/classes');
    if (res.success) {
      res.data.forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; sel.appendChild(o); });
    }
  } catch(e) {}
}

// ─── Student Detail Page ──────────────────────────────────────────────────────

async function loadStudentDetail() {
  if (typeof STUDENT_ID === 'undefined') return;
  try {
    const [studRes, attRes] = await Promise.all([
      API.get(`/api/v1/students/${STUDENT_ID}`),
      API.get(`/api/v1/attendance/student/${STUDENT_ID}`)
    ]);
    if (!studRes.success) return;
    const s = studRes.data;
    const content = document.getElementById('student-content');
    const stats = attRes.success ? attRes.data.summary : {};
    const records = attRes.success ? attRes.data.records.slice(0,10) : [];

    content.innerHTML = `
      <div class="profile-header">
        <div class="avatar avatar-xl">${s.name[0]}</div>
        <div class="profile-info">
          <h2>${s.name}</h2>
          <p class="text-secondary">${s.student_id} · ${s.department || 'No Department'}</p>
          <div class="flex gap-2 mt-2">
            <span class="badge badge-blue">${s.gender || '—'}</span>
            ${s.is_active ? '<span class="badge badge-green">Active</span>' : '<span class="badge badge-red">Inactive</span>'}
          </div>
        </div>
        <div style="margin-left:auto;text-align:right">
          <div style="font-size:2.5rem;font-weight:800;color:var(--accent-blue)">${stats.percentage || 0}%</div>
          <div class="text-muted text-sm">Attendance Rate</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <h3 class="mb-4">Student Info</h3>
          ${[['Email',s.email],['Phone',s.phone||'—'],['Roll No',s.roll_no||'—'],['DoB',s.dob||'—'],['Class',s.class?.name||'—']].map(([k,v])=>`<div class="flex justify-between" style="padding:8px 0;border-bottom:1px solid var(--border)"><span class="text-muted text-sm">${k}</span><span class="text-sm">${v}</span></div>`).join('')}
        </div>
        <div class="card">
          <h3 class="mb-4">Attendance Summary</h3>
          <div class="stats-grid" style="grid-template-columns:1fr 1fr;gap:12px">
            <div class="stat-card" style="padding:14px"><div><div class="stat-value text-green">${stats.present_days||0}</div><div class="stat-label">Present</div></div></div>
            <div class="stat-card" style="padding:14px"><div><div class="stat-value text-red">${stats.absent_days||0}</div><div class="stat-label">Absent</div></div></div>
            <div class="stat-card" style="padding:14px"><div><div class="stat-value">${stats.total_days||0}</div><div class="stat-label">Total Days</div></div></div>
            <div class="stat-card" style="padding:14px"><div><div class="stat-value text-blue">${stats.percentage||0}%</div><div class="stat-label">Rate</div></div></div>
          </div>
        </div>
      </div>
      <div class="table-wrapper mt-6">
        <div class="table-header"><h3>Recent Attendance</h3></div>
        <table><thead><tr><th>Date</th><th>Session</th><th>Method</th><th>Confidence</th><th>Status</th></tr></thead>
        <tbody>
          ${records.map(r=>`<tr><td>${fmtDate(r.date)}</td><td>${r.session||'—'}</td><td>${methodBadge(r.method)}</td><td>${r.confidence?(r.confidence*100).toFixed(0)+'%':'—'}</td><td>${statusBadge(r.status)}</td></tr>`).join('')||'<tr><td colspan="5" class="text-center text-muted" style="padding:32px">No records found</td></tr>'}
        </tbody></table>
      </div>
    `;
  } catch(e) { showToast('Failed to load student.', 'error'); }
}

// Auto-init
if (document.getElementById('students-tbody'))   { loadStudents(); }
if (document.getElementById('class_id'))          { loadClasses(); }
if (document.getElementById('student-content'))  { loadStudentDetail(); }
