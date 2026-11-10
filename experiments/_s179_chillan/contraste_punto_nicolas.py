"""S179: nuestros píxeles calientes de Chillán contra el punto que dio Nicolás (2026-11-10).

POR QUÉ: geometria_vista.py mostró la zona alertada de VIIRS 375 creciendo hacia el SSO y SO, y Nicolás veía una colada
al SE. Nicolás corrigió: la colada va al SO, y dio el punto lat -36.86730944665678, lon -71.37916685099893. Se mide la
distancia y el rumbo, desde ese punto, del píxel más caliente y del más lejano de cada pasada de VIIRS 375 publicada,
por quincena, en todas las pasadas y sólo en las casi verticales (cenit < 35°, donde mirar de lado no corre los píxeles).

Entrada: pasadas.json de comparar_chillan.py, producción de main y los trozos de la vía (igual que geometria_vista.py).
Uso, desde un worktree de main:  python <este script> --pasadas <pasadas.json> --via <carpeta de trozos>
Pregunta 1 del instrumento: se imprime n por grupo; sin píxeles con posición no hay filas. Pregunta 2: el punto del yaml
se mide con la misma función como control (su distancia al punto de Nicolás se imprime y se puede comprobar a mano).
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
PUNTO = (-36.86730944665678, -71.37916685099893)   # Nicolás, 2026-11-10
YAML = (-36.863, -71.377)
FOCOS = {"prod": (-36.86665, -71.38112), "via": (-36.86529, -71.37998)}   # de comparar_chillan.py


def dist_rumbo(lat, lon, ref=PUNTO):
    e = (lon - ref[1]) * 111.32 * math.cos(math.radians(ref[0]))
    n = (lat - ref[0]) * 111.32
    return math.hypot(e, n), (math.degrees(math.atan2(e, n)) + 360) % 360


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

    d, r = dist_rumbo(*YAML)
    print(f"Control: punto del yaml a {d:.3f} km, rumbo {r:.0f}° del punto de Nicolás")
    for nombre, (la, lo) in FOCOS.items():
        d, r = dist_rumbo(la, lo)
        print(f"Foco {nombre} (mediana del píxel más caliente) a {d:.3f} km, rumbo {r:.0f}° del punto de Nicolás")

    for nombre, full in (("prod", prod), ("via", via)):
        grupos = collections.defaultdict(list)
        for f in F:
            if f["sensor"] != "VIIRS375" or not f[nombre] or not f[nombre]["pub"]:
                continue
            rec = full.get((f[nombre]["sat"], f["utc"])) or {}
            px = [p for p in rec.get("anomaly_pixels") or [] if p.get("lat") is not None]
            z = rec.get("sensor_zenith_deg")
            if not px or z is None:
                continue
            cal = max(px, key=lambda p: p.get("bt_k") or 0)
            dc, rc = dist_rumbo(cal["lat"], cal["lon"])
            dr = [dist_rumbo(p["lat"], p["lon"]) for p in px]
            dl, rl = max(dr)
            dia = int(f["utc"][8:10])
            q = f["utc"][:7] + ("-01a15" if dia <= 15 else "-16a31")
            for corte in ("todas", "cenit<35") if z < 35 else ("todas",):
                grupos[(corte, q)].append((dc, rc, dl, rl, len(px)))
        print(f"== {nombre}, VIIRS 375, desde el punto de Nicolás")
        for (corte, q), l in sorted(grupos.items()):
            print(f"   {corte:8s} {q}: n {len(l):2d} | píxel más caliente med {statistics.median(x[0] for x in l):.2f} km "
                  f"[{min(x[0] for x in l):.2f} a {max(x[0] for x in l):.2f}] | píxel más lejano med "
                  f"{statistics.median(x[2] for x in l):.2f} km, rumbo med {statistics.median(x[3] for x in l):.0f}° "
                  f"[{min(x[3] for x in l):.0f} a {max(x[3] for x in l):.0f}] | píxeles {statistics.median(x[4] for x in l):.0f}")


if __name__ == "__main__":
    main()
