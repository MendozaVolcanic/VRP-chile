# Verificador: que commit escribio cada record, por raiz y brazo, y rango de fechas por raiz.
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path(sys.argv[1])
for w in sorted(p.name for p in D.iterdir() if p.is_dir()):
    for brazo in ("_s151_ab_diurno_control", "_s151_ab_diurno_on"):
        shas, fechas, origen, n = collections.Counter(), [], collections.Counter(), 0
        for f in sorted((D / w / brazo).glob("*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")).get("records", []):
                n += 1
                rg = r.get("regimen") or {}
                shas[(rg.get("codigo_sha") or "?")[:10]] += 1
                origen[rg.get("perfil")] += 1
                fechas.append((r.get("datetime_utc") or "")[:10])
        print(w, brazo[15:], "records", n, "fechas", min(fechas) if fechas else "-", "a", max(fechas) if fechas else "-",
              "shas", dict(shas), "perfil", dict(origen))
    logs = D / w / "logs"
    nlog = len(list(logs.glob("*.log"))) if logs.exists() else 0
    print("   logs:", nlog)
