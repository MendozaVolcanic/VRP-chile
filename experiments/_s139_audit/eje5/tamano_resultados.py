"""Tamano de data/mirova_equivalent para los 11 Tier A y bytes por record, para estimar lo que ocupa un brazo
en 2026-01-01..2026-09-12. P1: si los JSON estuvieran truncados, bytes/record caeria fuera de rango entre volcanes.
P2: volcan sin archivo = SIN_DATO. Supuesto: bytes/record del brazo ~ produccion (no verificado: flags cambian
anomaly_pixels y por tanto el tamano)."""
import json, os, pathlib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = pathlib.Path(__file__).resolve().parents[3] / "data" / "mirova_equivalent"
TIER = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
tb = tr = t26 = 0
for v in TIER:
    p = D / f"{v}.json"
    if not p.exists(): print(v, "SIN_DATO"); continue
    b = p.stat().st_size; recs = json.load(open(p, encoding="utf-8"))["records"]
    n26 = sum(1 for r in recs if (r.get("datetime_utc") or "") >= "2026-01-01")
    tb += b; tr += len(recs); t26 += n26
    print(f"{v:20s} {b/1e6:6.1f} MB  records={len(recs)}  2026={n26}  bytes/record={b/len(recs):.0f}")
print(f"TOTAL 11 Tier A: {tb/1e6:.0f} MB, {tr} records, {t26} de 2026; brazo 2026-01..09 estimado {tb*t26/tr/1e6:.0f} MB")
