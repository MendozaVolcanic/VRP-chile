"""¿Qué supuesto de la cadena (interpolador, caja de ROI, posición de la grilla) explica las alertas de MIROVA que el
oráculo no ve en los gránulos chilenos? Corre sin red sobre los recortes del run 39641637298.

Pregunta 1: si el supuesto probado fuera el que falta, ¿se vería? Sí: la alerta aparecería con su magnitud cerca de
la de MIROVA. Pregunta 2: un instrumento muerto daría 0 en todas las variantes, también en las tres pasadas que el
oráculo base sí reproduce (Láscar 10-08, Chillán 10-10, Villarrica 09-19), que sirven de control positivo; Llaima
10-10 (RUTINA) y Tupungatito 03-01 (sin alerta de MIROVA) son el control negativo: una variante que los haga alertar
compra recall con falsas alarmas.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import griddata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "oraculo"))
sys.path.insert(0, str(AQUI))
import mirova_v750_r2 as ORA  # noqa: E402
from probe_granulos import caja_mirova, N, CELDA  # noqa: E402

run = AQUI / "run_39641637298"
res = json.loads(Path(glob.glob(str(run / "**" / "resultados.json"), recursive=True)[0]).read_text())
obj = {(o["volcan"], o["hora_utc"]): o for o in json.loads((AQUI / "objetivos.json").read_text(encoding="utf-8"))}


def grilla(g, dx=0.0, dy=0.0):
    xs = g["ul_x"] + dx + CELDA * (np.arange(N) + 0.5)
    ys = g["ul_y"] + dy - CELDA * (np.arange(N) + 0.5)
    return np.meshgrid(xs, ys)


def caja_toda_sensible():
    b = caja_mirova(); b[(b == 1)] = 2; return b


def correr(m13, m15, box, sg):
    mk, _ = ORA.detectar(m13, m15, box, 0, sg)
    if not mk.any():
        return 0, None, []
    r = ORA.vrp(m13, mk)
    rr, cc = np.nonzero(mk)
    return int(mk.sum()), round(r["VRP_MW"], 3), [round(float(np.hypot(a - 33, b - 33) * 0.75), 1) for a, b in zip(rr, cc)]


for r in res:
    if r.get("estado") != "ok":
        continue
    clave = f"{r['volcan']}_{r['hora_utc'].replace(' ', '_').replace(':', '')}"
    z = np.load(run / glob.glob(str(run / "**" / f"recorte_{clave}.npz"), recursive=True)[0].split(str(run) + "\\")[-1]
                if False else glob.glob(str(run / "**" / f"recorte_{clave}.npz"), recursive=True)[0])
    g = obj[(r["volcan"], r["hora_utc"])]["grilla"]
    sg = r["sunglint"]
    mir = [(m["VRP_MW"], m["Distancia_km"]) for m in r["mirova"]]
    print(f"== {r['volcan']} {r['hora_utc']} MIROVA {mir} produccion pc {r['produccion'].get('pc_vrp_mw')}")
    filas = []
    for metodo in ("linear", "nearest", "cubic"):
        for (dx, dy) in ((0, 0), (375, 0), (-375, 0), (0, 375), (0, -375)):
            X, Y = grilla(g, dx, dy)
            ok = np.isfinite(z["m13"]) & np.isfinite(z["m15"])
            pts = np.column_stack([z["x"][ok], z["y"][ok]])
            m13 = griddata(pts, z["m13"][ok], (X, Y), method=metodo)
            m15 = griddata(pts, z["m15"][ok], (X, Y), method=metodo)
            for nombre_caja, box in (("caja_def", caja_mirova()), ("anillo_sensible", caja_toda_sensible())):
                if (dx, dy) != (0, 0) and nombre_caja != "caja_def":
                    continue
                filas.append((metodo, dx, dy, nombre_caja) + correr(m13, m15, box, sg))
    for f in filas:
        print("   ", f)
