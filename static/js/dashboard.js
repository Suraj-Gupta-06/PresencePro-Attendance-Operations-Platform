/**
 * dashboard.js — loads stats, charts, and recent attendance for dashboard page.
 */

// Set hero date/greeting
(function() {
  const el = document.getElementById('hero-date');
  const gr = document.getElementById('hero-greeting');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
  const h = now.getHours();
  gr.textContent = h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening';
})();

let trendChart, deptChart;

const CHART_DEFAULTS = {
  color: { grid: 'rgba(255,255,255,0.05)', text: '#8b96b0' },
  font: { family: 'Inter' },
};

function buildTrendChart(labels, data) {
  const ctx = document.getElementById('trend-chart');
  if (!ctx) return;
  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Attendance %',
        data,
        borderColor: '#4f8ef7',
        backgroundColor: 'rgba(79,142,247,0.08)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#4f8ef7',
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: CHART_DEFAULTS.color.grid }, ticks: { color: CHART_DEFAULTS.color.text, maxTicksLimit: 8 } },
        y: { grid: { color: CHART_DEFAULTS.color.grid }, ticks: { color: CHART_DEFAULTS.color.text }, min: 0, max: 100, }
      }
    }
  });
}

function buildDeptChart(labels, data) {
  const ctx = document.getElementById('dept-chart');
  if (!ctx) return;
  if (deptChart) deptChart.destroy();
  const colors = ['#4f8ef7','#8b5cf6','#10d97a','#f97316','#fbbf24','#ef4444'];
  deptChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: 'transparent',
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#8b96b0', padding: 16, font: { size: 12 } } }
      }
    }
  });
}

async function loadDashboard() {
  // Today stats
  try {
    const res = await API.get('/api/v1/attendance/today');
    if (res.success) {
      const d = res.data;
      document.getElementById('stat-total').textContent   = d.total_students;
      document.getElementById('stat-present').textContent = d.present;
      document.getElementById('stat-absent').textContent  = d.absent;
      document.getElementById('stat-pct').textContent     = d.percentage + '%';

      // Recent table
      const tbody = document.getElementById('recent-tbody');
      if (d.recent && d.recent.length > 0) {
        tbody.innerHTML = d.recent.map(r => `
          <tr>
            <td>
              <div class="flex items-center gap-2">
                <div class="avatar">${(r.student?.name || '?')[0].toUpperCase()}</div>
                <div>
                  <div class="font-semibold text-sm">${r.student?.name || '—'}</div>
                  <div class="text-xs text-muted">${r.student?.student_id || ''}</div>
                </div>
              </div>
            </td>
            <td class="text-sm">${fmtTime(r.timestamp)}</td>
            <td><span class="badge badge-gray">${r.session || '—'}</span></td>
            <td class="text-sm">${r.confidence ? (r.confidence * 100).toFixed(0) + '%' : '—'}</td>
            <td>${methodBadge(r.method)}</td>
            <td>${statusBadge(r.status)}</td>
          </tr>
        `).join('');
      } else {
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><h3>No attendance for today</h3></div></td></tr>`;
      }
    }
  } catch(e) { console.error(e); }

  // Analytics overview for charts
  try {
    const res = await API.get('/api/v1/analytics/overview');
    if (res.success) {
      const d = res.data;
      // Trend chart
      const labels = d.attendance_by_day.map(x => x.date.slice(5));
      const vals   = d.attendance_by_day.map(x => x.percentage);
      buildTrendChart(labels, vals);

      // Dept chart
      const deptLabels = d.department_stats.map(x => x.department);
      const deptVals   = d.department_stats.map(x => x.percentage);
      buildDeptChart(deptLabels, deptVals);
    }
  } catch(e) { console.error(e); }
}

loadDashboard();
