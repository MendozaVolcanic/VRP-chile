# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 1: el pareo pasada nuestra <-> fila de MIROVA.

PREGUNTAS DEL INSTRUMENTO
 1. Si el pareo estuviera roto (tolerancia corta, satelites mezclados), esta sonda lo veria? Si: mide
    la distribucion de desfases de cada fila de MIROVA a la pasada nuestra mas cercana del mismo
    volcan y sensor, cuenta las filas que caen FUERA de +-120 s pero dentro de +-15 min, y cuenta
    pasadas nuestras de satelites distintos que caen a +-120 s entre si (la referencia no trae satelite).
 2. Si la sonda estuviera muerta, se veria distinto? Control positivo: desplazo todas nuestras pasadas
    +5 min y el pareo a +-120 s tiene que caer a casi cero.

Uso: python d1_pareo.py <dir_brazo> <dir_congelado> <desde> <hasta>
"""
import bisect, collections, io, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada

d_brazo, d_cong, desde, hasta = sys.argv[1:5]
ventana = (desde, hasta)
coords = bp._coords_por_volcan()
filas = cargar_referencia_unificada(Path(d_cong) / "registro_vrp_consolidado.csv", Path(d_cong) / "registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)

# nuestras pasadas nocturnas, sin node (solo tiempos)
ours = collections.defaultdict(list)
for vol in bp.VOLS:
    p = Path(d_brazo) / f"{vol}.json"
    if not p.exists():
        continue
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (desde <= r.get("datetime_utc", "")[:10] <= hasta):
            continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        lat, lon = coords[vol]
        if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        ours[(vol, b)].append((dt, r.get("sensor"), r.get("granule")))
for v in ours.values():
    v.sort()


def desfases(shift_s=0):
    hist = collections.Counter(); fuera = collections.Counter(); ejemplos = []
    for (vol, b), lista in por_vb.items():
        ts = [x[0] + timedelta(seconds=shift_s) for x in ours.get((vol, b), [])]
        for dt, f in lista:
            i = bisect.bisect_left(ts, dt)
            cands = [abs((ts[j] - dt).total_seconds()) for j in (i - 1, i) if 0 <= j < len(ts)]
            d = min(cands) if cands else None
            tipo = "ALERTA" if bp.es_alerta(f["tipo"]) else ("FP" if bp.es_fp(f["tipo"]) else "RUTINA")
            if d is None:
                k = "sin_pasada_nuestra"
            elif d <= 120:
                k = "<=120s"
            elif d <= 900:
                k = "120s-15min"
                if len(ejemplos) < 12 and tipo == "ALERTA":
                    ejemplos.append((vol, b, f["fecha_utc"], f["source"], f["vrp_mw"], round(d)))
            else:
                k = ">15min"
            hist[(b, tipo, k)] += 1
    return hist, ejemplos


h, ej = desfases()
print("ventana", ventana, "| filas nocturnas de referencia", n_ref)
for b in bp.BUCKETS:
    for tipo in ("ALERTA", "RUTINA", "FP"):
        tot = sum(v for (bb, t, k), v in h.items() if bb == b and t == tipo)
        if tot:
            print("  %-8s %-6s n %5d | %s" % (b, tipo, tot, {k: v for (bb, t, k), v in h.items() if bb == b and t == tipo}))
print("  ejemplos de ALERTA entre 120 s y 15 min de nuestra pasada mas cercana:")
for e in ej:
    print("    ", e)

# satelites distintos a +-120 s entre si, mismo volcan y sensor
choques = collections.Counter(); ej2 = []
for (vol, b), lista in ours.items():
    for i in range(1, len(lista)):
        a, c = lista[i - 1], lista[i]
        if (c[0] - a[0]).total_seconds() <= 120 and a[1] != c[1]:
            choques[(b, a[1], c[1])] += 1
            if len(ej2) < 5:
                ej2.append((vol, a[0].isoformat(), a[1], c[1]))
mismo = collections.Counter()
for (vol, b), lista in ours.items():
    for i in range(1, len(lista)):
        a, c = lista[i - 1], lista[i]
        if (c[0] - a[0]).total_seconds() <= 120 and a[1] == c[1]:
            mismo[b] += 1
print("pasadas nuestras de satelites DISTINTOS a +-120 s (mismo volcan y sensor):", dict(choques), ej2)
print("pasadas nuestras del MISMO satelite a +-120 s (granulos contiguos o duplicados):", dict(mismo))

# control positivo: desplazar +5 min
h5, _ = desfases(300)
tot = sum(v for (b, t, k), v in h5.items() if t == "ALERTA")
ok = sum(v for (b, t, k), v in h5.items() if t == "ALERTA" and k == "<=120s")
print("CONTROL POSITIVO (+5 min): ALERTAS pareadas a +-120 s %d de %d" % (ok, tot))
