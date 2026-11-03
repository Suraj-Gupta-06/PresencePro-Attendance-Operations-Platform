/**
 * camera.js — webcam helpers, face overlay rendering, liveness & audio cues.
 */
let stream = null;
let recognitionInterval = null;
let liveLogInterval = null;
let isRecognising = false;
let audioCtx = null;
const FRAME_INTERVAL = 1400; // ms between recognition calls

// Browser user-gesture audio unlocker
function ensureAudioReady() {
  try {
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtxClass) return;
    if (!audioCtx) {
      audioCtx = new AudioCtxClass();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  } catch (err) {
    console.warn("AudioContext init error:", err);
  }
}

// Play modern 2-tone melodic success chime (D5 -> A5)
function playSuccessChime() {
  try {
    ensureAudioReady();
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = 'sine';

    const now = audioCtx.currentTime;
    osc.frequency.setValueAtTime(587.33, now); // D5
    osc.frequency.setValueAtTime(880.00, now + 0.10); // A5

    gain.gain.setValueAtTime(0.35, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.50);

    osc.start(now);
    osc.stop(now + 0.50);
  } catch (err) {
    console.error("Audio playback error:", err);
  }
}

async function startCamera() {
  ensureAudioReady();
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    const video = document.getElementById('camera-feed');
    const placeholder = document.getElementById('camera-placeholder');
    if (video) {
      video.srcObject = stream;
      video.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';

    document.getElementById('start-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'inline-flex';
    showToast('Camera active. Scanning faces…', 'success');

    const resultEl = document.getElementById('recognition-result');
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera active. Detecting faces…</p>';

    startRecognitionLoop();
    startLiveLogPolling();
  } catch (err) {
    showToast('Camera error: ' + err.message, 'error');
    const resultEl = document.getElementById('recognition-result');
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera error. Please allow camera access.</p>';
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  clearInterval(recognitionInterval);
  stopLiveLogPolling();

  const video = document.getElementById('camera-feed');
  const placeholder = document.getElementById('camera-placeholder');
  if (video) {
    video.srcObject = null;
    video.style.display = 'none';
  }
  if (placeholder) placeholder.style.display = 'flex';

  clearOverlay();

  document.getElementById('start-btn').style.display = 'inline-flex';
  document.getElementById('stop-btn').style.display = 'none';
  showToast('Camera stopped.', 'info');

  const resultEl = document.getElementById('recognition-result');
  if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Camera idle</p>';
}

function captureBase64Frame() {
  const video = document.getElementById('camera-feed');
  if (!video || !video.videoWidth) return null;
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.85);
}

function startRecognitionLoop() {
  recognitionInterval = setInterval(async () => {
    if (isRecognising || !stream) return;
    isRecognising = true;
    const frame = captureBase64Frame();
    if (!frame) {
      isRecognising = false;
      return;
    }
    try {
      const res = await API.post('/api/v1/recognize/frame', { frame });
      if (res.success) {
        handleRecognitionResult(res.data);
      } else {
        handleRecognitionError(res.message || 'Recognition failed.');
      }
    } catch (e) {
      // Keep silent on transient glitches
    } finally {
      isRecognising = false;
    }
  }, FRAME_INTERVAL);
}

function handleRecognitionError(message) {
  clearOverlay();
  const resultEl = document.getElementById('recognition-result');
  if (resultEl) resultEl.innerHTML = `<p class="text-muted text-sm">${message}</p>`;
}

function clearOverlay() {
  const canvas = document.getElementById('canvas-overlay');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

function handleRecognitionResult(data) {
  const resultEl = document.getElementById('recognition-result');
  if (!data.faces_detected || !data.recognitions || !data.recognitions.length) {
    clearOverlay();
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Scanning… No face detected.</p>';
    return;
  }

  // Draw real-time bounding box overlay on canvas
  drawOverlay(data.recognitions);

  data.recognitions.forEach(r => {
    if (r.attendance_marked) {
      playSuccessChime();
      showToast(`Attendance Marked: ${r.name}`, 'success');
      addToLiveLog(r);
      refreshTodayCount();
      refreshTodayList();
    } else if (r.spoof_blocked) {
      showToast('Anti-Spoofing: Static photo or screen detected.', 'warning');
    }

    if (resultEl) {
      const isLive = r.liveness ? r.liveness.is_live : true;
      let color = '#38bdf8'; // Blue for unknown
      if (!isLive) color = '#ef4444';
      else if (r.matched && !r.low_confidence) color = '#10d97a';
      else if (r.matched) color = '#fbbf24';

      const livenessLabel = isLive ? 'Live Verified ✓' : 'Spoof Detected ⚠️';

      resultEl.innerHTML = `
        <div style="color:${color};font-size:1.15rem;font-weight:700">${r.name || 'Unknown Face'}</div>
        <div class="text-sm text-muted">${(r.confidence * 100).toFixed(0)}% match • ${livenessLabel}</div>
        ${r.attendance_marked ? '<div class="badge badge-green mt-2">Attendance Marked</div>' : ''}
        ${r.already_marked ? '<div class="badge badge-yellow mt-2">Already Marked (Cooldown)</div>' : ''}
        ${r.spoof_blocked ? '<div class="badge badge-red mt-2">Spoofing Blocked</div>' : ''}
      `;
    }
  });
}

function drawOverlay(recognitions) {
  const canvas = document.getElementById('canvas-overlay');
  const video = document.getElementById('camera-feed');
  if (!canvas || !video || !video.videoWidth || !video.videoHeight) return;

  const rect = video.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  // Set canvas coordinate system to match display dimensions exactly
  canvas.width = rect.width;
  canvas.height = rect.height;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Compute exact scaling accounting for object-fit: cover
  const videoAspect = video.videoWidth / video.videoHeight;
  const containerAspect = rect.width / rect.height;
  let renderW, renderH, offsetX, offsetY;

  if (containerAspect > videoAspect) {
    renderW = rect.width;
    renderH = rect.width / videoAspect;
    offsetX = 0;
    offsetY = (rect.height - renderH) / 2;
  } else {
    renderH = rect.height;
    renderW = rect.height * videoAspect;
    offsetX = (rect.width - renderW) / 2;
    offsetY = 0;
  }

  const scale = renderW / video.videoWidth;

  recognitions.forEach(r => {
    const bb = r.bounding_box;
    if (!bb) return;

    const x = offsetX + (bb.x * scale);
    const y = offsetY + (bb.y * scale);
    const w = bb.width * scale;
    const h = bb.height * scale;

    const isLive = r.liveness ? r.liveness.is_live : true;
    let strokeColor = '#38bdf8'; // Cyan/Blue
    let statusText = 'Scanning';

    if (!isLive) {
      strokeColor = '#ef4444'; // Red
      statusText = 'Spoof Detected';
    } else if (r.matched && !r.low_confidence) {
      strokeColor = '#10d97a'; // Green
      statusText = 'Live Verified';
    } else if (r.matched) {
      strokeColor = '#fbbf24'; // Yellow
      statusText = 'Uncertain';
    }

    // Outer glow effect
    ctx.shadowColor = strokeColor;
    ctx.shadowBlur = 8;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    // Reset shadow
    ctx.shadowBlur = 0;

    // Stylish corner accents
    const corner = Math.min(22, Math.min(w, h) / 3);
    ctx.lineWidth = 5;
    ctx.beginPath();
    // Top-left
    ctx.moveTo(x, y + corner); ctx.lineTo(x, y); ctx.lineTo(x + corner, y);
    // Top-right
    ctx.moveTo(x + w - corner, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + corner);
    // Bottom-right
    ctx.moveTo(x + w, y + h - corner); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - corner, y + h);
    // Bottom-left
    ctx.moveTo(x + corner, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - corner);
    ctx.stroke();

    // High-contrast label banner
    const name = r.name || 'Unknown Face';
    const conf = r.confidence ? `${(r.confidence * 100).toFixed(0)}%` : '';
    const label = conf ? `${name} (${conf}) • ${statusText}` : `${name} • ${statusText}`;

    ctx.font = 'bold 13px Inter, system-ui, sans-serif';
    const textWidth = ctx.measureText(label).width;
    const bannerW = textWidth + 16;
    const bannerH = 24;
    const bannerY = Math.max(0, y - bannerH - 4);

    ctx.fillStyle = strokeColor;
    ctx.fillRect(x, bannerY, bannerW, bannerH);

    ctx.fillStyle = '#0f172a';
    ctx.fillText(label, x + 8, bannerY + 16);
  });
}

function addToLiveLog(r) {
  const list = document.getElementById('att-list');
  if (!list) return;

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
    <div class="att-time">${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</div>
    <span class="badge badge-green">Present</span>
  `;
  list.prepend(item);
  while (list.children.length > 15) list.removeChild(list.lastChild);
}

async function refreshTodayCount() {
  try {
    const res = await API.get('/api/v1/attendance/today');
    if (res.success) {
      const el = document.getElementById('today-count');
      if (el) el.textContent = res.data.present + ' Present';
    }
  } catch (e) {}
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
  } catch (e) {}
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
  } catch (e) {}
})();
