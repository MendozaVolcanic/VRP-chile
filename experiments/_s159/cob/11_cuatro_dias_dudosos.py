# -*- coding: utf-8 -*-
"""COB 11 (S159). Los 4 dias-plataforma con 0 records y granulos en la caja grande de Chile (script 10): se consulta cada una de las 11 cajas
de volcan (fetch.py:751-753, +-25 km) en la ventana 00-10 UTC. Si ningun volcan tiene granulo de esa plataforma ese dia, el 0 es geometria
(la plataforma paso por Chile pero no sobre los volcanes), no un hueco. Control positivo: el dia vecino (dia-1) debe dar granulos en al menos un volcan."""
import sys, io, json, time, datetime, urllib.parse, urllib.request
from pathlib import Path
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas")
VOL = {v["name"]: v for v in yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
VN = ["Lascar","Chaiten","PuyehueCordonCaulle","Lastarria","Villarrica","NevadosDeChillan","Isluga","Copahue","PlanchonPeteroa","Llaima","Tupungatito"]
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
PL = {"MODIS_TERRA": ("MOD021KM", "6.1"), "MODIS_AQUA": ("MYD021KM", "6.1")}
CASOS = [("MODIS_TERRA", "2025-07-15"), ("MODIS_TERRA", "2026-06-02"), ("MODIS_AQUA", "2025-11-16"), ("MODIS_AQUA", "2026-07-21")]
last = [0.0]
def q(sn, ver, dia, v):
    d = 25 / 111.0; x = VOL[v]
    p = {"short_name": sn, "version": ver, "temporal": f"{dia}T00:00:00Z,{dia}T10:00:00Z", "page_size": "50",
         "bounding_box": f"{x['lon']-d:.5f},{x['lat']-d:.5f},{x['lon']+d:.5f},{x['lat']+d:.5f}"}
    w = 1 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    r = json.loads(urllib.request.urlopen(urllib.request.Request(BASE + "?" + urllib.parse.urlencode(p), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90).read())
    last[0] = time.time(); return [e["time_start"][11:16] for e in r["feed"]["entry"]]
for pl, dia in CASOS:
    sn, ver = PL[pl]
    dm = (datetime.date.fromisoformat(dia) - datetime.timedelta(days=1)).isoformat()
    print(f"\n{pl} {dia} (std {sn} v{ver}); control dia-1 {dm}")
    for v in VN:
        a = q(sn, ver, dia, v); b = q(sn, ver, dm, v)
        print(f"  {v:20s} dia: {a}   | dia-1: {b}")
