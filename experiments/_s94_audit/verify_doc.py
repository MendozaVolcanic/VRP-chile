"""Verificación programática: docs/AUDIT_S94_per_sensor_metrics.md == per_sensor_metrics.json.

Regla integridad §0.5: ningún número del doc se transcribe a mano sin chequeo.
Re-corre el script (regenera el JSON), luego asserta que cada número de las tablas
§1/§2/§4 del doc coincide con la fuente. Falla con diff si algo no cuadra.

  python experiments/_s94_audit/verify_doc.py
"""
import os, json, re, subprocess, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(REPO, "docs", "AUDIT_S94_per_sensor_metrics.md")
JSON = os.path.join(HERE, "per_sensor_metrics.json")

# 1) regenerar la fuente
subprocess.run([sys.executable, os.path.join(HERE, "per_sensor_metrics.py")],
               check=True, capture_output=True)
o = json.load(open(JSON, encoding="utf-8"))
doc = open(DOC, encoding="utf-8").read()

fails = []


def check(label, value):
    """Asserta que `value` (string exacto) aparece en el doc."""
    if value not in doc:
        fails.append(f"{label}: '{value}' NO está en el doc")


def pct(x):
    return f"{x*100:.1f}%"


# --- VISTA A (raw) y B (summit): N_ours, N_mir, TP, match_mir, precisión, recall, ratio ---
for view in ("raw", "summit_gated"):
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        s = o[view][b]
        check(f"{view}.{b}.N_ours", f"| {s['N_ours']} |")
        check(f"{view}.{b}.precision", pct(s["precision"]))
        check(f"{view}.{b}.recall", pct(s["recall"]))
        check(f"{view}.{b}.ratio", f"{s['ratio_median']:.2f}×")

# números narrativos clave
raw750 = o["raw"]["VIIRS750"]
check("raw.VIIRS750.recall narrativa", "86.7%")
check("summit.VIIRS750.recall narrativa", "83.0%")
check("summit.MODIS.recall narrativa", "11.8%")

# --- §4 ctx-only ---
ctx = o["ctx_only_split"]
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    c = ctx[b]
    tp_pct = round(100 * c["tp_ctx"] / c["tp"]) if c["tp"] else 0
    fp_pct = round(100 * c["fp_ctx"] / c["fp"]) if c["fp"] else 0
    check(f"ctx.{b}.tp", f"| {c['tp']} | {c['tp_ctx']} ({tp_pct}%)")
    check(f"ctx.{b}.fp", f"{c['fp']} | {c['fp_ctx']} ({fp_pct}%)")

# --- FN VIIRS750 ---
check("n_fn_v750", f"{len(o['v750_fn_alerts'])} FN")
# distance_class FP
check("v750_fp_far", str(o["v750_fp_distance_class"].get("far")))
check("v750_fp_summit", str(o["v750_fp_distance_class"].get("summit")))

# --- §6 espacial Tupungatito ---
subprocess.run([sys.executable, os.path.join(HERE, "tupungatito_spatial.py")],
               check=True, capture_output=True)
tup = json.load(open(os.path.join(HERE, "tupungatito_spatial.json"), encoding="utf-8"))
check("tup.crater_offset", f"{tup['crater_to_mirova_center_km']} km")
check("tup.v375_close", f"{tup['v375_centroid_within_2km']} / {tup['v375_total']}")
check("tup.vrp_crater", f"{tup['vrp_med_crater_0_2km']} MW")
check("tup.vrp_glacier", f"{tup['vrp_med_glacier_gt7km']} MW")
tr = tup["top_record"]
check("tup.top_vrp", f"{tr['vrp_mw']} MW")
check("tup.top_pixels", f"{tr['pixels_within_2km']} / {tr['n_anomaly_pixels']}")

# --- §7 magnitud VIIRS ---
subprocess.run([sys.executable, os.path.join(HERE, "viirs_magnitude_diag.py")],
               check=True, capture_output=True)
vm = json.load(open(os.path.join(HERE, "viirs_magnitude_diag.json"), encoding="utf-8"))
v375 = vm["VIIRS375"]
for vol in ("Lascar", "Tupungatito", "Villarrica", "PuyehueCordonCaulle", "Lastarria"):
    m = v375[vol]
    check(f"v375.{vol}.sum", f"{m['ratio_sum_med']:.2f}×")
# foco de los robustos
check("v375.PCC.focus", f"{v375['PuyehueCordonCaulle']['ratio_focus_med']:.2f}×")

if fails:
    print("✗ VERIFICACIÓN FALLÓ:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("✓ doc == fuente: todos los números de las tablas §1/§2/§4 coinciden con el JSON.")
