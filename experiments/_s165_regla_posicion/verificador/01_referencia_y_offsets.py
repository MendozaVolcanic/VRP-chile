# -*- coding: utf-8 -*-
"""Verificador S165 (regla de posición), 1: qué hay en la referencia de MIROVA que los universos de VIIRS no miran, y
desde dónde mide cada regla. Sólo lectura.

POR QUÉ. (a) Los universos de VIIRS 750 y VIIRS 375 vienen de poblacion_completa.json de S159, que sólo trae
neg_limpio y pos: una pasada con fila FALSO_POSITIVO (fuente lejana que MIROVA publicó y el scraper marcó por
distancia) o sin fila no está. En MODIS esa clase («resto») existe y es donde cayó el único cambio. Cuento cuántas
filas FALSO_POSITIVO tiene la copia de hoy por sensor y volcán en la ventana de cada censo. (b) La regla «cercano»
tiene un sesgo estructural en el cotejo: el alertado más cercano a la referencia puede estar EN la celda de referencia
(0,0 km); si MIROVA nunca informa 0,0 para una alerta, «cercano» pierde ese cotejo por construcción. Cuento cuántas
alertas de la tabla traen Distancia_km = 0. (c) El desfase cráter (get_detection_anchor) contra X0, Y0 por volcán,
que es lo que separa cerc_cr de cerc_ref y lo que hace posible la dirección «calla» con cerc_ref.
Uso: python 01_referencia_y_offsets.py  (escribe 01_referencia_y_offsets_salida.txt)
"""
import collections
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun as C  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan", "PlanchonPeteroa",
          "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
VENTANA = {"MODIS": ("2026-03-01", "2026-10-16 23:59"), "VIIRS750": ("2026-04-01", "2026-10-21 23:59"),
           "VIIRS375": ("2026-04-01", "2026-10-21 23:59")}


def main():
    idx, proc = C.cargar_referencia()
    pr("== referencia:", json.dumps({k: v["sha_commit"] for k, v in proc.items() if k.endswith(".csv")}))
    filas = [f for lst in idx.values() for _, f in lst]
    pr("\n== (a) filas de la tabla (CONS) por tipo, sensor y ventana del censo, Tier A")
    for b, (d0, d1) in VENTANA.items():
        sel = [f for f in filas if f["sensor_bucket"] == b and f["source"] == "CONS" and f["volcano"] in TIER_A
               and d0 <= f["fecha_utc"][:16] <= d1]
        pr(f"   {b} ({d0} a {d1[:10]}): {len(sel)} filas;", dict(collections.Counter(f["tipo"] for f in sel)))
        fp = [f for f in sel if f["tipo"] == "FALSO_POSITIVO"]
        pr(f"      FALSO_POSITIVO por volcán:", dict(collections.Counter(f["volcano"] for f in fp)))
        pr(f"      FALSO_POSITIVO nocturnas (hora UTC 00 a 12):",
           sum(1 for f in fp if 0 <= int(f["fecha_utc"][11:13]) < 12), "| dist mediana (km):",
           float(np.median([f["dist_km"] for f in fp if f["dist_km"] is not None])) if fp else None)
        ocr = [f for f in filas if f["sensor_bucket"] == b and f["source"] == "OCR" and f["volcano"] in TIER_A
               and d0 <= f["fecha_utc"][:16] <= d1]
        pr(f"      OCR: {len(ocr)} filas;", dict(collections.Counter(f["tipo"] for f in ocr)))

    pr("\n== (b) Distancia_km de las alertas de la tabla con VRP > 0: ¿alguna vez 0,0?")
    for b in VENTANA:
        al = [f for f in filas if f["sensor_bucket"] == b and f["source"] == "CONS" and f["volcano"] in TIER_A
              and f["tipo"].startswith("ALERTA") and (f["vrp_mw"] or 0) > 0 and f["dist_km"] is not None]
        ceros = sum(1 for f in al if f["dist_km"] == 0)
        vals = collections.Counter(round(f["dist_km"], 2) for f in al)
        pr(f"   {b}: {len(al)} alertas con distancia; con 0,0 km: {ceros}; valores más frecuentes:",
           vals.most_common(8))
    pr("   (FALSO_POSITIVO y RUTINA aparte)")
    for b in VENTANA:
        fp = [f for f in filas if f["sensor_bucket"] == b and f["source"] == "CONS" and f["volcano"] in TIER_A
              and f["tipo"] == "FALSO_POSITIVO" and f["dist_km"] is not None]
        pr(f"   {b} FALSO_POSITIVO: {len(fp)}; con 0,0 km: {sum(1 for f in fp if f['dist_km'] == 0)}; "
           f"mín dist {min((f['dist_km'] for f in fp), default=None)}")

    pr("\n== (c) desfase cráter (get_detection_anchor) contra la referencia X0, Y0 de grillas_mirova.yaml, por volcán")
    V = C.volcanes()
    MV = C.MV
    pr("   volcán | inner_km | cráter a X0,Y0 (km) | cráter a celda (33,33) de la grilla 750 (km) | "
       "una celda-cráter sola: cerc_ref > inner?")
    for n in TIER_A:
        v = V[n]
        la, lo = C.get_detection_anchor(v)
        g = MV.grilla_del_volcan(n)                               # 750 m
        pos = MV.posicion_de(g, la, lo)
        ref = ((g["ul_y"] - g["y0"]) / g["paso"] - 0.5, (g["x0"] - g["ul_x"]) / g["paso"] - 0.5)
        d_ref = float(np.hypot(pos[0] - ref[0], pos[1] - ref[1]) * g["paso"] / 1000)
        d_33 = float(np.hypot(pos[0] - 33, pos[1] - 33) * g["paso"] / 1000)
        pr(f"   {n:20s} {v['inner_radius_km']:4.0f} {d_ref:8.3f} {d_33:8.3f}   {d_33 > v['inner_radius_km']}")
    pr("   (si el desfase es mayor que el inner, un píxel en el cráter queda far con cerc_ref: ahí la dirección "
       "«calla» es posible por el punto de medida, no por la regla)")
    (AQUI / "01_referencia_y_offsets_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
