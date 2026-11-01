"""S163 H3, segunda vara: lo que GitHub Pages sirve HOY al operador, no lo que hay en main.

Baja de https://mendozavolcanic.github.io/VRP-chile/ el index.html desplegado y, para los 11 Tier A, el JSON completo
(`<vol>.json`) y la ventana reciente con que arranca el tablero (`<vol>_recent.json`, S120). Clasifica cada record con
las mismas dos varas de censo_h3.py (marca de régimen y huella del Test 1) y corre el predicado del tablero con node
sobre el index.html desplegado. Sólo lectura; los archivos bajados van al temporal y no se commitean.
Uso: python -I pages_h3.py
"""
import collections
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_h3 as c  # noqa: E402  (configura stdout utf-8 e importa banco_paridad)

BASE = "https://mendozavolcanic.github.io/VRP-chile/"
TMP = Path(os.environ.get("TMP", "/tmp")) / "h3_pages"
TMP.mkdir(parents=True, exist_ok=True)


def bajar(rel):
    destino = TMP / rel.replace("/", "_")
    with urllib.request.urlopen(BASE + rel, timeout=120) as r:
        destino.write_bytes(r.read())
    return destino


def main():
    html = bajar("index.html")
    c.bp.HTML = html
    txt = html.read_text(encoding="utf-8")
    inner = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', txt):
        inner.setdefault(m.group(1), float(m.group(2)))
    print(f"index.html desplegado: {len(txt)} bytes; control del predicado: {c.bp.control_identidad_predicado()}")
    for sufijo in ("", "_recent"):
        filas = []
        for v in c.VOLS:
            recs = json.loads(bajar(f"data/mirova_equivalent/{v}{sufijo}.json").read_text(encoding="utf-8"))
            recs = recs["records"] if isinstance(recs, dict) else recs
            pub = c.bp.correr_node([[r, inner[v]] for r in recs])
            for r, p in zip(recs, pub):
                filas.append((v, r.get("sensor"), r["datetime_utc"], c.regimen_de(r.get("regimen")),
                              c.huella_test1(r), p[4]))
        fechas = sorted(f[2] for f in filas)
        print(f"\n== Pages {sufijo or '(completo)'}: {len(filas)} records, ventana {fechas[0]} a {fechas[-1]} UTC ==")
        print("  régimen:", dict(collections.Counter(f[3] for f in filas)))
        print("  huella Test 1:", sum(f[4] for f in filas), "| publicados:", sum(f[5] for f in filas),
              "| publicados NO-K:", sum(f[5] and f[3] != "K" for f in filas),
              "| publicados con huella:", sum(f[5] and f[4] for f in filas))
        for f in filas:
            if f[0] == "Lascar" and f[2] == "2026-08-22 05:06":
                print(f"  caso S162 {f[1]}: régimen {f[3]}, huella {f[4]}, publica {f[5]}")


if __name__ == "__main__":
    main()
