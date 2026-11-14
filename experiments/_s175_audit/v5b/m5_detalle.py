# -*- coding: utf-8 -*-
"""m5 (V5B): detalle de la pasada V375 de 351, publicacion con el predicado real, tabla de MIROVA y tasas condicionales.

Por que: (a) 2026-10-18 05:06 es la unica de las cuatro de 351 sin mancha grande borrada; hay que ver si elige un empate.
(b) «publicamos» se comprueba ejecutando el predicado del tablero (frontend/index.html de 752d348bc con node, _JS de
scripts/banco_paridad.py, regla A97). (c) «protegida» se comprueba en la fila de la tabla de la base. (d) las tasas de
m2 se separan segun si el maximo del TIF reproduce la tabla (la vara de F5).
Pregunta 1: si el predicado estuviera roto, un caso sintetico no publicable saldria publicado (control incluido).
Pregunta 2: si node fallara, el script cae con error. Ventana: las 4 pasadas de 351; denominador explicito en cada linea.
"""
import csv, json, math, os, re, subprocess, sys, tempfile
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "f5b"))
import f5b_lib as L
import yaml
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
refs = json.load(open(os.path.join(HERE, "..", "f5b", "p6_tif_referencia_out.json"), encoding="utf-8"))
p8 = [x for x in json.load(open(os.path.join(HERE, "..", "f5b", "p8_clases.json"), encoding="utf-8")) if x.get("vol") == "NevadosDeChillan"]

print("== (a) 2026-10-18 05:06 V375: componentes blancas en el inner ==")
x = [r for r in p8 if r["b"] == "VIIRS375" and r["dt"] == "2026-10-18 05:06"][0]
g = L.grilla(os.path.join(TMP, "tif_ref", "ChillanNevadosde_" + os.path.basename(refs["ChillanNevadosde|VIIRS375"]["ref_sep"]["path"])))
mc = (V["NevadosDeChillan"]["mirova_center_lat"], V["NevadosDeChillan"]["mirova_center_lon"])
inner = L.mascara_inner(g, mc, 5)
im = L.abrir_png(os.path.join(TMP, "png", x["png"].split("/")[-2] + "_" + os.path.basename(x["png"])))
bb = L.bbox_marco(im, x["panel"])
X0, Y0, W, Hh = L.geometria(bb)
pan, px_x, px_y = L.recorte(im, X0, Y0, W, Hh)
cy, cx = L.celdas_de(px_x, px_y, X0, Y0, W, Hh, g["n"])
bl = pan.min(axis=2) > 245
lab, nl = ndimage.label(bl, structure=np.ones((3, 3)))
la, lo = float(x["our_lat"]), float(x["our_lon"])
for i in range(1, nl + 1):
    m = lab == i
    if not (m & inner[np.ix_(cy, cx)]).any():
        continue
    yy, xx = np.where(m)
    cel = sorted(set(zip(cy[yy].tolist(), cx[xx].tolist())))
    print("  comp", i, "px", int(m.sum()), "celdas", cel, "lum max", float(pan[m].mean(axis=1).max()), "d_mc km", [round(L.hav(g["lats"][r, c], g["lons"][r, c], *mc), 2) for r, c in cel], "d_nuestro km", [round(L.hav(g["lats"][r, c], g["lons"][r, c], la, lo), 2) for r, c in cel])
print("  celda de mirova_center (67,66); nuestro punto en", np.unravel_index(np.argmin((g["lats"] - la) ** 2 + ((g["lons"] - lo) * 0.8) ** 2), g["lats"].shape))
print("  Luminancia alrededor del centro (filas 62..71, cols 60..71, media por celda):")
L_ = pan.astype(float).mean(axis=2)
grid = np.full((g["n"], g["n"]), np.nan)
sumas = np.zeros((g["n"], g["n"])); cuentas = np.zeros((g["n"], g["n"]))
for i_, r in enumerate(cy):
    for j_, c in enumerate(cx):
        sumas[r, c] += L_[i_, j_]; cuentas[r, c] += 1
grid = np.divide(sumas, cuentas, out=np.full_like(sumas, np.nan), where=cuentas > 0)
print("     col " + " ".join(f"{c:4d}" for c in range(60, 72)))
for r in range(62, 72):
    print(f"  r{r:3d}  " + " ".join(f"{grid[r, c]:4.0f}" for c in range(60, 72)))

print("\n== (b) Predicado del tablero con node sobre frontend/index.html de la base ==")
banco = subprocess.run(["git", "-C", REPO, "show", f"{BASE}:scripts/banco_paridad.py"], capture_output=True, text=True, encoding="utf-8").stdout
_JS = re.search(r'_JS = r"""\n(.*?)\n"""', banco, re.S).group(1)
CAMPOS = re.search(r"CAMPOS_JS = \[(.*?)\]", banco, re.S).group(1)
CAMPOS = re.findall(r'"(\w+)"', CAMPOS)
print("  campos JS:", CAMPOS)
tmp = r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\base_front"
os.makedirs(tmp, exist_ok=True)
for fn in ("frontend/index.html", "frontend/cambio_detector.js"):
    with open(os.path.join(tmp, os.path.basename(fn)), "wb") as f:
        f.write(subprocess.run(["git", "-C", REPO, "show", f"{BASE}:{fn}"], capture_output=True).stdout)
open(os.path.join(tmp, "r.js"), "w", encoding="utf-8").write(_JS)
d = json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\chillan_base.json", encoding="utf-8"))
w = [("VIIRS_NOAA21", "2026-10-18 05:06"), ("VIIRS_NOAA21_750", "2026-10-29 06:42"), ("VIIRS_NOAA20_750", "2026-10-10 06:54"), ("VIIRS_NOAA20_750", "2026-10-16 06:42")]
casos = []
rec = []
for s, t in w:
    r = [r for r in d["records"] if r["sensor"] == s and r["datetime_utc"] == t][0]
    slim = {k: r.get(k) for k in CAMPOS if k != "anomaly_pixels"}
    if r.get("f5_core_vrp_mw") is None:
        slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
    casos.append([slim, 5.0])
    rec.append(r)
casos.append([{"vrp_mw": 5.0, "distance_class": "far", "t_max_k": 290, "sensor": "MODIS_AQUA", "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}, 5.0])  # control no publicable (guard S139)
json.dump(casos, open(os.path.join(tmp, "c.json"), "w", encoding="utf-8"))
o = subprocess.run(["node", os.path.join(tmp, "r.js"), os.path.join(tmp, "index.html"), os.path.join(tmp, "c.json")], capture_output=True, text=True, encoding="utf-8")
print("  rc", o.returncode, "stderr", o.stderr[:300])
res = json.loads(o.stdout)
for (s, t), p, r in zip(w + [("control_far", "")], res, rec + [None]):
    print("  ", s, t, "[summit, valid, art, disp, publica] =", p, "final_hotspot", (r or {}).get("final_hotspot_lat"), (r or {}).get("final_hotspot_lon"), "fuente", (r or {}).get("final_hotspot_source"))
print("  El control far debe dar publica=0:", res[-1][4] == 0)

print("\n== (c) Filas de la tabla de MIROVA (snapshot_consolidado_base.csv) para las 4 pasadas ==")
tabla = list(csv.DictReader(open(r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_consolidado_base.csv", encoding="utf-8")))
for s, t, hhmm in [("VIIRS375", "VIIRS375", "2026-10-18 05:06"), ("VIIRS750", "VIIRS750", "2026-10-29 06:42"), ("VIIRS750", "VIIRS750", "2026-10-10 06:54"), ("VIIRS750", "VIIRS750", "2026-10-16 06:42")]:
    fil = [r for r in tabla if r["Volcan"].lower().startswith("nevados") and r["Sensor"] == s and r["Fecha_Satelite_UTC"][:16] == hhmm]
    print(" ", s, hhmm, [(r["Fecha_Satelite_UTC"], r["VRP_MW"], r["Distancia_km"], r["Tipo_Registro"], r["Clasificacion Mirova"]) for r in fil])

print("\n== (d) m2: tasas condicionadas a que el maximo del TIF reproduzca la tabla ==")
m2 = [o for o in json.load(open(os.path.join(HERE, "m2_validacion.json"), encoding="utf-8")) if o.get("ocr_ok") and "d_A_km" in o]
for et in ("nuevo",):
    for b in ("VIIRS375", "VIIRS750"):
        for repro in (True, False):
            g_ = [o for o in m2 if o["etiqueta"] == et and o["b"] == b and o.get("tif_reproduce_tabla") is repro]
            if g_:
                print(f"  {et} {b} TIF reproduce tabla={repro}: n={len(g_)}; A<=tol {sum(o['d_A_km'] <= o['tol'] for o in g_)}; A<=1 celda {sum(o['d_A_km'] <= o['celda_km'] + 1e-6 for o in g_)}; p50 {np.median([o['d_A_km'] for o in g_]):.2f} km; corr p50 {np.median([o['corr_panel_tif'] for o in g_]):.3f}")
print("  Por volcan en nuevos con TIF que reproduce:", {(o["vol"], o["b"]): 1 for o in m2 if o["etiqueta"] == "nuevo" and o.get("tif_reproduce_tabla")} and sorted({(o["vol"], o["b"]) for o in m2 if o["etiqueta"] == "nuevo" and o.get("tif_reproduce_tabla")}))
