# -*- coding: utf-8 -*-
"""COB 07 (S159). Conteo global (cabecera CMR-Hits, page_size=1) de granulos L1B y GEO por dia y producto, caja de Chile
continental (lon -76..-66, lat -56..-17), dias 2026-10-12 a 2026-10-21, Standard y NRT. Independiente de la caja de cada
volcan: sirve para confirmar R2-13 (CMR sin los dias 18-19 oct) y VB-1 (L1B con mas granulos que su GEO).
Pregunta 1: si CMR no tuviera datos de ningun dia, los dias de control (12, 14, 17, 21) mostrarian 0 tambien; no
lo hacen (control positivo). Pregunta 2: el conteo viene de la cabecera CMR-Hits, no de una pagina recortada.
Denominador: el dia UTC completo [00:00, 24:00) sobre la caja; incluye granulos diurnos."""
import sys, io, json, time, urllib.parse, urllib.request
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob")
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
BBOX = "-76,-56,-66,-17"
PROD = [("MOD021KM", "6.1", "MOD03", "6.1"), ("MYD021KM", "6.1", "MYD03", "6.1"), ("VNP02IMG", "2", "VNP03IMG", "2"),
        ("VNP02MOD", "2", "VNP03MOD", "2"), ("VJ102IMG", "2.1", "VJ103IMG", "2.1"), ("VJ202IMG", "2.1", "VJ203IMG", "2.1"),
        ("VJ102MOD", "2.1", "VJ103MOD", "2.1"), ("VJ202MOD", "2.1", "VJ203MOD", "2.1")]
NRT = {"MOD021KM": ("MOD021KM", "6.1NRT", "MOD03", "6.1NRT"), "MYD021KM": ("MYD021KM", "6.1NRT", "MYD03", "6.1NRT")}
DIAS = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21"]
cache = HERE / "_cache_hits.json"
C = json.loads(cache.read_text()) if cache.exists() else {}
last = [0.0]

def hits(sn, ver, dia):
    k = f"{sn}|{ver}|{dia}"
    if k in C: return C[k]
    y, m, d = map(int, dia.split("-"))
    import datetime as dt
    t0 = dt.datetime(y, m, d); t1 = t0 + dt.timedelta(days=1)
    q = {"short_name": sn, "version": ver, "bounding_box": BBOX, "page_size": "1",
         "temporal": t0.strftime("%Y-%m-%dT%H:%M:%SZ") + "," + (t1 - dt.timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    w = 1.0 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    for i in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(BASE + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90)
            n = int(r.headers["CMR-Hits"]); break
        except Exception:
            if i == 3: raise
            time.sleep(3 * (i + 1))
    last[0] = time.time(); C[k] = n; cache.write_text(json.dumps(C)); return n

rows = []
for l1, v1, g1, v2 in PROD:
    for dia in DIAS:
        a = hits(l1, v1, dia); b = hits(g1, v2, dia)
        row = [l1, dia, "std", a, b]
        rows.append(row)
        if l1 in NRT:
            n = NRT[l1]; rows.append([l1, dia, "nrt", hits(n[0], n[1], dia), hits(n[2], n[3], dia)])
        # VIIRS NRT
for sn, g in (("VNP02IMG_NRT", "VNP03IMG_NRT"), ("VNP02MOD_NRT", "VNP03MOD_NRT"), ("VJ102IMG_NRT", "VJ103IMG_NRT"), ("VJ202IMG_NRT", "VJ203IMG_NRT")):
    for dia in DIAS:
        ver = "2.1" if sn.startswith("VJ") else "2"
        rows.append([sn, dia, "nrt", hits(sn, ver, dia), hits(g, ver, dia)])
print("producto            dia         tipo  L1B   GEO   (L1B sin GEO = L1B - GEO)")
for r in sorted(rows, key=lambda r: (r[0], r[2], r[1])):
    print(f"{r[0]:14s} {r[1]} {r[2]:4s} {r[3]:5d} {r[4]:5d}  {r[3]-r[4]:+d}")
