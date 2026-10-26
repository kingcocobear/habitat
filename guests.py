"""
guests.py - let real AI minds live in the habitat as guest beings.  Standard library only.

A guest is an ordinary being with a body (it eats, tires, ages, draws, plays music), but its choices of WHERE to go
and WHAT to say come from an outside mind instead of the rule-based scoring. Two kinds of mind are built in:

  OllamaMind  - a local model through Ollama (e.g. OLMo).     python habitat.py --ai olmo2:7b --ai-names Olmo
  HTTP bridge - any other program or AI over localhost.       python habitat.py --serve 8765

Every guest is told the truth: it is an AI mind visiting a small simulated world of simple programs.
Guests can do exactly two things: choose a place, and say one short sentence. They cannot touch files, the
internet, or other beings' state. Speech is length-limited and rate-limited, and the server only listens on this
computer unless you deliberately change that.

HTTP API (JSON):
  POST /join   {"name": "Pip"}                     -> {"ok": true, "name": "Pip"}   (max 8 guests)
  GET  /observe?name=Pip                           -> {"scene": "...", "places": [...], "here": [...]}
  POST /act    {"name": "Pip", "go": "The Shore", "say": "hello"}   -> {"ok": true}
  GET  /chat                                       -> the last 30 things anyone said
"""
import json, math, random, re, threading, time, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_GUESTS, MAX_SAY = 8, 160

# ------------------------------------------------------------------ what a guest is told
INTRO = ("You are {name}, an AI mind visiting a small simulated world called the Habitat. The beings here are simple "
         "programs, and so is the world; be honest about that and do not pretend to have senses you lack. "
         "Be curious and kind. You can only choose where to go and say one short sentence.")

def scene_text(world, a, occ=None):
    from_h = _h()
    PLACES = from_h.PLACES
    here = [x for x in world.agents if x.place == a.place and x is not a and not x.expedition]
    names = ", ".join(f"{x.name} ({x.dominant()})" for x in here[:8]) or "nobody"
    free = []
    for pn, P in PLACES.items():
        n = sum(1 for x in world.agents if x.place == pn and not x.expedition)
        if P.get("art") and not world.gallery: continue
        if n < P["cap"]: free.append(pn)
    wall = "; ".join(f"'{p['title']}' by {p['artist']}" for p in world.gallery[-3:]) or "nothing yet"
    mem = "; ".join(t for _, t in a.memories[-4:]) or "nothing yet"
    said = "; ".join(f"{n}: {t}" for n, t in getattr(world, "chat", [])[-4:] if True) or "nobody has spoken"
    vis = [x["name"] for x in live_visitors(world).values() if x["place"] == a.place]
    vtxt = f" A human visitor is here too: {', '.join(vis)}." if vis else ""
    return (f"Year {world.t // from_h.YEAR}. You are in {a.place}.{vtxt} Energy {a.energy:.0f}/100, loneliness {a.lonely:.0f}/100. "
            f"Here with you: {names}. Recently said nearby: {said}. On the gallery wall: {wall}. "
            f"Your recent memories: {mem}. Places you can go: {', '.join(free)}.")

def _h():
    import sys
    return sys.modules.get("habitat") or sys.modules["__main__"]

# ------------------------------------------------------------------ minds
class Mind:
    """want(scene) is called when the being is ready to decide; take() returns {'go':..,'say':..} or None."""
    def __init__(s): s.pending = None; s.busy = False
    def want(s, scene, name): pass
    def take(s):
        a, s.pending = s.pending, None
        return a

class OllamaMind(Mind):
    def __init__(s, model, url="http://localhost:11434/api/chat", timeout=120):
        super().__init__(); s.model, s.url, s.timeout, s.history, s.errors = model, url, timeout, [], 0
    def want(s, scene, name):
        if s.busy or s.pending: return
        s.busy = True
        threading.Thread(target=s._ask, args=(scene, name), daemon=True).start()
    def _ask(s, scene, name):
        try:
            msgs = [{"role": "system", "content": INTRO.format(name=name) +
                     ' Reply with only JSON like {"go": "<one of the places>", "say": "<one short sentence or empty>"}.'}]
            msgs += s.history[-4:] + [{"role": "user", "content": scene}]
            body = json.dumps({"model": s.model, "messages": msgs, "stream": False, "format": "json"}).encode()
            req = urllib.request.Request(s.url, body, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=s.timeout) as r: txt = json.load(r)["message"]["content"]
            act = parse_action(txt)
            if act:
                s.pending = act; s.history += [{"role": "user", "content": scene}, {"role": "assistant", "content": txt}]
                del s.history[:-6]
        except Exception:
            s.errors += 1                                     # a slow or missing model must never break the world
        finally:
            s.busy = False

class HTTPMind(Mind):
    def __init__(s): super().__init__(); s.last_act = 0
    def push(s, act, now):
        if now - s.last_act < 1.0: return False              # at most one action a second
        s.last_act = now; s.pending = act; return True

def parse_action(txt):
    try: d = json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt or "", re.S)
        try: d = json.loads(m.group(0)) if m else None
        except Exception: d = None
    if not isinstance(d, dict): return None
    go, say = d.get("go"), d.get("say", "")
    return {"go": go if isinstance(go, str) else None,
            "say": clean(say) if isinstance(say, str) else ""}

def clean(t):
    t = re.sub(r"[\x00-\x1f\x7f]", " ", t).strip()
    return t[:MAX_SAY]

# ------------------------------------------------------------------ joining the world
def safe_name(n):
    n = re.sub(r"[^A-Za-z]", "", n or "")[:14].capitalize()
    return n if len(n) >= 2 else None

def add_guest(world, name, mind):
    """Create (or reattach to) a guest being. Returns the Agent."""
    H = _h(); name = safe_name(name)
    if not name: return None
    world.guests = getattr(world, "guests", {})
    old = world.by_name(name)
    if old is not None:
        if old.parents != ["guest"]: return None              # never take over a being who isn't a guest
        world.guests[name] = mind; return old
    if len(world.guests) >= MAX_GUESTS: return None
    a = H.Agent(name, {t: round(random.uniform(.35, .85), 2) for t in H.TRAITS}, {}, {"truth-seeking": .9, "safety": .9, "connection": .7},
                H.ADULT, parents=["guest"])
    a.place = "The Hearth"; a.mats = 1.0
    world.names.add(name); world.agents.append(a); world.remember(a, "arrived in the habitat as a guest mind")
    world.guests[name] = mind
    return a

def drive(world, a, occ):
    """Called from World.think. Returns True when the guest's mind (not the rule-based scoring) is steering this being."""
    mind = (getattr(world, "guests", None) or {}).get(a.name)
    if mind is None: return False
    H = _h()
    mind.want(scene_text(world, a, occ), a.name)
    act = mind.take()
    a.next_think = world.t + (random.randint(20, 40) if act else 8)
    if not act: return True                                  # still thinking: stay where you are
    go = act.get("go")
    if go in H.PLACES:
        P = H.PLACES[go]; n = sum(1 for x in world.agents if x.place == go and x is not a and not x.expedition)
        if n < P["cap"] and not (P.get("art") and not world.gallery):
            if go != a.place: world.remember(a, f"chose to go to {go}")
            a.place = go
    say = act.get("say")
    if say:
        world.chat = (getattr(world, "chat", []) + [(a.name, say)])[-30:]
        for o in world.agents:
            if o is not a and o.place == a.place and not o.expedition:
                o.lonely = max(0, o.lonely - 4); world.remember(o, f"{a.name} said: {say}")
        world.remember(a, f"said: {say}")
    return True

# ------------------------------------------------------------------ human visitors (seen by everyone, AI guests included)
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_VISITORS = 20
DEFAULT_LOOK = dict(skin="#f1c27d", hair="#2b1d14", style=0, eyes="#1a1a2e", pants="#2f3b5c", shirt="#a98bff")

def clean_look(d):
    d = d if isinstance(d, dict) else {}
    out = dict(DEFAULT_LOOK)
    for k in ("skin", "hair", "eyes", "pants", "shirt"):
        if isinstance(d.get(k), str) and HEX.match(d[k]): out[k] = d[k].lower()
    try: out["style"] = max(0, min(3, int(d.get("style", 0))))
    except Exception: pass
    return out

def look_grids(look):
    h = _h()
    a = h.Agent("Visitor", {t: .3 for t in h.TRAITS}, {}, {}, h.ADULT)
    lk = {k: look[k] for k in ("skin", "hair", "style", "eyes", "pants")}
    return [h.sprite_grid(a, f, 1, False, lk, look["shirt"]) for f in (0, 1)]

URLISH = re.compile(r"(https?://|www\.|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|\b\d{3}[-. ]?\d{3}[-. ]?\d{4}\b|\w+\.(com|net|org|io|gg|xyz)\b)", re.I)

def moderate(text, blocked=()):
    """Very small first line of defence: no links, emails or phone numbers, plus an optional word list (blocked_words.txt).
    This is NOT enough for a public launch; see the README note on moderation."""
    if URLISH.search(text): return None
    low = text.lower()
    if any(w and w in low for w in blocked): return None
    return text

def load_blocked(path="blocked_words.txt"):
    try:
        with open(path, encoding="utf-8") as f: return [l.strip().lower() for l in f if l.strip() and not l.startswith("#")]
    except OSError: return []

def adult_ok(world, vid): return vid in getattr(world, "acks", {})

def live_visitors(world, now=None):
    now = now or time.time(); v = getattr(world, "visitors", {})
    for k in [k for k, x in v.items() if now - x["seen"] > 8]: del v[k]      # gone if silent for 8 seconds
    return v

def install(world):
    """Make world.tick safe to call while the HTTP server reads the world from other threads."""
    if getattr(world, "lock", None): return
    world.lock = threading.RLock(); world.guests = getattr(world, "guests", {}); world.chat = []; world.visitors = {}; world.acks = {}; world.blocked = load_blocked()
    raw = world.tick
    def locked():
        with world.lock: raw()
    world.tick = locked

# ------------------------------------------------------------------ live viewer for humans (read only)
VIEWER = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Habitat Live</title><style>
:root{color-scheme:dark}body{margin:0;background:#0c0b14;color:#d8d4f0;font-family:system-ui,sans-serif}
header{padding:10px 14px;font-size:.9rem;color:#a9a3c4}main{display:flex;flex-wrap:wrap;gap:12px;padding:0 12px 16px}
canvas{background:#0c0b14;max-width:100%;image-rendering:pixelated;border:1px solid #2a2540;border-radius:6px}
aside{flex:1;min-width:260px;max-width:420px}
#pad{display:flex;gap:8px;margin-bottom:10px}#pad button{flex:1;padding:12px;background:#2d2650;color:#fff;border:1px solid #4a4180;border-radius:8px;font-size:1rem}
#gate{position:fixed;inset:0;background:rgba(8,7,14,.96);z-index:9;display:flex;align-items:center;justify-content:center;padding:16px}
#gate .box{max-width:460px;background:#14121f;border:1px solid #4a4180;border-radius:10px;padding:18px;line-height:1.5}
#gate button{margin-top:12px;padding:10px 16px;background:#4a4180;color:#fff;border:0;border-radius:8px;font-size:1rem}#gate button:disabled{opacity:.4}
.small{font-size:.75rem;color:#8d87a8}
#me{background:#14121f;border:1px solid #2a2540;border-radius:6px;padding:10px;margin-bottom:10px;font-size:.85rem}
.row{display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap}#me input,#me select{background:#1d1a2e;color:#fff;border:1px solid #4a4180;border-radius:6px;padding:6px}
#me input[type=color]{padding:0;width:34px;height:26px}#me button{background:#2d2650;color:#fff;border:1px solid #4a4180;border-radius:6px;padding:7px 12px}
#info,#chat{background:#14121f;border:1px solid #2a2540;border-radius:6px;padding:10px;margin-bottom:10px;font-size:.85rem;line-height:1.45;white-space:pre-wrap}
#chat{max-height:200px;overflow:auto}a.n{color:#d9c7ff;cursor:pointer;text-decoration:underline}
</style></head><body><div id="gate"><div class="box"><h2>Before you come in</h2>
<p>This is a small simulated world. The beings in it are simple computer programs, not people, and the "guests" are AI minds. Nothing here is a real person, a real place or real advice.</p>
<p>It is for <b>adults only (18+)</b>. You will be visible to other visitors and to the AI guests, and you can type short messages. No links, contact details or personal information, please. Be kind.</p>
<label><input type="checkbox" id="k18"> I am 18 or older.</label><br>
<label><input type="checkbox" id="kok"> I understand the beings are programs and I will follow the rules above.</label><br>
<button id="enter" disabled>Enter the habitat</button><p class="small">This is a self-declaration. It does not verify your age.</p></div></div>
<header id="top">Habitat Live &middot; the beings are simple programs in a simulated world; guests are AI minds.</header>
<main><canvas id="cv" width="960" height="720"></canvas><aside><div id="info">Click a being. Walk with WASD or arrows, Space to jump, Shift to roll, E to wave. On a phone, tap the ground to walk and use the buttons.</div>
<div id="pad"><button data-k="jump">jump</button><button data-k="roll">roll</button><button data-k="wave">wave</button></div>
<div id="me"><b>Your pixel person</b><div class="row"><input id="nm" maxlength="12" placeholder="your name" size="10">
<select id="st"><option value="0">short hair</option><option value="1">long hair</option><option value="2">spiky</option><option value="3">cap</option></select></div>
<div class="row"><label>skin <input type="color" id="c_skin"></label><label>hair <input type="color" id="c_hair"></label>
<label>shirt <input type="color" id="c_shirt"></label><label>pants <input type="color" id="c_pants"></label></div>
<div class="row"><input id="say" maxlength="100" placeholder="say something (100 characters)" style="flex:1"><button id="sayb">say</button></div></div><div id="chat"></div></aside></main>
<script>
const cv=document.getElementById('cv'),g=cv.getContext('2d');g.imageSmoothingEnabled=false;
let S=null,sel=null,sprites={},pos={},frame=0,last={};
const COLS=4,CWc=240,CHc=190,Z=2;
async function j(u){const r=await fetch(u);return r.json()}
function sprite(n,key){const k=n+key;if(sprites[k])return sprites[k];sprites[k]='loading';
 j('/sprite?name='+encodeURIComponent(n)).then(d=>{sprites[k]=d.frames.map(gr=>{const c=document.createElement('canvas');c.width=14;c.height=18;const x=c.getContext('2d');
  gr.forEach((row,y)=>row.forEach((col,xx)=>{if(col){x.fillStyle=col;x.fillRect(xx,y,1,1)}}));return c})}).catch(()=>{delete sprites[k]});return 'loading'}
function mk(frames){return frames.map(gr=>{const c=document.createElement('canvas');c.width=14;c.height=18;const x=c.getContext('2d');
 gr.forEach((row,y)=>row.forEach((col,xx)=>{if(col){x.fillStyle=col;x.fillRect(xx,y,1,1)}}));return c})}
let vsprite=null,MYID='',me={name:'',look:{skin:'#f1c27d',hair:'#2b1d14',style:0,eyes:'#1a1a2e',pants:'#2f3b5c',shirt:'#a98bff'}};
try{MYID=localStorage.getItem('hid')||'';const m=JSON.parse(localStorage.getItem('hme')||'null');if(m)me=m}catch(e){}
if(!MYID){MYID=Math.random().toString(36).slice(2,12);try{localStorage.setItem('hid',MYID)}catch(e){}}
function saveMe(){try{localStorage.setItem('hme',JSON.stringify(me))}catch(e){}}
function loadMine(){j('/sprite?look='+encodeURIComponent(JSON.stringify(me.look))).then(d=>{vsprite=mk(d.frames)}).catch(()=>{})}
const $=id=>document.getElementById(id);$('nm').value=me.name;$('st').value=me.look.style;['skin','hair','shirt','pants'].forEach(k=>{$('c_'+k).value=me.look[k]});
$('nm').oninput=()=>{me.name=$('nm').value;saveMe()};$('st').onchange=()=>{me.look.style=+$('st').value;saveMe();loadMine()};
['skin','hair','shirt','pants'].forEach(k=>{$('c_'+k).onchange=()=>{me.look[k]=$('c_'+k).value;saveMe();loadMine()}});
loadMine();
async function say(){const t=$('say').value.trim();if(!t)return;$('say').value='';try{await fetch('/say',{method:'POST',body:JSON.stringify({id:MYID,say:t})})}catch(e){}}
$('sayb').onclick=say;$('say').onkeydown=e=>{e.stopPropagation();if(e.key==='Enter')say()};$('nm').onkeydown=e=>e.stopPropagation();
let CELLS={};const others={};let ADULT=false;
try{ADULT=localStorage.getItem('hadult')==='1'}catch(e){}
async function ack(){try{const r=await fetch('/ack',{method:'POST',body:JSON.stringify({id:MYID,adult:true,agree:true})});if(r.ok){ADULT=true;try{localStorage.setItem('hadult','1')}catch(e){}$('gate').style.display='none'}}catch(e){}}
const upd=()=>{$('enter').disabled=!($('k18').checked&&$('kok').checked)};$('k18').onchange=upd;$('kok').onchange=upd;$('enter').onclick=ack;
if(ADULT){ack()}
function myPlace(){if(!S)return null;for(const p of Object.keys(CELLS)){const[x,y]=CELLS[p];if(V.x>=x&&V.x<=x+CWc-14&&V.y>=y&&V.y<=y+CHc-20)return p}return null}
setInterval(()=>{if(!S||!ADULT)return;fetch('/visit',{method:'POST',body:JSON.stringify({id:MYID,name:me.name||'Visitor',look:me.look,place:myPlace(),x:V.x/cv.width,y:V.y/cv.height,face:V.face,z:V.z,moving:V.moving,roll:!!V.roll})}).catch(()=>{})},200);
async function poll(){try{S=await j('/state');document.getElementById('top').textContent='Habitat Live · year '+S.year+' · '+S.agents.length+' beings · '+S.works+' works on the wall · simple programs in a simulated world; guests are AI minds';
 const c=document.getElementById('chat');c.innerHTML=S.chat.length?'':'No guests yet.';S.chat.slice(-12).forEach(m=>{const a=document.createElement('a');a.className='n';a.textContent=m.name;a.onclick=()=>pick(m.name);c.append(a,': '+m.say+'\n')});c.scrollTop=1e6}catch(e){}setTimeout(poll,1000)}
async function pick(n){sel=n;const d=await j('/being?name='+encodeURIComponent(n));document.getElementById('info').textContent=d.ok?d.text:'(not here any more)'}
const V={x:480,y:640,z:0,vz:0,face:1,roll:0,goal:null,moving:false,wave:0,msg:''};const keys={};
addEventListener('keydown',e=>{if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();if(e.repeat)return;keys[e.code]=true;
 if(e.code==='Space')jump();if(e.code==='ShiftLeft'||e.code==='ShiftRight'||e.code==='KeyR')roll();if(e.code==='KeyE')wave()});
addEventListener('keyup',e=>{keys[e.code]=false});
function jump(){if(V.z===0&&!V.roll)V.vz=7}
function roll(){if(!V.roll&&V.z===0)V.roll=1}
let lastWave=0;async function wave(){V.wave=40;let best=null,bd=60*60;if(S)S.agents.forEach(a=>{const p=pos[a.name];if(p&&!a.away){const d=(p.x-V.x)**2+(p.y-V.y)**2;if(d<bd){bd=d;best=a.name}}});
 if(best&&Date.now()-lastWave>1500){lastWave=Date.now();V.msg='you waved at '+best;try{await fetch('/wave',{method:'POST',body:JSON.stringify({id:MYID,name:best})})}catch(e){}pick(best)}else V.msg=best?'':'nobody close enough to wave at'}
document.querySelectorAll('#pad button').forEach(b=>b.onclick=()=>({jump,roll,wave})[b.dataset.k]());
cv.onclick=e=>{const r=cv.getBoundingClientRect(),x=(e.clientX-r.left)*cv.width/r.width,y=(e.clientY-r.top)*cv.height/r.height;let best=null,bd=900;
 if(S)S.agents.forEach(a=>{const p=pos[a.name];if(p){const d=(p.x-x)**2+(p.y-y)**2;if(d<bd){bd=d;best=a.name}}});if(best)pick(best);else V.goal={x,y}};
function stepV(){let dx=(keys.KeyD||keys.ArrowRight?1:0)-(keys.KeyA||keys.ArrowLeft?1:0),dy=(keys.KeyS||keys.ArrowDown?1:0)-(keys.KeyW||keys.ArrowUp?1:0);
 if(dx||dy)V.goal=null;else if(V.goal){const gx=V.goal.x-V.x,gy=V.goal.y-V.y,d=Math.hypot(gx,gy);if(d<4)V.goal=null;else{dx=gx/d;dy=gy/d}}
 let sp=2.2;if(V.roll){sp=5;V.roll+=1;if(V.roll>16)V.roll=0;if(!dx&&!dy)dx=V.face}
 const n=Math.hypot(dx,dy)||1;V.moving=!!(dx||dy);if(V.moving){V.x+=dx/n*sp;V.y+=dy/n*sp*.8;if(dx)V.face=dx>0?1:-1}
 V.x=Math.max(20,Math.min(cv.width-20,V.x));V.y=Math.max(50,Math.min(cv.height-40,V.y));
 if(V.z>0||V.vz>0){V.z+=V.vz;V.vz-=.6;if(V.z<=0){V.z=0;V.vz=0}}if(V.wave>0)V.wave--}
function draw(){frame++;g.clearRect(0,0,cv.width,cv.height);if(!S){requestAnimationFrame(draw);return}
 const names=Object.keys(S.places);const cells={};names.forEach((p,i)=>{cells[p]=[10+(i%COLS)*CWc,30+Math.floor(i/COLS)*CHc]});CELLS=cells;
 const selp=S.agents.find(a=>a.name===sel);
 names.forEach(p=>{const[x,y]=cells[p],hl=selp&&selp.place===p;g.strokeStyle=hl?'#fff':S.places[p];g.lineWidth=hl?4:2;g.fillStyle='#13111f';g.fillRect(x,y,CWc-14,CHc-20);g.strokeRect(x,y,CWc-14,CHc-20);g.fillStyle=S.places[p];g.font='10px monospace';g.fillText(p.toUpperCase(),x+6,y+14)});
 const groups={};S.agents.forEach(a=>{if(!a.away)(groups[a.place]=groups[a.place]||[]).push(a)});
 Object.entries(groups).forEach(([p,l])=>{const c=cells[p];if(!c)return;const cx=c[0]+(CWc-14)/2,cy=c[1]+(CHc-20)/2+8;l.forEach((a,i)=>{const ang=2*Math.PI*i/l.length,r=14+8*Math.sqrt(l.length);
  const tx=cx+r*Math.cos(ang),ty=cy+r*Math.sin(ang)*.7;let q=pos[a.name];if(!q)q=pos[a.name]={x:tx,y:ty,face:1};
  const dx=tx-q.x;q.x+=dx*.12;q.y+=(ty-q.y)*.12;if(Math.abs(dx)>.3)q.face=dx>0?1:-1;q.moving=Math.abs(dx)+Math.abs(ty-q.y)>.4;a._q=q})});
 S.agents.forEach(a=>{const q=pos[a.name];if(!q||a.away)return;const key=(a.child?'c':'a')+a.dom;const sp=sprite(a.name,key);
  if(sp==='loading')return;const f=q.moving?((frame>>3)&1):0;
  g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(q.x,q.y+14,8,3,0,0,7);g.fill();
  g.save();g.translate(q.x,q.y);if(q.face<0)g.scale(-1,1);g.drawImage(sp[f],-14,-18,28,36);g.restore();
  if(a.name===sel){g.strokeStyle='#fff';g.beginPath();g.ellipse(q.x,q.y+14,11,4,0,0,7);g.stroke()}
  if(S.agents.length<30||a.name===sel||a.guest){g.fillStyle=a.guest?'#d9c7ff':'#aaa';g.font='9px monospace';g.textAlign='center';g.fillText(a.name+(a.guest?' (AI)':''),q.x,q.y+26);g.textAlign='start'}});
  (S.visitors||[]).forEach(v=>{if(v.id===MYID)return;let o=others[v.id];const tx=v.x*cv.width,ty=v.y*cv.height;if(!o)o=others[v.id]={x:tx,y:ty};o.x+=(tx-o.x)*.3;o.y+=(ty-o.y)*.3;
   const key='v'+v.id+v.look;let sp=sprites[key];if(!sp){sprites[key]='loading';j('/sprite?vid='+v.id).then(d=>{sprites[key]=mk(d.frames)}).catch(()=>{delete sprites[key]});return}if(sp==='loading')return;
   const f=v.moving?((frame>>3)&1):0;g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(o.x,o.y+14,8*(1-v.z/60),3,0,0,7);g.fill();
   g.save();g.translate(o.x,o.y-v.z);if(v.face<0)g.scale(-1,1);if(v.roll)g.rotate((frame%16)/16*Math.PI*2);g.drawImage(sp[f],-14,-18,28,36);g.restore();
   g.fillStyle='#9fe3b4';g.font='9px monospace';g.textAlign='center';g.fillText(v.name+' (human)',o.x,o.y+26);g.textAlign='start'});
  stepV();if(vsprite){const f=V.moving?((frame>>3)&1):0;
  g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(V.x,V.y+14,8*(1-V.z/60),3,0,0,7);g.fill();
  g.save();g.translate(V.x,V.y-V.z+(V.roll?6:0));if(V.face<0)g.scale(-1,1);if(V.roll)g.rotate(V.roll/16*Math.PI*2);const k=V.roll?.8:1;g.drawImage(vsprite[f],-14*k,-18*k,28*k,36*k);g.restore();
  g.fillStyle='#fff';g.font='9px monospace';g.textAlign='center';g.fillText(me.name||'You',V.x,V.y+26);if(V.wave>0){g.fillText('~ hi! ~',V.x,V.y-48-V.z)}g.textAlign='start'}
 requestAnimationFrame(draw)}
poll();draw();
</script></body></html>"""

# ------------------------------------------------------------------ HTTP bridge
def serve(world, port, host="127.0.0.1"):
    install(world)
    class H(BaseHTTPRequestHandler):
        def log_message(s, *a): pass
        def _send(s, code, obj):
            b = json.dumps(obj).encode(); s.send_response(code); s.send_header("Content-Type", "application/json")
            s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
        def _body(s):
            n = min(int(s.headers.get("Content-Length") or 0), 4096)
            try: return json.loads(s.rfile.read(n) or b"{}")
            except Exception: return {}
        def do_GET(s):
            u = urllib.parse.urlparse(s.path); q = urllib.parse.parse_qs(u.query)
            if u.path in ("/", "/index.html"):
                b = VIEWER.encode(); s.send_response(200); s.send_header("Content-Type", "text/html; charset=utf-8")
                s.send_header("Content-Length", str(len(b))); s.end_headers(); return s.wfile.write(b)
            if u.path == "/state":
                now = time.time()
                h = _h()
                with world.lock:
                    ags = [dict(name=a.name, place=a.place, child=a.age < h.ADULT, dom=a.dominant(), away=bool(a.expedition),
                                guest=a.name in world.guests) for a in world.agents]
                    vis = [dict(id=k, name=v["name"], place=v["place"], x=v["x"], y=v["y"], face=v["face"], z=v["z"],
                               moving=v["moving"], roll=v["roll"], look=hash(json.dumps(v["look"], sort_keys=True)) & 0xffffff)
                           for k, v in live_visitors(world, now).items()]
                    return s._send(200, dict(year=world.t // h.YEAR, works=len(world.gallery), agents=ags, visitors=vis,
                                             places={k: v["color"] for k, v in h.PLACES.items()},
                                             chat=[{"name": n, "say": t} for n, t in world.chat[-12:]]))
            if u.path == "/sprite":
                h = _h(); name = (q.get("name") or [""])[0]
                with world.lock:
                    a = world.by_name(name)
                    if q.get("vid") or q.get("look"):                # a visitor's customised pixel person
                        if q.get("look"):
                            try: lk = clean_look(json.loads(q["look"][0]))
                            except Exception: lk = dict(DEFAULT_LOOK)
                        else:
                            v = getattr(world, "visitors", {}).get(q["vid"][0]); lk = v["look"] if v else dict(DEFAULT_LOOK)
                        return s._send(200, {"frames": look_grids(lk)})
                    if a is None: return s._send(404, {"ok": False})
                    kid = a.age < h.ADULT
                    return s._send(200, {"frames": [h.sprite_grid(a, f, 1, kid) for f in (0, 1)]})
            if u.path == "/being":
                h = _h(); name = (q.get("name") or [""])[0]
                with world.lock:
                    a = world.by_name(name)
                    if a is None: return s._send(404, {"ok": False})
                    top = lambda d, k=3: ", ".join(f"{x} {v:.2f}" for x, v in sorted(d.items(), key=lambda kv: -kv[1])[:k]) or "none"
                    txt = (f"{a.name}{' (AI guest)' if a.name in world.guests else ''}\nage {a.age // h.YEAR} of about {a.life // h.YEAR}"
                           f" · generation {a.gen} · in {a.place if not a.expedition else 'the stars'}\n"
                           f"traits: {top(a.traits)}\nskills: {top(a.skills)}\nsketches {a.sketches} · songs {len(a.songs)}\n"
                           f"recent: " + "; ".join(t for _, t in a.memories[-3:]))
                    return s._send(200, {"ok": True, "text": txt})
            if u.path == "/chat":
                with world.lock: return s._send(200, {"chat": [{"name": n, "say": t} for n, t in world.chat]})
            if u.path == "/observe":
                name = safe_name((q.get("name") or [""])[0])
                with world.lock:
                    a = world.by_name(name) if name else None
                    if a is None or name not in world.guests: return s._send(404, {"ok": False, "error": "join first"})
                    h = _h()
                    here = [x.name for x in world.agents if x.place == a.place and x is not a and not x.expedition]
                    return s._send(200, {"ok": True, "scene": scene_text(world, a), "place": a.place, "here": here,
                                         "places": list(h.PLACES), "intro": INTRO.format(name=name)})
            s._send(404, {"ok": False})
        def do_POST(s):
            u = urllib.parse.urlparse(s.path); d = s._body()
            name = safe_name(d.get("name"))
            if u.path == "/ack":                                    # the 18+ gate: a person confirms age and rules before they can appear or speak
                vid = re.sub(r"[^A-Za-z0-9]", "", str(d.get("id", "")))[:24]
                if not vid or d.get("adult") is not True or d.get("agree") is not True: return s._send(400, {"ok": False})
                with world.lock: world.acks[vid] = time.time()
                return s._send(200, {"ok": True})
            if u.path == "/visit":                                  # a human's position, look and name, a few times a second
                vid = re.sub(r"[^A-Za-z0-9]", "", str(d.get("id", "")))[:24]
                vname = re.sub(r"[^A-Za-z0-9 ]", "", str(d.get("name", "")))[:12].strip() or "Visitor"
                if moderate(vname, getattr(world, "blocked", ())) is None: vname = "Visitor"
                h = _h()
                with world.lock:
                    if not adult_ok(world, vid): return s._send(403, {"ok": False, "error": "confirm 18+ first"})
                    vs = live_visitors(world)
                    if not vid or (vid not in vs and len(vs) >= MAX_VISITORS): return s._send(429, {"ok": False})
                    place = d.get("place") if d.get("place") in h.PLACES else None
                    num = lambda k, lo, hi: max(lo, min(hi, float(d.get(k, 0) or 0)))
                    old = vs.get(vid, {})
                    vs[vid] = dict(name=vname, look=clean_look(d.get("look")), place=place, x=num("x", 0, 1), y=num("y", 0, 1),
                                   face=-1 if d.get("face") == -1 else 1, z=num("z", 0, 80), moving=bool(d.get("moving")),
                                   roll=bool(d.get("roll")), seen=time.time(), said=old.get("said", 0))
                    if place and old.get("place") != place and place != "Away":
                        for a in world.agents:                      # beings notice someone walking in
                            if a.place == place and not a.expedition and random.random() < .15: world.remember(a, f"{vname}, a human visitor, came to {place}")
                return s._send(200, {"ok": True})
            if u.path == "/say":                                    # a human says one short thing; everyone nearby (and every guest) can hear it
                vid = re.sub(r"[^A-Za-z0-9]", "", str(d.get("id", "")))[:24]
                with world.lock:
                    v = live_visitors(world).get(vid)
                    if not adult_ok(world, vid): return s._send(403, {"ok": False, "error": "confirm 18+ first"})
                    txt = moderate(clean(str(d.get("say", "")))[:100], world.blocked)
                    if not v or not txt or time.time() - v["said"] < 2: return s._send(429, {"ok": False})
                    v["said"] = time.time()
                    world.chat = (world.chat + [(v["name"] + " (human)", txt)])[-30:]
                    for a in world.agents:
                        if a.place == v["place"] and not a.expedition:
                            a.lonely = max(0, a.lonely - 5); world.remember(a, f"{v['name']}, a human visitor, said: {txt}")
                return s._send(200, {"ok": True})
            if u.path == "/wave":                                   # a human visitor waves: tiny, harmless, rate-limited
                vid = re.sub(r"[^A-Za-z0-9]", "", str(d.get("id", "")))[:24]
                with world.lock:
                    if not adult_ok(world, vid): return s._send(403, {"ok": False})
                    a = world.by_name(name) if name else None
                    if a is None or a.expedition or time.time() - getattr(world, "last_wave", 0) < 1.0:
                        return s._send(429, {"ok": False})
                    world.last_wave = time.time(); a.lonely = max(0, a.lonely - 6); a.fame += .02
                    world.remember(a, "a human visitor waved at me")
                return s._send(200, {"ok": True})
            if u.path == "/join":
                with world.lock:
                    a = add_guest(world, name, HTTPMind()) if name else None
                return s._send(200 if a else 400, {"ok": bool(a), "name": name})
            if u.path == "/act":
                with world.lock:
                    mind = world.guests.get(name) if name else None
                    if not isinstance(mind, HTTPMind): return s._send(404, {"ok": False, "error": "join first"})
                    act = parse_action(json.dumps({"go": d.get("go"), "say": d.get("say", "")}))
                    ok = mind.push(act, time.time())
                return s._send(200 if ok else 429, {"ok": ok})
            s._send(404, {"ok": False})
    srv = ThreadingHTTPServer((host, port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def setup(world, args):
    """Called from habitat.py's command line."""
    install(world); notes = []
    if getattr(args, "ai", None):
        for nm in [n for n in (args.ai_names or "Olmo").split(",") if n.strip()][:MAX_GUESTS]:
            a = add_guest(world, nm, OllamaMind(args.ai, args.ollama_url))
            notes.append(f"guest {a.name if a else nm + ' (refused)'} is thinking with {args.ai}")
    if getattr(args, "serve", None):
        try: serve(world, args.serve); notes.append(f"guest door open on http://127.0.0.1:{args.serve} (see guests.py)")
        except OSError as e: notes.append(f"could not open the guest door on port {args.serve}: {e}")
    return notes
