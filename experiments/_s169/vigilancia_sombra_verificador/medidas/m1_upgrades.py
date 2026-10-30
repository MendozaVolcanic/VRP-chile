"""M1. PREGUNTAS DEL INSTRUMENTO
1) Si el upgrade NRT->standard ocurriera a diario sobre la ventana, ¿esta medicion lo veria? Si: mide records cuyo
   processed_utc difiere de first_processed_utc (reescritos) y su edad respecto de la pasada (datetime_utc).
2) Si el instrumento estuviera muerto (sin campos), ¿se veria distinto? Se imprime el denominador de records con ambos campos.
Control positivo: en cualquier volcan con NRT activo hay reescrituras (processed != first) si el upgrade existe; si el conteo da 0
con denominador >0, el upgrade no deja huella en esos campos (limite del instrumento).
Datos: origin/main (a33070b9, 2026-10-30 04:33 UTC) data/mirova_equivalent/<Volcan>.json via git show, solo lectura.
"""
import json, subprocess, sys, collections
from datetime import datetime
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
vol = sys.argv[1]
raw = subprocess.run(["git", "-C", REPO, "show", f"origin/main:data/mirova_equivalent/{vol}.json"], capture_output=True, env={"MSYS_NO_PATHCONV": "1", **__import__('os').environ}).stdout
d = json.loads(raw)
recs = d["records"]
P = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
D = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M")
n_total = len(recs)
con = [r for r in recs if r.get("processed_utc") and r.get("first_processed_utc")]
print(f"{vol}: records {n_total}, con processed_utc y first_processed_utc: {len(con)}")
rew = [r for r in con if r["processed_utc"] != r["first_processed_utc"]]
print(f"reescritos (processed != first): {len(rew)}")
by_pv = collections.Counter((r.get("product_version"),) for r in rew)
print("reescritos por product_version actual:", dict(by_pv))
# retraso entre primera aparicion y reescritura, y edad de la pasada al reescribir
dias_ret = collections.Counter()
for r in rew:
    ret = (P(r["processed_utc"]) - P(r["first_processed_utc"])).days
    dias_ret[min(ret, 15)] += 1
print("dias entre first y processed (>=15 agrupado):", sorted(dias_ret.items()))
# ventana reciente: processed_utc en los ultimos 20 dias de datos
ult = max(P(r["processed_utc"]) for r in con)
print("ultimo processed_utc:", ult)
rec_rew = collections.Counter()
for r in rew:
    p = P(r["processed_utc"])
    if (ult - p).days <= 20:
        edad = (p - D(r["datetime_utc"])).days
        rec_rew[(p.date().isoformat(), r.get("product_version"), edad)] += 1
print("reescrituras por dia de proceso, product_version, edad en dias de la pasada (ult 20 d):")
for k, v in sorted(rec_rew.items())[:60]:
    print("  ", k, v)
# records NRT que quedaron con mas de 8 dias
nrt_viejos = [r for r in recs if r.get("product_version") == "nrt" and r.get("processed_utc") and (ult - D(r["datetime_utc"])).days > 8]
print("records product_version=nrt con pasada de >8 dias:", len(nrt_viejos), "de", sum(1 for r in recs if r.get("product_version")=="nrt"))
print("product_version global:", dict(collections.Counter(r.get("product_version") for r in recs)))
