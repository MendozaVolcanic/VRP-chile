"""S177: C-via y cobertura de D4 (vía en R25). Sólo cuenta marcas y pasadas; no lee VRP ni detecciones (candado 11).

POR QUÉ. Un run verde no prueba que la vía haya corrido (A108, vigilante ciego): si la vía cae a K en silencio
el job termina bien igual. En R25 el pre-registro §7 acepta records sin marca como SIN DATO, pero más de 10 %
en una clase deja INDECIDIBLE ese sensor y tramo. Aquí se suma la marca por sensor y por volcán.

La lectura decisiva de C-via (por clase) la hace el lector después del candado; esto es el control de montaje.
"""
import collections
import io
import json
import pathlib
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales/s177_d4")
UMBRAL = 90.0
PAT = re.compile(r"([\w ]+?): (\d+)/(\d+) de la via \(([\d.]+)%\)")

logs = sorted(R.glob("log-*"))
trozos = sorted(R.glob("trozo-*"))
print(f"carpetas log {len(logs)}  trozo {len(trozos)}")

tot = collections.Counter()
por_sensor = collections.defaultdict(lambda: [0, 0])
por_vol_sensor = collections.defaultdict(lambda: [0, 0])
bajos = []
sin_txt = []
for d in logs:
    t = d / "controles_via.txt"
    if not t.exists():
        sin_txt.append(d.name)
        continue
    vol = d.name[len("log-"):].split("-")[0]
    lineas = 0
    for m in PAT.finditer(t.read_text(encoding="utf-8")):
        sensor, si, n, pct = m[1].strip(), int(m[2]), int(m[3]), float(m[4])
        lineas += 1
        por_sensor[sensor][0] += si
        por_sensor[sensor][1] += n
        por_vol_sensor[(vol, sensor)][0] += si
        por_vol_sensor[(vol, sensor)][1] += n
        if n and pct < UMBRAL:
            bajos.append((d.name, sensor, si, n, pct))
    tot["lineas_via"] += lineas
    if lineas == 0:
        tot["logs_sin_lineas"] += 1
    for c in (d / "cobertura").glob("*.json"):
        j = json.loads(c.read_text(encoding="utf-8"))
        tot["coberturas"] += 1
        for k in ("fallas", "sin_granulos", "retiradas"):
            v = j[k]
            tot[k] += len(v) if hasattr(v, "__len__") else v
        tot["n_incidencias"] += j["n_incidencias"]
        if j["fallas"]:
            print("FALLA", c, str(j["fallas"])[:300])

print(dict(tot))
print("sin controles_via.txt:", len(sin_txt), sin_txt[:5])
print("\nC-via por sensor (umbral de lectura 90 %):")
for s, (si, n) in sorted(por_sensor.items()):
    print(f"  {s:18s} {si:6d}/{n:6d}  {100 * si / n if n else 0:6.2f} %")
print("\nC-via por volcán y sensor:")
for (v, s), (si, n) in sorted(por_vol_sensor.items()):
    marca = "  <-- bajo 90" if n and 100 * si / n < UMBRAL else ""
    print(f"  {v:22s} {s:18s} {si:5d}/{n:5d}  {100 * si / n if n else 0:6.2f} %{marca}")
print(f"\nlíneas de trozo bajo 90 %: {len(bajos)}")
for b in bajos[:30]:
    print("  ", b)

pasadas = collections.Counter()
dias = collections.defaultdict(set)
for d in trozos:
    js = list(d.glob("*.json"))
    assert len(js) == 1, d
    for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
        pasadas[(js[0].stem, r["sensor"])] += 1
        dias[js[0].stem].add(r["datetime_utc"][:10])
print("\nregistros por volcán (sin leer detección) y días con datos:")
for v in sorted(dias):
    print(f"  {v:22s} días {len(dias[v]):4d}  " + "  ".join(f"{s}={c}" for (w, s), c in sorted(pasadas.items()) if w == v))
