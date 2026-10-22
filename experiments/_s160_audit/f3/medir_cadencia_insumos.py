"""F3 (S160): cadencia real de nrt.yml y de sync-mirova-csv.yml a partir de los insumos del orquestador
(50 corridas cada uno, bajadas el 2026-10-22 03:11 UTC; no se hace ninguna llamada a GitHub).

Qué mide: por evento (schedule = cron de GitHub, workflow_dispatch = cron externo de cron-job.org),
cuántas corridas por día, el atraso de cada corrida `schedule` respecto de su cron, el hueco máximo
entre corridas consecutivas del NRT, y en el sync cuántas quedaron `cancelled` y el hueco máximo entre
dos sync `success` (que es cuánto puede atrasarse la referencia sin que nadie lo vea).

Pregunta 1: si el cron externo dejara de disparar, bajarían las `workflow_dispatch` por día y el hueco
máximo subiría; si GitHub dejara de encolar el cron, bajarían las `schedule`. Pregunta 2: un archivo
vacío imprime n=0 y sale con 2, no con un resumen de ceros. Control positivo: el hueco entre dos
corridas `schedule` consecutivas es mayor que 2 h en al menos un caso (ya se ve a ojo en el TSV:
2026-10-21 09:07 y 14:51).
Uso: python -I medir_cadencia_insumos.py <runs_nrt.tsv> <runs_sync.tsv>
"""
import sys
from collections import Counter
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def leer(p):
    filas = []
    with open(p, encoding="utf-8") as fh:
        for l in fh:
            c = l.rstrip("\n").split("\t")
            if len(c) < 7:
                continue
            filas.append({"id": c[0], "creado": datetime.fromisoformat(c[1].replace("Z", "+00:00")),
                          "fin": datetime.fromisoformat(c[2].replace("Z", "+00:00")),
                          "estado": c[3], "concl": c[4], "evento": c[5], "sha": c[6]})
    return sorted(filas, key=lambda f: f["creado"])


nrt = leer(sys.argv[1])
sync = leer(sys.argv[2])
if not nrt or not sync:
    print("SIN DATO: archivo vacío")
    sys.exit(2)

print(f"nrt.yml: {len(nrt)} corridas, de {nrt[0]['creado']:%Y-%m-%d %H:%M} a {nrt[-1]['creado']:%Y-%m-%d %H:%M} UTC")
print("  por evento y conclusión:", dict(Counter((f["evento"], f["concl"] or f["estado"]) for f in nrt)))
dias = (nrt[-1]["creado"] - nrt[0]["creado"]).total_seconds() / 86400
for ev in ("schedule", "workflow_dispatch"):
    n = sum(1 for f in nrt if f["evento"] == ev)
    print(f"  {ev}: {n} corridas en {dias:.2f} días = {n / dias:.1f} por día")
atrasos = []
for f in nrt:
    if f["evento"] != "schedule":
        continue
    t = f["creado"]
    slot = t.replace(minute=0, second=0, microsecond=0)
    if slot.hour % 2:
        slot = slot.replace(hour=slot.hour - 1)
    atrasos.append(((t - slot).total_seconds() / 60, t))
atrasos.sort()
print(f"  atraso de las corridas schedule respecto del cron 0 */2 (min): mín {atrasos[0][0]:.0f}, "
      f"mediana {atrasos[len(atrasos)//2][0]:.0f}, máx {atrasos[-1][0]:.0f} ({atrasos[-1][1]:%Y-%m-%d %H:%M})")
huecos = sorted(((b["creado"] - a["creado"]).total_seconds() / 3600, a["creado"], b["creado"])
                for a, b in zip(nrt, nrt[1:]))
print(f"  hueco máx entre corridas consecutivas (cualquier evento): {huecos[-1][0]:.2f} h "
      f"({huecos[-1][1]:%m-%d %H:%M} -> {huecos[-1][2]:%m-%d %H:%M})")
sch = [f for f in nrt if f["evento"] == "schedule"]
hs = sorted(((b["creado"] - a["creado"]).total_seconds() / 3600, a["creado"], b["creado"]) for a, b in zip(sch, sch[1:]))
print(f"  hueco máx entre corridas schedule solas: {hs[-1][0]:.2f} h ({hs[-1][1]:%m-%d %H:%M} -> {hs[-1][2]:%m-%d %H:%M}); "
      f"control positivo (> 2 h): {'OK' if hs[-1][0] > 2 else 'FALLA'}")
dur = sorted(((f["fin"] - f["creado"]).total_seconds() / 60) for f in nrt if f["estado"] == "completed")
print(f"  duración de las corridas (min): mediana {dur[len(dur)//2]:.0f}, máx {dur[-1]:.0f}")

print(f"\nsync-mirova-csv.yml: {len(sync)} corridas, de {sync[0]['creado']:%Y-%m-%d %H:%M} a {sync[-1]['creado']:%Y-%m-%d %H:%M} UTC")
print("  por conclusión:", dict(Counter(f["concl"] or f["estado"] for f in sync)))
dias_s = (sync[-1]["creado"] - sync[0]["creado"]).total_seconds() / 86400
print(f"  corridas por día: {len(sync) / dias_s:.1f} (cron 12 * * * * pide 24)")
ok = [f for f in sync if f["concl"] == "success"]
hk = sorted(((b["creado"] - a["creado"]).total_seconds() / 3600, a["creado"], b["creado"]) for a, b in zip(ok, ok[1:]))
print(f"  hueco máx entre dos sync success: {hk[-1][0]:.2f} h ({hk[-1][1]:%m-%d %H:%M} -> {hk[-1][2]:%m-%d %H:%M}); "
      f"los 5 mayores: {[round(h, 1) for h, _, _ in hk[-5:]]}")
canc = [f for f in sync if f["concl"] == "cancelled"]
print(f"  cancelled: {len(canc)}; ejemplos: {[(f['creado'].strftime('%m-%d %H:%M'), round((f['fin']-f['creado']).total_seconds()/60)) for f in canc[:6]]} (min hasta la cancelación)")
