# Verificador: por raiz, volcan y brazo, que commit escribio los records y si los diurnos traen umbrales diurnos.
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path(sys.argv[1])
for w in sys.argv[2:]:
    for f in sorted((D / w / "_s151_ab_diurno_on").glob("*.json")):
        vol = f.stem
        lin = []
        for brazo in ("_s151_ab_diurno_control", "_s151_ab_diurno_on"):
            recs = json.loads((D / w / brazo / f.name).read_text(encoding="utf-8")).get("records", [])
            shas = collections.Counter(((r.get("regimen") or {}).get("codigo_sha") or "?")[:7] for r in recs)
            vday = sum(1 for r in recs if r.get("diag_umbrales_diurnos"))
            lin.append("%s %s umbrales_diurnos=%d" % (brazo[15:], dict(shas), vday))
        log = D / w / "logs" / ("_s151_ab_diurno_on_%s.log" % vol)
        fb = next((l[:60] for l in log.read_text(encoding="utf-8", errors="replace").splitlines() if l.startswith("FLAGS_BRAZO")), None) if log.exists() else None
        print(w, vol, " | ".join(lin), "| log on:", "FLAGS ok" if fb else "SIN FLAGS")
