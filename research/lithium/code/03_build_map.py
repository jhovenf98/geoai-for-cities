"""Build the interactive map's SVG (tracts, Salton Sea, towns, approximate geothermal field, PM10 monitors).

Output: data/processed/map_svg.html, a fragment pasted into the web page. The page's JavaScript reads
the data-* attributes on each tract and monitor; see page/index.html.
Town points and the geothermal-field ellipse are approximate and for orientation only.
"""
import json, math
from shapely.geometry import shape, box, MultiPolygon
from _paths import RAW, OUT, BBOX

W, S, E, N = BBOX
K = 900                                   # SVG units per degree of latitude
CX = math.cos(math.radians(33.2))         # shrink longitude so shapes are not stretched

def P(x, y):
    return ((x - W) * CX * K, (N - y) * K)

def path_d(geom):
    out = []
    for p in ([geom] if geom.geom_type == "Polygon" else list(geom.geoms)):
        for r in [p.exterior] + list(p.interiors):
            out.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in (P(x, y) for x, y in r.coords)) + "Z")
    return "".join(out)

TOWNS = [("Niland", -115.519, 33.240, "r"), ("Calipatria", -115.514, 33.125, "r"), ("Brawley", -115.530, 32.979, "r"),
         ("Westmorland", -115.621, 33.037, "l"), ("Salton City", -115.956, 33.299, "l"), ("Bombay Beach", -115.729, 33.351, "r"),
         ("Mecca", -116.077, 33.572, "l"), ("Coachella", -116.174, 33.680, "l"), ("El Centro", -115.563, 32.792, "l"),
         ("Calexico", -115.499, 32.679, "r"), ("North Shore", -115.930, 33.520, "r")]
OFFSET = {"Westmorland": 30, "Brawley": 30, "El Centro": 26, "Calexico": 26, "Mecca": 28, "Coachella": 12}
KEYS = ["tract", "pop", "asthma", "asthmaP", "pm", "pmP", "pov", "povP", "ces"]

def fmt(k, v):
    if v is None: return ""
    return int(v) if (k.endswith("P") or k in ("ces", "pop")) else v

def main():
    clip = box(W, S, E, N)
    tracts = json.load(open(OUT / "ces_tracts_salton.geojson"))
    paths = []
    for f in tracts["features"]:
        g = shape(f["geometry"]).buffer(0).intersection(clip)
        if g.is_empty: continue
        if g.geom_type == "GeometryCollection":
            g = MultiPolygon([x for x in g.geoms if x.geom_type == "Polygon"])
        attrs = " ".join(f'data-{k}="{fmt(k, f["properties"][k])}"' for k in KEYS)
        paths.append(f'<path class="t" {attrs} tabindex="0" d="{path_d(g)}"/>')
    sea = shape(json.load(open(RAW / "salton_sea_ne10m.geojson"))["features"][0]["geometry"])
    towns = []
    for n, x, y, side in TOWNS:
        a, b = P(x, y); off = OFFSET.get(n, 9); dx = off if side == "r" else -off
        towns.append(f'<g class="town"><circle cx="{a:.1f}" cy="{b:.1f}" r="4"/><text x="{a+dx:.1f}" y="{b+4:.1f}" '
                     f'text-anchor="{"start" if side == "r" else "end"}">{n}</text></g>')
    gx, gy = P(-115.605, 33.170); rx, ry = 0.07 * CX * K, 0.06 * K
    geo = (f'<g class="geo"><ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>'
           f'<text x="{gx-rx-6:.1f}" y="{gy+ry+18:.1f}">Geothermal field (approx.)</text></g>')
    pm = json.load(open(RAW / "pm10_monitors_2023_2025.json"))
    mons = []
    for m in sorted(pm["monitors"], key=lambda m: -sum(v[2] for v in m["y"].values())):
        a, b = P(m["lon"], m["lat"]); tot = sum(v[2] for v in m["y"].values()); r = 6 + 1.8 * math.sqrt(tot)
        yrs = ";".join(f"{y}:{':'.join(map(str, v))}" for y, v in m["y"].items())
        mons.append(f'<g class="mon" tabindex="0" role="button" data-name="{m["name"]}" data-id="{m["id"]}" '
                    f'data-tot="{tot}" data-yrs="{yrs}"><rect x="{a-r:.1f}" y="{b-r:.1f}" width="{2*r:.1f}" '
                    f'height="{2*r:.1f}" transform="rotate(45 {a:.1f} {b:.1f})"/>'
                    f'<text x="{a:.1f}" y="{b+5:.1f}" text-anchor="middle">{tot}</text></g>')
    vw, vh = P(E, S)
    sx, sy = P(-115.83, 33.33)
    svg = (f'<svg class="im-svg lv-svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Map of census tracts '
           f'around the Salton Sea">\n<g id="lv-tracts">{"".join(paths)}</g>\n<path class="sea" d="{path_d(sea)}"/>'
           f'<text class="sealbl" x="{sx:.1f}" y="{sy:.1f}" text-anchor="middle">Salton Sea</text>\n'
           f'{geo}{"".join(towns)}<g id="lv-mon">{"".join(mons)}</g></svg>')
    (OUT / "map_svg.html").write_text(svg)
    print(f"{len(paths)} tracts, {len(mons)} monitors -> {OUT / 'map_svg.html'}")

if __name__ == "__main__":
    main()
