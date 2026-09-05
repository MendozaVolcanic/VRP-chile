# -*- coding: utf-8 -*-
"""F2/01 - De donde viene el 14% de desacuerdo nombre-vs-acquisition_utc.
Si eligiera mal el timestamp, emparejaria TIF con pasadas equivocadas y todo F2
seria basura. Control: caracterizo el desacuerdo por variante (_lm vs last) y
por sensor, y miro casos concretos."""
import csv, io, os, re, sys, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RE_FN = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]+)(_lm)?\.tif$")
rows = list(csv.DictReader(open(os.path.join(AQUI, "index.csv"), encoding="utf-8")))

por = {}
ejemplos = []
for r in rows:
    a = (r["acquisition_utc"] or "").strip()
    p = r["tif_path"].replace("\\", "/")
    m = RE_FN.search(p)
    if not m: continue
    var = "lm" if m.group(4) else "last"
    tfn = dt.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    if not a:
        k = (var, r["sensor"], "sin_acq"); por[k] = por.get(k, 0) + 1; continue
    ta = dt.datetime.fromisoformat(a.replace("Z", "+00:00"))
    if ta.tzinfo is None: ta = ta.replace(tzinfo=dt.timezone.utc)
    d = abs((tfn - ta).total_seconds())
    k = (var, r["sensor"], "igual" if d <= 60 else "distinto")
    por[k] = por.get(k, 0) + 1
    if d > 60 and len(ejemplos) < 8:
        ejemplos.append((r["volcano"], r["sensor"], p.split("/")[-1], a, r["last_modified_utc"], round(d/3600, 2)))

print("variante | sensor | acuerdo -> n")
for k in sorted(por): print("  %-5s %-9s %-9s %6d" % (k[0], k[1], k[2], por[k]))
print("\nejemplos de DESACUERDO (>60 s):")
print("%-22s %-9s %-34s %-22s %-22s %s" % ("volcan","sensor","archivo","acquisition_utc","last_modified_utc","dif_h"))
for e in ejemplos: print("%-22s %-9s %-34s %-22s %-22s %s" % e)
