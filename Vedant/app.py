
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import re, json, io, pathlib
import streamlit.components.v1 as components

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Audit System",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load frontend assets ───────────────────────────────────────────────
BASE   = pathlib.Path(__file__).parent / "frontend"
CSS    = (BASE / "style.css").read_text(encoding="utf-8")
THREEJS= (BASE / "threejs.html").read_text(encoding="utf-8")

# Inject CSS
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# Inject Three.js + all JS (uses components.html so scripts actually execute)
components.html(THREEJS, height=0, scrolling=False)

# ══════════════════════════════════════════════════════════════════════
#  CHART THEME
# ══════════════════════════════════════════════════════════════════════
def chart_theme():
    plt.rcParams.update({
        "figure.facecolor": "#06090f", "axes.facecolor": "#020408",
        "axes.edgecolor":   "#1a2540", "axes.labelcolor": "#4a5a8a",
        "axes.titlecolor":  "#dce8ff", "axes.titlesize": 10, "axes.titleweight": "600",
        "axes.labelsize":   8,         "xtick.color": "#4a5a8a", "ytick.color": "#4a5a8a",
        "xtick.labelsize":  7.5,       "ytick.labelsize": 7.5, "text.color": "#dce8ff",
        "grid.color":       "#0c1220", "grid.linestyle": "-",
        "axes.grid": True,  "axes.grid.axis": "y",
        "axes.spines.top":  False,     "axes.spines.right": False,
        "axes.spines.left": False,     "axes.spines.bottom": True,
        "font.family":      "sans-serif", "figure.dpi": 150,
    })

PAL = ["#3d7fff","#8b5cf6","#10b981","#f59e0b","#ef4444",
       "#06b6d4","#ec4899","#34d399","#fb923c","#a3e635"]

# ══════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════════
def mc(label, val, sub="", accent="#3d7fff", delay=0):
    st.markdown(f"""
    <div class="mc" style="animation-delay:{delay}s">
      <div class="mc-bar" style="background:{accent}"></div>
      <div class="mc-label">{label}</div>
      <div class="mc-value" style="color:{accent}">{val}</div>
      {'<div class="mc-sub">'+sub+'</div>' if sub else ''}
    </div>""", unsafe_allow_html=True)

def sec(icon, title, sub=""):
    st.markdown(f"""
    <div class="stitle">
      <span style="font-size:1.1rem">{icon}</span>
      <div>
        <div class="stitle-main">{title}</div>
        {'<div class="stitle-sub">'+sub+'</div>' if sub else ''}
      </div>
      <div class="stitle-line"></div>
    </div>""", unsafe_allow_html=True)

def rfind(dot, html, delay=0):
    st.markdown(f"""
    <div class="finding" style="animation-delay:{delay}s">
      <div class="finding-dot" style="background:{dot};box-shadow:0 0 8px {dot}66"></div>
      <div>{html}</div>
    </div>""", unsafe_allow_html=True)

def dqs_grade(s):
    if s >= 85: return "#10b981", "A", "Excellent"
    if s >= 70: return "#06b6d4", "B", "Good"
    if s >= 55: return "#f59e0b", "C", "Moderate"
    if s >= 40: return "#fb923c", "D", "Poor"
    return "#ef4444", "F", "Critical"

# ══════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in [("df", None), ("meta", {}), ("audit", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════
#  NAVBAR
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="nav">
  <div class="nav-logo">
    <div class="nav-icon">◈</div>
    <div>
      <div class="nav-title">Data Audit System</div>
      <div class="nav-sub">Professional Data Quality Analysis</div>
    </div>
  </div>
  <div class="nav-right">
    <span class="nav-ver">v3.0</span>
    <div class="nav-badge"><div class="nav-dot"></div>System Ready</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  HERO + UPLOAD  (shown only when no file loaded)
# ══════════════════════════════════════════════════════════════════════
if st.session_state.df is None:
    st.markdown("""
    <div class="hero">
      <div class="hero-glow"></div>
      <div class="hero-grid"></div>
      <div class="hero-eyebrow">◈ &nbsp; Professional Data Auditing Platform</div>
      <div class="hero-title">Know your data.<br>Before it fails you.</div>
      <div class="hero-sub">
        Drop any CSV or Excel file — instant comprehensive quality audit,
        weighted Dataset Quality Score, stunning visualizations, and
        actionable fix recommendations.
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("", type=["csv", "xlsx"],
                                label_visibility="collapsed",
                                help="CSV or XLSX · up to 1 GB")

    # Particle burst on upload
    if uploaded:
        components.html("""<script>
        setTimeout(function(){
          if(parent.window._burst){
            parent.window._burst(parent.window.innerWidth/2,   parent.window.innerHeight/2);
            parent.window._burst(parent.window.innerWidth/2-100, parent.window.innerHeight/2+50);
            parent.window._burst(parent.window.innerWidth/2+100, parent.window.innerHeight/2+50);
          }
        }, 200);
        </script>""", height=0)
        with st.spinner("Parsing dataset…"):
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") \
                     else pd.read_excel(uploaded)
                st.session_state.df   = df
                st.session_state.meta = {"name": uploaded.name, "size": uploaded.size}
                st.session_state.audit = None
                st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")

    st.markdown("""
    <div class="features">
      <div class="feat"><span class="feat-i">🎯</span>
        <div class="feat-t">Quality Score</div>
        <div class="feat-d">Weighted DQS across 7 dimensions with animated ring + grade A–F</div>
      </div>
      <div class="feat"><span class="feat-i">🔬</span>
        <div class="feat-t">Deep Fault Detection</div>
        <div class="feat-d">Nulls, outliers, duplicates, encoding, type errors — all flagged</div>
      </div>
      <div class="feat"><span class="feat-i">🌐</span>
        <div class="feat-t">Live Sparklines</div>
        <div class="feat-d">Animated Canvas charts showing column distributions at a glance</div>
      </div>
      <div class="feat"><span class="feat-i">📥</span>
        <div class="feat-t">Audit Report CSV</div>
        <div class="feat-d">Download every issue with severity, example values and fix code</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Re-upload expander ─────────────────────────────────────────────────
with st.expander("⬆  Upload a different file"):
    nf = st.file_uploader("", type=["csv", "xlsx"],
                          label_visibility="collapsed", key="reup")
    if nf:
        try:
            df2 = pd.read_csv(nf) if nf.name.endswith(".csv") else pd.read_excel(nf)
            st.session_state.df    = df2
            st.session_state.meta  = {"name": nf.name, "size": nf.size}
            st.session_state.audit = None
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

df   = st.session_state.df
meta = st.session_state.meta
mem_kb = df.memory_usage(deep=True).sum() / 1024

# ── File banner ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <div style="display:flex;align-items:center;gap:.85rem">
    <div class="banner-icon">📁</div>
    <div>
      <div style="font-size:.9rem;font-weight:700;color:var(--t);font-family:'Syne',sans-serif">{meta.get('name','dataset')}</div>
      <div style="font-size:.68rem;color:var(--t2);margin-top:.1rem">{meta.get('size',0)/1024:.1f} KB on disk</div>
    </div>
  </div>
  <div style="display:flex;gap:.4rem;flex-wrap:wrap">
    <span class="tag" style="background:rgba(61,127,255,.1);border:1px solid rgba(61,127,255,.22);color:#7aafff">{df.shape[0]:,} rows</span>
    <span class="tag" style="background:rgba(61,127,255,.1);border:1px solid rgba(61,127,255,.22);color:#7aafff">{df.shape[1]} cols</span>
    <span class="tag" style="background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.22);color:#c4b5fd">{df.dtypes.nunique()} dtypes</span>
    <span class="tag" style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);color:#6ee7b7">{mem_kb:.1f} KB</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  AUDIT ENGINE
# ══════════════════════════════════════════════════════════════════════
if st.session_state.audit is None:
    import time
    prog = st.progress(0, "Initialising…")
    PH   = {"n/a","na","none","null","nil","-","--","?","unknown",
            "undefined","missing","tbd","tbc","#n/a"}

    # Completeness
    prog.progress(10, "Checking completeness…")
    nc = df.isnull().sum().sum(); es = ph = 0
    for c in df.select_dtypes("object").columns:
        v  = df[c].dropna().astype(str)
        es += (v.str.strip() == "").sum()
        ph += v.str.strip().str.lower().isin(PH).sum()
    tm = nc + es + ph; mr = tm / max(1, df.shape[0] * df.shape[1])
    s1 = max(0, 100 - mr * 100 * 1.5)

    # Uniqueness
    prog.progress(22, "Checking uniqueness…")
    ed = df.duplicated().sum(); dc = []
    cols = list(df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if df[cols[i]].equals(df[cols[j]]): dc.append((cols[i], cols[j]))
    cc = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    s2 = max(0, 100 - ed / len(df) * 100 * 2)

    # Consistency
    prog.progress(36, "Checking consistency…")
    mx, ca, en = [], [], []
    for c in df.select_dtypes("object").columns:
        v = df[c].dropna()
        if not len(v): continue
        n = pd.to_numeric(v, errors="coerce").notnull().sum()
        s = v.astype(str).str.match(r"^[A-Za-z]").sum()
        if 0 < n < len(v) and s > 0: mx.append(c)
        if df[c].nunique() <= 100:
            if v.astype(str).str.strip().str.lower().nunique() < v.astype(str).str.strip().nunique(): ca.append(c)
        if v.astype(str).str.contains(r"[^\x00-\x7F]|â€|Ã©", regex=True, na=False).sum() > 0: en.append(c)
    s3 = max(0, 100 - (len(mx) + len(ca) + len(en)) / df.shape[1] * 100 * 1.8)

    # Validity
    prog.progress(50, "Checking validity…")
    oc, im = [], []
    for c in df.select_dtypes("number").columns:
        d = df[c].dropna()
        if len(d) < 4: continue
        Q1, Q3 = d.quantile(.25), d.quantile(.75); IQR = Q3 - Q1
        if IQR > 0:
            no = ((d < Q1 - 3*IQR) | (d > Q3 + 3*IQR)).sum()
            if no > 0: oc.append({"col": c, "count": int(no)})
        cl = c.lower()
        if any(k in cl for k in ["age","years"]) and ((d<0)|(d>150)).sum(): im.append(c)
        if any(k in cl for k in ["price","salary","cost","amount"]) and (d<0).sum(): im.append(c)
        if any(k in cl for k in ["percent","pct","rate"]) and ((d<0)|(d>100)).sum(): im.append(c)
    nuc = sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
    s4  = max(0, 100 - sum(o["count"] for o in oc)/max(1,nuc)*60 - len(im)/max(1,len(df))*100)

    # Accuracy
    prog.progress(64, "Checking accuracy…")
    sk, ib = [], []
    for c in df.select_dtypes("number").columns:
        sv = df[c].dropna().skew()
        if abs(sv) > 2: sk.append({"col": c, "skew": round(float(sv), 3)})
    for c in df.select_dtypes("object").columns:
        vc = df[c].value_counts(normalize=True)
        if len(vc) >= 2 and float(vc.iloc[0]) > 0.85: ib.append(c)
    cn = df.select_dtypes("object").shape[1]
    s5 = max(0, 100 - sum(min(abs(x["skew"])/20, .05) for x in sk)*100
                    - (len(ib)/cn*20 if cn > 0 else 0))

    # Structure
    prog.progress(78, "Checking structure…")
    bn, wt = [], []; er = int(df.isnull().all(axis=1).sum())
    for c in df.columns:
        sv = str(c)
        if sv.strip() == "" or re.match(r"^Unnamed", sv) or re.search(r"[^a-zA-Z0-9_ ]", sv): bn.append(c)
    for c in df.select_dtypes("object").columns:
        if pd.to_numeric(df[c], errors="coerce").notnull().mean() > 0.95: wt.append(c)
    s6 = max(0, 100 - (len(bn)+len(wt))/df.shape[1]*30 - (10 if df.shape[0]/df.shape[1] < 5 else 0))

    # Correlation
    prog.progress(90, "Checking correlations…")
    hc = []
    nd = df.select_dtypes("number").dropna(axis=1, how="all")
    if nd.shape[1] >= 2:
        cr = nd.corr().abs(); cc2 = cr.columns
        for i in range(len(cc2)):
            for j in range(i+1, len(cc2)):
                r = float(cr.iloc[i, j])
                if r > 0.95: hc.append({"a": cc2[i], "b": cc2[j], "r": round(r, 4)})
    s7 = max(0, 100 - len(hc) * 3)

    # Final DQS
    W = {"Completeness":.28,"Uniqueness":.18,"Consistency":.16,"Validity":.16,
         "Accuracy":.10,"Structure":.07,"Correlation":.05}
    S = {"Completeness":s1,"Uniqueness":s2,"Consistency":s3,"Validity":s4,
         "Accuracy":s5,"Structure":s6,"Correlation":s7}
    raw = sum(W[k]*S[k] for k in W)
    sf  = max(0.5, min(1.0, np.log10(len(df)+1)/4.0))
    db  = min(1.05, 1 + (df.dtypes.nunique()-1)*0.01)
    DQS = round(min(100, max(0, raw*sf*db)), 2)

    time.sleep(.3); prog.progress(100, "✓ Audit complete"); time.sleep(.4); prog.empty()
    st.success(f"✓  Full audit complete — {len(W)} quality dimensions analysed")

    st.session_state.audit = dict(
        DQS=DQS, raw=raw, sf=sf, db=db, W=W, S=S,
        nc=nc, es=es, ph=ph, tm=tm, mr=mr,
        ed=ed, dc=dc, cc=cc, mx=mx, ca=ca, en=en,
        oc=oc, im=im, sk=sk, ib=ib, bn=bn, wt=wt,
        er=er, hc=hc,
    )

A = st.session_state.audit
chart_theme()

# ══════════════════════════════════════════════════════════════════════
#  §1  DQS + ANIMATED RING + KPIs
# ══════════════════════════════════════════════════════════════════════
sec("◈", "Dataset Quality Score", "Animated score ring · 7 weighted dimensions · Grade A–F")

dqs_clr, grade, grade_lbl = dqs_grade(A["DQS"])
null_pct   = round(A["tm"] / (df.shape[0]*df.shape[1]) * 100, 2)
complete_p = round(df.dropna().shape[0] / len(df) * 100, 1)

col_dqs, col_kpis = st.columns([1, 2.6], gap="large")

with col_dqs:
    st.markdown(f"""
    <div class="dqs-card holo">
      <div class="dqs-glow" style="background:radial-gradient(ellipse,{dqs_clr}35 0%,transparent 65%)"></div>
      <div class="dqs-eyebrow">Dataset Quality Score</div>
      <div id="score-ring-container" style="position:relative;width:180px;height:180px;margin:0 auto .8rem">
        <canvas id="score-ring-canvas" width="360" height="360"
                style="width:180px;height:180px;position:absolute;top:0;left:0"></canvas>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
          <div style="font-family:'Syne',sans-serif;font-size:3.2rem;font-weight:800;color:{dqs_clr};line-height:1">{A['DQS']}</div>
          <div style="font-size:.62rem;color:var(--t3);font-family:'JetBrains Mono',monospace">/100</div>
        </div>
      </div>
      <div class="dqs-pill" style="background:{dqs_clr}18;border:1px solid {dqs_clr}44;color:{dqs_clr}">
        Grade {grade} &nbsp;·&nbsp; {grade_lbl}
      </div>
      <hr class="dqs-divider">
      <div class="dqs-row"><span>Raw weighted</span><b>{A['raw']:.3f}</b></div>
      <div class="dqs-row"><span>Size factor</span><b>{A['sf']:.3f}</b></div>
      <div class="dqs-row"><span>Diversity bonus</span><b>{A['db']:.4f}</b></div>
      <div class="dqs-row"><span>Missing cells</span><b>{A['tm']:,}</b></div>
      <div class="dqs-row"><span>Duplicate rows</span><b>{A['ed']:,}</b></div>
    </div>""", unsafe_allow_html=True)

    components.html(f"""<script>
    setTimeout(function(){{
      if(parent.window._drawRing) parent.window._drawRing({A['DQS']}, '{dqs_clr}');
    }}, 600);
    </script>""", height=0)

with col_kpis:
    num_cols_spark = df.select_dtypes(include=np.number).columns.tolist()
    if num_cols_spark:
        spark_cols = st.columns(min(4, len(num_cols_spark)), gap="small")
        for i, col_name in enumerate(num_cols_spark[:4]):
            data_spark  = df[col_name].dropna().sample(min(60, df[col_name].dropna().shape[0])).tolist()
            color_spark = PAL[i % len(PAL)]
            canvas_id   = f"spark_{i}"
            with spark_cols[i]:
                st.markdown(f"""
                <div class="spark-wrap">
                  <div style="font-size:.6rem;font-weight:700;text-transform:uppercase;
                              letter-spacing:.09em;color:var(--t2);margin-bottom:.3rem">{col_name[:14]}</div>
                  <canvas id="{canvas_id}" width="200" height="50"
                          style="width:100%;height:50px"></canvas>
                  <div style="display:flex;justify-content:space-between;margin-top:.3rem;
                              font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--t3)">
                    <span>μ {df[col_name].mean():.2f}</span>
                    <span>σ {df[col_name].std():.2f}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
                components.html(f"""<script>
                setTimeout(function(){{
                  if(parent.window._sparkline)
                    parent.window._sparkline('{canvas_id}', {json.dumps([round(x,4) for x in data_spark])}, '{color_spark}');
                }}, 700);
                </script>""", height=0)

    st.markdown("<br>", unsafe_allow_html=True)
    r1 = st.columns(3, gap="small"); r2 = st.columns(3, gap="small")
    kdata = [
        ("Rows",          f"{df.shape[0]:,}",      "total records",          "#3d7fff"),
        ("Columns",       str(df.shape[1]),         "features",               "#8b5cf6"),
        ("Missing Cells", f"{A['tm']:,}",           f"{null_pct}% of data",   "#ef4444" if A["tm"]>0 else "#10b981"),
        ("Duplicates",    str(A["ed"]),             "exact row copies",       "#ef4444" if A["ed"]>0 else "#10b981"),
        ("Outlier Cols",  str(len(A["oc"])),        "columns affected",       "#f59e0b" if A["oc"] else "#10b981"),
        ("Complete Rows", f"{complete_p}%",         "rows with no nulls",     "#10b981" if complete_p>90 else "#f59e0b"),
    ]
    for i, (cols, kd) in enumerate([(r1, kdata[:3]), (r2, kdata[3:])]):
        for col, k in zip(cols, kd):
            with col: mc(k[0], k[1], k[2], k[3], delay=i*0.08)

# ══════════════════════════════════════════════════════════════════════
#  §2  DIMENSION BREAKDOWN
# ══════════════════════════════════════════════════════════════════════
sec("📐", "Score Breakdown", "7 quality dimensions · each scored 0–100 with animated bar")

DIM_C = {"Completeness":"#3d7fff","Uniqueness":"#8b5cf6","Consistency":"#10b981",
         "Validity":"#06b6d4","Accuracy":"#f59e0b","Structure":"#ec4899","Correlation":"#34d399"}
DIM_I = {"Completeness":"🕳️","Uniqueness":"🪞","Consistency":"🔀",
         "Validity":"📐","Accuracy":"📉","Structure":"🏗️","Correlation":"🔗"}

cols7 = st.columns(7, gap="small")
for i, (dim, score) in enumerate(A["S"].items()):
    clr = DIM_C[dim]; wt = int(A["W"][dim]*100)
    with cols7[i]:
        st.markdown(f"""
        <div class="dim" style="animation-delay:{i*.06}s">
          <div class="dim-bot" style="background:{clr}"></div>
          <span class="dim-icon">{DIM_I[dim]}</span>
          <div class="dim-name">{dim}</div>
          <div class="dim-score" style="color:{clr}">{score:.0f}</div>
          <div class="dim-denom">/ 100</div>
          <div class="dim-bar">
            <div class="dim-fill" style="width:{score}%;background:{clr};--w:{score}%"></div>
          </div>
          <div class="dim-wt">{wt}% weight</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  §3  KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════
sec("💡", "Key Findings", "Auto-detected issues with inline code-level fix recommendations")

fl = []
if A["tm"]>0: fl.append(("#ef4444", f"<strong>{A['tm']:,} missing values</strong> — {null_pct}% of all cells. {A['nc']:,} true nulls + {A['ph']:,} placeholders like <code>N/A</code>, <code>unknown</code>."))
if A["ed"]>0: fl.append(("#ef4444", f"<strong>{A['ed']:,} exact duplicate rows</strong> — use <code>df.drop_duplicates()</code>."))
if A["oc"]:
    nm = " · ".join(f"<code>{o['col']}</code> ({o['count']} pts)" for o in A["oc"][:4])
    fl.append(("#f59e0b", f"<strong>Extreme outliers (3×IQR)</strong> in {len(A['oc'])} column(s): {nm}"))
if A["sk"]:
    nm = " · ".join(f"<code>{s['col']}</code> ({s['skew']:+})" for s in A["sk"][:4])
    fl.append(("#f59e0b", f"<strong>Highly skewed</strong> (|skew|>2): {nm}. Apply <code>np.log1p()</code>."))
if A["mx"]: fl.append(("#ef4444", f"<strong>Mixed-type columns</strong>: {' · '.join('<code>'+c+'</code>' for c in A['mx'][:5])}."))
if A["ca"]: fl.append(("#f59e0b", f"<strong>Case inconsistency</strong> in {len(A['ca'])} column(s). Use <code>.str.lower().str.strip()</code>."))
if A["hc"]:
    p = A["hc"][0]
    fl.append(("#06b6d4", f"<strong>{len(A['hc'])} correlated pair(s)</strong> (r>0.95): <code>{p['a']}</code> ↔ <code>{p['b']}</code> (r={p['r']})."))
if A["cc"]: fl.append(("#8b5cf6", f"<strong>Zero-variance columns</strong>: {' · '.join('<code>'+c+'</code>' for c in A['cc'][:5])}."))
if A["ib"]: fl.append(("#f59e0b", f"<strong>Imbalanced categoricals</strong> >85%: {', '.join(A['ib'][:4])}."))
if not fl:  fl.append(("#10b981", "🎉 <strong>No major issues detected.</strong> Your dataset is clean and well-structured!"))

for i, (d, h) in enumerate(fl):
    rfind(d, h, delay=i*0.04)

# ══════════════════════════════════════════════════════════════════════
#  §4  COLUMN HEALTH GRID
# ══════════════════════════════════════════════════════════════════════
sec("🩺", "Column Health Grid", "Per-column health score — null rate, type, uniqueness at a glance")

health_rows = []
for c in df.columns:
    null_r = df[c].isnull().mean() * 100
    uniq_r = df[c].nunique() / len(df) * 100
    score  = max(0, 100 - null_r*2 - (10 if c in A["mx"] else 0) - (10 if c in A["ca"] else 0))
    health_rows.append({
        "Column":       c,
        "Dtype":        str(df[c].dtype),
        "Null %":       round(null_r, 2),
        "Unique %":     round(uniq_r, 2),
        "Health Score": round(score, 1),
    })
st.dataframe(pd.DataFrame(health_rows), use_container_width=True,
             height=min(420, 50 + len(health_rows)*38))

# ══════════════════════════════════════════════════════════════════════
#  §5  LIVE AUDIT LOG
# ══════════════════════════════════════════════════════════════════════
sec("📡", "Live Audit Log", "Real-time feed from the data analysis engine")

log_lines = [
    f'<span class="live-blue">[SYS]</span> &nbsp;Audit engine initialised · {df.shape[0]:,} rows × {df.shape[1]} cols',
    f'<span class="live-green">[OK]</span> &nbsp;Completeness → score <b>{A["S"]["Completeness"]:.1f}</b> · missing: {A["tm"]:,}',
    f'<span class="live-green">[OK]</span> &nbsp;Uniqueness → score <b>{A["S"]["Uniqueness"]:.1f}</b> · duplicates: {A["ed"]:,}',
]
if A["mx"]:  log_lines.append(f'<span class="live-red">[WARN]</span> Mixed-type columns → {", ".join(A["mx"][:3])}')
if A["oc"]:  log_lines.append(f'<span class="live-red">[WARN]</span> Outliers in {len(A["oc"])} column(s) via 3×IQR rule')
if A["sk"]:  log_lines.append(f'<span class="live-am">[INFO]</span> Skewed distributions → {len(A["sk"])} column(s) |skew|>2')
if A["hc"]:  log_lines.append(f'<span class="live-am">[INFO]</span> High correlation: {len(A["hc"])} pair(s) r>0.95')
log_lines.append(f'<span class="live-green">[OK]</span> &nbsp;DQS = <b style="color:#10b981">{A["DQS"]} / 100</b> · Grade <b>{dqs_grade(A["DQS"])[1]}</b>')
log_lines.append(f'<span class="live-blue">[SYS]</span> All {len(A["W"])} dimensions processed · report ready ↓')

st.markdown(f"""
<div class="live-feed">
{"".join(f'<div class="live-feed-line">{l}</div>' for l in log_lines)}
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  §6  DATA PREVIEW + STATS
# ══════════════════════════════════════════════════════════════════════
sec("🗂", "Data Preview", "Raw snapshot + column type audit")
cp, ct = st.columns([3, 2], gap="large")
with cp:
    st.markdown('<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--t2);margin-bottom:.55rem">First 8 rows</div>', unsafe_allow_html=True)
    st.dataframe(df.head(8), use_container_width=True, height=295)
with ct:
    st.markdown('<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--t2);margin-bottom:.55rem">Column types &amp; null rate</div>', unsafe_allow_html=True)
    tdf = pd.DataFrame({
        "Column":   df.columns,
        "Type":     df.dtypes.values,
        "Non-Null": df.notnull().sum().values,
        "Null %":   (df.isnull().mean()*100).round(2).values,
        "Unique":   df.nunique().values,
    })
    st.dataframe(tdf, use_container_width=True, height=295)

sec("📊", "Statistical Summary", "Full descriptive statistics for every column")
st.dataframe(df.describe(include="all").round(3), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
#  §7  VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════
num_cols = df.select_dtypes(include=np.number).columns.tolist()

if num_cols:
    # Distributions
    sec("📈", "Distributions", "Mean (red) · Median (green) · Skew & Kurtosis annotated")
    ns = min(9, len(num_cols)); show = num_cols[:ns]; nc2 = 3; nr = (len(show)+nc2-1)//nc2
    fig, axes = plt.subplots(nr, nc2, figsize=(14, 3.9*nr))
    axes = np.array(axes).flatten()
    from matplotlib.lines import Line2D
    for i, col in enumerate(show):
        ax = axes[i]; data = df[col].dropna(); clr = PAL[i % len(PAL)]
        ax.hist(data, bins=28, color=clr, alpha=.72, edgecolor="#020408", linewidth=.3)
        ax.axvline(data.mean(),   color="#ef4444", lw=1.5, ls="--", alpha=.9)
        ax.axvline(data.median(), color="#10b981", lw=1.5, ls=":",  alpha=.9)
        ax.set_title(col, fontsize=9.5, fontweight="600", pad=8)
        ax.set_ylabel("Count", fontsize=7)
        sk = data.skew(); ku = data.kurt()
        ax.text(.97,.96, f"skew {sk:+.2f}  kurt {ku:.2f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=6.5, color="#4a5a8a", fontfamily="monospace",
                bbox=dict(facecolor="#06090f", edgecolor="#1a2540", boxstyle="round,pad=.3", alpha=.92))
        ax.legend(handles=[
            Line2D([0],[0], color="#ef4444", ls="--", lw=1.5, label=f"μ {data.mean():.2f}"),
            Line2D([0],[0], color="#10b981", ls=":",  lw=1.5, label=f"M {data.median():.2f}"),
        ], fontsize=6.5, framealpha=0, labelcolor="#4a5a8a", loc="upper left")
    for j in range(len(show), len(axes)): axes[j].set_visible(False)
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)

    # Heatmap
    nd2 = df.select_dtypes(include=np.number)
    if nd2.shape[1] >= 2:
        sec("🌡️", "Correlation Matrix", "Pearson r · lower triangle")
        cr2 = nd2.corr(); n2 = cr2.shape[1]; fs = max(7, min(18, n2*1.1))
        fig, ax = plt.subplots(figsize=(fs, fs*.8))
        mask = np.triu(np.ones_like(cr2, dtype=bool))
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        sns.heatmap(cr2, mask=mask, annot=n2<=16, fmt=".2f", cmap=cmap, center=0, ax=ax,
                    linewidths=.5, linecolor="#020408",
                    annot_kws={"size":7.5,"weight":"600","color":"#dce8ff"},
                    cbar_kws={"shrink":.5}, square=True)
        ax.tick_params(axis="x", rotation=40, labelsize=8)
        ax.tick_params(axis="y", rotation=0,  labelsize=8)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)
        if n2 > 2:
            pairs = []
            for i in range(len(cr2.columns)):
                for j in range(i+1, len(cr2.columns)):
                    pairs.append({"Column A":cr2.columns[i],"Column B":cr2.columns[j],
                                  "Pearson r":round(cr2.iloc[i,j],4),
                                  "|r|":round(abs(cr2.iloc[i,j]),4)})
            pdf = pd.DataFrame(pairs).sort_values("|r|", ascending=False).drop("|r|", axis=1)
            with st.expander("📋 All correlation pairs — sorted by strength"):
                st.dataframe(pdf, use_container_width=True, height=320)

    # Boxplots
    sec("📦", "Boxplots", "IQR bounds · extreme outlier count per chart")
    nb = min(9, len(num_cols)); showb = num_cols[:nb]; nc3 = 3; nr2 = (len(showb)+nc3-1)//nc3
    fig, axes = plt.subplots(nr2, nc3, figsize=(14, 3.9*nr2))
    axes = np.array(axes).flatten()
    for i, col in enumerate(showb):
        ax = axes[i]; data = df[col].dropna(); clr = PAL[i % len(PAL)]
        bp = ax.boxplot(data, patch_artist=True, notch=False,
                        medianprops={"color":"#fff","linewidth":2.2},
                        flierprops={"marker":"o","markersize":3.5,"markerfacecolor":clr,"alpha":.6,"markeredgewidth":0},
                        whiskerprops={"linewidth":1.2,"color":"#4a5a8a"},
                        capprops={"linewidth":1.2,"color":"#4a5a8a"})
        for p in bp["boxes"]:
            p.set_facecolor(clr); p.set_alpha(.6); p.set_edgecolor(clr); p.set_linewidth(1.1)
        ax.set_title(col, fontsize=9.5, fontweight="600", pad=8); ax.set_xticks([])
        Q1, Q3 = data.quantile(.25), data.quantile(.75); IQR = Q3 - Q1
        no = int(((data < Q1-3*IQR)|(data > Q3+3*IQR)).sum()) if IQR > 0 else 0
        ax.text(.97,.04, f"IQR {IQR:.2f}  ·  {no} outlier{'s' if no!=1 else ''}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5,
                color="#4a5a8a", fontfamily="monospace",
                bbox=dict(facecolor="#06090f", edgecolor="#1a2540", boxstyle="round,pad=.3", alpha=.92))
    for j in range(len(showb), len(axes)): axes[j].set_visible(False)
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)

# Missing values
miss = df.isnull().sum(); miss_nz = miss[miss > 0]
sec("🕳️", "Missing Values", "Column-level completeness — count + rate charts")
mc1, mc2c, mc3, mc4 = st.columns(4, gap="small")
with mc1:  mc("Cols w/ Missing",  str(len(miss_nz)),    f"of {df.shape[1]}",    "#ef4444" if len(miss_nz)>0 else "#10b981")
with mc2c: mc("Total Missing",    f"{miss.sum():,}",    f"{miss.sum()/(df.shape[0]*df.shape[1])*100:.3f}%", "#ef4444" if miss.sum()>0 else "#10b981")
with mc3:  mc("Complete Rows",    f"{df.dropna().shape[0]:,}", f"{complete_p}% complete", "#10b981" if complete_p>90 else "#f59e0b")
with mc4:  mc("Placeholders",     str(A["ph"]),         "fake nulls",           "#f59e0b" if A["ph"]>0 else "#10b981")
st.markdown("<br>", unsafe_allow_html=True)

if miss_nz.empty:
    st.markdown("""<div class="empty-ok">
    <div style="font-size:1.8rem;margin-bottom:.5rem">✅</div>
    <div style="font-size:.95rem;font-weight:700;color:#10b981;font-family:'Syne',sans-serif">Perfect Completeness</div>
    <div style="font-size:.8rem;color:#6ee7b7;margin-top:.4rem">Every cell has a value. No imputation needed.</div>
    </div>""", unsafe_allow_html=True)
else:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(4, len(miss_nz)*.6+1.5)))
    colors = [PAL[i % len(PAL)] for i in range(len(miss_nz))]
    ax1.barh(miss_nz.index, miss_nz.values, color=colors, edgecolor="#020408", height=.65)
    ax1.set_title("Missing Count", fontsize=10, fontweight="600"); ax1.set_xlabel("Count"); ax1.invert_yaxis()
    for bar, val in zip(ax1.patches, miss_nz.values):
        ax1.text(bar.get_width()+miss_nz.max()*.015, bar.get_y()+bar.get_height()/2, f"{val:,}",
                 va="center", ha="left", fontsize=7, color="#4a5a8a", fontfamily="monospace")
    mp = (miss_nz / len(df) * 100).round(2)
    ax2.barh(mp.index, mp.values, color=colors, edgecolor="#020408", height=.65, alpha=.82)
    ax2.set_title("Missing Rate (%)", fontsize=10, fontweight="600"); ax2.set_xlabel("%"); ax2.invert_yaxis()
    for bar, val in zip(ax2.patches, mp.values):
        ax2.text(bar.get_width()+mp.max()*.015, bar.get_y()+bar.get_height()/2, f"{val}%",
                 va="center", ha="left", fontsize=7, color="#4a5a8a", fontfamily="monospace")
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)
    md = pd.DataFrame({"Column":miss_nz.index,"Missing":miss_nz.values,
                       "Missing %":(miss_nz/len(df)*100).round(3).values,
                       "Present":(len(df)-miss_nz).values,
                       "Dtype":[str(df[c].dtype) for c in miss_nz.index]})
    st.dataframe(md, use_container_width=True, height=min(320, 50+len(md)*38))

# ══════════════════════════════════════════════════════════════════════
#  §8  DETAILED FAULT REPORT
# ══════════════════════════════════════════════════════════════════════
sec("🔍", "Detailed Fault Report", "Expand each dimension · full findings + code recommendations")

panels = [
    ("🕳️  Completeness", A["S"]["Completeness"], [
        ("#ef4444" if A["nc"]>0 else "#10b981", f"True null cells: <strong>{A['nc']:,}</strong>"),
        ("#f59e0b" if A["es"]>0 else "#10b981",  f"Empty string cells: <strong>{A['es']:,}</strong>"),
        ("#f59e0b" if A["ph"]>0 else "#10b981",  f"Placeholder strings: <strong>{A['ph']:,}</strong>"),
        ("#06b6d4", "💡 Fix: " + ("Complete." if A["tm"]==0 else "Impute numerics with median. Use mode/constant for categoricals.")),
    ]),
    ("🪞  Uniqueness", A["S"]["Uniqueness"], [
        ("#ef4444" if A["ed"]>0 else "#10b981", f"Exact duplicate rows: <strong>{A['ed']:,}</strong>"),
        ("#f59e0b" if A["dc"] else "#10b981",    f"Identical column pairs: <strong>{len(A['dc'])}</strong> — {', '.join([f'{a}↔{b}' for a,b in A['dc']]) or 'None'}"),
        ("#ef4444" if A["cc"] else "#10b981",    f"Constant columns: <strong>{len(A['cc'])}</strong> — {', '.join(A['cc']) or 'None'}"),
        ("#06b6d4", "💡 Fix: " + ("None." if A["ed"]==0 else "<code>df.drop_duplicates()</code>. Drop constant columns.")),
    ]),
    ("🔀  Consistency", A["S"]["Consistency"], [
        ("#ef4444" if A["mx"] else "#10b981", f"Mixed-type columns: <strong>{len(A['mx'])}</strong> — {', '.join(A['mx']) or 'None'}"),
        ("#f59e0b" if A["ca"] else "#10b981", f"Case-inconsistent: <strong>{len(A['ca'])}</strong> — {', '.join(A['ca']) or 'None'}"),
        ("#ef4444" if A["en"] else "#10b981", f"Encoding artifacts: <strong>{len(A['en'])}</strong> — {', '.join(A['en']) or 'None'}"),
        ("#06b6d4", "💡 Fix: <code>.str.lower().str.strip()</code>. Re-read with <code>encoding='utf-8'</code>."),
    ]),
    ("📐  Validity", A["S"]["Validity"], [
        ("#f59e0b" if A["oc"] else "#10b981", f"Outlier columns (3×IQR): <strong>{len(A['oc'])}</strong>" + (" — " + ", ".join(f"{o['col']} ({o['count']})" for o in A["oc"][:5]) if A["oc"] else "")),
        ("#ef4444" if A["im"] else "#10b981", f"Domain violations: <strong>{len(A['im'])}</strong> — {', '.join(A['im']) or 'None'}"),
        ("#06b6d4", "💡 Fix: Winsorize or clip outliers. Set impossible values to NaN then impute."),
    ]),
    ("📉  Accuracy", A["S"]["Accuracy"], [
        ("#f59e0b" if A["sk"] else "#10b981", f"Skewed columns |skew|>2: <strong>{len(A['sk'])}</strong>" + (" — " + ", ".join(f"{s['col']} ({s['skew']})" for s in A["sk"][:4]) if A["sk"] else "")),
        ("#f59e0b" if A["ib"] else "#10b981", f"Imbalanced categoricals >85%: <strong>{len(A['ib'])}</strong> — {', '.join(A['ib']) or 'None'}"),
        ("#06b6d4", "💡 Fix: <code>np.log1p()</code> or Box-Cox. Use <code>class_weight='balanced'</code>."),
    ]),
    ("🏗️  Structure", A["S"]["Structure"], [
        ("#ef4444" if A["bn"] else "#10b981",  f"Bad column names: <strong>{len(A['bn'])}</strong> — {', '.join(str(c) for c in A['bn']) or 'None'}"),
        ("#f59e0b" if A["wt"] else "#10b981",  f"Wrong dtype (numeric as string): <strong>{len(A['wt'])}</strong> — {', '.join(A['wt']) or 'None'}"),
        ("#ef4444" if A["er"]>0 else "#10b981",f"Fully empty rows: <strong>{A['er']}</strong>"),
        ("#06b6d4", "💡 Fix: Rename to snake_case. <code>pd.to_numeric(errors='coerce')</code>."),
    ]),
    ("🔗  Correlation", A["S"]["Correlation"], [
        ("#f59e0b" if A["hc"] else "#10b981", f"Highly correlated pairs r>0.95: <strong>{len(A['hc'])}</strong>" + (" — " + ", ".join(f"{p['a']}↔{p['b']} ({p['r']})" for p in A["hc"][:3]) if A["hc"] else "")),
        ("#06b6d4", "💡 Fix: Drop one from each correlated pair. Use PCA for dimensionality reduction."),
    ]),
]
for title, score, items in panels:
    g = "A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
    with st.expander(f"{title}  ·  {score:.1f} / 100  ·  Grade {g}"):
        for dot, html in items: rfind(dot, html)

# ══════════════════════════════════════════════════════════════════════
#  §9  DOWNLOAD AUDIT REPORT CSV
# ══════════════════════════════════════════════════════════════════════
sec("📥", "Download Audit Report", "Export a detailed CSV of every issue with severity, example values & fix code")

def build_audit_csv(df, A):
    rows = []
    PH2  = {"n/a","na","none","null","nil","-","--","?","unknown","undefined","missing","tbd","tbc","#n/a"}

    rows.append({"Issue_ID":"DQS-000","Dimension":"Summary","Severity":"INFO",
                 "Column":"— (dataset level)","Issue_Type":"Dataset Quality Score",
                 "Detail":f"DQS = {A['DQS']} / 100  |  Grade {dqs_grade(A['DQS'])[1]} — {dqs_grade(A['DQS'])[2]}",
                 "Affected_Rows":df.shape[0],"Affected_Cols":df.shape[1],"Value_Example":"",
                 "Fix_Recommendation":f"Raw={A['raw']:.3f}  Size_Factor={A['sf']:.3f}  Diversity_Bonus={A['db']:.4f}"})

    iid = 1
    for c in df.columns:
        n = int(df[c].isnull().sum())
        if n:
            pct = round(n/len(df)*100, 3)
            rows.append({"Issue_ID":f"COMP-{iid:03d}","Dimension":"Completeness",
                         "Severity":"HIGH" if pct>20 else "MEDIUM" if pct>5 else "LOW",
                         "Column":c,"Issue_Type":"Null / NaN values",
                         "Detail":f"{n:,} null cells ({pct}% of column)",
                         "Affected_Rows":n,"Affected_Cols":1,"Value_Example":"NaN",
                         "Fix_Recommendation":"Impute with median (numeric) or mode/constant (categorical)."})
            iid += 1

    iid = 1
    for c in df.select_dtypes("object").columns:
        v = df[c].dropna().astype(str); ph_m = v.str.strip().str.lower().isin(PH2); cnt = int(ph_m.sum())
        if cnt:
            ex = v[ph_m].unique()[:3].tolist()
            rows.append({"Issue_ID":f"COMP-PH-{iid:03d}","Dimension":"Completeness","Severity":"MEDIUM",
                         "Column":c,"Issue_Type":"Placeholder / fake null string",
                         "Detail":f"{cnt:,} cells contain filler values",
                         "Affected_Rows":cnt,"Affected_Cols":1,"Value_Example":", ".join(str(e) for e in ex),
                         "Fix_Recommendation":"df[col].replace(['N/A','unknown','-'], np.nan)"})
            iid += 1

    if A["ed"]:
        dup_idx = df[df.duplicated()].index.tolist()
        rows.append({"Issue_ID":"UNIQ-001","Dimension":"Uniqueness",
                     "Severity":"HIGH" if A["ed"]>len(df)*.05 else "MEDIUM",
                     "Column":"— (all columns)","Issue_Type":"Exact duplicate rows",
                     "Detail":f"{A['ed']:,} rows are exact duplicates ({round(A['ed']/len(df)*100,2)}%)",
                     "Affected_Rows":A["ed"],"Affected_Cols":df.shape[1],
                     "Value_Example":f"Row indices: {dup_idx[:5]}",
                     "Fix_Recommendation":"df.drop_duplicates(inplace=True)"})

    for i, c in enumerate(A["cc"]):
        uv = df[c].dropna().unique()
        rows.append({"Issue_ID":f"UNIQ-CC-{i+1:03d}","Dimension":"Uniqueness","Severity":"MEDIUM",
                     "Column":c,"Issue_Type":"Constant / zero-variance column",
                     "Detail":f"Only 1 unique value: '{uv[0] if len(uv) else 'N/A'}'",
                     "Affected_Rows":len(df),"Affected_Cols":1,
                     "Value_Example":str(uv[0]) if len(uv) else "N/A",
                     "Fix_Recommendation":f"df.drop(columns=['{c}'], inplace=True)"})

    for i, c in enumerate(A["mx"]):
        rows.append({"Issue_ID":f"CONS-MX-{i+1:03d}","Dimension":"Consistency","Severity":"HIGH",
                     "Column":c,"Issue_Type":"Mixed data types",
                     "Detail":"Contains both numeric and text values",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":str(df[c].dropna().iloc[0]) if df[c].dropna().shape[0] else "",
                     "Fix_Recommendation":f"pd.to_numeric(df['{c}'], errors='coerce')"})

    for i, c in enumerate(A["ca"]):
        ex = df[c].dropna().astype(str).str.strip().unique()[:4].tolist()
        rows.append({"Issue_ID":f"CONS-CA-{i+1:03d}","Dimension":"Consistency","Severity":"LOW",
                     "Column":c,"Issue_Type":"Case inconsistency",
                     "Detail":"Same values appear in different cases",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":", ".join(str(e) for e in ex),
                     "Fix_Recommendation":f"df['{c}'] = df['{c}'].str.lower().str.strip()"})

    for i, o in enumerate(A["oc"]):
        c = o["col"]; d = df[c].dropna()
        Q1,Q3 = d.quantile(.25),d.quantile(.75); IQR = Q3-Q1
        lo,hi = Q1-3*IQR, Q3+3*IQR
        ovs = d[(d<lo)|(d>hi)].round(4).tolist()
        rows.append({"Issue_ID":f"VALD-OUT-{i+1:03d}","Dimension":"Validity",
                     "Severity":"HIGH" if o["count"]>len(df)*.05 else "MEDIUM",
                     "Column":c,"Issue_Type":"Extreme outliers (3×IQR rule)",
                     "Detail":f"{o['count']} extreme values | Q1={round(Q1,3)} Q3={round(Q3,3)} IQR={round(IQR,3)} | fences [{round(lo,3)}, {round(hi,3)}]",
                     "Affected_Rows":o["count"],"Affected_Cols":1,
                     "Value_Example":", ".join(str(v) for v in ovs[:5]),
                     "Fix_Recommendation":f"df['{c}'] = df['{c}'].clip({round(lo,3)}, {round(hi,3)})"})

    for i, c in enumerate(A["im"]):
        rows.append({"Issue_ID":f"VALD-DOM-{i+1:03d}","Dimension":"Validity","Severity":"HIGH",
                     "Column":c,"Issue_Type":"Domain violation (impossible values)",
                     "Detail":f"Values outside expected domain range",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":str(df[c].dropna().min()),
                     "Fix_Recommendation":f"df.loc[invalid_mask, '{c}'] = np.nan"})

    for i, s in enumerate(A["sk"]):
        c = s["col"]; sk = s["skew"]
        rows.append({"Issue_ID":f"ACCR-SK-{i+1:03d}","Dimension":"Accuracy",
                     "Severity":"HIGH" if abs(sk)>5 else "MEDIUM",
                     "Column":c,"Issue_Type":"Highly skewed distribution",
                     "Detail":f"Skewness = {sk}",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":f"min={round(df[c].min(),3)}  max={round(df[c].max(),3)}",
                     "Fix_Recommendation":f"df['{c}'] = np.log1p(df['{c}'])"})

    for i, c in enumerate(A["ib"]):
        vc = df[c].value_counts(normalize=True)
        rows.append({"Issue_ID":f"ACCR-IB-{i+1:03d}","Dimension":"Accuracy","Severity":"MEDIUM",
                     "Column":c,"Issue_Type":"Imbalanced categorical (>85% one class)",
                     "Detail":f"'{vc.index[0]}' = {round(float(vc.iloc[0])*100,2)}%",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":str(vc.index[0]),
                     "Fix_Recommendation":"Use SMOTE or class_weight='balanced'"})

    for i, c in enumerate(A["bn"]):
        rows.append({"Issue_ID":f"STRC-BN-{i+1:03d}","Dimension":"Structure","Severity":"LOW",
                     "Column":str(c),"Issue_Type":"Bad column name",
                     "Detail":f"Contains special chars or is auto-generated",
                     "Affected_Rows":len(df),"Affected_Cols":1,
                     "Value_Example":str(c),
                     "Fix_Recommendation":f"df.rename(columns={{'{c}': 'clean_name'}}, inplace=True)"})

    for i, c in enumerate(A["wt"]):
        rows.append({"Issue_ID":f"STRC-WT-{i+1:03d}","Dimension":"Structure","Severity":"MEDIUM",
                     "Column":c,"Issue_Type":"Wrong dtype (numeric as string)",
                     "Detail":">95% of values are numeric but dtype=object",
                     "Affected_Rows":int(df[c].notna().sum()),"Affected_Cols":1,
                     "Value_Example":str(df[c].dropna().iloc[0]) if df[c].dropna().shape[0] else "",
                     "Fix_Recommendation":f"df['{c}'] = pd.to_numeric(df['{c}'], errors='coerce')"})

    if A["er"]:
        empty_idx = df[df.isnull().all(axis=1)].index.tolist()
        rows.append({"Issue_ID":"STRC-ER-001","Dimension":"Structure","Severity":"HIGH",
                     "Column":"— (all columns)","Issue_Type":"Fully empty rows",
                     "Detail":f"{A['er']} rows have no values",
                     "Affected_Rows":A["er"],"Affected_Cols":df.shape[1],
                     "Value_Example":f"Row indices: {empty_idx[:5]}",
                     "Fix_Recommendation":"df.dropna(how='all', inplace=True)"})

    for i, p in enumerate(A["hc"]):
        rows.append({"Issue_ID":f"CORR-{i+1:03d}","Dimension":"Correlation",
                     "Severity":"HIGH" if p["r"]>0.999 else "MEDIUM",
                     "Column":f"{p['a']}  ↔  {p['b']}","Issue_Type":"Highly correlated pair (r>0.95)",
                     "Detail":f"Pearson r = {p['r']}",
                     "Affected_Rows":len(df),"Affected_Cols":2,
                     "Value_Example":f"r = {p['r']}",
                     "Fix_Recommendation":f"df.drop(columns=['{p['b']}'], inplace=True)"})

    for dim, score in A["S"].items():
        g = "A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
        rows.append({"Issue_ID":f"SCORE-{dim[:4].upper()}","Dimension":dim,"Severity":"SCORE",
                     "Column":"— (dimension)","Issue_Type":f"{dim} Dimension Score",
                     "Detail":f"Score={score:.2f}/100  Weight={int(A['W'][dim]*100)}%  Grade {g}",
                     "Affected_Rows":"","Affected_Cols":"","Value_Example":"","Fix_Recommendation":""})

    return pd.DataFrame(rows)

audit_df = build_audit_csv(df, A)
sev      = audit_df[audit_df["Severity"].isin(["HIGH","MEDIUM","LOW"])]["Severity"].value_counts()
high_c   = sev.get("HIGH",  0)
med_c    = sev.get("MEDIUM",0)
low_c    = sev.get("LOW",   0)
total_i  = high_c + med_c + low_c

st.markdown(f"""
<div style="background:rgba(255,255,255,.022);border:1px solid var(--b2);border-radius:var(--rl);
            padding:1.8rem;backdrop-filter:blur(20px);
            box-shadow:0 8px 40px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.04);margin-bottom:1.2rem">
  <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1.2rem">
    <span style="font-size:1.3rem">📥</span>
    <div>
      <div style="font-family:'Syne',sans-serif;font-size:.95rem;font-weight:700;color:var(--t)">Detailed Audit Report</div>
      <div style="font-size:.72rem;color:var(--t2);margin-top:.1rem">{len(audit_df)} rows · every issue documented with severity, example value &amp; fix code</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin-bottom:1.4rem">
    <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:.9rem;text-align:center">
      <div style="font-size:1.6rem;font-weight:800;color:#ef4444;font-family:'Syne',sans-serif">{high_c}</div>
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:rgba(239,68,68,.7);margin-top:.2rem">High Severity</div>
    </div>
    <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:.9rem;text-align:center">
      <div style="font-size:1.6rem;font-weight:800;color:#f59e0b;font-family:'Syne',sans-serif">{med_c}</div>
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:rgba(245,158,11,.7);margin-top:.2rem">Medium Severity</div>
    </div>
    <div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:.9rem;text-align:center">
      <div style="font-size:1.6rem;font-weight:800;color:#10b981;font-family:'Syne',sans-serif">{low_c}</div>
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:rgba(16,185,129,.7);margin-top:.2rem">Low Severity</div>
    </div>
    <div style="background:rgba(61,127,255,.08);border:1px solid rgba(61,127,255,.2);border-radius:10px;padding:.9rem;text-align:center">
      <div style="font-size:1.6rem;font-weight:800;color:#3d7fff;font-family:'Syne',sans-serif">{total_i}</div>
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:rgba(61,127,255,.7);margin-top:.2rem">Total Issues</div>
    </div>
  </div>
  <div style="font-size:.74rem;color:var(--t2);line-height:1.7">
    Columns: <strong style="color:var(--t)">Issue_ID · Dimension · Severity · Column · Issue_Type · Detail · Affected_Rows · Value_Example · Fix_Recommendation</strong>
  </div>
</div>""", unsafe_allow_html=True)

with st.expander("👁  Preview audit report (first 20 rows)"):
    st.dataframe(audit_df.head(20), use_container_width=True, height=380)

csv_buf   = io.StringIO(); audit_df.to_csv(csv_buf, index=False)
csv_bytes = csv_buf.getvalue().encode("utf-8")
fname     = f"audit_report_{meta.get('name','dataset').replace('.','_').replace(' ','_')}.csv"

col_dl, col_info = st.columns([1, 3], gap="large")
with col_dl:
    st.download_button("⬇  Download Audit Report CSV", data=csv_bytes,
                       file_name=fname, mime="text/csv", use_container_width=True)
with col_info:
    st.markdown(f"""
    <div style="background:rgba(255,255,255,.018);border:1px solid var(--b);border-radius:10px;
                padding:.85rem 1.1rem;font-size:.77rem;color:var(--t2);line-height:1.8">
      <strong style="color:var(--t)">📄 {fname}</strong><br>
      {len(audit_df)} rows &nbsp;·&nbsp; 10 columns &nbsp;·&nbsp;
      {high_c} HIGH · {med_c} MEDIUM · {low_c} LOW severity issues<br>
      <span style="color:var(--t3)">Opens in Excel, Google Sheets, Notion, Jira</span>
    </div>""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:4rem;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,.04);
            display:flex;justify-content:space-between;align-items:center">
  <div style="font-size:.7rem;color:rgba(255,255,255,.12);font-family:'JetBrains Mono',monospace">◈ Data Audit System v3.0</div>
  <div style="font-size:.68rem;color:rgba(255,255,255,.1)">Upload a new file above to re-run the audit</div>
</div>""", unsafe_allow_html=True)
