"""T7: lo que el frontend lee contra lo que hay en origin/main.
index.html:975-977 lee data/mirova_equivalent/<V>_recent.json y data/mirova/<V>.json.
Pregunta 1: si _recent.json o data/mirova/<V>.json quedaran congelados, el max datetime_utc se quedaria atras del JSON completo. Si.
Pregunta 2: si el archivo no existiera, se imprime FALTA (no cero silencioso).
Control positivo: el JSON completo (que el NRT si escribe) debe tener max fecha de hoy.
Ventana: estado de origin/main al 2026-09-13 11:49 UTC. Denominador: 11 Tier A.
Ademas: records sin primary_cluster (fallback distinto entre index/mosaico y diario) y su distance_class.
"""
import json, subprocess, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TIER_A = ["Lastarria", "Lascar", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten",
          "PlanchonPeteroa", "Tupungatito", "Copahue", "PuyehueCordonCaulle"]
def show(path):
    p = subprocess.run(["git", "show", f"origin/main:{path}"], capture_output=True)
    if p.returncode != 0: return None
    return json.loads(p.stdout)
def maxdt(recs, key="datetime_utc"):
    v = [r.get(key) or r.get("Fecha_Satelite_UTC") for r in recs if r.get(key) or r.get("Fecha_Satelite_UTC")]
    return max(v) if v else None
print("volcan | full N/max | _recent N/max | data/mirova N/max/updated | sin pc (N, dist_class) ")
tot_nopc = Counter()
for v in TIER_A:
    full = show(f"data/mirova_equivalent/{v}.json")
    rec = show(f"data/mirova_equivalent/{v}_recent.json")
    mir = show(f"data/mirova/{v}.json")
    fr = full["records"]
    nopc = [r for r in fr if not r.get("primary_cluster")]
    dc = Counter(r.get("distance_class") for r in nopc)
    tot_nopc.update(dc)
    s_rec = f"{len(rec['records'])}/{maxdt(rec['records'])}" if rec else "FALTA"
    if mir:
        mr = mir.get("records", [])
        s_mir = f"{len(mr)}/{maxdt(mr)}/{mir.get('updated') or mir.get('generated') or list(mir.keys())[:4]}"
    else:
        s_mir = "FALTA"
    print(f"{v} | {len(fr)}/{maxdt(fr)} | {s_rec} | {s_mir} | {len(nopc)} {dict(dc)}")
print("TOTAL records sin primary_cluster en 11 Tier A:", sum(tot_nopc.values()), dict(tot_nopc))
mir = show("data/mirova/Villarrica.json")
if mir:
    print("claves data/mirova/Villarrica.json:", list(mir.keys())[:8])
    print("ejemplo record:", mir["records"][-1] if mir.get("records") else None)
