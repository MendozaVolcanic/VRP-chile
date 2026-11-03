# -*- coding: utf-8 -*-
"""02b (S173): el fenómeno detrás de FA, en temperaturas. Por pasada de Chillán con grilla capturada: temperatura de
brillo MIR de la celda más caliente, del fondo local de la vía bajo las celdas alertadas (fillmissing2 con halo) y del
anillo de K (mediana de 5 a 25 km), contra el cenit.

POR QUE: FA (02) hunde la razón en las pasadas oblicuas. La lectura física candidata: el domo está en una cumbre fría,
el anillo de 5 a 25 km toma valles más tibios, y cuando el píxel oblicuo diluye el calor del foco, las celdas alertadas
quedan por debajo de la mediana del anillo; el recorte a cero las borra. Si eso es lo que pasa, (T_celda - T_anillo)
tiene que caer con el cenit y quedar bajo cero, mientras (T_celda - T_fondo_local) sigue positivo.
P1: el exceso local promedio tiene que ser positivo en todas las pasadas (son alertas de la vía: si no, el cálculo
    está roto). P2: si el anillo no fuera distinto del fondo local, las dos columnas darían lo mismo.
Uso: python -B 02b_temperaturas_grilla.py <raiz copia main> [<glob de grillas>]
"""
import glob
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1]).resolve()
PATRON = sys.argv[2] if len(sys.argv) > 2 else "D:/vrp-trabajo/temporales/s170_ab*/*/grillas/grilla_NevadosDeChillan_*.npz"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

exec(open(AQUI / "_estadistica.py", encoding="utf-8").read())
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def bt(x):
    return float(MV.radiancia_a_temperatura(np.array([x], float), PZ.LAM)[0])


pas = [p for p in json.load(open(AQUI / "01_salida.json", encoding="utf-8"))["pasadas"] if p["via_codigo_mirova"] is not True]
arch = {Path(f).stem.split("_")[-1]: f for f in glob.glob(PATRON)}
filas = []
for p in pas:
    f = arch.get(p["dt"].replace("-", "").replace(" ", "").replace(":", ""))
    if not f:
        continue
    z = np.load(f)
    g = {"epsg": int(z["epsg"]), "ul_x": float(z["ul_x"]), "ul_y": float(z["ul_y"]), "n": int(z["n"]), "paso": float(z["paso"])}
    m, mask = z["mir"], z["mascara"]
    fondo = PZ.fondo_via(m, mask, halo=True)
    dist = PZ.dist_celdas_km(g, -36.863, -71.377)
    t_ring = PZ.t_bg_anillo(m, dist)
    L_ring = float(MV.temperatura_a_radiancia(np.array([t_ring]), PZ.LAM)[0])
    th = [bt(x) for x in m[mask]]
    tl = [bt(x) for x in fondo[mask]]
    sobre_anillo = int(np.sum(m[mask] > L_ring))
    filas.append({"dt": p["dt"], "z": p["z"], "npix": int(mask.sum()), "T_max": max(th), "T_media_alertadas": float(np.mean(th)),
                  "T_fondo_local": float(np.mean(tl)), "T_anillo": t_ring, "alertadas_sobre_anillo": sobre_anillo,
                  "exceso_local_K": float(np.mean(th) - np.mean(tl)), "exceso_anillo_K": float(np.mean(th) - t_ring),
                  "anillo_menos_local_K": float(t_ring - np.mean(tl))})
pr("== Chillán, pasadas K con alerta y grilla capturada: temperaturas de brillo MIR (B22) en la grilla de la vía")
pr(f"  {'dt':16s} {'z':>5s} {'npix':>4s} {'Tmax':>7s} {'Tmed_al':>7s} {'Tfondo':>7s} {'Tanillo':>7s} "
   f"{'ex_loc':>6s} {'ex_anil':>7s} {'anil-loc':>8s} sobre_anillo")
for f in sorted(filas, key=lambda x: x["z"]):
    pr(f"  {f['dt']:16s} {f['z']:5.1f} {f['npix']:4d} {f['T_max']:7.2f} {f['T_media_alertadas']:7.2f} "
       f"{f['T_fondo_local']:7.2f} {f['T_anillo']:7.2f} {f['exceso_local_K']:6.2f} {f['exceso_anillo_K']:7.2f} "
       f"{f['anillo_menos_local_K']:8.2f} {f['alertadas_sobre_anillo']}/{f['npix']}")
zz = [f["z"] for f in filas]
for k in ("T_max", "exceso_local_K", "exceso_anillo_K", "anillo_menos_local_K"):
    rho, lo, hi = con_barajado(zz, [f[k] for f in filas])
    a = [f[k] for f in filas if f["z"] < 30]
    c = [f[k] for f in filas if f["z"] >= 30]
    pr(f"  {k:22s} Spearman con el cenit {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]  z<30 mediana {med(a)}  z>=30 mediana {med(c)}")
pr(f"  control P1: exceso local > 0 en {sum(f['exceso_local_K'] > 0 for f in filas)} de {len(filas)}")
json.dump(filas, open(AQUI / "02b_salida.json", "w", encoding="utf-8"), indent=1)
(AQUI / "02b_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
