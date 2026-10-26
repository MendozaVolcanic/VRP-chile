"""v05_reposicion.py (A5, instrumento propio): para cada fila del archivo de reposicion de la rama s163
(2.351), busca su llave en el PADRE de cada commit de mezcla (los 16 que uso el autor + 53b1e6d3c0^),
bajando cada version por raw.githubusercontent.com (no toca el clon), y compara campo a campo:
(a) todas las columnas menos las dos UTC; (b) las dos UTC: iguales al padre, o vacias en el padre y
derivables de la hora de Chile (America/Santiago -> UTC); (c) la llave no esta hoy en main (clon);
(d) nombres canonicos y tipos; (e) repetidas dentro del archivo; (f) protegidas (ALERTA_TERMICA >= 1 MW)."""
import csv, io, os, subprocess, sys, time, urllib.request, collections
import pytz
from datetime import datetime
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"
AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
EPIS = ["79b9033e90", "74af2c3899", "b1dc9640c0", "e555d63337", "c05dc4d778", "85089b8a60",
        "9d70bc2d53", "8825bb4057", "fb2a3123f8", "f843a1ead6", "8e04975286", "dc5e5c0121", "81c06c52ab",
        "f1eaeaf74f", "c292d6b267", "ecdc09e4d6", "53b1e6d3c0"]
def git(*a):
    return subprocess.run(["git", "-C", CLON] + list(a), capture_output=True, check=True).stdout.decode("utf-8")
def leer_raw(sha):
    url = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}"
    for i in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise RuntimeError(f"{sha}: {err}")
def llave(f):
    return ((f.get("timestamp") or "").strip(), (f.get("Volcan") or "").strip(), (f.get("Sensor") or "").strip())
rep = list(csv.DictReader(io.StringIO(git("show", "s163/d39-reposicion-y-bucle:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv"))))
pr = list(csv.DictReader(io.StringIO(git("show", "pr26:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv"))))
print("filas s163", len(rep), "filas pr26", len(pr), "las primeras", len(pr), "de s163 == pr26:", rep[:len(pr)] == pr, flush=True)
kr = [llave(f) for f in rep]
print("llaves distintas", len(set(kr)), "repetidas", len(kr) - len(set(kr)), flush=True)
hoy = {llave(f) for f in csv.DictReader(io.StringIO(git("show", f"main:{RUTA}")))}
print("presentes hoy en main (clon f5fe3b9a64):", sum(k in hoy for k in kr), flush=True)
# nombres canonicos
exec(compile(git("show", "s163/d39-reposicion-y-bucle:volcanes.py"), "volcanes.py", "exec"), ns := {})
NOMBRES = {v["nombre"] for v in ns["VOLCANES_CONFIG"].values()}
print("nombres no canonicos:", collections.Counter(f["Volcan"] for f in rep if f["Volcan"] not in NOMBRES), flush=True)
print("tipos:", collections.Counter(f["Tipo_Registro"] for f in rep), flush=True)
prot = [f for f in rep if f["Tipo_Registro"] == "ALERTA_TERMICA" and float(f["VRP_MW"] or 0) >= 1.0]
print("protegidas:", len(prot), flush=True)
for f in prot:
    print("   ", f["Fecha_Satelite_UTC"], f["Volcan"], f["Sensor"], f["VRP_MW"], f["Distancia_km"], flush=True)
# padres
pend = set(kr)
padres = {}
for e in EPIS:
    padre = git("rev-parse", e + "^").strip()
    t0 = time.time()
    rows = {}
    hijo_keys = None
    for f in csv.DictReader(io.StringIO(leer_raw(padre))):
        k = llave(f)
        if k in pend:
            rows[k] = f
    padres[e] = rows
    print(f"padre de {e} = {padre[:10]}: {len(rows)} de las llaves buscadas ({time.time()-t0:.0f}s)", flush=True)
UTC = {"Fecha_Proceso_UTC", "Ultima_Actualizacion_UTC"}
PAR = {"Fecha_Proceso_UTC": "Fecha_Proceso_GitHub", "Ultima_Actualizacion_UTC": "Ultima_Actualizacion"}
tz = pytz.timezone("America/Santiago")
def derivable(chile, utc):
    if not chile:
        return utc == ""
    try:
        d = datetime.strptime(chile, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    try:
        loc = tz.localize(d, is_dst=None)
    except Exception:
        return utc == ""   # ambigua o inexistente: el backfill la deja vacia
    return loc.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ") == utc
res = collections.Counter(); detalle = []
for f in rep:
    k = llave(f)
    cands = [e for e in EPIS if k in padres[e]]
    if not cands:
        res["sin padre entre los 17"] += 1; detalle.append(("sin padre", k)); continue
    ok_no_utc = [e for e in cands if all((padres[e][k].get(c) or "") == (f.get(c) or "") for c in f if c not in UTC)]
    if not ok_no_utc:
        res["en padre pero distinta fuera de UTC"] += 1
        e = cands[0]; dif = [(c, padres[e][k].get(c), f.get(c)) for c in f if c not in UTC and (padres[e][k].get(c) or "") != (f.get(c) or "")]
        detalle.append(("campo", k, e, dif[:3])); continue
    ident = [e for e in ok_no_utc if all((padres[e][k].get(c) or "") == (f.get(c) or "") for c in UTC)]
    if ident:
        res["identica campo a campo a un padre"] += 1; continue
    e = ok_no_utc[0]
    if all(((padres[e][k].get(c) or "") == "" and derivable(f.get(PAR[c]) or "", f.get(c) or "")) for c in UTC):
        res["igual salvo UTC vacias en el padre y derivadas de la hora de Chile"] += 1
    else:
        res["UTC distintas y no derivables"] += 1
        detalle.append(("utc", k, e, [(c, padres[e][k].get(c), f.get(c), f.get(PAR[c])) for c in UTC]))
print("RESULTADO", dict(res), flush=True)
for d in detalle[:40]:
    print("  ", d, flush=True)
# las 241 de s163: identicas a 53b1e6d3c0^?
k241 = [llave(f) for f in rep[len(pr):]]
p = padres["53b1e6d3c0"]
print("241 agregadas: en 53b1e6d3c0^", sum(k in p for k in k241), "identicas campo a campo",
      sum(k in p and all((p[k].get(c) or "") == (f.get(c) or "") for c in f) for k, f in zip(k241, rep[len(pr):])), flush=True)
print("FIN", flush=True)
