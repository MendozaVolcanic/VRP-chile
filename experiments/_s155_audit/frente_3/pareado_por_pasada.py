"""F3: el descenso de la razón por noche bajo K, ¿es magnitud por pasada o menos pasadas que publican?
Mismas pasadas (volcán, datetime_utc, sensor) en K (mirova_equivalent) y C0 (sombra experimental_v2),
desde 2026-10-02 (inicio de la sombra) hasta 2026-10-18, predicado 'dash' del auto-audit.
P1: si K sólo quitara pasadas, la mediana K/C0 en pasadas donde ambos publican sería 1. P2: n impreso."""
import json, os, sys, statistics
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa
from pareado_k_vs_sombra import dash  # noqa  (mismo directorio)
res = {}
for vol in aw.VOLS:
    som = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(os.path.join(ROOT, "data", "experimental_v2", vol + ".json"), encoding="utf-8"))["records"]}
    prod = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]}
    c = Counter(); rat = []
    for k in set(som) & set(prod):
        if k[0][:10] < "2026-09-18": continue
        a, b = dash(prod[k], vol), dash(som[k], vol)
        c[("K" if a > 0 else "-") + ("C0" if b > 0 else "-")] += 1
        if a > 0 and b > 0: rat.append(a / b)
    res[vol] = {"conteo": dict(c), "n_ambos": len(rat), "med_K_sobre_C0": round(statistics.median(rat), 3) if rat else "SIN DATO"}
    print(vol, res[vol])
json.dump(res, open(os.path.join(os.path.dirname(__file__), "pareado_por_pasada.json"), "w", encoding="utf-8"), indent=1)
