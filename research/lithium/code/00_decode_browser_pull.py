"""Decode the CalEnviroScreen snapshot that was pulled in a browser (data/raw/ces_tracts_salton.txt).

Why this exists: the original pull was made from a browser session, and each tract was written as one
compact line so it could be copied out:  attributes | ring/ring
  attributes = tract,pop,asthma,asthmaP,pm,pmP,pov,povP,CIscoreP
  ring       = space-separated integers (degrees x 1000); first pair absolute, then deltas.
If you can reach the internet, 01_pull_calenviroscreen.py rebuilds the same layer directly.
"""
import json
from _paths import RAW, OUT

def decode_ring(text):
    n = list(map(int, text.split()))
    x, y = n[0], n[1]
    pts = [(x / 1000, y / 1000)]
    for i in range(2, len(n), 2):
        x += n[i]; y += n[i + 1]
        pts.append((x / 1000, y / 1000))
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts

def num(s):
    return float(s) if s != "" else None

def main():
    feats = []
    for line in open(RAW / "ces_tracts_salton.txt"):
        attrs, geom = line.strip().split("|")
        f = attrs.split(",")
        rings = [decode_ring(r) for r in geom.split("/")]
        p = {"tract": f[0], "pop": int(f[1]), "asthma": num(f[2]), "asthmaP": num(f[3]),
             "pm": num(f[4]), "pmP": num(f[5]), "pov": num(f[6]), "povP": num(f[7]), "ces": num(f[8])}
        if p["pov"] is None:          # one tract has no poverty value, so no overall score either
            p["povP"] = None; p["ces"] = None
        g = ({"type": "Polygon", "coordinates": rings} if len(rings) == 1
             else {"type": "MultiPolygon", "coordinates": [[r] for r in rings]})
        feats.append({"type": "Feature", "properties": p, "geometry": g})
    out = OUT / "ces_tracts_salton.geojson"
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"))
    print(f"{len(feats)} tracts -> {out}")

if __name__ == "__main__":
    main()
