"""V3, hallazgo 243: proporción de records MODIS con product_version 'nrt' por mes de observación, en los
11 Tier A de SHA_MAIN. Si el Standard 6.1 dejara de producir, el auto-upgrade nrt->standard (store.py:683)
no ocurriría y los records quedarían 'nrt' para siempre: esta serie lo vería subir. Control: VIIRS (no tocado
por el decomiso). Pregunta 2: si el campo no existiera, la columna 'sin_campo' lo diría.
Uso: python -I v3_proporcion_nrt_modis.py <data/mirova_equivalent>"""
import json, sys, collections, pathlib
d = pathlib.Path(sys.argv[1])
TIER = ["Lascar","PuyehueCordonCaulle","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","Chaiten","Villarrica","NevadosDeChillan","Llaima","Copahue"]
c = collections.defaultdict(collections.Counter)
for v in TIER:
    for r in json.loads((d / f"{v}.json").read_text(encoding="utf-8"))["records"]:
        s = r.get("sensor",""); t = (r.get("datetime_utc") or "")[:7]
        fam = "MODIS" if s.startswith("MODIS") else "VIIRS"
        if t < "2026-06": continue
        c[(fam, t)][r.get("product_version","sin_campo")] += 1
for k in sorted(c):
    tot = sum(c[k].values()); print(k[0], k[1], dict(c[k]), f"nrt={100*c[k]['nrt']/tot:.1f}%", f"n={tot}")
# Por día en la última quincena (MODIS)
dd = collections.defaultdict(collections.Counter)
for v in TIER:
    for r in json.loads((d / f"{v}.json").read_text(encoding="utf-8"))["records"]:
        if r.get("sensor","").startswith("MODIS") and (r.get("datetime_utc") or "") >= "2026-10-01":
            dd[r["datetime_utc"][:10]][r.get("product_version","sin_campo")] += 1
for k in sorted(dd): print("MODIS", k, dict(dd[k]))
