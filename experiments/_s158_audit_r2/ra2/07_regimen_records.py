# -*- coding: utf-8 -*-
"""RA2 (S158 r2), H3: con que sha de codigo y cuando se procesaron los records de 2025 y de 2026 (los 11 Tier A).
Pregunta 1: si hubiera un regimen anterior a K en los datos, apareceria otro sha con processed_utc anterior al 2026-10-18.
Pregunta 2: si el campo no existiera, saldria '?' y no un sha."""
import json, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2"
TIER = ["Lascar","Chaiten","PuyehueCordonCaulle","Lastarria","Villarrica","NevadosDeChillan","Isluga","Copahue","PlanchonPeteroa","Llaima","Tupungatito"]
tot = collections.Counter()
for v in TIER:
    c = collections.Counter()
    for r in json.load(open(f"{WT}/data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
        d = r["datetime_utc"]
        tramo = "2025" if d < "2026" else ("2026 hasta 09-17" if d < "2026-09-18" else "2026 desde 09-18")
        c[(tramo, (r.get("regimen") or {}).get("codigo_sha", "?")[:8], (r.get("processed_utc") or "")[:10] >= "2026-10-18")] += 1
    tot.update(c)
    print(v, sorted(c.items()))
print("\nTOTAL 11 volcanes (tramo, sha, procesado desde 2026-10-18):")
for k, n in sorted(tot.items()): print(" ", k, n)
