# -*- coding: utf-8 -*-
"""S131 auditoria MAGNITUD - item 4 bis: el gradiente cenital medido POR PASADA.

POR QUE. `02_correccion_area_por_angulo.py` (un par por NOCHE, maximo de cada lado,
la regla de `_s126_lib`) dio un gradiente V375 de 0.80 -> 0.60 entre nadir y 50+,
mientras S130/S131 (`factor_requerido.py`, que empareja CADA record contra el maximo
de MIROVA de la noche) dieron 0.74 -> 0.25. Las dos definiciones son legitimas para
cosas distintas, pero ninguna es la correcta para un eje ANGULAR: el maximo de la
noche mezcla pasadas de angulos distintos. La ground truth tiene hora al segundo
(`Fecha_Satelite_UTC`), asi que se puede emparejar pasada con pasada.

DEFINICION (A90): par = (record nuestro nocturno con pc.vrp_mw>0) x (fila ALERTA de
MIROVA, CONS union OCR con alias A11/A14, mismo bucket de sensor, |dt| <= 20 min,
VRP_MW>0, nocturna 03-09 UTC como en el loader canonico). Si hay varias filas
MIROVA en la ventana se toma la mas cercana en tiempo. Ventana 2026, 11 Tier A.
Angulo = |sensor_zenith_deg| del record. Brazos A/B/C identicos al script 02.
Cruce extra: donde la fila OCR trae `Zenith_Sat_deg`, se compara con nuestro angulo.
Cruce extra 2: records MODIS con `pc.d9_capped` (cap 5 MW del path D) vs MIROVA.
"""
import csv
import io
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta

if __name__ == "__main__":   # al importarlo desde 04 no re-envolver stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
sys.path.insert(0, HERE)
from _s126_lib import ALIAS, FUENTES_GT, SENSOR_MAP, bucket, ic95  # noqa: E402
import importlib  # noqa: E402
m02 = importlib.import_module("02_correccion_area_por_angulo")
f_modelo, f_lineal, bin_de = m02.f_modelo, m02.f_lineal, m02.bin_de

OUT = os.path.join(HERE, "03_pares_por_pasada.json")
VOLS = list(ALIAS)
BINS = ["0-15", "15-25", "25-35", "35-50", "50+"]
MIN_N = 15
TOL = timedelta(minutes=20)
BANDA = (0.7, 1.4)


def cargar_gt_por_pasada(ventana):
    """{(vol, bucket): [(datetime, vrp, zen_ocr)]} de ALERTAS nocturnas 2026."""
    out = defaultdict(list)
    for fname in FUENTES_GT:
        path = os.path.join(ROOT, fname)
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            f = (r.get("Fecha_Satelite_UTC") or "")
            if not b or not (ventana[0] <= f[:10] <= ventana[1]):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
                dt = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if v <= 0 or not (3 <= dt.hour <= 9):
                continue
            zen = None
            try:
                zen = float(r.get("Zenith_Sat_deg")) if r.get("Zenith_Sat_deg") else None
            except ValueError:
                zen = None
            out[(vol, b)].append((dt, v, zen))
    return out


def med(xs):
    return round(st.median(xs), 3)


def main():
    gt = cargar_gt_por_pasada(("2026-01-01", "2026-12-31"))
    pares = []          # (vol, bk, zen, ours, mirova, zen_ocr, d9)
    zen_cmp = []
    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            sol = r.get("solar_zenith_deg")
            if bk is None or (sol is not None and sol < 90):
                continue
            sen = r.get("sensor_zenith_deg")
            pc = r.get("primary_cluster") or {}
            pcv = pc.get("vrp_mw") or 0
            if sen is None or pcv <= 0:
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if not ("2026-01-01" <= r["datetime_utc"][:10] <= "2026-12-31"):
                continue
            cand = [(abs(g[0] - dt), g) for g in gt.get((v, bk), []) if abs(g[0] - dt) <= TOL]
            if not cand:
                continue
            _, (gdt, gv, gzen) = min(cand, key=lambda x: x[0])
            pares.append((v, bk, abs(sen), pcv, gv, gzen, bool(pc.get("d9_capped"))))
            if gzen is not None:
                zen_cmp.append((abs(sen), gzen))

    brazos = {"A_sin": lambda z: 1.0, "B_modelo": f_modelo, "C_lineal": f_lineal}
    res = {"definicion": __doc__, "por_sensor": {}, "por_volcan": {},
           "cruce_zenith_ocr": {}, "modis_d9_capped": {}}
    print(f"pares por pasada: {len(pares)}  (V375 {sum(1 for p in pares if p[1]=='v375')}, "
          f"V750 {sum(1 for p in pares if p[1]=='v750')}, MODIS {sum(1 for p in pares if p[1]=='modis')})")
    if zen_cmp:
        d = [a - b for a, b in zen_cmp]
        res["cruce_zenith_ocr"] = {"n": len(d), "mediana_dif_deg": med(d),
                                   "p90_abs_dif_deg": round(sorted(abs(x) for x in d)[int(0.9*len(d))], 1)}
        print(f"cruce zenith nuestro - OCR: n={len(d)} mediana={med(d)} "
              f"p90|dif|={res['cruce_zenith_ocr']['p90_abs_dif_deg']}")
    for bk, nom in (("v375", "VIIRS375"), ("v750", "VIIRS750"), ("modis", "MODIS")):
        sub = [p for p in pares if p[1] == bk]
        if len(sub) < MIN_N:
            continue
        usar = ("A_sin",) if bk == "modis" else tuple(brazos)
        print(f"\n{nom} n_pares={len(sub)}")
        print(f"  {'bin':7s} {'n':>5s} {'zen_med':>8s} {'ours_med':>9s} {'mir_med':>8s} "
              + " ".join(f"{b:>10s}" for b in usar))
        out_b = {}
        for b in BINS:
            xs = [p for p in sub if bin_de(p[2]) == b]
            if len(xs) < MIN_N:
                continue
            fila = {"n": len(xs), "zen_mediano": med([p[2] for p in xs]),
                    "ours_mediana_mw": med([p[3] for p in xs]),
                    "mirova_mediana_mw": med([p[4] for p in xs])}
            for br in usar:
                fila[br] = med([p[3] * brazos[br](p[2]) / p[4] for p in xs])
            out_b[b] = fila
            print(f"  {b:7s} {len(xs):5d} {fila['zen_mediano']:8.1f} {fila['ours_mediana_mw']:9.3f} "
                  f"{fila['mirova_mediana_mw']:8.3f} " + " ".join(f"{fila[br]:10.3f}" for br in usar))
        glob = {}
        for br in usar:
            rs = [p[3] * brazos[br](p[2]) / p[4] for p in sub]
            glob[br] = {"mediana": med(rs), "ic95": ic95(rs), "n": len(rs),
                        "n_sobre_2": sum(1 for x in rs if x > 2.0),
                        "pct_sobre_2": round(100 * sum(1 for x in rs if x > 2.0) / len(rs), 1),
                        "n_en_banda": sum(1 for x in rs if BANDA[0] <= x <= BANDA[1]),
                        "pct_en_banda": round(100 * sum(1 for x in rs if BANDA[0] <= x <= BANDA[1]) / len(rs), 1)}
            print(f"  global {br:9s} mediana={glob[br]['mediana']:.3f} IC95={glob[br]['ic95']} "
                  f">2.0: {glob[br]['n_sobre_2']}/{len(rs)} ({glob[br]['pct_sobre_2']}%)  "
                  f"en banda: {glob[br]['n_en_banda']} ({glob[br]['pct_en_banda']}%)")
        res["por_sensor"][bk] = {"bins": out_b, "global": glob}
        pv = {}
        print(f"  por volcan (n>=15): {'volcan':20s} {'n':>4s} {'zen':>5s} " + " ".join(f"{b:>9s}" for b in usar))
        for v in VOLS:
            xs = [p for p in sub if p[0] == v]
            if len(xs) < MIN_N:
                pv[v] = {"n": len(xs)}
                continue
            fila = {"n": len(xs), "zen_mediano": med([p[2] for p in xs])}
            for br in usar:
                rs = [p[3] * brazos[br](p[2]) / p[4] for p in xs]
                fila[br] = med(rs)
                fila[br + "_sobre_2"] = sum(1 for x in rs if x > 2.0)
                fila[br + "_en_banda"] = BANDA[0] <= fila[br] <= BANDA[1]
            pv[v] = fila
            print(f"    {v:20s} {len(xs):4d} {fila['zen_mediano']:5.1f} "
                  + " ".join(f"{fila[br]:9.3f}" for br in usar)
                  + "   banda: " + " ".join(
                      f"{br[0]}={'si' if fila[br + '_en_banda'] else 'NO'}" for br in usar))
        res["por_volcan"][bk] = pv
        if bk == "modis":
            cap = [p for p in sub if p[6]]
            nocap = [p for p in sub if not p[6]]
            res["modis_d9_capped"] = {
                "n_capped_con_mirova": len(cap),
                "ratio_capped_mediana": med([p[3] / p[4] for p in cap]) if cap else None,
                "mirova_mediana_mw_capped": med([p[4] for p in cap]) if cap else None,
                "n_no_capped": len(nocap),
                "ratio_no_capped_mediana": med([p[3] / p[4] for p in nocap]) if nocap else None}
            print(f"  MODIS d9_capped con MIROVA: n={len(cap)} ratio med="
                  f"{res['modis_d9_capped']['ratio_capped_mediana']} MIROVA med MW="
                  f"{res['modis_d9_capped']['mirova_mediana_mw_capped']} | sin cap n={len(nocap)} "
                  f"ratio med={res['modis_d9_capped']['ratio_no_capped_mediana']}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
