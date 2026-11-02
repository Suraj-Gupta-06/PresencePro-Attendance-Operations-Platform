/**
 * camera.js — webcam helpers, face overlay rendering, liveness & audio cues.
 */
let stream = null;
let recognitionInterval = null;
let liveLogInterval = null;
let isRecognising = false;
const FRAME_INTERVAL = 1400; // ms between recognition calls

function playSuccessChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.08); // A5
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.32);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.32);
  } catch (err) {}
}

async function startCamera() {
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
      // Keep silent on transient network glitches
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
  if (!data.faces_detected || !data.recognitions.length) {
    clearOverlay();
    if (resultEl) resultEl.innerHTML = '<p class="text-muted text-sm">Scanning… No face detected.</p>';
    return;
  }

  // Draw real-time bounding box overlay
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
      const color = !isLive ? '#ef4444' : (r.matched && !r.low_confidence ? '#10d97a' : r.matched ? '#fbbf24' : '#60a5fa');
      const livenessLabel = isLive ? 'Live Verified ✓' : 'Spoof Detected ⚠️';

      resultEl.innerHTML = `
        <div style="color:${color};font-size:1.15rem;font-weight:700">${r.name || 'Unknown'}</div>
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
  if (!canvas || !video || !video.videoWidth) return;

  // Set internal resolution to match raw video frames
  if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  }

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  recognitions.forEach(r => {
    const bb = r.bounding_box;
    if (!bb) return;

    const x = bb.x;
    const y = bb.y;
    const w = bb.width;
    const h = bb.height;

    const isLive = r.liveness ? r.liveness.is_live : true;
    let strokeColor = '#60a5fa'; // Blue for unknown
    if (!isLive) {
      strokeColor = '#ef4444'; // Red for spoofing
    } else if (r.matched && !r.low_confidence) {
      strokeColor = '#10d97a'; // Green for high confidence match
    } else if (r.matched) {
      strokeColor = '#fbbf24'; // Yellow for low confidence
    }

    // Draw bounding box
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.strokeRect(x, y, w, h);

    // Label banner
    const label = `${r.name || 'Unknown'} (${(r.confidence * 100).toFixed(0)}%)`;
    ctx.font = 'bold 15px Inter, sans-serif';
    const textWidth = ctx.measureText(label).width;

    ctx.fillStyle = strokeColor;
    ctx.beginPath();
    ctx.roundRect(x, Math.max(0, y - 28), textWidth + 16, 26, 4);
    ctx.fill();

    ctx.fillStyle = '#0f172a';
    ctx.fillText(label, x + 8, Math.max(18, y - 10));
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
