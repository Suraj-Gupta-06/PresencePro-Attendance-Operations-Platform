/**
 * camera.js — webcam helpers used by mark attendance page.
 */
let stream = null;
let recognitionInterval = null;
let liveLogInterval = null;
let isRecognising = false;
const FRAME_INTERVAL = 1500; // ms between recognition calls

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width:1280, height:720 }, audio: false });
    const video = document.getElementById('camera-feed');
    const placeholder = document.getElementById('camera-placeholder');
    if (video) { video.srcObject = stream; video.style.display = 'block'; }
    if (placeholder) placeholder.style.display = 'none';
    document.getElementById('start-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display  = 'inline-flex';
    showToast('Camera started. Recognition active.', 'success');
    const resultEl = document.getElementById('recognition-result');
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera active. Detecting faces…</p>';
    startRecognitionLoop();
    startLiveLogPolling();
  } catch(err) {
    showToast('Camera error: ' + err.message, 'error');
    const resultEl = document.getElementById('recognition-result');
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera error. Please allow access.</p>';
  }
}

function stopCamera() {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  clearInterval(recognitionInterval);
  stopLiveLogPolling();
  const video = document.getElementById('camera-feed');
  const placeholder = document.getElementById('camera-placeholder');
  if (video) { video.srcObject = null; video.style.display = 'none'; }
  if (placeholder) placeholder.style.display = 'flex';
  document.getElementById('start-btn').style.display = 'inline-flex';
  document.getElementById('stop-btn').style.display  = 'none';
  showToast('Camera stopped.', 'info');
  const resultEl = document.getElementById('recognition-result');
  if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera idle</p>';
}

function captureBase64Frame() {
  const video = document.getElementById('camera-feed');
  if (!video || !video.videoWidth) return null;
  const canvas = document.createElement('canvas');
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.85);
}

function startRecognitionLoop() {
  recognitionInterval = setInterval(async () => {
    if (isRecognising || !stream) return;
    isRecognising = true;
    const frame = captureBase64Frame();
    if (!frame) { isRecognising = false; return; }
    try {
      const res = await API.post('/api/v1/recognize/frame', { frame });
      if (res.success) handleRecognitionResult(res.data);
      else handleRecognitionError(res.message || 'Recognition failed.');
    } catch(e) {}
    finally { isRecognising = false; }
  }, FRAME_INTERVAL);
}

function handleRecognitionError(message) {
  const resultEl = document.getElementById('recognition-result');
  if (resultEl) resultEl.innerHTML = `<p class="text-muted text-sm">${message}</p>`;
}

function handleRecognitionResult(data) {
  const resultEl = document.getElementById('recognition-result');
  if (!data.faces_detected) {
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">No face detected.</p>';
    return;
  }

  // Draw overlay
  drawOverlay(data.recognitions);

  data.recognitions.forEach(r => {
    if (r.attendance_marked) {
      showToast(`Attendance marked: ${r.name}`, 'success');
      addToLiveLog(r);
      refreshTodayCount();
      refreshTodayList();
    } else if (r.already_marked) {
      // Silently update display
    }

    if (resultEl) {
      const color = r.matched && !r.low_confidence ? '#10d97a' : r.matched ? '#fbbf24' : '#8b96b0';
      resultEl.innerHTML = `
        <div style="color:${color};font-size:1.1rem;font-weight:700">${r.name || 'Unknown'}</div>
        <div class="text-sm text-muted">${(r.confidence*100).toFixed(0)}% confidence</div>
        ${r.attendance_marked ? '<div class="badge badge-green mt-2">Attendance Marked</div>' : ''}
        ${r.already_marked ? '<div class="badge badge-yellow mt-2">Already Marked</div>' : ''}
      `;
    }
  });
}

function drawOverlay(recognitions) {
  const canvas = document.getElementById('canvas-overlay');
  const video  = document.getElementById('camera-feed');
  if (!canvas || !video) return;

  canvas.width  = video.videoWidth  || canvas.offsetWidth;
  canvas.height = video.videoHeight || canvas.offsetHeight;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scaleX = canvas.offsetWidth  / (video.videoWidth  || 1);
  const scaleY = canvas.offsetHeight / (video.videoHeight || 1);

  recognitions.forEach(r => {
    const bb = r.bounding_box;
    if (!bb) return;
    const x = bb.x * scaleX, y = bb.y * scaleY;
    const w = bb.width * scaleX, h = bb.height * scaleY;

    ctx.strokeStyle = r.matched && !r.low_confidence ? '#10d97a' : r.matched ? '#fbbf24' : '#8b96b0';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);

    // Label
    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = 'bold 14px Inter';
    ctx.fillText(r.name || 'Unknown', x, y - 8);
  });
}

function addToLiveLog(r) {
  const list = document.getElementById('att-list');
  if (!list) return;
  // Remove empty state
  const empty = list.querySelector('.empty-state');
  if (empty) empty.remove();

  const item = document.createElement('div');
  item.className = 'att-list-item';
  item.innerHTML = `
    <div class="avatar">${(r.name || '?')[0]}</div>
    <div style="flex:1">
      <div class="font-semibold text-sm">${r.name}</div>
      <div class="text-xs text-muted">${r.student_code || ''}</div>
    </div>
    <div class="att-time">${new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})}</div>
    <span class="badge badge-green">Present</span>
  `;
  list.prepend(item);
  // Keep max 15 items
  while (list.children.length > 15) list.removeChild(list.lastChild);
}

async function refreshTodayCount() {
  try {
    const res = await API.get('/api/v1/attendance/today');
    if (res.success) {
      const el = document.getElementById('today-count');
      if (el) el.textContent = res.data.present + ' Present';
    }
  } catch(e) {}
}

async function refreshTodayList() {
  try {
    const res = await API.get('/api/v1/attendance/today');
    if (!res.success) return;
    const list = document.getElementById('att-list');
    if (!list) return;
    const recent = res.data.recent || [];
    if (!recent.length) return;
    list.innerHTML = '';
    recent.slice(0, 15).forEach(r => {
      const item = document.createElement('div');
      item.className = 'att-list-item';
      item.innerHTML = `
        <div class="avatar">${(r.student?.name || '?')[0]}</div>
        <div style="flex:1">
          <div class="font-semibold text-sm">${r.student?.name || '—'}</div>
          <div class="text-xs text-muted">${r.student?.student_id || ''}</div>
        </div>
        <div class="att-time">${fmtTime(r.timestamp)}</div>
        ${statusBadge(r.status)}
      `;
      list.appendChild(item);
    });
  } catch(e) {}
}

function startLiveLogPolling() {
  stopLiveLogPolling();
  liveLogInterval = setInterval(() => {
    refreshTodayCount();
    refreshTodayList();
  }, 8000);
}

function stopLiveLogPolling() {
  if (liveLogInterval) {
    clearInterval(liveLogInterval);
    liveLogInterval = null;
  }
}

// Initial load of today's attendance
(async function() {
  try {
    const res = await API.get('/api/v1/attendance/today');
    if (res.success) {
      const el = document.getElementById('today-count');
      if (el) el.textContent = res.data.present + ' Present';
      await refreshTodayList();
    }
  } catch(e) {}
})();
