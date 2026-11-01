# -*- coding: utf-8 -*-
"""V4 / 281: cuenta independiente de qué detector escribió cada record de la serie publicada (main d516b9d8c).
Pregunta 1 del instrumento: si el reemplazo no hubiera ocurrido, los records antes del 2026-09-18 saldrían sin
regimen.codigo_sha y esta cuenta lo vería (control positivo: data/_c0_residuales, que deben salir 100 % sin marca).
Pregunta 2: si el instrumento estuviera muerto (campo mal leído), daría 0 K en todos lados; el control positivo de
records posteriores a 2026-10-18 (NRT con K) lo distingue."""
import json, sys, collections
from pathlib import Path
R = Path(sys.argv[1])
TIER = ["Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica",
        "PuyehueCordonCaulle","Chaiten","Isluga"]
def esk(r): return bool((r.get("regimen") or {}).get("codigo_sha"))
tot = collections.Counter(); mes = collections.defaultdict(collections.Counter); shas = collections.Counter()
tramos = collections.Counter()
for v in TIER:
    recs = json.loads((R/"data/mirova_equivalent"/f"{v}.json").read_text(encoding="utf-8"))["records"]
    for r in recs:
        d = (r.get("datetime_utc") or "")[:10]
        k = esk(r); m = d[:7]
        mes[m]["K" if k else "noK"] += 1
        if k: shas[(r["regimen"]["codigo_sha"])[:9]] += 1
        t = "<2025-02-15" if d < "2025-02-15" else ("2025-02-15..2026-09-17" if d < "2026-09-18" else ">=2026-09-18")
        tramos[(t, "K" if k else "noK")] += 1
print("serie publicada 11 Tier A, main d516b9d8c")
for t in ["<2025-02-15","2025-02-15..2026-09-17",">=2026-09-18"]:
    a, b = tramos[(t,"K")], tramos[(t,"noK")]
    print(f"  {t:24s} K={a:6d} sinK={b:6d} fracK={a/max(1,a+b):.4f}")
print("por mes (K/sinK):")
for m in sorted(mes): print(f"  {m} {mes[m]['K']:5d} {mes[m]['noK']:5d}")
print("codigo_sha distintos (primeros 9):", shas.most_common(10))
# control positivo
res = collections.Counter()
for p in sorted(Path(sys.argv[2]).glob("*.json")):
    for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
        res["K" if esk(r) else "noK"] += 1
print("control positivo data/_c0_residuales:", dict(res))
