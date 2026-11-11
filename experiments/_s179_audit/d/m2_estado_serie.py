# -*- coding: utf-8 -*-
"""M2 (frente D, S179). Estado de la serie publicada (data/mirova_equivalent/, main 438a60a1e) por familia de sensor
y por detector, para comprobar las cifras y las reglas del plan de reemplazo (#981, 62ccb8830).

Las dos preguntas del instrumento:
1. Si la serie estuviera rota (por ejemplo, MODIS sin records de la via, o K mezclado despues de la via), esta medicion
   lo veria?  Si: cuenta cada record por familia y marca `via_codigo_mirova`, y lista los K posteriores a la primera via.
2. Si el instrumento estuviera muerto, el resultado se veria distinto?  Si: controles al final (45 archivos, 11 Tier A
   con records de la via en MODIS y 0 en VIIRS, porque VIIRS de produccion sigue con K en la base; si el conteo de la via
   en MODIS diera 0 o el de VIIRS diera mas de 0, el script termina con error).

Denominador: todos los records de los 45 JSON de data/mirova_equivalent/ del commit. Ventana: toda la serie.
Uso: python m2_estado_serie.py <carpeta con los 45 JSON> <salida.json>
"""
import json, sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DIR, OUT = Path(sys.argv[1]), sys.argv[2]
TIER_A = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten"]

def fam(s):
    s = str(s or "")
    if s.startswith("MODIS"): return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"

def marca(r):
    v = r.get("via_codigo_mirova")
    return "via" if v is True else ("K" if v is None else f"caida:{v}")

res = {"volcanes": {}}
tot = collections.Counter()
for p in sorted(DIR.glob("*.json")):
    if p.stem.endswith("_recent"): continue
    recs = json.loads(p.read_text(encoding="utf-8"))["records"]
    v = p.stem
    fila = {"n": len(recs), "antes_2025_02_15": sum(1 for r in recs if (r.get("datetime_utc") or "") < "2025-02-15")}
    perfiles = collections.Counter((fam(r.get("sensor")), marca(r), (r.get("regimen") or {}).get("perfil")) for r in recs)
    fila["perfil_por_familia_y_marca"] = {f"{a}|{b}|{c}": n for (a, b, c), n in sorted(perfiles.items(), key=str)}
    for f in ("MODIS", "VIIRS375", "VIIRS750"):
        rf = [r for r in recs if fam(r.get("sensor")) == f]
        c = collections.Counter(marca(r) for r in rf)
        via = sorted(r["datetime_utc"] for r in rf if marca(r) == "via")
        k = sorted(r["datetime_utc"] for r in rf if marca(r) == "K")
        proc_via = sorted(str(r.get("processed_utc")) for r in rf if marca(r) == "via" and r.get("processed_utc"))
        d = {"n": len(rf), "por_marca": dict(c), "primera": min((r["datetime_utc"] for r in rf), default=None),
             "ultima": max((r["datetime_utc"] for r in rf), default=None),
             "primera_via": via[0] if via else None, "ultima_K": k[-1] if k else None,
             "min_processed_utc_via": proc_via[0] if proc_via else None,
             "K_posteriores_a_la_primera_via": [x for x in k if via and x > via[0]],
             "via_hasta_2026_11_02_inclusive": sum(1 for x in via if x[:10] <= "2026-11-02"),
             "K_antes_de_la_primera_via": sum(1 for x in k if via and x < via[0]),
             "pv": dict(collections.Counter(str(r.get("product_version")) for r in rf if (r.get("datetime_utc") or "") >= "2026-10-25"))}
        if v == "Tupungatito":
            d["antes_2026_02_23"] = dict(collections.Counter(marca(r) for r in rf if r["datetime_utc"][:10] < "2026-02-23"))
        fila[f] = d
        for m, n in c.items(): tot[(v in TIER_A, f, m)] += n
    res["volcanes"][v] = fila
res["totales"] = {f"{'TierA' if a else '34'}|{f}|{m}": n for (a, f, m), n in sorted(tot.items(), key=str)}

print("== Totales por grupo, familia y marca ==")
for k, n in res["totales"].items(): print(f"  {k}: {n}")
print("\n== 11 Tier A, MODIS ==")
print(f"{'volcan':22s} {'K':>6s} {'via':>5s} {'caidas':>6s}  primera_via        ultima_K           via<=11-02  K>1a_via  min processed_utc via")
for v in TIER_A:
    m = res["volcanes"][v]["MODIS"]; pm = m["por_marca"]
    caidas = sum(n for k, n in pm.items() if k.startswith("caida"))
    print(f"{v:22s} {pm.get('K',0):6d} {pm.get('via',0):5d} {caidas:6d}  {m['primera_via']}  {m['ultima_K']}  {m['via_hasta_2026_11_02_inclusive']:9d}  {len(m['K_posteriores_a_la_primera_via']):8d}  {m['min_processed_utc_via']}")
    for x in m["K_posteriores_a_la_primera_via"]: print(f"      K posterior a la primera via: {x}")
print("\n== 11 Tier A, VIIRS (K esperado en la base) ==")
for v in TIER_A:
    for f in ("VIIRS375", "VIIRS750"):
        m = res["volcanes"][v][f]
        print(f"  {v:22s} {f}: {m['por_marca']}  primera {m['primera']}  ultima {m['ultima']}")
print("\n== Tupungatito antes del 2026-02-23 (el plan dice 787 MODIS, 1.574 VIIRS 375 y 1.563 VIIRS 750, todos K) ==")
for f in ("MODIS", "VIIRS375", "VIIRS750"): print(f"  {f}: {res['volcanes']['Tupungatito'][f].get('antes_2026_02_23')}")
print("\n== Records anteriores al 2025-02-15 en los 45 archivos ==")
print("  ", sum(x["antes_2025_02_15"] for x in res["volcanes"].values()))
print("\n== Los 34 fuera del NRT: MODIS ==")
c34 = collections.Counter(); rango = []
for v, x in res["volcanes"].items():
    if v in TIER_A: continue
    for m, n in x["MODIS"]["por_marca"].items(): c34[m] += n
    if x["MODIS"]["primera"]: rango.append((x["MODIS"]["primera"], x["MODIS"]["ultima"]))
print("  por marca:", dict(c34), " rango:", min(a for a, _ in rango), "a", max(b for _, b in rango), " volcanes:", len(rango))
print("\n== Perfil (regimen.perfil) de los records, por familia y marca, sumado en los 11 Tier A ==")
pp = collections.Counter()
for v in TIER_A:
    for k, n in res["volcanes"][v]["perfil_por_familia_y_marca"].items(): pp[k] += n
for k, n in sorted(pp.items()): print(f"  {k}: {n}")

# controles
assert len(res["volcanes"]) == 45, f"control: {len(res['volcanes'])} archivos, esperaba 45"
via_modis = sum(res["volcanes"][v]["MODIS"]["por_marca"].get("via", 0) for v in TIER_A)
via_viirs = sum(res["volcanes"][v][f]["por_marca"].get("via", 0) for v in TIER_A for f in ("VIIRS375", "VIIRS750"))
assert via_modis > 0, "control positivo: MODIS de produccion deberia traer records de la via desde el 2026-11-02"
assert via_viirs == 0, "control: VIIRS de produccion en la base deberia ser todo K"
print(f"\nCONTROLES OK: 45 archivos; via en MODIS Tier A {via_modis} (>0); via en VIIRS Tier A {via_viirs} (=0)")
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
