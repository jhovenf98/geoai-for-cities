"""Build video.html: a 1280x720 animated explainer whose every animation is a CSS animation,
so a capture script can seek all of them to any time t and screenshot a frame."""
import json, math
from shapely.geometry import shape

T = json.load(open("timing.json"))
G = json.load(open("geo.json"))
SC = {s["id"]: s for s in T["scenes"]}

def L(sid, i):            # absolute start time (s) of line i in scene sid
    return SC[sid]["lines"][i]["t"]

def a(name, d, du=0.6, ease="cubic-bezier(.2,.8,.2,1)", fill="both", it="1"):
    return f"animation:{name} {du}s {ease} {d:.2f}s {it} {fill};"

def pathd(geom, P):
    g = shape(geom).buffer(0)
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    out = []
    for p in polys:
        out.append("M" + "L".join("%.1f,%.1f" % P(x, y) for x, y in p.exterior.coords) + "Z")
    return "".join(out)

def proj(W, N, k, ox, oy, lat0):
    cx = math.cos(math.radians(lat0))
    return lambda x, y: (ox + (x - W) * cx * k, oy + (N - y) * k)

CA = [f for f in G["states"]["features"] if f["properties"]["name"] == "California"][0]["geometry"]
SEA = G["sea"]
G2 = json.load(open("geo2.json"))
LIPS = json.load(open("lips.json"))
from shapely.geometry import LineString, MultiLineString, box as _box

ROAD_LABEL = {"10": "I-10", "8": "I-8", "86": "86", "111": "111", "78": "78"}
def regional(P, clipbox, d0, towns=True, roads=True, counties=True, mexico=True, tlist=None):
    """Detailed base layers: Mexico, county lines, highways (drawn on), shields, towns."""
    out = []
    W_, S_, E_, N_ = clipbox
    cb = _box(W_, S_, E_, N_)
    if mexico:
        mx = shape(G2["mexico"]).intersection(cb)
        if not mx.is_empty:
            out.append(f'<path d="{pathd(mx.__geo_interface__, P)}" style="fill:var(--mx);stroke:var(--ink2);stroke-width:1.5;stroke-dasharray:2 4;{a("fade", d0, .8)}"/>')
            c = mx.representative_point(); x, y = P(c.x, c.y)
            bx = mx.bounds; hpx = (bx[3]-bx[1]) * (P(0, 0)[1] - P(0, 1)[1])
            if hpx > 60: out.append(f'<text x="{x:.0f}" y="{y:.0f}" class="mxl" style="{a("fade", d0+.4, .8)}">MEXICO</text>')
    if counties:
        for k, g in G2["counties"].items():
            gg = shape(g).intersection(cb)
            if gg.is_empty: continue
            out.append(f'<path d="{pathd(gg.__geo_interface__, P)}" style="fill:none;stroke:var(--ink2);stroke-width:1.6;stroke-dasharray:7 5;opacity:.55;{a("fade", d0+.2, .8)}"/>')
    if roads:
        shields = {}
        for i, f in enumerate(G2["roads"]["features"]):
            g = shape(f["geometry"]).intersection(cb)
            if g.is_empty: continue
            lines = [g] if g.geom_type == "LineString" else [x for x in getattr(g, "geoms", []) if x.geom_type == "LineString"]
            major = f["properties"]["type"] == "Major Highway"
            for ln in lines:
                d = "M" + "L".join("%.1f,%.1f" % P(x, y) for x, y in ln.coords)
                ln_len = sum(math.dist(P(*ln.coords[j]), P(*ln.coords[j+1])) for j in range(len(ln.coords)-1))
                out.append(f'<path d="{d}" class="{"rdM" if major else "rdS"}" style="stroke-dasharray:{ln_len:.0f};--L:{ln_len:.0f};{a("drawL", d0+.3+(i%8)*.12, 1.6, "ease-out")}"/>')
                nm = ROAD_LABEL.get(str(f["properties"]["name"]))
                if nm and (nm not in shields or ln.length > shields[nm][0]):
                    pt = ln.interpolate(0.5, normalized=True); shields[nm] = (ln.length, P(pt.x, pt.y), major)
        for nm, (_, (x, y), major) in shields.items():
            if not (0 < x < 1280 and 0 < y < 720): continue
            w = 14 + 9 * len(nm)
            out.append(f'<g style="{a("pop", d0+1.6, .4)}transform-origin:{x:.0f}px {y:.0f}px"><rect x="{x-w/2:.0f}" y="{y-12:.0f}" width="{w}" height="24" rx="{12 if not nm.startswith("I-") else 4}" class="{"shI" if nm.startswith("I-") else "shS"}"/><text x="{x:.0f}" y="{y+6:.0f}" text-anchor="middle" class="shT">{nm}</text></g>')
    if towns and tlist:
        for j, (n, x, y, side) in enumerate(tlist):
            px, py = P(x, y)
            if not (0 < px < 1280 and 0 < py < 720): continue
            dx = 12 if side == "r" else -12; anc = "start" if side == "r" else "end"
            out.append(f'<g style="{a("fade", d0+.9+j*.08, .5)}"><circle cx="{px:.0f}" cy="{py:.0f}" r="6" class="twC"/><text x="{px+dx:.0f}" y="{py+5:.0f}" text-anchor="{anc}" class="twT">{n}</text></g>')
    return "".join(out)

TOWNS_ALL = [("Niland", -115.519, 33.240, "r"), ("Calipatria", -115.514, 33.125, "r"), ("Brawley", -115.530, 32.979, "r"),
 ("Westmorland", -115.621, 33.037, "l"), ("Salton City", -115.956, 33.299, "l"), ("Bombay Beach", -115.729, 33.351, "r"),
 ("Mecca", -116.077, 33.572, "l"), ("Coachella", -116.174, 33.680, "l"), ("El Centro", -115.563, 32.792, "l"),
 ("Calexico", -115.499, 32.679, "r")]

def wind_field(x0, y0, w, h, d0, n=26, seed=3, ang=18):
    import random
    rnd = random.Random(seed); out = []
    for i in range(n):
        x = x0 + rnd.random() * w; y = y0 + rnd.random() * h; L_ = 40 + rnd.random() * 50
        du = 2.2 + rnd.random() * 1.6; dl = d0 + rnd.random() * du
        out.append(f'<path d="M{x:.0f} {y:.0f} h{L_:.0f}" class="wf" style="transform:rotate({ang}deg);transform-box:fill-box;--dx:{w*0.25:.0f}px;opacity:0;{a("streak", dl, du, "linear", "none", "infinite")}"/>')
    return "".join(out)

# ---------- presenter (original character: a field researcher) ----------
def presenter_svg(gest=""):
    return f"""<svg viewBox="0 0 300 520" class="hostsvg">
 <ellipse cx="150" cy="508" rx="95" ry="10" class="hshadow"/>
 <g class="hbody">
  <path d="M112 360 L104 494 H140 L148 380 Z M188 360 L196 494 H160 L152 380 Z" class="hpants"/>
  <path d="M96 494 h48 v12 h-54 z M156 494 h48 l6 12 h-54 z" class="hshoe"/>
  <path d="M78 214 Q150 182 222 214 L238 372 Q150 392 62 372 Z" class="hjacket"/>
  <path d="M128 196 L150 250 L172 196 Z" class="hshirt"/>
  <path d="M118 198 L150 262 L130 268 L108 212 Z M182 198 L150 262 L170 268 L192 212 Z" class="hcollar"/>
  <rect x="176" y="276" width="34" height="18" rx="3" class="hpatch"/><text x="193" y="289" text-anchor="middle" class="hpatchT">GeoAI</text>
  <path d="M150 262 V372" class="hzip"/>
  <g class="harmL"><path d="M84 222 Q62 280 76 330 L98 326 Q90 284 104 236 Z" class="hjacket"/>
   <path d="M76 330 Q100 344 138 320 L132 304 Q102 318 92 312 Z" class="hjacket"/>
   <rect x="118" y="268" width="64" height="88" rx="6" transform="rotate(-12 150 312)" class="htab"/><rect x="125" y="276" width="50" height="66" rx="3" transform="rotate(-12 150 312)" class="htabS"/>
   <circle cx="136" cy="318" r="10" class="hskin"/></g>
  <g class="harmR" style="{gest}">
   <path d="M210 218 Q236 270 228 330 L206 328 Q212 278 198 236 Z" class="hjacket"/>
   <circle cx="217" cy="338" r="11" class="hskin"/>
  </g>
  <rect x="136" y="166" width="28" height="30" class="hskin"/>
  <g class="hhead">
   <ellipse cx="92" cy="122" rx="10" ry="14" class="hskin"/><ellipse cx="208" cy="122" rx="10" ry="14" class="hskin"/>
   <ellipse cx="150" cy="118" rx="58" ry="64" class="hskin"/>
   <path d="M92 112 Q90 52 150 50 Q214 50 210 112 Q200 84 170 78 Q140 92 104 96 Q96 102 92 112 Z" class="hhair"/>
   <path d="M112 100 q14 -8 28 -2 M162 98 q14 -6 28 2" class="hbrow"/>
   <g class="heyes"><ellipse cx="127" cy="116" rx="6.5" ry="8" class="heye"/><ellipse cx="175" cy="116" rx="6.5" ry="8" class="heye"/>
    <circle cx="129" cy="113" r="2" class="hglint"/><circle cx="177" cy="113" r="2" class="hglint"/></g>
   <path d="M150 122 q-6 14 2 18" class="hnose"/>
   <ellipse cx="116" cy="140" rx="10" ry="6" class="hcheek"/><ellipse cx="186" cy="140" rx="10" ry="6" class="hcheek"/>
   <g class="hmouthG"><ellipse cx="151" cy="156" rx="15" ry="10" class="mouth"/></g>
   <path d="M134 152 q17 10 34 0" class="hsmile"/>
  </g>
 </g>
</svg>"""

def host_full(x, y, h, d_in, gestures=""):
    return f'<div class="host full" style="left:{x}px;top:{y}px;height:{h}px;{a("hostIn", d_in, .8)}">{presenter_svg(gestures)}</div>'

def host_bubble(d_in):
    return f'<div class="host bub" style="{a("pop", d_in, .5)}"><div class="bubin">{presenter_svg()}</div></div>'

# ---------- Scene helpers ----------
def scene(sid, inner, chapter_no):
    s = SC[sid]
    title = s["title"]
    return f'''<section class="sc" data-id="{sid}" style="animation:sIn .5s ease {s['start']:.2f}s both, sOut .45s ease {s['end']-0.45:.2f}s forwards">
  <div class="chap" style="{a('slideR', s['start']+0.2)}"><b>{chapter_no:02d}</b>{title}</div>
  {inner}
</section>'''

def label(x, y, text, d, cls="lbl", anchor="start", an="up"):
    if anchor == "middle":
        return f'<div class="mid" style="top:{y}px"><div class="{cls}" style="position:relative;display:inline-block;{a(an, d)}">{text}</div></div>'
    return f'<div class="{cls}" style="left:{x}px;top:{y}px;{a(an, d)}">{text}</div>'

def source(text, d):
    return f'<div class="src" style="{a("fade", d)}">{text}</div>'

parts = []

# ---------- 1 HOOK ----------
s = "hook"; l0, l1, l2 = L(s, 0), L(s, 1), L(s, 2)
P = proj(-124.6, 42.1, 56, 700, 70, 37)
ca_d = pathd(CA, P); sx, sy = P(-115.83, 33.30)
car = f'''<svg class="abs" style="left:400px;top:300px;width:420px;height:240px;{a('carIn', l0, 1.2)}" viewBox="0 0 420 240">
  <path d="M30 170 L60 110 Q80 80 130 78 L270 78 Q310 80 340 120 L390 140 Q405 145 405 165 L405 180 L30 180 Z" fill="var(--sea2)"/>
  <path d="M110 112 L135 92 L200 92 L200 125 L100 125 Z M215 92 L265 92 Q290 95 305 125 L215 125 Z" fill="var(--paper)" opacity=".85"/>
  <g class="wheel" style="{a('spin', l0, 1.2, 'linear', 'both')}transform-origin:110px 185px"><circle cx="110" cy="185" r="30" fill="var(--ink)"/><circle cx="110" cy="185" r="11" fill="var(--paper)"/></g>
  <g class="wheel" style="{a('spin', l0, 1.2, 'linear', 'both')}transform-origin:320px 185px"><circle cx="320" cy="185" r="30" fill="var(--ink)"/><circle cx="320" cy="185" r="11" fill="var(--paper)"/></g>
  <path d="M10 214 H410" stroke="var(--rule)" stroke-width="4" stroke-linecap="round"/>
</svg>
<div class="batt" style="left:500px;top:150px;{a('pop', l0+1.1)}"><div class="bfill" style="{a('fillW', l0+1.4, 1.4)}"></div><span>battery</span></div>
<div class="li" style="left:700px;top:118px;{a('pop', l0+2.0)}"><small>3</small><b>Li</b><em>Lithium</em></div>'''
camap = f'''<div class="lay" style="{a('fadeOut', l2-0.2, .5, 'ease', 'forwards')}"><svg class="abs" viewBox="0 0 1280 720" style="inset:0;{a('fade', l1)}">
  <path d="{ca_d}" fill="var(--sand2)" stroke="var(--ink2)" stroke-width="2" style="stroke-dasharray:3000;{a('draw', l1, 1.8, 'ease-out')}"/>
  <circle cx="{sx:.0f}" cy="{sy:.0f}" r="9" fill="var(--sea)" stroke="var(--ink)" stroke-width="2" style="{a('pop', l1+1.4)}transform-origin:{sx:.0f}px {sy:.0f}px"/>
  <circle cx="{sx:.0f}" cy="{sy:.0f}" r="9" fill="none" stroke="var(--sea2)" stroke-width="3" style="{a('ping', l1+1.6, 1.6, 'ease-out', 'both', '2')}transform-origin:{sx:.0f}px {sy:.0f}px"/>
</svg>
{label(sx-160, sy-60, 'Salton Sea', l1+1.6, 'tag')}</div>'''
houses = "".join(f'<path d="M{x} 70 v-34 l22-18 22 18 v34z" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/>' for x in (10, 60, 110))
hook3 = f'''<svg class="abs" style="left:820px;top:430px;width:300px;height:135px;{a('up', l2)}" viewBox="0 0 170 80">{houses}</svg>
<div class="dustcloud big2" style="left:700px;top:330px;{a('drift', l2+0.4, 3.5, 'ease-in-out')}"></div>
<div class="big" style="left:400px;top:170px;{a('up', l2+0.3)}">Lithium <span class="hl">and</span><br>clean air?</div>'''
parts.append(scene(s, f'<div class="lay" style="{a("fadeOut", l1-0.1, .4, "ease", "forwards")}">{car}</div>' + camap + f'<div class="lay">{hook3}</div>' + host_full(20, 150, 560, SC['hook']['start']+0.1, f"animation:wave 2s ease-in-out {l0+0.2:.2f}s 1 both, point 5.5s ease-in-out {l1+1.2:.2f}s 1 forwards;") , 1))

# ---------- 2 HOW ----------
s = "how"; l0, l1, l2 = L(s, 0), L(s, 1), L(s, 2)
P2 = proj(-124.6, 42.1, 58, 360, 70, 37)
ca2 = pathd(CA, P2); sx2, sy2 = P2(-115.83, 33.30)
zoom_k = 6.5
tx, ty = 640 - sx2 * zoom_k, 330 - sy2 * zoom_k
Pz = proj(-124.6, 42.1, 58, 360, 70, 37)
sea_small = pathd(SEA, Pz)
how_map = f'''<div class="lay" style="{a('fadeOut', l1-0.2, .5, 'ease', 'forwards')}">
<svg class="abs" viewBox="0 0 1280 720" style="inset:0">
 <g style="transform-origin:0 0;--tx:{tx:.0f}px;--ty:{ty:.0f}px;--k:{zoom_k};{a('zoomTo', l0+0.6, 3.2, 'cubic-bezier(.6,0,.2,1)')}">
  <path d="{ca2}" fill="var(--sand2)" stroke="var(--ink2)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>
  <path d="{sea_small}" fill="var(--sea)" stroke="var(--sea2)" stroke-width="1" vector-effect="non-scaling-stroke"/>
 </g></svg>
 {label(640, 600, "California's largest lake", l0+2.6, 'tag', 'middle')}
</div>'''
# cross-section
xs = f'''<div class="lay" style="{a('fade', l1)}">
<svg class="abs" viewBox="0 0 1280 720" style="inset:0">
 <defs><radialGradient id="brine" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="var(--hot)"/><stop offset="1" stop-color="var(--clay)"/></radialGradient></defs>
 <rect x="0" y="250" width="1280" height="470" fill="var(--sand2)"/>
 <rect x="0" y="330" width="1280" height="390" fill="var(--earth1)"/>
 <rect x="0" y="450" width="1280" height="270" fill="var(--earth2)"/>
 <ellipse cx="640" cy="640" rx="560" ry="110" fill="url(#brine)" style="{a('glow', l1+0.3, 2.4, 'ease-in-out', 'both', 'infinite')}"/>
 {''.join(f'<text x="{x}" y="{y}" class="lip" style="{a("bob", l1+0.8+i*0.15, 2.2, "ease-in-out", "both", "infinite")}">Li</text>' for i,(x,y) in enumerate([(300,640),(420,680),(560,620),(700,670),(820,630),(940,675),(470,600),(780,700)]))}
 <text x="640" y="600" text-anchor="middle" class="svgl light">hot, salty brine with lithium</text>
 <g style="{a('fade', l2)}">
  <path id="up" d="M420 640 V250" stroke="var(--pipe)" stroke-width="16" fill="none"/>
  <path d="M860 250 V640" stroke="var(--pipe)" stroke-width="16" fill="none"/>
  <rect x="470" y="150" width="200" height="100" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/>
  <rect x="690" y="180" width="110" height="70" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/>
  <path d="M500 150 v-40 h26 v40 M560 150 v-55 h26 v55" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/>
  <path d="M420 250 V200 H470 M800 215 H860 V250" stroke="var(--pipe)" stroke-width="12" fill="none"/>
 </g>
 {''.join(f'<circle r="7" fill="var(--hot)" style="offset-path:path(\'M420 640 V200 H470\');opacity:0;{a("flowUp", l2+0.6+i*0.45, 2.6, "linear", "none", "infinite")}"/>' for i in range(5))}
 {''.join(f'<circle r="7" fill="var(--clay)" style="offset-path:path(\'M800 215 H860 V640\');opacity:0;{a("flowUp", l2+1.5+i*0.45, 2.6, "linear", "none", "infinite")}"/>' for i in range(5))}
</svg>
{label(300, 120, '<b>1</b> pump brine up', l2+0.4, 'step')}
{label(520, 70, '<b>2</b> pull the lithium out', l2+1.6, 'step')}
{label(880, 120, '<b>3</b> send brine back down', l2+2.8, 'step')}
<div class="li sm" style="left:705px;top:100px;{a('pop', l2+2.2)}"><b>Li</b></div>
</div>'''
parts.append(scene(s, how_map + xs + host_bubble(SC['how']['start']+0.3), 2))

# ---------- 3 PROBLEM ----------
s = "problem"; l0, l1, l2 = L(s, 0), L(s, 1), L(s, 2)
P3 = proj(-116.12, 33.56, 1050, 440, 70, 33.3)
sea3 = pathd(SEA, P3)
c3 = shape(SEA).centroid; cx3, cy3 = P3(c3.x, c3.y)
towns3 = [("Niland", -115.519, 33.240), ("Calipatria", -115.514, 33.125), ("Westmorland", -115.621, 33.037), ("Bombay Beach", -115.729, 33.351), ("Salton City", -115.956, 33.299), ("Mecca", -116.077, 33.572)]
tw = "".join(f'<g><circle cx="{P3(x,y)[0]:.0f}" cy="{P3(x,y)[1]:.0f}" r="7" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/><text x="{P3(x,y)[0]+12:.0f}" y="{P3(x,y)[1]+6:.0f}" class="svgl">{n}</text></g>' for n,x,y in towns3 if 0 < P3(x,y)[1] < 700)
dust = "".join(f'<circle cx="{cx3-60+dx:.0f}" cy="{cy3+120+dy:.0f}" r="{r}" fill="var(--dust)" style="{a("blow", l1+1.0+i*0.25, 4.2, "ease-in-out", "both", "infinite")}"/>' for i,(dx,dy,r) in enumerate([(0,0,22),(40,-30,30),(-30,40,26),(70,20,18),(20,70,24),(-50,-10,20)]))
wind = "".join(f'<path d="M{80} {y} h120 m-22 -12 l22 12 -22 12" stroke="var(--ink2)" stroke-width="5" fill="none" stroke-linecap="round" style="{a("windA", l1+0.3+i*0.3, 2.0, "ease-in-out", "both", "infinite")}"/>' for i,y in enumerate((300, 360, 420)))
BOX3 = (-116.75, 32.85, -115.05, 33.62)
reg3 = regional(P3, BOX3, l0+0.1, tlist=None, mexico=False)
wf3 = wind_field(300, 150, 600, 420, l1+0.2, n=30, seed=7)
plumes = "".join(f'<circle cx="{P3(x,y)[0]+dx:.0f}" cy="{P3(x,y)[1]+dy:.0f}" r="{r}" fill="var(--dust)" style="{a("plume", l1+0.8+i*0.35, 3.6, "ease-out", "both", "infinite")}"/>' for i,(x,y,dx,dy,r) in enumerate([(-115.66,33.16,0,0,26),(-115.62,33.10,10,0,30),(-115.74,33.20,0,0,22),(-115.70,33.12,0,0,28),(-115.80,33.22,0,0,20),(-115.58,33.18,0,0,24)]))
prob = f'''<svg class="abs" viewBox="0 0 1280 720" style="inset:0"><defs><clipPath id="clp3"><rect x="380" y="20" width="900" height="700"/></clipPath></defs>
  <g clip-path="url(#clp3)">{reg3}</g>
  <path d="{sea3}" fill="var(--playa)" stroke="var(--ink2)" stroke-width="2" stroke-dasharray="8 6"/>
  <g style="transform-origin:{cx3:.0f}px {cy3:.0f}px;{a('shrink', l0+0.8, 4.5, 'ease-in-out')}"><path d="{sea3}" fill="var(--sea)" stroke="var(--sea2)" stroke-width="2"/></g>
  <g style="{a('fade', l1)}" clip-path="url(#clp3)">{wf3}{dust}{plumes}</g>
  {tw}
</svg>
{label(70, 140, 'old shoreline', l0+1.0, 'key dash')}
{label(70, 180, 'exposed lakebed', l0+3.0, 'key playa')}
{label(70, 440, 'wind → dust → towns', l1+0.8, 'tag')}
<div class="card court" style="left:230px;top:548px;{a('up', l2+0.2)}"><div class="cicon">⚖</div><div><small>August 2026 · California Court of Appeal</small><p>The biggest project’s review hadn’t shown how its water use could affect the air.</p></div></div>'''
parts.append(scene(s, prob + host_bubble(SC['problem']['start']+0.3) + source("Map: Natural Earth (older shoreline, highways); towns approximate", l0+0.5), 3))

# ---------- 4 BURDEN ----------
s = "burden"; l0, l1, l2 = L(s, 0), L(s, 1), L(s, 2)
P4 = proj(-116.40, 33.80, 545, 650, 40, 33.2)
def cls(p):
    v = p.get("asthmaP")
    if v is None: return "var(--none)"
    return ["var(--q0)", "var(--q1)", "var(--q2)", "var(--q3)", "var(--q4)"][min(4, int(v // 20))]
from shapely.geometry import box
clip = box(-116.40, 32.62, -115.25, 33.80)
paths = []
for i, f in enumerate(G["tracts"]["features"]):
    g = shape(f["geometry"]).buffer(0).intersection(clip)
    if g.is_empty: continue
    polys = [g] if g.geom_type == "Polygon" else [x for x in getattr(g, "geoms", []) if x.geom_type == "Polygon"]
    d = "".join("M" + "L".join("%.1f,%.1f" % P4(x, y) for x, y in p.exterior.coords) + "Z" for p in polys)
    top = (f["properties"].get("asthmaP") or 0) >= 85
    delay_in = l0 + 0.3 + (i % 20) * 0.04
    anim = f"animation:fade .5s ease {delay_in:.2f}s both, toFill 1s ease {l2+0.1:.2f}s both" + ("" if top else f", dim .8s ease {l2+3.2:.2f}s both") + ";"
    paths.append(f'<path d="{d}" style="--c:{cls(f["properties"])};{anim}"/>')
sea4 = pathd(SEA, P4)
legend = "".join(f'<span><i style="background:var(--q{k})"></i>{lab}</span>' for k, lab in enumerate(["0–20", "20–40", "40–60", "60–80", "80–100"]))
BOX4 = (-116.40, 32.62, -115.25, 33.80)
reg4 = regional(P4, BOX4, l1+0.3, tlist=TOWNS_ALL, counties=True, mexico=True)
fx, fy = P4(-115.56, 33.02)
burden = f'''<svg class="abs map" viewBox="0 0 1280 720" style="inset:0"><defs><clipPath id="clp4"><rect x="640" y="30" width="600" height="660"/></clipPath></defs>
<g clip-path="url(#clp4)"><g style="transform-origin:{fx:.0f}px {fy:.0f}px;{a('cam', l2+3.2, 3.5, 'cubic-bezier(.5,0,.2,1)')}">{''.join(paths)}<g class="ov">{reg4}</g><path d="{sea4}" style="fill:var(--sea);stroke:var(--sea2);stroke-width:1.5"/></g></g></svg>
<div class="big" style="left:70px;top:150px;{a('up', l1+0.2)}"><span class="num" style="{a('count79', l1+0.4, 1.4, 'ease-out')}"></span><br><small>census tracts around the sea</small></div>
<div class="legend" style="left:70px;top:360px;{a('up', l2+0.3)}"><b>Asthma ER visits · statewide percentile</b><div>{legend}</div></div>
<div class="big alt" style="left:230px;top:440px;{a('up', l2+3.4)}">20 of 79<br><small>in California’s worst 15% · all in Imperial County</small></div>'''
parts.append(scene(s, burden + host_bubble(SC['burden']['start']+0.3) + source("Data: CalEnviroScreen 4.0 (OEHHA, 2021); highways and border: Natural Earth", l0+0.5), 4))

# ---------- 5 DUST ----------
s = "dust"; l0, l1, l2 = L(s, 0), L(s, 1), L(s, 2)
base = "".join(f'<path d="{"".join("M" + "L".join("%.1f,%.1f" % P4(x, y) for x, y in p.exterior.coords) + "Z" for p in ([g] if g.geom_type=="Polygon" else [x for x in getattr(g,"geoms",[]) if x.geom_type=="Polygon"]))}" fill="var(--sand2)" stroke="var(--paper)" stroke-width="1"/>' for g in [shape(f["geometry"]).buffer(0).intersection(clip) for f in G["tracts"]["features"]] if not g.is_empty)
mons = ""
for i, m in enumerate(sorted(G["pm"]["monitors"], key=lambda m: -sum(v[2] for v in m["y"].values()))):
    x, y = P4(m["lon"], m["lat"]); tot = sum(v[2] for v in m["y"].values()); r = 10 + 2.0 * math.sqrt(tot)
    mons += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" class="ripple" style="transform-origin:{x:.0f}px {y:.0f}px;opacity:0;{a("ripple", l0+1.6+i*0.18, 2.4, "ease-out", "none", "infinite")}"/>'
    mons += f'<g style="transform-origin:{x:.0f}px {y:.0f}px;{a("pop", l0+1.2+i*0.18)}"><rect x="{x-r:.0f}" y="{y-r:.0f}" width="{2*r:.0f}" height="{2*r:.0f}" transform="rotate(45 {x:.0f} {y:.0f})" fill="var(--ink)" stroke="var(--paper)" stroke-width="3"/><text x="{x:.0f}" y="{y+6:.0f}" text-anchor="middle" class="mon">{tot}</text></g>'
months = [7,16,11,17,22,9,14,8,26,25,6,1]; mx = max(months)
bars = "".join(f'<div class="bar" style="--h:{v/mx*150:.0f}px;{a("grow", l2+0.2+i*0.06, .7)}"><span>{v}</span><i></i><em>{"JFMAMJJASOND"[i]}</em></div>' for i, v in enumerate(months))
dustsc = f'''<div class="lay" style="{a('fadeOut', l2+4.6, .5, 'ease', 'forwards')}">
<svg class="abs" viewBox="0 0 1280 720" style="inset:0"><defs><clipPath id="clp5"><rect x="640" y="30" width="600" height="660"/></clipPath></defs><g clip-path="url(#clp5)">{base}<g class="ov">{regional(P4, (-116.40, 32.62, -115.25, 33.80), l0+0.1, tlist=TOWNS_ALL)}</g><path d="{sea4}" fill="var(--sea)" stroke="var(--sea2)" stroke-width="1.5"/>{wind_field(660, 60, 520, 600, l0+0.8, n=34, seed=11, ang=22)}</g>{mons}</svg>
{label(70, 100, '8 EPA monitors for coarse dust (PM10)', l0+0.8, 'tag')}
<div class="big" style="left:70px;top:160px;{a('up', l1+0.2)}"><span class="num" style="{a('count71', l1+0.4, 1.6, 'ease-out')}"></span> days<br><small>over the federal 24-hour limit, 2023–2025</small></div>
<div class="bars" style="left:70px;top:300px;{a('fade', l2)}">{bars}</div>
<p class="cap" style="left:70px;top:505px;{a('fade', l2+0.4)}">monitor-days over the limit, by month</p>
</div>
<div class="lay q3" style="{a('fade', l2+4.8)}">
  <div class="srcq" style="left:200px;{a('pop', l2+5.0)}"><div class="ic lake"></div>lakebed?</div>
  <div class="srcq" style="left:520px;{a('pop', l2+5.4)}"><div class="ic dune"></div>desert?</div>
  <div class="srcq" style="left:840px;{a('pop', l2+5.8)}"><div class="ic farm"></div>farm field?</div>
</div>'''
parts.append(scene(s, dustsc + host_bubble(SC['dust']['start']+0.3) + source("Data: U.S. EPA AirData, daily PM10, 2023–2025", l0+0.5), 5))

# ---------- 6 GEOAI ----------
s = "geoai"; l0, l1, l2, l3 = L(s, 0), L(s, 1), L(s, 2), L(s, 3)
cols, rows, cw, x0, y0 = 10, 6, 66, 250, 210
import random
random.seed(4)
truth = [[("loose" if (random.random() < 0.35 + 0.05*c) else "crust") for c in range(cols)] for r in range(rows)]
tiles = ""
for r in range(rows):
    for c in range(cols):
        t = truth[r][c]
        if c < 3: t0 = l1 + 1.0 + c * 0.9 + r * 0.08            # drone-labelled
        else:     t0 = l2 + 0.8 + (c - 3) * 0.32 + r * 0.03     # model-predicted
        tiles += f'<rect x="{x0+c*cw}" y="{y0+r*cw}" width="{cw-4}" height="{cw-4}" rx="4" style="--c:var(--{t});animation:toFill .4s ease {t0:.2f}s both"/>'
drone_path = f"M{x0-80} {y0+30} H{x0+3*cw-20} V{y0+rows*cw-40} H{x0+20} V{y0+80} H{x0+3*cw+40}"
geo = f'''<div class="lay" style="{a('fadeOut', l1-0.2, .4, 'ease', 'forwards')}">
  <div class="mega shiftR" style="{a('pop', l0+0.1)}">GeoAI</div>
  <div class="sub shiftR" style="{a('up', l0+1.0)}">artificial intelligence that learns from <b>maps</b> and <b>images</b></div>
  <div class="icons3 shiftR" style="{a('fade', l0+1.6)}"><span class="ic3 m">map</span><i>+</i><span class="ic3 p">image</span><i>→</i><span class="ic3 n">model</span></div>
  {host_full(20, 150, 560, SC['geoai']['start']+0.1, f"animation:point 3.2s ease-in-out {l0+0.4:.2f}s 1 forwards;")}
</div>
<div class="lay" style="{a('fade', l1, .5, 'ease', 'both')};animation-name:fade">
<svg class="abs" viewBox="0 0 1280 720" style="inset:0">
 <g class="tiles">{tiles}</g>
 <rect x="{x0-6}" y="{y0-6}" width="{3*cw+8}" height="{rows*cw+8}" fill="none" stroke="var(--ink)" stroke-width="3" stroke-dasharray="10 6" style="{a('fade', l1+0.6)}"/>
 <g style="offset-path:path('{drone_path}');offset-rotate:0deg;{a('flyDrone', l1+0.6, 5.0, 'linear')}">
   <path d="M0 10 L-46 120 H46 Z" class="beam"/>
   <g transform="translate(-34 -34)"><path d="M14 34 H54 M34 14 V54" stroke="var(--ink)" stroke-width="6"/><circle cx="14" cy="34" r="12" fill="none" stroke="var(--ink)" stroke-width="3"/><circle cx="54" cy="34" r="12" fill="none" stroke="var(--ink)" stroke-width="3"/><circle cx="34" cy="14" r="12" fill="none" stroke="var(--ink)" stroke-width="3"/><circle cx="34" cy="54" r="12" fill="none" stroke="var(--ink)" stroke-width="3"/></g>
 </g>
 <rect x="{x0+3*cw}" y="{y0-10}" width="10" height="{rows*cw+16}" class="scan" style="opacity:0;--sx:{(cols-3)*cw}px;{a('scanX', l2+0.7, 2.6, 'linear', 'none')}"/>
 <g style="{a('satPass', l2, 3.2, 'linear')}"><rect x="-20" y="80" width="40" height="26" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/><path d="M-50 93 H-20 M20 93 H50" stroke="var(--ink)" stroke-width="8"/></g>
</svg>
{label(x0, 130, 'drone labels', l1+1.0, 'tag')}
{label(x0+3*cw+20, 130, 'model predicts the rest from satellite images', l2+0.5, 'tag')}
<div class="keyrow" style="left:{x0}px;top:{y0+rows*cw+20}px;{a('fade', l1+1.4)}"><span><i style="background:var(--crust)"></i>crusted</span><span><i style="background:var(--loose)"></i>loose (dusty)</span></div>
<div class="fc" style="{a('up', l3+0.2)}"><b>Goal: dust forecast</b>
  <div class="days"><div><small>Day 1</small><i class="lv lo"></i>low</div><div><small>Day 2</small><i class="lv hi"></i>HIGH</div><div><small>Day 3</small><i class="lv md"></i>medium</div></div>
  <p>so schools and clinics can prepare</p></div>
</div>'''
parts.append(scene(s, geo + f'<div class="lay" style="{a("fade", l1)}">' + host_bubble(l1+0.2) + '</div>', 6))

# ---------- 7 TEST ----------
s = "test"; l0, l1 = L(s, 0), L(s, 1)
def grid(x, y, mode, d):
    out = ""
    for r in range(4):
        for c in range(10):
            test = ((r*7 + c*3) % 5 == 0) if mode == "rand" else (c in (6, 7))
            col = "var(--clay)" if test else "var(--q2)"
            out += f'<rect x="{x+c*44}" y="{y+r*44}" width="40" height="40" rx="3" fill="{col}" style="{a("pop", d + (c+r)*0.02, .35)}"/>'
    return out
test = f'''<svg class="abs" viewBox="0 0 1280 720" style="inset:0">
 <g>{grid(240, 260, "rand", l0+0.3)}</g>
 <g>{grid(780, 260, "block", l1+0.3)}</g>
 <path d="M240 520 h436" stroke="var(--ink2)"/><path d="M780 520 h436" stroke="var(--ink2)"/>
</svg>
{label(240, 200, 'Random test points', l0+0.3, 'tag')}
{label(240, 545, 'neighbors look alike: scores look too good', l0+1.2, 'cap2')}
{label(780, 200, 'Whole stretches held out', l1+0.3, 'tag')}
{label(780, 545, 'the honest test: shore it has never seen', l1+1.2, 'cap2')}
<div class="keyrow" style="left:240px;top:620px;{a('fade', l0+0.8)}"><span><i style="background:var(--q2)"></i>training</span><span><i style="background:var(--clay)"></i>test</span></div>
<div class="mark x" style="left:620px;top:190px;{a('pop', l0+2.2)}">✕</div>
<div class="mark ok" style="left:1160px;top:190px;{a('pop', l1+2.6)}">✓</div>'''
parts.append(scene(s, test + host_bubble(SC['test']['start']+0.3), 7))

# ---------- 8 FIXES ----------
s = "fixes"; l0, l1, l2, l3 = L(s, 0), L(s, 1), L(s, 2), L(s, 3)
gnd = '<rect x="0" y="150" width="520" height="70" fill="var(--sand2)"/><rect x="0" y="190" width="520" height="30" fill="var(--earth1)"/>'
flood = f'''<div class="lay" style="{a('fadeOut', l2-0.2, .4, 'ease', 'forwards')}">
<svg class="abs" style="left:80px;top:180px;width:620px;height:270px" viewBox="0 0 520 230">{gnd}
 <rect x="20" y="138" height="12" width="480" fill="var(--sea)" stroke="var(--sea2)" style="transform-origin:20px 0;{a('growX', l1+0.5, 2.0, 'ease-out')}"/>
 {''.join(f'<path d="M{60+k*70} 143 h26" class="shim" style="opacity:0;{a("shimmer", l1+2.4+k*0.3, 1.8, "ease-in-out", "none", "infinite")}"/>' for k in range(6))}</svg>
{label(80, 130, 'Owens Lake, California: shallow flooding', l1+0.3, 'tag')}
<div class="stats" style="left:760px;top:170px">
 <div style="{a('up', l1+1.6)}"><b>−99%</b>dust emissions</div>
 <div style="{a('up', l1+3.4)}"><b>$2.5B+</b>in costs</div>
 <div style="{a('up', l1+5.2)}"><b>~60,000</b>acre-feet of water a year</div>
</div></div>'''
grav = "".join(f'<circle cx="{30+i*13+(5 if i%2 else 0)}" cy="{144-(i%3)*2}" r="6" fill="var(--ink2)" stroke="var(--paper)" stroke-width="1.5" style="{a("pop", l2+0.4+i*0.02, .3)}"/>' for i in range(36))
pond = f'<path d="M20 150 l30-24 h8 l30 24z M430 150 l30-24 h8 l30 24z" fill="var(--earth1)"/><rect x="88" y="132" width="342" height="18" fill="var(--sea)" style="transform-origin:0 150px;{a("growY", l2+3.6, 1.0)}"/>' + "".join(f'<path d="M{x} {y} q8 -8 16 0 q8 -8 16 0" stroke="var(--ink)" stroke-width="3" fill="none" style="{a("bob", l2+4.0+i*.2, 2, "ease-in-out", "both", "infinite")}"/>' for i,(x,y) in enumerate([(160,80),(230,60),(300,90)]))
two = f'''<div class="lay" style="{a('fade', l2)};{''}">
<div class="lay" style="{a('fadeOut', l3-0.2, .4, 'ease', 'forwards')}">
<svg class="abs" style="left:60px;top:200px;width:560px;height:250px" viewBox="0 0 520 230">{gnd}{grav}</svg>
<svg class="abs" style="left:660px;top:200px;width:560px;height:250px" viewBox="0 0 520 230">{gnd}{pond}</svg>
{label(60, 150, 'Gravel cover', l2+0.2, 'tag')}{label(60, 470, 'no water · but tons of rock', l2+1.0, 'cap2')}
{label(660, 150, 'Habitat ponds', l2+3.4, 'tag')}{label(660, 470, 'good for birds · about 1/6 of the 2028 goal built', l2+4.2, 'cap2')}
</div></div>'''
patch_cols = ["var(--sea)", "var(--ink2)", "var(--moss)", "var(--q3)", "var(--sea)", "var(--q3)", "var(--ink2)", "var(--moss)"]
patches = "".join(f'<rect x="{200+(i%4)*220}" y="{230+(i//4)*170}" width="210" height="160" rx="8" fill="{c}" style="{a("pop", l3+0.3+i*0.12, .4)}"/>' for i, c in enumerate(patch_cols))
mix = f'''<div class="lay" style="{a('fade', l3)}">
<svg class="abs" viewBox="0 0 1280 720" style="inset:0">{patches}</svg>
{label(640, 140, 'No single fix wins: match each patch to the right fix', l3+0.2, 'tag', 'middle')}
<div class="keyrow" style="left:200px;top:580px;{a('fade', l3+1.4)}"><span><i style="background:var(--sea)"></i>water / ponds</span><span><i style="background:var(--ink2)"></i>gravel</span><span><i style="background:var(--moss)"></i>plants</span><span><i style="background:var(--q3)"></i>roughening</span><em>illustration</em></div>
</div>'''
parts.append(scene(s, flood + two + mix + host_bubble(SC['fixes']['start']+0.3) + source("Sources: LADWP; National Academies (2020); Salton Sea Management Program", l1+0.3), 8))

# ---------- 9 SCENARIOS ----------
s = "scen"; l0, l1 = L(s, 0), L(s, 1)
cards = [("No new lithium", "baseline"), ("One big project", "Hell’s Kitchen"), ("Full build-out", "every project"), ("+ dust control", "mitigation")]
cc = "".join(f'<div class="scard" style="left:{90+i*285}px;{a("flip", l0+0.6+i*0.9, .7)}"><b>{t}</b><small>{d}</small></div>' for i,(t,d) in enumerate(cards))
scen = f'''{cc}
<svg class="abs" viewBox="0 0 1280 720" style="inset:0"><path d="M90 520 H1190 m-26 -16 l26 16 -26 16" stroke="var(--ink)" stroke-width="5" fill="none" style="stroke-dasharray:1200;{a('draw', l1+0.2, 1.4, 'ease-out')}"/></svg>
{label(640, 560, 'compare futures before anything is built', l1+0.8, 'tag', 'middle')}'''
parts.append(scene(s, scen + host_bubble(SC['scen']['start']+0.3), 9))

# ---------- 10 END ----------
s = "end"; l0, l1 = L(s, 0), L(s, 1)
end = f'''<div class="lay" style="{a('fadeOut', l1-0.2, .4, 'ease', 'forwards')}">
 <div class="mega sm2 shiftR" style="{a('pop', l0+0.2)}">Lithium <span class="plus">+</span> clean air</div>
 <div class="sub shiftR" style="{a('up', l0+2.0)}">only if we <b>measure</b></div>
</div>
<div class="lay endc shiftR" style="{a('fade', l1)}">
 <small>GeoAI for Cities · research plan</small>
 <h1>Lithium Without the Dust:<br>A GeoAI Plan for the Salton Sea</h1>
 <p>Jhoven (Johan) Fernandez</p>
 <div class="url">Full plan, maps and code<br><b>github.com/jhovenf98/geoai-for-cities</b></div>
</div>'''
parts.append(scene(s, end + host_full(20, 150, 560, SC['end']['start']+0.1, f"animation:point 4s ease-in-out {l1+0.6:.2f}s 1 forwards, wave 2s ease-in-out {T['total']-2.6:.2f}s 1 forwards;"), 10))

total = T["total"]
progress = f'<div class="prog"><i style="animation:prog {total:.2f}s linear 0s both"></i></div>'

FONT = "/home/claude/explainer/fonts"
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:PS;src:url(file://{FONT}/public-sans-latin-400-normal.woff2);font-weight:400}}
@font-face{{font-family:PS;src:url(file://{FONT}/public-sans-latin-600-normal.woff2);font-weight:600}}
@font-face{{font-family:PS;src:url(file://{FONT}/public-sans-latin-700-normal.woff2);font-weight:700}}
@font-face{{font-family:PS;src:url(file://{FONT}/public-sans-latin-800-normal.woff2);font-weight:800}}
@property --n{{syntax:'<integer>';inherits:false;initial-value:0}}
:root{{--bg:#F3EBDD;--paper:#FBF7EE;--ink:#2B2219;--ink2:#6B5A47;--rule:#D6C7AC;--sand2:#E7D6B8;--playa:#E9DDC4;
--sea:#8FC1CF;--sea2:#2F6F82;--clay:#B0643A;--hot:#F2A65A;--earth1:#CDA77A;--earth2:#A9805A;--pipe:#5C6B70;
--dust:rgba(196,150,96,.55);--moss:#4E7A46;--q0:#F3E3CF;--q1:#E5BE94;--q2:#D0905C;--q3:#A9622F;--q4:#6E3A17;--none:#D8D2C6;
--crust:#F4F1EA;--loose:#B98B57;--mx:#E6E1D8}}
*{{box-sizing:border-box;margin:0}}
html,body{{width:1280px;height:720px;overflow:hidden;background:var(--bg);font-family:PS,sans-serif;color:var(--ink)}}
.sc{{position:absolute;inset:0}}
.lay{{position:absolute;inset:0}}
.abs{{position:absolute}}
.chap{{position:absolute;left:56px;top:40px;display:flex;gap:12px;align-items:center;font-weight:700;font-size:22px;letter-spacing:.01em;z-index:5}}
.chap b{{background:var(--ink);color:var(--paper);font-size:16px;padding:5px 9px;border-radius:4px}}
.mid{{position:absolute;left:0;width:1280px;text-align:center}}
.src{{position:absolute;right:40px;bottom:30px;font-size:15px;color:var(--ink2);z-index:5}}
.tag{{position:absolute;font-weight:700;font-size:26px;background:var(--paper);padding:8px 16px;border-radius:6px;box-shadow:0 2px 0 var(--rule);white-space:nowrap}}
.lbl,.cap2{{position:absolute;font-size:22px;color:var(--ink2);white-space:nowrap}}
.cap{{position:absolute;font-size:17px;color:var(--ink2)}}
.step{{position:absolute;font-weight:700;font-size:22px;background:var(--paper);padding:6px 14px;border-radius:6px;white-space:nowrap;box-shadow:0 2px 0 var(--rule)}}
.step b{{background:var(--clay);color:var(--paper);border-radius:50%;width:28px;height:28px;display:inline-grid;place-items:center;margin-right:8px;font-size:16px}}
.big{{position:absolute;font-weight:800;font-size:76px;line-height:1.02;letter-spacing:-.02em}}
.big small{{display:block;font-size:24px;font-weight:600;color:var(--ink2);letter-spacing:0;margin-top:10px;max-width:520px;line-height:1.3}}
.big.alt{{font-size:64px;color:var(--q4)}}
.hl{{color:var(--clay)}}
.num{{counter-reset:n var(--n)}} .num::after{{content:counter(n)}}
.mega{{position:absolute;left:0;right:0;top:230px;text-align:center;font-weight:800;font-size:150px;letter-spacing:-.04em}}
.mega.sm2{{font-size:96px;top:250px}} .plus{{color:var(--clay)}}
.sub{{position:absolute;left:0;right:0;top:420px;text-align:center;font-size:34px;color:var(--ink2)}}
.sub b{{color:var(--ink)}}
.li{{position:absolute;width:120px;height:130px;background:var(--paper);border:4px solid var(--ink);border-radius:10px;display:grid;place-items:center;padding:8px}}
.li small{{position:absolute;left:10px;top:6px;font-size:18px;font-weight:700}}
.li b{{font-size:56px;font-weight:800;line-height:1}} .li em{{font-style:normal;font-size:15px;font-weight:600}}
.li.sm{{width:70px;height:70px}} .li.sm b{{font-size:34px}}
.batt{{position:absolute;width:160px;height:70px;border:5px solid var(--ink);border-radius:10px;padding:6px;background:var(--paper)}}
.batt::after{{content:"";position:absolute;right:-16px;top:18px;width:10px;height:24px;background:var(--ink);border-radius:0 4px 4px 0}}
.bfill{{height:100%;background:var(--moss);border-radius:4px;width:var(--w,0%)}}
.batt span{{position:absolute;left:0;right:0;top:78px;text-align:center;font-weight:700;font-size:18px}}
.dustcloud{{position:absolute;width:280px;height:120px;border-radius:50%;background:radial-gradient(closest-side,rgba(196,150,96,.7),rgba(196,150,96,0))}}
.lip{{font:800 26px PS;fill:#FFF3DF}}
.svgl{{font:700 20px PS;fill:var(--ink);paint-order:stroke;stroke:var(--paper);stroke-width:5px}}
.svgl.light{{fill:#FFF3DF;stroke:none;font-size:24px}}
.mon{{font:800 18px PS;fill:var(--paper)}}
.key{{position:absolute;font-size:21px;font-weight:600;padding-left:40px}}
.key::before{{content:"";position:absolute;left:0;top:4px;width:28px;height:20px;border-radius:3px}}
.key.dash::before{{border:2px dashed var(--ink2)}} .key.playa::before{{background:var(--playa);border:1px solid var(--ink2)}}
.card{{position:absolute;display:flex;gap:16px;background:var(--paper);border-left:6px solid var(--clay);padding:18px 22px;width:460px;box-shadow:0 6px 0 var(--rule)}}
.card small{{font-weight:700;color:var(--clay);font-size:16px}} .card p{{font-size:22px;font-weight:600;line-height:1.35;margin-top:4px}}
.cicon{{font-size:46px;line-height:1}}
.map path{{stroke:var(--paper);stroke-width:1;fill:var(--sand2)}}
.legend{{position:absolute;font-size:17px}} .legend b{{display:block;margin-bottom:8px}}
.legend div{{display:flex;gap:10px}} .legend span{{display:flex;gap:5px;align-items:center}} .legend i{{width:20px;height:20px;display:inline-block;border-radius:3px}}
.bars{{position:absolute;display:flex;gap:10px;align-items:flex-end;height:200px}}
.bar{{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;width:30px;font-size:15px;font-weight:700;height:200px}}
.bar i{{display:block;width:100%;height:var(--h);background:var(--clay);border-radius:4px 4px 0 0;transform-origin:bottom}}
.bar em{{font-style:normal;color:var(--ink2);margin-top:4px}}
.srcq{{position:absolute;top:260px;width:240px;text-align:center;font-size:30px;font-weight:700;display:grid;justify-items:center;gap:14px}}
.ic{{width:160px;height:120px;border-radius:12px;background:var(--paper);border:4px solid var(--ink);position:relative;overflow:hidden}}
.ic.lake::before{{content:"";position:absolute;left:10px;right:10px;top:40px;height:40px;background:var(--playa);border-radius:50%;box-shadow:inset 0 0 0 10px var(--sea)}}
.ic.dune::before{{content:"";position:absolute;left:-20px;right:-20px;bottom:-60px;height:130px;background:var(--earth1);border-radius:50% 50% 0 0}}
.ic.farm::before{{content:"";position:absolute;inset:30px 12px 12px;background:repeating-linear-gradient(90deg,var(--moss) 0 10px,var(--earth1) 10px 20px)}}
.keyrow{{position:absolute;display:flex;gap:22px;font-size:19px;font-weight:600;align-items:center}}
.keyrow span{{display:flex;gap:8px;align-items:center}} .keyrow i{{width:22px;height:22px;border-radius:4px;display:inline-block;border:1px solid var(--rule)}}
.keyrow em{{font-style:italic;color:var(--ink2);font-weight:400}}
.tiles rect{{fill:var(--sand2)}}
.fc{{position:absolute;left:1080px;top:200px;width:190px;display:none}}
.fc{{display:grid;left:auto;right:30px;top:180px;width:300px;background:var(--paper);padding:18px;border-radius:10px;box-shadow:0 6px 0 var(--rule);gap:10px;font-size:19px}}
.fc p{{font-size:17px;color:var(--ink2)}}
.days{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center;font-weight:700;font-size:16px}}
.days small{{display:block;color:var(--ink2);font-weight:600}}
.lv{{display:block;height:46px;margin:6px 0;border-radius:6px}} .lv.lo{{background:var(--q0)}} .lv.md{{background:var(--q2)}} .lv.hi{{background:var(--q4)}}
.mark{{position:absolute;font-size:56px;font-weight:800;width:72px;height:72px;border-radius:50%;display:grid;place-items:center;color:var(--paper)}}
.mark.x{{background:var(--clay)}} .mark.ok{{background:var(--moss)}}
.stats{{position:absolute;display:grid;gap:22px}}
.stats div{{font-size:22px;color:var(--ink2);font-weight:600}} .stats b{{display:block;font-size:60px;color:var(--ink);font-weight:800;line-height:1}}
.scard{{position:absolute;top:250px;width:255px;height:200px;background:var(--paper);border-radius:12px;border-top:8px solid var(--clay);box-shadow:0 6px 0 var(--rule);display:grid;align-content:center;justify-items:center;text-align:center;gap:8px;padding:16px}}
.scard b{{font-size:28px;line-height:1.15}} .scard small{{font-size:19px;color:var(--ink2)}}
.endc{{display:grid;align-content:center;justify-items:center;text-align:center;gap:18px}}
.endc small{{font-size:22px;font-weight:700;color:var(--clay);letter-spacing:.06em;text-transform:uppercase}}
.endc h1{{font-size:58px;line-height:1.08;font-weight:800;letter-spacing:-.02em}}
.endc p{{font-size:26px;color:var(--ink2)}}
.url{{margin-top:16px;background:var(--ink);color:var(--paper);padding:18px 30px;border-radius:10px;font-size:22px;line-height:1.5}} .url b{{font-size:30px}}
.prog{{position:absolute;left:0;right:0;bottom:0;height:6px;background:var(--rule);z-index:9}} .prog i{{display:block;height:100%;background:var(--clay);transform-origin:left}}
@keyframes sIn{{from{{opacity:0}}to{{opacity:1}}}} @keyframes sOut{{to{{opacity:0}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}} @keyframes fadeOut{{to{{opacity:0}}}}
@keyframes up{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:none}}}}
@keyframes slideR{{from{{opacity:0;transform:translateX(-30px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(.5)}}70%{{opacity:1;transform:scale(1.08)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes carIn{{from{{transform:translateX(-500px)}}to{{transform:none}}}}
@keyframes spin{{from{{transform:rotate(0)}}to{{transform:rotate(720deg)}}}}
@keyframes fillW{{from{{--w:0%;width:0%}}to{{width:100%}}}}
@keyframes draw{{from{{stroke-dashoffset:3000}}to{{stroke-dashoffset:0}}}}
@keyframes ping{{from{{transform:scale(1);opacity:1}}to{{transform:scale(4);opacity:0}}}}
@keyframes drift{{0%{{opacity:0;transform:translateX(-40px) scale(.7)}}40%{{opacity:1}}100%{{opacity:.9;transform:translateX(60px) scale(1.1)}}}}
@keyframes zoomTo{{from{{transform:translate(0,0) scale(1)}}to{{transform:translate(var(--tx),var(--ty)) scale(var(--k))}}}}
@keyframes glow{{0%,100%{{opacity:.85}}50%{{opacity:1}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}
@keyframes flowUp{{from{{offset-distance:0%;opacity:1}}to{{offset-distance:100%;opacity:1}}}}
@keyframes shrink{{from{{transform:scale(1)}}to{{transform:scale(.8,.86)}}}}
@keyframes windA{{0%{{opacity:0;transform:translateX(-40px)}}30%{{opacity:1}}100%{{opacity:0;transform:translateX(160px)}}}}
@keyframes blow{{0%{{opacity:0;transform:translate(0,0) scale(.6)}}30%{{opacity:1}}100%{{opacity:0;transform:translate(220px,-90px) scale(1.4)}}}}
@keyframes toFill{{to{{fill:var(--c)}}}}
@keyframes dim{{to{{opacity:.22}}}}
@keyframes count79{{from{{--n:0}}to{{--n:79}}}} @keyframes count71{{from{{--n:0}}to{{--n:71}}}}
@keyframes grow{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes flyDrone{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
@keyframes satPass{{from{{transform:translateX(-80px)}}to{{transform:translateX(1360px)}}}}
@keyframes growX{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes growY{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes flip{{from{{opacity:0;transform:perspective(800px) rotateY(80deg)}}to{{opacity:1;transform:none}}}}
@keyframes prog{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.bar i{{animation:inherit;animation-name:barH}}
@keyframes barH{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}

.shiftR{{left:320px!important;right:0}}
.endc.shiftR{{left:300px!important}}
.icons3{{position:absolute;top:500px;display:flex;justify-content:center;gap:16px;align-items:center;font-size:30px;font-weight:700;color:var(--ink2)}}
.ic3{{background:var(--paper);border:3px solid var(--ink);border-radius:10px;padding:10px 20px;font-size:22px;color:var(--ink)}}
.ic3.m{{border-color:var(--moss)}} .ic3.p{{border-color:var(--sea2)}} .ic3.n{{border-color:var(--clay)}}
.mxl{{font:800 20px PS;letter-spacing:.3em;fill:var(--ink2);opacity:.75}}
.rdM{{fill:none;stroke:#8C7A66;stroke-width:3.2;stroke-linecap:round;stroke-linejoin:round;opacity:.9}}
.rdS{{fill:none;stroke:#A8977F;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.85}}
.shI{{fill:#2F4E80;stroke:#fff;stroke-width:2}} .shS{{fill:#fff;stroke:var(--ink);stroke-width:2}}
.shT{{font:800 14px PS;fill:#fff}} .shS+.shT{{fill:var(--ink)}}
.twC{{fill:var(--paper);stroke:var(--ink);stroke-width:2.5}}
.twT{{font:700 15px PS;fill:var(--ink);paint-order:stroke;stroke:var(--paper);stroke-width:4px;stroke-linejoin:round}}
.map .ov path{{stroke-width:inherit}}
.map path.rdM,.map path.rdS{{fill:none}}
.wf{{stroke:var(--ink2);stroke-width:2.2;stroke-linecap:round;fill:none}}
.ripple{{fill:none;stroke:var(--clay);stroke-width:3}}
.beam{{fill:rgba(242,166,90,.28);stroke:rgba(176,100,58,.5)}}
.scan{{fill:rgba(47,111,130,.35)}}
.shim{{stroke:#fff;stroke-width:3;stroke-linecap:round;opacity:.8}}
.dustcloud.big2{{width:440px;height:200px}}
.host{{position:absolute;z-index:6}}
.host.full .hostsvg{{height:100%;width:auto;display:block}}
.host.bub{{left:26px;top:526px;width:168px;height:168px;border-radius:50%;background:var(--paper);border:5px solid var(--ink);overflow:hidden;box-shadow:0 6px 0 var(--rule)}}
.bubin{{position:absolute;left:-36px;top:-10px;width:240px}} .bubin .hostsvg{{width:240px;height:auto;display:block}}
.hshadow{{fill:rgba(43,34,25,.15)}}
.hpants{{fill:#3E3A36}} .hshoe{{fill:#2B2219}}
.hjacket{{fill:#4E7A46}} .hshirt{{fill:#F4EEDF}} .hcollar{{fill:#3F6639}} .hzip{{stroke:#3F6639;stroke-width:3}}
.hpatch{{fill:#F2A65A}} .hpatchT{{font:800 10px PS;fill:#2B2219}}
.htab{{fill:#2B2219}} .htabS{{fill:#8FC1CF}}
.hskin{{fill:#C88E66}} .hhair{{fill:#2B2219}} .hbrow{{stroke:#2B2219;stroke-width:5;fill:none;stroke-linecap:round}}
.heye{{fill:#2B2219}} .hglint{{fill:#fff}} .hnose{{stroke:#A86E4A;stroke-width:3;fill:none;stroke-linecap:round}}
.hcheek{{fill:#E39C86;opacity:.45}} .mouth{{fill:#6B2E22}} .hsmile{{stroke:#6B2E22;stroke-width:3;fill:none;stroke-linecap:round;opacity:.6}}
.hmouthG{{transform-box:fill-box;transform-origin:center;transform:scaleY(calc(.12 + var(--m,0) * .95)) scaleX(calc(.85 + var(--m,0) * .2))}}
.heyes{{transform-box:fill-box;transform-origin:center;animation:blink 4.3s linear 0s infinite both}}
.hhead{{transform-origin:150px 190px;animation:headBob 5s ease-in-out 0s infinite both}}
.hbody{{transform-origin:150px 500px;animation:breathe 3.6s ease-in-out 0s infinite both}}
.harmR{{transform-origin:210px 222px}}
@keyframes blink{{0%,93%,100%{{transform:scaleY(1)}}95.5%{{transform:scaleY(.1)}}}}
@keyframes headBob{{0%,100%{{transform:rotate(-1.5deg)}}50%{{transform:rotate(1.8deg)}}}}
@keyframes breathe{{0%,100%{{transform:scaleY(1)}}50%{{transform:scaleY(1.008)}}}}
@keyframes hostIn{{from{{opacity:0;transform:translateX(-60px)}}to{{opacity:1;transform:none}}}}
@keyframes wave{{0%{{transform:rotate(0)}}15%{{transform:rotate(-150deg)}}30%{{transform:rotate(-125deg)}}45%{{transform:rotate(-150deg)}}60%{{transform:rotate(-125deg)}}75%{{transform:rotate(-150deg)}}100%{{transform:rotate(0)}}}}
@keyframes point{{0%{{transform:rotate(0)}}14%{{transform:rotate(-100deg)}}86%{{transform:rotate(-96deg)}}100%{{transform:rotate(0)}}}}
@keyframes drawL{{from{{stroke-dashoffset:var(--L)}}to{{stroke-dashoffset:0}}}}
@keyframes streak{{0%{{opacity:0;translate:0 0}}20%{{opacity:.7}}100%{{opacity:0;translate:var(--dx) 40px}}}}
@keyframes ripple{{from{{opacity:.8;transform:scale(1)}}to{{opacity:0;transform:scale(2.4)}}}}
@keyframes plume{{0%{{opacity:0;transform:translate(0,0) scale(.5)}}25%{{opacity:.9}}100%{{opacity:0;transform:translate(150px,-40px) scale(1.7)}}}}
@keyframes cam{{from{{transform:scale(1)}}to{{transform:scale(1.55)}}}}
@keyframes scanX{{0%{{opacity:1;transform:translateX(0)}}100%{{opacity:1;transform:translateX(var(--sx))}}}}
@keyframes shimmer{{0%,100%{{opacity:0}}50%{{opacity:.9}}}}
</style></head><body>
{''.join(parts)}
{progress}
<script>
window.LIPS={json.dumps(LIPS['m'])};
window.seek=function(t){{document.getAnimations().forEach(function(a){{a.pause();a.currentTime=t*1000;}});
 var i=Math.min(window.LIPS.length-1,Math.max(0,Math.round(t*24)));var m=window.LIPS[i]||0;
 document.querySelectorAll('.hmouthG').forEach(function(g){{g.style.setProperty('--m',m);}});}};
window.TOTAL={total};
</script>
</body></html>'''
open("video2.html", "w").write(html)
print("ok", total)
