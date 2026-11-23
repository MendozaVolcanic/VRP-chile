# -*- coding: utf-8 -*-
"""Medición previa de las mejoras 3 y 4 del plan S196: cuando VIIRS 375 publica la cumbre y VIIRS 750 calla, ¿qué vio
el 750 del mismo satélite?

POR QUÉ. Son dos causas posibles con remedios distintos (V750-C, `experiments/_s162_v750c/INFORME.md`): (a) el 750 vio
algo pero lo diluyó (la interpolación lineal a la grilla de MIROVA reparte el calor de un píxel aislado entre cuatro
celdas, y el exceso no cruza el umbral): el 750 tiene 0 alertados o alertados lejos; remedio de la mejora 3 (vecino
más cercano o geometría nativa); (b) el 750 no miró ahí: la caja de detección (ROI) de la grilla de MIROVA no cubre el
cráter, porque la grilla está centrada en el punto de MIROVA y no en el cráter; remedio de la mejora 4 (grilla anclada
al cráter). Este script no distingue (a) de (b) por sí solo (no tiene las cajas por pasada), pero cuenta lo que se
puede leer de los records: cuántos alertados trae el par 750, a qué distancia del cráter publica el 375 y a qué
distancia del centro de la grilla de MIROVA cae esa posición.

Uso: python experiments/_s196_plan_mejoras/m4_par_750_de_solo375.py
"""
import collections
import importlib.util
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
_s = importlib.util.spec_from_file_location("m3", AQUI / "m3_cumbre_375_sin_750.py")
M3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M3)
bp = M3.bp


def main():
    import yaml
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    recs = M3.cargar("2026-03-01", "2026-11-22")
    # completar con campos crudos del 750 y del 375 que cargar() no guarda
    crudo = {}
    for vol in bp.VOLS:
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            crudo[(vol, r.get("sensor"), r.get("datetime_utc"))] = r
    _, _, solo = M3.clasificar(recs)
    por750 = collections.defaultdict(list)
    for r in recs:
        if r["b"] == "VIIRS750":
            por750[(r["vol"], r["plat"])].append(r)
    print("pasadas solo375 (375 publica, su par 750 no), ventana 2026-03-01 a 2026-11-22, data/mirova_equivalent")
    print("%-20s %5s | par 750: %-26s | 375: dist cráter km (mediana) | 375: dist centro MIROVA km (mediana)" % (
        "volcán", "n", "0 alertados / alertados"))
    for vol in bp.VOLS:
        L = [r for r in solo if r["vol"] == vol]
        if not L:
            continue
        v = vy[vol]
        c0 = (v.get("mirova_center_lat"), v.get("mirova_center_lon"))
        cero = con = 0
        dc, dm = [], []
        for r in L:
            par = [x for x in por750[(vol, r["plat"])] if abs((x["dt"] - r["dt"]).total_seconds()) <= M3.VENTANA_S]
            c750 = crudo.get((vol, r["plat"] + "_750", par[0]["dt"].strftime("%Y-%m-%d %H:%M"))) if par else None
            if c750 is not None and (c750.get("n_anomalous_pixels") or 0) > 0:
                con += 1
            else:
                cero += 1
            c375 = crudo.get((vol, r["plat"], r["dt"].strftime("%Y-%m-%d %H:%M")))
            if c375 and c375.get("final_hotspot_lat") is not None:
                dc.append(c375.get("final_hotspot_dist_km"))
                if c0[0] is not None:
                    dm.append(bp._hav_km(c375["final_hotspot_lat"], c375["final_hotspot_lon"], *c0))
        print("%-20s %5d | %26s | %28.2f | %34s" % (vol, len(L), "%d / %d" % (cero, con),
              statistics.median([d for d in dc if d is not None]) if dc else float("nan"),
              ("%.2f" % statistics.median(dm)) if dm else "-"))


if __name__ == "__main__":
    main()
