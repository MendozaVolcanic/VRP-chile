"""S159: comprobar H3 (hueco del 17 al 20 de octubre en Standard, NRT presente) por dia, en CMR publico,
y mirar que product_version tienen nuestros records VIIRS/MODIS esos dias (datos de origin/main).

Uso: python -I cmr_hueco_17_20_oct.py <arbol_origin_main>
Pregunta 1: si el hueco no existiera, Standard daria conteos parecidos a NRT esos dias.
Pregunta 2: control positivo: el 14 de octubre (fuera del hueco) Standard debe dar > 0. Error de red -> ERROR, no 0.
"""
import json, sys, io, time, urllib.request, urllib.parse, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
BBOX = "-76,-46,-66,-17"
PARES = [("VNP02IMG", "2"), ("VNP02IMG_NRT", "2"), ("VJ102IMG", "2.1"), ("VJ102IMG_NRT", "2.1"),
         ("MOD021KM", "6.1"), ("MOD021KM", "6.1NRT")]
DIAS = ["2026-10-14", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21"]
print("dia        " + " ".join(f"{s}v{v}"[:16].rjust(16) for s, v in PARES))
for d in DIAS:
    fila = []
    for s, v in PARES:
        q = {"short_name": s, "version": v, "bounding_box": BBOX,
             "temporal": f"{d}T00:00:00Z,{d}T23:59:59Z", "page_size": 0}
        try:
            req = urllib.request.Request(CMR + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "vrp-audit"})
            with urllib.request.urlopen(req, timeout=60) as r:
                fila.append(r.headers.get("CMR-Hits"))
        except Exception as e:
            fila.append("ERROR")
        time.sleep(1.0)
    print(d, " ".join(str(x).rjust(16) for x in fila))

ARBOL = Path(sys.argv[1]).resolve()
c = collections.Counter()
for p in (ARBOL / "data" / "mirova_equivalent").glob("*.json"):
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        dia = (r.get("datetime_utc") or "")[:10]
        if "2026-10-14" <= dia <= "2026-10-21":
            c[(dia, (r.get("sensor") or "").split("_")[0] + ("_SNPP" if "SNPP" in (r.get("sensor") or "") else ""),
               r.get("product_version"))] += 1
print("\nrecords Tier A de origin/main por (dia, familia, product_version):")
for k in sorted(c):
    print(" ", k, c[k])
