# -*- coding: utf-8 -*-
"""Pregunta 1: donde esta el calor que MIROVA alerta, segun su propia Distancia_km.

Distancia_km es un radio sin acimut, cuantizado al reticulo del sensor, medido desde el origen de la
grilla de MIROVA (docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md §5 y §7: origen ~250 m al SW del
Volc_LAT/LON; SOSPECHA fuerte de que es el pixel alertado MAS LEJANO, no el mas caliente). Aqui se
compara ese radio con:
  - nuestro inner_radius_km (medido desde el VENT, no desde el centro de la grilla: no son el mismo origen,
    y la diferencia de origenes es 4,8 km en Tupungatito y 7,2 km en PCC);
  - la media anchura de la caja de cumbre de MIROVA (2,625 km; esquina 3,71) y del anillo (7,875; esquina ~11,1).

Las dos preguntas del instrumento:
  P1 (si estuviera roto, se veria): si Distancia_km fuera basura, los histogramas no se concentrarian en
     valores del reticulo ni cambiarian entre volcanes; control positivo: Lascar y Villarrica (foco en el
     crater) deben dar mediana < 1,5 km.
  P2 (instrumento muerto): se imprime n por estrato; un estrato vacio se declara SIN DATO, no 0 %.

Denominador: filas ALERTA_TERMICA (CONS) y ALERTA_TERMICA_OCR (OCR) nocturnas (es_pasada_diurna_descartada)
de la referencia unificada local (snapshot del 2026-10-14 del CONS, 2026-10-18 del OCR, en data/mirova_reference/
mirova_v1_snapshot, commit db0dfe847 de origin/main), ventana 2026-01-10 a 2026-10-18.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import comun as C

sys.path.insert(0, str(C.ROOT))
sys.path.insert(0, str(C.ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from auto_audit_weekly import es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

SAL = C.AQUI / "01_distancia_mirova_salida.txt"
JS = C.AQUI / "01_distancia_mirova.json"
VOLS = C.VOLS + ["Lascar", "Villarrica"]
INNER = {"Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0, "Isluga": 5.0, "Lascar": 5.0, "Villarrica": 5.0}
LATLON = {"Lascar": (-23.369, -67.732), "Villarrica": (-39.42, -71.93)}
for v in C.VOLS:
    LATLON[v] = (C.GEO[v]["lat"], C.GEO[v]["lon"])

out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def q(xs, f):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * f
    i = int(k)
    return xs[i] if i == len(xs) - 1 else xs[i] + (xs[i + 1] - xs[i]) * (k - i)


def resumen(nombre, filas):
    d = [f["dist_km"] for f in filas if f["dist_km"] is not None]
    sin = sum(1 for f in filas if f["dist_km"] is None)
    if not d:
        p(f"  {nombre:36s} n={len(filas)} SIN DATO de distancia (sin distancia: {sin})")
        return {"n": len(filas), "n_dist": 0, "sin_dist": sin}
    vol = filas[0]["volcano"]
    inner = INNER[vol]
    r = {"n": len(filas), "n_dist": len(d), "sin_dist": sin, "p10": q(d, .1), "p50": q(d, .5), "p90": q(d, .9),
         "max": max(d), "pct_le_inner": 100 * sum(x <= inner for x in d) / len(d),
         "pct_le_caja": 100 * sum(x <= C.CAJA_KM for x in d) / len(d),
         "pct_le_caja_esq": 100 * sum(x <= C.CAJA_ESQUINA_KM for x in d) / len(d),
         "pct_le_anillo": 100 * sum(x <= C.ANILLO_KM for x in d) / len(d),
         "pct_le_anillo_esq": 100 * sum(x <= C.ANILLO_ESQUINA_KM for x in d) / len(d),
         "pct_gt_anillo_esq": 100 * sum(x > C.ANILLO_ESQUINA_KM for x in d) / len(d)}
    p(f"  {nombre:36s} n={r['n']:4d} (dist {r['n_dist']}, sin {sin}) p10/p50/p90/max = "
      f"{r['p10']:.2f}/{r['p50']:.2f}/{r['p90']:.2f}/{r['max']:.2f} km | <=inner({inner:g}) {r['pct_le_inner']:.0f}% | "
      f"<=caja 2,63 {r['pct_le_caja']:.0f}% (esq 3,71: {r['pct_le_caja_esq']:.0f}%) | <=anillo 7,88 {r['pct_le_anillo']:.0f}% "
      f"(esq 11,1: {r['pct_le_anillo_esq']:.0f}%) | >11,1 {r['pct_gt_anillo_esq']:.0f}%")
    return r


def main():
    filas = cargar_referencia_unificada()
    p(f"referencia unificada: {len(filas)} filas; ventana {min(f['fecha_utc'] for f in filas)[:10]} a "
      f"{max(f['fecha_utc'] for f in filas)[:10]}; sha origin/main {C.SHA_ORIGIN_MAIN}")
    res = {}
    noct = []
    for f in filas:
        if f["volcano"] not in VOLS or not f["tipo"].startswith("ALERTA"):
            continue
        if f["tipo"] == "ALERTA_SIN_GEOMETRIA_OCR":
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = LATLON[f["volcano"]]
        if es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
            continue
        f = dict(f)
        f["tramo"] = C.tramo_a119(f["fecha_utc"], f["source"])
        f["protegida"] = (f["vrp_mw"] or 0) >= C.PROTEGIDA_MW
        f["minima_sn"] = f["sensor_bucket"] == "VIIRS375" and (f["vrp_mw"] or 0) <= C.MINIMA_MW + 1e-9
        noct.append(f)
    p(f"alertas nocturnas (ALERTA_TERMICA + ALERTA_TERMICA_OCR, sin las SIN_GEOMETRIA) en los 5 volcanes: {len(noct)}")
    p("umbrales: caja de cumbre media anchura %.3f km (esquina %.2f); anillo %.3f km (esquina %.2f); inner por volcan %s"
      % (C.CAJA_KM, C.CAJA_ESQUINA_KM, C.ANILLO_KM, C.ANILLO_ESQUINA_KM, INNER))
    p("origen de Distancia_km: la grilla de MIROVA (~centro del TIF); origen de inner: el vent. Desfase vent-centro TIF:")
    for v in C.VOLS:
        g = C.GEO[v]
        d = C.hav_km(*g["tif_centro"], *g["vent"])
        b = C.rumbo_deg(*g["tif_centro"], *g["vent"])
        p(f"   {v:22s} vent a {d:.2f} km del centro del TIF, rumbo {b:.0f} ({C.octante(b)}); inner {g['inner_km']:g} km")
    for v in VOLS:
        p(f"\n== {v}")
        fv = [f for f in noct if f["volcano"] == v]
        res[v] = {}
        for b in ["VIIRS375", "VIIRS750", "MODIS"]:
            fb = [f for f in fv if f["sensor_bucket"] == b]
            if not fb:
                p(f"  {b}: SIN DATO (0 alertas nocturnas)")
                continue
            p(f"  -- {b}: {len(fb)} alertas; por tramo {dict(Counter(f['tramo'] for f in fb))}; "
              f"CONS {sum(f['source']=='CONS' for f in fb)} / OCR {sum(f['source']=='OCR' for f in fb)}; "
              f"protegidas {sum(f['protegida'] for f in fb)}; minimas SN {sum(f['minima_sn'] for f in fb)}")
            res[v][b] = {}
            res[v][b]["todas"] = resumen("todas", fb)
            res[v][b]["CONS"] = resumen("tabla (CONS) sola", [f for f in fb if f["source"] == "CONS"])
            res[v][b]["sin_minimas"] = resumen("sin minimas SN (decide)", [f for f in fb if not f["minima_sn"]])
            res[v][b]["protegidas"] = resumen("protegidas >= 1 MW", [f for f in fb if f["protegida"]])
            for t in sorted(set(f["tramo"] for f in fb)):
                res[v][b]["tramo_" + t] = resumen("tramo " + t, [f for f in fb if f["tramo"] == t])
            # histograma por valor exacto (reticulo)
            cnt = Counter(round(f["dist_km"], 2) for f in fb if f["dist_km"] is not None)
            p("  valores mas frecuentes de Distancia_km:", cnt.most_common(8))
            res[v][b]["hist"] = cnt.most_common(30)
    JS.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    SAL.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
