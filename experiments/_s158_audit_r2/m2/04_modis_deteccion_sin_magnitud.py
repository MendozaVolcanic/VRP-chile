"""M2 (S158 r2): MODIS, detección con magnitud cero y origen del fondo del VRP.

Fenómeno: el pipeline resta al píxel caliente un fondo que, salvo en los 5 volcanes con
`local_kernel_bg: true`, es la MEDIANA de temperatura del anillo de 5 a 25 km convertida a radiancia
(process_modis.py:1083), y recorta el exceso a cero (:1118). En un volcán nevado el cráter puede
estar más frío que la mediana de un anillo que incluye valles: el detector dice "anómalo" (contraste
local NTI) y la magnitud dice 0. Un cúmulo con vrp_mw = 0 no es detección válida para el tablero
(isValidDetection), así que la detección desaparece.

Pregunta 1: si el recorte estuviera borrando detecciones, aparecen records MODIS con
n_anomalous_pixels > 0 y pc.vrp_mw == 0 (o sin pc). Pregunta 2: control: el mismo conteo en VIIRS
375 (fondo distinto) y la lista de volcanes con kernel local (donde el fenómeno debe ser menor).

Ventana: todo el corpus; también por tramo (antes y después de la observación del 2026-09-18, K).
"""
import glob, json, os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
import yaml
vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml")))["volcanoes"]}
print("volcanes con local_kernel_bg:", [n for n, v in vols.items() if v.get("local_kernel_bg")])

def grupo(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"

tot = Counter(); det = Counter(); det_pc0 = Counter(); det_nopc = Counter(); det_pc0_summit = Counter()
lbg_local = Counter(); ejemplos = []
for f in sorted(glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json"))):
    name = os.path.basename(f)[:-5]
    v = vols[name]; inner = v.get("inner_radius_km")
    if not inner: continue
    for r in json.load(open(f))["records"]:
        g = grupo(r["sensor"]); tramo = "K" if r["datetime_utc"] >= "2026-09-18" else "pre"
        k = (g, tramo)
        tot[k] += 1
        if (r.get("n_anomalous_pixels") or 0) > 0:
            det[k] += 1
            pc = r.get("primary_cluster")
            if pc is None:
                det_nopc[k] += 1
            elif (pc.get("vrp_mw") or 0) == 0:
                det_pc0[k] += 1
                if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inner:
                    det_pc0_summit[(g, tramo, name)] += 1
                    if g == "MODIS" and len(ejemplos) < 8:
                        ejemplos.append((name, r["datetime_utc"], r["sensor"], r.get("t_max_k"), r.get("t_bg_k"), pc.get("n_pixels"), r.get("vrp_mw"), r.get("diag_L_bg_local_w_m2_sr_um")))
            if g == "MODIS" and r.get("diag_L_bg_local_w_m2_sr_um") is not None:
                lbg_local[(name, tramo)] += 1

for k in sorted(tot):
    print(f"{k}: records {tot[k]:6d} | con pixeles anomalos {det[k]:6d} | de ellos pc.vrp_mw==0: {det_pc0[k]:5d} | sin pc: {det_nopc[k]:4d}")
print("\npc.vrp_mw == 0 CON cumulo dentro del inner (deteccion del crater que el tablero no ve), por (sensor, tramo, volcan):")
for k in sorted(det_pc0_summit): print("  ", k, det_pc0_summit[k])
print("\nMODIS con fondo local del kernel (diag_L_bg_local presente), por (volcan, tramo):", dict(lbg_local))
print("\nejemplos MODIS (volcan, dt, sensor, t_max, t_bg, n_px, vrp_mw, L_bg_local):")
for e in ejemplos: print("  ", e)
