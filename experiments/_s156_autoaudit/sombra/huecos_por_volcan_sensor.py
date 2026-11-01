"""¿Cuántas veces un volcán y sensor pasó más de 3 días sin records? Mide la tasa de falsas «vigilancias ciegas»
que daría el umbral MAX_DIAS_SOMBRA_SIN_DATOS = 3 de scripts/vigilancia_sombra.py, en producción y en la sombra.
Uso: python huecos_por_volcan_sensor.py <raiz> [desde]"""
import json
import os
import sys
from collections import defaultdict
from datetime import date

raiz = sys.argv[1]
desde = sys.argv[2] if len(sys.argv) > 2 else "2026-08-01"
sys.path.insert(0, os.path.join(raiz, "scripts"))
import auto_audit_weekly as aa  # noqa: E402

for nombre, sub in (("produccion", "mirova_equivalent"), ("sombra", "experimental_v2")):
    peor, n_huecos = {}, 0
    for vol in aa.VOLS:
        p = os.path.join(raiz, "data", sub, vol + ".json")
        dias = defaultdict(set)
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b = aa.our_bucket(r.get("sensor", ""))
            if b and r.get("datetime_utc", "") >= desde:
                dias[b].add(r["datetime_utc"][:10])
        for b in aa.SENSORS:
            ds = sorted(date.fromisoformat(d) for d in dias[b])
            gaps = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
            peor[(vol, b)] = max(gaps) if gaps else None
            n_huecos += sum(1 for g in gaps if g > 4)   # hueco que deja más de 3 días sin datos
    print(f"== {nombre} desde {desde}")
    print(f"   huecos de más de 3 días sin datos (volcán y sensor): {n_huecos}")
    for k, v in sorted(peor.items(), key=lambda kv: -(kv[1] or 0))[:8]:
        print(f"   {k[0]:20s} {k[1]:9s} hueco máximo {v} días")
