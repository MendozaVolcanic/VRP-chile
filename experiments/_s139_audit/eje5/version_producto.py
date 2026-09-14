"""product_version (standard/nrt) por mes, 11 Tier A, 2026-01..09, en data/mirova_equivalent.
P1: si todo fuera NRT o standard lo veriamos por mes. P2: records sin campo -> 'SIN_CAMPO', no se asume standard.
Limite: dice que se USO en produccion, no que el Standard exista hoy en LAADS para cada granule (supuesto: si
produccion lo tiene 'standard', LAADS lo sirve)."""
import json, pathlib, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = pathlib.Path(__file__).resolve().parents[3] / "data" / "mirova_equivalent"
TIER = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
c = collections.Counter()
for v in TIER:
    for r in json.load(open(D/f"{v}.json", encoding="utf-8"))["records"]:
        m = (r.get("datetime_utc") or "")[:7]
        if m >= "2026-01": c[(m, r.get("product_version", "SIN_CAMPO"))] += 1
for m in sorted({k[0] for k in c}):
    print(m, {k[1]: n for k, n in c.items() if k[0] == m})
