# -*- coding: utf-8 -*-
"""F2 M7. Estratifica por VOLCAN (S126: una mediana agrupada invirtio un veredicto) los dos numeros de cabecera
de S150 (V375, abril a agosto): publicacion en negativos limpios B->F y conservacion de positivas que B publica.
Wilson 95 % por celda. Control: la suma por volcan debe dar 829/63/2324 y 988/946."""
import json, sys, io, collections, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (100 * (c - h) / d, 100 * (c + h) / d)
a = collections.defaultdict(collections.Counter)
for ruta in sys.argv[1:]:
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]; x = a[vol]
        if c["lab"] == "neg_limpio": x["neg"] += 1; x["nB"] += c["pub"]; x["nF"] += f["pub"]
        if c["lab"] == "pos" and c["pub"]: x["pB"] += 1; x["pF"] += f["pub"]
tot = collections.Counter()
print("%-20s %6s %14s %14s %18s | %5s %14s" % ("volcan", "neg", "B pub neg", "F pub neg", "F Wilson95", "posB", "F conserva"))
for vol, x in sorted(a.items()):
    tot.update(x); lo, hi = wilson(x["nF"], x["neg"])
    print("%-20s %6d %8d %5.1f%% %8d %5.1f%% [%5.1f,%5.1f] | %5d %8d %5.1f%%" % (vol, x["neg"], x["nB"], 100 * x["nB"] / max(x["neg"], 1), x["nF"],
          100 * x["nF"] / max(x["neg"], 1), lo, hi, x["pB"], x["pF"], 100 * x["pF"] / max(x["pB"], 1)))
print("TOTAL neg %d B %d F %d | posB %d F %d" % (tot["neg"], tot["nB"], tot["nF"], tot["pB"], tot["pF"]))
