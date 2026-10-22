# -*- coding: utf-8 -*-
"""V4: el hueco 2025-11-16..2026-01-28 (CLAUDE.md, marca S146 V-15) ¿sigue en la serie de main d516b9d8c?
Cuenta días con al menos un record por volcán dentro de la ventana (75 días). Control positivo: la misma cuenta sobre
la versión previa al reemplazo (tag pre-s158-reemplazo-k), que debería mostrar el hueco."""
import json, sys, datetime as dt
from pathlib import Path
TIER = ["Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica",
        "PuyehueCordonCaulle","Chaiten","Isluga"]
d0, d1 = "2025-11-16", "2026-01-28"
for v in TIER:
    recs = json.loads(Path(sys.argv[1], f"{v}.json").read_text(encoding="utf-8"))["records"]
    dias = {r["datetime_utc"][:10] for r in recs if d0 <= r["datetime_utc"][:10] <= d1}
    print(f"{v:22s} dias_con_record={len(dias):3d} de 74  n_records_ventana={sum(1 for r in recs if d0 <= r['datetime_utc'][:10] <= d1)}")
