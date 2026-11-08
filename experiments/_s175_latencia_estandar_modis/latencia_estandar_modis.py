"""Cuánto tarda el producto estándar de NASA en reemplazar a una pasada MODIS guardada como NRT, y qué pasadas quedaron
con la vía «código MIROVA» alrededor del encendido. Respaldo de la ficha CPLT v1.19 (VPR956-01, PR #956).

POR QUÉ existe: `pipeline/store.py` dice en un comentario de S12 que el estándar llega «typically 3-5 days»; nadie lo
había medido, y la ficha pública lo repetía. Se mide en los records publicados.

Qué mide. `first_processed_utc` se escribe una sola vez y se hereda en todo reemplazo (S150); `processed_utc` es la
última escritura. En un record `standard`, la diferencia es lo que tardó el reemplazo desde que el sistema guardó la
pasada por primera vez (no desde que NASA la publicó). Si es 0, el record entró ya como estándar: no hay reemplazo.

Trampa que este script separa. La misma diferencia también crece con un reproceso: el 2026-10-18, tras #850, el reproceso
de 30 días (commits `data(backfill): ... 2026-09-18..2026-10-18 (S120)`, 10:55 a 12:27 UTC) re-escribió las pasadas de la
ventana con su `first_processed_utc` heredado. Esos records no son la llegada del estándar y se cuentan aparte.

Instrumento: imprime también el conteo sin excluir, para que se vea qué mueve la exclusión; el 3 a 5 días sin excluir da
distinto de 0, así que el instrumento puede ver esa franja. Lee por `git show` (no toca `data/` ni el checkout).

Uso: python latencia_estandar_modis.py [REF]   (REF por omisión: origin/main)
"""
import io
import json
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
REF = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
# POR QUÉ estos límites: el primer record re-escrito del reproceso tiene processed_utc 10:37:01 y el último commit del
# reproceso es de 12:27:15 UTC del 2026-10-18. Fuera de esa franja la re-escritura es la de la corrida normal.
REPROCESO_DESDE = "2026-10-18T10:30:00Z"
REPROCESO_HASTA = "2026-10-18T12:30:00Z"
ENCENDIDO = None  # se calcula de los datos: menor processed_utc de un record de la vía (regla de reversión, §4.1)


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, check=True).stdout


def fecha(s):
    return datetime.fromisoformat(s.replace("Z", "")[:19].replace(" ", "T"))


def resumen(etiqueta, filas):
    """filas: (volcán, observación, primera escritura, última escritura, horas)."""
    if not filas:
        print(f"{etiqueta}: n=0")
        return
    hs = sorted(f[4] for f in filas)
    n = len(hs)
    q = lambda p: hs[int(p * (n - 1))]
    franjas = [("<24 h", sum(h < 24 for h in hs)), ("24 a 72 h", sum(24 <= h < 72 for h in hs)),
               ("3 a 5 dias", sum(72 <= h <= 120 for h in hs)), (">5 dias", sum(h > 120 for h in hs))]
    print(f"{etiqueta}: n={n}")
    print(f"  horas: min {hs[0]:.1f} | p10 {q(.1):.1f} | mediana {statistics.median(hs):.1f} | p90 {q(.9):.1f} | "
          f"max {hs[-1]:.1f} ({hs[-1] / 24:.2f} dias)")
    print("  " + " | ".join(f"{e}: {c} ({100 * c / n:.1f} %)" for e, c in franjas))
    print(f"  observadas de {min(f[1] for f in filas)} a {max(f[1] for f in filas)} UTC; "
          f"reemplazadas de {min(f[3] for f in filas)} a {max(f[3] for f in filas)}")


vl = yaml.safe_load(git("show", f"{REF}:volcanoes.yaml"))
vl = vl["volcanoes"] if isinstance(vl, dict) else vl
tier_a = sorted(v["name"] for v in vl if v.get("radius_km") == 25)
print("ref:", git("rev-parse", REF).decode().strip(), "| Tier A:", len(tier_a))

todos = []
for nombre in tier_a:
    for r in json.loads(git("show", f"{REF}:data/mirova_equivalent/{nombre}.json"))["records"]:
        if str(r.get("sensor", "")).upper().startswith("MODIS"):
            todos.append((nombre, r.get("datetime_utc", ""), r.get("product_version"), r.get("first_processed_utc"),
                          r.get("processed_utc"), r.get("via_codigo_mirova")))

estandar = [t for t in todos if t[2] == "standard" and t[3] and t[4]]
reescritos = []
for n, obs, _, primera, ultima, _ in estandar:
    horas = (fecha(ultima) - fecha(primera)).total_seconds() / 3600
    if horas >= 0.01:
        reescritos.append((n, obs, primera, ultima, horas))
print("MODIS Tier A:", len(todos), "| estandar con los dos sellos:", len(estandar),
      "| entraron ya como estandar:", len(estandar) - len(reescritos), "| re-escritos despues:", len(reescritos))

del_reproceso = [f for f in reescritos if REPROCESO_DESDE <= f[3] <= REPROCESO_HASTA]
naturales = [f for f in reescritos if not REPROCESO_DESDE <= f[3] <= REPROCESO_HASTA]
print()
resumen("TODOS los re-escritos (sin separar el reproceso)", reescritos)
resumen("re-escritos DENTRO del reproceso del 2026-10-18 (no son llegada del estandar)", del_reproceso)
resumen("REEMPLAZOS NATURALES NRT a estandar (el numero de la ficha)", naturales)
primera_post = [f for f in reescritos if f[2] > REPROCESO_HASTA]
resumen("sensibilidad: primera escritura posterior al reproceso", primera_post)

pendientes = [t for t in todos if t[2] == "nrt" and t[3] and t[3] > REPROCESO_HASTA]
print("\nNRT aun sin reemplazo (censura, primera escritura posterior al reproceso):", len(pendientes),
      "| observados desde 2026-11-06:", sum(t[1] >= "2026-11-06" for t in pendientes))
print("  mas antiguos que eso:", [(t[0], t[1]) for t in pendientes if t[1] < "2026-11-06"])

print("\nmaximo observacion a ultima escritura en re-escritos de octubre de 2026 (el 9,42 de la regla, sec. 4.1):")
oct_reesc = [(f[0], f[1], f[3], (fecha(f[3]) - fecha(f[1])).total_seconds() / 86400) for f in reescritos
             if "2026-10-01" <= f[1] < "2026-11-01"]
oct_reesc.sort(key=lambda x: -x[3])
print("  mayores 3:", [(a, b, c, round(d, 2)) for a, b, c, d in oct_reesc[:3]])
print("  max entre reemplazos naturales: %.2f dias" % max(((fecha(f[3]) - fecha(f[1])).total_seconds() / 86400) for f in naturales))

via = [t for t in todos if t[5] is True]
encendido = min(t[4] for t in via)
print("\nencendido (menor processed_utc de un record de la via):", encendido)
print("primera observacion con la via:", min(t[1] for t in via),
      "| horas antes del encendido: %.2f" % ((fecha(encendido) - fecha(min(t[1] for t in via))).total_seconds() / 3600))
antes = [t for t in todos if "2026-10-25" <= t[1] and fecha(t[1]) < fecha(encendido)]
print("observadas desde 2026-10-25 hasta el encendido, por (producto, via):", dict(Counter((t[2], t[5]) for t in antes)))
madrugada = [t for t in antes if t[1] >= "2026-11-02 01:15" and t[1] <= "2026-11-02 07:30"]
print("madrugada del 2026-11-02 (01:15 a 07:30 UTC):", len(madrugada), dict(Counter((t[2], t[5]) for t in madrugada)))
con_via = [t for t in madrugada if t[5] is True]
print("  con via: primera escritura de", min(t[3] for t in con_via), "a", max(t[3] for t in con_via),
      "| reemplazo de", min(t[4] for t in con_via), "a", max(t[4] for t in con_via))
print("  sin via:", [(t[0], t[1], t[2], t[3], t[4]) for t in madrugada if t[5] is not True])
sin_via_tras = [t for t in antes if t[5] is not True and t[4] >= encendido]
print("sin via y escritas despues del encendido:", len(sin_via_tras))
print("ultimo processed_utc de un record estandar sin via de esa franja:",
      max(t[4] for t in antes if t[5] is not True and t[2] == "standard"))
