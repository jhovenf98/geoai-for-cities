"""Pull CalEnviroScreen 4.0 census tracts around the Salton Sea from OEHHA's official feature service.

Output: data/processed/ces_tracts_salton_live.geojson (same fields as the browser snapshot).
Missing values in CalEnviroScreen are coded -999; they become null here.
"""
import json
import requests
from _paths import OUT, BBOX

URL = ("https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/"
       "CalEnviroScreen_4_0_Results_/FeatureServer/0/query")
KEEP = {"tract": "tract", "acs2019totalpop": "pop", "asthma": "asthma", "asthmap": "asthmaP",
        "pm": "pm", "pmp": "pmP", "pov": "pov", "povp": "povP", "ciscorep": "ces"}

def main(simplify_deg=0.007):
    params = {
        "where": "1=1", "geometry": ",".join(map(str, BBOX)), "geometryType": "esriGeometryEnvelope",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326,
        "maxAllowableOffset": simplify_deg, "geometryPrecision": 3, "f": "geojson",
    }
    r = requests.get(URL, params=params, timeout=60)
    r.raise_for_status()
    fc = r.json()
    for f in fc["features"]:
        src = {k.lower(): v for k, v in f["properties"].items()}
        props = {}
        for k, new in KEEP.items():
            v = src.get(k)
            props[new] = None if v in (None, -999, -999.0) else v
        props["tract"] = str(int(float(props["tract"])))
        f["properties"] = props
    out = OUT / "ces_tracts_salton_live.geojson"
    json.dump(fc, open(out, "w"))
    print(f"{len(fc['features'])} tracts -> {out}")

if __name__ == "__main__":
    main()
