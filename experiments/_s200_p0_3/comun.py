"""Piezas comunes del experimento P0 parte (3): enmascaramiento en la detección de la vía (VIIRS 750).

Importa el detector de producción desde una copia de origin/main exportada con `git archive` a main_snapshot/
(no toca el checkout ni pipeline/). Ninguna función de aquí cambia la detección: sólo arma las entradas como lo
hace calcular_vrp_granulo y llama a detectar_mirova tal cual.
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import os

import numpy as np

os.environ["VRP_PROFILE"] = "mirova_equivalent"   # perfil de producción, antes de importar pipeline
AQUI = Path(__file__).resolve().parent
SNAP = AQUI / "main_snapshot"
sys.path.insert(0, str(SNAP))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
DIR_REC = REPO / "experiments" / "_s158_audit_r2" / "granulos" / "run_39641637298" / "s158-r2-granulos"


def utf8():
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def volcanes():
    import yaml
    return {v["name"]: v for v in yaml.safe_load((SNAP / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def escenas():
    """Lista de escenas: recorte + geometría del centro (de resultados.json, la misma pasada)."""
    res = json.loads((DIR_REC / "resultados.json").read_text(encoding="utf-8"))
    geo = {}
    for r in res:
        if "geometria_centro" in r:
            clave = f"{r['volcan']}_{r['hora_utc'].replace(' ', '_').replace(':', '')}"
            geo[clave] = (r["geometria_centro"], r.get("granulo"))
    out = []
    for f in sorted(DIR_REC.glob("recorte_*.npz")):
        clave = f.stem[len("recorte_"):]
        volcan = clave.split("_")[0]
        out.append({"clave": clave, "volcan": volcan, "ruta": f, "geom": geo[clave][0], "granulo": geo[clave][1]})
    return out


def cargar(esc):
    d = np.load(esc["ruta"])
    return {k: d[k] for k in d.files}


class Escena:
    """Una pasada lista para el detector, armada como calcular_vrp_granulo (VIIRS 750)."""

    def __init__(self, esc):
        self.meta = esc
        self.d = cargar(esc)
        v = volcanes()[esc["volcan"]]
        self.v = v
        self.vent_lat, self.vent_lon = get_detection_anchor(v)
        self.inner_km = v.get("inner_radius_km")
        self.g = MV.grilla_del_volcan(esc["volcan"])
        geom = esc["geom"]
        self.geom = geom
        self.dayflag = 0 if geom["solar_zenith"] > 90 else 1
        self.sg = MV.sunglint_deg(geom["sensor_zenith"], geom["solar_zenith"], geom["sensor_azimuth"],
                                  geom["solar_azimuth"])
        # recorte de producción (45 km del centro de SU grilla) sobre los píxeles del recorte S158
        lat, lon = self.d["lat"], self.d["lon"]
        dist = MV._haversine(lat, lon, self.g["centro_lat"], self.g["centro_lon"])
        self.sel = np.isfinite(dist) & (dist < MV.RADIO_RECORTE_KM)
        self.m13g, self.m15g = MV.remuestrear_grilla(lat, lon, self.d["m13"], self.d["m15"], self.g)
        self.pos = MV.posicion_de(self.g, self.vent_lat, self.vent_lon)
        celda = MV.celda_de(self.g, self.vent_lat, self.vent_lon)
        self.roi = self.g.get("roi", "def")
        cfg = MV.FAMILIAS["VIIRS750"]
        self.box = MV.caja_roi(self.roi, n=self.g["n"], celda_crater=celda, inner_km=self.inner_km,
                               lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=self.g["paso"])
        # x, y UTM de los píxeles del recorte en la zona de la grilla (para ubicar el foco)
        from pyproj import Transformer
        t = Transformer.from_crs("EPSG:4326", f"EPSG:{self.g['epsg']}", always_xy=True)
        self.px, self.py = t.transform(lon, lat)
        self._t_inv = Transformer.from_crs(f"EPSG:{self.g['epsg']}", "EPSG:4326", always_xy=True)

    def detectar(self, m13g, m15g):
        return MV.detectar_mirova(m13g, m15g, self.box, self.dayflag, self.sg, devolver_diag=True)

    def xy_celda(self, fila, col):
        paso = self.g["paso"]
        return self.g["ul_x"] + paso * (col + 0.5), self.g["ul_y"] - paso * (fila + 0.5)

    def celda_xy(self, x, y):
        paso = self.g["paso"]
        return (self.g["ul_y"] - y) / paso - 0.5, (x - self.g["ul_x"]) / paso - 0.5

    def pesos_pixel_lento(self, i):
        """Peso de interpolación del píxel i sobre cada celda llamando a remuestrear_grilla de producción con un impulso
        (sólo para el control de la matriz rápida)."""
        out = []
        for b in ("m13", "m15"):
            v = self.d[b]
            imp = np.where(np.isfinite(v), 0.0, np.nan)
            imp[i] = 1.0
            w13, _ = MV.remuestrear_grilla(self.d["lat"], self.d["lon"], imp, imp, self.g)
            out.append(np.nan_to_num(w13, nan=0.0))
        return out

    def matrices(self):
        """Matriz de interpolación lineal (celdas x píxeles del recorte) por banda, con la MISMA triangulación que
        griddata(method='linear') de remuestrear_grilla (LinearNDInterpolator sobre los mismos puntos). POR QUÉ: la
        interpolación lineal con triangulación fija es lineal en los valores, así que la grilla con el foco es la grilla
        base más delta por la columna del píxel; así no hay que re-triangular en cada contraste."""
        if getattr(self, "_W", None) is not None:
            return self._W
        from scipy.interpolate import LinearNDInterpolator
        from scipy.sparse import csr_matrix
        from pyproj import Transformer
        g = self.g
        n, paso = int(g["n"]), float(g["paso"])
        idx_sel = np.flatnonzero(self.sel)
        t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
        x, y = t.transform(self.d["lon"][self.sel], self.d["lat"][self.sel])
        X, Y = np.meshgrid(g["ul_x"] + paso * (np.arange(n) + 0.5), g["ul_y"] - paso * (np.arange(n) + 0.5))
        xi = np.column_stack([X.ravel(), Y.ravel()])
        W = []
        for b in ("m13", "m15"):
            v = self.d[b][self.sel]
            ok = np.isfinite(v)
            pts = np.column_stack([x[ok], y[ok]])
            it = LinearNDInterpolator(pts, v[ok])
            tri = it.tri
            s = tri.find_simplex(xi)
            T = tri.transform[s]
            bary2 = np.einsum("ijk,ik->ij", T[:, :2, :], xi - T[:, 2, :])
            bary = np.column_stack([bary2, 1 - bary2.sum(axis=1)])
            verts = tri.simplices[s]
            col_global = idx_sel[ok][verts]          # índice del píxel en el recorte
            filas = np.repeat(np.arange(xi.shape[0]), 3)
            dentro = np.repeat(s >= 0, 3)
            M = csr_matrix((bary.ravel()[dentro], (filas[dentro], col_global.ravel()[dentro])),
                           shape=(xi.shape[0], self.d[b].size))
            W.append((M, s < 0))
        self._W = W
        return W

    def pesos_pixel(self, i):
        """Columna i de las matrices de interpolación, como grilla n x n, por banda."""
        n = int(self.g["n"])
        out = []
        for M, fuera in self.matrices():
            w = np.asarray(M[:, i].todense()).ravel()
            w[fuera] = 0.0
            out.append(w.reshape(n, n))
        return out


def nombre_corto(clave):
    return clave
