#!/usr/bin/env python3
"""F3-08: noches con alerta de MIROVA (VIIRS 375 y MODIS) que el audit cuenta como perdidas bajo K, con su VRP.
P1/control: n y aciertos deben reproducir la corrida K de simular_cron (V375 n=104, 92,3 %; MODIS n=12, 66,7 %).
D-9: alerta V375 de 0,05 MW o menos = NONE para MIROVA (docs/MISSION.md punto 5)."""
import json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
AQUI = Path(__file__).resolve().parent; REPO = AQUI.parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts")); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw
hoy = datetime(2026, 10, 19).date(); win = ((hoy - timedelta(days=60)).isoformat(), hoy.isoformat())
coords = aw._coords_por_volcan()
for raizn in ["raiz_K", "raiz_C0"]:
    mir = defaultdict(float)
    for a in aw.alertas_mirova(str(AQUI / "ref_fresca/registro_vrp_consolidado.csv"), str(AQUI / "ref_fresca/registro_vrp_ocr.csv"), str(AQUI / "historico_combinado.csv")):
        dt = a["fecha_utc"] or ""
        if not (win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS: continue
        ll = coords[a["volcano"]]
        o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        if aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o): continue
        k = (a["volcano"], a["sensor_bucket"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
    vistos, crater, dashn = set(), set(), set()
    for vol in aw.VOLS:
        for r in json.load(open(AQUI / raizn / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
            dt = r.get("datetime_utc")
            if not (dt and win[0] <= dt[:10] <= win[1]): continue
            b = aw.our_bucket(r.get("sensor", "")); vistos.add((vol, b, dt[:10]))
            pc = r.get("primary_cluster") or {}; v = pc.get("vrp_mw") or 0; c = pc.get("centroid_dist_km")
            if 0 < v <= aw.CAP and c is not None and c <= aw.INNER[vol]:
                crater.add((vol, b, dt[:10]))
                if r.get("distance_class") in (None, "summit"): dashn.add((vol, b, dt[:10]))
    print("=====", raizn)
    for s in ["VIIRS375", "MODIS", "VIIRS750"]:
        ks = [k for k in mir if k[1] == s and k[0] in aw.VOLS and k in vistos]
        hits = [k for k in ks if k in crater]; per = sorted(k for k in ks if k not in crater)
        print(f"{s}: n={len(ks)} crater={len(hits)} ({100*len(hits)/len(ks):.1f} %) dash={sum(k in dashn for k in ks)}" if ks else f"{s}: SIN DATO")
        for k in per: print("   perdida", k, "MIROVA max VRP", mir[k], "<=0,05" if mir[k] <= 0.05 else "")
        if s == "VIIRS375":
            ks2 = [k for k in ks if mir[k] > 0.05]
            print(f"   con D-9 (fuera <=0,05 MW): n={len(ks2)} crater={sum(k in crater for k in ks2)} "
                  f"({100*sum(k in crater for k in ks2)/len(ks2):.1f} %)")
