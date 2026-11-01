"""VB v07: alertas de MIROVA en VIIRS 750 ("VIIRS" en el CSV) de 1 MW o mas, DIURNAS sobre el volcan, y si
produccion tiene record en esa pasada (cualquier plataforma VIIRS 750, +-10 min). Todos los volcanes Tier A,
no solo Chillan (camino distinto al del auditor). Fuente: latest_consolidado.csv (canal tabla; A119: desde 2026-03 la
tabla es sana; en esta ventana sale el aviso del OCR, que aqui no se usa).
Dia: elevacion solar > 0 con pipeline.store._solar_elevation (la misma funcion que decide el rechazo).
Control positivo: las mismas alertas de 1 MW o mas pero NOCTURNAS: produccion deberia tener record en casi todas.
Pregunta 1: si el rechazo diurno no existiera, las diurnas tendrian record como las nocturnas. Pregunta 2: si el
pareo de tiempo estuviera roto, las nocturnas tampoco tendrian record (eso seria SIN DATO).
Ventana: 2026-03-01 a 2026-10-21. Denominador: alertas ALERTA_TERMICA con VRP_MW >= 1.
"""
import csv, json, os, sys, io, glob
from datetime import datetime, timedelta
from collections import defaultdict, Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.store import _solar_elevation
import yaml
vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml")))["volcanoes"]}
norm = lambda s: s.replace(" ", "").replace("-", "").lower()
nombre = {norm(k): k for k in vols}
nombre[norm("Puyehue-Cordon Caulle")] = "PuyehueCordonCaulle"
rec = defaultdict(list)
for f in glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json")):
    v = os.path.basename(f)[:-5]
    for r in json.load(open(f))["records"]:
        if r["sensor"].endswith("_750"):
            rec[v].append(datetime.fromisoformat(r["datetime_utc"].replace("Z", "")[:16]))
cont = Counter(); faltan = []
for row in csv.DictReader(open(os.path.join(REPO, "latest_consolidado.csv"), encoding="utf-8")):
    if row["Sensor"] != "VIIRS" or not row["Tipo_Registro"].startswith("ALERTA"):
        continue
    try:
        vrp = float(row["VRP_MW"])
    except ValueError:
        continue
    t = datetime.fromisoformat(row["Fecha_Satelite_UTC"][:16])
    if vrp < 1 or not ("2026-03-01" <= row["Fecha_Satelite_UTC"][:10] <= "2026-10-21"):
        continue
    v = nombre.get(norm(row["Volcan"]))
    if v is None or v not in rec:
        cont[("sin_volcan_en_produccion", row["Volcan"])] += 1; continue
    dia = _solar_elevation(vols[v]["lat"], vols[v]["lon"], t) > 0
    hay = any(abs((x - t).total_seconds()) <= 600 for x in rec[v])
    cont[("dia" if dia else "noche", "con_record" if hay else "sin_record")] += 1
    if dia and not hay:
        faltan.append((v, row["Fecha_Satelite_UTC"], vrp, row["Tipo_Registro"], row["Distancia_km"]))
print("conteo:", dict(cont))
print("diurnas >= 1 MW sin record (volcan, hora UTC, VRP, tipo, distancia):")
for x in sorted(faltan): print("  ", x)
print("por volcan:", Counter(x[0] for x in faltan))
