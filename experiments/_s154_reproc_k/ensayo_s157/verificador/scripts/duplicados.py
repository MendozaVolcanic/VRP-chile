# -*- coding: utf-8 -*-
"""Pasadas fisicamente iguales con clave distinta: mismo sensor a <=10 min, en el resultado del reemplazo."""
import json, sys, io
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from scripts.reemplazar_ventana_reproceso import reemplazar_ventana
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[5]  # raiz del repo
DESDE, HASTA = "2025-02-15", "2026-09-17"
vols = sys.argv[1:]
tot = {}
for v in vols:
    op = json.load(open(RAIZ / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))
    re_ = json.load(open(RAIZ / "data/_s154_reproc_k_historico" / f"{v}.json", encoding="utf-8"))
    store, inf = reemplazar_ventana(op, re_, DESDE, HASTA, "_s154_reproc_k_historico")
    def pares(recs, etiqueta):
        por = {}
        for r in recs:
            if not (DESDE <= r["datetime_utc"][:10] <= HASTA):
                continue
            por.setdefault(r["sensor"], []).append(r)
        out = []
        for s, L in por.items():
            L.sort(key=lambda r: r["datetime_utc"])
            for a, b in zip(L, L[1:]):
                ta = datetime.fromisoformat(a["datetime_utc"]); tb = datetime.fromisoformat(b["datetime_utc"])
                if (tb - ta).total_seconds() <= 600:
                    ma = "K" if (a.get("regimen") or {}).get("codigo_sha") else "C0"
                    mb = "K" if (b.get("regimen") or {}).get("codigo_sha") else "C0"
                    out.append((s, a["datetime_utc"], ma, a.get("product_version"), b["datetime_utc"], mb, b.get("product_version")))
        return out
    p_op, p_new, p_re = pares(op["records"], "op"), pares(store["records"], "nuevo"), pares(re_["records"], "re")
    mixtos = [p for p in p_new if p[2] != p[5]]
    print(f"== {v}: pares <=10 min mismo sensor: op {len(p_op)}, reproceso {len(p_re)}, resultado {len(p_new)} (mixtos C0/K {len(mixtos)})")
    for p in mixtos: print("   MIXTO", p)
    for p in p_re[:4]: print("   en reproceso", p)
    # pub de islas C0
    tot[v] = (len(p_op), len(p_re), len(p_new), len(mixtos))
print(tot)
