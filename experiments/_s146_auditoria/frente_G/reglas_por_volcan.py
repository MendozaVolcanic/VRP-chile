"""Frente G: tabula las claves por volcan de volcanoes.yaml y de pipeline/volcanic_features.yaml. Solo lectura."""
import yaml, json, os, collections
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
cfg = yaml.safe_load(open(os.path.join(root, "volcanoes.yaml"), encoding="utf-8"))
vs = cfg["volcanoes"]
print("claves de nivel raiz:", [k for k in cfg if k != "volcanoes"])
keys = collections.Counter(k for v in vs for k in v)
print("n volcanes", len(vs)); print(keys)
base = {"name","display_name","lat","lon","radius_km","region","elevation_m","active","tier"}
out = {}
for v in vs:
    exc = {k: v[k] for k in v if k not in base}
    out[v["name"]] = {"radius_km": v.get("radius_km"), **exc}
tierA = [n for n, d in out.items() if d.get("radius_km") == 25]
print("radius 25:", tierA)
for n in tierA:
    print(n, json.dumps(out[n], ensure_ascii=False, default=str))
print("--- resto: claves no base que aparezcan")
for n, d in out.items():
    if n in tierA: continue
    extra = {k: x for k, x in d.items() if k not in ("radius_km","vent_lat","vent_lon","vent_radius_km","inner_radius_km")}
    if extra: print(n, extra)
from collections import Counter
print(Counter((d.get("radius_km"), d.get("inner_radius_km"), d.get("vent_radius_km")) for n,d in out.items() if n not in tierA))
json.dump(out, open(os.path.join(os.path.dirname(__file__), "reglas_por_volcan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
vf = yaml.safe_load(open(os.path.join(root, "pipeline", "volcanic_features.yaml"), encoding="utf-8"))
print("volcanic_features:", json.dumps(vf, ensure_ascii=False)[:1500])
