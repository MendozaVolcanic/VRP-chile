"""Chillán V375: VRP del record NRT original (historia git de data/mirova_equivalent/NevadosDeChillan.json) contra el
estándar publicado hoy, en las 8 pasadas del probe S185. Hipótesis: la cola baja del este viene del gránulo estándar de
I-band; si el NRT (lo que MIROVA pudo usar) da una razón cerca de 1 en las bajas y el estándar no, la hipótesis gana.
Solo lee git (origin/main); no baja nada."""
import json, subprocess, sys
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding="utf-8")
W = r"D:\vrp-trabajo\worktrees\s190-l1b-ab"
F = "data/mirova_equivalent/NevadosDeChillan.json"
PAS = [("baja_este", "VIIRS_NOAA20", "2026-10-10 05:12", 0.679), ("baja_este", "VIIRS_NOAA21", "2026-10-29 05:00", 0.652),
       ("baja_este", "VIIRS_NOAA21", "2026-11-14 05:00", 0.676), ("ctrl_este", "VIIRS_NOAA20", "2026-11-11 05:12", 0.957),
       ("ctrl_este", "VIIRS_NOAA20", "2026-10-26 05:12", 0.925), ("ctrl_este", "VIIRS_NOAA20", "2026-09-29 05:18", 1.047),
       ("ctrl_oeste", "VIIRS_NOAA21", "2026-10-30 06:18", 1.001), ("ctrl_oeste", "VIIRS_NOAA21", "2026-11-04 06:24", 1.000)]
def git(*a):
    return subprocess.run(["git", "-C", W, *a], capture_output=True, text=True, encoding="utf-8").stdout
res = []
for rol, sen, dt, razon_std in PAS:
    t = datetime.strptime(dt, "%Y-%m-%d %H:%M")
    commits = git("log", "origin/main", "--reverse", "--format=%H %cI", f"--since={(t + timedelta(hours=1)).isoformat()}Z",
                  f"--until={(t + timedelta(days=10)).isoformat()}Z", "--", F).split("\n")
    vistos = []
    for c in [x for x in commits if x.strip()]:
        h, fecha = c.split()
        try:
            recs = json.loads(git("show", f"{h}:{F}"))["records"]
        except Exception:
            continue
        r = [x for x in recs if x["sensor"] == sen and x["datetime_utc"] == dt]
        if not r:
            continue
        r = r[0]
        clave = (r.get("product_version"), r.get("granule"), r.get("vrp_mw"))
        if not vistos or vistos[-1][1:] != clave:
            vistos.append((fecha, *clave, r.get("via_codigo_mirova"), (r.get("regimen") or {}).get("perfil")))
        if r.get("product_version") == "standard":
            break
    res.append({"rol": rol, "sensor": sen, "dt": dt, "razon_std_s185": razon_std, "versiones": vistos})
    print(rol, sen, dt, "razon std", razon_std)
    for v in vistos:
        print("   ", v)
json.dump(res, open(r"D:\vrp-trabajo\temporales\s190_l1b_ab\chi\1_nrt_vs_std_git.json", "w", encoding="utf-8"), indent=1)
