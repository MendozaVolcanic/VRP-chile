"""S177: fechas y sensores de lo que el K-gemelo trae y K de disco no. Solo claves; no lee VRP (candado 11)."""
import collections, json, pathlib, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
c = collections.Counter(); proc = collections.Counter()
for d in sorted((R/"s177_d3").glob("trozo-*")):
    js = list(d.glob("*.json")); v = js[0].stem
    recs = json.loads(js[0].read_text(encoding="utf-8"))["records"]
    t = subprocess.run(["git", "show", f"origin/main:data/mirova_equivalent/{v}.json"], capture_output=True).stdout
    k = {(r["datetime_utc"], r["sensor"]) for r in json.loads(t)["records"]}
    for r in recs:
        if (r["datetime_utc"], r["sensor"]) not in k:
            c[(r["datetime_utc"][:13], r["sensor"])] += 1
for x, n in sorted(c.items()): print(x, n)
print(sum(c.values()))
