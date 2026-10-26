# -*- coding: utf-8 -*-
"""Verificador S159 PORTES, v03: ¿las 6 «protegidas perdidas» de VIIRS 375 son etiqueta (distancia del OCR de
otra pasada) o pérdida real del port? Dos pruebas con control.

(a) ¿Qué distancia informa MIROVA? Sobre las alertas de la TABLA (distancia confiable) en que el port encuentra
    píxeles, se compara Distancia_km con tres reglas del port: píxel más cercano, píxel de mayor radiancia MIR y
    centroide. La regla que mejor calza es el instrumento para (b). Control: si ninguna calza, (b) no se lee.
(b) Con esa regla, ¿la distancia del OCR de las filas dudosas calza con los píxeles del port de SU pasada? Se
    compara la tasa de calce de las filas dudosas con la de las filas sólo OCR no dudosas (control del mismo canal)
    y con la de la tabla (control del otro canal).
(c) ¿La distancia del OCR de una fila dudosa reaparece EXACTA en otra pasada del mismo volcán en las 36 h
    siguientes? Nulo: la misma búsqueda desplazada 7 días (las distancias están cuantizadas, D15, y repiten por
    azar).
Pregunta 1: si el OCR siempre trajera la distancia de su pasada, (b) daría la misma tasa en dudosas y control.
Pregunta 2: sin píxeles del port no hay calce posible; esas pasadas se cuentan como SIN DATO, no como desacuerdo.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"C:/vrp-trabajo/s159-n")
PORTES = ROOT / "experiments/_s159/portes"
ART = Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945")
REF = Path(r"D:/vrp-trabajo/temporales/s159_portes/ref")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

TOL_KM = 1.0       # calce entre la distancia de MIROVA y la del port (celda de 375 m, más la cuantización D15)


def reglas(p):
    px = p["pixeles"]
    d = [q[3] for q in px]
    imax = int(np.argmax([q[4] for q in px]))
    return {"cercano": min(d), "max_rad": px[imax][3], "centroide": p.get("_dcen")}


def main():
    obj = {o["id"]: o for o in json.loads((PORTES / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(ART.rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok":
                res[r["id"]] = r
    sys.path.insert(0, str(PORTES))
    import importlib.util
    spec = importlib.util.spec_from_file_location("an04", PORTES / "04_analizar.py")
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)

    grupos = {"tabla": [], "ocr_dudosa": [], "ocr_control": []}
    for i, o in sorted(obj.items()):
        if o["b"] != "VIIRS375" or o["lab"] != "pos" or i not in res:
            continue
        p = res[i]["port"]["sensible"]       # la caja más amplia: ve también lo que está fuera del ROI de cumbre
        al = [f for f in o["mirova"] if B.es_alerta(f["tipo"])]
        if not p.get("npix"):
            for f in al:
                g = "tabla" if f["source"] == "CONS" else None
                if g is None:
                    tabla = any(x["source"] == "CONS" for x in al)
                    g = None if tabla else ("ocr_dudosa" if (o["sensor"] == "VIIRS_SNPP" and o["hora_utc"] < "2026-10-09") else "ocr_control")
                if g:
                    grupos[g].append((i, o["volcan"], o["hora_utc"], f["dist_km"], None))
            continue
        p["_dcen"] = A.dist_centroide(p, o["grilla"])
        rg = reglas(p)
        tabla = any(x["source"] == "CONS" for x in al)
        for f in al:
            if f["source"] == "CONS":
                g = "tabla"
            elif tabla:
                continue                        # fila OCR de una pasada que la tabla ya trae: no es «sólo OCR»
            else:
                g = "ocr_dudosa" if (o["sensor"] == "VIIRS_SNPP" and o["hora_utc"] < "2026-10-09") else "ocr_control"
            grupos[g].append((i, o["volcan"], o["hora_utc"], f["dist_km"], rg))
    print("(a) y (b): ¿la distancia de MIROVA calza (|dif| <= %.1f km) con la regla del port en SU pasada?" % TOL_KM)
    print("    port = variante 'sensible' (ROI de escena entero; ve lo que la caja física no ve)")
    out = {}
    for g, lst in grupos.items():
        con = [x for x in lst if x[4] is not None and x[3] is not None]
        sin = [x for x in lst if x[4] is None]
        linea = f"  {g:12s} filas {len(lst)}, con píxeles del port {len(con)}, SIN DATO (0 px) {len(sin)}:"
        out[g] = {}
        for r in ("cercano", "max_rad", "centroide"):
            dif = [abs(x[3] - x[4][r]) for x in con]
            k = sum(d <= TOL_KM for d in dif)
            out[g][r] = [k, len(con), float(np.median(dif)) if dif else None]
            linea += f" {r} {k}/{len(con)} (mediana |dif| {np.median(dif) if dif else float('nan'):.2f} km);"
        print(linea)
        if g == "ocr_dudosa":
            for x in con:
                print(f"     {x[0]} {x[1]} {x[2]} OCR {x[3]} km | port cercano {x[4]['cercano']} max_rad "
                      f"{x[4]['max_rad']} centroide {x[4]['centroide']:.2f}")

    # (c) ¿la distancia del OCR dudoso reaparece exacta en otra pasada del mismo volcán?
    coords = B._coords_por_volcan()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, *_ = B.indexar_referencia(filas, coords, ("2026-03-01", "2026-10-28"), regla_minimas="original")
    todas = {}
    for (v, b), lst in por_vb.items():
        if b == "VIIRS375":
            todas[v] = lst

    def reaparece(v, t, d, desfase_dias=0, horas=36):
        t0 = t + timedelta(days=desfase_dias)
        for dt, f in todas.get(v, []):
            if abs((dt - t0).total_seconds()) <= 120 and desfase_dias == 0:
                continue
            if t0 < dt <= t0 + timedelta(hours=horas) and f.get("dist_km") is not None and abs(f["dist_km"] - d) <= 0.005:
                return True
        return False
    print("\n(c) ¿la distancia de la fila reaparece EXACTA (±0,005 km) en otra pasada VIIRS 375 del mismo volcán"
          " en las 36 h siguientes? (nulo: misma búsqueda 7 y 14 días después)")
    for g in ("ocr_dudosa", "ocr_control", "tabla"):
        lst = [x for x in grupos[g] if x[3] is not None and x[3] > 0]
        k0 = sum(reaparece(x[1], datetime.strptime(x[2], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), x[3]) for x in lst)
        k7 = sum(reaparece(x[1], datetime.strptime(x[2], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), x[3], 7) for x in lst)
        k14 = sum(reaparece(x[1], datetime.strptime(x[2], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), x[3], 14) for x in lst)
        print(f"  {g:12s} n {len(lst)}: reaparece {k0}; nulo +7 d {k7}; nulo +14 d {k14}")
        out[g]["reaparece"] = [k0, k7, k14, len(lst)]
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
