#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175), afirmación 157 (mitigación): con MIN_N_RECALL=15 el recall de VIA_MODIS no da flag, pero ¿una protegida
que la vía calla sí da flag por sí sola? Copia los 11 JSON de producción a una carpeta temporal, calla el record de la
vía de NevadosDeChillan MODIS 2026-11-05 07:45 (MIROVA 25 MW, la única protegida posterior al encendido con record
de los dos lados en el snapshot) y corre auto_audit_weekly.main con aa.ROOT (sólo lo usa cargar_records, l. 703) y
bp.DATA apuntando a la copia; la salida va a la carpeta temporal de V1.
Pregunta 1: si el audit no viera una pérdida de la vía hasta juntar 15 noches, no habría flag. Pregunta 2 (control):
sin mutar (corrida A de audit_con_y_sin_via.py) da 0 flags; aquí tiene que aparecer exactamente la de Chillán.
Uso: python audit_via_calla.py <root_base> <tmp>
"""
import io, contextlib, json, os, shutil, sys
from pathlib import Path
root, tmp = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, os.path.join(root, "scripts")); sys.path.insert(0, root)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aa
import banco_paridad as bp
if tmp.exists():
    shutil.rmtree(tmp)
d = tmp / "data" / "mirova_equivalent"; d.mkdir(parents=True)
for v in bp.VOLS:
    shutil.copy(Path(root) / "data" / "mirova_equivalent" / f"{v}.json", d / f"{v}.json")
p = d / "NevadosDeChillan.json"
j = json.load(open(p, encoding="utf-8")); n = 0
for r in j["records"]:
    if str(r.get("sensor", "")).startswith("MODIS") and str(r.get("datetime_utc"))[:16] == "2026-11-05 07:45":
        assert r.get("via_codigo_mirova") is True
        r["vrp_mw"] = 0.0; r["primary_cluster"] = None; r["distance_class"] = None; r["anomaly_pixels"] = []; n += 1
json.dump(j, open(p, "w", encoding="utf-8"))
aa.ROOT = str(tmp); bp.DATA = d; aa.OUTDIR = str(tmp / "out")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    aa.main()
lat = json.load(open(tmp / "out" / "latest.json", encoding="utf-8"))
print(json.dumps({"records_callados": n, "verdict": lat["verdict"], "flags": lat["flags"]}, indent=1, ensure_ascii=False))
shutil.rmtree(tmp)
