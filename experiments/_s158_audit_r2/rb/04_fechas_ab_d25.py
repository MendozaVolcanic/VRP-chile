"""Afirmación 4: qué fechas de observación trae cada brazo del A/B de D25 (run 39530508296) en la rama
remota origin/s146-ab/39530508296, por brazo y volcán, contra la ventana V1 del pre-registro
(2026-08-29 a 2026-10-18, PREREGISTRO.md l. 104). Sólo fechas y conteos; ninguna métrica.

Pregunta 1 (¿lo vería si estuviera roto?): si un brazo trajera menos días o un día de menos, la
tabla de días presentes por brazo lo muestra; el control positivo es la fecha 2026-08-28 (anterior
a la ventana) que NO debe aparecer, y 2026-10-18 que la afirmación dice que falta.
Pregunta 2 (¿instrumento muerto?): si git show fallara o el JSON no cargara, el script lanza; un
brazo con 0 records se imprime como 0, distinto de "no leído".
Lee la rama con git show (MSYS_NO_PATHCONV=1), sin checkout. Fecha de observación = `datetime_utc`
del record (día UTC), que es como el pre-registro cuenta días (start/end del workflow)."""
import sys, io, json, subprocess, os
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["MSYS_NO_PATHCONV"] = "1"
RAMA = "origin/s146-ab/39530508296"
BASE = "experiments/_s146_ab_sin_test1/salidas/39530508296"
BRAZOS = ["_s157_ab_d25_k_control", "_s157_ab_d25_k_gemelo", "_s157_ab_d25_k_on"]
VOLS = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan",
        "PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
V_INI, V_FIN = "2026-08-29", "2026-10-18"

def leer(brazo, vol):
    out = subprocess.run(["git", "show", f"{RAMA}:{BASE}/{brazo}/{vol}.json"],
                         capture_output=True, check=True).stdout
    d = json.loads(out.decode("utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    return recs

fechas_por = {}   # (brazo, vol) -> Counter(fecha)
sensores = Counter()
for b in BRAZOS:
    for v in VOLS:
        recs = leer(b, v)
        c = Counter()
        for r in recs:
            dt = r.get("datetime_utc") or ""
            c[dt[:10]] += 1
            sensores[(b, r.get("sensor"))] += 1
        fechas_por[(b, v)] = c

print("Sensores por brazo (todos los records, sin ventana):")
for k in sorted(sensores): print("  ", k, sensores[k])

print("\nPor brazo: records totales, dentro de V1, fuera de V1, y dias distintos dentro de V1")
for b in BRAZOS:
    tot = sum(sum(c.values()) for (bb, v), c in fechas_por.items() if bb == b)
    dentro = sum(n for (bb, v), c in fechas_por.items() if bb == b for f, n in c.items() if V_INI <= f <= V_FIN)
    fuera = tot - dentro
    dias = sorted({f for (bb, v), c in fechas_por.items() if bb == b for f in c if V_INI <= f <= V_FIN})
    print(f"  {b}: total={tot} dentro_V1={dentro} fuera_V1={fuera} dias_distintos_V1={len(dias)} primero={dias[0] if dias else None} ultimo={dias[-1] if dias else None}")
    fuera_f = sorted({f for (bb, v), c in fechas_por.items() if bb == b for f in c if not (V_INI <= f <= V_FIN)})
    print(f"     fechas fuera de V1: {fuera_f[:10]}{' ...' if len(fuera_f) > 10 else ''}")

# días de V1 que faltan en algún brazo (unión de los 11 volcanes)
from datetime import datetime, timedelta
d0, d1 = datetime.strptime(V_INI, "%Y-%m-%d"), datetime.strptime(V_FIN, "%Y-%m-%d")
todos = []
while d0 <= d1:
    todos.append(d0.strftime("%Y-%m-%d")); d0 += timedelta(days=1)
print(f"\nVentana V1 tiene {len(todos)} dias ({V_INI}..{V_FIN}).")
for b in BRAZOS:
    presentes = {f for (bb, v), c in fechas_por.items() if bb == b for f in c}
    faltan = [f for f in todos if f not in presentes]
    print(f"  {b}: dias de V1 sin ningun record en ningun volcan: {faltan}")

print("\nPor brazo y volcan: n records en V1, dias distintos, ultimo dia, n en 2026-10-18, n en 2026-10-17")
print(f"{'brazo':26} {'volcan':20} {'n_V1':>6} {'dias':>5} {'ultimo':>10} {'n1018':>6} {'n1017':>6} {'n1016':>6}")
for b in BRAZOS:
    for v in VOLS:
        c = fechas_por[(b, v)]
        en = {f: n for f, n in c.items() if V_INI <= f <= V_FIN}
        print(f"{b:26} {v:20} {sum(en.values()):6d} {len(en):5d} {max(en) if en else '-':>10} {c.get('2026-10-18',0):6d} {c.get('2026-10-17',0):6d} {c.get('2026-10-16',0):6d}")

# Igualdad de fechas entre brazos por volcan (solo conteo por dia)
print("\nDiferencias de conteo por dia entre brazos (mismo volcan):")
ndif = 0
for v in VOLS:
    ref = fechas_por[(BRAZOS[0], v)]
    for b in BRAZOS[1:]:
        c = fechas_por[(b, v)]
        for f in sorted(set(ref) | set(c)):
            if ref.get(f, 0) != c.get(f, 0):
                ndif += 1
                print(f"  {v} {f}: {BRAZOS[0]}={ref.get(f,0)} {b}={c.get(f,0)}")
print(f"  total diferencias de conteo por dia: {ndif}")

# Hora UTC de la ultima pasada por brazo (para ver si el 18-oct quedo cortado)
print("\nUltima pasada (datetime_utc) por brazo y sensor:")
for b in BRAZOS:
    ult = {}
    for v in VOLS:
        for r in leer(b, v):
            s = r.get("sensor"); dt = r.get("datetime_utc")
            if dt and (s not in ult or dt > ult[s]): ult[s] = dt
    for s in sorted(ult): print(f"  {b} {s}: {ult[s]}")
