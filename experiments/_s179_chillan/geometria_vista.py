"""S179: ¿hacia dónde crece la zona caliente de Chillán, y cuánto de eso es la geometría de observación?

POR QUÉ: comparar_chillan.py mostró la zona alertada alargándose hacia el SO, y Nicolás ve una colada hacia el SE. Si el
corrimiento fuera un efecto de mirar de lado (relieve de 3.200 m, píxel oblicuo), cambiaría de signo con el lado desde
el que mira el satélite y casi desaparecería mirando en vertical. Se mide: (1) centroide de los píxeles alertados
respecto del foco, por lado del satélite y por cenit; (2) sólo pasadas casi verticales (cenit < 35°), por quincena,
alcance y rumbo del píxel más lejano; (3) la distancia de la tabla de MIROVA por quincena (sin rumbo: la tabla no lo trae).

Entrada: pasadas.json de comparar_chillan.py, producción de main y los trozos de la vía.
Uso, desde un worktree de main:  python <este script> --pasadas <pasadas.json> --via <carpeta de trozos>
Pregunta 1 del instrumento: si los píxeles no tuvieran posición, no habría centroides (se imprime n por grupo). Pregunta
2: el control es el propio corte por lado del satélite: un instrumento muerto daría lo mismo en los dos lados.
"""
import argparse
import collections
import glob
import io
import json
import math
import statistics
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
LAT0, LON0 = -36.863, -71.377
FOCOS = {"prod": (-36.86665, -71.38112), "via": (-36.86529, -71.37998)}   # de comparar_chillan.py (mediana del más caliente)


def enu(lat, lon):
    return (lon - LON0) * 111.32 * math.cos(math.radians(LAT0)), (lat - LAT0) * 111.32


def rumbo(e, n):
    return (math.degrees(math.atan2(e, n)) + 360) % 360


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasadas", required=True)
    ap.add_argument("--via", required=True)
    a = ap.parse_args()
    F = json.loads(Path(a.pasadas).read_text(encoding="utf-8"))
    prod = {(r["sensor"], r["datetime_utc"]): r for r in
            json.loads(Path("data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]}
    via = {}
    for f in glob.glob(str(Path(a.via) / "*" / "NevadosDeChillan.json")):
        for r in json.loads(Path(f).read_text(encoding="utf-8"))["records"]:
            via[(r["sensor"], r["datetime_utc"])] = r

    for nombre, full in (("prod", prod), ("via", via)):
        fe, fn = enu(*FOCOS[nombre])
        lados, quinc = collections.defaultdict(list), collections.defaultdict(list)
        for f in F:
            if f["sensor"] != "VIIRS375" or not f[nombre] or not f[nombre]["pub"]:
                continue
            r = full.get((f[nombre]["sat"], f["utc"])) or {}
            px = [p for p in r.get("anomaly_pixels") or [] if p.get("lat") is not None]
            az, z = r.get("sensor_azimuth_deg"), r.get("sensor_zenith_deg")
            if len(px) < 2 or az is None or z is None:
                continue
            pts = [(enu(p["lat"], p["lon"])[0] - fe, enu(p["lat"], p["lon"])[1] - fn) for p in px]
            ce, cn = statistics.mean(t[0] for t in pts), statistics.mean(t[1] for t in pts)
            # azimut del satélite visto desde el píxel: menos de 180° = satélite al este
            lados[("sat al E" if az % 360 < 180 else "sat al O", "cenit<35" if z < 35 else "cenit>=35")].append((ce, cn, len(px)))
            if z < 35:
                lejos = max(pts, key=lambda t: math.hypot(*t))
                d = int(f["utc"][8:10])
                quinc[f["utc"][:7] + ("-01a15" if d <= 15 else "-16a31")].append(
                    (ce, cn, len(px), math.hypot(*lejos), round(rumbo(*lejos))))
        print(f"== {nombre}, VIIRS 375: centroide de los píxeles alertados respecto del foco, por lado del satélite (km)")
        for k, l in sorted(lados.items()):
            print(f"   {k[0]:8s} {k[1]:9s} n {len(l):2d} | E {statistics.median(x[0] for x in l):+.2f} "
                  f"N {statistics.median(x[1] for x in l):+.2f} | píxeles {statistics.median(x[2] for x in l):.0f}")
        print(f"   sólo cenit < 35°, por quincena:")
        for q, l in sorted(quinc.items()):
            print(f"   {q}: n {len(l):2d} | centroide E {statistics.median(x[0] for x in l):+.2f} N "
                  f"{statistics.median(x[1] for x in l):+.2f} | píxeles {statistics.median(x[2] for x in l):.0f} | "
                  f"píxel más lejano {statistics.median(x[3] for x in l):.2f} km, rumbos {sorted(x[4] for x in l)}")

    print("== Distancia de la tabla de MIROVA (Distancia_km) y la nuestra (vía, final_hotspot_dist_km), por quincena")
    g, gv = collections.defaultdict(list), collections.defaultdict(list)
    for f in F:
        if f["mirova_dist_tabla"] is None:
            continue
        d = int(f["utc"][8:10])
        q = (f["sensor"], f["utc"][:7] + ("-01a15" if d <= 15 else "-16a31"))
        g[q].append(f["mirova_dist_tabla"])
        if f["via"] and f["via"]["pub"] and f["via"]["dist_final"] is not None:
            gv[q].append(f["via"]["dist_final"])
    for k in sorted(g):
        v = gv.get(k, [])
        print(f"   {k[0]:9s} {k[1]}: MIROVA med {statistics.median(g[k]):.2f} [{min(g[k]):.2f} a {max(g[k]):.2f}] n {len(g[k]):2d}"
              f" | vía med {statistics.median(v) if v else float('nan'):.2f} n {len(v)}")


if __name__ == "__main__":
    main()
