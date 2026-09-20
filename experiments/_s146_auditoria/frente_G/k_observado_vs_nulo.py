"""Frente G: compara test1_k_observed y n_test1_pixels persistidos (regimen >= 2026-09-01) con la prediccion del nulo
de ruido puro: k ~ 0,399*sqrt(N_roi), n_contrib ~ N_roi/2. Solo lectura."""
import json, os, statistics as st, yaml, collections
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
cfg = yaml.safe_load(open(os.path.join(root, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]
D = collections.defaultdict(lambda: {"k": [], "n": [], "k_no": []})
for v in cfg:
    if not v.get("inner_radius_km"): continue
    for r in json.load(open(os.path.join(root, "data/mirova_equivalent", v["name"] + ".json"), encoding="utf-8"))["records"]:
        if (r.get("datetime_utc") or "") < "2026-09-01": continue
        s = str(r.get("sensor") or ""); b = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
        if r.get("triggered_test1"):
            D[b]["k"].append(r.get("test1_k_observed") or 0); D[b]["n"].append(r.get("n_test1_pixels") or 0)
        else: D[b]["k_no"].append(r.get("test1_k_observed") or 0)
out = {}
for b, d in D.items():
    q = lambda x, p: sorted(x)[int(p * (len(x) - 1))] if x else None
    out[b] = {"n_dispara": len(d["k"]), "k_obs_p10_p50_p90": [q(d["k"], .1), q(d["k"], .5), q(d["k"], .9)],
              "n_test1_pixels_p10_p50_p90": [q(d["n"], .1), q(d["n"], .5), q(d["n"], .9)],
              "n_no_dispara": len(d["k_no"]), "k_obs_no_dispara_p10_p50_p90": [q(d["k_no"], .1), q(d["k_no"], .5), q(d["k_no"], .9)]}
    print(b, out[b])
print("prediccion nulo: V375 N=208 -> k=5,75 n=104 | V750 N=49 -> k=2,79 n=24 | MODIS N=32 -> k=2,26 n=16")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "k_observado_vs_nulo.json"), "w"), indent=1)
