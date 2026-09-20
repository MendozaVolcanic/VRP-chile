# -*- coding: utf-8 -*-
"""V-15: hueco del corpus. (1) Si roto fallaria? control positivo: imprime tambien los dias CON records en el mes anterior.
(2) Instrumento muerto: si la carga fallara n=0 en todo, y se imprime n por mes."""
import io, sys, datetime as dt
from collections import Counter
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar()
for v in VOLS:
    dias = sorted({r["datetime_utc"][:10] for r in D[v]})
    ds = [dt.date.fromisoformat(x) for x in dias]
    gaps = [(a, b, (b - a).days - 1) for a, b in zip(ds, ds[1:]) if (b - a).days > 7]
    m = Counter(x[:7] for x in (r["datetime_utc"][:10] for r in D[v]))
    print(v, "huecos>7d:", [(str(a), str(b), n) for a, b, n in gaps], "| 2025-10:", m.get("2025-10"), "2025-11:", m.get("2025-11"), "2025-12:", m.get("2025-12"), "2026-01:", m.get("2026-01"), "2026-02:", m.get("2026-02"))
