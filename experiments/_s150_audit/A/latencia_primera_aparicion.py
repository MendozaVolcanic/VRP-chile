"""S150 frente A: latencia REAL hasta el repo = hora del primer commit que contiene la pasada
menos datetime_utc. No depende de processed_utc (que se reescribe al promover a standard).
Ventana: pasadas 2026-09-24 a 2026-10-02 de un volcan. P1: si el NRT se atrasara, crece.
P2: pasadas que aparecen en el primer commit de la serie se descartan (no se sabe cuando entraron).
Control: el primer commit de la serie debe tener pasadas descartadas > 0 (si no, la ventana no arranca antes)."""
import json, subprocess, sys, statistics, collections
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
vol = sys.argv[1]; ruta = f"data/mirova_equivalent/{vol}.json"
log = subprocess.run(["git", "log", "--reverse", "--since=2026-09-22", "--format=%H %cI", "--", ruta],
                     capture_output=True, text=True).stdout.split("\n")
log = [l.split() for l in log if l.strip()]
visto = {}; primero = True; descart = 0
for sha, ci in log:
    d = json.loads(subprocess.run(["git", "show", f"{sha}:{ruta}"], capture_output=True).stdout)
    t = datetime.fromisoformat(ci).astimezone(timezone.utc).replace(tzinfo=None)
    for r in d["records"]:
        k = (r["datetime_utc"], r["sensor"])
        if k in visto: continue
        if primero: visto[k] = None; descart += 1; continue
        visto[k] = t
    primero = False
lat = collections.defaultdict(list)
for (dt, s), t in visto.items():
    if t is None or not ("2026-09-24" <= dt[:10] <= "2026-10-02"): continue
    fam = "MODIS" if "MODIS" in s else ("V750" if s.endswith("_750") else "V375")
    lat[fam].append((t - datetime.strptime(dt, "%Y-%m-%d %H:%M")).total_seconds() / 3600)
print(f"{vol}: commits={len(log)} descartadas_por_estar_en_el_primero={descart}")
for f, v in sorted(lat.items()):
    v.sort(); q = lambda x: v[min(len(v)-1, int(x*len(v)))]
    print(f"  {f}: n={len(v)} p10={q(.1):.1f} h mediana={q(.5):.1f} h p90={q(.9):.1f} h max={v[-1]:.1f} h")
