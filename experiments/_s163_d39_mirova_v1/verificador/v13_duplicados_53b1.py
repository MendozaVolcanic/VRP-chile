"""v13_duplicados_53b1.py (A1, complemento): las 1.565 llaves repetidas que dejo 53b1e6d3c0: difieren las dos copias?
Y cual copia sobrevivio en main hoy (dedup posterior del scraper, keep='last')?"""
import csv, io, subprocess, urllib.request, gzip, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
def raw(sha):
    req = urllib.request.Request(f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}", headers={"Accept-Encoding": "gzip"})
    r = urllib.request.urlopen(req, timeout=60); d = r.read()
    return (gzip.decompress(d) if r.headers.get("Content-Encoding") == "gzip" else d).decode("utf-8")
def k(f): return ((f["timestamp"] or "").strip(), f["Volcan"], f["Sensor"])
h = list(csv.DictReader(io.StringIO(raw("53b1e6d3c0"))))
m = {k(f): f for f in csv.DictReader(io.StringIO(subprocess.run(["git","-C",CLON,"show",f"main:{RUTA}"],capture_output=True,check=True).stdout.decode("utf-8")))}
por = collections.defaultdict(list)
for f in h: por[k(f)].append(f)
dup = {kk: v for kk, v in por.items() if len(v) > 1}
print("llaves repetidas en 53b1e6d3c0:", len(dup), "| max copias:", max(len(v) for v in dup.values()))
dif = collections.Counter(); ej = {}
sobrev = collections.Counter()
for kk, copias in dup.items():
    cols = [c for c in copias[0] if len({(x.get(c) or "") for x in copias}) > 1]
    dif[tuple(cols)] += 1; ej.setdefault(tuple(cols), (kk, [(c, [x.get(c) for x in copias]) for c in cols][:3]))
    if kk in m:
        iguales = [i for i, x in enumerate(copias) if all((x.get(c) or "") == (m[kk].get(c) or "") for c in x)]
        sobrev["igual a alguna copia" if iguales else "distinta de todas las copias"] += 1
    else:
        sobrev["ausente hoy"] += 1
print("campos en que difieren las copias:"); [print("  ", n, d, ej[d]) for d, n in dif.most_common(8)]
print("hoy en main:", dict(sobrev))
