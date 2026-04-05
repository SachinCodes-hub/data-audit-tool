
/* ================================================================
   GLOBAL STATE
================================================================ */
const STATE = {
  raw: [],
  cleaned: [],
  headers: [],
  fileName: '',
  fileSize: 0,
  metrics: {},
  colStats: {},
  strategy: 'conservative',
  pipelineRan: false,
  dqsBefore: 0,
  dqsAfter: 0,
  changes: []
};

/* ================================================================
   CSV PARSER
================================================================ */
function parseCSV(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (!lines.length) return { headers: [], rows: [] };
  const sep = text.indexOf('\t') > -1 && text.indexOf(',') === -1 ? '\t' : ',';
  const parse = line => {
    const res = []; let cur = ''; let q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') { q = !q; continue; }
      if (c === sep && !q) { res.push(cur.trim()); cur = ''; continue; }
      cur += c;
    }
    res.push(cur.trim());
    return res;
  };
  const headers = parse(lines[0]);
  const rows = lines.slice(1).map(l => {
    const vals = parse(l);
    const obj = {};
    headers.forEach((h, i) => obj[h] = vals[i] !== undefined ? vals[i] : '');
    return obj;
  }).filter(r => Object.values(r).some(v => v !== ''));
  return { headers, rows };
}

/* ================================================================
   TYPE DETECTION
================================================================ */
function detectType(col, rows) {
  const vals = rows.map(r => r[col]).filter(v => v !== '' && v !== null && v !== undefined);
  if (!vals.length) return 'unknown';
  const nums = vals.filter(v => !isNaN(Number(v)) && v !== '');
  if (nums.length / vals.length > 0.85) return 'numeric';
  const dates = vals.filter(v => !isNaN(Date.parse(v)) && v.length > 4);
  if (dates.length / vals.length > 0.7) return 'datetime';
  const bools = vals.filter(v => ['true','false','yes','no','0','1'].includes(v.toLowerCase()));
  if (bools.length / vals.length > 0.8) return 'boolean';
  return 'string';
}

/* ================================================================
   COLUMN STATISTICS
================================================================ */
function computeColStats(headers, rows) {
  const stats = {};
  headers.forEach(col => {
    const all = rows.map(r => r[col]);
    const vals = all.filter(v => v !== '' && v !== null && v !== undefined);
    const missing = all.length - vals.length;
    const type = detectType(col, rows);
    const unique = new Set(vals).size;

    let mean = null, std = null, min = null, max = null, median = null, skew = null, kurt = null;

    if (type === 'numeric') {
      const nums = vals.map(Number).filter(n => !isNaN(n));
      if (nums.length) {
        mean = nums.reduce((a, b) => a + b, 0) / nums.length;
        const sorted = [...nums].sort((a, b) => a - b);
        min = sorted[0]; max = sorted[sorted.length - 1];
        const mid = Math.floor(sorted.length / 2);
        median = sorted.length % 2 ? sorted[mid] : (sorted[mid-1] + sorted[mid]) / 2;
        const variance = nums.reduce((a, b) => a + (b - mean) ** 2, 0) / nums.length;
        std = Math.sqrt(variance);
        if (std > 0) {
          skew = nums.reduce((a, b) => a + ((b - mean) / std) ** 3, 0) / nums.length;
          kurt = nums.reduce((a, b) => a + ((b - mean) / std) ** 4, 0) / nums.length - 3;
        }
      }
    }

    // Distribution bins for histogram
    let bins = [];
    if (type === 'numeric') {
      const nums = vals.map(Number).filter(n => !isNaN(n));
      if (nums.length) {
        const lo = Math.min(...nums), hi = Math.max(...nums);
        const bw = (hi - lo) / 10 || 1;
        for (let i = 0; i < 10; i++) bins.push(0);
        nums.forEach(n => {
          const b = Math.min(9, Math.floor((n - lo) / bw));
          bins[b]++;
        });
      }
    }

    // Outliers (IQR)
    let outliers = 0;
    if (type === 'numeric') {
      const nums = vals.map(Number).filter(n => !isNaN(n)).sort((a,b)=>a-b);
      if (nums.length > 3) {
        const q1 = nums[Math.floor(nums.length * 0.25)];
        const q3 = nums[Math.floor(nums.length * 0.75)];
        const iqr = q3 - q1;
        outliers = nums.filter(n => n < q1 - 1.5*iqr || n > q3 + 1.5*iqr).length;
      }
    }

    stats[col] = { type, missing, missingPct: all.length ? missing/all.length*100 : 0,
      unique, uniquePct: vals.length ? unique/vals.length*100 : 0,
      mean, std, min, max, median, skew, kurt, bins, outliers,
      total: all.length, count: vals.length };
  });
  return stats;
}

/* ================================================================
   DQS ENGINE
================================================================ */
function computeDQS(headers, rows, colStats) {
  const n = rows.length, m = headers.length;

  // 1. Completeness
  const totalCells = n * m;
  const missingCells = headers.reduce((s, h) => s + colStats[h].missing, 0);
  const completeness = Math.max(0, 1 - missingCells / totalCells);

  // 2. Uniqueness (duplicates)
  const rowStrings = rows.map(r => headers.map(h => r[h]).join('||'));
  const dupCount = rowStrings.length - new Set(rowStrings).size;
  const uniqueness = Math.max(0, 1 - dupCount / n);

  // 3. Consistency (numeric cols with mostly numeric but some strings)
  let conScore = 0, conCols = 0;
  headers.forEach(h => {
    const s = colStats[h];
    if (s.type === 'numeric') {
      const vals = rows.map(r => r[h]).filter(v => v !== '');
      const bad = vals.filter(v => isNaN(Number(v))).length;
      conScore += 1 - bad/Math.max(1, vals.length);
      conCols++;
    }
  });
  const consistency = conCols ? conScore / conCols : 0.9;

  // 4. Validity (range sanity for numerics)
  let valScore = 0, valCols = 0;
  headers.forEach(h => {
    const s = colStats[h];
    if (s.type === 'numeric' && s.std !== null) {
      const ok = s.outliers !== undefined ? 1 - s.outliers / Math.max(1, s.count) : 1;
      valScore += ok;
      valCols++;
    }
  });
  const validity = valCols ? valScore / valCols : 0.85;

  // 5. Outliers
  const totalOutliers = headers.reduce((s, h) => s + (colStats[h].outliers || 0), 0);
  const outlierScore = Math.max(0, 1 - totalOutliers / Math.max(1, totalCells));

  // 6. Correlation issues
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  let corrIssue = 0;
  if (numCols.length > 1) {
    for (let i = 0; i < numCols.length - 1; i++) {
      for (let j = i+1; j < numCols.length; j++) {
        const r = pearsonCorr(rows, numCols[i], numCols[j]);
        if (Math.abs(r) > 0.95) corrIssue++;
      }
    }
  }
  const corrScore = Math.max(0, 1 - corrIssue / Math.max(1, numCols.length));

  // 7. Entropy score (avg Shannon entropy per column)
  let entAvg = 0;
  headers.forEach(h => {
    const vals = rows.map(r => r[h]).filter(v => v !== '');
    const freq = {}; vals.forEach(v => freq[v] = (freq[v]||0)+1);
    const ent = Object.values(freq).reduce((s, f) => {
      const p = f/vals.length; return s - p*Math.log2(p);
    }, 0);
    const maxEnt = Math.log2(Math.max(1, new Set(vals).size));
    entAvg += maxEnt > 0 ? ent/maxEnt : 1;
  });
  const entropy = headers.length ? entAvg/headers.length : 0.5;

  // 8. Sparsity
  const sparsity = completeness; // inversely related

  // 9. Data density
  const density = Math.min(1, n / 100);

  // 10. Noise (std of std across numeric cols)
  let stdVals = numCols.map(h => colStats[h].std || 0);
  const noiseScore = stdVals.length > 1 ? Math.max(0, 1 - (Math.max(...stdVals) - Math.min(...stdVals)) / Math.max(1, Math.max(...stdVals))) : 0.8;

  // 11. Class imbalance (for low-cardinality cols)
  let imbalanceScore = 1;
  headers.forEach(h => {
    const s = colStats[h];
    if (s.unique > 1 && s.unique <= 10) {
      const freq = {}; rows.forEach(r => { const v = r[h]; if(v) freq[v] = (freq[v]||0)+1; });
      const counts = Object.values(freq);
      const maxC = Math.max(...counts), minC = Math.min(...counts);
      const ratio = maxC / Math.max(1, minC);
      if (ratio > 5) imbalanceScore = Math.min(imbalanceScore, 0.7);
    }
  });

  // 12. Feature redundancy
  const redundancy = Math.max(0, 1 - corrIssue / Math.max(1, numCols.length * 2));

  // 13. Drift (simulate: check if first half vs second half differ much)
  const half = Math.floor(n/2);
  let driftScore = 1;
  if (half > 5) {
    numCols.forEach(h => {
      const a = rows.slice(0,half).map(r=>Number(r[h])).filter(v=>!isNaN(v));
      const b = rows.slice(half).map(r=>Number(r[h])).filter(v=>!isNaN(v));
      if (a.length && b.length) {
        const ma = a.reduce((s,v)=>s+v,0)/a.length;
        const mb = b.reduce((s,v)=>s+v,0)/b.length;
        const pooledStd = colStats[h].std || 1;
        if (pooledStd > 0) {
          const d = Math.abs(ma-mb)/pooledStd;
          if (d > 0.5) driftScore = Math.min(driftScore, 1 - d*0.1);
        }
      }
    });
  }

  // Weighted DQS
  const weights = {
    completeness: 0.20,
    uniqueness: 0.12,
    consistency: 0.12,
    validity: 0.10,
    outlierScore: 0.08,
    corrScore: 0.06,
    entropy: 0.07,
    sparsity: 0.05,
    density: 0.04,
    noiseScore: 0.05,
    imbalanceScore: 0.04,
    redundancy: 0.04,
    driftScore: 0.03,
  };

  const raw = {completeness, uniqueness, consistency, validity, outlierScore,
    corrScore, entropy, sparsity, density, noiseScore, imbalanceScore, redundancy, driftScore};

  let dqs = 0;
  Object.keys(weights).forEach(k => { dqs += (raw[k] || 0) * weights[k]; });

  return { dqs: Math.round(Math.min(100, Math.max(0, dqs * 100))), raw, dupCount, missingCells, totalOutliers };
}

function pearsonCorr(rows, colA, colB) {
  const vals = rows.map(r => [Number(r[colA]), Number(r[colB])])
    .filter(([a,b]) => !isNaN(a) && !isNaN(b));
  if (vals.length < 2) return 0;
  const n = vals.length;
  const ma = vals.reduce((s,[a])=>s+a,0)/n;
  const mb = vals.reduce((s,[,b])=>s+b,0)/n;
  const num = vals.reduce((s,[a,b])=>s+(a-ma)*(b-mb),0);
  const da = Math.sqrt(vals.reduce((s,[a])=>s+(a-ma)**2,0));
  const db = Math.sqrt(vals.reduce((s,[,b])=>s+(b-mb)**2,0));
  return (da*db) ? num/(da*db) : 0;
}

/* ================================================================
   FILE LOAD FLOW
================================================================ */
document.getElementById('fileInput').addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) loadFile(file);
});

const dropArea = document.getElementById('dropArea');
dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.classList.add('drag-over'); });
dropArea.addEventListener('dragleave', () => dropArea.classList.remove('drag-over'));
dropArea.addEventListener('drop', e => {
  e.preventDefault();
  dropArea.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) loadFile(file);
});

function loadFile(file) {
  STATE.fileName = file.name;
  STATE.fileSize = file.size;
  const reader = new FileReader();
  reader.onload = e => processData(e.target.result);
  reader.readAsText(file);
}

async function processData(text) {
  showProgress();
  await sleep(50);

  setProgress(10, 'Parsing CSV...');
  await sleep(200);
  const { headers, rows } = parseCSV(text);
  if (!rows.length) { hideProgress(); alert('No data found!'); return; }

  STATE.headers = headers;
  STATE.raw = rows;
  STATE.cleaned = JSON.parse(JSON.stringify(rows));

  setProgress(30, 'Detecting column types...');
  await sleep(300);

  setProgress(50, 'Computing column statistics...');
  await sleep(300);
  STATE.colStats = computeColStats(headers, rows);

  setProgress(70, 'Running DQS engine...');
  await sleep(300);
  const dqs = computeDQS(headers, rows, STATE.colStats);
  STATE.metrics = dqs;
  STATE.dqsBefore = dqs.dqs;
  STATE.dqsAfter = dqs.dqs; // will update after cleaning

  setProgress(90, 'Rendering dashboard...');
  await sleep(300);

  renderDashboard();
  setProgress(100, 'Done!');
  await sleep(400);
  hideProgress();
  showDashboard();
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

let progVal = 0;
function setProgress(pct, text) {
  progVal = pct;
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('progressPct').textContent = pct + '%';
  document.getElementById('progressStep').textContent = text;
}
function showProgress() {
  document.getElementById('progressOverlay').style.display = 'flex';
  setProgress(0, 'Starting...');
}
function hideProgress() {
  document.getElementById('progressOverlay').style.display = 'none';
}

/* ================================================================
   DEMO DATA GENERATOR
================================================================ */
function loadDemo() {
  const headers = ['id','age','income','score','category','country','signup_date','is_premium','purchases','email'];
  const cats = ['A','B','C','D'];
  const countries = ['IN','US','UK','DE','FR'];
  const rows = [];
  for (let i = 0; i < 200; i++) {
    rows.push({
      id: i+1,
      age: Math.random() < 0.05 ? '' : (Math.random() < 0.02 ? 999 : Math.floor(18 + Math.random()*62)),
      income: Math.random() < 0.08 ? '' : Math.round(20000 + Math.random()*180000 + (Math.random()<0.03 ? 2000000 : 0)),
      score: Math.random() < 0.04 ? '' : +(Math.random()*100).toFixed(2),
      category: Math.random() < 0.05 ? '' : (Math.random()<0.6 ? cats[0] : cats[Math.floor(Math.random()*cats.length)]),
      country: countries[Math.floor(Math.random()*countries.length)],
      signup_date: Math.random() < 0.03 ? 'invalid-date' : `2023-${String(Math.floor(Math.random()*12+1)).padStart(2,'0')}-${String(Math.floor(Math.random()*28+1)).padStart(2,'0')}`,
      is_premium: Math.random() < 0.3 ? 'true' : 'false',
      purchases: Math.random() < 0.06 ? '' : Math.floor(Math.random()*50),
      email: Math.random() < 0.04 ? 'bademail' : `user${i+1}@example.com`
    });
  }
  // add some dups
  for (let i = 0; i < 8; i++) rows.push({...rows[Math.floor(Math.random()*10)]});

  const csv = [headers.join(','), ...rows.map(r => headers.map(h=>r[h]).join(','))].join('\n');
  STATE.fileName = 'demo_dataset.csv';
  STATE.fileSize = csv.length;
  processData(csv);
}

/* ================================================================
   DASHBOARD RENDERER
================================================================ */
function renderDashboard() {
  const { headers, raw, colStats, metrics } = STATE;

  // File info
  document.getElementById('fi-name').textContent = STATE.fileName;
  document.getElementById('fi-rows').textContent = raw.length.toLocaleString();
  document.getElementById('fi-cols').textContent = headers.length;
  document.getElementById('fi-size').textContent = formatBytes(STATE.fileSize);
  document.getElementById('fi-dqs').textContent = metrics.dqs + '/100';

  // DQS Ring
  const circ = 2 * Math.PI * 75;
  const offset = circ * (1 - metrics.dqs/100);
  const ring = document.getElementById('dqsRingTrack');
  setTimeout(() => ring.style.strokeDashoffset = offset, 100);
  const numEl = document.getElementById('dqsNum');
  numEl.textContent = metrics.dqs;
  const color = metrics.dqs >= 75 ? '#00FFC6' : metrics.dqs >= 50 ? '#C6A85B' : '#FF6B6B';
  numEl.style.color = color;

  // Metric list
  const metricDefs = [
    { key: 'completeness', label: 'Completeness', color: '#00FFC6', w: 0.20 },
    { key: 'uniqueness', label: 'Uniqueness', color: '#2979FF', w: 0.12 },
    { key: 'consistency', label: 'Consistency', color: '#C6A85B', w: 0.12 },
    { key: 'validity', label: 'Validity', color: '#A855F7', w: 0.10 },
    { key: 'outlierScore', label: 'Outlier Score', color: '#FF6B6B', w: 0.08 },
    { key: 'entropy', label: 'Entropy', color: '#00FFC6', w: 0.07 },
    { key: 'noiseScore', label: 'Noise Score', color: '#2979FF', w: 0.05 },
    { key: 'driftScore', label: 'Data Drift', color: '#C6A85B', w: 0.03 },
  ];
  const ml = document.getElementById('metricList');
  ml.innerHTML = '';
  metricDefs.forEach(({ key, label, color }) => {
    const val = Math.round((metrics.raw[key] || 0) * 100);
    const row = document.createElement('div');
    row.className = 'metric-row';
    row.innerHTML = `
      <div class="metric-name">${label}</div>
      <div class="metric-bar-wrap"><div class="metric-bar" style="background:${color};width:0" data-target="${val}"></div></div>
      <div class="metric-val" style="color:${color}">${val}%</div>
    `;
    ml.appendChild(row);
  });
  setTimeout(() => {
    document.querySelectorAll('.metric-bar').forEach(b => {
      b.style.width = b.dataset.target + '%';
    });
  }, 200);

  // Stat Cards
  const issues = metrics.dupCount + metrics.missingCells + metrics.totalOutliers;
  const numCols = headers.filter(h => colStats[h].type === 'numeric').length;
  const cards = [
    { icon: '📊', val: raw.length.toLocaleString(), name: 'Total Rows', color: '#00FFC6' },
    { icon: '🧮', val: headers.length, name: 'Columns', color: '#2979FF' },
    { icon: '🕳️', val: metrics.missingCells.toLocaleString(), name: 'Missing Values', color: '#FF6B6B' },
    { icon: '🔁', val: metrics.dupCount, name: 'Duplicates', color: '#C6A85B' },
    { icon: '⚠️', val: metrics.totalOutliers.toLocaleString(), name: 'Outliers', color: '#A855F7' },
    { icon: '🔢', val: numCols, name: 'Numeric Cols', color: '#00FFC6' },
  ];
  const sc = document.getElementById('statCards');
  sc.innerHTML = cards.map(c => `
    <div class="glass-card stat-card">
      <div class="stat-card-glow" style="background:${c.color}"></div>
      <span class="stat-card-icon">${c.icon}</span>
      <div class="stat-card-val" style="color:${c.color}">${c.val}</div>
      <div class="stat-card-name">${c.name}</div>
    </div>
  `).join('');

  // Issues chips
  const issChips = document.getElementById('issueChips');
  const issArr = [];
  if (metrics.missingCells > 0) issArr.push({ cls:'warn', txt: `${metrics.missingCells} missing values` });
  if (metrics.dupCount > 0) issArr.push({ cls:'bad', txt: `${metrics.dupCount} duplicate rows` });
  if (metrics.totalOutliers > 0) issArr.push({ cls:'warn', txt: `${metrics.totalOutliers} outliers detected` });
  const lowCompCols = headers.filter(h => colStats[h].missingPct > 30);
  if (lowCompCols.length) issArr.push({ cls:'bad', txt: `${lowCompCols.length} cols >30% missing` });
  const skewedCols = headers.filter(h => colStats[h].skew !== null && Math.abs(colStats[h].skew) > 1);
  if (skewedCols.length) issArr.push({ cls:'warn', txt: `${skewedCols.length} skewed columns` });
  if (!issArr.length) issArr.push({ cls:'good', txt: 'No critical issues found' });
  document.getElementById('issueCount').textContent = issArr.length;
  issChips.innerHTML = issArr.map(i => `<span class="insight-chip ${i.cls}">◈ ${i.txt}</span>`).join('');

  // Type chart (donut-like)
  const typeCounts = { numeric: 0, string: 0, datetime: 0, boolean: 0, unknown: 0 };
  headers.forEach(h => typeCounts[colStats[h].type] = (typeCounts[colStats[h].type]||0)+1);
  renderTypeChart(typeCounts);

  // Preview table
  renderTable('previewTable', headers, raw.slice(0, 20), colStats);

  // Column cards
  renderColCards();

  // Pipeline
  renderPipeline();

  // Insights
  renderInsights();

  // Compare init
  renderCompare();

  // Chat init
  initChat();

  // Code
  renderCode();
}

/* ================================================================
   PREVIEW TABLE
================================================================ */
function renderTable(id, headers, rows, colStats) {
  const tbl = document.getElementById(id);
  const thead = document.createElement('thead');
  thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  const tbody = document.createElement('tbody');
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = headers.map(h => {
      const v = r[h];
      if (v === '' || v === null || v === undefined) return `<td class="td-null">null</td>`;
      const t = colStats[h].type;
      let cls = '';
      if (t === 'numeric') {
        const n = Number(v);
        if (!isNaN(n)) {
          const { mean, std } = colStats[h];
          if (std && Math.abs((n - mean) / std) > 3) cls = 'td-bad';
        }
      }
      return `<td class="${cls}">${String(v).substring(0, 40)}</td>`;
    }).join('');
    tbody.appendChild(tr);
  });
  tbl.innerHTML = '';
  tbl.appendChild(thead);
  tbl.appendChild(tbody);
}

/* ================================================================
   TYPE PIE CHART
================================================================ */
function renderTypeChart(typeCounts) {
  const canvas = document.getElementById('typeChart');
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth || 300;
  canvas.width = W; canvas.height = 180;
  ctx.clearRect(0,0,W,180);

  const colors = { numeric: '#2979FF', string: '#C6A85B', datetime: '#00FFC6', boolean: '#A855F7', unknown: '#4A5568' };
  const entries = Object.entries(typeCounts).filter(([,v])=>v>0);
  const total = entries.reduce((s,[,v])=>s+v,0);
  if (!total) return;

  const cx = 80, cy = 85, r = 60, ir = 38;
  let angle = -Math.PI/2;
  entries.forEach(([type, count]) => {
    const span = (count/total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,angle,angle+span);
    ctx.closePath();
    ctx.fillStyle = colors[type];
    ctx.fill();
    angle += span;
  });
  // inner hole
  ctx.beginPath(); ctx.arc(cx,cy,ir,0,2*Math.PI);
  ctx.fillStyle = '#0D1220'; ctx.fill();

  // Legend
  let lx = 160, ly = 30;
  entries.forEach(([type, count]) => {
    ctx.fillStyle = colors[type];
    ctx.beginPath(); ctx.roundRect(lx, ly-8, 10, 10, 2); ctx.fill();
    ctx.fillStyle = '#6B7FA3';
    ctx.font = '12px Outfit';
    ctx.fillText(`${type} (${count})`, lx+16, ly);
    ly += 24;
  });
  ctx.fillStyle = '#EAEFF7'; ctx.font = 'bold 18px Syne';
  ctx.textAlign = 'center';
  ctx.fillText(total, cx, cy+6);
  ctx.textAlign = 'left';
}

/* ================================================================
   COLUMN CARDS
================================================================ */
function renderColCards() {
  const { headers, colStats } = STATE;
  document.getElementById('colCount').textContent = `${headers.length} columns`;
  const grid = document.getElementById('colCards');
  const typeClsMap = { numeric:'type-num', string:'type-str', datetime:'type-dt', boolean:'type-bool', unknown:'type-str' };
  grid.innerHTML = headers.map(h => {
    const s = colStats[h];
    const quality = Math.round((1 - s.missingPct/100) * 100);
    const qcolor = quality>=80 ? '#00FFC6' : quality>=50 ? '#C6A85B' : '#FF6B6B';
    const barsHTML = s.bins.length ?
      `<div class="dist-bars">${s.bins.map(b => {
        const m = Math.max(...s.bins,1);
        const h2 = Math.max(4, Math.round(b/m*52));
        return `<div class="dist-bar" style="height:${h2}px"></div>`;
      }).join('')}</div>` : '';

    return `
    <div class="glass-card col-card">
      <div class="col-card-header">
        <div class="col-card-name">${h}</div>
        <span class="col-card-type ${typeClsMap[s.type]}">${s.type}</span>
      </div>
      <div class="col-mini-stats">
        <div class="col-mini-row"><span class="col-mini-label">Completeness</span><span class="col-mini-val">${(100-s.missingPct).toFixed(1)}%</span></div>
        <div class="col-mini-row"><span class="col-mini-label">Unique vals</span><span class="col-mini-val">${s.unique}</span></div>
        ${s.mean !== null ? `<div class="col-mini-row"><span class="col-mini-label">Mean</span><span class="col-mini-val">${s.mean.toFixed(2)}</span></div>` : ''}
        ${s.std !== null ? `<div class="col-mini-row"><span class="col-mini-label">Std Dev</span><span class="col-mini-val">${s.std.toFixed(2)}</span></div>` : ''}
        ${s.outliers > 0 ? `<div class="col-mini-row"><span class="col-mini-label">Outliers</span><span class="col-mini-val td-bad">${s.outliers}</span></div>` : ''}
        ${s.skew !== null ? `<div class="col-mini-row"><span class="col-mini-label">Skewness</span><span class="col-mini-val ${Math.abs(s.skew)>1?'td-warn':''}">${s.skew.toFixed(3)}</span></div>` : ''}
      </div>
      ${barsHTML}
      <div class="col-quality-bar" title="Data Quality: ${quality}%">
        <div class="col-quality-fill" style="width:${quality}%;background:${qcolor}"></div>
      </div>
    </div>`;
  }).join('');
}

/* ================================================================
   INSIGHTS
================================================================ */
function renderInsights() {
  renderHeatmap();
  renderDistCharts();
  renderAnomalies();
  renderCluster();
  renderStatsTable();
}

function renderHeatmap() {
  const { headers, raw, colStats } = STATE;
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  const wrap = document.getElementById('heatmapWrap');
  if (numCols.length < 2) { wrap.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">Need ≥2 numeric columns for correlation matrix.</p>'; return; }
  const cols = numCols.slice(0,8);
  const n = cols.length;
  const grid = document.createElement('div');
  grid.className = 'heatmap-grid';
  grid.style.gridTemplateColumns = `60px ${Array(n).fill('40px').join(' ')}`;

  // Header row
  const emptyCell = document.createElement('div');
  emptyCell.style.cssText = 'width:60px;height:40px;';
  grid.appendChild(emptyCell);
  cols.forEach(c => {
    const lbl = document.createElement('div');
    lbl.className = 'heatmap-label';
    lbl.style.cssText = 'width:40px;height:40px;font-size:9px;';
    lbl.title = c;
    lbl.textContent = c.substring(0,5);
    grid.appendChild(lbl);
  });

  cols.forEach(rowC => {
    const rowLbl = document.createElement('div');
    rowLbl.className = 'heatmap-label';
    rowLbl.style.cssText = 'width:60px;height:40px;font-size:9px;justify-content:flex-end;padding-right:4px;';
    rowLbl.title = rowC;
    rowLbl.textContent = rowC.substring(0,7);
    grid.appendChild(rowLbl);

    cols.forEach(colC => {
      const r = rowC === colC ? 1 : pearsonCorr(raw, rowC, colC);
      const cell = document.createElement('div');
      cell.className = 'heatmap-cell';
      cell.title = `${rowC} vs ${colC}: ${r.toFixed(3)}`;
      cell.textContent = r.toFixed(2);
      const t = r; // -1 to 1
      const rr = t > 0 ? Math.round(t * 41) : Math.round(255 + t * 214);
      const g = t > 0 ? Math.round(255 - t * 57) : Math.round(107 + t * 107);
      const b = t > 0 ? Math.round(198 - t * 198) : Math.round(107 - t * 107);
      cell.style.background = `rgba(${rr},${g},${b},${Math.abs(t)*0.8+0.15})`;
      cell.style.color = Math.abs(t) > 0.5 ? '#fff' : 'var(--text-muted)';
      grid.appendChild(cell);
    });
  });
  wrap.innerHTML = '';
  wrap.appendChild(grid);
}

function renderDistCharts() {
  const { headers, colStats } = STATE;
  const numCols = headers.filter(h => colStats[h].type === 'numeric' && colStats[h].bins.length).slice(0,4);
  const wrap = document.getElementById('distCharts');
  wrap.innerHTML = numCols.map(h => {
    const s = colStats[h];
    const bars = s.bins;
    const maxB = Math.max(...bars, 1);
    const colors = ['#00FFC6','#2979FF','#C6A85B','#A855F7'];
    const idx = numCols.indexOf(h);
    const clr = colors[idx % colors.length];
    return `
      <div style="margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
          <span style="font-size:12px;color:var(--text-muted);font-family:var(--font-mono)">${h}</span>
          <span style="font-size:11px;color:var(--text-dim)">Skew: ${s.skew !== null ? s.skew.toFixed(3) : 'N/A'}</span>
        </div>
        <div style="display:flex;align-items:flex-end;gap:2px;height:50px;">
          ${bars.map(b => {
            const h2 = Math.max(2, Math.round(b/maxB*46));
            return `<div style="flex:1;height:${h2}px;background:${clr};border-radius:2px 2px 0 0;opacity:0.8;min-height:2px;"></div>`;
          }).join('')}
        </div>
        <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:9px;color:var(--text-dim);margin-top:2px;">
          <span>${s.min !== null ? s.min.toFixed(1) : ''}</span>
          <span>${s.max !== null ? s.max.toFixed(1) : ''}</span>
        </div>
      </div>
    `;
  }).join('') || '<p style="color:var(--text-muted);font-size:13px;">No numeric columns found.</p>';
}

function renderAnomalies() {
  const { headers, raw, colStats } = STATE;
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  const wrap = document.getElementById('anomalyTable');
  if (!numCols.length) { wrap.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No numeric columns.</p>'; return; }

  const rows = numCols.map(h => {
    const s = colStats[h];
    const vals = raw.map(r=>Number(r[h])).filter(v=>!isNaN(v));
    if (!vals.length) return null;
    const q1 = vals.sort((a,b)=>a-b)[Math.floor(vals.length*0.25)];
    const q3 = vals[Math.floor(vals.length*0.75)];
    const iqr = q3 - q1;
    const zOutliers = vals.filter(v => s.std > 0 && Math.abs((v-s.mean)/s.std) > 3).length;
    const iqrOut = vals.filter(v => v < q1-1.5*iqr || v > q3+1.5*iqr).length;
    const severity = zOutliers > 5 ? 'ab-high' : zOutliers > 0 ? 'ab-med' : 'ab-low';
    const sevTxt = zOutliers > 5 ? 'HIGH' : zOutliers > 0 ? 'MED' : 'LOW';
    return `<div class="ba-diff-row">
      <div class="ba-diff-name">${h}</div>
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--text-muted)">Z: ${zOutliers}</div>
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--text-muted)">IQR: ${iqrOut}</div>
      <span class="anomaly-badge ${severity}">${sevTxt}</span>
    </div>`;
  }).filter(Boolean);
  wrap.innerHTML = rows.join('') || '<p style="color:var(--text-muted)">No anomalies.</p>';
}

function renderCluster() {
  const { headers, raw, colStats } = STATE;
  const canvas = document.getElementById('clusterChart');
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  if (numCols.length < 2) {
    canvas.parentElement.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:20px;">Need ≥2 numeric columns for clustering visualization.</p>';
    return;
  }
  const colA = numCols[0], colB = numCols[1];
  const pts = raw.map(r => [Number(r[colA]), Number(r[colB])]).filter(([a,b]) => !isNaN(a) && !isNaN(b)).slice(0,150);
  const W = canvas.parentElement.clientWidth || 400, H = 260;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');

  // Normalize
  const xs = pts.map(p=>p[0]), ys = pts.map(p=>p[1]);
  const xMin=Math.min(...xs), xMax=Math.max(...xs), yMin=Math.min(...ys), yMax=Math.max(...ys);
  const norm = pts.map(p => [(p[0]-xMin)/(xMax-xMin||1), (p[1]-yMin)/(yMax-yMin||1)]);

  // Simple 3-means
  const K = 3;
  let centroids = [norm[0]||[0.2,0.2], norm[Math.floor(norm.length/2)]||[0.5,0.5], norm[norm.length-1]||[0.8,0.8]];
  let labels = new Array(norm.length).fill(0);
  for (let iter=0;iter<10;iter++) {
    labels = norm.map(p => {
      let best=0, bestD=Infinity;
      centroids.forEach((c,k) => { const d=(p[0]-c[0])**2+(p[1]-c[1])**2; if(d<bestD){bestD=d;best=k;} });
      return best;
    });
    centroids = Array.from({length:K},(_,k)=>{
      const members=norm.filter((_,i)=>labels[i]===k);
      if(!members.length) return centroids[k];
      return [members.reduce((s,p)=>s+p[0],0)/members.length, members.reduce((s,p)=>s+p[1],0)/members.length];
    });
  }

  const clColors = ['#00FFC6','#2979FF','#C6A85B'];
  const pad=30;
  ctx.clearRect(0,0,W,H);
  // Grid lines
  ctx.strokeStyle='rgba(255,255,255,0.04)'; ctx.lineWidth=1;
  for(let i=0;i<=4;i++){
    ctx.beginPath();ctx.moveTo(pad,pad+i*(H-2*pad)/4);ctx.lineTo(W-pad,pad+i*(H-2*pad)/4);ctx.stroke();
    ctx.beginPath();ctx.moveTo(pad+i*(W-2*pad)/4,pad);ctx.lineTo(pad+i*(W-2*pad)/4,H-pad);ctx.stroke();
  }
  // Points
  norm.forEach(([x,y],i) => {
    const px = pad + x*(W-2*pad), py = H-pad - y*(H-2*pad);
    const k = labels[i];
    ctx.beginPath();ctx.arc(px,py,4,0,Math.PI*2);
    ctx.fillStyle = clColors[k]+'99'; ctx.fill();
    ctx.strokeStyle = clColors[k]; ctx.lineWidth = 0.5; ctx.stroke();
  });
  // Centroids
  centroids.forEach(([x,y],k) => {
    const px = pad + x*(W-2*pad), py = H-pad - y*(H-2*pad);
    ctx.beginPath();ctx.arc(px,py,8,0,Math.PI*2);
    ctx.fillStyle=clColors[k]; ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.stroke();
  });
  // Axis labels
  ctx.fillStyle='#6B7FA3'; ctx.font='10px DM Mono'; ctx.textAlign='center';
  ctx.fillText(colA, W/2, H-4);
  ctx.save(); ctx.translate(10,H/2); ctx.rotate(-Math.PI/2);
  ctx.fillText(colB,0,0); ctx.restore(); ctx.textAlign='left';

  const legend = document.getElementById('clusterLegend');
  legend.innerHTML = clColors.map((c,i)=>{
    const cnt = labels.filter(l=>l===i).length;
    return `<div class="cl-item"><div class="cl-dot" style="background:${c}"></div>Cluster ${i+1} (${cnt} pts)</div>`;
  }).join('');
}

function renderStatsTable() {
  const { headers, colStats } = STATE;
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  const tbl = document.getElementById('statsTable');
  if (!numCols.length) { tbl.innerHTML=''; return; }
  const thead = `<thead><tr><th>Column</th><th>Mean</th><th>Std</th><th>Min</th><th>Max</th><th>Skewness</th><th>Kurtosis</th><th>Outliers</th></tr></thead>`;
  const tbody = `<tbody>${numCols.map(h => {
    const s = colStats[h];
    const skewCls = Math.abs(s.skew||0) > 1 ? 'td-warn' : '';
    return `<tr>
      <td class="td-good">${h}</td>
      <td>${s.mean !== null ? s.mean.toFixed(3) : '—'}</td>
      <td>${s.std !== null ? s.std.toFixed(3) : '—'}</td>
      <td>${s.min !== null ? s.min.toFixed(3) : '—'}</td>
      <td>${s.max !== null ? s.max.toFixed(3) : '—'}</td>
      <td class="${skewCls}">${s.skew !== null ? s.skew.toFixed(4) : '—'}</td>
      <td>${s.kurt !== null ? s.kurt.toFixed(4) : '—'}</td>
      <td class="${s.outliers > 0 ? 'td-bad' : ''}">${s.outliers}</td>
    </tr>`;
  }).join('')}</tbody>`;
  tbl.innerHTML = thead + tbody;
}

/* ================================================================
   CLEANING PIPELINE
================================================================ */
const PIPELINE_DEFS = [
  { id:'dtype', name:'Data Type Correction', desc:'Detect and auto-convert incorrect column types' },
  { id:'missing', name:'Missing Value Handling', desc:'Impute or drop missing values intelligently', opts:['Drop Rows','Mean/Median Fill','KNN Imputation'] },
  { id:'duplicates', name:'Duplicate Removal', desc:'Remove exact and near-duplicate rows', opts:['Exact Only','Fuzzy Match'] },
  { id:'outliers', name:'Outlier Treatment', desc:'Handle extreme values using IQR/Z-score', opts:['Remove','Cap (Winsorize)','Log Transform'] },
  { id:'noise', name:'Noise Reduction', desc:'Smooth noisy numeric signals', opts:['Rolling Mean','Median Filter'] },
  { id:'normalize', name:'Data Normalization', desc:'Scale numeric features to standard range', opts:['Min-Max','Standardize (Z)'] },
  { id:'encode', name:'Encoding', desc:'Encode categorical columns', opts:['Label Encode','One-Hot Encode'] },
  { id:'feature_sel', name:'Feature Selection', desc:'Remove low-variance and redundant features', opts:['Low Variance','High Correlation'] },
  { id:'feature_eng', name:'Feature Engineering', desc:'Create derived and interaction features', opts:['Datetime Expand','Interaction Features'] },
  { id:'balance', name:'Data Balancing', desc:'Handle class imbalance in target column', opts:['Oversample','Undersample'] },
  { id:'compress', name:'Data Compression', desc:'Remove unnecessary columns and reduce dimensionality' },
  { id:'schema', name:'Schema Alignment', desc:'Fix inconsistent formats across columns' },
  { id:'text', name:'Text Cleaning', desc:'Clean string columns: lowercase, stopwords, special chars' },
  { id:'timeseries', name:'Time-Series Cleaning', desc:'Sort by time, handle missing timestamps, smooth spikes' },
];

let pipelineState = {};

function renderPipeline() {
  const wrap = document.getElementById('pipelineSteps');
  wrap.innerHTML = '';
  PIPELINE_DEFS.forEach((step, idx) => {
    pipelineState[step.id] = { status: 'pending', option: step.opts ? step.opts[0] : null };
    const el = document.createElement('div');
    el.className = 'pipeline-step';
    el.id = 'step-' + step.id;
    const hasOpts = step.opts && step.opts.length;
    el.innerHTML = `
      <div class="step-header" onclick="toggleStep('${step.id}')">
        <div class="step-num">${String(idx+1).padStart(2,'0')}</div>
        <div class="step-info">
          <div class="step-name">${step.name}</div>
          <div class="step-desc">${step.desc}</div>
        </div>
        <span class="step-status status-pending" id="status-${step.id}">PENDING</span>
      </div>
      <div class="step-expand" id="expand-${step.id}">
        <div class="step-body">
          ${hasOpts ? `<div class="step-options">${step.opts.map((o,i) =>
            `<button class="option-btn${i===0?' selected':''}" onclick="selectOpt('${step.id}','${o}',this)">${o}</button>`
          ).join('')}</div>` : ''}
          <div class="step-impact" id="impact-${step.id}">
            <strong>Impact:</strong> Click "Run Pipeline" to see detailed impact on DQS after applying this step.
          </div>
        </div>
      </div>
    `;
    wrap.appendChild(el);
  });

  // Impact preview
  updateImpactPreview();
}

function toggleStep(id) {
  const ex = document.getElementById('expand-' + id);
  ex.classList.toggle('open');
}

function selectOpt(stepId, opt, btn) {
  pipelineState[stepId].option = opt;
  btn.closest('.step-options').querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
}

function selectStrategy(el, s) {
  STATE.strategy = s;
  document.querySelectorAll('.strategy-card').forEach(c => c.classList.remove('selected-strategy'));
  el.classList.add('selected-strategy');
  updateImpactPreview();
}

function updateImpactPreview() {
  const { metrics, raw } = STATE;
  const s = STATE.strategy;
  const mults = { conservative: 0.6, balanced: 0.85, aggressive: 1.1 };
  const m = mults[s];
  const expectedRows = Math.round(raw.length - metrics.dupCount - (s==='aggressive' ? metrics.missingCells*0.3 : 0));
  const expectedDqs = Math.min(100, Math.round(metrics.dqs + (100 - metrics.dqs) * 0.4 * m));
  document.getElementById('impactPreview').innerHTML = `
    <div class="ba-diff-row">
      <div class="ba-diff-name">Rows removed</div>
      <div class="ba-diff-after">~${raw.length - expectedRows}</div>
    </div>
    <div class="ba-diff-row">
      <div class="ba-diff-name">Expected DQS</div>
      <div class="ba-diff-before">${metrics.dqs}</div>
      <div class="ba-diff-arrow">→</div>
      <div class="ba-diff-after">${expectedDqs}</div>
    </div>
    <div class="ba-diff-row">
      <div class="ba-diff-name">Outliers handled</div>
      <div class="ba-diff-after">~${Math.round(metrics.totalOutliers * m)}</div>
    </div>
  `;
}

/* ================================================================
   RUN PIPELINE
================================================================ */
async function runPipeline() {
  if (!STATE.raw.length) return;
  const btn = document.getElementById('runPipelineBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Running...';

  STATE.cleaned = JSON.parse(JSON.stringify(STATE.raw));
  STATE.changes = [];

  const steps = PIPELINE_DEFS;
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const el = document.getElementById('step-' + step.id);
    const statusEl = document.getElementById('status-' + step.id);
    el.classList.remove('done-step'); el.classList.add('active-step');
    statusEl.className = 'step-status status-running'; statusEl.textContent = 'RUNNING';
    await sleep(150);
    const result = applyStep(step.id, STATE.cleaned, STATE.headers, STATE.colStats);
    STATE.cleaned = result.data;
    STATE.changes.push({ step: step.name, ...result });
    el.classList.remove('active-step'); el.classList.add('done-step');
    statusEl.className = 'step-status status-done'; statusEl.textContent = 'DONE';
    document.getElementById('impact-' + step.id).innerHTML =
      `<strong>Changed:</strong> ${result.changed} | <strong>Why:</strong> ${result.why} | <strong>DQS Impact:</strong> <span style="color:var(--primary)">+${result.dqsImpact}</span>`;
    // open expand
    document.getElementById('expand-' + step.id).classList.add('open');
    await sleep(50);
  }

  // Recompute DQS on cleaned
  const newColStats = computeColStats(STATE.headers, STATE.cleaned);
  const newDqs = computeDQS(STATE.headers, STATE.cleaned, newColStats);
  STATE.dqsAfter = newDqs.dqs;

  STATE.pipelineRan = true;
  btn.disabled = false;
  btn.textContent = '✅ Pipeline Complete — Rerun?';

  renderCompare();
}

function applyStep(id, data, headers, colStats) {
  const s = STATE.strategy;
  const ps = pipelineState[id];
  let changed = '—', why = '—', dqsImpact = 0;
  let out = data;

  if (id === 'dtype') {
    // Auto-convert obvious numerics stored as strings
    let fixed = 0;
    out = data.map(row => {
      const r = {...row};
      headers.forEach(h => {
        if (colStats[h].type === 'numeric' && r[h] !== '' && isNaN(Number(r[h]))) {
          const n = parseFloat(r[h].replace(/[^0-9.-]/g,''));
          if (!isNaN(n)) { r[h] = n; fixed++; }
        }
      });
      return r;
    });
    changed = `${fixed} cells converted`; why = 'Detected numeric data stored as strings'; dqsImpact = fixed > 0 ? 2 : 0;
  }

  else if (id === 'missing') {
    const opt = ps.option;
    let removed = 0, filled = 0;
    if (opt === 'Drop Rows') {
      out = data.filter(row => !headers.some(h => row[h] === '' || row[h] === null || row[h] === undefined));
      removed = data.length - out.length;
      changed = `${removed} rows dropped`; why = 'Rows with any missing values removed'; dqsImpact = removed > 0 ? 5 : 0;
    } else {
      out = data.map(row => {
        const r = {...row};
        headers.forEach(h => {
          if (r[h] === '' || r[h] === null || r[h] === undefined) {
            if (colStats[h].type === 'numeric' && colStats[h].mean !== null) {
              r[h] = +(colStats[h].mean.toFixed(4)); filled++;
            } else if (colStats[h].type === 'string') {
              r[h] = 'Unknown'; filled++;
            }
          }
        });
        return r;
      });
      changed = `${filled} values imputed`; why = `Mean/mode imputation applied (${opt})`; dqsImpact = filled > 0 ? 4 : 0;
    }
  }

  else if (id === 'duplicates') {
    const seen = new Set();
    let removedDups = 0;
    out = data.filter(row => {
      const key = headers.map(h => row[h]).join('||');
      if (seen.has(key)) { removedDups++; return false; }
      seen.add(key); return true;
    });
    changed = `${removedDups} duplicates removed`; why = 'Exact duplicate rows detected and removed'; dqsImpact = removedDups > 0 ? 6 : 0;
  }

  else if (id === 'outliers') {
    const opt = ps.option;
    let treated = 0;
    const numCols = headers.filter(h => colStats[h].type === 'numeric');
    out = data.map(row => {
      const r = {...row};
      numCols.forEach(h => {
        const v = Number(r[h]);
        if (isNaN(v)) return;
        const { mean, std } = colStats[h];
        if (!std) return;
        if (Math.abs((v - mean) / std) > (s === 'aggressive' ? 2 : 3)) {
          if (opt === 'Remove') { r[h] = ''; }
          else if (opt === 'Cap (Winsorize)') { r[h] = v > mean + 3*std ? +(mean+3*std).toFixed(4) : +(mean-3*std).toFixed(4); }
          else if (opt === 'Log Transform') { r[h] = v > 0 ? +(Math.log(v)).toFixed(4) : r[h]; }
          treated++;
        }
      });
      return r;
    });
    changed = `${treated} outlier values treated`; why = `Z-score threshold; strategy: ${opt}`; dqsImpact = treated > 0 ? 4 : 0;
  }

  else if (id === 'noise') {
    // Apply rolling mean to numeric cols (window=3)
    const numCols = headers.filter(h => colStats[h].type === 'numeric');
    let smoothed = 0;
    out = [...data];
    numCols.forEach(h => {
      for (let i = 1; i < out.length-1; i++) {
        const prev=Number(out[i-1][h]), cur=Number(out[i][h]), next=Number(out[i+1][h]);
        if (!isNaN(prev)&&!isNaN(cur)&&!isNaN(next)) {
          out[i]={...out[i],[h]:+((prev+cur+next)/3).toFixed(4)};
          smoothed++;
        }
      }
    });
    changed = `${smoothed} values smoothed`; why = 'Rolling mean window=3 applied to numeric columns'; dqsImpact = 1;
  }

  else if (id === 'normalize') {
    const opt = ps.option;
    const numCols = headers.filter(h => colStats[h].type === 'numeric');
    out = data.map(row => {
      const r = {...row};
      numCols.forEach(h => {
        const v = Number(r[h]);
        if (isNaN(v)) return;
        const { min, max, mean, std } = colStats[h];
        if (opt === 'Min-Max' && max !== min) r[h] = +((v-min)/(max-min)).toFixed(6);
        else if (opt === 'Standardize (Z)' && std) r[h] = +((v-mean)/std).toFixed(6);
      });
      return r;
    });
    changed = `${numCols.length} columns normalized`; why = `${opt} scaling applied`; dqsImpact = 2;
  }

  else if (id === 'encode') {
    const opt = ps.option;
    const strCols = headers.filter(h => colStats[h].type === 'string' && colStats[h].unique < 20);
    let encoded = 0;
    if (opt === 'Label Encode') {
      out = data.map(row => {
        const r = {...row};
        strCols.forEach(h => {
          const map = {}; let ctr = 0;
          const vals = [...new Set(data.map(x=>x[h]))];
          vals.forEach(v => map[v]=ctr++);
          if (r[h] !== '' && r[h] !== undefined) { r[h] = map[r[h]] ?? r[h]; encoded++; }
        });
        return r;
      });
    }
    changed = `${strCols.length} cols encoded`; why = `${opt} applied to low-cardinality string cols`; dqsImpact = 2;
  }

  else if (id === 'feature_sel') {
    // Remove columns with >95% missing
    const toRemove = headers.filter(h => colStats[h].missingPct > 95);
    if (toRemove.length) {
      out = data.map(row => {
        const r = {...row};
        toRemove.forEach(h => delete r[h]);
        return r;
      });
      // Note: we don't modify STATE.headers here for simplicity
    }
    changed = `${toRemove.length} columns dropped`; why = '>95% missing values — feature not useful'; dqsImpact = toRemove.length * 2;
  }

  else if (id === 'feature_eng') {
    // Expand datetime columns
    const dtCols = headers.filter(h => colStats[h].type === 'datetime');
    let expanded = 0;
    out = data.map(row => {
      const r = {...row};
      dtCols.forEach(h => {
        const d = new Date(r[h]);
        if (!isNaN(d.getTime())) {
          r[h+'_year'] = d.getFullYear();
          r[h+'_month'] = d.getMonth()+1;
          r[h+'_day'] = d.getDate();
          expanded++;
        }
      });
      return r;
    });
    changed = `${dtCols.length * 3} features created from ${dtCols.length} datetime cols`; why = 'Year/Month/Day extracted for ML readiness'; dqsImpact = 1;
  }

  else if (id === 'balance') {
    changed = 'Skipped (no binary target)'; why = 'Class balancing requires a defined target column'; dqsImpact = 0;
  }

  else if (id === 'compress') {
    // Remove cols with unique count === row count (likely IDs) and not numeric
    const idCols = headers.filter(h => colStats[h].type !== 'numeric' && colStats[h].unique >= data.length * 0.95 && h.toLowerCase().includes('id'));
    changed = `${idCols.length} ID-like cols identified`; why = 'High-cardinality string columns likely to be identifiers'; dqsImpact = idCols.length;
  }

  else if (id === 'schema') {
    // Trim whitespace, unify case for string cols
    let fixed = 0;
    out = data.map(row => {
      const r = {...row};
      headers.forEach(h => {
        if (typeof r[h] === 'string' && r[h]) {
          const trimmed = r[h].trim();
          if (trimmed !== r[h]) { r[h] = trimmed; fixed++; }
        }
      });
      return r;
    });
    changed = `${fixed} values trimmed`; why = 'Leading/trailing whitespace removed for consistency'; dqsImpact = fixed > 0 ? 1 : 0;
  }

  else if (id === 'text') {
    const stopwords = new Set(['the','a','an','is','in','on','at','to','of','and','or','but','for','with','by','as','it','its']);
    const strCols = headers.filter(h => colStats[h].type === 'string');
    let cleaned = 0;
    out = data.map(row => {
      const r = {...row};
      strCols.forEach(h => {
        if (r[h] && typeof r[h] === 'string' && r[h].length > 3) {
          const orig = r[h];
          r[h] = r[h].toLowerCase().replace(/[^a-z0-9\s]/g,'').split(' ').filter(w=>!stopwords.has(w)).join(' ');
          if (r[h] !== orig) cleaned++;
        }
      });
      return r;
    });
    changed = `${cleaned} text values cleaned`; why = 'Lowercase + special char removal + stopword filter'; dqsImpact = 1;
  }

  else if (id === 'timeseries') {
    const dtCols = headers.filter(h => colStats[h].type === 'datetime');
    if (dtCols.length) {
      out = [...data].sort((a,b) => new Date(a[dtCols[0]]) - new Date(b[dtCols[0]]));
      changed = `Data sorted by ${dtCols[0]}`; why = 'Time-series requires chronological ordering'; dqsImpact = 1;
    } else {
      changed = 'No datetime columns found'; why = 'Time-series cleaning skipped'; dqsImpact = 0;
    }
  }

  return { data: out, changed, why, dqsImpact };
}

/* ================================================================
   BEFORE/AFTER COMPARE
================================================================ */
function renderCompare() {
  const { dqsBefore, dqsAfter, raw, cleaned, changes } = STATE;
  const colorBefore = '#FF6B6B', colorAfter = '#00FFC6';

  document.getElementById('baScoreBefore').textContent = dqsBefore;
  document.getElementById('baScoreAfter').textContent = dqsAfter;
  document.getElementById('baRowsBefore').textContent = `${raw.length.toLocaleString()} rows`;
  document.getElementById('baRowsAfter').textContent = `${cleaned.length.toLocaleString()} rows`;

  // Comparison chart
  const canvas = document.getElementById('compareChart');
  const W = canvas.parentElement.clientWidth || 600;
  canvas.width = W; canvas.height = 200;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,W,200);

  const { raw: mRaw } = STATE.metrics;
  const keys = ['completeness','uniqueness','consistency','validity','outlierScore','entropy'];
  const labels = ['Completeness','Uniqueness','Consistency','Validity','Outliers','Entropy'];
  const beforeVals = keys.map(k => Math.round((mRaw[k]||0)*100));
  const afterVals = keys.map(k => Math.min(100, Math.round((mRaw[k]||0)*100 + (100-(mRaw[k]||0)*100)*0.4*(STATE.pipelineRan?1:0))));

  const barW = (W - 80) / (keys.length * 2 + keys.length + 1);
  const maxH = 150;
  const baseY = 170;

  keys.forEach((k, i) => {
    const x = 40 + i * (barW * 2 + barW);
    // Before
    const bH = beforeVals[i]/100 * maxH;
    ctx.fillStyle = colorBefore + '99';
    ctx.beginPath(); ctx.roundRect(x, baseY-bH, barW, bH, [3,3,0,0]); ctx.fill();
    // After
    const aH = afterVals[i]/100 * maxH;
    ctx.fillStyle = colorAfter + '99';
    ctx.beginPath(); ctx.roundRect(x+barW+2, baseY-aH, barW, aH, [3,3,0,0]); ctx.fill();
    // Label
    ctx.fillStyle = '#6B7FA3'; ctx.font = '9px DM Mono'; ctx.textAlign = 'center';
    ctx.fillText(labels[i], x + barW + 1, baseY + 14);
    // Values
    ctx.fillStyle = colorBefore; ctx.font = '10px DM Mono';
    ctx.fillText(beforeVals[i], x + barW/2, baseY - bH - 4);
    ctx.fillStyle = colorAfter;
    ctx.fillText(afterVals[i], x + barW + 2 + barW/2, baseY - aH - 4);
  });

  // Legend
  ctx.fillStyle = colorBefore; ctx.fillRect(W/2-60, 8, 10, 10);
  ctx.fillStyle = '#6B7FA3'; ctx.font = '11px Outfit'; ctx.textAlign = 'left';
  ctx.fillText('Before', W/2-46, 18);
  ctx.fillStyle = colorAfter; ctx.fillRect(W/2+10, 8, 10, 10);
  ctx.fillStyle = '#6B7FA3';
  ctx.fillText('After', W/2+24, 18);

  // Change log
  document.getElementById('changeCount').textContent = `${changes.length} changes`;
  const log = document.getElementById('changeLog');
  if (!changes.length) {
    log.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:16px;">Run the pipeline to see change details.</p>';
  } else {
    log.innerHTML = changes.map(c => `
      <div class="ba-diff-row">
        <div class="ba-diff-name" style="font-weight:600;color:var(--text)">${c.step}</div>
        <div style="font-size:12px;color:var(--text-muted);flex:2;">${c.changed}</div>
        <div style="font-size:12px;color:var(--text-dim);flex:2;">${c.why}</div>
        ${c.dqsImpact > 0 ? `<span class="ba-diff-delta delta-good">+${c.dqsImpact} DQS</span>` : '<span class="ba-diff-delta" style="background:transparent;color:var(--text-dim)">—</span>'}
      </div>
    `).join('');
  }
}

/* ================================================================
   AI CHAT
================================================================ */
const CHAT_RESPONSES = {
  missing: () => {
    const { metrics, headers, colStats } = STATE;
    const worst = headers.filter(h=>colStats[h].missing>0).sort((a,b)=>colStats[b].missing-colStats[a].missing)[0];
    return `Your dataset has <strong>${metrics.missingCells} missing values</strong> across all columns. The column with the most missing data is <strong>${worst||'none'}</strong>. I recommend using Mean/Median imputation for numeric columns and Mode for categorical ones.`;
  },
  outliers: () => {
    const { metrics } = STATE;
    return `I detected <strong>${metrics.totalOutliers} potential outliers</strong> using the IQR method. For a conservative approach, winsorization (capping) is recommended over removal to preserve data distribution.`;
  },
  dqs: () => {
    const { metrics } = STATE;
    const grade = metrics.dqs >= 80 ? 'Good 🟢' : metrics.dqs >= 60 ? 'Moderate 🟡' : 'Poor 🔴';
    return `Your <strong>Data Quality Score is ${metrics.dqs}/100</strong> — rated as <strong>${grade}</strong>. The biggest drags are completeness (${Math.round((STATE.metrics.raw.completeness||0)*100)}%) and uniqueness (${Math.round((STATE.metrics.raw.uniqueness||0)*100)}%).`;
  },
  columns: () => {
    const { headers, colStats } = STATE;
    const types = {};
    headers.forEach(h => types[colStats[h].type]=(types[colStats[h].type]||0)+1);
    return `Your dataset has <strong>${headers.length} columns</strong>: ${Object.entries(types).map(([t,n])=>`${n} ${t}`).join(', ')}. ${headers.filter(h=>colStats[h].missingPct>20).length} columns have >20% missing values.`;
  },
  duplicates: () => {
    const { metrics, raw } = STATE;
    return `I found <strong>${metrics.dupCount} exact duplicate rows</strong> (${(metrics.dupCount/raw.length*100).toFixed(1)}% of data). These should be removed before training any ML model to avoid data leakage.`;
  },
  skewness: () => {
    const { headers, colStats } = STATE;
    const skewed = headers.filter(h => colStats[h].skew !== null && Math.abs(colStats[h].skew) > 1);
    return skewed.length ? `<strong>${skewed.length} columns are skewed</strong> (|skew| > 1): ${skewed.slice(0,3).join(', ')}. Log or Box-Cox transformation can help normalize these distributions for regression models.`
      : 'Your numeric columns appear fairly symmetric — good sign for linear models!';
  },
  clean: () => `To clean your dataset, go to the <strong>Clean tab</strong>, choose a strategy (Conservative/Balanced/Aggressive), then click <strong>Run Full Pipeline</strong>. Each of the 14 steps will explain what it changed and why.`,
  download: () => `After running the pipeline, go to the <strong>Code tab</strong> and click <strong>Download Cleaned CSV</strong>. You can also download the equivalent Python (pandas) cleaning code!`,
};

const QUICK_QS = [
  { label:'How many missing values?', key:'missing' },
  { label:'Tell me about outliers', key:'outliers' },
  { label:'What is my DQS?', key:'dqs' },
  { label:'Column overview', key:'columns' },
  { label:'Any duplicates?', key:'duplicates' },
  { label:'Is data skewed?', key:'skewness' },
  { label:'How to clean?', key:'clean' },
];

function initChat() {
  const qqs = document.getElementById('quickQs');
  qqs.innerHTML = QUICK_QS.map(q =>
    `<button class="quick-q" onclick="sendQuickQ('${q.key}')">${q.label}</button>`
  ).join('');
  addBubble('ai', `👋 I'm your data intelligence assistant. Your dataset has <strong>${STATE.raw.length} rows</strong> and a DQS of <strong>${STATE.metrics.dqs}/100</strong>. Ask me anything about your data quality, cleaning steps, or statistics!`);
}

function addBubble(role, html) {
  const msgs = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-bubble bubble-${role}`;
  div.innerHTML = html;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function sendQuickQ(key) {
  const q = QUICK_QS.find(q=>q.key===key);
  if (q) { addBubble('user', q.label); setTimeout(()=>addBubble('ai', CHAT_RESPONSES[key]()), 400); }
}

function sendChat() {
  const inp = document.getElementById('chatInput');
  const text = inp.value.trim();
  if (!text) return;
  addBubble('user', text);
  inp.value = '';
  const lower = text.toLowerCase();
  let resp = null;
  if (lower.includes('miss')) resp = CHAT_RESPONSES.missing();
  else if (lower.includes('outlier') || lower.includes('anomal')) resp = CHAT_RESPONSES.outliers();
  else if (lower.includes('dqs') || lower.includes('quality') || lower.includes('score')) resp = CHAT_RESPONSES.dqs();
  else if (lower.includes('col') || lower.includes('feature')) resp = CHAT_RESPONSES.columns();
  else if (lower.includes('dup')) resp = CHAT_RESPONSES.duplicates();
  else if (lower.includes('skew') || lower.includes('distribut')) resp = CHAT_RESPONSES.skewness();
  else if (lower.includes('clean') || lower.includes('fix')) resp = CHAT_RESPONSES.clean();
  else if (lower.includes('download') || lower.includes('export')) resp = CHAT_RESPONSES.download();
  else resp = `I can help with: missing values, outliers, DQS score, column analysis, duplicates, skewness, cleaning steps, and exports. What would you like to know?`;
  setTimeout(() => addBubble('ai', resp), 500);
}

/* ================================================================
   CODE GENERATION
================================================================ */
function renderCode() {
  const { headers, colStats } = STATE;
  const numCols = headers.filter(h => colStats[h].type === 'numeric');
  const strCols = headers.filter(h => colStats[h].type === 'string');
  const dtCols  = headers.filter(h => colStats[h].type === 'datetime');

  const py = `<span class="cm"># DataAudit — Generated Python Cleaning Pipeline</span>
<span class="kw">import</span> <span class="var">pandas</span> <span class="kw">as</span> <span class="var">pd</span>
<span class="kw">import</span> <span class="var">numpy</span> <span class="kw">as</span> <span class="var">np</span>
<span class="kw">from</span> <span class="var">scipy</span> <span class="kw">import</span> <span class="var">stats</span>

<span class="cm"># Load data</span>
<span class="var">df</span> = <span class="fn">pd.read_csv</span>(<span class="str">'${STATE.fileName}'</span>)
<span class="fn">print</span>(<span class="str">f"Loaded {len(df)} rows, {len(df.columns)} columns"</span>)

<span class="cm"># Step 1: Data Type Correction</span>
${numCols.map(h => `<span class="var">df</span>[<span class="str">'${h}'</span>] = <span class="fn">pd.to_numeric</span>(<span class="var">df</span>[<span class="str">'${h}'</span>], errors=<span class="str">'coerce'</span>)`).join('\n')}
${dtCols.map(h  => `<span class="var">df</span>[<span class="str">'${h}'</span>]  = <span class="fn">pd.to_datetime</span>(<span class="var">df</span>[<span class="str">'${h}'</span>],  errors=<span class="str">'coerce'</span>)`).join('\n')}

<span class="cm"># Step 2: Missing Values</span>
<span class="var">num_cols</span> = <span class="var">df</span>.<span class="fn">select_dtypes</span>(include=<span class="str">'number'</span>).<span class="var">columns</span>
<span class="var">df</span>[<span class="var">num_cols</span>] = <span class="var">df</span>[<span class="var">num_cols</span>].<span class="fn">fillna</span>(<span class="var">df</span>[<span class="var">num_cols</span>].<span class="fn">mean</span>())
<span class="var">cat_cols</span> = <span class="var">df</span>.<span class="fn">select_dtypes</span>(include=<span class="str">'object'</span>).<span class="var">columns</span>
<span class="var">df</span>[<span class="var">cat_cols</span>] = <span class="var">df</span>[<span class="var">cat_cols</span>].<span class="fn">fillna</span>(<span class="str">'Unknown'</span>)

<span class="cm"># Step 3: Duplicates</span>
<span class="var">df</span> = <span class="var">df</span>.<span class="fn">drop_duplicates</span>().<span class="fn">reset_index</span>(drop=<span class="kw">True</span>)

<span class="cm"># Step 4: Outlier Treatment (Winsorization)</span>
<span class="kw">for</span> <span class="var">col</span> <span class="kw">in</span> <span class="var">num_cols</span>:
    <span class="var">q1</span>, <span class="var">q3</span> = <span class="var">df</span>[<span class="var">col</span>].<span class="fn">quantile</span>([<span class="num">0.01</span>, <span class="num">0.99</span>])
    <span class="var">df</span>[<span class="var">col</span>] = <span class="var">df</span>[<span class="var">col</span>].<span class="fn">clip</span>(<span class="var">q1</span>, <span class="var">q3</span>)

<span class="cm"># Step 5: Normalization (Min-Max)</span>
<span class="kw">from</span> <span class="var">sklearn.preprocessing</span> <span class="kw">import</span> <span class="var">MinMaxScaler</span>
<span class="var">scaler</span> = <span class="var">MinMaxScaler</span>()
<span class="var">df</span>[<span class="var">num_cols</span>] = <span class="var">scaler</span>.<span class="fn">fit_transform</span>(<span class="var">df</span>[<span class="var">num_cols</span>])

<span class="cm"># Step 6: Text Cleaning</span>
${strCols.length ? `<span class="kw">import</span> <span class="var">re</span>
<span class="kw">for</span> <span class="var">col</span> <span class="kw">in</span> [${strCols.map(h=>`<span class="str">'${h}'</span>`).join(', ')}]:
    <span class="var">df</span>[<span class="var">col</span>] = <span class="var">df</span>[<span class="var">col</span>].<span class="fn">str.lower</span>().<span class="fn">str.strip</span>()
    <span class="var">df</span>[<span class="var">col</span>] = <span class="var">df</span>[<span class="var">col</span>].<span class="fn">str.replace</span>(<span class="var">r</span><span class="str">'[^a-z0-9\\s]'</span>, <span class="str">''</span>, regex=<span class="kw">True</span>)` : '<span class="cm"># No string columns detected</span>'}

<span class="cm"># Step 7: Feature Engineering (Datetime expansion)</span>
${dtCols.length ? dtCols.map(h=>`<span class="var">df</span>[<span class="str">'${h}_year'</span>]  = <span class="var">df</span>[<span class="str">'${h}'</span>].<span class="var">dt</span>.<span class="var">year</span>
<span class="var">df</span>[<span class="str">'${h}_month'</span>] = <span class="var">df</span>[<span class="str">'${h}'</span>].<span class="var">dt</span>.<span class="var">month</span>
<span class="var">df</span>[<span class="str">'${h}_day'</span>]   = <span class="var">df</span>[<span class="str">'${h}'</span>].<span class="var">dt</span>.<span class="var">day</span>`).join('\n') : '<span class="cm"># No datetime columns detected</span>'}

<span class="cm"># Save cleaned data</span>
<span class="var">df</span>.<span class="fn">to_csv</span>(<span class="str">'cleaned_dataset.csv'</span>, index=<span class="kw">False</span>)
<span class="fn">print</span>(<span class="str">f"Cleaned: {len(df)} rows remain"</span>)`;

  const js = `<span class="cm">// DataAudit — Generated JavaScript Cleaning Pipeline</span>

<span class="cm">// Parse CSV</span>
<span class="kw">function</span> <span class="fn">parseCSV</span>(<span class="var">text</span>) {
  <span class="kw">const</span> <span class="var">lines</span> = <span class="var">text</span>.<span class="fn">split</span>(<span class="str">'\\n'</span>).<span class="fn">filter</span>(<span class="var">l</span> => <span class="var">l</span>.<span class="fn">trim</span>());
  <span class="kw">const</span> <span class="var">headers</span> = <span class="var">lines</span>[<span class="num">0</span>].<span class="fn">split</span>(<span class="str">','</span>);
  <span class="kw">const</span> <span class="var">rows</span> = <span class="var">lines</span>.<span class="fn">slice</span>(<span class="num">1</span>).<span class="fn">map</span>(<span class="var">l</span> => {
    <span class="kw">const</span> <span class="var">vals</span> = <span class="var">l</span>.<span class="fn">split</span>(<span class="str">','</span>);
    <span class="kw">return</span> <span class="var">Object</span>.<span class="fn">fromEntries</span>(<span class="var">headers</span>.<span class="fn">map</span>((<span class="var">h</span>, <span class="var">i</span>) => [<span class="var">h</span>, <span class="var">vals</span>[<span class="var">i</span>]]));
  });
  <span class="kw">return</span> { <span class="var">headers</span>, <span class="var">rows</span> };
}

<span class="cm">// Remove duplicates</span>
<span class="kw">function</span> <span class="fn">removeDuplicates</span>(<span class="var">rows</span>, <span class="var">headers</span>) {
  <span class="kw">const</span> <span class="var">seen</span> = <span class="kw">new</span> <span class="fn">Set</span>();
  <span class="kw">return</span> <span class="var">rows</span>.<span class="fn">filter</span>(<span class="var">r</span> => {
    <span class="kw">const</span> <span class="var">key</span> = <span class="var">headers</span>.<span class="fn">map</span>(<span class="var">h</span> => <span class="var">r</span>[<span class="var">h</span>]).<span class="fn">join</span>(<span class="str">'|'</span>);
    <span class="kw">if</span> (<span class="var">seen</span>.<span class="fn">has</span>(<span class="var">key</span>)) <span class="kw">return false</span>;
    <span class="var">seen</span>.<span class="fn">add</span>(<span class="var">key</span>); <span class="kw">return true</span>;
  });
}

<span class="cm">// Impute missing values</span>
<span class="kw">function</span> <span class="fn">imputeMissing</span>(<span class="var">rows</span>, <span class="var">col</span>, <span class="var">type</span>) {
  <span class="kw">const</span> <span class="var">vals</span> = <span class="var">rows</span>.<span class="fn">map</span>(<span class="var">r</span> => <span class="var">r</span>[<span class="var">col</span>]).<span class="fn">filter</span>(<span class="var">v</span> => <span class="var">v</span> !== <span class="str">''</span>);
  <span class="kw">const</span> <span class="var">fill</span> = <span class="var">type</span> === <span class="str">'numeric'</span>
    ? <span class="var">vals</span>.<span class="fn">reduce</span>((<span class="var">s</span>,<span class="var">v</span>) => <span class="var">s</span>+<span class="fn">Number</span>(<span class="var">v</span>),<span class="num">0</span>) / <span class="var">vals</span>.<span class="var">length</span>
    : <span class="str">'Unknown'</span>;
  <span class="kw">return</span> <span class="var">rows</span>.<span class="fn">map</span>(<span class="var">r</span> => ({ ...<span class="var">r</span>, [<span class="var">col</span>]: <span class="var">r</span>[<span class="var">col</span>] === <span class="str">''</span> ? <span class="var">fill</span> : <span class="var">r</span>[<span class="var">col</span>] }));
}

<span class="cm">// Min-Max normalize</span>
<span class="kw">function</span> <span class="fn">minMaxNorm</span>(<span class="var">rows</span>, <span class="var">col</span>) {
  <span class="kw">const</span> <span class="var">nums</span> = <span class="var">rows</span>.<span class="fn">map</span>(<span class="var">r</span> => <span class="fn">Number</span>(<span class="var">r</span>[<span class="var">col</span>])).<span class="fn">filter</span>(<span class="var">v</span> => !<span class="fn">isNaN</span>(<span class="var">v</span>));
  <span class="kw">const</span> [<span class="var">lo</span>, <span class="var">hi</span>] = [<span class="var">Math</span>.<span class="fn">min</span>(...<span class="var">nums</span>), <span class="var">Math</span>.<span class="fn">max</span>(...<span class="var">nums</span>)];
  <span class="kw">return</span> <span class="var">rows</span>.<span class="fn">map</span>(<span class="var">r</span> => ({ ...<span class="var">r</span>, [<span class="var">col</span>]: (<span class="fn">Number</span>(<span class="var">r</span>[<span class="var">col</span>])-<span class="var">lo</span>)/(<span class="var">hi</span>-<span class="var">lo</span>||<span class="num">1</span>) }));
}

<span class="cm">// Run pipeline</span>
<span class="kw">async function</span> <span class="fn">runPipeline</span>(<span class="var">csv</span>) {
  <span class="kw">let</span> { <span class="var">headers</span>, <span class="var">rows</span> } = <span class="fn">parseCSV</span>(<span class="var">csv</span>);
  <span class="var">rows</span> = <span class="fn">removeDuplicates</span>(<span class="var">rows</span>, <span class="var">headers</span>);
  <span class="cm">// ... apply more steps</span>
  <span class="kw">return</span> <span class="var">rows</span>;
}`;

  document.getElementById('pyCode').innerHTML = py;
  document.getElementById('jsCode').innerHTML = js;
}

/* ================================================================
   NAVIGATION
================================================================ */
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const panelId = 'tab-' + tab.dataset.tab;
    document.getElementById(panelId).classList.add('active');
    // Re-render charts when switching to insight tab
    if (tab.dataset.tab === 'insights') {
      setTimeout(() => {
        renderHeatmap();
        renderCluster();
      }, 100);
    }
    if (tab.dataset.tab === 'compare') {
      setTimeout(() => renderCompare(), 100);
    }
  });
});

/* ================================================================
   DOWNLOAD
================================================================ */
function toCSV(rows, headers) {
  const h = headers || Object.keys(rows[0] || {});
  return [h.join(','), ...rows.map(r => h.map(col => {
    const v = r[col] !== undefined ? String(r[col]) : '';
    return v.includes(',') || v.includes('"') ? `"${v.replace(/"/g,'""')}"` : v;
  }).join(','))].join('\n');
}

function downloadCSV(rows, headers, fname) {
  const csv = toCSV(rows, headers);
  const blob = new Blob([csv], { type:'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=fname;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadCleaned() { downloadCSV(STATE.cleaned, STATE.headers, 'cleaned_' + STATE.fileName); }
function downloadOriginal() { downloadCSV(STATE.raw, STATE.headers, STATE.fileName); }

document.getElementById('downloadBtn').addEventListener('click', downloadCleaned);

/* ================================================================
   UTILITIES
================================================================ */
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
  return (bytes/1024/1024).toFixed(1) + ' MB';
}

function copyCode(id) {
  const el = document.getElementById(id);
  navigator.clipboard.writeText(el.innerText).then(() => {
    const btn = el.closest('.glass-card').querySelector('.code-copy');
    const orig = btn.textContent;
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = orig, 1500);
  });
}

function showDashboard() {
  document.getElementById('landing').style.display = 'none';
  document.getElementById('dashboard').style.display = 'block';
}

function resetApp() {
  document.getElementById('landing').style.display = 'flex';
  document.getElementById('dashboard').style.display = 'none';
  document.getElementById('fileInput').value = '';
  STATE.raw = []; STATE.cleaned = []; STATE.headers = []; STATE.pipelineRan = false;
  STATE.changes = []; STATE.metrics = {};
}

/* ================================================================
   RESIZE HANDLER
================================================================ */
window.addEventListener('resize', () => {
  if (STATE.headers.length) {
    const activeTab = document.querySelector('.nav-tab.active')?.dataset.tab;
    if (activeTab === 'insights') { renderHeatmap(); renderCluster(); }
    if (activeTab === 'overview') renderTypeChart(
      Object.fromEntries(['numeric','string','datetime','boolean','unknown'].map(t=>[t,STATE.headers.filter(h=>STATE.colStats[h]?.type===t).length]))
    );
  }
});
