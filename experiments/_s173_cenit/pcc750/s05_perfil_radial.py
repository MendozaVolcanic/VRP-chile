# -*- coding: utf-8 -*-
"""s05 (S173, cenit PCC V750): perfil radial de la temperatura de brillo M13 en la grilla, en las pasadas con alerta
de MIROVA, para ver físicamente por qué el anillo de 5 a 25 km de K es más tibio que el entorno del lacolito.

POR QUÉ. s04 midió que la mediana del anillo es 3,6 a 5,5 K más tibia que el fondo local que interpola MIROVA bajo los
píxeles alertados. Si eso es porque el anillo junta terreno más bajo (valles y lagos alrededor del complejo), la BT
mediana tiene que subir con la distancia al centro; si es porque el anillo contiene la propia anomalía difusa, la
subida tiene que estar en la banda del lacolito (5-10 km) y no afuera. Sin modelo de elevación no se puede atribuir a
la altura: sólo se describe el perfil (SOSPECHA de causa).

P1: el perfil de una pasada sin alerta (negativo limpio) debe tener la misma forma si es topografía y no la anomalía:
    se repite sobre los negativos limpios de la misma ventana como control.
P2: si la grilla estuviera vacía (NaN) las bandas darían 'sin datos'; se cuenta cuántas celdas finitas tiene cada banda.
BT con la Planck de producción (pipeline/process_viirs_mod.py bt_to_spectral_radiance) invertida analíticamente.
Uso: python -B s05_perfil_radial.py
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / "src" / "s162"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import pipeline.process_viirs_mod as PV  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402
from _est import fl, linea, med, q  # noqa: E402

GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
BANDAS = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25)]
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def bt(Lr, lam=PV.M13_LAMBDA):
    with np.errstate(invalid="ignore", divide="ignore"):
        return PV.C2_PLANCK / (lam * np.log(PV.C1_PLANCK / (lam ** 5 * Lr) + 1))


def main():
    # control de la inversa
    t = np.array([250.0, 270.0, 290.0])
    pr("control inversa Planck (debe dar 250, 270, 290):", np.round(bt(PV.bt_to_spectral_radiance(t, PV.M13_LAMBDA)), 4))
    P = list(csv.DictReader(open(AQUI / "s03_por_pasada.csv", encoding="utf-8")))
    dk = OA.dist_km_centro()
    for grupo, sel in (("ALERTA MIROVA", lambda x: fl(x["vM"]) and fl(x["vM"]) > 0),
                       ("NEGATIVO LIMPIO (control)", lambda x: x["lab"] == "neg_limpio")):
        S = [x for x in P if sel(x)]
        pr(f"\n== {grupo}: n = {len(S)}")
        perf = {b: [] for b in BANDAS}
        rel = {b: [] for b in BANDAS}
        filas = []
        for x in S:
            g = np.load(GRILLAS / x["grilla"])
            T = bt(np.asarray(g["m13"], float))
            ref = np.nanmedian(T[(dk >= 5) & (dk <= 25)])
            fila = {"z": fl(x["z_record_K"])}
            for b in BANDAS:
                m = (dk >= b[0]) & (dk < b[1]) & np.isfinite(T)
                v = float(np.nanmedian(T[m])) if m.sum() else None
                perf[b].append((fila["z"], v))
                rel[b].append((fila["z"], v - ref if v is not None else None))
                fila[b] = (v, int(m.sum()))
            filas.append(fila)
        pr("celdas finitas por banda (mediana):", {f"{a}-{b}": int(np.median([f[(a, b)][1] for f in filas]))
                                                   for a, b in BANDAS})
        for b in BANDAS:
            linea(pr, f"BT {b[0]:>2}-{b[1]:<2} km - mediana 5-25",
                  [(z, v) for z, v in rel[b] if v is not None])
        for b in BANDAS:
            linea(pr, f"BT {b[0]:>2}-{b[1]:<2} km (K)", [(z, v) for z, v in perf[b] if v is not None])
    (AQUI / "s05_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
