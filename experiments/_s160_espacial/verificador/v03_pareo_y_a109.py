# -*- coding: utf-8 -*-
"""V03 (verificador S160 espacial): dos controles sobre las afirmaciones 1 y 2.

(a) Tolerancia del pareo TIF <-> fila de MIROVA. 02b parea cada TIF con la fila de MIROVA a +-30 min, dando PRIORIDAD a una
    ALERTA sobre RUTINA. Con tres satelites VIIRS separados ~25-50 min, un TIF de una pasada puede quedar etiquetado ALERTA
    por la alerta de otra pasada. Aqui se recalcula "foco a vent p50" y "% a <= 1 km" restringiendo a |dt| <= 2 min, 2-10 min
    y > 10 min, sobre el CSV 02b_tif_v375_focos.csv del auditor (columna mir_dt_min) y, aparte, re-pareando por mi cuenta con
    las filas a <= 120 s sin prioridad de tipo.
(b) Control A109 (maldicion del ganador) para la coincidencia foco del TIF <-> nuestro cumulo: la distancia del foco del TIF
    de una pasada con alerta al cumulo nuestro de la MISMA pasada (+-15 min) contra la distancia al cumulo nuestro de OTRA
    pasada de la misma noche separada 45 a 120 min (otro granulo, mismo estado del volcan) y contra un placebo: el cumulo de
    una pasada de OTRA noche elegida al azar (semilla fija).
P1: si el pareo estuviera roto, |dt| <= 2 min daria resultados indistinguibles de > 10 min; control positivo: en RUTINA el
    foco cae lejos del vent (02b: 7 % a <= 1 km en Tupungatito). P2: n por estrato impreso; estrato vacio = SIN DATO.
Ventana: la de los TIF de 02b (mayo a octubre 2026) y los records de origin/main db0dfe847.
"""
from __future__ import annotations

import io
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pandas as pd
from pyproj import Geod

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent
ROOT = AUD.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

G = Geod(ellps="WGS84")
VENT = {"PuyehueCordonCaulle": (-40.525499, -72.146137), "Tupungatito": (-33.389044, -69.826374), "Isluga": (-19.15, -68.83)}


def dkm(a, b):
    return G.inv(a[1], a[0], b[1], b[0])[2] / 1000


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    return "VIIRS375" if s.startswith("VIIRS") else None


def resumen(nombre, sub):
    if len(sub) == 0:
        print(f"    {nombre:40s} SIN DATO")
        return
    print(f"    {nombre:40s} n={len(sub):3d} foco a vent p50 {sub.d_vent.median():.2f} km, <=1 km {100*(sub.d_vent<=1).mean():.0f} %, "
          f"<=1,5 km {100*(sub.d_vent<=1.5).mean():.0f} %")


def main():
    df = pd.read_csv(AUD / "02b_tif_v375_focos.csv")
    ref = [f for f in cargar_referencia_unificada() if f["volcano"] in VENT and f["sensor_bucket"] == "VIIRS375"]
    print("(a) tolerancia del pareo TIF <-> MIROVA (CSV 02b del auditor; d_vent recalculado aqui con geodesica WGS84)")
    df = df[df.vol.isin(list(VENT))].copy()
    df["d_vent"] = [dkm((r.lat, r.lon), VENT[r.vol]) for r in df.itertuples()]
    df["mir_tipo"] = df.mir_tipo.fillna("")
    for v in VENT:
        dv = df[df.vol == v]
        al = dv[dv.mir_tipo.str.startswith("ALERTA")]
        print(f"\n  == {v}: TIF etiquetados ALERTA {len(al)}; |dt| en min: p50 {al.mir_dt_min.abs().median():.1f}, max {al.mir_dt_min.abs().max():.1f}")
        resumen("ALERTA (como 02b, +-30 min)", al)
        resumen("ALERTA con |dt| <= 2 min", al[al.mir_dt_min.abs() <= 2])
        resumen("ALERTA con 2 < |dt| <= 10 min", al[(al.mir_dt_min.abs() > 2) & (al.mir_dt_min.abs() <= 10)])
        resumen("ALERTA con |dt| > 10 min", al[al.mir_dt_min.abs() > 10])
        resumen("RUTINA (control)", dv[dv.mir_tipo == "RUTINA"])
        rv = [(datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc), f) for f in ref if f["volcano"] == v]
        lab = []
        for r in dv.itertuples():
            t = datetime.strptime(r.t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            tipos = set(f["tipo"] for dt, f in rv if abs((dt - t).total_seconds()) <= 120)
            lab.append("ALERTA" if any(x.startswith("ALERTA") for x in tipos) else ("RUTINA" if tipos == {"RUTINA"} else ("sin_fila" if not tipos else "otra")))
        dv = dv.assign(lab120=lab)
        resumen("re-pareo propio a 120 s: ALERTA", dv[dv.lab120 == "ALERTA"])
        resumen("re-pareo propio a 120 s: RUTINA", dv[dv.lab120 == "RUTINA"])
        print(f"    TIF que 02b llama ALERTA, segun el re-pareo a 120 s: {dict(dv[dv.mir_tipo.str.startswith('ALERTA')].lab120.value_counts())}")
        print(f"    origen de la hora del TIF en ALERTA: {dict(al.origen_t.value_counts())}")

    print("\n(b) control A109: foco del TIF (ALERTA segun 02b) contra nuestro cumulo de la misma pasada, de otra pasada de la "
          "misma noche (45-120 min) y de otra noche al azar")
    rnd = random.Random(160)
    for v in VENT:
        recs = []
        for r in json.load(open(AUD / "data" / f"{v}.json", encoding="utf-8"))["records"]:
            if bucket(r.get("sensor")) != "VIIRS375":
                continue
            pc = r.get("primary_cluster") or {}
            if pc.get("centroid_lat") is None:
                continue
            recs.append((datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), (pc["centroid_lat"], pc["centroid_lon"])))
        dv = df[(df.vol == v) & df.mir_tipo.str.startswith("ALERTA")]
        misma, otra, azar, vent_d = [], [], [], []
        for r in dv.itertuples():
            t = datetime.strptime(r.t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            f = (r.lat, r.lon)
            m = sorted(((abs((dt - t).total_seconds()), p) for dt, p in recs if abs((dt - t).total_seconds()) <= 900), key=lambda x: x[0])
            o = [p for dt, p in recs if 45 * 60 <= abs((dt - t).total_seconds()) <= 120 * 60]
            z = [p for dt, p in recs if abs((dt - t).total_seconds()) > 86400 * 2]
            if not (m and o and z):
                continue
            misma.append(dkm(f, m[0][1]))
            otra.append(min(dkm(f, p) for p in o))
            azar.append(dkm(f, rnd.choice(z)))
            vent_d.append(dkm(f, VENT[v]))
        if not misma:
            print(f"  {v}: SIN DATO")
            continue
        n = len(misma)
        print(f"  {v}: n={n} TIF con cumulo nuestro en la misma pasada Y en otra pasada de la misma noche")
        for nom, L in (("misma pasada", misma), ("otra pasada misma noche (la mas cercana)", otra), ("otra noche al azar", azar), ("vent (referencia fija)", vent_d)):
            print(f"     d(foco TIF, {nom:42s}) p50 {median(L):.2f} km; <=0,6 km {100*sum(x<=0.6 for x in L)/n:.0f} %; <=1,5 km {100*sum(x<=1.5 for x in L)/n:.0f} %")


if __name__ == "__main__":
    main()
