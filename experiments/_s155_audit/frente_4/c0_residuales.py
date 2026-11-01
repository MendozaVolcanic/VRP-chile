# -*- coding: utf-8 -*-
"""Lista los records con datetime_utc dentro de la ventana declarada como reprocesada con K
(2026-09-18 a 2026-10-18) cuyo processed_utc es ANTERIOR al merge de #850 (2026-10-18 09:57:30 UTC),
o sea que siguen siendo del detector C0. P1: si el reproceso hubiera cubierto todo, la lista sale
vacia; si no, la lista los nombra. P2: control: la misma consulta con la frontera movida al
2026-01-01 debe devolver 0 (todo se proceso despues); con la frontera al 2027 debe devolver todos."""
import json, sys, io
from pathlib import Path
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
TIER_A = ["Lascar","Lastarria","Isluga","NevadosDeChillan","Llaima","Villarrica","Chaiten",
          "PlanchonPeteroa","Copahue","Tupungatito","PuyehueCordonCaulle"]
def correr(frontera, listar=False):
    tot = 0; res = []
    for v in TIER_A:
        for r in json.load(open(ROOT/"data/mirova_equivalent"/f"{v}.json", encoding="utf-8"))["records"]:
            dt = r.get("datetime_utc","")
            if "2026-09-18" <= dt[:10] <= "2026-10-18":
                tot += 1
                if (r.get("processed_utc") or "") < frontera:
                    res.append((v, dt, r["sensor"], r.get("granule"), r.get("processed_utc"), r.get("vrp_mw"),
                                r.get("distance_class"), (r.get("primary_cluster") or {}).get("vrp_mw")))
    return tot, res
tot, res = correr("2026-10-18T09:57:30")
print("records en ventana", tot, "| C0 residuales", len(res))
print(Counter((x[0], x[2]) for x in res))
for x in sorted(res): print(x)
print("control frontera 2026-01-01:", len(correr("2026-01-01")[1]), "| frontera 2027:", len(correr("2027")[1]), "de", tot)
