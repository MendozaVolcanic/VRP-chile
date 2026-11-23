# -*- coding: utf-8 -*-
"""Medición previa de MEJ-4 (plan S196), segunda vuelta: noches en que VIIRS 375 publica 1 MW o más y MODIS calla.

POR QUÉ. La primera cuenta (`m4b_modis_en_noches_375.py`) comparó noches con focos de 0,1 a 0,3 MW, que MODIS no ve
en ninguna caja: no tenía poder para ver el efecto de la caja (verificador S196, debilidad 1). Con el 375 sobre 1 MW
el foco ya es del tamaño que MODIS ve en Láscar y Chillán; si en Cordón Caulle o Tupungatito, con el cráter fuera de
la caja MODIS (D36 punto 7), MODIS sigue en cero esas noches, la caja es sospechosa. No lo prueba: el MODIS pasa horas
antes o después que el VIIRS y el lacolito es una fuente extensa y tibia. Diseño del verificador S196 (su script en
D:/vrp-trabajo/temporales/s196_plan/verificador/disparador_mej4.py), traído al repo con este encabezado.

Uso: python experiments/_s196_plan_mejoras/m4c_disparador_mej4.py
"""
import collections
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent


def _cargar(nombre, archivo):
    s = importlib.util.spec_from_file_location(nombre, AQUI / archivo)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M3 = _cargar("m3", "m3_cumbre_375_sin_750.py")
M7 = _cargar("m7", "m7_modis_sobre_rutina.py")


def main():
    v = M3.cargar("2026-03-01", "2026-11-22")
    m = M7.cargar_modis("2026-03-01", "2026-11-22")
    mx = collections.defaultdict(float)
    for r in v:
        if r["b"] == "VIIRS375" and r["pub"]:
            k = (r["vol"], r["dt"].date())
            mx[k] = max(mx[k], r["disp"] or 0)
    mrec = collections.defaultdict(list)
    for r in m:
        mrec[(r["vol"], r["dt"].date())].append(r)
    print("noches (2026-03-01 a 2026-11-22) con VIIRS 375 publicado de 1 MW o más y algún record MODIS; MODIS publica:")
    for vol in M3.bp.VOLS:
        noches = [k for k in mx if k[0] == vol and mx[k] >= 1.0 and k in mrec]
        pub = [k for k in noches if any(x["pub"] for x in mrec[k])]
        print("  %-20s %3d noches; MODIS publica en %3d" % (vol, len(noches), len(pub)))
    crudo = {}
    for vol in ("PuyehueCordonCaulle", "Tupungatito"):
        for r in json.loads((M3.bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            crudo[(vol, r.get("sensor"), r.get("datetime_utc"))] = r
    for vol in ("PuyehueCordonCaulle", "Tupungatito"):
        print("\n%s: pasadas 375 publicadas de 1 MW o más en noches con record MODIS (MODIS: hora, publica, MW, píxeles)" % vol)
        for r in sorted(v, key=lambda x: x["dt"]):
            if (r["vol"] == vol and r["b"] == "VIIRS375" and r["pub"] and (r["disp"] or 0) >= 1.0
                    and (vol, r["dt"].date()) in mrec):
                c = crudo.get((vol, r["plat"], r["dt"].strftime("%Y-%m-%d %H:%M")))
                ms = [(x["dt"].strftime("%H:%M"), bool(x["pub"]), round(x["disp"] or 0, 2), x["npix"])
                      for x in mrec[(vol, r["dt"].date())]]
                print("  %s %-12s %.2f MW, a %s km del cráter; MODIS %s" % (
                    r["dt"].strftime("%Y-%m-%d %H:%M"), r["plat"], r["disp"],
                    c.get("final_hotspot_dist_km") if c else None, ms))


if __name__ == "__main__":
    main()
