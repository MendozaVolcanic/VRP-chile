# -*- coding: utf-8 -*-
"""S162 MOD-E real: piezas comunes de la ablacion del bow tie sobre los recortes nativos del lote 40120713181.

POR QUE. MODIS barre con 10 detectores por barrido; lejos del nadir la huella de cada detector se estira a lo largo de
la traza y los barridos vecinos se pisan (bow tie): el mismo suelo sale en los ultimos detectores de un barrido y en
los primeros del siguiente. MIROVA quita esos duplicados antes de remuestrear (D28); el port remuestrea con todos.
Aqui se rearma la grilla del port desde el recorte nativo (control: tiene que dar lo mismo que el lote), se definen
metodos de quitar duplicados y se mide, ANTES de leer ningun resultado, que fraccion del suelo queda vista 0, 1 y 2
veces con cada uno (A110: un metodo que abre huecos no sirve para concluir).

Geometria. Cada pixel nativo se proyecta a la UTM de la grilla de la pasada. Para cada columna (frame) se estima la
direccion a lo largo de la traza como el promedio, sobre pares de barridos completos, del vector entre los centroides
de dos barridos consecutivos en ese frame; u = proyeccion de la posicion sobre esa direccion (crece con el barrido).
La huella nominal de un pixel es el paralelogramo centro +/- a/2 +/- b/2, con a = paso entre detectores vecinos del
mismo barrido y frame (a lo largo) y b = paso entre frames vecinos (a lo ancho); en los detectores 0 y 9 y en los
frames del borde se usa el paso del lado que existe. Sin PSF: es la huella nominal, declarada como tal.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
WT = AQUI.parents[2]
ARBOL = WT / "experiments/_s162_modis_verif_cde/arbol"
PORTES = ARBOL / "experiments/_s159/portes"
RUN = Path(os.environ.get("VRP_S162_RUN", r"C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181"))
OBJ = WT / "experiments/_s162_modis_negativos/objetivos_neg_resto_modis.json"

sys.path.insert(0, str(ARBOL))
sys.path.insert(0, str(ARBOL / "scripts"))
sys.path.insert(0, str(PORTES))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import probe_portes as PP  # noqa: E402
import mirova_port as MP  # noqa: E402
from pipeline.process_modis import merge_mir_bands  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ORDEN_METODOS = ["todos", "A_centro_cubierto_ant", "A_centro_cubierto_sig", "A_huella_entera_ant", "B_filas_borde",
                 "C_sin_det0"]
DESCRIPCION = {
    "todos": "sin quitar nada (lo que hace el port)",
    "A_centro_cubierto_ant": "quita del barrido s los pixeles cuyo centro cae dentro del tramo de centros del barrido "
                             "s-1 en el mismo frame",
    "A_centro_cubierto_sig": "igual, pero quita del barrido s lo cubierto por el s+1 (conserva la copia posterior)",
    "A_huella_entera_ant": "quita del barrido s solo si su huella entera cae dentro de la huella del barrido s-1",
    "B_filas_borde": "regla de filas de borde del sintetico: conserva el detector solo si su centro esta a menos de "
                     "medio paso de barrido del centro de su barrido (franja nominal de ~10 km)",
    "C_sin_det0": "control positivo de cobertura: quita siempre el detector 0 (tiene que abrir huecos en el nadir)",
}


def pr_factory():
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)
    return pr, L


def objetivos():
    return {o["id"]: o for o in json.loads(OBJ.read_text(encoding="utf-8"))
            if o["b"] == "MODIS" and o["clase"] in ("neg_resto", "control_s159")}


def resultados():
    res = {}
    for f in sorted(RUN.glob("s162-negmodis-MODIS-*/resultados_MODIS_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    return res


def ruta_nativo(i):
    h = list(RUN.glob(f"s162-negmodis-MODIS-*/nativo_{i:04d}.npz"))
    return h[0] if len(h) == 1 else None


def evaluable(r):
    """Mismo criterio que experiments/_s162_modis_negativos/07_leer_lote.py."""
    if not r or r.get("estado") != "ok" or not r.get("port"):
        return False
    f = r["port"].get("fisica") or {}
    if f.get("motivo_vacio") in ("escena_invalida", "sunglint"):
        return False
    return r.get("port_estado") != "grilla_incompleta"


def cargar_nativo(i):
    z = np.load(ruta_nativo(i))
    return {k: z[k] for k in z.files}


def crop_desde_nativo(n, quitar=None):
    """Recorte con las claves que usa probe_portes.grillar; los quitados van con lat/lon NaN (grillar los ignora)."""
    lat = n["lat_mxd03"].astype(np.float64).copy()
    lon = n["lon_mxd03"].astype(np.float64).copy()
    if quitar is not None:
        lat[quitar] = np.nan
        lon[quitar] = np.nan
    return {"lat": lat, "lon": lon, "mir": merge_mir_bands(n["b21"], n["b22"], True), "tir": n["b31"]}


def correr_port(n, o, r, quitar=None):
    g = o["grilla"]
    mir, tir = PP.grillar(crop_desde_nativo(n, quitar), g, g["epsg"])
    p = MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], MP.SENSORES["MODIS"], modo="fisica",
                  semillas=0)
    p["_nan_grilla"] = int(np.isnan(mir).sum())
    return p


# ------------------------------------------------------------------------------------------------ geometria nativa
def xy_utm(n, epsg):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = t.transform(n["lon_mxd03"], n["lat_mxd03"])
    return np.asarray(x, np.float64), np.asarray(y, np.float64)


def geometria(n, epsg):
    """u (a lo largo de la traza, m), barrido, detector, vectores de huella a y b, y direccion por frame."""
    x, y = xy_utm(n, epsg)
    lin = n["linea"].astype(int)
    scan = lin // 10
    det = lin % 10
    R, C = x.shape
    scans = np.unique(scan[:, 0])
    filas = {s: np.nonzero(scan[:, 0] == s)[0] for s in scans}
    completos = [s for s in scans if len(filas[s]) == 10]
    # centroides por barrido completo y frame
    cx = {s: np.nanmean(x[filas[s]], axis=0) for s in completos}
    cy = {s: np.nanmean(y[filas[s]], axis=0) for s in completos}
    vx, vy, npar = np.zeros(C), np.zeros(C), 0
    for s in completos:
        if s + 1 in cx:
            dx, dy = cx[s + 1] - cx[s], cy[s + 1] - cy[s]
            nn = np.hypot(dx, dy)
            vx += dx / nn
            vy += dy / nn
            npar += 1
    nn = np.hypot(vx, vy)
    vx, vy = vx / nn, vy / nn
    u = x * vx[None, :] + y * vy[None, :]
    # vectores de huella: a lo largo (entre detectores del mismo barrido) y a lo ancho (entre frames)
    ax, ay = np.full_like(x, np.nan), np.full_like(y, np.nan)
    for s in scans:
        fs = filas[s]
        if len(fs) < 2:
            continue
        xs, ys = x[fs], y[fs]
        gx, gy = np.gradient(xs, axis=0), np.gradient(ys, axis=0)   # centrado dentro, de un lado en los bordes
        ax[fs], ay[fs] = gx, gy
    bx, by = np.gradient(x, axis=1), np.gradient(y, axis=1)
    # paso de barrido por frame (distancia entre centros de barridos consecutivos, a lo largo de u)
    cu = {s: cx[s] * vx + cy[s] * vy for s in completos}
    pasos = [cu[s + 1] - cu[s] for s in completos if s + 1 in cu]
    paso = np.nanmedian(np.vstack(pasos), axis=0) if pasos else np.full(C, np.nan)
    return {"x": x, "y": y, "u": u, "scan": scan, "det": det, "filas": filas, "completos": completos, "ax": ax,
            "ay": ay, "bx": bx, "by": by, "paso": paso, "cu": cu, "npares": npar}


def mascara_quitar(G, metodo):
    """Booleano (R, C): True = el pixel se quita antes de remuestrear."""
    u, scan, det, filas = G["u"], G["scan"], G["det"], G["filas"]
    R, C = u.shape
    q = np.zeros((R, C), bool)
    if metodo == "todos":
        return q
    if metodo == "C_sin_det0":
        return det == 0
    alen = np.hypot(G["ax"], G["ay"])
    scans = sorted(filas)
    for s in scans:
        fs = filas[s]
        if metodo in ("A_centro_cubierto_ant", "A_huella_entera_ant", "A_centro_cubierto_sig"):
            ref = s - 1 if metodo != "A_centro_cubierto_sig" else s + 1
            if ref not in filas:
                continue
            ur = u[filas[ref]]
            lo, hi = np.nanmin(ur, axis=0), np.nanmax(ur, axis=0)
            if metodo == "A_huella_entera_ant":
                ar = alen[filas[ref]]
                lo2 = lo - 0.5 * ar[np.nanargmin(ur, axis=0), np.arange(C)]
                hi2 = hi + 0.5 * ar[np.nanargmax(ur, axis=0), np.arange(C)]
                us, a_s = u[fs], alen[fs]
                q[fs] = ((us - 0.5 * a_s) >= lo2[None, :]) & ((us + 0.5 * a_s) <= hi2[None, :])
            else:
                us = u[fs]
                q[fs] = (us >= lo[None, :]) & (us <= hi[None, :])
        elif metodo == "B_filas_borde":
            if s in G["cu"]:
                c = G["cu"][s]
            else:   # barrido partido en el borde del recorte: su centro desde el vecino completo +/- paso
                vec = [t for t in G["cu"] if abs(t - s) == 1]
                if not vec:
                    continue
                t = vec[0]
                c = G["cu"][t] + (s - t) * G["paso"]
            q[fs] = np.abs(u[fs] - c[None, :]) >= 0.5 * G["paso"][None, :]
        else:
            raise ValueError(metodo)
    return q


def puntos_caja(g, medio_m, paso_m=200.0):
    """Puntos de muestreo del suelo en una caja de +/- medio_m alrededor de (X0, Y0), corridos para no caer en bordes."""
    off = 0.37 * paso_m
    xs = np.arange(g["X0"] - medio_m + off, g["X0"] + medio_m, paso_m)
    ys = np.arange(g["Y0"] - medio_m + off, g["Y0"] + medio_m, paso_m)
    X, Y = np.meshgrid(xs, ys)
    return X.ravel(), Y.ravel()


def conteo_cobertura(G, quitar, px, py, k=24, escala=1.0):
    """Cuantas huellas nominales de pixeles conservados contienen cada punto del suelo. escala > 1 agranda la huella
    (para separar rendijas finas entre huellas de huecos de verdad)."""
    from scipy.spatial import cKDTree
    x, y = G["x"].ravel(), G["y"].ravel()
    ax, ay, bx, by = (G[c].ravel() for c in ("ax", "ay", "bx", "by"))
    keep = ~quitar.ravel() & np.isfinite(x) & np.isfinite(ax) & np.isfinite(bx)
    idx = np.nonzero(keep)[0]
    tree = cKDTree(np.column_stack([x[idx], y[idx]]))
    _d, nb = tree.query(np.column_stack([px, py]), k=k)
    j = idx[nb]                                   # (npts, k)
    dx, dy = px[:, None] - x[j], py[:, None] - y[j]
    det = ax[j] * by[j] - ay[j] * bx[j]
    alpha = (dx * by[j] - dy * bx[j]) / det
    beta = (ax[j] * dy - ay[j] * dx) / det
    dentro = (np.abs(alpha) < 0.5 * escala) & (np.abs(beta) < 0.5 * escala)
    return dentro.sum(axis=1), dentro[:, -1]     # conteo, y si el vecino k-esimo aun contiene (k insuficiente)


def pixel_crater(G, g):
    """Pixel nativo mas cercano al punto de referencia (X0, Y0) de la grilla, y su detector."""
    d = np.hypot(G["x"] - g["X0"], G["y"] - g["Y0"])
    i, j = np.unravel_index(np.nanargmin(d), d.shape)
    return int(i), int(j), float(d[i, j])
