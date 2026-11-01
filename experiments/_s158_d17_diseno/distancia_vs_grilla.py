# -*- coding: utf-8 -*-
"""S158, diseño D17: ¿desde qué celda mide MIROVA su `Distancia_km`, y cae su foco donde lo dice el TIF?

POR QUÉ: D15 mostró que el `Distancia_km` de VIIRS 375 es siempre √(i²+j²)·0,375 km, pero no pudo decir
desde qué celda, porque sólo tenía TIF reproyectados. Con los TIF UTM (14 y 15 de septiembre, A106) la
grilla es exacta (`grilla_tif.py`). Si el TIF es la matriz sobre la que MIROVA detecta, la celda más
caliente del TIF tiene que estar justo a `Distancia_km` de una celda de referencia fija.

Pasos: (1) índice del archivo de TIF por la API; (2) TIF de VIIRS 375 con CRS UTM; (3) alertas del
consolidado y del OCR (VRP > 0, VIIRS375) de la misma adquisición (|Δt| ≤ 120 s, hora de adquisición del
índice, no la del nombre: A106); (4) celda de mayor exceso local (valor menos mediana de 7x7) en el TIF;
(5) su distancia en celdas a cada celda de referencia candidata, comparada con `Distancia_km`.

Candidatas: las cuatro celdas que tocan el centro de la grilla (134 celdas: el centro es una esquina) y la
celda que contiene `mirova_center`. Coincide si |d_pred − Distancia_km| ≤ 0,01 km (MIROVA publica dos
decimales).
Uso: python -I distancia_vs_grilla.py <raiz del repo> <carpeta temporal>
"""
import csv
import io
import math
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
import yaml
from pyproj import Transformer
from scipy.ndimage import median_filter

REPO_TIF = "MendozaVolcanic/mirova-tif-archive"
ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}
ALIAS_CSV = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}
CELDA = 375.0


def gh_raw(ruta):
    return subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                           f"repos/{REPO_TIF}/contents/{ruta}"], capture_output=True, check=True).stdout


def t_utc(s):
    s = s.strip().replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def alertas(repo):
    out = []
    base = os.path.join(repo, "data", "mirova_reference", "mirova_v1_snapshot")
    for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        for r in csv.DictReader(open(os.path.join(base, nombre), encoding="utf-8", errors="replace")):
            if r.get("Sensor") != "VIIRS375" or not r.get("Fecha_Satelite_UTC", "").startswith(("2026-09-14", "2026-09-15")):
                continue
            try:
                vrp, dist = float(r["VRP_MW"]), float(r["Distancia_km"])
            except (TypeError, ValueError):
                continue
            if vrp <= 0:
                continue
            out.append({"vol": ALIAS_CSV.get(r["Volcan"], r["Volcan"]), "t": t_utc(r["Fecha_Satelite_UTC"]),
                        "vrp": vrp, "dist": dist, "tipo": r["Tipo_Registro"], "fuente": nombre.split("_")[2][:4]})
    return out


def main(repo, tmp):
    os.makedirs(tmp, exist_ok=True)
    vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(repo, "volcanoes.yaml"),
                                                      encoding="utf-8"))["volcanoes"]}
    idx = list(csv.DictReader(io.StringIO(gh_raw("index.csv").decode("utf-8"))))
    filas = [f for f in idx if f["sensor"] == "VIIRS375" and f["acquisition_utc"][:10] in ("2026-09-14", "2026-09-15")]
    als = alertas(repo)
    cuenta = {}
    n_par = 0
    vistos = set()
    for f in filas:
        vol = ALIAS_TIF.get(f["volcano"], f["volcano"])
        if vol not in vols or f["md5"] in vistos:
            continue      # MIROVA a veces repite una imagen vieja bajo otra hora (A106)
        vistos.add(f["md5"])
        t_acq = t_utc(f["acquisition_utc"])
        pares = [a for a in als if a["vol"] == vol and abs((a["t"] - t_acq).total_seconds()) <= 120]
        if not pares:
            continue
        destino = os.path.join(tmp, f["tif_path"].replace("/", "_"))
        if not os.path.exists(destino):
            open(destino, "wb").write(gh_raw(f["tif_path"]))
        with rasterio.open(destino) as s:
            if s.crs.to_epsg() == 4326:
                continue
            a, t, epsg = s.read(1).astype(float), s.transform, s.crs.to_epsg()
        exceso = a - median_filter(a, size=7, mode="nearest")
        n = a.shape[0]
        fwd = Transformer.from_crs(4326, epsg, always_xy=True)
        v = vols[vol]
        mx, my = fwd.transform(v["mirova_center_lon"], v["mirova_center_lat"])
        refs = {"(66,66)": (66, 66), "(66,67)": (66, 67), "(67,66)": (67, 66), "(67,67)": (67, 67),
                "mirova_center": (int((t.f - my) // CELDA), int((mx - t.c) // CELDA))}
        for al in pares:
            # foco: celda de mayor exceso a menos de Distancia_km + 2 km del centro (MIROVA no informa dónde)
            fil, col = np.indices(a.shape)
            dcen = np.hypot(col + 0.5 - n / 2, fil + 0.5 - n / 2) * CELDA / 1000
            m = np.where(dcen <= al["dist"] + 2.0, exceso, -np.inf)
            jf, jc = np.unravel_index(np.argmax(m), m.shape)
            n_par += 1
            linea = []
            for nom, (rf, rc) in refs.items():
                d = math.hypot(jf - rf, jc - rc) * CELDA / 1000
                ok = abs(d - al["dist"]) <= 0.01
                cuenta[nom] = cuenta.get(nom, 0) + ok
                linea.append(f"{nom}={d:.2f}{'*' if ok else ''}")
            print(f"{vol:20s} {al['t']:%m-%d %H:%M} {al['fuente']} {al['tipo']:16s} VRP {al['vrp']:6.2f} "
                  f"Dist {al['dist']:5.2f} foco(fila {jf}, col {jc}) " + " ".join(linea))
    print(f"\npares alerta-TIF UTM: {n_par}")
    for nom, c in cuenta.items():
        print(f"  referencia {nom:14s}: Distancia_km coincide en {c} de {n_par}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
