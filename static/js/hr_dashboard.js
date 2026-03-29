/**
 * HR Analytics System — HR Dashboard JS
 * Fetches data from Flask API endpoints and renders Chart.js charts
 */

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { labels: { color: '#8b949e', font: { family: 'DM Sans' } } }
  },
  scales: {
    x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
    y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } }
  }
};

async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    return await r.json();
  } catch (e) {
    console.warn('API fetch failed:', url, e);
    return [];
  }
}

// ── Department Chart ──
async function loadDeptChart() {
  const data = await fetchJSON('/api/attrition_by_dept');
  if (!data.length) return;
  const ctx = document.getElementById('deptChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.Department),
      datasets: [
        {
          label: 'Total',
          data: data.map(d => d.total),
          backgroundColor: 'rgba(59,130,246,.5)',
          borderColor: '#3b82f6', borderWidth: 1, borderRadius: 4
        },
        {
          label: 'Attrited',
          data: data.map(d => d.attrited),
          backgroundColor: 'rgba(239,68,68,.6)',
          borderColor: '#ef4444', borderWidth: 1, borderRadius: 4
        }
      ]
    },
    options: {
      ...CHART_OPTS,
      plugins: { ...CHART_OPTS.plugins, tooltip: { callbacks: {
        afterLabel: (ctx) => {
          const d = data[ctx.dataIndex];
          return `Rate: ${(d.attrited/d.total*100).toFixed(1)}%`;
        }
      }}}
    }
  });
}

// ── Age Group Chart ──
async function loadAgeChart() {
  const data = await fetchJSON('/api/attrition_by_age');
  if (!data.length) return;
  const ctx = document.getElementById('ageChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.AgeGroup),
      datasets: [{
        label: 'Attrited',
        data: data.map(d => d.Attrited),
        backgroundColor: [
          'rgba(239,68,68,.7)', 'rgba(245,158,11,.7)',
          'rgba(59,130,246,.7)', 'rgba(34,197,94,.7)', 'rgba(168,85,247,.7)'
        ],
        borderRadius: 4
      }]
    },
    options: { ...CHART_OPTS, plugins: { ...CHART_OPTS.plugins, legend: { display: false } } }
  });
}

// ── Overtime Chart ──
async function loadOvertimeChart() {
  const data = await fetchJSON('/api/attrition_by_overtime');
  if (!data.length) return;
  const ctx = document.getElementById('otChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => `OverTime: ${d.OverTime} (${d.AttritionRate}%)`),
      datasets: [{
        data: data.map(d => d.Attrited),
        backgroundColor: ['rgba(239,68,68,.7)', 'rgba(59,130,246,.7)'],
        borderColor: ['#ef4444', '#3b82f6'], borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: '#8b949e' } } }
    }
  });
}

// ── Risk Distribution Chart ──
async function loadRiskChart() {
  const data = await fetchJSON('/api/risk_distribution');
  if (!data.length) return;
  const ctx = document.getElementById('riskChart');
  if (!ctx) return;
  const colorMap = { High: 'rgba(239,68,68,.7)', Medium: 'rgba(245,158,11,.7)', Low: 'rgba(34,197,94,.7)' };
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: data.map(d => d.risk_level),
      datasets: [{
        data: data.map(d => d.count),
        backgroundColor: data.map(d => colorMap[d.risk_level] || 'rgba(99,102,241,.7)'),
        borderColor: '#161b22', borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: '#8b949e' } } }
    }
  });
}

// ── Table Filter ──
function setupTableFilter() {
  const search = document.getElementById('empSearch');
  const riskSel = document.getElementById('riskFilter');
  const rows = Array.from(document.querySelectorAll('#empTable tbody tr'));

  function filter() {
    const q = (search?.value || '').toLowerCase();
    const r = (riskSel?.value || '').toLowerCase();
    rows.forEach(row => {
      const name = (row.dataset.name || '').toLowerCase();
      const dept = (row.dataset.dept || '').toLowerCase();
      const risk = (row.dataset.risk || '').toLowerCase();
      const textMatch = !q || name.includes(q) || dept.includes(q);
      const riskMatch = !r || risk === r.toLowerCase();
      row.style.display = (textMatch && riskMatch) ? '' : 'none';
    });
  }
  search?.addEventListener('input', filter);
  riskSel?.addEventListener('change', filter);
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  loadDeptChart();
  loadAgeChart();
  loadOvertimeChart();
  loadRiskChart();
  setupTableFilter();
});
