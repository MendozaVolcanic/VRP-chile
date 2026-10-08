"""S150 frente A: huecos de la serie por volcan y por familia de sensor (MODIS, V375, V750).
Un 'hueco' = horas entre dos pasadas consecutivas de la misma familia. Ventana 2026-06-01 a hoy.
Pregunta: ¿alguna familia estuvo >48 h sin pasadas mientras el volcan seguia 'fresco' por otra?
Eso es lo que el healthcheck (records[-1] por volcan, nrt-healthcheck.yml) NO puede ver.
P1: un apagon de un sensor produce un hueco largo en esa familia y no en las otras (lo ve).
P2: si el JSON no cargara, n=0 y se informa. Control positivo: el apagon 2026-10-02/08
debe aparecer como hueco simultaneo en las tres familias de los 11 volcanes."""
import json, sys, glob, os
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
TIER_A = ["Lascar","PuyehueCordonCaulle","Lastarria","Isluga","Tupungatito","PlanchonPeteroa",
          "Chaiten","Villarrica","NevadosDeChillan","Llaima","Copahue"]
base = sys.argv[1] if len(sys.argv) > 1 else "data/mirova_equivalent"
desde = sys.argv[2] if len(sys.argv) > 2 else "2026-06-01"
fam = lambda s: "MODIS" if "MODIS" in s else ("V750" if s.endswith("_750") else "V375")
for v in TIER_A:
    rs = json.load(open(os.path.join(base, f"{v}.json"), encoding="utf-8"))["records"]
    por = {}
    for r in rs:
        if r["datetime_utc"][:10] < desde: continue
        por.setdefault(fam(r["sensor"]), []).append(datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M"))
    linea = []
    for f in ("MODIS", "V375", "V750"):
        ts = sorted(por.get(f, []))
        huecos = sorted((((b - a).total_seconds() / 3600, a, b) for a, b in zip(ts, ts[1:])), reverse=True)[:3]
        linea.append(f"{f}: n={len(ts)} ultimo={ts[-1]:%m-%d %H:%M} " +
                     " ".join(f"[{h:.0f}h {a:%m-%d}->{b:%m-%d}]" for h, a, b in huecos if h > 48))
    print(v); [print("   ", l) for l in linea]
