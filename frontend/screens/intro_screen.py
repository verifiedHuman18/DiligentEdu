"""Interactive 3D Intro / Splash Screen for DiligentEdu — Phases 1–23.

Architecture:
- Three.js "Knowledge Universe" rendered via components.html() — purely visual, no Streamlit communication.
- One centered "Enter DiligentEdu" button — native st.button(), no JS bridge.
- Subtle "Skip" link — native st.button() styled as text.
- Phased cinematic animation (~3s): particles → core → orbits → branding → ready.
- Session-state handoff: intro_completed → login screen.
- Zero browser navigation. Zero postMessage. Zero declare_component.
- WebGL fallback to static branding.
- prefers-reduced-motion support.
- Responsive viewport-relative layout.
"""

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# 3D Scene — self-contained HTML / Three.js (visual only, no Streamlit comms)
# ---------------------------------------------------------------------------
_INTRO_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden!important;background:#0D0A07;font-family:'Outfit',sans-serif;color:#EDE0DB;user-select:none}
#vp{position:fixed;inset:0;width:100%;height:100%;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#1A1310 0%,#0D0A07 60%,#050302 100%)}
canvas{position:absolute;inset:0;width:100%;height:100%;z-index:1}
/* ─── Branding Overlay ─── */
.brand{position:absolute;top:56%;left:50%;transform:translate(-50%,-50%);z-index:10;
display:flex;flex-direction:column;align-items:center;text-align:center;
width:100%;max-width:640px;padding:0 24px;pointer-events:none;
opacity:0;animation:brandUp .9s cubic-bezier(.16,1,.3,1) forwards}
.brand .ttl{font-size:clamp(2.4rem,5.5vw,4rem);font-weight:900;color:#FFF;
text-shadow:0 4px 36px rgba(251,191,36,.35),0 0 80px rgba(251,191,36,.12);margin-bottom:8px;line-height:1.1}
.brand .ac{background:linear-gradient(135deg,#FDE68A 0%,#FBBF24 45%,#F59E0B 100%);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.brand .tg{font-size:clamp(.82rem,1.6vw,1.1rem);font-weight:500;color:#B8A89E;letter-spacing:2px;text-transform:uppercase}
@keyframes brandUp{from{opacity:0;transform:translate(-50%,-42%)}to{opacity:1;transform:translate(-50%,-50%)}}
/* ─── Reduced Motion ─── */
@media(prefers-reduced-motion:reduce){.brand{animation:none!important;opacity:1!important}}
</style>
</head>
<body>
<div id="vp">
<canvas id="c"></canvas>
<div class="brand" id="brand">
<div class="ttl">Diligent<span class="ac">Edu</span></div>
<div class="tg">Learn · Understand · Grow</div>
</div>
</div>
<script>
(function(){
'use strict';
var brandEl=document.getElementById('brand');
var reduced=window.matchMedia('(prefers-reduced-motion:reduce)').matches;
/* Branding text appears during Phase 3 (~2.0s) */
brandEl.style.animationDelay=reduced?'0s':'2.0s';

try{
/* ═══════════ Scene Setup ═══════════ */
var W=window.innerWidth,H=window.innerHeight;
var scene=new THREE.Scene();
var cam=new THREE.PerspectiveCamera(45,W/H,0.1,1000);
cam.position.set(0,0,22);
var ren=new THREE.WebGLRenderer({canvas:document.getElementById('c'),alpha:true,antialias:true});
ren.setSize(W,H);ren.setPixelRatio(Math.min(window.devicePixelRatio,2));
ren.setClearColor(0x0D0A07,1);

/* ─── Mouse Parallax ─── */
var mx={x:0,y:0,tx:0,ty:0};
window.addEventListener('mousemove',function(e){mx.tx=(e.clientX/W)*2-1;mx.ty=-(e.clientY/H)*2+1});

/* ─── Lighting ─── */
scene.add(new THREE.AmbientLight(0xFFE8D6,0.65));
var pl1=new THREE.PointLight(0xFBBF24,3.0,65);pl1.position.set(0,1.5,6);scene.add(pl1);
var pl2=new THREE.PointLight(0x14B8A6,2.0,55);pl2.position.set(-9,7,2);scene.add(pl2);
var pl3=new THREE.PointLight(0xA855F7,2.0,55);pl3.position.set(9,-5,2);scene.add(pl3);

/* ═══════════ Core Group (Sphere + Wireframe Cage) ═══════════ */
var CY=0.8; /* Core center Y */
var core=new THREE.Group();core.position.set(0,CY,0);scene.add(core);
var sph=new THREE.Mesh(
    new THREE.SphereGeometry(2.4,32,32),
    new THREE.MeshPhongMaterial({color:0xFBBF24,emissive:0xB45309,emissiveIntensity:0.6,shininess:90,transparent:true,opacity:0})
);core.add(sph);
var cage=new THREE.Mesh(
    new THREE.IcosahedronGeometry(3.6,1),
    new THREE.MeshBasicMaterial({color:0xFDE68A,wireframe:true,transparent:true,opacity:0})
);core.add(cage);
core.scale.set(0.001,0.001,0.001);

/* ═══════════ 3 Orbital Rings ═══════════ */
var rGrp=new THREE.Group();rGrp.position.set(0,CY,0);scene.add(rGrp);
var rCfg=[
    {r:5.5,c:0xFBBF24,rx:Math.PI/3,ry:Math.PI/6,opMax:0.60},
    {r:7.2,c:0x14B8A6,rx:-Math.PI/4,ry:Math.PI/3,opMax:0.50},
    {r:9.0,c:0xA855F7,rx:Math.PI/2.2,ry:-Math.PI/5,opMax:0.50}
];
var rings=[];
rCfg.forEach(function(d){
    var m=new THREE.Mesh(
        new THREE.RingGeometry(d.r-0.04,d.r+0.04,64),
        new THREE.MeshBasicMaterial({color:d.c,transparent:true,opacity:0,side:THREE.DoubleSide})
    );
    m.rotation.x=d.rx;m.rotation.y=d.ry;
    m._opMax=d.opMax;
    rGrp.add(m);rings.push(m);
});
rGrp.scale.set(0.001,0.001,0.001);

/* ═══════════ 3 Academic Satellites ═══════════ */
var sGrp=new THREE.Group();sGrp.position.set(0,CY,0);scene.add(sGrp);
var sat1=new THREE.Mesh(new THREE.OctahedronGeometry(0.55),new THREE.MeshPhongMaterial({color:0xFBBF24,emissive:0xF59E0B,emissiveIntensity:0.8,transparent:true,opacity:0}));
var sat2=new THREE.Mesh(new THREE.DodecahedronGeometry(0.48),new THREE.MeshPhongMaterial({color:0x14B8A6,emissive:0x0D9488,emissiveIntensity:0.8,transparent:true,opacity:0}));
var sat3=new THREE.Mesh(new THREE.TetrahedronGeometry(0.55),new THREE.MeshPhongMaterial({color:0xA855F7,emissive:0x7E22CE,emissiveIntensity:0.8,transparent:true,opacity:0}));
sGrp.add(sat1);sGrp.add(sat2);sGrp.add(sat3);

/* ═══════════ Neural Filament Lines ═══════════ */
function mkLine(){
    var g=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]);
    var m=new THREE.LineBasicMaterial({color:0xFBBF24,transparent:true,opacity:0,blending:THREE.AdditiveBlending});
    var l=new THREE.Line(g,m);scene.add(l);return{g:g,m:m,l:l};
}
var nl1=mkLine(),nl2=mkLine(),nl3=mkLine();

/* ═══════════ Background Particle Field ═══════════ */
var PC=320;
var pGeo=new THREE.BufferGeometry();
var pPos=new Float32Array(PC*3),pClr=new Float32Array(PC*3);
var pal=[new THREE.Color(0xFBBF24),new THREE.Color(0x14B8A6),new THREE.Color(0xA855F7),new THREE.Color(0xF97316),new THREE.Color(0xFFFFFF)];
for(var i=0;i<PC;i++){
    pPos[i*3]=(Math.random()-0.5)*52;pPos[i*3+1]=(Math.random()-0.5)*36;pPos[i*3+2]=(Math.random()-0.5)*42;
    var c=pal[Math.floor(Math.random()*pal.length)];pClr[i*3]=c.r;pClr[i*3+1]=c.g;pClr[i*3+2]=c.b;
}
pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3));
pGeo.setAttribute('color',new THREE.BufferAttribute(pClr,3));
var pts=new THREE.Points(pGeo,new THREE.PointsMaterial({size:0.28,vertexColors:true,transparent:true,opacity:0,blending:THREE.AdditiveBlending}));
scene.add(pts);

/* ═══════════ Assembly Particles (converge to core in Phase 1) ═══════════ */
var APC=80;
var aGeo=new THREE.BufferGeometry();
var aPos=new Float32Array(APC*3),aStart=new Float32Array(APC*3),aClr=new Float32Array(APC*3);
for(var i=0;i<APC;i++){
    var th=Math.random()*Math.PI*2,ph=Math.random()*Math.PI,r=12+Math.random()*18;
    aStart[i*3]=r*Math.sin(ph)*Math.cos(th);
    aStart[i*3+1]=CY+r*Math.sin(ph)*Math.sin(th);
    aStart[i*3+2]=r*Math.cos(ph);
    aPos[i*3]=aStart[i*3];aPos[i*3+1]=aStart[i*3+1];aPos[i*3+2]=aStart[i*3+2];
    var c2=pal[Math.floor(Math.random()*3)];aClr[i*3]=c2.r;aClr[i*3+1]=c2.g;aClr[i*3+2]=c2.b;
}
aGeo.setAttribute('position',new THREE.BufferAttribute(aPos,3));
aGeo.setAttribute('color',new THREE.BufferAttribute(aClr,3));
var aPts=new THREE.Points(aGeo,new THREE.PointsMaterial({size:0.38,vertexColors:true,transparent:true,opacity:0,blending:THREE.AdditiveBlending}));
scene.add(aPts);

/* ─── Easing ─── */
function easeOut(x){return 1-Math.pow(1-x,3)}

/* ─── Resize ─── */
window.addEventListener('resize',function(){W=window.innerWidth;H=window.innerHeight;cam.aspect=W/H;cam.updateProjectionMatrix();ren.setSize(W,H)});

/* ═══════════ Animation Loop ═══════════
   Phase 0 (0.0–0.5s): Background particles fade in, assembly particles appear far away
   Phase 1 (0.5–1.2s): Assembly particles converge to center, Knowledge Core materializes
   Phase 2 (1.2–2.0s): Orbital rings scale up, satellites appear & start orbiting
   Phase 3 (2.0–2.8s): Branding text fades in (CSS), scene stabilizes
   Phase 4 (2.8s+):    Continuous gentle animation — core rotates/pulses, orbits continue
*/
var T0=performance.now();
var clk=new THREE.Clock();

function anim(){
requestAnimationFrame(anim);
var elapsed=(performance.now()-T0)/1000;
var t=clk.getElapsedTime();

/* ─── Phase & progress ─── */
var ph,pg;
if(reduced){ph=4;pg=1;}
else if(elapsed<0.5){ph=0;pg=elapsed/0.5;}
else if(elapsed<1.2){ph=1;pg=(elapsed-0.5)/0.7;}
else if(elapsed<2.0){ph=2;pg=(elapsed-1.2)/0.8;}
else if(elapsed<2.8){ph=3;pg=(elapsed-2.0)/0.8;}
else{ph=4;pg=1;}
var ep=easeOut(Math.min(pg,1));

/* ─── Mouse parallax ─── */
mx.x+=(mx.tx-mx.x)*0.05;mx.y+=(mx.ty-mx.y)*0.05;
cam.position.x=mx.x*1.8;cam.position.y=mx.y*1.4;cam.lookAt(0,CY,0);

/* ═══ Phase 0: Background particles fade in ═══ */
pts.material.opacity=ph===0?ep*0.75:0.75;
pts.rotation.y=t*0.04;pts.rotation.x=Math.sin(t*0.05)*0.04;
pts.position.x=-mx.x*1.5;pts.position.y=-mx.y*1.2;

/* Assembly particles: appear in Phase 0, converge in Phase 1, fade after Phase 1 */
if(ph===0){
    aPts.material.opacity=ep*0.55;
}else if(ph===1){
    aPts.material.opacity=(1-ep)*0.65;
    var ap=aGeo.attributes.position.array;
    for(var i=0;i<APC;i++){
        ap[i*3]=aStart[i*3]*(1-ep);
        ap[i*3+1]=CY+(aStart[i*3+1]-CY)*(1-ep);
        ap[i*3+2]=aStart[i*3+2]*(1-ep);
    }
    aGeo.attributes.position.needsUpdate=true;
}else if(ph===2&&pg<0.3){
    aPts.material.opacity=(1-pg/0.3)*0.2;
}else{
    aPts.material.opacity=0;
}

/* ═══ Phase 1: Core materializes ═══ */
if(ph>=1){
    var cs=ph===1?ep:1;
    core.scale.set(cs,cs,cs);
    sph.material.opacity=cs*0.88;
    cage.material.opacity=cs*0.45;
}

/* ═══ Phase 2+: Core rotation & pulse, rings, satellites ═══ */
if(ph>=2){
    /* Core animation */
    core.rotation.y=t*0.45;core.rotation.x=Math.sin(t*0.3)*0.15;
    var pulse=1+Math.sin(t*2.5)*0.03;
    core.scale.set(pulse,pulse,pulse);
    cage.rotation.y=-t*0.3;cage.rotation.z=t*0.2;
    core.position.x=mx.x*0.25;core.position.y=CY+mx.y*0.2;

    /* Rings scale in */
    var rs=ph===2?ep:1;
    rGrp.scale.set(rs,rs,rs);
    rings.forEach(function(ring){ring.material.opacity=rs*ring._opMax});
    rings[0].rotation.z=t*0.35;rings[1].rotation.z=-t*0.25;rings[2].rotation.z=t*0.18;
    rGrp.position.x=mx.x*0.5;rGrp.position.y=CY+mx.y*0.35;

    /* Satellites fade in & orbit */
    sat1.material.opacity=rs;sat2.material.opacity=rs;sat3.material.opacity=rs;
    var o1=t*0.9;
    sat1.position.set(Math.cos(o1)*5.5,Math.sin(o1)*5.5*Math.cos(Math.PI/3),Math.sin(o1)*5.5*Math.sin(Math.PI/3));
    sat1.rotation.x=t*1.5;sat1.rotation.y=t*1.2;
    var o2=-t*0.75+1.2;
    sat2.position.set(Math.cos(o2)*7.2,Math.sin(o2)*7.2*Math.cos(-Math.PI/4),Math.sin(o2)*7.2*Math.sin(-Math.PI/4));
    sat2.rotation.x=t*1.2;sat2.rotation.z=t*1.4;
    var o3=t*0.6+2.4;
    sat3.position.set(Math.cos(o3)*9,Math.sin(o3)*9*Math.cos(Math.PI/2.2),Math.sin(o3)*9*Math.sin(Math.PI/2.2));
    sat3.rotation.y=t*1.6;

    /* Neural lines */
    var nop=rs*0.22;
    nl1.m.opacity=nop;nl2.m.opacity=nop;nl3.m.opacity=nop;
    var cp=core.position;
    nl1.g.setFromPoints([cp,sat1.position]);
    nl2.g.setFromPoints([cp,sat2.position]);
    nl3.g.setFromPoints([cp,sat3.position]);
}

/* Light ramp */
pl1.intensity=ph>=1?3.0:3.0*Math.max(0.25,ep);

ren.render(scene,cam);
}
anim();

}catch(e){
/* ═══ WebGL Fallback: static branded splash ═══ */
document.getElementById('vp').style.background='radial-gradient(ellipse at 50% 40%,#1A1310,#0D0A07 60%,#050302)';
document.getElementById('vp').innerHTML=
'<div class="brand" style="opacity:1;animation:none">'
+'<div class="ttl">Diligent<span class="ac">Edu</span></div>'
+'<div class="tg">Learn \u00b7 Understand \u00b7 Grow</div></div>';
}
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Render Function
# ---------------------------------------------------------------------------
def render_intro_screen() -> None:
    """Renders the fullscreen 3D intro with a single native Streamlit Enter button.

    Flow: App opens → 3D animation (~3s) → user clicks Enter → login screen.
    No expensive backend resources are initialized during the intro.
    """

    # ── Fullscreen CSS: positions 3D iframe, Enter button, Skip link ──
    st.markdown(
        r"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;600;700;800;900&display=swap');

            /* ─── Hide Streamlit Chrome ─── */
            header[data-testid="stHeader"],
            footer,
            [data-testid="stSidebar"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"] {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }

            /* ─── App Background ─── */
            .stApp {
                background-color: #0D0A07 !important;
                overflow: hidden !important;
            }
            section.main,
            [data-testid="stAppViewContainer"],
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100vw !important;
                overflow: hidden !important;
            }

            /* ─── 3D Iframe: Fixed Fullscreen ─── */
            [data-testid="stMainBlockContainer"] iframe {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                border: none !important;
                z-index: 1 !important;
            }

            /* ─── Enter Button (centered, appears at ~2.5s) ─── */
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) {
                position: fixed !important;
                bottom: 16% !important;
                left: 50% !important;
                z-index: 99999 !important;
                width: auto !important;
                animation: introFadeEnter 0.9s cubic-bezier(.16,1,.3,1) 2.5s both !important;
            }
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) button {
                background: rgba(30, 22, 16, 0.82) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1.5px solid rgba(251, 191, 36, 0.40) !important;
                border-radius: 32px !important;
                font-family: 'Inter', 'Outfit', system-ui, sans-serif !important;
                font-size: 0.88rem !important;
                font-weight: 700 !important;
                letter-spacing: 2.5px !important;
                text-transform: uppercase !important;
                color: #FBBF24 !important;
                padding: 16px 48px !important;
                cursor: pointer !important;
                box-shadow: 0 0 28px rgba(251,191,36,0.25), inset 0 0 12px rgba(251,191,36,0.06) !important;
                transition: all 0.25s ease !important;
                animation: introGlow 2.8s infinite ease-in-out !important;
                white-space: nowrap !important;
            }
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) button:hover {
                background: rgba(251, 191, 36, 0.16) !important;
                border-color: rgba(251, 191, 36, 0.70) !important;
                box-shadow: 0 0 48px rgba(251,191,36,0.55), inset 0 0 20px rgba(251,191,36,0.10) !important;
                transform: scale(1.05) !important;
                color: #FDE68A !important;
            }

            /* ─── Skip Link (bottom-right, appears at ~1s) ─── */
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-secondary"]) {
                position: fixed !important;
                bottom: 28px !important;
                right: 32px !important;
                z-index: 99999 !important;
                width: auto !important;
                animation: introFadeSkip 0.5s ease 1.0s both !important;
            }
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-secondary"]) button {
                background: transparent !important;
                border: none !important;
                color: #6B5D55 !important;
                font-family: 'Inter', system-ui, sans-serif !important;
                font-size: 0.8rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.5px !important;
                padding: 8px 14px !important;
                cursor: pointer !important;
                box-shadow: none !important;
                transition: color 0.2s ease !important;
            }
            div[data-testid="stButton"]:has(button[data-testid="stBaseButton-secondary"]) button:hover {
                color: #FBBF24 !important;
            }

            /* ─── Keyframes ─── */
            @keyframes introFadeEnter {
                0%   { opacity: 0; transform: translateX(-50%) translateY(18px); }
                100% { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
            @keyframes introFadeSkip {
                0%   { opacity: 0; }
                100% { opacity: 1; }
            }
            @keyframes introGlow {
                0%, 100% { box-shadow: 0 0 22px rgba(251,191,36,0.20), inset 0 0 10px rgba(251,191,36,0.04); }
                50%      { box-shadow: 0 0 40px rgba(251,191,36,0.45), inset 0 0 16px rgba(251,191,36,0.08); }
            }

            /* ─── Reduced Motion ─── */
            @media (prefers-reduced-motion: reduce) {
                div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) {
                    animation-delay: 0s !important;
                }
                div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) button {
                    animation: none !important;
                }
                div[data-testid="stButton"]:has(button[data-testid="stBaseButton-secondary"]) {
                    animation-delay: 0s !important;
                }
            }

            /* ─── Responsive ─── */
            @media (max-width: 600px) {
                div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) {
                    bottom: 20% !important;
                }
                div[data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) button {
                    padding: 14px 32px !important;
                    font-size: 0.78rem !important;
                    letter-spacing: 1.5px !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── 1. 3D Scene (visual only — no Streamlit communication) ──
    components.html(_INTRO_HTML, height=700, scrolling=False)

    # ── 2. Single Centered Enter Button (native Streamlit widget) ──
    enter_clicked = st.button(
        "✦  Enter DiligentEdu  ✦",
        key="intro_enter_btn",
        type="primary",
    )

    # ── 3. Subtle Skip Link (native Streamlit widget) ──
    skip_clicked = st.button("Skip intro →", key="intro_skip_btn")

    # ── 4. Either click → session state transition → login ──
    if enter_clicked or skip_clicked:
        st.session_state.intro_completed = True
        st.rerun()
