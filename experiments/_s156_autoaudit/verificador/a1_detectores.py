"""A1: conteo propio de records por marca codigo_sha alrededor de la frontera 2026-09-18."""
import json, os, sys
from collections import Counter, defaultdict
W = sys.argv[1]
VOLS = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
FR = "2026-09-18"
c = Counter(); sinmarca_k = Counter(); primero_sha = {}; ultimo_sin = {}
shas = Counter(); claves_rara = Counter()
for v in VOLS:
    for r in json.load(open(os.path.join(W, "data/mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc") or ""
        reg = r.get("regimen")
        sha = (reg or {}).get("codigo_sha")
        if reg is not None and not sha: claves_rara["regimen sin codigo_sha"] += 1
        s = r.get("sensor", "")
        if sha:
            shas[sha[:8]] += 1
            primero_sha[s] = min(primero_sha.get(s, "9"), dt)
        else:
            ultimo_sin[s] = max(ultimo_sin.get(s, "0"), dt)
        if not ("2026-08-20" <= dt[:10] <= "2026-10-19"): continue
        noche = "K" if dt[:10] >= FR else "C0"
        c[(noche, "sha" if sha else "sin")] += 1
        if noche == "K" and not sha: sinmarca_k[(v, s)] += 1
        if noche == "C0" and sha: claves_rara[("K en C0", v, s, dt)] += 1
print("ventana 2026-08-20..2026-10-19:", dict(c))
print("sin_marca en noche K por (vol, sensor):", dict(sinmarca_k), "total", sum(sinmarca_k.values()))
print("primer record con sha por sensor:", primero_sha)
print("ultimo record sin sha por sensor:", ultimo_sin)
print("shas:", dict(shas))
print("rarezas:", dict(claves_rara))
