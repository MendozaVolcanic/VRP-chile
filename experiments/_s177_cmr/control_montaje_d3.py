"""S177: control de montaje de D3 (K-gemelo) contra D2 (via). Solo cuenta pasadas; no lee VRP ni detecciones (candado 11)."""
import collections, glob, json, os, pathlib, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
def pasadas(raiz):
    out = collections.defaultdict(set)
    for d in sorted((R/raiz).glob("trozo-*")):
        js = list(d.glob("*.json"))
        assert len(js) == 1, d
        for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
            out[js[0].stem].add((r["datetime_utc"], r["sensor"]))
    return out
# cobertura y controles de D3
n = collections.Counter(); malos = []; via = collections.Counter()
for d in sorted((R/"s177_d3").glob("log-*")):
    n["logs"] += 1
    for c in (d/"cobertura").glob("*.json"):
        j = json.loads(c.read_text(encoding="utf-8")); n["cob"] += 1
        if n["cob"] == 1: print("claves cobertura:", list(j)[:12])
    tv = d/"controles_via.txt"
    via[tv.read_text(encoding="utf-8").replace(d.name, "")[:0] if False else ("con_txt" if tv.exists() else "sin_txt")] += 1
print(n, via)
print((sorted((R/"s177_d3").glob("log-*"))[0]/"controles_via.txt").read_text(encoding="utf-8"))
d3, d2 = pasadas("s177_d3"), pasadas("s177_d2")
tot = collections.Counter()
for v in sorted(d3):
    dias = {x[0][:10] for x in d3[v]}
    sub = {x for x in d2.get(v, set()) if x[0][:10] in dias}
    solo_k, solo_via = d3[v]-sub, sub-d3[v]
    tot["k"] += len(d3[v]); tot["via"] += len(sub); tot["solo_k"] += len(solo_k); tot["solo_via"] += len(solo_via)
    pors = collections.Counter(("K", s) for _, s in solo_k) + collections.Counter(("via", s) for _, s in solo_via)
    print(f"{v:22s} K {len(d3[v]):5d} via {len(sub):5d} solo_K {len(solo_k):4d} solo_via {len(solo_via):4d} {dict(pors) if pors else ''}")
print(dict(tot))
