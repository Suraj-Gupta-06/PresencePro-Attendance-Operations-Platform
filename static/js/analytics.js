/**
 * analytics.js — charts and reports page.
 */
let dailyChart, deptBarChart, sessionPieChart;

const CHART_COLORS = ['#4f8ef7','#8b5cf6','#10d97a','#f97316','#fbbf24','#ef4444'];

function buildChart(id, type, labels, data, label, color) {
  const ctx = document.getElementById(id);
  if (!ctx) return null;
  return new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: Array.isArray(color) ? color : (type==='line' ? color+'22' : color+'99'),
        borderColor: Array.isArray(color) ? color : color,
        borderWidth: 2,
        fill: type === 'line',
        tension: 0.4,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: {
          display: type !== 'line',
          labels: { color: '#8b96b0', font: { family: 'Inter' }, padding: 16 }
        }
      },
      scales: type !== 'doughnut' && type !== 'pie' ? {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b96b0', maxTicksLimit: 10 } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b96b0' }, min: 0 }
      } : undefined
    }
  });
}

async function loadAnalytics() {
  const start = document.getElementById('analytics-start')?.value;
  const end   = document.getElementById('analytics-end')?.value;
  const params = new URLSearchParams();
  if (start) params.append('start_date', start);
  if (end)   params.append('end_date', end);

  try {
    const [overviewRes, absenteesRes] = await Promise.all([
      API.get('/api/v1/analytics/overview?' + params.toString()),
      API.get('/api/v1/analytics/absentees?limit=8'),
    ]);

    if (overviewRes.success) {
      const d = overviewRes.data;
      document.getElementById('a-total').textContent = d.total_students;
      document.getElementById('a-avg').textContent   = d.avg_attendance_percentage + '%';
      document.getElementById('a-days').textContent  = d.attendance_by_day.length;

      // Daily chart
      if (dailyChart) dailyChart.destroy();
      dailyChart = buildChart(
        'daily-chart', 'line',
        d.attendance_by_day.map(x => x.date.slice(5)),
        d.attendance_by_day.map(x => x.percentage),
        'Attendance %', '#4f8ef7'
      );

      // Dept bar chart
      if (deptBarChart) deptBarChart.destroy();
      deptBarChart = buildChart(
        'dept-bar-chart', 'bar',
        d.department_stats.map(x => x.department),
        d.department_stats.map(x => x.percentage),
        'Attendance %', CHART_COLORS
      );

      // Student analytics table
      buildStudentTable(d);
    }

    if (absenteesRes.success) {
      document.getElementById('a-absentees').textContent = absenteesRes.data.filter(s => s.percentage < 75).length;
      const list = document.getElementById('absentees-list');
      if (list) {
        list.innerHTML = absenteesRes.data.map(s => `
          <div class="flex items-center gap-3" style="padding:10px;border-bottom:1px solid var(--border)">
            <div class="avatar">${s.student.name[0]}</div>
            <div style="flex:1">
              <div class="text-sm font-semibold">${s.student.name}</div>
              <div class="text-xs text-muted">${s.student.student_id}</div>
            </div>
            <div>
              <div class="font-bold ${s.percentage < 75 ? 'text-red' : 'text-yellow'}">${s.percentage}%</div>
              <div class="text-xs text-muted">${s.present_days} days</div>
            </div>
          </div>
        `).join('');
      }
    }

    // Session breakdown from attendance
    buildSessionChart();

  } catch(e) { showToast('Failed to load analytics.', 'error'); }
}

async function buildSessionChart() {
  try {
    const res = await API.get('/api/v1/attendance/?per_page=200');
    if (!res.success) return;
    const counts = { Morning: 0, Afternoon: 0, Evening: 0 };
    (res.data.items || []).forEach(r => { if (counts[r.session] !== undefined) counts[r.session]++; });
    if (sessionPieChart) sessionPieChart.destroy();
    const ctx = document.getElementById('session-pie-chart');
    if (!ctx) return;
    sessionPieChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(counts),
        datasets: [{ data: Object.values(counts), backgroundColor: ['#4f8ef7','#8b5cf6','#10d97a'], borderColor: 'transparent', hoverOffset: 8 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: '#8b96b0', padding: 16 } } }
      }
    });
  } catch(e) {}
}

let allStudents = [];

function buildStudentTable(d) {
  // We'll pull students and merge with present counts from overview
  loadStudentTable();
}

async function loadStudentTable(search = '') {
  try {
    const res = await API.get(`/api/v1/students/?per_page=100&search=${encodeURIComponent(search)}`);
    if (!res.success) return;
    allStudents = res.data.items;
    renderStudentTable(allStudents);
  } catch(e) {}
}

function renderStudentTable(students) {
  const tbody = document.getElementById('student-analytics-tbody');
  if (!tbody) return;
  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding:32px">No students found</td></tr>`;
    return;
  }
  tbody.innerHTML = students.map(s => {
    return `<tr>
      <td>
        <div class="flex items-center gap-2">
          <div class="avatar">${s.name[0]}</div>
          <a href="/students/${s.id}" style="color:var(--text-primary)" class="font-semibold text-sm">${s.name}</a>
        </div>
      </td>
      <td class="text-sm">${s.student_id}</td>
      <td class="text-sm">${s.department || '—'}</td>
      <td class="text-sm">Not available</td>
      <td class="text-sm">Not available</td>
      <td><a href="/students/${s.id}" class="btn btn-secondary btn-sm">View</a></td>
    </tr>`;
  }).join('');
}

const searchStudentAnalytics = debounce((v) => loadStudentTable(v), 400);

function exportCSVReport() {
  showToast('Generating CSV export…', 'info');
  const rows = [...document.querySelectorAll('#student-analytics-tbody tr')];
  if (!rows.length) { showToast('No records available.', 'error'); return; }
  const headers = ['Student','Student ID','Department','Present Days','Attendance %'];
  const csv = [headers.join(','), ...rows.map(r => {
    const cells = [...r.querySelectorAll('td')].slice(0,5).map(td => `"${td.textContent.trim()}"`);
    return cells.join(',');
  })].join('\n');
  const blob = new Blob([csv], { type:'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `analytics_${new Date().toISOString().slice(0,10)}.csv`;
  a.click(); URL.revokeObjectURL(url);
}

// Init
(function() {
  // Default date range: last 30 days
  const today = new Date().toISOString().slice(0,10);
  const ago = new Date(Date.now() - 30*24*60*60*1000).toISOString().slice(0,10);
  const se = document.getElementById('analytics-start');
  const ee = document.getElementById('analytics-end');
  if (se) se.value = ago;
  if (ee) ee.value = today;
  loadAnalytics();
})();
