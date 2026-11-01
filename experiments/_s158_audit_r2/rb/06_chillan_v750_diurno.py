"""Afirmación 6: alertas de MIROVA de VIIRS 750 en Nevados de Chillán de 1 MW o más (protegida, lectura A:
tipo ALERTA_TERMICA o ALERTA_TERMICA_OCR, scripts/clase_mirova.py:65) que son DIURNAS según la definición del
código (pipeline/store.py:218: se rechaza si _solar_elevation(lat, lon, datetime_utc) > 0 en el volcán;
fetch.py:1018 descarta antes de bajar si elev < 0 es falso) y que no tienen record nuestro publicado
(data/mirova_equivalent/NevadosDeChillan.json, sensor *_750, pareo a +-120 s como banco_paridad.TOL_S).
Referencia: latest_consolidado.csv (tabla) + registro_vrp_ocr.csv del snapshot (OCR), Sensor 'VIIRS' = 750
(scripts/referencia_mirova_unificada.normalize_sensor). Ventanas: toda la referencia (desde 2026-01-10),
desde 2026-03-01 (tabla sana, A119) y V1 2026-08-29..2026-10-18. También informa lo mismo para las nocturnas
(control: las nocturnas protegidas deben tener record casi siempre) y para 375.
Pregunta 1: si el rechazo diurno no existiera, las diurnas tendrían record; si la elevación solar estuviera
mal, el reparto día/noche por hora UTC se vería raro (se imprime la hora UTC de cada diurna).
Pregunta 2: si el CSV no cargara o el pareo fallara siempre, 'con record' daría 0 también para las nocturnas."""
import sys, io, os, csv
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
from pipeline.store import _solar_elevation
from referencia_mirova_unificada import normalize_sensor, normalize_volcano_name
import json, bisect
LAT, LON = -36.863, -71.377     # volcanoes.yaml:249-250
TOL = 120
def cargar(path, fuente):
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if normalize_volcano_name(r.get("Volcan")) != "NevadosDeChillan": continue
        f = (r.get("Fecha_Satelite_UTC") or "").strip()
        if len(f) < 16: continue
        try: v = float(r.get("VRP_MW") or 0)
        except ValueError: v = 0.0
        out.append({"fecha": f[:19], "bucket": normalize_sensor(r.get("Sensor")), "vrp": v, "tipo": r.get("Tipo_Registro"), "fuente": fuente, "raw": r.get("Sensor")})
    return out
ref = cargar("latest_consolidado.csv", "tabla") + cargar("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", "ocr")
print("filas NdC:", Counter((f["fuente"], f["bucket"]) for f in ref))
print("normalize_sensor('VIIRS') =", normalize_sensor("VIIRS"), "| normalize_sensor('VIIRS375') =", normalize_sensor("VIIRS375"))
recs = json.load(open("data/mirova_equivalent/NevadosDeChillan.json", encoding="utf-8")); recs = recs["records"] if isinstance(recs, dict) else recs
def bucket_ours(s): return "MODIS" if s.startswith("MODIS") else "VIIRS750" if s.endswith("_750") else "VIIRS375"
nuestros = defaultdict(list)
for r in recs:
    nuestros[bucket_ours(r["sensor"])].append(datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M"))
for k in nuestros: nuestros[k].sort()
def tiene_record(b, t):
    L = nuestros.get(b, []); i = bisect.bisect_left(L, t - timedelta(seconds=TOL))
    return i < len(L) and L[i] <= t + timedelta(seconds=TOL)
PROT = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")
def tabla(desde, hasta, b):
    # una pasada = (bucket, fecha al minuto); protegida si alguna fila (tabla u OCR) es alerta >= 1 MW
    pas = {}
    for f in ref:
        if f["bucket"] != b or not (desde <= f["fecha"][:10] <= hasta): continue
        k = f["fecha"][:16]
        pas.setdefault(k, {"prot": False, "vrp": 0.0, "tipos": set()})
        pas[k]["tipos"].add(f["tipo"])
        if f["tipo"] in PROT and f["vrp"] >= 1.0:
            pas[k]["prot"] = True; pas[k]["vrp"] = max(pas[k]["vrp"], f["vrp"])
    n = Counter(); diurnas = []
    for k, p in pas.items():
        t = datetime.strptime(k, "%Y-%m-%d %H:%M")
        elev = _solar_elevation(LAT, LON, t)
        dia = elev > 0
        rec = tiene_record(b, t)
        n[("pasadas", dia)] += 1
        if p["prot"]:
            n[("protegidas", dia)] += 1
            if not rec: n[("protegidas_sin_record", dia)] += 1
            else: n[("protegidas_con_record", dia)] += 1
            if dia: diurnas.append((k, round(elev, 1), p["vrp"], sorted(p["tipos"]), rec))
    print(f"\n== {b} {desde}..{hasta}: pasadas de la referencia noche={n[('pasadas',False)]} dia={n[('pasadas',True)]}")
    print(f"   protegidas (>=1 MW, lectura A): noche={n[('protegidas',False)]} (sin record nuestro {n[('protegidas_sin_record',False)]}) | "
          f"dia={n[('protegidas',True)]} (sin record nuestro {n[('protegidas_sin_record',True)]}, con record {n[('protegidas_con_record',True)]})")
    for d in sorted(diurnas): print("      diurna protegida:", d)
for b in ("VIIRS750", "VIIRS375"):
    tabla("2026-01-10", "2026-10-21", b)
    tabla("2026-03-01", "2026-10-21", b)
    tabla("2026-08-29", "2026-10-18", b)
# Control del instrumento día/noche: distribución de elevación solar de las pasadas 750 de la referencia por hora UTC
print("\nControl: horas UTC de las pasadas VIIRS750 de la referencia clasificadas de día (elev>0):")
hh = Counter(datetime.strptime(f["fecha"][:16], "%Y-%m-%d %H:%M").hour for f in ref if f["bucket"] == "VIIRS750" and _solar_elevation(LAT, LON, datetime.strptime(f["fecha"][:16], "%Y-%m-%d %H:%M")) > 0)
print("  ", dict(sorted(hh.items())))
hn = Counter(datetime.strptime(f["fecha"][:16], "%Y-%m-%d %H:%M").hour for f in ref if f["bucket"] == "VIIRS750" and _solar_elevation(LAT, LON, datetime.strptime(f["fecha"][:16], "%Y-%m-%d %H:%M")) <= 0)
print("   de noche:", dict(sorted(hn.items())))
print("\nRecords nuestros VIIRS750 de NdC por hora UTC (ninguno debe ser diurno):", dict(sorted(Counter(t.hour for t in nuestros["VIIRS750"]).items())))
