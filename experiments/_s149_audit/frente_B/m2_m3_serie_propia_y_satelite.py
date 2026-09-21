# -*- coding: utf-8 -*-
"""Frente B. M2: huecos y regimenes de NUESTRA serie (data/mirova_equivalent, 11 Tier A).
M3: por satelite y por mes, que fraccion de nuestras pasadas NOCTURNAS tiene fila en la tabla
(canal CONS) a +-120 s, mismo volcan y mismo bucket; y cuantas solo en OCR.

Instrumento:
1. Si la tabla dejara de listar un satelite, lo veria? SI: la tasa de ese satelite cae. Control
   positivo: desplazar las horas de la tabla 30 min debe llevar la tasa cerca de 0.
2. Si el pareo estuviera muerto daria 0 en todo; se imprime n por celda, y una celda sin pasadas
   nuestras sale SIN DATO, no 0.
Noche = el mismo predicado del pipeline (auto_audit_weekly.es_pasada_diurna_descartada).
Ventana de la tabla: 2026-01-10 a hoy; nuestras pasadas fuera de esa ventana no entran en M3.
"""
import bisect, collections, csv, io, json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name  # noqa

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
coords = _coords_por_volcan()
DATA = ROOT / "data/mirova_equivalent"
SNAP = ROOT / "data/mirova_reference/mirova_v1_snapshot"


def bucket(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"


def sat(s):
    for k in ("SNPP", "NOAA20", "NOAA21", "TERRA", "AQUA"):
        if k in s: return k
    return s


recs = []
for v in VOLS:
    d = json.load(open(DATA / (v + ".json"), encoding="utf-8"))
    for r in d["records"]:
        s = r.get("sensor") or ""
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        recs.append((v, s, dt, r.get("product_version"), r.get("granule") or ""))
print("records totales 11 Tier A:", len(recs), "| rango", min(x[2] for x in recs), "a", max(x[2] for x in recs))
print("sensores:", collections.Counter(x[1] for x in recs))

# ---------- M2a huecos > 5 dias por volcan (cualquier sensor)
print("\n[M2a] huecos de mas de 5 dias sin NINGUN record, por volcan")
for v in VOLS:
    ts = sorted(x[2] for x in recs if x[0] == v)
    hs = [(a, b) for a, b in zip(ts, ts[1:]) if (b - a) > timedelta(days=5)]
    print("  %-20s primero %s | huecos: %s" % (v, ts[0].date(), ["%s a %s (%d d)" % (a.date(), b.date(), (b - a).days) for a, b in hs] or "ninguno"))
# por sensor-satelite: primer y ultimo record, huecos > 10 d (agregado 11 volcanes)
print("\n[M2b] por sensor: primero, ultimo, huecos > 10 dias (los 11 volcanes juntos)")
for s in sorted(set(x[1] for x in recs)):
    ts = sorted(x[2] for x in recs if x[1] == s)
    hs = [(a, b) for a, b in zip(ts, ts[1:]) if (b - a) > timedelta(days=10)]
    print("  %-18s n=%6d %s a %s | %s" % (s, len(ts), ts[0].date(), ts[-1].date(), ["%s a %s" % (a.date(), b.date()) for a, b in hs] or "sin huecos"))

# ---------- M2c product_version por mes
print("\n[M2c] product_version por mes (todos los records): mes | n | % nrt | % standard | otros")
pm = collections.defaultdict(collections.Counter)
for x in recs:
    pm[x[2].strftime("%Y-%m")][x[3]] += 1
for m in sorted(pm):
    n = sum(pm[m].values())
    print("  %s | %5d | %5.1f | %5.1f | %s" % (m, n, 100.0 * pm[m]["nrt"] / n, 100.0 * pm[m]["standard"] / n, {k: c for k, c in pm[m].items() if k not in ("nrt", "standard")}))
# por bucket en 2026-08/09 (MODIS NRT se etiquetaba standard hasta #659)
print("  por bucket, desde 2026-06: mes bucket %nrt n")
pb = collections.defaultdict(collections.Counter)
for x in recs:
    if x[2] >= datetime(2026, 6, 1, tzinfo=timezone.utc):
        pb[(x[2].strftime("%Y-%m"), bucket(x[1]))][x[3]] += 1
for k in sorted(pb):
    n = sum(pb[k].values()); print("   ", k, "%.1f" % (100.0 * pb[k]["nrt"] / n), n)
# contradiccion etiqueta vs nombre del granulo
contra = collections.Counter()
for x in recs:
    es_nrt_nombre = "NRT" in x[4].upper()
    if x[4]:
        contra[(bucket(x[1]), x[3], "granulo_NRT" if es_nrt_nombre else "granulo_std")] += 1
print("  etiqueta contra nombre del granulo:", dict(contra))

# ---------- M3
cons = collections.defaultdict(list); ocr = collections.defaultdict(list)
for path, dest in ((SNAP / "registro_vrp_consolidado.csv", cons), (SNAP / "registro_vrp_ocr.csv", ocr)):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        v = normalize_volcano_name(r.get("Volcan")); b = normalize_sensor(r.get("Sensor"))
        f = (r.get("Fecha_Satelite_UTC") or "")[:19]
        if v is None or len(f) < 19: continue
        dest[(v, b)].append(datetime.strptime(f, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc))
for d in (cons, ocr):
    for k in d: d[k].sort()
print("\nbuckets normalizados de la tabla:", sorted(set(k[1] for k in cons)))
T0 = datetime(2026, 1, 10, 19, 6, tzinfo=timezone.utc)
T1 = max(max(v) for v in cons.values())


def hay(lista, t, tol=120, shift=0):
    t = t + timedelta(seconds=shift)
    i = bisect.bisect_left(lista, t - timedelta(seconds=tol))
    return i < len(lista) and lista[i] <= t + timedelta(seconds=tol)


def tabla_m3(shift=0, etiqueta=""):
    cel = collections.defaultdict(lambda: [0, 0, 0])  # n, con fila CONS, solo OCR
    for v, s, dt, pv, g in recs:
        if not (T0 <= dt <= T1): continue
        b = bucket(s)
        if b is None: continue
        lat, lon = coords[v]
        if es_pasada_diurna_descartada(b, lat, lon, dt): continue
        c = cel[(b, sat(s), dt.strftime("%Y-%m"))]
        c[0] += 1
        if hay(cons.get((v, b), []), dt, shift=shift): c[1] += 1
        elif hay(ocr.get((v, b), []), dt, shift=shift): c[2] += 1
    print("\n[M3%s] bucket satelite | por mes: %% de nuestras pasadas nocturnas con fila en la TABLA (n) [+solo OCR]" % etiqueta)
    meses = sorted(set(k[2] for k in cel))
    print("   %-22s" % "" + " ".join("%-15s" % m for m in meses))
    for b, st in sorted(set((k[0], k[1]) for k in cel)):
        fila = []
        for m in meses:
            n, a, o = cel.get((b, st, m), [0, 0, 0])
            fila.append("%-15s" % ("%.0f%% (%d)+%d" % (100.0 * a / n, n, o) if n else "SIN DATO"))
        print("   %-22s" % (b + " " + st) + " ".join(fila))
    return cel


cel = tabla_m3()
tabla_m3(shift=1800, etiqueta=" CONTROL: tabla desplazada 30 min, debe dar cerca de 0")

# ---------- M3b: el reverso. Filas nocturnas VIIRS de la tabla: a que satelite NUESTRO corresponden
print("\n[M3b] filas nocturnas de la TABLA por bucket y mes, repartidas segun el satelite de NUESTRO record a +-120 s")
nuestros = collections.defaultdict(list)
for v, s, dt, pv, g in recs:
    nuestros[(v, bucket(s))].append((dt, sat(s)))
for k in nuestros: nuestros[k].sort()
rev = collections.defaultdict(collections.Counter)
for (v, b), ts in cons.items():
    if b == "MODIS" or v not in coords: continue
    lst = nuestros.get((v, b), []); tt = [x[0] for x in lst]
    lat, lon = coords[v]
    for t in ts:
        if es_pasada_diurna_descartada(b, lat, lon, t): continue
        i = bisect.bisect_left(tt, t - timedelta(seconds=120))
        quien = lst[i][1] if i < len(lst) and lst[i][0] <= t + timedelta(seconds=120) else "sin_record_nuestro"
        rev[(b, t.strftime("%Y-%m"))][quien] += 1
for k in sorted(rev):
    n = sum(rev[k].values())
    print("   %s %s n=%4d | %s" % (k[0], k[1], n, "  ".join("%s %.0f%%" % (q, 100.0 * c / n) for q, c in sorted(rev[k].items()))))
