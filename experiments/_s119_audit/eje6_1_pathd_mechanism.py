# S119 audit Eje 6.1 — mecanismo pathd_off: por qué difiere VRP con n_anomalous_pixels identico
# Compara brazos _c2ab_baseline (gate path-D intra-radio ON) vs _c2ab_pathd_off (OFF)
# sobre los artifacts locales de experiments/_s118_c2ab/_artifacts/.
# Hipotesis original (parent): pixeles path-D re-entrantes cambian mu/sigma del second-run.
# Hipotesis alternativa (code-trace): dnti_ctx_hot NO participa del hot_mask final
# (first-pass ON lo reemplaza, process_modis.py:736) pero SI es la mascara de
# cluster_focal_vrp_mw (process_modis.py:986 y :1235, vrp_regimes.py:214) -> el gate
# cambia SOLO la magnitud focal del cluster, no la deteccion.
import sys, io, json, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "experiments", "_s118_c2ab", "_artifacts")
OUT = os.path.join(os.path.dirname(__file__), "eje6_1_pathd_mechanism.json")

VOLS = ["Lascar", "NevadosDeChillan"]
ARMS = ["_c2ab_baseline", "_c2ab_pathd_off"]


def load_arm(arm, vol):
    recs = {}
    for d in sorted(glob.glob(os.path.join(ART, f"s118c2ab-{arm}-{vol}-*"))):
        p = os.path.join(d, f"{vol}.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        for r in data.get("records", data if isinstance(data, list) else []):
            key = (r.get("datetime_utc"), r.get("sensor"))
            recs[key] = r
    return recs


def pcv(r):
    pc = r.get("primary_cluster") or {}
    return pc.get("vrp_mw")


def scalar_diff(a, b):
    """Diff campo a campo de valores escalares top-level + primary_cluster."""
    out = {}
    keys = sorted(set(a.keys()) | set(b.keys()))
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if k in ("anomaly_pixels", "discarded_anomaly_pixels"):
            va = f"len={len(va)}" if isinstance(va, list) else va
            vb = f"len={len(vb)}" if isinstance(vb, list) else vb
        if isinstance(va, dict) or isinstance(vb, dict):
            sub_keys = sorted(set((va or {}).keys()) | set((vb or {}).keys()))
            for sk in sub_keys:
                sa = (va or {}).get(sk)
                sb = (vb or {}).get(sk)
                if sa != sb:
                    out[f"{k}.{sk}"] = {"baseline": sa, "pathd_off": sb}
            continue
        if va != vb:
            out[k] = {"baseline": va, "pathd_off": vb}
    return out


result = {"vols": {}, "example_diff": None}
for vol in VOLS:
    base = load_arm("_c2ab_baseline", vol)
    off = load_arm("_c2ab_pathd_off", vol)
    common = sorted(set(base) & set(off))
    differs = []
    for key in common:
        rb, ro = base[key], off[key]
        if rb.get("product_version") != ro.get("product_version"):
            continue  # ruido NRT vs standard, no comparable
        same_npix = rb.get("n_anomalous_pixels") == ro.get("n_anomalous_pixels")
        vb, vo = pcv(rb), pcv(ro)
        vrp_differs = (vb != vo) or (rb.get("vrp_mw") != ro.get("vrp_mw"))
        if vrp_differs:
            pcb = rb.get("primary_cluster") or {}
            pco = ro.get("primary_cluster") or {}
            differs.append({
                "datetime_utc": key[0], "sensor": key[1],
                "same_n_anomalous_pixels": same_npix,
                "n_anomalous_pixels": rb.get("n_anomalous_pixels"),
                "vrp_mw": {"baseline": rb.get("vrp_mw"), "pathd_off": ro.get("vrp_mw")},
                "pc_vrp_mw": {"baseline": vb, "pathd_off": vo},
                "pc_n_pixels": {"baseline": pcb.get("n_pixels"), "pathd_off": pco.get("n_pixels")},
                "pc_focal_magnitude": {"baseline": pcb.get("focal_magnitude"), "pathd_off": pco.get("focal_magnitude")},
                "pc_focal_degraded": {"baseline": pcb.get("focal_degraded"), "pathd_off": pco.get("focal_degraded")},
                "pc_centroid_dist_km": {"baseline": pcb.get("centroid_dist_km"), "pathd_off": pco.get("centroid_dist_km")},
            })
    result["vols"][vol] = {
        "n_common": len(common),
        "n_vrp_differs": len(differs),
        "n_vrp_differs_same_npix": sum(1 for d in differs if d["same_n_anomalous_pixels"]),
        "sensors": sorted({d["sensor"] for d in differs}),
        "differs": differs,
    }

# Diff campo a campo del primer record MODIS de Lascar que difiere con npix identico
for d in result["vols"]["Lascar"]["differs"]:
    if d["same_n_anomalous_pixels"]:
        key = (d["datetime_utc"], d["sensor"])
        base = load_arm("_c2ab_baseline", "Lascar")
        off = load_arm("_c2ab_pathd_off", "Lascar")
        result["example_diff"] = {
            "record": {"datetime_utc": key[0], "sensor": key[1]},
            "fields_differing": scalar_diff(base[key], off[key]),
        }
        break

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

for vol, v in result["vols"].items():
    print(f"{vol}: common={v['n_common']} vrp_differs={v['n_vrp_differs']} "
          f"(same_npix={v['n_vrp_differs_same_npix']}) sensors={v['sensors']}")
if result["example_diff"]:
    print("\nEjemplo (Lascar):", result["example_diff"]["record"])
    for k, v in result["example_diff"]["fields_differing"].items():
        print(f"  {k}: base={v['baseline']}  off={v['pathd_off']}")
print(f"\nOK -> {OUT}")
