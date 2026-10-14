import json, sys, collections, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BR = ["C0","T0","E","B","F","J","K","KE","KET"]
print("brazo sensor fase | alertas<1MW perdidas (de n) | pub en neg_limpio (de n) | pub en 'otras' etiquetas")
for n in BR:
    par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
    T = json.load(open("tmp/t_%s_%s.json" % par, encoding="utf-8"))["pasadas"]
    tot = collections.Counter()
    for s in ("MODIS","VIIRS375","VIIRS750"):
        for f in ("reposo","actividad"):
            ks = [k for k,v in T.items() if k.split("|")[1]==s and lado in v and ((k.split("|")[2][:10] >= "2026-09-28") == (f=="actividad"))]
            pos = [k for k in ks if T[k][lado]["lab"]=="pos" and (T[k][lado]["vrp_ref"] or 0) < 1]
            perd = [k for k in pos if not T[k][lado]["pub"]]
            neg = [k for k in ks if T[k][lado]["lab"]=="neg_limpio"]
            fp = [k for k in neg if T[k][lado]["pub"]]
            otras = collections.Counter(T[k][lado]["lab"] for k in ks if T[k][lado]["pub"] and T[k][lado]["lab"] not in ("pos","neg_limpio"))
            tot["perd"] += len(perd); tot["fp"] += len(fp)
            print("%-4s %-8s %-9s | %d de %d %s | %d de %d | %s" % (n, s, f, len(perd), len(pos), [k.split("|")[2] for k in perd], len(fp), len(neg), dict(otras)))
    print("   %s TOTAL perdidas<1MW %d + pub neg_limpio %d = %d" % (n, tot["perd"], tot["fp"], tot["perd"]+tot["fp"]))
labs = collections.Counter(v["control"]["lab"] for v in json.load(open("tmp/t_C0_B.json",encoding="utf-8"))["pasadas"].values() if "control" in v)
print("etiquetas C0:", labs)
