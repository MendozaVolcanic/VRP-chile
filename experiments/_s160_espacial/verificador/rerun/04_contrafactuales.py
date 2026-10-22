# -*- coding: utf-8 -*-
"""Pregunta 4: que cambio de GEOMETRIA acercaria nuestra publicacion a la de MIROVA. Contrafactuales sobre records
existentes (origin/main db0dfe847), sin tocar el pipeline. NINGUNO es una recomendacion de adopcion (eso pasa por
pre-registro). Cada contrafactual se evalua con el mismo filtro de artefacto del tablero (isThermalArtifact = 1 apaga
siempre) y con la deteccion tal cual esta en el record: solo cambia QUE pixeles/cumulos cuentan y DESDE DONDE se mide.

Reglas (todas con "hay energia" = vrp_mw > 0 del pixel o del cumulo; un cumulo en 0 MW no publica en ninguna):
  PROD   : predicado del tablero ejecutado con node (03_pareo_geometria_pasadas.csv, columna pub).
  R1     : como PROD pero el inner se mide desde el centro del TIF de MIROVA (no desde el vent): publica si
           distance_class != far-by-vent... se reconstruye: pc.vrp > 0 y d(pc, centro TIF) <= inner.
  R2     : caja de cumbre de MIROVA: pc.vrp > 0 y el centroide dentro del cuadrado de +-2,625 km (N-S y E-W) del centro del TIF.
  R3     : anillo de MIROVA: pc.vrp > 0 y centroide dentro del rectangulo +-7,875 km N-S y +-7,125 km E-W del centro del TIF
           (21 x 19 celdas de 750 m, m08_box_forma.txt).
  R4     : suma de TODOS los pixeles anomalos con vrp > 0 dentro del anillo (R3) del centro del TIF, sin eleccion de cumulo ni
           etiqueta: publica si la suma > 0. (Lo que haria MIROVA segun su codigo: suma todos los alertados del recuadro.)
  R5     : como R4 pero con la caja de cumbre (R2).
  R6     : PROD o R4 (union): mide cuantas alertas se RECUPERAN solo por geometria sin perder las de hoy.
  R7     : pixel anomalo con vrp > 0 a <= inner del VENT (sin eleccion de cumulo ni etiqueta): aisla el efecto de la
           eleccion de cumulo / etiqueta far respecto del radio actual.
Para cada regla: alertas publicadas (de las pareadas, y protegidas), negativos limpios encendidos, y el neto contra PROD.
Ventana y etiquetas: las de 03_pareo_geometria.py (nocturno, 2026-01-10 a 2026-10-21, D-9 SN, lectura A).

Las dos preguntas del instrumento:
  P1: R2 debe apagar casi todo en Tupungatito y PCC (su calor esta a 4,8 y 7,6 km del centro) y no cambiar Isluga: si R2 no
      apaga nada, la geometria no se esta aplicando. R7 con inner infinito debe publicar toda pasada con energia (control).
  P2: se imprime n por celda; sin alertas pareadas en un sensor = SIN DATO.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict

import comun as C

SAL = C.AQUI / "04_contrafactuales_salida.txt"
JS = C.AQUI / "04_contrafactuales.json"
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def dentro_caja(lat, lon, centro, half_ns, half_ew):
    de, dn = C.dxy_km(centro[0], centro[1], lat, lon)
    return abs(dn) <= half_ns and abs(de) <= half_ew


def main():
    pas = list(csv.DictReader(open(C.AQUI / "03_pareo_geometria_pasadas.csv", encoding="utf-8")))
    idx = {(r["vol"], r["hora"]): r for r in pas}
    assert len({(r["vol"], r["hora"], r["b"]) for r in pas}) == len(pas), "clave (vol, hora, sensor) no unica"
    recs = {}
    for v in C.VOLS:
        for r in json.load(open(C.DATA / f"{v}.json", encoding="utf-8"))["records"]:
            k = (v, r["datetime_utc"], C.bucket(r.get("sensor")))
            if (v, r["datetime_utc"]) in idx and k not in recs:
                recs[k] = r
    p(f"pasadas de 03: {len(pas)}; con record cargado: {len(recs)}")
    reglas = ["PROD", "R1_inner_desde_centroTIF", "R2_caja_cumbre_pc", "R3_anillo_pc", "R4_suma_pixeles_anillo",
              "R5_suma_pixeles_caja", "R6_PROD_o_R4", "R7_pixel_a_inner_del_vent", "CTRL_R7_inner_inf"]
    res = {}
    for v in C.VOLS:
        g = C.GEO[v]
        tc, vent, inner = g["tif_centro"], g["vent"], g["inner_km"]
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            R = [r for r in pas if r["vol"] == v and r["b"] == b]
            if not R:
                continue
            tab = defaultdict(lambda: {"pos": 0, "pos_tabla": 0, "prot": 0, "neg_limpio": 0, "minima": 0, "far_ref": 0})
            n = Counter()
            ejemplos = defaultdict(list)
            for r in R:
                rec = recs[(v, r["hora"], b)]
                pc = rec.get("primary_cluster") or {}
                ap = [x for x in (rec.get("anomaly_pixels") or []) if x.get("lat") is not None]
                art = r["pub"] == "0" and r.get("art") == "1"
                art = int(r.get("art") or 0) == 1
                pcv = (pc.get("vrp_mw") or 0) > 0
                pc_ll = (pc.get("centroid_lat"), pc.get("centroid_lon")) if pc.get("centroid_lat") is not None else None
                pub = {"PROD": r["pub"] == "1"}
                pub["R1_inner_desde_centroTIF"] = (not art) and pcv and pc_ll is not None and C.hav_km(*pc_ll, *tc) <= inner
                pub["R2_caja_cumbre_pc"] = (not art) and pcv and pc_ll is not None and dentro_caja(*pc_ll, tc, C.CAJA_KM, C.CAJA_KM)
                pub["R3_anillo_pc"] = (not art) and pcv and pc_ll is not None and dentro_caja(*pc_ll, tc, C.ANILLO_KM, 9.5 * 0.75)
                s4 = sum((x.get("vrp_mw") or 0) for x in ap if dentro_caja(x["lat"], x["lon"], tc, C.ANILLO_KM, 9.5 * 0.75))
                s5 = sum((x.get("vrp_mw") or 0) for x in ap if dentro_caja(x["lat"], x["lon"], tc, C.CAJA_KM, C.CAJA_KM))
                pub["R4_suma_pixeles_anillo"] = (not art) and s4 > 0
                pub["R5_suma_pixeles_caja"] = (not art) and s5 > 0
                pub["R6_PROD_o_R4"] = pub["PROD"] or pub["R4_suma_pixeles_anillo"]
                pub["R7_pixel_a_inner_del_vent"] = (not art) and any((x.get("vrp_mw") or 0) > 0 and C.hav_km(x["lat"], x["lon"], *vent) <= inner for x in ap)
                pub["CTRL_R7_inner_inf"] = (not art) and any((x.get("vrp_mw") or 0) > 0 for x in ap)
                lab = r["lab"]
                n[lab] += 1
                if lab == "pos" and r["protegida"] == "True":
                    n["prot"] += 1
                if lab == "pos" and ("CONS" in (r.get("mir_src") or "")):
                    n["pos_tabla"] += 1
                for k, val in pub.items():
                    if not val:
                        continue
                    if lab == "pos":
                        tab[k]["pos"] += 1
                        if r["protegida"] == "True":
                            tab[k]["prot"] += 1
                        if ("CONS" in (r.get("mir_src") or "")):
                            tab[k]["pos_tabla"] += 1
                    elif lab in ("neg_limpio", "minima", "far_ref"):
                        tab[k][lab] += 1
                    if k == "R4_suma_pixeles_anillo" and not pub["PROD"] and lab in ("pos", "neg_limpio") and len(ejemplos[(k, lab)]) < 5:
                        ejemplos[(k, lab)].append((r["hora"], r["mir_vrp"], r["mir_dist"], round(s4, 3), r["dc"], r["pc_vrp"], r["pc_dvent"]))
                    if k == "R3_anillo_pc" and pub["PROD"] and lab == "pos" and len(ejemplos[("R3_pierde", lab)]) < 5 and not pub["R3_anillo_pc"]:
                        pass
                for k in ("R2_caja_cumbre_pc", "R3_anillo_pc"):
                    if pub["PROD"] and not pub[k] and lab == "pos" and len(ejemplos[(k, "pierde")]) < 4:
                        ejemplos[(k, "pierde")].append((r["hora"], r["mir_vrp"], r["mir_dist"], r["pc_vrp"], r["pc_dtif"], r["pc_rtif"]))
            p(f"\n== {v} {b}: pasadas {len(R)}; pos {n['pos']} (tabla {n['pos_tabla']}, protegidas {n['prot']}), neg_limpio {n['neg_limpio']}, "
              f"minima {n['minima']}, far_ref {n['far_ref']}")
            p(f"   {'regla':28s} {'alertas pub':>12s} {'tabla':>6s} {'proteg':>7s} {'neg enc':>8s} {'neg %':>6s} {'minima':>7s} {'far_ref':>8s} | neto vs PROD (alertas, negativos)")
            base = tab["PROD"]
            res[f"{v}|{b}"] = {"n": dict(n)}
            for k in reglas:
                t = tab[k]
                negpct = 100 * t["neg_limpio"] / n["neg_limpio"] if n["neg_limpio"] else float("nan")
                p(f"   {k:28s} {t['pos']:5d}/{n['pos']:<6d} {t['pos_tabla']:6d} {t['prot']:3d}/{n['prot']:<3d} {t['neg_limpio']:8d} {negpct:5.1f}% {t['minima']:7d} {t['far_ref']:8d} | "
                  f"{t['pos']-base['pos']:+d} alertas, {t['neg_limpio']-base['neg_limpio']:+d} negativos")
                res[f"{v}|{b}"][k] = dict(t)
            for (k, lab), ej in ejemplos.items():
                p(f"     ejemplos {k} {lab}: {ej}")
    JS.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    SAL.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
