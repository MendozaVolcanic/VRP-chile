# -*- coding: utf-8 -*-
"""Verificador F5, paso 5: razon VIIRS 750 / VIIRS 375 en la MISMA pasada (mismo satelite, mismo minuto),
con lo publicado y con lo que V750 habria publicado sumando todo lo alertado (sin seleccion ni modo de un pixel).

Por que: las bandas M e I del mismo satelite comparten geometria y agregacion bow-tie, asi que un efecto de
area no deberia mover su cociente con el cenit. Si el cociente cae con lo publicado y queda plano con la
suma total, la caida de V750 la explica la seleccion de cumulo (F5-01), no el area.

Denominador: todos los records de la ventana 2026-09-28..2026-10-19 (no solo los pareados con MIROVA),
pasadas con V375 publicado > 0 y V750 con primary_cluster. Pregunta 1: si la seleccion no importara, las
dos columnas darian igual: lo veria. Pregunta 2: sin pares, imprime SIN DATO.
"""
import io, json, math, os, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
VLAT, VLON = -36.863, -71.377


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def main():
    d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
    rs = [r for r in d["records"] if "2026-09-28" <= r["datetime_utc"][:10] <= "2026-10-19"]
    i375 = {(r["datetime_utc"][:16], r["sensor"]): r for r in rs if r["sensor"].startswith("VIIRS") and not r["sensor"].endswith("_750")}
    filas = []
    for r in rs:
        if not r["sensor"].endswith("_750"):
            continue
        k = (r["datetime_utc"][:16], r["sensor"][:-4])
        q = i375.get(k)
        pc = r.get("primary_cluster")
        if not q or not pc or r.get("distance_class") != "summit":
            continue
        v375 = q.get("f5_core_vrp_mw")
        if v375 is None:
            v375 = (q.get("primary_cluster") or {}).get("vrp_mw")
        if not v375 or v375 <= 0.05:
            continue
        tot750 = sum(p["vrp_mw"] for p in (r.get("anomaly_pixels") or []) if hav(p["lat"], p["lon"], VLAT, VLON) <= 5.0)
        filas.append(dict(t=k[0], zen=r["sensor_zenith_deg"], pub=pc["vrp_mw"], tot=tot750, v375=v375, solar=r.get("solar_zenith_deg")))
    if not filas:
        print("SIN DATO"); return
    noct = [f for f in filas if (f["solar"] or 0) > 90]
    print("pares misma pasada (V750 summit con pc, V375 > 0,05 MW): %d, nocturnos %d" % (len(filas), len(noct)))
    for nombre, e0 in (("todos", filas), ("nocturnos", noct)):
        print("\n[%s] banda   n  V750pub/V375  V750total/V375" % nombre)
        for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
            e = [f for f in e0 if lo <= f["zen"] < hi]
            if e:
                print("  %2d-%2d %4d   %6.2f        %6.2f" % (lo, hi, len(e), statistics.median(f["pub"] / f["v375"] for f in e), statistics.median(f["tot"] / f["v375"] for f in e)))
        e = [f for f in e0 if f["zen"] < 30]; g = [f for f in e0 if f["zen"] >= 45]
        if e and g:
            print("  nadir(<30) n=%d: %.2f / total %.2f    borde(>=45) n=%d: %.2f / total %.2f" % (
                len(e), statistics.median(f["pub"] / f["v375"] for f in e), statistics.median(f["tot"] / f["v375"] for f in e),
                len(g), statistics.median(f["pub"] / f["v375"] for f in g), statistics.median(f["tot"] / f["v375"] for f in g)))


if __name__ == "__main__":
    main()
