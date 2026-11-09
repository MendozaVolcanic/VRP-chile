"""S177: de las pasadas V750 solo en la via, cuales estan en los logs de K y que dice el log. No lee VRP (candado 11)."""
import datetime as dt, glob, pathlib, re, sys, io, collections, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
def pas(raiz):
    o = collections.defaultdict(dict)
    for d in sorted((R/raiz).glob("trozo-*")):
        js = list(d.glob("*.json"))
        for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
            o[js[0].stem][(r["datetime_utc"], r["sensor"])] = r.get("granule")
    return o
d3, d2 = pas("s177_d3"), pas("s177_d2")
def t(s): return dt.datetime.strptime(s, "%Y-%m-%d %H:%M")
res = collections.Counter(); filas = []
for v in sorted(d3):
    dias = {x[0][:10] for x in d3[v]}
    for k in sorted(set(x for x in d2[v] if x[0][:10] in dias) - set(d3[v])):
        g = d2[v][k]
        vec = sorted((abs((t(x[0]) - t(k[0])).total_seconds())/60, x[0]) for x in d3[v] if x[1] == k[1] and abs((t(x[0]) - t(k[0])).total_seconds()) <= 1800)
        ag = re.search(r"A\d{7}\.\d{4}", g or "")
        ag = ag.group(0) if ag else None
        lk = [l.strip()[:150] for f in glob.glob(str(R/"s177_d3"/f"log-{v}-*"/"pipeline.log")) for l in open(f, encoding="utf-8", errors="replace") if ag and ag in l]
        cl = "vecino_6min" if vec and vec[0][0] <= 6 else ("log_K_menciona" if lk else "K_sin_rastro")
        res[cl] += 1
        filas.append((cl, v, k[0], k[1], g[:45] if g else None, vec[:1], lk[:2]))
print(res)
for f in filas: print(f)
