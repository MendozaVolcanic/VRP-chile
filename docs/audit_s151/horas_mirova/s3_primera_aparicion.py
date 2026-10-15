"""s3: reloj independiente. Recorre TODOS los commits de una ventana que tocaron
registro_vrp_consolidado.csv, baja el comienzo del archivo en cada commit (el CSV esta ordenado por
timestamp descendente, asi que las pasadas recientes estan arriba; Range de bytes) y registra:
  - el primer commit en que aparece cada fila (timestamp, Volcan, Sensor), con su hora UTC de commit;
  - el valor de Fecha_Proceso_GitHub y Ultima_Actualizacion en ese momento y despues.
Compara la hora del commit con Fecha_Proceso_GitHub leida como America/Santiago, como UTC y con -3/-4 fijos.
Uso: python s3_primera_aparicion.py commits.csv DESDE_COMMIT HASTA_COMMIT PASADA_MIN PASADA_MAX salida.csv
"""
import sys, io, csv, concurrent.futures as cf
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
Z = ZoneInfo("America/Santiago")
commits_csv, c_desde, c_hasta, p_min, p_max, out = sys.argv[1:7]
RANGO = 160_000

def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

coms = [r for r in csv.DictReader(open(commits_csv, encoding="utf-8"))]
coms = [r for r in coms if c_desde <= r["committer_utc"] < c_hasta]
coms.sort(key=lambda r: r["committer_utc"])
print("commits en ventana:", len(coms), coms[0]["committer_utc"], "->", coms[-1]["committer_utc"])
gaps = [(utc(b["committer_utc"]) - utc(a["committer_utc"])).total_seconds() / 60 for a, b in zip(coms, coms[1:])]
gaps.sort()
print(f"separacion entre commits (min): mediana {gaps[len(gaps)//2]:.1f} p90 {gaps[int(len(gaps)*.9)]:.1f} max {gaps[-1]:.1f}")

def bajar(sha):
    url = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/registro_vrp_consolidado.csv"
    for intento in range(4):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes=0-{RANGO}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                txt = r.read().decode("utf-8", errors="replace")
            lineas = txt.split("\n")[:-1]  # la ultima puede estar cortada
            return list(csv.DictReader(lineas))
        except Exception as e:
            err = e
    raise err

tmin = int(datetime.fromisoformat(p_min).replace(tzinfo=timezone.utc).timestamp())
tmax = int(datetime.fromisoformat(p_max).replace(tzinfo=timezone.utc).timestamp())
with cf.ThreadPoolExecutor(8) as ex:
    filas_por_commit = list(ex.map(lambda c: bajar(c["sha"]), coms))

primera = {}      # clave -> dict
historia = {}     # clave -> lista de (commit_utc, fproc, ultima)
cobertura_mala = 0
for c, filas in zip(coms, filas_por_commit):
    if not filas or int(filas[-1]["timestamp"]) > tmin:
        cobertura_mala += 1   # el rango no alcanzo a cubrir PASADA_MIN en este commit
    for r in filas:
        ts = int(r["timestamp"])
        if not (tmin <= ts <= tmax):
            continue
        k = (ts, r["Volcan"], r["Sensor"])
        historia.setdefault(k, []).append((c["committer_utc"], r["Fecha_Proceso_GitHub"], r["Ultima_Actualizacion"]))
        if k not in primera:
            primera[k] = dict(ts=ts, volcan=r["Volcan"], sensor=r["Sensor"], fecha_utc=r["Fecha_Satelite_UTC"],
                              commit_utc=c["committer_utc"], sha=c["sha"][:10],
                              fproc=r["Fecha_Proceso_GitHub"], ultima=r["Ultima_Actualizacion"])
print("commits con rango insuficiente:", cobertura_mala)
# filas cuya pasada ya estaba antes del primer commit no sirven (no vemos su aparicion)
t0 = utc(coms[0]["committer_utc"])
validas = [p for p in primera.values() if utc(p["commit_utc"]) > t0]
print("filas con pasada en ventana:", len(primera), "| primera aparicion observable (no en el 1er commit):", len(validas))

def dif_min(p, hip):
    f = datetime.strptime(p["fproc"], "%Y-%m-%d %H:%M:%S")
    if hip == "Santiago":
        f = f.replace(tzinfo=Z)
    elif hip == "UTC":
        f = f.replace(tzinfo=timezone.utc)
    else:
        f = f.replace(tzinfo=timezone(timedelta(hours=hip)))
    return (utc(p["commit_utc"]) - f).total_seconds() / 60

for hip in ["Santiago", "UTC", -3, -4]:
    d = sorted(dif_min(p, hip) for p in validas)
    if d:
        dentro = sum(0 <= x <= 5 for x in d)
        print(f"  hipotesis Fecha_Proceso en {hip}: commit - Fecha_Proceso (min) min {d[0]:.1f} mediana {d[len(d)//2]:.1f} max {d[-1]:.1f}; en [0,5] min: {dentro}/{len(d)}")

# estabilidad de Fecha_Proceso y comportamiento de Ultima_Actualizacion
cambia_fproc = sum(len(set(h[1] for h in v)) > 1 for v in historia.values())
print("filas cuyo Fecha_Proceso_GitHub cambia entre commits:", cambia_fproc, "de", len(historia))
# Ultima_Actualizacion: hora del ultimo commit en que cambio, contra su valor leido como Santiago
dd = []
for k, v in historia.items():
    ult = v[-1][2]
    # primer commit donde aparece ese valor final
    c_first = next(h[0] for h in v if h[2] == ult)
    if utc(c_first) > t0:
        f = datetime.strptime(ult, "%Y-%m-%d %H:%M:%S").replace(tzinfo=Z)
        dd.append((utc(c_first) - f).total_seconds() / 60)
dd.sort()
if dd:
    print(f"Ultima_Actualizacion (Santiago) vs commit donde toma su valor final: min {dd[0]:.1f} mediana {dd[len(dd)//2]:.1f} max {dd[-1]:.1f} min (n={len(dd)})")
n_val_ult = [len(set(h[2] for h in v)) for v in historia.values()]
print("valores distintos de Ultima_Actualizacion por fila: mediana", sorted(n_val_ult)[len(n_val_ult)//2], "max", max(n_val_ult))

with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(validas[0].keys()) + ["n_commits_visto"])
    w.writeheader()
    for p in sorted(validas, key=lambda p: p["ts"]):
        w.writerow({**p, "n_commits_visto": len(historia[(p["ts"], p["volcan"], p["sensor"])])})
print("escrito", out)
