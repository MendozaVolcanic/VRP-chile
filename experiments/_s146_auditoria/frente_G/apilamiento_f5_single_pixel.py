"""Frente G: apilamiento single_pixel_mode (pipeline) + nucleo F5' (store/dashboard) en VIIRS375, y tope Villarrica.
Regimen >= 2026-09-01. Solo lectura."""
import json, os, statistics as st, collections, yaml
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
cfg = yaml.safe_load(open(os.path.join(root, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]
tierA = {v["name"]: v for v in cfg if v.get("inner_radius_km")}
C = collections.Counter(); ratios = []; ratios_sp = []; vill = []
for name, v in tierA.items():
    d = json.load(open(os.path.join(root, "data", "mirova_equivalent", name + ".json"), encoding="utf-8"))
    for r in d["records"]:
        if (r.get("datetime_utc") or "") < "2026-09-01": continue
        s = str(r.get("sensor") or ""); pc = r.get("primary_cluster") or {}
        if name == "Villarrica" and (pc.get("n_pixels") or 0) > 12:
            vill.append((r["datetime_utc"], s, pc.get("n_pixels"), pc.get("vrp_mw"), r.get("vrp_mw"), r.get("triggered_test1"), r.get("distance_class"), r.get("discarded_reason")))
        if s.startswith("MODIS") or s.endswith("_750"): continue
        f5 = r.get("f5_core_vrp_mw"); p = pc.get("vrp_mw") or 0
        if f5 is None or p <= 0 or r.get("distance_class") != "summit": continue
        C["n V375 summit con f5 y pc>0"] += 1
        sp = bool(pc.get("single_pixel_mode")); npx = pc.get("n_pixels") or 0
        ratios.append(f5 / p)
        if f5 > p + 0.0015:
            C["f5 > pc"] += 1
            C["f5 > pc y single_pixel_mode=True"] += sp
            C["f5 > pc y single_pixel y n_pixels>1"] += (sp and npx > 1)
            C["f5 > pc y single_pixel y n_pixels==1 (F5 suma pixeles de OTRO cumulo o BT>=295)"] += (sp and npx == 1)
            C["f5 > pc y NO single_pixel"] += (not sp)
        elif f5 < p - 0.0015: C["f5 < pc"] += 1
        else: C["f5 == pc"] += 1
        if sp and npx > 1: ratios_sp.append(f5 / p)
print(dict(C))
print("mediana f5/pc todos:", round(st.median(ratios), 3), "n", len(ratios))
if ratios_sp: print("mediana f5/pc donde single_pixel cambio el valor:", round(st.median(ratios_sp), 3), "n", len(ratios_sp))
print("Villarrica pc.n_pixels>12 (tope max_cluster_pixels=12):")
for x in vill: print("  ", x)
json.dump({"conteos": dict(C), "mediana_f5_sobre_pc": st.median(ratios), "villarrica_tope": vill},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "apilamiento_f5_single_pixel.json"), "w"), indent=1)
