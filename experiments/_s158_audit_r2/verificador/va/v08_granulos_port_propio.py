# -*- coding: utf-8 -*-
"""VA, hallazgo 10: port propio (va_port.py, escrito desde el .m) sobre los recortes .npz de los granulos chilenos.

Camino propio: (1) reproyecto lat/lon a UTM con pyproj y comparo con x, y guardados (control de georreferencia);
(2) remuestreo M13 y M15 con scipy griddata 'linear' a la grilla de objetivos.json (ul_x, ul_y, 67 x 67, 750 m);
(3) deteccion y VRP con mi port; (4) comparo con MIROVA NRT y con la produccion guardada en resultados.json.
BOX: dos supuestos, 21 x 21 centrado (el del probe) y el bloque 21 x 19 de la matriz de Etna (filas 22-42,
columnas 24-42), los dos con el 7 x 7 central como cumbre.
Pregunta 1: si el port o el remuestreo estuvieran rotos, Chillan 2026-10-10 (13 MW) no apareceria (control
positivo); Llaima 2026-10-10 (RUTINA) y Tupungatito 2026-03-01 (sin alerta) son control negativo.
Pregunta 2: un instrumento muerto daria 0 pixeles en todas; se imprime Npix por pasada.
Fondo: Qhull sin perturbar y el rango sobre 30 triangulaciones perturbadas (hallazgo 9).
"""
import glob, json, sys
from pathlib import Path
import numpy as np
from pyproj import Transformer
from scipy.interpolate import griddata

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import va_port as P  # noqa: E402

G = AQUI.parent.parent / "granulos"
RUN = G / "run_39641637298" / "s158-r2-granulos"
res = json.loads((RUN / "resultados.json").read_text())
obj = {(o["volcan"], o["hora_utc"]): o for o in json.loads((G / "objetivos.json").read_text(encoding="utf-8"))}
N, CEL = 67, 750.0


def box(tipo):
    b = np.zeros((N, N))
    if tipo == "21x21":
        b[23:44, 23:44] = 1
    else:  # bloque de Etna
        b[22:43, 24:43] = 1
    b[30:37, 30:37] = 2
    return b


rng = np.random.default_rng(7)
for r in res:
    if r.get("estado") != "ok":
        continue
    clave = f"{r['volcan']}_{r['hora_utc'].replace(' ', '_').replace(':', '')}"
    z = np.load(RUN / f"recorte_{clave}.npz")
    g = obj[(r["volcan"], r["hora_utc"])]["grilla"]
    tr = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    xx, yy = tr.transform(z["lon"], z["lat"])
    dgeo = float(np.nanmax(np.hypot(xx - z["x"], yy - z["y"])))
    xs = g["ul_x"] + CEL * (np.arange(N) + 0.5)
    ys = g["ul_y"] - CEL * (np.arange(N) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    ok = np.isfinite(z["m13"]) & np.isfinite(z["m15"])
    pts = np.c_[xx[ok], yy[ok]]
    m13 = griddata(pts, z["m13"][ok], (X, Y), method="linear")
    m15 = griddata(pts, z["m15"][ok], (X, Y), method="linear")
    dif_grilla = float(np.nanmax(np.abs(m13 - z["grilla_linear_M13"])))
    mir = [(m["Tipo_Registro"], m["VRP_MW"], m["Distancia_km"]) for m in r["mirova"]]
    prod = r["produccion"].get("pc_vrp_mw")
    linea = f"{r['volcan']:20s} {r['hora_utc']} dayflag={r.get('dayflag')} MIROVA={mir} produccion_pc={prod} | geo_max_dif={dgeo:.2f} m, grilla_vs_probe={dif_grilla:.2e}"
    print(linea)
    for tb in ("21x21", "etna21x19"):
        al = P.deteccion(m13, m15, box(tb))
        if al.size == 0:
            print(f"     BOX {tb:9s}: Npix=0")
            continue
        hot = m13.ravel(order="F")[al].sum()
        bk = P.fondo(m13, al).ravel(order="F")[al].sum()
        vrp = (hot - bk) * 1.97e7 * 0.5625 / 1e6
        vs = []
        for _ in range(30):
            try:
                b2 = P.fondo(m13, al, jitter=1e-3, rng=rng).ravel(order="F")[al].sum()
                vs.append((hot - b2) * 1.97e7 * 0.5625 / 1e6)
            except Exception:
                pass
        rr, cc = np.unravel_index(np.unique(al), m13.shape, order="F")
        dist = np.round(np.hypot(rr - 33, cc - 33) * 0.75, 1)
        ref = [m[1] for m in mir if m[0].startswith("ALERTA")]
        razon = f"{vrp / ref[0]:.3f}" if ref and ref[0] else "-"
        print(f"     BOX {tb:9s}: Npix={al.size} VRP={vrp:.3f} MW (triang. {min(vs):.3f} a {max(vs):.3f}) razon/MIROVA={razon} dist_celdas_km={list(dist)}")
