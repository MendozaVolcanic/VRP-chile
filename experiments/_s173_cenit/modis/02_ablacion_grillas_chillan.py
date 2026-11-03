# -*- coding: utf-8 -*-
"""02 (S173): ablación por pieza de magnitud (fondo y suma) sobre las grillas que capturó el A/B de MOD-D (fase 4,
S168-S170) para las pasadas MODIS de Chillán con alerta de MIROVA, partida por cenit.

POR QUE: la caída de K con el cenit puede venir del fondo (D25) o de lo que pasa antes, al remuestrear (D17). Las
grillas capturadas son la vía DESPUÉS del remuestreo: con ellas se puede cambiar el fondo y la suma por los de K sin
tocar la detección. Si alguno de esos brazos vuelve a hundir la razón en las pasadas oblicuas, el fondo o la suma son
la palanca; si no, la caída está antes (remuestreo, geolocalización o detector), y eso se mide en 03 sobre recortes
nativos y en el workflow s173-cenit-modis.

Insumos: las grillas grilla_NevadosDeChillan_<YYYYMMDDHHMM>.npz de los artefactos del A/B de MOD-D bajo
D:/vrp-trabajo/temporales/s170_ab*/ (mir, tir, box, pos_crater, mascara, vrp_mw, dayflag, sunglint, grilla), la lista
de 01_salida.json y la lectura modd_resultado_f4.json. Código: pipeline/ de la copia de main que se pasa como raíz.

P1 (si lo medido estuviera roto, ¿se vería?): control V0 = recalcular la vía sobre la grilla capturada tiene que dar la
    misma máscara y el mismo VRP que la captura, y V0 / MIROVA tiene que ser la razon_b de la lectura del A/B; X2 tiene
    que doblar el VRP sin mover ninguna celda. FA tiene que cambiar algo (si no, no es una pieza que actúe).
P2 (instrumento muerto): un brazo que no se aplicara daría V0 exacto; se informa cuántas pasadas cambian por brazo. Un
    brazo sin VRP (cúmulo vacío) cuenta como 0, y se dice cuántas.
Uso: python -B 02_ablacion_grillas_chillan.py <raiz copia main> [<glob de grillas>]
"""
import glob
import json
import math
import os
import random
import statistics
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1]).resolve()
PATRON = sys.argv[2] if len(sys.argv) > 2 else "D:/vrp-trabajo/temporales/s170_ab*/*/grillas/grilla_NevadosDeChillan_*.npz"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import profile as PF  # noqa: E402
import banco_paridad as bp  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


exec(open(AQUI / "_estadistica.py", encoding="utf-8").read())   # spearman, con_barajado, med (mismo código que 01)

VOL = {"lat": -36.863, "lon": -71.377}       # volcanoes.yaml (se comprueba abajo)
pasadas = json.load(open(AQUI / "01_salida.json", encoding="utf-8"))["pasadas"]
md = json.load(open(AQUI / "modd_resultado_f4.json", encoding="utf-8"))["chillan"]
razon_b = {p["dt"]: p["razon_b"] for p in md["pares"]}
razon_b.update({p["dt"]: p["razon"] for p in md["recuperadas"]})

import yaml  # noqa: E402
vy = [v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
      if v["name"] == "NevadosDeChillan"][0]
pr(f"== controles de configuración: volcanoes.yaml lat {vy['lat']} lon {vy['lon']} (usado {VOL}); anillo de K en "
   f"profile.py {PF.BG_INNER_KM}-{PF.BG_OUTER_KM} km (usado {PZ.BG_INNER_KM}-{PZ.BG_OUTER_KM}); "
   f"local_kernel_bg de Chillán: {vy.get('local_kernel_bg', False)}")
assert (vy["lat"], vy["lon"]) == (VOL["lat"], VOL["lon"]) and (PF.BG_INNER_KM, PF.BG_OUTER_KM) == (PZ.BG_INNER_KM,
                                                                                                   PZ.BG_OUTER_KM)
g_ref = MV.grilla_del_volcan("NevadosDeChillan", paso_m=1000.0, clave_roi="roi_modis")

archivos = {}
for f in glob.glob(PATRON):
    archivos.setdefault(Path(f).stem.split("_")[-1], f)
pr(f"   grillas de Chillán encontradas: {len(archivos)} (patrón {PATRON})")

filas = []
for p in pasadas:
    if p["via_codigo_mirova"] is True:
        continue
    clave = p["dt"].replace("-", "").replace(" ", "").replace(":", "")
    f = archivos.get(clave)
    if f is None:
        filas.append({**p, "grilla": None})
        continue
    z = np.load(f)
    g = {"epsg": int(z["epsg"]), "ul_x": float(z["ul_x"]), "ul_y": float(z["ul_y"]), "n": int(z["n"]),
         "paso": float(z["paso"]), "roi": g_ref.get("roi")}
    mir, tir, box, pos = z["mir"], z["tir"], z["box"], tuple(z["pos_crater"])
    dayflag, sg, inner = int(z["dayflag"]), float(z["sunglint"]), float(z["inner_km"])
    sensor = p["sensor"]
    # --- control V0 directo (sin procesar_grilla)
    mask, _ = MV.detectar_mirova(mir, tir, box, dayflag, sg, devolver_diag=True, lam_mir=PZ.LAM,
                                 lam_tir=PZ.FAM["lam_tir"])
    v = MV.vrp_mirova(mir, mask, coef=PZ.COEF)
    fila = {**p, "grilla": f, "grilla_igual_a_la_del_volcan": all(abs(g[k] - g_ref[k]) < 1e-6 for k in ("ul_x", "ul_y"))
            and g["epsg"] == g_ref["epsg"] and g["n"] == g_ref["n"],
            "mascara_igual": bool(np.array_equal(mask, z["mascara"])),
            "vrp_v0_directo": None if not v["npix"] else float(v["VRP_MW"]), "vrp_captura": float(z["vrp_mw"]),
            "razon_b_lectura": razon_b.get(p["dt"]), "npix_v0": int(mask.sum())}
    dist = PZ.dist_celdas_km(g, VOL["lat"], VOL["lon"])
    fila["t_bg_anillo_grilla_k"] = round(PZ.t_bg_anillo(mir, dist), 2)
    br = {}
    for b in PZ.BRAZOS_GRILLA:
        rec = PZ.correr_en_grilla(b, mir, tir, g, box, dayflag, sg, pos, inner, sensor, (VOL["lat"], VOL["lon"]))
        r = PZ.resumen(rec)
        r["_record"] = rec
        br[b] = r
    fila["brazos"] = br
    filas.append(fila)

# ------------------------------------------------------------------ publicación con el predicado del tablero (node)
# mismo armado que experiments/_s151_mxd03_etiquetas/probe_etiquetas.py::publica (l. 187-203 en main de hoy)
inner_html = bp.inner_desde_html()["NevadosDeChillan"]
casos, idx = [], []
for i, fl in enumerate(filas):
    if not fl.get("grilla"):
        continue
    for b, r in fl["brazos"].items():
        rec = dict(r["_record"])
        rec.update({"datetime_utc": fl["dt"], "sensor_zenith_deg": fl["z"]})
        slim = {k: rec.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                  for q in (rec.get("anomaly_pixels") or [])]
        casos.append([slim, inner_html])
        idx.append((i, b))
for (i, b), res in zip(idx, bp.correr_node(casos) if casos else []):
    filas[i]["brazos"][b]["publica"] = int(res[4])
    filas[i]["brazos"][b]["disp"] = float(res[3]) if isinstance(res[3], (int, float)) else None

# ------------------------------------------------------------------ informe
con = [f for f in filas if f.get("grilla")]
pr(f"\n== pasadas K con alerta (01_salida.json, sin las 2 ya escritas por la vía): "
   f"{sum(1 for p in pasadas if p['via_codigo_mirova'] is not True)}; con grilla capturada: {len(con)}; sin grilla: "
   + ", ".join(f["dt"] for f in filas if not f.get("grilla")))
pr("\n== controles del instrumento")
pr(f"  grilla capturada = grilla_del_volcan de main (ul_x, ul_y, epsg, n): {sum(f['grilla_igual_a_la_del_volcan'] for f in con)} de {len(con)}")
pr(f"  V0 directo: máscara igual a la capturada en {sum(f['mascara_igual'] for f in con)} de {len(con)}; "
   f"|VRP V0 - VRP capturado| máx "
   f"{max(abs((f['vrp_v0_directo'] or 0) - f['vrp_captura']) for f in con):.2e} MW")
dv = [abs(round(f['vrp_captura'], 3) - (f['brazos']['V0']['vrp_mw'] or 0)) for f in con]
pr(f"  V0 por procesar_grilla con el patch: |record - captura redondeada| máx {max(dv):.2e} MW")
cmp = [(f["dt"], f["vrp_captura"] / f["vrp_mirova_mw"], f["razon_b_lectura"]) for f in con if f["razon_b_lectura"] is not None]
pr(f"  V0 / MIROVA contra razon_b de la lectura del A/B: {sum(abs(a - b) < 1e-6 for _, a, b in cmp)} de {len(cmp)} "
   f"iguales a 1e-6 (las {len(con) - len(cmp)} restantes no estaban en la lectura)")
x2 = [f for f in con if f["brazos"]["V0"]["npix"]]
pr(f"  X2 (control positivo): VRP = 2 x V0 en {sum(abs((f['brazos']['X2']['vrp_mw'] or 0) - 2 * (f['brazos']['V0']['vrp_mw'] or 0)) <= 0.0015 for f in x2)} "
   f"de {len(x2)}; celdas iguales en {sum(f['brazos']['X2']['celdas'] == f['brazos']['V0']['celdas'] for f in x2)} de {len(x2)}")
for b in PZ.BRAZOS_GRILLA[1:]:
    cambia = sum(abs((f["brazos"][b]["vrp_mw"] or 0) - (f["brazos"]["V0"]["vrp_mw"] or 0)) > 0.0005 for f in con)
    pr(f"  {b}: VRP distinto de V0 en {cambia} de {len(con)}")
pr("  t_bg del anillo en la grilla contra t_bg_k del record K (fidelidad de FA al fondo de K):")
recs = {(r["sensor"], r["datetime_utc"]): r for r in
        json.load(open(RAIZ / "data/mirova_equivalent/NevadosDeChillan.json", encoding="utf-8"))["records"]}
dif = []
for f in con:
    tk = (recs.get((f["sensor"], f["dt"])) or {}).get("t_bg_k")
    if tk is not None:
        dif.append(f["t_bg_anillo_grilla_k"] - tk)
pr(f"    n {len(dif)}; diferencia (grilla - K) mediana {statistics.median(dif):+.2f} K, rango [{min(dif):+.2f}; {max(dif):+.2f}] K")

pr("\n== por pasada (VRP en MW; razón = VRP / MIROVA; K = disp publicado por K; P = publica en el tablero)")
cab = f"  {'dt':16s} {'z':>5s} {'M':>7s} {'K':>7s} " + " ".join(f"{b:>13s}" for b in PZ.BRAZOS_GRILLA) + "  npixV0"
pr(cab)
for f in sorted(con, key=lambda x: x["z"]):
    cols = []
    for b in PZ.BRAZOS_GRILLA:
        r = f["brazos"][b]
        v = r["vrp_mw"] or 0.0
        cols.append(f"{v:6.2f}({v / f['vrp_mirova_mw']:4.2f}){'P' if r.get('publica') else '-'}")
    pr(f"  {f['dt']:16s} {f['z']:5.1f} {f['vrp_mirova_mw']:7.2f} {f['disp_mw']:7.2f} " + " ".join(cols)
       + f"  {f['npix_v0']}")

pr("\n== razón contra MIROVA por brazo: Spearman con el cenit (200 barajados, semilla 173) y tramos")
resumen = {}
zz = [f["z"] for f in con]
for b in ("K",) + PZ.BRAZOS_GRILLA:
    if b == "K":
        rr = [(f["disp_mw"] if f["pub_K"] else 0.0) / f["vrp_mirova_mw"] for f in con]
    else:
        rr = [(f["brazos"][b]["vrp_mw"] or 0.0) / f["vrp_mirova_mw"] for f in con]
    rho, lo, hi = con_barajado(zz, rr)
    a = [r for r, z in zip(rr, zz) if z < 30]
    c = [r for r, z in zip(rr, zz) if z >= 30]
    pubs = sum((f["pub_K"] if b == "K" else f["brazos"][b].get("publica", 0)) for f in con)
    resumen[b] = {"spearman": rho, "barajado": [lo, hi], "z<30": {"n": len(a), "mediana": med(a)},
                  "z>=30": {"n": len(c), "mediana": med(c)}, "publica": pubs, "n": len(con)}
    pr(f"  {b:6s} Spearman {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]  z<30 n {len(a)} mediana {med(a)}  z>=30 n {len(c)} "
       f"mediana {med(c)}  publica {pubs} de {len(con)}")
rn = [f["npix_v0"] for f in con]
rho, lo, hi = con_barajado(zz, [float(x) for x in rn])
pr(f"\n== conteo de celdas alertadas por la vía (V0) contra el cenit: Spearman {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]; "
   f"z<30 mediana {med([n for n, z in zip(rn, zz) if z < 30])}, z>=30 mediana {med([n for n, z in zip(rn, zz) if z >= 30])}")
resumen["npix_v0_vs_cenit"] = {"spearman": rho, "barajado": [lo, hi]}

for f in filas:
    for r in (f.get("brazos") or {}).values():
        r.pop("_record", None)
json.dump({"filas": filas, "resumen": resumen}, open(AQUI / "02_salida.json", "w", encoding="utf-8"), indent=1,
          ensure_ascii=False, default=str)
(AQUI / "02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
