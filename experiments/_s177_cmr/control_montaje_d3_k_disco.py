"""S177: las pasadas V750 solo en la via (contra K-gemelo) estan en K de disco? Solo claves; no lee VRP (candado 11)."""
import collections, json, pathlib, subprocess, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["MSYS_NO_PATHCONV"] = "1"
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
def pas(raiz):
    o = collections.defaultdict(set)
    for d in sorted((R/raiz).glob("trozo-*")):
        js = list(d.glob("*.json"))
        for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
            o[js[0].stem].add((r["datetime_utc"], r["sensor"]))
    return o
def disco(v):
    t = subprocess.run(["git", "show", f"origin/main:data/mirova_equivalent/{v}.json"], capture_output=True).stdout
    return {(r["datetime_utc"], r["sensor"]) for r in json.loads(t)["records"]}
d3, d2 = pas("s177_d3"), pas("s177_d2")
tot = collections.Counter()
for v in sorted(d3):
    dias = {x[0][:10] for x in d3[v]}
    sub = {x for x in d2[v] if x[0][:10] in dias}
    k = {x for x in disco(v) if x[0][:10] in dias}
    sv = sub - d3[v]
    tot["solo_via_vs_gemelo"] += len(sv); tot["de_esas_en_K_disco"] += len(sv & k); tot["de_esas_no_en_K_disco"] += len(sv - k)
    tot["via_sin_K_disco(sobra_en_via)"] += len(sub - k); tot["K_disco_sin_gemelo"] += len(k - d3[v]); tot["gemelo_sin_K_disco"] += len(d3[v] - k); tot["K_disco"] += len(k); tot["gemelo"] += len(d3[v])
    for x in sorted(k - d3[v])[:3]: print("K_disco sin gemelo:", v, x, "en via" if x in sub else "no en via")
    for x in sorted(d3[v] - k)[:2]: print("gemelo sin K_disco:", v, x)
print(dict(tot))
