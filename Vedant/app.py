import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import re
import json
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Data Audit System",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════
#  ALL CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

:root {
  --bg:#020408; --l1:#06090f; --l2:#0a0f1c; --l3:#0e1424;
  --b:rgba(255,255,255,.06); --b2:rgba(255,255,255,.11);
  --t:#dce8ff; --t2:#4a5a8a; --t3:#1e2a48;
  --blue:#3d7fff; --vi:#8b5cf6; --cy:#06b6d4;
  --gr:#10b981; --am:#f59e0b; --re:#ef4444; --pk:#ec4899;
  --r:12px; --rl:18px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:var(--bg)!important;color:var(--t)!important;-webkit-font-smoothing:antialiased}
.block-container{padding:0 2.5rem 6rem!important;max-width:1440px!important;position:relative;z-index:10}
#MainMenu,footer,header,.stDeployButton,[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stToolbar"]{display:none!important}
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:rgba(61,127,255,.3);border-radius:2px}

/* NAV */
.nav{display:flex;align-items:center;justify-content:space-between;padding:1.1rem 0 1.2rem;border-bottom:1px solid var(--b);position:sticky;top:0;z-index:999;background:rgba(2,4,8,.9);backdrop-filter:blur(40px)}
.nav-logo{display:flex;align-items:center;gap:.75rem}
.nav-icon{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#3d7fff,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:1.05rem;color:#fff;font-weight:900;box-shadow:0 0 30px rgba(61,127,255,.5),0 0 60px rgba(139,92,246,.2);animation:iconFloat 4s ease-in-out infinite}
@keyframes iconFloat{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-5px) rotate(4deg)}}
.nav-title{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:var(--t);letter-spacing:-.02em}
.nav-sub{font-size:.58rem;color:var(--t3);text-transform:uppercase;letter-spacing:.12em;font-weight:500}
.nav-right{display:flex;align-items:center;gap:.75rem}
.nav-badge{display:flex;align-items:center;gap:.4rem;font-size:.66rem;color:var(--t2);font-weight:600;background:rgba(16,185,129,.07);border:1px solid rgba(16,185,129,.18);padding:.28rem .85rem;border-radius:999px}
.nav-dot{width:6px;height:6px;border-radius:50%;background:var(--gr);box-shadow:0 0 8px var(--gr);animation:dotPulse 2s ease-in-out infinite}
@keyframes dotPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.75)}}
.nav-ver{font-size:.6rem;color:var(--t3);font-family:'JetBrains Mono',monospace;background:var(--l2);border:1px solid var(--b);padding:.22rem .7rem;border-radius:5px}

/* HERO */
.hero{text-align:center;padding:5.5rem 0 3rem;position:relative;overflow:hidden}
.hero-glow{position:absolute;top:0;left:50%;transform:translateX(-50%);width:900px;height:500px;background:radial-gradient(ellipse,rgba(61,127,255,.08) 0%,rgba(139,92,246,.05) 40%,transparent 70%);pointer-events:none;z-index:-1}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:60px 60px;pointer-events:none;z-index:-1;-webkit-mask-image:radial-gradient(ellipse,black 30%,transparent 70%)}
.hero-eyebrow{display:inline-flex;align-items:center;gap:.4rem;background:rgba(61,127,255,.08);border:1px solid rgba(61,127,255,.2);color:#7aafff;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;padding:.32rem .95rem;border-radius:999px;margin-bottom:1.7rem}
.hero-title{font-family:'Syne',sans-serif;font-size:clamp(2.8rem,6vw,5.5rem);font-weight:800;line-height:1.0;letter-spacing:-.04em;margin-bottom:1.2rem;background:linear-gradient(135deg,#ffffff 0%,#a0c4ff 30%,#8b5cf6 60%,#ec4899 100%);background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:titleShimmer 8s linear infinite}
@keyframes titleShimmer{0%{background-position:0% center}100%{background-position:300% center}}
.hero-sub{font-size:.95rem;color:var(--t2);max-width:520px;margin:0 auto 3rem;line-height:1.85}
.hero-stats{display:flex;justify-content:center;gap:2rem;margin-top:2.5rem}
.hstat{text-align:center}
.hstat-n{font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:700;color:var(--t);line-height:1}
.hstat-l{font-size:.62rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-top:.25rem}

/* UPLOAD */
[data-testid="stFileUploader"]{background:rgba(255,255,255,.02)!important;border:1.5px dashed rgba(61,127,255,.3)!important;border-radius:var(--rl)!important;transition:all .25s!important;backdrop-filter:blur(20px)!important}
[data-testid="stFileUploader"]:hover{border-color:rgba(61,127,255,.65)!important;background:rgba(61,127,255,.05)!important;box-shadow:0 0 50px rgba(61,127,255,.12),inset 0 0 50px rgba(61,127,255,.03)!important}

/* FEATURES */
.features{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin-top:2rem}
.feat{background:rgba(255,255,255,.022);border:1px solid var(--b);border-radius:var(--r);padding:1.3rem;backdrop-filter:blur(12px);transition:all .25s;position:relative;overflow:hidden;cursor:default}
.feat::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,.04),transparent 60%);opacity:0;transition:opacity .25s}
.feat:hover{border-color:var(--b2);transform:translateY(-5px);box-shadow:0 24px 64px rgba(0,0,0,.55)}
.feat:hover::before{opacity:1}
.feat-i{font-size:1.5rem;margin-bottom:.6rem;display:block}
.feat-t{font-size:1rem;font-weight:700;color:var(--t);margin-bottom:.25rem;font-family:'Syne',sans-serif}
.feat-d{font-size:.71rem;color:var(--t2);line-height:1.6}

/* BANNER */
.banner{background:rgba(255,255,255,.022);border:1px solid var(--b2);border-radius:var(--rl);padding:1rem 1.5rem;display:flex;align-items:center;justify-content:space-between;backdrop-filter:blur(24px);margin-bottom:2.5rem;box-shadow:0 8px 40px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.04);animation:fadeUp .5s ease both}
.banner-icon{width:44px;height:44px;border-radius:11px;flex-shrink:0;background:linear-gradient(135deg,rgba(61,127,255,.2),rgba(139,92,246,.2));border:1px solid rgba(61,127,255,.28);display:flex;align-items:center;justify-content:center;font-size:1.2rem}
.tag{font-size:.66rem;font-weight:700;padding:.22rem .75rem;border-radius:999px;display:inline-block}

/* SECTION TITLE */
.stitle{display:flex;align-items:center;gap:.9rem;margin:3.5rem 0 1.4rem;animation:fadeUp .4s ease both}
.stitle-line{flex:1;height:1px;background:linear-gradient(90deg,var(--b2),transparent)}
.stitle-main{font-family:'Syne',sans-serif;font-size:1.75rem;font-weight:800;color:var(--t);letter-spacing:-.03em;line-height:1.1}
.stitle-sub{font-size:.78rem;color:var(--t2);margin-top:.3rem;font-weight:400}

/* DQS CARD */
.dqs-card{background:rgba(255,255,255,.022);border:1px solid var(--b2);border-radius:var(--rl);padding:2rem 1.8rem;text-align:center;backdrop-filter:blur(24px);position:relative;overflow:hidden;box-shadow:0 28px 90px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.05);animation:scaleSpring .7s cubic-bezier(.34,1.56,.64,1) both .1s}
.dqs-glow{position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:320px;height:220px;border-radius:50%;pointer-events:none;animation:glowPulse 3s ease-in-out infinite}
@keyframes glowPulse{0%,100%{opacity:.45}50%{opacity:1}}
.dqs-eyebrow{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--t2);margin-bottom:1rem}
.dqs-num{font-family:'Syne',sans-serif;font-size:6.5rem;font-weight:800;line-height:1;letter-spacing:-.06em;animation:fadeUp .6s ease both .35s}
.dqs-unit{font-size:.82rem;color:var(--t3);margin:.2rem 0 .7rem;font-family:'JetBrains Mono',monospace}
.dqs-pill{display:inline-flex;align-items:center;gap:.4rem;border-radius:999px;padding:.4rem 1.2rem;font-size:.88rem;font-weight:700;letter-spacing:.04em}
.dqs-divider{border:none;border-top:1px solid var(--b);margin:1.4rem 0}
.dqs-row{display:flex;justify-content:space-between;font-size:.8rem;color:var(--t2);padding:.25rem 0}
.dqs-row b{color:var(--t);font-family:'JetBrains Mono',monospace;font-weight:500}

/* METRIC CARDS */
.mc{background:rgba(255,255,255,.022);border:1px solid var(--b);border-radius:var(--rl);padding:1.2rem 1.35rem;position:relative;overflow:hidden;backdrop-filter:blur(12px);transition:all .22s;box-shadow:0 4px 28px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.04);animation:fadeUp .4s ease both}
.mc-bar{position:absolute;top:0;left:0;right:0;height:2px;border-radius:var(--rl) var(--rl) 0 0}
.mc:hover{border-color:var(--b2);transform:translateY(-4px);box-shadow:0 20px 60px rgba(0,0,0,.55)}
.mc-label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--t2);margin-bottom:.55rem}
.mc-value{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;line-height:1;letter-spacing:-.03em}
.mc-sub{font-size:.66rem;color:var(--t3);margin-top:.3rem;font-weight:500}

/* DIMENSION CARDS */
.dim{background:rgba(255,255,255,.022);border:1px solid var(--b);border-radius:var(--r);padding:.95rem .85rem;text-align:center;backdrop-filter:blur(12px);transition:all .22s;position:relative;overflow:hidden;animation:fadeUp .4s ease both}
.dim-bot{position:absolute;bottom:0;left:0;right:0;height:2px;border-radius:0 0 var(--r) var(--r)}
.dim:hover{border-color:var(--b2);transform:translateY(-6px);box-shadow:0 24px 70px rgba(0,0,0,.6)}
.dim-icon{font-size:1rem;display:block;margin-bottom:.3rem}
.dim-name{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--t2);margin-bottom:.5rem}
.dim-score{font-family:'Syne',sans-serif;font-size:1.65rem;font-weight:800;line-height:1}
.dim-denom{font-size:.54rem;color:var(--t3);font-family:'JetBrains Mono',monospace;margin:.14rem 0 .5rem}
.dim-bar{height:3px;background:rgba(255,255,255,.06);border-radius:999px;overflow:hidden;margin-bottom:.4rem}
.dim-fill{height:100%;border-radius:999px;animation:barGrow .9s cubic-bezier(.4,0,.2,1) both .6s}
@keyframes barGrow{from{width:0}to{width:var(--w)}}
.dim-wt{font-size:.57rem;color:var(--t3);font-weight:600}

/* FINDINGS */
.finding{display:flex;align-items:flex-start;gap:.85rem;background:rgba(255,255,255,.02);border:1px solid var(--b);border-radius:var(--r);padding:.95rem 1.1rem;margin-bottom:.4rem;backdrop-filter:blur(12px);transition:all .2s;animation:fadeUp .35s ease both;line-height:1.65;font-size:.92rem}
.finding:hover{border-color:var(--b2);background:rgba(255,255,255,.034);transform:translateX(5px)}
.finding-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:.42rem}

/* TABLES */
[data-testid="stDataFrame"]{border:1px solid var(--b)!important;border-radius:var(--r)!important;overflow:hidden!important;animation:fadeUp .4s ease both}
[data-testid="stDataFrame"] table{background:rgba(6,9,15,.85)!important}
[data-testid="stDataFrame"] thead th{background:rgba(255,255,255,.03)!important;color:var(--t2)!important;font-size:.78rem!important;font-weight:700!important;letter-spacing:.07em!important;text-transform:uppercase!important;border-bottom:1px solid var(--b)!important}
[data-testid="stDataFrame"] tbody td{color:var(--t)!important;font-family:'JetBrains Mono',monospace!important;font-size:.85rem!important;border-bottom:1px solid rgba(255,255,255,.03)!important}
[data-testid="stDataFrame"] tbody tr:hover td{background:rgba(61,127,255,.05)!important}

/* EXPANDERS */
[data-testid="stExpander"]{background:rgba(255,255,255,.02)!important;border:1px solid var(--b)!important;border-radius:var(--r)!important;backdrop-filter:blur(12px)!important;margin-bottom:.45rem!important;transition:border-color .2s!important}
[data-testid="stExpander"]:hover{border-color:var(--b2)!important}
[data-testid="stExpander"] summary{font-size:1.05rem!important;font-weight:700!important;color:var(--t)!important;padding:.95rem 1.2rem!important;font-family:'Syne',sans-serif!important}

/* BUTTON */
.stButton>button{background:linear-gradient(135deg,#3d7fff,#8b5cf6)!important;color:#fff!important;border:none!important;border-radius:12px!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.88rem!important;padding:.7rem 2.2rem!important;box-shadow:0 4px 28px rgba(61,127,255,.45)!important;transition:all .2s!important}
.stButton>button:hover{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 12px 45px rgba(61,127,255,.65)!important}

/* ALERTS */
.stSuccess{background:rgba(16,185,129,.07)!important;border:1px solid rgba(16,185,129,.2)!important;border-radius:var(--r)!important}
.stError{background:rgba(239,68,68,.07)!important;border:1px solid rgba(239,68,68,.2)!important;border-radius:var(--r)!important}
.stProgress>div>div{background:linear-gradient(90deg,#3d7fff,#8b5cf6)!important}
.stImage img{border-radius:var(--r)!important;border:1px solid var(--b)!important}

/* SPARKLINE canvas */
.spark-wrap{background:rgba(255,255,255,.02);border:1px solid var(--b);border-radius:var(--r);padding:.9rem 1rem;backdrop-filter:blur(12px);transition:all .2s}
.spark-wrap:hover{border-color:var(--b2);transform:translateY(-3px)}

/* ANIMATED RING */
.ring-wrap{display:flex;justify-content:center;align-items:center;margin-bottom:1rem}

/* ANIMATIONS */
@keyframes fadeUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
@keyframes scaleSpring{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
@keyframes typewriter{from{width:0}to{width:100%}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

/* TYPEWRITER */
.typewriter{overflow:hidden;white-space:nowrap;border-right:2px solid var(--blue);animation:typewriter 2s steps(40) both,blink .7s step-end infinite}

/* HOLOGRAPHIC shimmer on DQS */
.holo::after{content:'';position:absolute;inset:0;background:linear-gradient(105deg,transparent 20%,rgba(255,255,255,.04) 50%,transparent 80%);background-size:200% 100%;animation:holoSweep 3s linear infinite;pointer-events:none;border-radius:var(--rl)}
@keyframes holoSweep{0%{background-position:-200% 0}100%{background-position:200% 0}}

/* SCORE RING */
#score-ring-container{position:relative;width:180px;height:180px;margin:0 auto 1rem}

/* LIVE FEED */
.live-feed{background:rgba(255,255,255,.018);border:1px solid var(--b);border-radius:var(--r);padding:.8rem 1rem;font-family:'JetBrains Mono',monospace;font-size:.82rem;color:var(--t2);line-height:1.9;max-height:160px;overflow:hidden;position:relative}
.live-feed::after{content:'';position:absolute;bottom:0;left:0;right:0;height:40px;background:linear-gradient(transparent,var(--l1))}
.live-feed-line{animation:fadeUp .3s ease both}
.live-green{color:#10b981}.live-red{color:#ef4444}.live-blue{color:#3d7fff}.live-am{color:#f59e0b}

.empty-ok{background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.18);border-radius:var(--rl);padding:2.5rem;text-align:center}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  THREE.JS + ALL INTERACTIVE JS  (via components.html)
# ══════════════════════════════════════════════════════════════════════
THREEJS = """<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden;width:100%;height:1px}</style>
</head><body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
var PD=parent.document,PW=parent.window;
var W=PW.innerWidth,H=PW.innerHeight;

/* ── WebGL renderer ── */
var renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(PW.devicePixelRatio,2));
renderer.setSize(W,H);
var cvs=renderer.domElement;
cvs.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
PD.body.appendChild(cvs);

var scene=new THREE.Scene();
var camera=new THREE.PerspectiveCamera(60,W/H,.1,2000);
camera.position.z=600;

/* ── 2200 colored particles ── */
var N=2200,geo=new THREE.BufferGeometry(),pos=new Float32Array(N*3),col=new Float32Array(N*3);
var COLS=[[.24,.5,1],[.55,.36,.96],[.04,.71,.83],[.06,.73,.51],[.96,.62,.07],[.93,.29,.6]];
for(var i=0;i<N;i++){
  var i3=i*3,c=COLS[Math.floor(Math.random()*COLS.length)];
  pos[i3]=(Math.random()-.5)*1800;pos[i3+1]=(Math.random()-.5)*1400;pos[i3+2]=(Math.random()-.5)*1000;
  col[i3]=c[0];col[i3+1]=c[1];col[i3+2]=c[2];
}
geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
geo.setAttribute('color',new THREE.BufferAttribute(col,3));
var pmat=new THREE.PointsMaterial({size:1.7,vertexColors:true,transparent:true,opacity:.45,sizeAttenuation:true,blending:THREE.AdditiveBlending,depthWrite:false});
var pts=new THREE.Points(geo,pmat);
scene.add(pts);

/* ── Glowing grid ── */
var gp=[];
for(var x=-800;x<=800;x+=140){gp.push(x,-700,-600,x,700,-600);}
for(var y=-700;y<=700;y+=120){gp.push(-800,y,-600,800,y,-600);}
var gg=new THREE.BufferGeometry();
gg.setAttribute('position',new THREE.BufferAttribute(new Float32Array(gp),3));
scene.add(new THREE.LineSegments(gg,new THREE.LineBasicMaterial({color:0x0a1530,transparent:true,opacity:.35})));

/* ── Floating geometric shapes ── */
var shapes=[];
var geos=[new THREE.OctahedronGeometry(18),new THREE.TetrahedronGeometry(16),new THREE.IcosahedronGeometry(14)];
var shapeColors=[0x3d7fff,0x8b5cf6,0x06b6d4,0x10b981];
for(var k=0;k<6;k++){
  var sm=new THREE.MeshBasicMaterial({color:shapeColors[k%4],wireframe:true,transparent:true,opacity:.12});
  var sm2=new THREE.Mesh(geos[k%3],sm);
  sm2.position.set((Math.random()-.5)*1200,(Math.random()-.5)*900,(Math.random()-.5)*400-200);
  sm2._speed={rx:Math.random()*.008,ry:Math.random()*.012,rz:Math.random()*.006};
  scene.add(sm2);shapes.push(sm2);
}

/* ── Mouse parallax ── */
var mouse={x:0,y:0};
PD.addEventListener('mousemove',function(e){mouse.x=(e.clientX/W-.5)*2;mouse.y=(e.clientY/H-.5)*2;});

/* ── Main loop ── */
var clock=new THREE.Clock();
(function loop(){
  requestAnimationFrame(loop);
  var t=clock.getElapsedTime();
  pts.rotation.y=t*.014;pts.rotation.x=Math.sin(t*.007)*.08;
  camera.position.x+=(mouse.x*28-camera.position.x)*.04;
  camera.position.y+=(-mouse.y*18-camera.position.y)*.04;
  camera.lookAt(scene.position);
  pmat.opacity=.38+Math.sin(t*.3)*.1;
  shapes.forEach(function(s){s.rotation.x+=s._speed.rx;s.rotation.y+=s._speed.ry;s.rotation.z+=s._speed.rz;});
  renderer.render(scene,camera);
})();
PW.addEventListener('resize',function(){W=PW.innerWidth;H=PW.innerHeight;camera.aspect=W/H;camera.updateProjectionMatrix();renderer.setSize(W,H);});

/* ── Cursor glow ── */
var glow=PD.createElement('div');
glow.style.cssText='position:fixed;width:400px;height:400px;border-radius:50%;pointer-events:none;z-index:1;transition:opacity .4s;background:radial-gradient(circle,rgba(61,127,255,.05) 0%,transparent 70%);transform:translate(-50%,-50%);opacity:0;';
PD.body.appendChild(glow);
PD.addEventListener('mousemove',function(e){glow.style.left=e.clientX+'px';glow.style.top=e.clientY+'px';glow.style.opacity='1';});
PD.addEventListener('mouseleave',function(){glow.style.opacity='0';});

/* ── Particle burst function (called on upload) ── */
PW._burst=function(cx,cy){
  var BURST=80;
  var particles=[];
  for(var i=0;i<BURST;i++){
    var d=PD.createElement('div');
    var angle=Math.random()*Math.PI*2;
    var speed=60+Math.random()*140;
    var size=2+Math.random()*4;
    var colors2=['#3d7fff','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ec4899'];
    var c=colors2[Math.floor(Math.random()*colors2.length)];
    d.style.cssText='position:fixed;width:'+size+'px;height:'+size+'px;border-radius:50%;background:'+c+';pointer-events:none;z-index:9999;left:'+cx+'px;top:'+cy+'px;box-shadow:0 0 '+(size*2)+'px '+c;
    PD.body.appendChild(d);
    particles.push({el:d,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,life:1,x:cx,y:cy});
  }
  var start=performance.now();
  (function tick(now){
    var dt=(now-start)/1000;start=now;
    var alive=false;
    particles.forEach(function(p){
      if(p.life<=0)return;
      alive=true;
      p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=200*dt;p.life-=dt*1.5;
      p.el.style.left=p.x+'px';p.el.style.top=p.y+'px';p.el.style.opacity=Math.max(0,p.life);
      p.el.style.transform='scale('+Math.max(0,p.life)+')';
      if(p.life<=0)p.el.remove();
    });
    if(alive)requestAnimationFrame(tick);
  })(performance.now());
};

/* ── Animated score ring ── */
PW._drawRing=function(score,color){
  var container=PD.getElementById('score-ring-container');
  if(!container)return;
  var size=180;
  var existCanvas=PD.getElementById('score-ring-canvas');
  if(existCanvas)existCanvas.remove();
  var c=PD.createElement('canvas');
  c.id='score-ring-canvas';c.width=size*2;c.height=size*2;
  c.style.cssText='width:'+size+'px;height:'+size+'px;position:absolute;top:0;left:0;';
  container.appendChild(c);
  var ctx=c.getContext('2d');
  var cx=size,cy=size,r=size-16,start=-Math.PI/2,target=2*Math.PI*(score/100),t=0;
  var hexToRgb=function(h){var r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return r+','+g+','+b;};
  var rgb=hexToRgb(color);
  (function anim(){
    t=Math.min(t+.025,1);var ease=1-Math.pow(1-t,3);var end=start+target*ease;
    ctx.clearRect(0,0,size*2,size*2);
    /* track */
    ctx.beginPath();ctx.arc(cx,cy,r,0,2*Math.PI);
    ctx.strokeStyle='rgba(255,255,255,.06)';ctx.lineWidth=10;ctx.stroke();
    /* progress */
    var grd=ctx.createLinearGradient(0,0,size*2,size*2);
    grd.addColorStop(0,color);grd.addColorStop(1,'rgba('+rgb+',.4)');
    ctx.beginPath();ctx.arc(cx,cy,r,start,end);
    ctx.strokeStyle=grd;ctx.lineWidth=10;ctx.lineCap='round';
    ctx.shadowBlur=20;ctx.shadowColor=color;ctx.stroke();
    /* tick marks */
    for(var i=0;i<100;i++){
      var a=start+2*Math.PI*(i/100);
      var inner=r-6,outer=r+(i%10===0?10:5);
      ctx.beginPath();
      ctx.moveTo(cx+inner*Math.cos(a),cy+inner*Math.sin(a));
      ctx.lineTo(cx+outer*Math.cos(a),cy+outer*Math.sin(a));
      ctx.strokeStyle=i/100<=score/100*ease?color:'rgba(255,255,255,.08)';
      ctx.lineWidth=i%10===0?2:1;ctx.shadowBlur=0;ctx.stroke();
    }
    if(t<1)requestAnimationFrame(anim);
  })();
};

/* ── Typewriter ── */
PW._typewrite=function(id,text,speed){
  var el=PD.getElementById(id);
  if(!el)return;
  el.textContent='';var i=0;
  var iv=setInterval(function(){if(i<text.length){el.textContent+=text[i++];}else clearInterval(iv);},speed||35);
};

/* ── Sparklines ── */
PW._sparkline=function(canvasId,data,color){
  var c=PD.getElementById(canvasId);
  if(!c)return;
  var ctx=c.getContext('2d');
  var w=c.width,h=c.height;
  ctx.clearRect(0,0,w,h);
  if(!data||data.length<2)return;
  var min=Math.min.apply(null,data),max=Math.max.apply(null,data);
  var range=max-min||1;
  var sx=function(i){return i/(data.length-1)*w;};
  var sy=function(v){return h-(v-min)/range*(h-8)-4;};
  /* fill */
  var grd=ctx.createLinearGradient(0,0,0,h);
  grd.addColorStop(0,color+'55');grd.addColorStop(1,color+'00');
  ctx.beginPath();ctx.moveTo(sx(0),h);
  data.forEach(function(v,i){ctx.lineTo(sx(i),sy(v));});
  ctx.lineTo(sx(data.length-1),h);ctx.closePath();
  ctx.fillStyle=grd;ctx.fill();
  /* line */
  ctx.beginPath();
  data.forEach(function(v,i){i===0?ctx.moveTo(sx(i),sy(v)):ctx.lineTo(sx(i),sy(v));});
  ctx.strokeStyle=color;ctx.lineWidth=2;ctx.lineJoin='round';ctx.stroke();
  /* dots */
  ctx.fillStyle=color;ctx.shadowBlur=8;ctx.shadowColor=color;
  [0,data.length-1].forEach(function(i){ctx.beginPath();ctx.arc(sx(i),sy(data[i]),3,0,2*Math.PI);ctx.fill();});
};

setTimeout(function(){PW._initDone=true;},800);
</script></body></html>"""

components.html(THREEJS, height=0, scrolling=False)


# ══════════════════════════════════════════════════════════════════════
#  CHART THEME
# ══════════════════════════════════════════════════════════════════════
def chart_theme():
    plt.rcParams.update({
        "figure.facecolor":"#06090f","axes.facecolor":"#020408",
        "axes.edgecolor":"#1a2540","axes.labelcolor":"#4a5a8a",
        "axes.titlecolor":"#dce8ff","axes.titlesize":10,"axes.titleweight":"600",
        "axes.labelsize":8,"xtick.color":"#4a5a8a","ytick.color":"#4a5a8a",
        "xtick.labelsize":7.5,"ytick.labelsize":7.5,"text.color":"#dce8ff",
        "grid.color":"#0c1220","grid.linestyle":"-",
        "axes.grid":True,"axes.grid.axis":"y",
        "axes.spines.top":False,"axes.spines.right":False,
        "axes.spines.left":False,"axes.spines.bottom":True,
        "font.family":"sans-serif","figure.dpi":150,
    })

PAL=["#3d7fff","#8b5cf6","#10b981","#f59e0b","#ef4444","#06b6d4","#ec4899","#34d399","#fb923c","#a3e635"]

# ══════════════════════════════════════════════════════════════════════
#  HELPERS
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
      <div><div class="stitle-main">{title}</div>{'<div class="stitle-sub">'+sub+'</div>' if sub else ''}</div>
      <div class="stitle-line"></div>
    </div>""", unsafe_allow_html=True)

def rfind(dot, html, delay=0):
    st.markdown(f"""
    <div class="finding" style="animation-delay:{delay}s">
      <div class="finding-dot" style="background:{dot};box-shadow:0 0 8px {dot}66"></div>
      <div>{html}</div>
    </div>""", unsafe_allow_html=True)

def dqs_grade(s):
    if s>=85: return "#10b981","A","Excellent"
    if s>=70: return "#06b6d4","B","Good"
    if s>=55: return "#f59e0b","C","Moderate"
    if s>=40: return "#fb923c","D","Poor"
    return "#ef4444","F","Critical"

# ══════════════════════════════════════════════════════════════════════
#  SESSION
# ══════════════════════════════════════════════════════════════════════
for k,v in [("df",None),("meta",{}),("audit",None)]:
    if k not in st.session_state: st.session_state[k]=v

# ══════════════════════════════════════════════════════════════════════
#  NAVBAR
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="nav">
  <div class="nav-logo">
    <div class="nav-icon">◈</div>
    <div><div class="nav-title">Data Audit System</div><div class="nav-sub">Professional Data Quality Analysis</div></div>
  </div>
  <div class="nav-right">
    <span class="nav-ver">v3.0</span>
    <div class="nav-badge"><div class="nav-dot"></div>System Ready</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  HERO + UPLOAD
# ══════════════════════════════════════════════════════════════════════
if st.session_state.df is None:
    st.markdown("""
    <div class="hero">
      <div class="hero-glow"></div>
      <div class="hero-grid"></div>
      <div class="hero-eyebrow">◈ &nbsp; Professional Data Auditing Platform</div>
      <div class="hero-title">Know your data.<br>Before it fails you.</div>
      <div class="hero-sub">Drop any CSV or Excel file — instant comprehensive quality audit, weighted Dataset Quality Score, stunning visualizations, and actionable fix recommendations.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("", type=["csv","xlsx"],
                                label_visibility="collapsed",
                                help="CSV or XLSX · up to 1 GB")

    # Trigger particle burst on upload
    if uploaded:
        components.html("""<script>
        setTimeout(function(){
          if(parent.window._burst){
            parent.window._burst(parent.window.innerWidth/2, parent.window.innerHeight/2);
            parent.window._burst(parent.window.innerWidth/2-100, parent.window.innerHeight/2+50);
            parent.window._burst(parent.window.innerWidth/2+100, parent.window.innerHeight/2+50);
          }
        },200);
        </script>""", height=0)
        with st.spinner("Parsing dataset…"):
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
                st.session_state.df   = df
                st.session_state.meta = {"name":uploaded.name,"size":uploaded.size}
                st.session_state.audit= None
                st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")

    st.markdown("""
    <div class="features">
      <div class="feat"><span class="feat-i">🎯</span><div class="feat-t">Quality Score</div><div class="feat-d">Weighted DQS across 7 dimensions with animated ring + grade A–F</div></div>
      <div class="feat"><span class="feat-i">🔬</span><div class="feat-t">Deep Fault Detection</div><div class="feat-d">Nulls, outliers, duplicates, encoding, type errors — all flagged</div></div>
      <div class="feat"><span class="feat-i">🌐</span><div class="feat-t">Live Sparklines</div><div class="feat-d">Real-time animated charts showing column distributions at a glance</div></div>
      <div class="feat"><span class="feat-i">💡</span><div class="feat-t">Fix Recommendations</div><div class="feat-d">Code-level advice for every single issue detected in your data</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Re-upload
with st.expander("⬆  Upload a different file"):
    nf = st.file_uploader("", type=["csv","xlsx"], label_visibility="collapsed", key="reup")
    if nf:
        try:
            df2 = pd.read_csv(nf) if nf.name.endswith(".csv") else pd.read_excel(nf)
            st.session_state.df=df2; st.session_state.meta={"name":nf.name,"size":nf.size}
            st.session_state.audit=None; st.rerun()
        except Exception as e: st.error(f"Error: {e}")

df=st.session_state.df; meta=st.session_state.meta
mem_kb=df.memory_usage(deep=True).sum()/1024

# File banner
st.markdown(f"""
<div class="banner">
  <div style="display:flex;align-items:center;gap:.85rem">
    <div class="banner-icon">📁</div>
    <div><div style="font-size:1.1rem;font-weight:700;color:var(--t);font-family:'Syne',sans-serif">{meta.get('name','dataset')}</div>
    <div style="font-size:.75rem;color:var(--t2);margin-top:.15rem">{meta.get('size',0)/1024:.1f} KB on disk</div></div>
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
#  AUDIT
# ══════════════════════════════════════════════════════════════════════
if st.session_state.audit is None:
    import time
    prog = st.progress(0,"Initialising…")
    PH={"n/a","na","none","null","nil","-","--","?","unknown","undefined","missing","tbd","tbc","#n/a"}
    prog.progress(10,"Checking completeness…"); nc=df.isnull().sum().sum(); es=ph=0
    for c in df.select_dtypes("object").columns:
        v=df[c].dropna().astype(str); es+=(v.str.strip()=="").sum(); ph+=v.str.strip().str.lower().isin(PH).sum()
    tm=nc+es+ph; mr=tm/max(1,df.shape[0]*df.shape[1]); s1=max(0,100-mr*100*1.5)
    prog.progress(22,"Checking uniqueness…"); ed=df.duplicated().sum(); dc=[]
    cols=list(df.columns)
    for i in range(len(cols)):
        for j in range(i+1,len(cols)):
            if df[cols[i]].equals(df[cols[j]]): dc.append((cols[i],cols[j]))
    cc=[c for c in df.columns if df[c].nunique(dropna=True)<=1]; s2=max(0,100-ed/len(df)*100*2)
    prog.progress(36,"Checking consistency…"); mx,ca,en=[],[],[]
    for c in df.select_dtypes("object").columns:
        v=df[c].dropna()
        if not len(v): continue
        n=pd.to_numeric(v,errors="coerce").notnull().sum(); s=v.astype(str).str.match(r"^[A-Za-z]").sum()
        if 0<n<len(v) and s>0: mx.append(c)
        if df[c].nunique()<=100:
            if v.astype(str).str.strip().str.lower().nunique()<v.astype(str).str.strip().nunique(): ca.append(c)
        if v.astype(str).str.contains(r"[^\x00-\x7F]|â€|Ã©",regex=True,na=False).sum()>0: en.append(c)
    s3=max(0,100-(len(mx)+len(ca)+len(en))/df.shape[1]*100*1.8)
    prog.progress(50,"Checking validity…"); oc,im=[],[]
    for c in df.select_dtypes("number").columns:
        d=df[c].dropna()
        if len(d)<4: continue
        Q1,Q3=d.quantile(.25),d.quantile(.75); IQR=Q3-Q1
        if IQR>0:
            no=((d<Q1-3*IQR)|(d>Q3+3*IQR)).sum()
            if no>0: oc.append({"col":c,"count":int(no)})
        cl=c.lower()
        if any(k in cl for k in ["age","years"]) and ((d<0)|(d>150)).sum(): im.append(c)
        if any(k in cl for k in ["price","salary","cost","amount"]) and (d<0).sum(): im.append(c)
        if any(k in cl for k in ["percent","pct","rate"]) and ((d<0)|(d>100)).sum(): im.append(c)
    nuc=sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
    s4=max(0,100-sum(o["count"] for o in oc)/max(1,nuc)*60-len(im)/max(1,len(df))*100)
    prog.progress(64,"Checking accuracy…"); sk,ib=[],[]
    for c in df.select_dtypes("number").columns:
        sv=df[c].dropna().skew()
        if abs(sv)>2: sk.append({"col":c,"skew":round(float(sv),3)})
    for c in df.select_dtypes("object").columns:
        vc=df[c].value_counts(normalize=True)
        if len(vc)>=2 and float(vc.iloc[0])>0.85: ib.append(c)
    cn=df.select_dtypes("object").shape[1]
    s5=max(0,100-sum(min(abs(x["skew"])/20,.05) for x in sk)*100-(len(ib)/cn*20 if cn>0 else 0))
    prog.progress(78,"Checking structure…"); bn,wt=[],[]; er=int(df.isnull().all(axis=1).sum())
    for c in df.columns:
        sv=str(c)
        if sv.strip()==""or re.match(r"^Unnamed",sv) or re.search(r"[^a-zA-Z0-9_ ]",sv): bn.append(c)
    for c in df.select_dtypes("object").columns:
        if pd.to_numeric(df[c],errors="coerce").notnull().mean()>0.95: wt.append(c)
    s6=max(0,100-(len(bn)+len(wt))/df.shape[1]*30-(10 if df.shape[0]/df.shape[1]<5 else 0))
    prog.progress(90,"Checking correlations…"); hc=[]
    nd=df.select_dtypes("number").dropna(axis=1,how="all")
    if nd.shape[1]>=2:
        cr=nd.corr().abs(); cc2=cr.columns
        for i in range(len(cc2)):
            for j in range(i+1,len(cc2)):
                r=float(cr.iloc[i,j])
                if r>0.95: hc.append({"a":cc2[i],"b":cc2[j],"r":round(r,4)})
    s7=max(0,100-len(hc)*3)
    W={"Completeness":.28,"Uniqueness":.18,"Consistency":.16,"Validity":.16,"Accuracy":.10,"Structure":.07,"Correlation":.05}
    S={"Completeness":s1,"Uniqueness":s2,"Consistency":s3,"Validity":s4,"Accuracy":s5,"Structure":s6,"Correlation":s7}
    raw=sum(W[k]*S[k] for k in W); sf=max(0.5,min(1.0,np.log10(len(df)+1)/4.0))
    db=min(1.05,1+(df.dtypes.nunique()-1)*0.01); DQS=round(min(100,max(0,raw*sf*db)),2)
    time.sleep(.3); prog.progress(100,"✓ Audit complete"); time.sleep(.4); prog.empty()
    st.success(f"✓  Full audit complete — {len(W)} quality dimensions analysed")
    st.session_state.audit=dict(DQS=DQS,raw=raw,sf=sf,db=db,W=W,S=S,nc=nc,es=es,ph=ph,tm=tm,mr=mr,ed=ed,dc=dc,cc=cc,mx=mx,ca=ca,en=en,oc=oc,im=im,sk=sk,ib=ib,bn=bn,wt=wt,er=er,hc=hc)

A=st.session_state.audit; chart_theme()

# ══════════════════════════════════════════════════════════════════════
#  §1  DQS + ANIMATED RING + KPIs
# ══════════════════════════════════════════════════════════════════════
sec("◈","Dataset Quality Score","Animated score ring · 7 weighted dimensions · Grade A–F")

dqs_clr,grade,grade_lbl=dqs_grade(A["DQS"])
null_pct=round(A["tm"]/(df.shape[0]*df.shape[1])*100,2)
complete_p=round(df.dropna().shape[0]/len(df)*100,1)

col_dqs,col_kpis=st.columns([1,2.6],gap="large")

with col_dqs:
    # Animated SVG ring rendered server-side + JS animates it
    st.markdown(f"""
    <div class="dqs-card holo">
      <div class="dqs-glow" style="background:radial-gradient(ellipse,{dqs_clr}35 0%,transparent 65%)"></div>
      <div class="dqs-eyebrow">Dataset Quality Score</div>
      <div id="score-ring-container" style="position:relative;width:180px;height:180px;margin:0 auto .8rem">
        <canvas id="score-ring-canvas" width="360" height="360" style="width:180px;height:180px;position:absolute;top:0;left:0"></canvas>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
          <div class="dqs-num" style="color:{dqs_clr};font-size:3.2rem" id="dqs-counter">{A['DQS']}</div>
          <div style="font-size:.62rem;color:var(--t3);font-family:'JetBrains Mono',monospace">/100</div>
        </div>
      </div>
      <div class="dqs-pill" style="background:{dqs_clr}18;border:1px solid {dqs_clr}44;color:{dqs_clr}">Grade {grade} &nbsp;·&nbsp; {grade_lbl}</div>
      <hr class="dqs-divider">
      <div class="dqs-row"><span>Raw weighted</span><b>{A['raw']:.3f}</b></div>
      <div class="dqs-row"><span>Size factor</span><b>{A['sf']:.3f}</b></div>
      <div class="dqs-row"><span>Diversity bonus</span><b>{A['db']:.4f}</b></div>
      <div class="dqs-row"><span>Missing cells</span><b>{A['tm']:,}</b></div>
      <div class="dqs-row"><span>Duplicate rows</span><b>{A['ed']:,}</b></div>
    </div>""", unsafe_allow_html=True)

    # Trigger the ring animation
    components.html(f"""<script>
    setTimeout(function(){{
      if(parent.window._drawRing) parent.window._drawRing({A['DQS']},'{dqs_clr}');
    }},600);
    </script>""", height=0)

with col_kpis:
    # Sparklines for numeric columns
    num_cols_spark = df.select_dtypes(include=np.number).columns.tolist()
    if num_cols_spark:
        sec_cols = st.columns(min(4, len(num_cols_spark)), gap="small")
        for i, col_name in enumerate(num_cols_spark[:4]):
            data_spark = df[col_name].dropna().sample(min(60, len(df[col_name].dropna()))).tolist()
            color_spark = PAL[i % len(PAL)]
            mean_v = df[col_name].mean()
            std_v  = df[col_name].std()
            canvas_id = f"spark_{i}"
            with sec_cols[i]:
                st.markdown(f"""
                <div class="spark-wrap">
                  <div style="font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--t2);margin-bottom:.3rem">{col_name[:14]}</div>
                  <canvas id="{canvas_id}" width="200" height="50" style="width:100%;height:50px"></canvas>
                  <div style="display:flex;justify-content:space-between;margin-top:.3rem;font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--t3)">
                    <span>μ {mean_v:.2f}</span><span>σ {std_v:.2f}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
                data_json = json.dumps([round(x,4) for x in data_spark])
                components.html(f"""<script>
                setTimeout(function(){{
                  if(parent.window._sparkline) parent.window._sparkline('{canvas_id}',{data_json},'{color_spark}');
                }},700);
                </script>""", height=0)

    st.markdown("<br>", unsafe_allow_html=True)
    r1=st.columns(3,gap="small"); r2=st.columns(3,gap="small")
    kdata=[
        ("Rows",         f"{df.shape[0]:,}","total records","#3d7fff"),
        ("Columns",      str(df.shape[1]),"features","#8b5cf6"),
        ("Missing Cells",f"{A['tm']:,}",f"{null_pct}% of data","#ef4444" if A["tm"]>0 else "#10b981"),
        ("Duplicates",   str(A["ed"]),"exact row copies","#ef4444" if A["ed"]>0 else "#10b981"),
        ("Outlier Cols", str(len(A["oc"])),"columns affected","#f59e0b" if A["oc"] else "#10b981"),
        ("Complete Rows",f"{complete_p}%","rows with no nulls","#10b981" if complete_p>90 else "#f59e0b"),
    ]
    for i,(cols,kd) in enumerate([(r1,kdata[:3]),(r2,kdata[3:])]):
        for col,k in zip(cols,kd):
            with col: mc(k[0],k[1],k[2],k[3],delay=i*.08)

# ══════════════════════════════════════════════════════════════════════
#  LIVE AUDIT LOG  (faked but looks real)
# ══════════════════════════════════════════════════════════════════════
sec("📡","Live Audit Log","Real-time feed from the data analysis engine")

log_lines = []
log_lines.append(f'<span class="live-blue">[SYS]</span> &nbsp;Audit engine initialised · dataset loaded · {df.shape[0]:,} rows × {df.shape[1]} cols')
log_lines.append(f'<span class="live-green">[OK]</span> &nbsp;Completeness scan complete → score <b>{A["S"]["Completeness"]:.1f}</b> · missing: {A["tm"]:,} cells')
log_lines.append(f'<span class="live-green">[OK]</span> &nbsp;Uniqueness scan complete → score <b>{A["S"]["Uniqueness"]:.1f}</b> · duplicates: {A["ed"]:,}')
if A["mx"]: log_lines.append(f'<span class="live-red">[WARN]</span> Mixed-type columns detected → {", ".join(A["mx"][:3])}')
if A["oc"]: log_lines.append(f'<span class="live-red">[WARN]</span> Outliers detected in {len(A["oc"])} column(s) using 3×IQR rule')
if A["sk"]: log_lines.append(f'<span class="live-am">[INFO]</span> Skewed distributions found → {len(A["sk"])} column(s) |skew|>2')
if A["hc"]: log_lines.append(f'<span class="live-am">[INFO]</span> High correlation pairs: {len(A["hc"])} pair(s) with r>0.95')
log_lines.append(f'<span class="live-green">[OK]</span> &nbsp;DQS computation complete → <b style="color:#10b981">{A["DQS"]} / 100</b> · Grade <b>{dqs_grade(A["DQS"])[1]}</b>')
log_lines.append(f'<span class="live-blue">[SYS]</span> All {len(A["W"])} dimensions processed · report ready ↓')

st.markdown(f"""
<div class="live-feed">
{"".join(f'<div class="live-feed-line">{l}</div>' for l in log_lines)}
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  §2  DIMENSION BREAKDOWN
# ══════════════════════════════════════════════════════════════════════
sec("📐","Score Breakdown","7 quality dimensions · each scored 0–100 with animated progress bar")
DIM_C={"Completeness":"#3d7fff","Uniqueness":"#8b5cf6","Consistency":"#10b981","Validity":"#06b6d4","Accuracy":"#f59e0b","Structure":"#ec4899","Correlation":"#34d399"}
DIM_I={"Completeness":"🕳️","Uniqueness":"🪞","Consistency":"🔀","Validity":"📐","Accuracy":"📉","Structure":"🏗️","Correlation":"🔗"}
cols7=st.columns(7,gap="small")
for i,(dim,score) in enumerate(A["S"].items()):
    clr=DIM_C[dim]; wt=int(A["W"][dim]*100)
    with cols7[i]:
        st.markdown(f"""
        <div class="dim" style="animation-delay:{i*.06}s">
          <div class="dim-bot" style="background:{clr}"></div>
          <span class="dim-icon">{DIM_I[dim]}</span>
          <div class="dim-name">{dim}</div>
          <div class="dim-score" style="color:{clr}">{score:.0f}</div>
          <div class="dim-denom">/ 100</div>
          <div class="dim-bar"><div class="dim-fill" style="width:{score}%;background:{clr};--w:{score}%"></div></div>
          <div class="dim-wt">{wt}% weight</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  §3  KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════
sec("💡","Key Findings","Auto-detected issues with inline code-level fix recommendations")
fl=[]
if A["tm"]>0: fl.append(("#ef4444",f"<strong>{A['tm']:,} missing values</strong> detected — {null_pct}% of all cells. {A['nc']:,} true nulls + {A['ph']:,} placeholders like <code>N/A</code>, <code>unknown</code>."))
if A["ed"]>0: fl.append(("#ef4444",f"<strong>{A['ed']:,} exact duplicate rows</strong> — use <code>df.drop_duplicates()</code>."))
if A["oc"]:
    nm=" · ".join(f"<code>{o['col']}</code> ({o['count']} pts)" for o in A["oc"][:4])
    fl.append(("#f59e0b",f"<strong>Extreme outliers (3×IQR)</strong> in {len(A['oc'])} column(s): {nm}"))
if A["sk"]:
    nm=" · ".join(f"<code>{s['col']}</code> ({s['skew']:+})" for s in A["sk"][:4])
    fl.append(("#f59e0b",f"<strong>Highly skewed</strong> (|skew|>2): {nm}. Apply <code>np.log1p()</code>."))
if A["mx"]: fl.append(("#ef4444",f"<strong>Mixed-type columns</strong>: {' · '.join('<code>'+c+'</code>' for c in A['mx'][:5])}."))
if A["ca"]: fl.append(("#f59e0b",f"<strong>Case inconsistency</strong> in {len(A['ca'])} column(s). Use <code>.str.lower().str.strip()</code>."))
if A["hc"]:
    p=A["hc"][0]
    fl.append(("#06b6d4",f"<strong>{len(A['hc'])} correlated pair(s)</strong> (r>0.95): <code>{p['a']}</code> ↔ <code>{p['b']}</code> (r={p['r']})."))
if A["cc"]: fl.append(("#8b5cf6",f"<strong>Zero-variance columns</strong>: {' · '.join('<code>'+c+'</code>' for c in A['cc'][:5])}."))
if A["ib"]: fl.append(("#f59e0b",f"<strong>Imbalanced categoricals</strong> >85%: {', '.join(A['ib'][:4])}."))
if not fl: fl.append(("#10b981","🎉 <strong>No major issues detected.</strong> Your dataset is clean and well-structured!"))
for i,(d,h) in enumerate(fl): rfind(d,h,delay=i*.04)

# ══════════════════════════════════════════════════════════════════════
#  §4  COLUMN HEALTH GRID
# ══════════════════════════════════════════════════════════════════════
sec("🩺","Column Health Grid","Per-column health score — null rate, type, uniqueness at a glance")
health_cols = []
for c in df.columns:
    null_r = df[c].isnull().mean()*100
    uniq_r = df[c].nunique()/len(df)*100
    dtype  = str(df[c].dtype)
    score  = max(0, 100 - null_r*2 - (10 if c in A["mx"] else 0) - (10 if c in A["ca"] else 0))
    clr    = "#10b981" if score>=80 else "#f59e0b" if score>=50 else "#ef4444"
    health_cols.append({"Column":c,"Dtype":dtype,"Null %":round(null_r,2),
                        "Unique %":round(uniq_r,2),"Health Score":round(score,1)})
hdf = pd.DataFrame(health_cols)
st.dataframe(hdf, use_container_width=True, height=min(420, 50+len(hdf)*38))

# ══════════════════════════════════════════════════════════════════════
#  §5  PREVIEW + TYPES
# ══════════════════════════════════════════════════════════════════════
sec("🗂","Data Preview","Raw snapshot + column type audit")
cp,ct=st.columns([3,2],gap="large")
with cp:
    st.markdown('<div style="font-size:.9rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--t2);margin-bottom:.6rem">First 8 rows</div>',unsafe_allow_html=True)
    st.dataframe(df.head(8),use_container_width=True,height=295)
with ct:
    st.markdown('<div style="font-size:.9rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--t2);margin-bottom:.6rem">Column types &amp; null rate</div>',unsafe_allow_html=True)
    tdf=pd.DataFrame({"Column":df.columns,"Type":df.dtypes.values,"Non-Null":df.notnull().sum().values,"Null %":(df.isnull().mean()*100).round(2).values,"Unique":df.nunique().values})
    st.dataframe(tdf,use_container_width=True,height=295)

sec("📊","Statistical Summary","Full descriptive stats for every column")
st.dataframe(df.describe(include="all").round(3),use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
#  §6  VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════
num_cols=df.select_dtypes(include=np.number).columns.tolist()

if num_cols:
    sec("📈","Distributions","Mean (red) · Median (green) · Skew & Kurtosis on every chart")
    ns=min(9,len(num_cols)); show=num_cols[:ns]; nc2=3; nr=(len(show)+nc2-1)//nc2
    fig,axes=plt.subplots(nr,nc2,figsize=(14,3.9*nr)); axes=np.array(axes).flatten()
    from matplotlib.lines import Line2D
    for i,col in enumerate(show):
        ax=axes[i]; data=df[col].dropna(); clr=PAL[i%len(PAL)]
        ax.hist(data,bins=28,color=clr,alpha=.72,edgecolor="#020408",linewidth=.3)
        ax.axvline(data.mean(),color="#ef4444",lw=1.5,ls="--",alpha=.9)
        ax.axvline(data.median(),color="#10b981",lw=1.5,ls=":",alpha=.9)
        ax.set_title(col,fontsize=9.5,fontweight="600",pad=8); ax.set_ylabel("Count",fontsize=7)
        sk=data.skew(); ku=data.kurt()
        ax.text(.97,.96,f"skew {sk:+.2f}  kurt {ku:.2f}",transform=ax.transAxes,ha="right",va="top",fontsize=6.5,color="#4a5a8a",fontfamily="monospace",bbox=dict(facecolor="#06090f",edgecolor="#1a2540",boxstyle="round,pad=.3",alpha=.92))
        ax.legend(handles=[Line2D([0],[0],color="#ef4444",ls="--",lw=1.5,label=f"μ {data.mean():.2f}"),Line2D([0],[0],color="#10b981",ls=":",lw=1.5,label=f"M {data.median():.2f}")],fontsize=6.5,framealpha=0,labelcolor="#4a5a8a",loc="upper left")
    for j in range(len(show),len(axes)): axes[j].set_visible(False)
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)

    nd2=df.select_dtypes(include=np.number)
    if nd2.shape[1]>=2:
        sec("🌡️","Correlation Matrix","Pearson r · lower triangle · warm=positive, cool=negative")
        cr2=nd2.corr(); n2=cr2.shape[1]; fs=max(7,min(18,n2*1.1))
        fig,ax=plt.subplots(figsize=(fs,fs*.8)); mask=np.triu(np.ones_like(cr2,dtype=bool))
        cmap=sns.diverging_palette(220,10,as_cmap=True)
        sns.heatmap(cr2,mask=mask,annot=n2<=16,fmt=".2f",cmap=cmap,center=0,ax=ax,linewidths=.5,linecolor="#020408",annot_kws={"size":7.5,"weight":"600","color":"#dce8ff"},cbar_kws={"shrink":.5},square=True)
        ax.tick_params(axis="x",rotation=40,labelsize=8); ax.tick_params(axis="y",rotation=0,labelsize=8)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)
        if n2>2:
            pairs=[]
            for i in range(len(cr2.columns)):
                for j in range(i+1,len(cr2.columns)):
                    pairs.append({"Column A":cr2.columns[i],"Column B":cr2.columns[j],"Pearson r":round(cr2.iloc[i,j],4),"|r|":round(abs(cr2.iloc[i,j]),4)})
            pdf=pd.DataFrame(pairs).sort_values("|r|",ascending=False).drop("|r|",axis=1)
            with st.expander("📋 All correlation pairs — sorted by strength"):
                st.dataframe(pdf,use_container_width=True,height=320)

    sec("📦","Boxplots","IQR bounds · extreme outlier count annotated on every chart")
    nb=min(9,len(num_cols)); showb=num_cols[:nb]; nc3=3; nr2=(len(showb)+nc3-1)//nc3
    fig,axes=plt.subplots(nr2,nc3,figsize=(14,3.9*nr2)); axes=np.array(axes).flatten()
    for i,col in enumerate(showb):
        ax=axes[i]; data=df[col].dropna(); clr=PAL[i%len(PAL)]
        bp=ax.boxplot(data,patch_artist=True,notch=False,medianprops={"color":"#fff","linewidth":2.2},flierprops={"marker":"o","markersize":3.5,"markerfacecolor":clr,"alpha":.6,"markeredgewidth":0},whiskerprops={"linewidth":1.2,"color":"#4a5a8a"},capprops={"linewidth":1.2,"color":"#4a5a8a"})
        for p in bp["boxes"]: p.set_facecolor(clr);p.set_alpha(.6);p.set_edgecolor(clr);p.set_linewidth(1.1)
        ax.set_title(col,fontsize=9.5,fontweight="600",pad=8); ax.set_xticks([])
        Q1,Q3=data.quantile(.25),data.quantile(.75); IQR=Q3-Q1
        no=int(((data<Q1-3*IQR)|(data>Q3+3*IQR)).sum()) if IQR>0 else 0
        ax.text(.97,.04,f"IQR {IQR:.2f}  ·  {no} outlier{'s' if no!=1 else ''}",transform=ax.transAxes,ha="right",va="bottom",fontsize=6.5,color="#4a5a8a",fontfamily="monospace",bbox=dict(facecolor="#06090f",edgecolor="#1a2540",boxstyle="round,pad=.3",alpha=.92))
    for j in range(len(showb),len(axes)): axes[j].set_visible(False)
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)

# Missing values
miss=df.isnull().sum(); miss_nz=miss[miss>0]
sec("🕳️","Missing Values","Column-level completeness — count + rate charts")
mc1,mc2c,mc3,mc4=st.columns(4,gap="small")
with mc1: mc("Cols w/ Missing",str(len(miss_nz)),f"of {df.shape[1]}","#ef4444" if len(miss_nz)>0 else "#10b981")
with mc2c:mc("Total Missing",f"{miss.sum():,}",f"{miss.sum()/(df.shape[0]*df.shape[1])*100:.3f}%","#ef4444" if miss.sum()>0 else "#10b981")
with mc3: mc("Complete Rows",f"{df.dropna().shape[0]:,}",f"{complete_p}% complete","#10b981" if complete_p>90 else "#f59e0b")
with mc4: mc("Placeholders",str(A["ph"]),"fake nulls detected","#f59e0b" if A["ph"]>0 else "#10b981")
st.markdown("<br>",unsafe_allow_html=True)
if miss_nz.empty:
    st.markdown("""<div class="empty-ok"><div style="font-size:1.8rem;margin-bottom:.5rem">✅</div>
    <div style="font-size:.95rem;font-weight:700;color:#10b981;font-family:'Syne',sans-serif">Perfect Completeness</div>
    <div style="font-size:.8rem;color:#6ee7b7;margin-top:.4rem">Every cell has a value. No imputation needed.</div></div>""",unsafe_allow_html=True)
else:
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,max(4,len(miss_nz)*.6+1.5)))
    colors=[PAL[i%len(PAL)] for i in range(len(miss_nz))]
    ax1.barh(miss_nz.index,miss_nz.values,color=colors,edgecolor="#020408",height=.65)
    ax1.set_title("Missing Count",fontsize=10,fontweight="600"); ax1.set_xlabel("Count"); ax1.invert_yaxis()
    for bar,val in zip(ax1.patches,miss_nz.values):
        ax1.text(bar.get_width()+miss_nz.max()*.015,bar.get_y()+bar.get_height()/2,f"{val:,}",va="center",ha="left",fontsize=7,color="#4a5a8a",fontfamily="monospace")
    mp=(miss_nz/len(df)*100).round(2)
    ax2.barh(mp.index,mp.values,color=colors,edgecolor="#020408",height=.65,alpha=.82)
    ax2.set_title("Missing Rate (%)",fontsize=10,fontweight="600"); ax2.set_xlabel("%"); ax2.invert_yaxis()
    for bar,val in zip(ax2.patches,mp.values):
        ax2.text(bar.get_width()+mp.max()*.015,bar.get_y()+bar.get_height()/2,f"{val}%",va="center",ha="left",fontsize=7,color="#4a5a8a",fontfamily="monospace")
    fig.tight_layout(pad=1.5); st.pyplot(fig); plt.close(fig)
    md=pd.DataFrame({"Column":miss_nz.index,"Missing":miss_nz.values,"Missing %":(miss_nz/len(df)*100).round(3).values,"Present":(len(df)-miss_nz).values,"Dtype":[str(df[c].dtype) for c in miss_nz.index]})
    st.dataframe(md,use_container_width=True,height=min(320,50+len(md)*38))

# ══════════════════════════════════════════════════════════════════════
#  §7  DETAILED FAULT REPORT
# ══════════════════════════════════════════════════════════════════════
sec("🔍","Detailed Fault Report","Expand each dimension · full findings + code recommendations")
panels=[
    ("🕳️  Completeness",A["S"]["Completeness"],[
        ("#ef4444" if A["nc"]>0 else "#10b981",f"True null cells: <strong>{A['nc']:,}</strong>"),
        ("#f59e0b" if A["es"]>0 else "#10b981",f"Empty string cells: <strong>{A['es']:,}</strong>"),
        ("#f59e0b" if A["ph"]>0 else "#10b981",f"Placeholder strings (N/A, unknown): <strong>{A['ph']:,}</strong>"),
        ("#06b6d4","💡 Fix: "+("Complete." if A["tm"]==0 else "Impute numerics with median. Use mode/constant for categoricals. Drop cols >50% missing.")),
    ]),
    ("🪞  Uniqueness",A["S"]["Uniqueness"],[
        ("#ef4444" if A["ed"]>0 else "#10b981",f"Exact duplicate rows: <strong>{A['ed']:,}</strong>"),
        ("#f59e0b" if A["dc"] else "#10b981",f"Identical column pairs: <strong>{len(A['dc'])}</strong> — {', '.join([f'{a}↔{b}' for a,b in A['dc']]) or 'None'}"),
        ("#ef4444" if A["cc"] else "#10b981",f"Constant columns: <strong>{len(A['cc'])}</strong> — {', '.join(A['cc']) or 'None'}"),
        ("#06b6d4","💡 Fix: "+("No duplicates." if A["ed"]==0 else "Use <code>df.drop_duplicates()</code>. Drop constant columns.")),
    ]),
    ("🔀  Consistency",A["S"]["Consistency"],[
        ("#ef4444" if A["mx"] else "#10b981",f"Mixed-type columns: <strong>{len(A['mx'])}</strong> — {', '.join(A['mx']) or 'None'}"),
        ("#f59e0b" if A["ca"] else "#10b981",f"Case-inconsistent: <strong>{len(A['ca'])}</strong> — {', '.join(A['ca']) or 'None'}"),
        ("#ef4444" if A["en"] else "#10b981",f"Encoding artifacts: <strong>{len(A['en'])}</strong> — {', '.join(A['en']) or 'None'}"),
        ("#06b6d4","💡 Fix: Normalise with <code>.str.lower().str.strip()</code>. Re-read with <code>encoding='utf-8'</code>."),
    ]),
    ("📐  Validity",A["S"]["Validity"],[
        ("#f59e0b" if A["oc"] else "#10b981",f"Outlier columns (3×IQR): <strong>{len(A['oc'])}</strong>"+(" — "+", ".join(f"{o['col']} ({o['count']})" for o in A["oc"][:5]) if A["oc"] else "")),
        ("#ef4444" if A["im"] else "#10b981",f"Domain violations: <strong>{len(A['im'])}</strong> — {', '.join(A['im']) or 'None'}"),
        ("#06b6d4","💡 Fix: Winsorize or clip outliers. Set impossible values to NaN then impute."),
    ]),
    ("📉  Accuracy",A["S"]["Accuracy"],[
        ("#f59e0b" if A["sk"] else "#10b981",f"Skewed columns |skew|>2: <strong>{len(A['sk'])}</strong>"+(" — "+", ".join(f"{s['col']} ({s['skew']})" for s in A["sk"][:4]) if A["sk"] else "")),
        ("#f59e0b" if A["ib"] else "#10b981",f"Imbalanced categoricals >85%: <strong>{len(A['ib'])}</strong> — {', '.join(A['ib']) or 'None'}"),
        ("#06b6d4","💡 Fix: Apply <code>np.log1p()</code> or Box-Cox. Use <code>class_weight='balanced'</code>."),
    ]),
    ("🏗️  Structure",A["S"]["Structure"],[
        ("#ef4444" if A["bn"] else "#10b981",f"Bad column names: <strong>{len(A['bn'])}</strong> — {', '.join(str(c) for c in A['bn']) or 'None'}"),
        ("#f59e0b" if A["wt"] else "#10b981",f"Wrong dtype (numeric as string): <strong>{len(A['wt'])}</strong> — {', '.join(A['wt']) or 'None'}"),
        ("#ef4444" if A["er"]>0 else "#10b981",f"Fully empty rows: <strong>{A['er']}</strong>"),
        ("#06b6d4","💡 Fix: Rename to snake_case. Cast with <code>pd.to_numeric(errors='coerce')</code>."),
    ]),
    ("🔗  Correlation",A["S"]["Correlation"],[
        ("#f59e0b" if A["hc"] else "#10b981",f"Highly correlated pairs r>0.95: <strong>{len(A['hc'])}</strong>"+(" — "+", ".join(f"{p['a']}↔{p['b']} ({p['r']})" for p in A["hc"][:3]) if A["hc"] else "")),
        ("#06b6d4","💡 Fix: Drop one from each correlated pair. Use PCA for dimensionality reduction."),
    ]),
]
for title,score,items in panels:
    g="A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
    with st.expander(f"{title}  ·  {score:.1f} / 100  ·  Grade {g}"):
        for dot,html in items: rfind(dot,html)

# ══════════════════════════════════════════════════════════════════════
#  §8  DOWNLOAD AUDIT REPORT  (detailed CSV)
# ══════════════════════════════════════════════════════════════════════
sec("📥","Download Audit Report","Export a detailed CSV of every issue found in your dataset")

import io

def build_audit_csv(df, A):
    rows = []

    # ── 1. DQS summary row ──────────────────────────────────────────
    rows.append({
        "Issue_ID":       "DQS-000",
        "Dimension":      "Summary",
        "Severity":       "INFO",
        "Column":         "— (dataset level)",
        "Issue_Type":     "Dataset Quality Score",
        "Detail":         f"DQS = {A['DQS']} / 100  |  Grade {dqs_grade(A['DQS'])[1]} — {dqs_grade(A['DQS'])[2]}",
        "Affected_Rows":  df.shape[0],
        "Affected_Cols":  df.shape[1],
        "Value_Example":  "",
        "Fix_Recommendation": f"Raw={A['raw']:.3f}  Size_Factor={A['sf']:.3f}  Diversity_Bonus={A['db']:.4f}",
    })

    # ── 2. Missing values — per column ──────────────────────────────
    issue_id = 1
    for col in df.columns:
        nc_col = int(df[col].isnull().sum())
        if nc_col > 0:
            pct = round(nc_col / len(df) * 100, 3)
            rows.append({
                "Issue_ID":       f"COMP-{issue_id:03d}",
                "Dimension":      "Completeness",
                "Severity":       "HIGH" if pct > 20 else "MEDIUM" if pct > 5 else "LOW",
                "Column":         col,
                "Issue_Type":     "Null / NaN values",
                "Detail":         f"{nc_col:,} null cells ({pct}% of column)",
                "Affected_Rows":  nc_col,
                "Affected_Cols":  1,
                "Value_Example":  "NaN",
                "Fix_Recommendation": "Impute with median (numeric) or mode/constant (categorical). Drop column if >50% null.",
            })
            issue_id += 1

    # ── 3. Placeholder strings — per column ─────────────────────────
    PH = {"n/a","na","none","null","nil","-","--","?","unknown","undefined","missing","tbd","tbc","#n/a"}
    issue_id = 1
    for col in df.select_dtypes("object").columns:
        vals = df[col].dropna().astype(str)
        ph_mask = vals.str.strip().str.lower().isin(PH)
        ph_count = int(ph_mask.sum())
        if ph_count > 0:
            examples = vals[ph_mask].unique()[:3].tolist()
            rows.append({
                "Issue_ID":       f"COMP-PH-{issue_id:03d}",
                "Dimension":      "Completeness",
                "Severity":       "MEDIUM",
                "Column":         col,
                "Issue_Type":     "Placeholder / fake null string",
                "Detail":         f"{ph_count:,} cells contain filler values",
                "Affected_Rows":  ph_count,
                "Affected_Cols":  1,
                "Value_Example":  ", ".join(str(e) for e in examples),
                "Fix_Recommendation": "Replace with NaN: df[col].replace(['N/A','unknown','-'], np.nan)",
            })
            issue_id += 1

    # ── 4. Duplicate rows ────────────────────────────────────────────
    if A["ed"] > 0:
        dup_idx = df[df.duplicated()].index.tolist()
        rows.append({
            "Issue_ID":       "UNIQ-001",
            "Dimension":      "Uniqueness",
            "Severity":       "HIGH" if A["ed"] > len(df)*0.05 else "MEDIUM",
            "Column":         "— (all columns)",
            "Issue_Type":     "Exact duplicate rows",
            "Detail":         f"{A['ed']:,} rows are exact duplicates ({round(A['ed']/len(df)*100,2)}% of dataset)",
            "Affected_Rows":  A["ed"],
            "Affected_Cols":  df.shape[1],
            "Value_Example":  f"Row indices: {dup_idx[:5]}",
            "Fix_Recommendation": "df.drop_duplicates(inplace=True)",
        })

    # ── 5. Constant / zero-variance columns ─────────────────────────
    for i, col in enumerate(A["cc"]):
        rows.append({
            "Issue_ID":       f"UNIQ-CC-{i+1:03d}",
            "Dimension":      "Uniqueness",
            "Severity":       "MEDIUM",
            "Column":         col,
            "Issue_Type":     "Constant / zero-variance column",
            "Detail":         f"Column has only 1 unique value: '{df[col].dropna().unique()[0] if df[col].dropna().shape[0]>0 else 'N/A'}'",
            "Affected_Rows":  len(df),
            "Affected_Cols":  1,
            "Value_Example":  str(df[col].dropna().unique()[0]) if df[col].dropna().shape[0]>0 else "N/A",
            "Fix_Recommendation": f"df.drop(columns=['{col}'], inplace=True)",
        })

    # ── 6. Mixed-type columns ────────────────────────────────────────
    for i, col in enumerate(A["mx"]):
        rows.append({
            "Issue_ID":       f"CONS-MX-{i+1:03d}",
            "Dimension":      "Consistency",
            "Severity":       "HIGH",
            "Column":         col,
            "Issue_Type":     "Mixed data types (numeric + string)",
            "Detail":         f"Column '{col}' contains both numeric and text values",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  str(df[col].dropna().iloc[0]) if df[col].dropna().shape[0]>0 else "",
            "Fix_Recommendation": f"Clean non-numeric values then cast: pd.to_numeric(df['{col}'], errors='coerce')",
        })

    # ── 7. Case inconsistency ────────────────────────────────────────
    for i, col in enumerate(A["ca"]):
        vals = df[col].dropna().astype(str).str.strip()
        examples = vals.unique()[:4].tolist()
        rows.append({
            "Issue_ID":       f"CONS-CA-{i+1:03d}",
            "Dimension":      "Consistency",
            "Severity":       "LOW",
            "Column":         col,
            "Issue_Type":     "Case inconsistency",
            "Detail":         f"Same values appear in different cases (e.g. 'Yes' vs 'yes' vs 'YES')",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  ", ".join(str(e) for e in examples),
            "Fix_Recommendation": f"df['{col}'] = df['{col}'].str.lower().str.strip()",
        })

    # ── 8. Outliers — per column ─────────────────────────────────────
    for i, o in enumerate(A["oc"]):
        col = o["col"]; count = o["count"]
        d = df[col].dropna()
        Q1, Q3 = d.quantile(.25), d.quantile(.75); IQR = Q3 - Q1
        lower, upper = Q1 - 3*IQR, Q3 + 3*IQR
        outlier_vals = d[(d < lower) | (d > upper)].round(4).tolist()
        rows.append({
            "Issue_ID":       f"VALD-OUT-{i+1:03d}",
            "Dimension":      "Validity",
            "Severity":       "HIGH" if count > len(df)*0.05 else "MEDIUM",
            "Column":         col,
            "Issue_Type":     "Extreme outliers (3×IQR rule)",
            "Detail":         f"{count} extreme values | Q1={round(Q1,3)} Q3={round(Q3,3)} IQR={round(IQR,3)} | Lower fence={round(lower,3)} Upper fence={round(upper,3)}",
            "Affected_Rows":  count,
            "Affected_Cols":  1,
            "Value_Example":  ", ".join(str(v) for v in outlier_vals[:5]),
            "Fix_Recommendation": f"Investigate visually. Cap: df['{col}'] = df['{col}'].clip({round(lower,3)}, {round(upper,3)})",
        })

    # ── 9. Domain violations ─────────────────────────────────────────
    for i, col in enumerate(A["im"]):
        rows.append({
            "Issue_ID":       f"VALD-DOM-{i+1:03d}",
            "Dimension":      "Validity",
            "Severity":       "HIGH",
            "Column":         col,
            "Issue_Type":     "Domain violation (impossible values)",
            "Detail":         f"Column '{col}' contains values outside the expected domain range",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  str(df[col].dropna().min()),
            "Fix_Recommendation": f"Set invalid values to NaN: df.loc[invalid_mask, '{col}'] = np.nan",
        })

    # ── 10. Skewed columns ───────────────────────────────────────────
    for i, s in enumerate(A["sk"]):
        col = s["col"]; skew = s["skew"]
        rows.append({
            "Issue_ID":       f"ACCR-SK-{i+1:03d}",
            "Dimension":      "Accuracy",
            "Severity":       "HIGH" if abs(skew) > 5 else "MEDIUM",
            "Column":         col,
            "Issue_Type":     "Highly skewed distribution",
            "Detail":         f"Skewness = {skew} (|skew| > 2 is problematic for ML models)",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  f"min={round(df[col].min(),3)}  max={round(df[col].max(),3)}  mean={round(df[col].mean(),3)}",
            "Fix_Recommendation": f"df['{col}'] = np.log1p(df['{col}'])  # or use sklearn PowerTransformer",
        })

    # ── 11. Imbalanced categoricals ──────────────────────────────────
    for i, col in enumerate(A["ib"]):
        vc = df[col].value_counts(normalize=True)
        dom_class = vc.index[0]; dom_pct = round(float(vc.iloc[0])*100, 2)
        rows.append({
            "Issue_ID":       f"ACCR-IB-{i+1:03d}",
            "Dimension":      "Accuracy",
            "Severity":       "MEDIUM",
            "Column":         col,
            "Issue_Type":     "Imbalanced categorical (dominant class >85%)",
            "Detail":         f"'{dom_class}' dominates at {dom_pct}% of all values",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  str(dom_class),
            "Fix_Recommendation": "Use stratified sampling, SMOTE, or class_weight='balanced' in your model",
        })

    # ── 12. Bad column names ─────────────────────────────────────────
    for i, col in enumerate(A["bn"]):
        rows.append({
            "Issue_ID":       f"STRC-BN-{i+1:03d}",
            "Dimension":      "Structure",
            "Severity":       "LOW",
            "Column":         str(col),
            "Issue_Type":     "Bad column name (special chars / Unnamed)",
            "Detail":         f"Column name '{col}' contains special characters or is auto-generated",
            "Affected_Rows":  len(df),
            "Affected_Cols":  1,
            "Value_Example":  str(col),
            "Fix_Recommendation": f"df.rename(columns={{'{col}': 'clean_name'}}, inplace=True)",
        })

    # ── 13. Wrong dtype columns ──────────────────────────────────────
    for i, col in enumerate(A["wt"]):
        rows.append({
            "Issue_ID":       f"STRC-WT-{i+1:03d}",
            "Dimension":      "Structure",
            "Severity":       "MEDIUM",
            "Column":         col,
            "Issue_Type":     "Wrong dtype (numeric stored as string/object)",
            "Detail":         f"Column '{col}' is dtype=object but >95% of values are numeric",
            "Affected_Rows":  int(df[col].notna().sum()),
            "Affected_Cols":  1,
            "Value_Example":  str(df[col].dropna().iloc[0]) if df[col].dropna().shape[0]>0 else "",
            "Fix_Recommendation": f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')",
        })

    # ── 14. Highly correlated pairs ──────────────────────────────────
    for i, p in enumerate(A["hc"]):
        rows.append({
            "Issue_ID":       f"CORR-{i+1:03d}",
            "Dimension":      "Correlation",
            "Severity":       "HIGH" if p["r"] > 0.999 else "MEDIUM",
            "Column":         f"{p['a']}  ↔  {p['b']}",
            "Issue_Type":     "Highly correlated column pair (r > 0.95)",
            "Detail":         f"Pearson r = {p['r']} — these columns carry near-identical information",
            "Affected_Rows":  len(df),
            "Affected_Cols":  2,
            "Value_Example":  f"r = {p['r']}",
            "Fix_Recommendation": f"Drop one: df.drop(columns=['{p['b']}'], inplace=True)  # or use PCA",
        })

    # ── 15. Fully empty rows ─────────────────────────────────────────
    if A["er"] > 0:
        empty_row_idx = df[df.isnull().all(axis=1)].index.tolist()
        rows.append({
            "Issue_ID":       "STRC-ER-001",
            "Dimension":      "Structure",
            "Severity":       "HIGH",
            "Column":         "— (all columns)",
            "Issue_Type":     "Fully empty rows",
            "Detail":         f"{A['er']} rows have no values in any column",
            "Affected_Rows":  A["er"],
            "Affected_Cols":  df.shape[1],
            "Value_Example":  f"Row indices: {empty_row_idx[:5]}",
            "Fix_Recommendation": "df.dropna(how='all', inplace=True)",
        })

    # ── 16. Dimension score summary rows ────────────────────────────
    for dim, score in A["S"].items():
        g = "A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
        rows.append({
            "Issue_ID":       f"SCORE-{dim[:4].upper()}",
            "Dimension":      dim,
            "Severity":       "SCORE",
            "Column":         "— (dimension level)",
            "Issue_Type":     f"{dim} Dimension Score",
            "Detail":         f"Score = {score:.2f} / 100  |  Weight = {int(A['W'][dim]*100)}%  |  Grade {g}",
            "Affected_Rows":  "",
            "Affected_Cols":  "",
            "Value_Example":  "",
            "Fix_Recommendation": "",
        })

    return pd.DataFrame(rows)

# Build the CSV
audit_df = build_audit_csv(df, A)

# Severity counts for the summary
sev_counts = audit_df[audit_df["Severity"].isin(["HIGH","MEDIUM","LOW"])]["Severity"].value_counts()
high_c  = sev_counts.get("HIGH",  0)
med_c   = sev_counts.get("MEDIUM",0)
low_c   = sev_counts.get("LOW",   0)
total_issues = high_c + med_c + low_c

st.markdown(f"""
<div style="background:rgba(255,255,255,.022);border:1px solid var(--b2);border-radius:var(--rl);
            padding:1.8rem;backdrop-filter:blur(20px);
            box-shadow:0 8px 40px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.04);
            margin-bottom:1.2rem">

  <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1.2rem">
    <span style="font-size:1.3rem">📥</span>
    <div>
      <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:var(--t)">Detailed Audit Report</div>
      <div style="font-size:.78rem;color:var(--t2);margin-top:.25rem">{len(audit_df)} rows · every issue documented with column, severity, example value &amp; fix</div>
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
      <div style="font-size:1.6rem;font-weight:800;color:#3d7fff;font-family:'Syne',sans-serif">{total_issues}</div>
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:rgba(61,127,255,.7);margin-top:.2rem">Total Issues</div>
    </div>
  </div>

  <div style="font-size:.75rem;color:var(--t2);line-height:1.7;margin-bottom:1rem">
    The CSV includes: <strong style="color:var(--t)">Issue ID · Dimension · Severity · Column · Issue Type · Detail · Affected Rows · Value Example · Fix Recommendation</strong>
  </div>
</div>
""", unsafe_allow_html=True)

# Preview table
with st.expander("👁  Preview audit report (first 20 rows)", expanded=False):
    st.dataframe(audit_df.head(20), use_container_width=True, height=380)

# Download button
csv_buffer = io.StringIO()
audit_df.to_csv(csv_buffer, index=False)
csv_bytes = csv_buffer.getvalue().encode("utf-8")
fname = f"audit_report_{meta.get('name','dataset').replace('.','_').replace(' ','_')}.csv"

col_dl, col_info = st.columns([1, 3], gap="large")
with col_dl:
    st.download_button(
        label="⬇  Download Audit Report CSV",
        data=csv_bytes,
        file_name=fname,
        mime="text/csv",
        use_container_width=True,
    )
with col_info:
    st.markdown(f"""
    <div style="background:rgba(255,255,255,.018);border:1px solid var(--b);border-radius:10px;
                padding:.85rem 1.1rem;font-size:.77rem;color:var(--t2);line-height:1.8">
      <strong style="color:var(--t)">📄 {fname}</strong><br>
      {len(audit_df)} rows &nbsp;·&nbsp; 10 columns &nbsp;·&nbsp;
      {high_c} HIGH &nbsp;·&nbsp; {med_c} MEDIUM &nbsp;·&nbsp; {low_c} LOW severity issues<br>
      <span style="color:var(--t3)">Ready to open in Excel, Google Sheets, or import into Notion / Jira</span>
    </div>""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="margin-top:4rem;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,.04);display:flex;justify-content:space-between;align-items:center">
  <div style="font-size:.7rem;color:rgba(255,255,255,.12);font-family:'JetBrains Mono',monospace">◈ Data Audit System v3.0</div>
  <div style="font-size:.68rem;color:rgba(255,255,255,.1)">Upload a new file above to re-run</div>
</div>""",unsafe_allow_html=True)
