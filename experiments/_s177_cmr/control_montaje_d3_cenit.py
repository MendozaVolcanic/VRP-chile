"""S177: angulo de vista de las pasadas V750 que la via tiene y K no, contra el resto. Solo geometria; no lee VRP (candado 11)."""
import collections, json, pathlib, statistics as st, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
def recs(raiz):
    o = collections.defaultdict(dict)
    for d in sorted((R/raiz).glob("trozo-*")):
        js = list(d.glob("*.json"))
        for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
            o[js[0].stem][(r["datetime_utc"], r["sensor"])] = r
    return o
d3, d2 = recs("s177_d3"), recs("s177_d2")
g = collections.defaultdict(list)
for v in d3:
    dias = {x[0][:10] for x in d3[v]}
    for k, r in d2[v].items():
        if k[0][:10] in dias and k[1].endswith("_750"):
            z = r.get("sensor_zenith_deg")
            if z is None: g["sin_zenit"].append(0); continue
            g["solo_via" if k not in d3[v] else "en_ambos"].append(float(z))
for n, x in g.items():
    if n == "sin_zenit": print(n, len(x)); continue
    x = sorted(x); print(n, "n", len(x), "min", round(x[0],1), "mediana", round(st.median(x),1), "max", round(x[-1],1), "sobre 65:", sum(1 for z in x if z > 65))
