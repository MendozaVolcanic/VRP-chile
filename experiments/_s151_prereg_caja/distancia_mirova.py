# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop, arreglo D1 del verificador del PR #800. ¿Desde que punto mide MIROVA `Distancia_km`, y cuantas
de sus alertas caen fuera de SU caja de 5 x 5 km?

POR QUE IMPORTA. La version 1 del pre-registro conto las alertas de MIROVA fuera de la caja solo en los 8 volcanes
cuyo centro de grilla esta cerca del crater (0,9 a 2,2 %) y dejo fuera Tupungatito, Puyehue Cordon Caulle y
Planchon Peteroa "porque su punto de referencia esta corrido". Pero si `Distancia_km` se mide desde el centro de la
grilla de MIROVA y la caja de MIROVA se centra en ese mismo punto, en esos tres volcanes la distancia SI ubica la
alerta respecto de la caja de MIROVA, y excluirlos sesga la cuenta hacia "MIROVA calla fuera de la caja".

LO QUE SE SABE, CON SU FUENTE.
  1. El CSV del scraper copia `Distancia_km` de la tabla `latest.php` de MIROVA (Mirova-v1, reconciliar_latest.py:
     "latest.php es la tabla AUTORITATIVA de MIROVA (trae la distancia exacta)"): la distancia la calcula MIROVA.
  2. Esa distancia es un desplazamiento en celdas ENTERAS de la grilla de MIROVA (100 % de 10.085 filas MODIS y de
     11.810 VIIRS 375, docs/MIROVA_DIVERGENCES.md D15): se mide desde una CELDA de su grilla, no desde un punto
     libre como el GVP o el crater.
  3. El centro de esa grilla esta a 4,86 km del crater en Tupungatito, 7,57 km en Puyehue Cordon Caulle y unos 2 km
     en Planchon Peteroa (D17, GeoTIFF de MIROVA; `mirova_center` de volcanoes.yaml).
  4. Coppola 2016a (p. 6) centra la grilla y la caja ROI1 en lo mismo, "the volcano's summit". No publica la
     coordenada: que sea el mismo punto es la lectura mas simple, no un dato.
LO QUE ESTE SCRIPT AGREGA. Si `Distancia_km` se mide desde el centro de grilla, las alertas de un volcan cuyo calor
esta en el crater deberian amontonarse a la distancia crater-centro de grilla (4,86 km en Tupungatito, 7,57 en
PCC). Si se midiera desde el crater, se amontonarian cerca de 0. Se mide la fraccion de alertas a menos de 1 km de
cada una de las dos distancias.

DOS LECTURAS DE "FUERA DE LA CAJA DE MIROVA", con su numero:
  L1 (caja centrada en el centro de grilla, el mismo punto desde el que se mide la distancia): fuera con cualquier
     acimut si Distancia_km > 3,54 km; ambiguo de 2,5 a 3,54.
  L2 (caja centrada en el crater): en los 8 centrados vale lo mismo que L1; en los 3 corridos solo hay una cota
     inferior de la distancia al crater, |Distancia_km - d(centro, crater)| (desigualdad triangular): fuera seguro
     si esa cota supera 3,54.

Uso: python distancia_mirova.py > distancia_mirova_salida.txt
"""
from __future__ import annotations

import collections, statistics, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1"), str(RAIZ / "experiments" / "_s148_caja")):
    sys.path.insert(0, _p)
import yaml  # noqa: E402
import evaluar as ev  # noqa: E402
import lectura_caja as lc  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
bp = ev.bp

CONG_V1 = RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v1"
SEMI = 2.5 * 2 ** 0.5
CORRIDOS = ("Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa")


def centros_de_grilla():
    cfg = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vs = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    out = {}
    for v in (vs.values() if isinstance(vs, dict) else vs):
        n = v.get("name") or v.get("id")
        if n in bp.VOLS:
            out[n] = (v.get("mirova_center_lat", v["lat"]), v.get("mirova_center_lon", v["lon"]), "mirova_center" in str(v.keys()))
    return out


def cuenta(filas, ventana, titulo, sensores=("VIIRS375", "VIIRS750", "MODIS")):
    coords = bp._coords_por_volcan(); anclas = lc.anclas(); cg = centros_de_grilla()
    por_vb, _, _, _ = bp.indexar_referencia(filas, coords, ventana)
    print("\n######## %s: %s a %s" % (titulo, ventana[0], ventana[1]))
    for s in sensores:
        tot = collections.Counter()
        print("\n== %s | por volcan: d(centro de grilla, crater) | alertas | mediana de Distancia_km | a menos de 1 km del crater "
              "si la distancia fuera desde el centro de grilla / desde el crater | L1 >3,54 y ambiguas | L2 fuera seguro" % s)
        for v in bp.VOLS:
            al = [f for dt, f in por_vb.get((v, s), []) if bp.es_alerta(f["tipo"]) and f["dist_km"] is not None]
            if not al:
                continue
            dc = ev._hav(cg[v][0], cg[v][1], anclas[v][0], anclas[v][1])
            d = [f["dist_km"] for f in al]
            cerca_cg = sum(abs(x - dc) <= 1.0 for x in d); cerca_cr = sum(x <= 1.0 for x in d)
            l1 = sum(x > SEMI for x in d); amb = sum(2.5 < x <= SEMI for x in d)
            l2 = sum(abs(x - dc) > SEMI for x in d)
            tot.update({"n": len(d), "l1": l1, "amb": amb, "l2": l2})
            if v in CORRIDOS:
                tot.update({"n_corr": len(d), "l1_corr": l1, "amb_corr": amb})
            print("   %-20s %5.2f km | %4d | %5.2f km | %4d / %4d | %4d y %3d | %4d" % (v, dc, len(d), statistics.median(d), cerca_cg, cerca_cr, l1, amb, l2))
        if tot["n"]:
            print("   TOTAL 11: alertas %d | L1 fuera %d (%.1f %%), con las ambiguas %d (%.1f %%) | L2 fuera seguro %d (%.1f %%) | de los 3 corridos: %d de %d fuera en L1" % (
                tot["n"], tot["l1"], 100 * tot["l1"] / tot["n"], tot["l1"] + tot["amb"], 100 * (tot["l1"] + tot["amb"]) / tot["n"],
                tot["l2"], 100 * tot["l2"] / tot["n"], tot["l1_corr"], tot["n_corr"]))


def main():
    v1 = cargar_referencia_unificada(CONG_V1 / "registro_vrp_consolidado.csv", CONG_V1 / "registro_vrp_ocr.csv",
                                     historico_path=CONG_V1 / "consolidado_filas_perdidas.csv", respaldo_path=CONG_V1 / "respaldo_20260408.csv")
    cuenta(v1, ("2026-08-29", "2026-10-08"), "V1, referencia congelada (tabla y OCR)")
    tabla = [f for f in cargar_referencia_unificada() if f["source"] == "CONS"]
    cuenta(tabla, ("2026-04-01", "2026-10-08"), "ABRIL A OCTUBRE, solo la tabla (la distancia que calcula MIROVA, sin OCR)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
