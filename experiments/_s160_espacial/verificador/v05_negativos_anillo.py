# -*- coding: utf-8 -*-
"""V05 (verificador S160 espacial): afirmacion 4 (E-02). Recuenta, en Cordon Caulle, los negativos limpios publicados con
el cumulo a > 2 km del vent y fuera del anillo de MIROVA, y las alertas que perderia el contrafactual "anillo desde el
centro del TIF", por un camino distinto del auditor:
  - coordenadas del cumulo a precision completa desde el JSON de produccion (el CSV 03 del auditor redondea pc_lat/pc_lon a
    0,01 grados, ~1,1 km N-S);
  - anillo con su forma REAL (experiments/_s158_audit_r2/a113/m08_box_forma.txt en origin/main: filas 22-42 x cols 24-42 de
    la grilla de 67, caja 30-36): 11 filas al N de la 33 y 9 al S, o sea +8,625 km al N y -7,125 km al S, +-7,125 E-O
    (el auditor usa +-7,875 N-S simetrico);
  - dos centros: el del TIF (rasterio) y el de la grilla de MIROVA (celda 33 de la grilla UTM de objetivos.json, por celda
    exacta: fila y columna del punto en esa grilla).
Etiquetas lab/pub: las del CSV 03 del auditor (predicado del tablero con node); se re-corrio 03 en verificador/rerun y se
comprueba aqui que el CSV re-corrido coincide en lab y pub con el del auditor.

P1: si el anillo no se aplicara, "fuera del anillo" daria 0 en todos los sensores; control positivo: Isluga (vent en el
    centro) debe dar casi 0 fuera; P2: n por sensor impreso; 0 negativos publicados es SIN DATO.
Ventana: la de 03 (nocturno 2026-01-10 a 2026-10-21; la referencia local llega al 2026-10-18).
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

from pyproj import Geod, Transformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent
G = Geod(ellps="WGS84")
VENT = {"PuyehueCordonCaulle": (-40.525499, -72.146137), "Tupungatito": (-33.389044, -69.826374), "Isluga": (-19.15, -68.83)}
TC = {"PuyehueCordonCaulle": (-40.59027, -72.11673), "Tupungatito": (-33.42529, -69.79837), "Isluga": (-19.15043, -68.83036)}


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    return "VIIRS375" if s.startswith("VIIRS") else None


def dkm(a, b):
    return G.inv(a[1], a[0], b[1], b[0])[2] / 1000


def main():
    obj = json.load(open(AUD / "_censo_s159" / "objetivos.json", encoding="utf-8"))
    grilla = {o["volcan"]: o["grilla"] for o in obj}
    aud = list(csv.DictReader(open(AUD / "03_pareo_geometria_pasadas.csv", encoding="utf-8")))
    rr = AQUI / "rerun" / "03_pareo_geometria_pasadas.csv"
    if rr.exists():
        mine = {(r["vol"], r["b"], r["hora"]): (r["lab"], r["pub"]) for r in csv.DictReader(open(rr, encoding="utf-8"))}
        dif = sum(1 for r in aud if mine.get((r["vol"], r["b"], r["hora"])) != (r["lab"], r["pub"]))
        print(f"control: CSV 03 re-corrido vs del auditor, filas con lab o pub distinto: {dif} de {len(aud)}")
    for v in ("PuyehueCordonCaulle", "Tupungatito", "Isluga"):
        g = grilla[v]
        T = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
        recs = {}
        for r in json.load(open(AUD / "data" / f"{v}.json", encoding="utf-8"))["records"]:
            recs[(r["datetime_utc"], bucket(r.get("sensor")))] = r

        def celda(lat, lon):
            x, y = T.transform(lon, lat)
            return int((g["ul_y"] - y) // 750), int((x - g["ul_x"]) // 750)

        def en_anillo_real(lat, lon):
            f, c = celda(lat, lon)
            return 22 <= f <= 42 and 24 <= c <= 42

        def en_anillo_sim(lat, lon, centro):
            dn = (lat - centro[0]) * 111.195
            import math
            de = (lon - centro[1]) * 111.195 * math.cos(math.radians((lat + centro[0]) / 2))
            return abs(dn) <= 7.875 and abs(de) <= 7.125

        fv, cv = celda(*VENT[v])
        print(f"\n===== {v}: vent en celda (fila {fv}, col {cv}) de la grilla de MIROVA (anillo filas 22-42, cols 24-42; caja 30-36)")
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            sel = [r for r in aud if r["vol"] == v and r["b"] == b and r["lab"] == "neg_limpio" and r["pub"] == "1"]
            if not sel:
                print(f"  {b}: SIN DATO (0 negativos limpios publicados)")
                continue
            n2 = fuera_sim_csv = fuera_sim = fuera_real = 0
            cambia = []
            for r in sel:
                pc = recs[(r["hora"], b)]["primary_cluster"]
                ll = (pc["centroid_lat"], pc["centroid_lon"])
                if dkm(ll, VENT[v]) > 2:
                    n2 += 1
                a = not en_anillo_sim(float(r["pc_lat"]), float(r["pc_lon"]), TC[v])
                s = not en_anillo_sim(*ll, TC[v])
                re_ = not en_anillo_real(*ll)
                fuera_sim_csv += a
                fuera_sim += s
                fuera_real += re_
                if len({a, s, re_}) > 1:
                    cambia.append((r["hora"], round(ll[0], 4), round(ll[1], 4), celda(*ll), "csv" if a else "-", "sim" if s else "-", "real" if re_ else "-"))
            print(f"  {b}: {len(sel)} negativos limpios publicados; cumulo a > 2 km del vent {n2}; fuera del anillo: "
                  f"simetrico con lat/lon del CSV (0,01 grados) {fuera_sim_csv}, simetrico a precision completa {fuera_sim}, forma real por celda {fuera_real}")
            for c in cambia:
                print(f"     difiere: {c}")
            # contrafactual R3 sobre alertas: cuantas publicadas se apagan
            pos = [r for r in aud if r["vol"] == v and r["b"] == b and r["lab"] == "pos" and r["pub"] == "1"]
            ps = pr = 0
            det = []
            for r in pos:
                pc = recs[(r["hora"], b)].get("primary_cluster") or {}
                if pc.get("centroid_lat") is None or not (pc.get("vrp_mw") or 0) > 0:
                    ps += 1
                    pr += 1
                    continue
                ll = (pc["centroid_lat"], pc["centroid_lon"])
                s = en_anillo_sim(*ll, TC[v])
                re_ = en_anillo_real(*ll)
                ps += not s
                pr += not re_
                if not s or not re_:
                    det.append((r["hora"], r["mir_vrp"], r["mir_dist"], r["protegida"], round(dkm(ll, VENT[v]), 2), celda(*ll), "sim:fuera" if not s else "sim:dentro", "real:fuera" if not re_ else "real:dentro"))
            print(f"  {b}: alertas publicadas {len(pos)}; las apagaria el anillo desde el centro: simetrico {ps}, forma real {pr}")
            for d in det:
                print(f"     {d}")


if __name__ == "__main__":
    main()
