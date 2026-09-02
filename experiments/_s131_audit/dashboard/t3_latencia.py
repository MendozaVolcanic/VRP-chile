# -*- coding: utf-8 -*-
"""S131 T3 - Latencia pasada satelital -> dato en el dashboard.
READ-ONLY.

PLAN A descartado: el schema de record NO tiene ningun campo de tiempo de
proceso (ingested_at / processed_at / created_at / *_at). Verificado sobre las
75 claves distintas del corpus (ver bloque 0).

PLAN B (el que se usa): sello `updated` a nivel de archivo menos el
`datetime_utc` maximo de ese mismo archivo, para dos snapshots:
  - LOCAL   data/mirova_equivalent/<vol>.json          (escritura del pipeline)
  - PUBLICADO scratchpad/pub/.../<vol>.json (_recent)  (copia servida del sitio)
Y la latencia total pasada -> publicado con el Last-Modified del sitio.
"""
import io, json, os, sys, glob
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PUB = (r"C:/Users/nmend/AppData/Local/Temp/claude/"
       r"C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/"
       r"d070441f-cd2d-4d91-960b-4815f3b595b9/scratchpad/pub/data/mirova_equivalent")
TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
          "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
          "Tupungatito", "Villarrica"]
# dato entregado por el usuario: cabecera HTTP del sitio publicado (Villarrica)
LAST_MODIFIED = datetime(2026, 9, 2, 16, 54, 32, tzinfo=timezone.utc)


def pu(s):
    """datetime_utc 'YYYY-MM-DD HH:MM' -> aware UTC."""
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def pi(s):
    """updated ISO 'YYYY-MM-DDTHH:MM:SSZ' -> aware UTC."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def q(vals, p):
    v = sorted(vals)
    if not v:
        return float('nan')
    k = (len(v) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


print("=== T3-0  el schema NO tiene campo de tiempo de proceso ===")
keys = set()
for vol in TIER_A:
    for r in json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                            encoding='utf-8'))['records']:
        keys |= set(r.keys())
cands = sorted(k for k in keys
               if any(t in k.lower() for t in
                      ('ingest', 'process', 'created', 'updated', 'fetch', '_at', 'publish')))
print("  claves distintas en record: %d" % len(keys))
print("  candidatas a tiempo-de-proceso: %s" % (cands or "NINGUNA -> se usa el PLAN B"))
print("  claves top-level del archivo : %s" % sorted(
    json.load(open(os.path.join(ROOT, 'data/mirova_equivalent/Villarrica.json'),
                   encoding='utf-8')).keys()))

rows = []
print("\n=== T3-A  ultima pasada procesada -> `updated` (2 snapshots) ===")
print("  %-22s %-17s %-21s %8s | %-17s %-21s %8s" %
      ("volcan", "LOCAL max_dt", "LOCAL updated", "h", "PUB max_dt", "PUB updated", "h"))
loc_h, pub_h = [], []
for vol in TIER_A:
    dl = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                        encoding='utf-8'))
    ml = max(pu(r['datetime_utc']) for r in dl['records'] if r.get('datetime_utc'))
    ul = pi(dl['updated'])
    hl = (ul - ml).total_seconds() / 3600.0
    dp = json.load(open(os.path.join(PUB, vol + '.json'), encoding='utf-8'))
    mp = max(pu(r['datetime_utc']) for r in dp['records'] if r.get('datetime_utc'))
    up = pi(dp['updated'])
    hp = (up - mp).total_seconds() / 3600.0
    loc_h.append(hl)
    pub_h.append(hp)
    rows.append((vol, ml, ul, hl, mp, up, hp))
    print("  %-22s %-17s %-21s %8.2f | %-17s %-21s %8.2f"
          % (vol, ml.strftime("%Y-%m-%d %H:%M"), ul.strftime("%Y-%m-%dT%H:%M:%SZ"), hl,
             mp.strftime("%Y-%m-%d %H:%M"), up.strftime("%Y-%m-%dT%H:%M:%SZ"), hp))
print("  n=11 volcanes, 1 medicion por snapshot")
print("  LOCAL  (snapshot 2026-09-01): mediana %.2f h   p90 %.2f h   min %.2f  max %.2f"
      % (q(loc_h, .5), q(loc_h, .9), min(loc_h), max(loc_h)))
print("  PUBLIC (snapshot 2026-09-02): mediana %.2f h   p90 %.2f h   min %.2f  max %.2f"
      % (q(pub_h, .5), q(pub_h, .9), min(pub_h), max(pub_h)))

print("\n=== T3-B  latencia total pasada -> publicado (Last-Modified del sitio) ===")
print("  Last-Modified entregado: %s (Villarrica _recent.json)"
      % LAST_MODIFIED.strftime("%Y-%m-%dT%H:%M:%SZ"))
tot_h = []
for vol, ml, ul, hl, mp, up, hp in rows:
    t = (LAST_MODIFIED - mp).total_seconds() / 3600.0
    d = (LAST_MODIFIED - up).total_seconds() / 3600.0
    tot_h.append(t)
    print("  %-22s pasada %s -> publicado: %6.2f h   (de los cuales %5.2f h son updated->publish)"
          % (vol, mp.strftime("%Y-%m-%d %H:%M"), t, d))
print("  n=11: mediana %.2f h  p90 %.2f h" % (q(tot_h, .5), q(tot_h, .9)))
print("  NOTA: el Last-Modified de GitHub Pages es el sello del DEPLOY, comun a")
print("        todos los archivos del sitio; se aplica el mismo a los 11.")

print("\n=== T3-C  confusor: NRT es nocturno -> `updated - max_dt` incluye tiempo SIN pasada ===")
print("  distribucion del hueco entre pasadas consecutivas, ultimos 30 dias del corpus local")
print("  %-22s %6s %8s %8s %8s" % ("volcan", "n_gaps", "mediana_h", "p90_h", "max_h"))
for vol in TIER_A:
    dl = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                        encoding='utf-8'))
    ts = sorted({pu(r['datetime_utc']) for r in dl['records'] if r.get('datetime_utc')})
    cut = ts[-1].timestamp() - 30 * 86400
    ts = [t for t in ts if t.timestamp() >= cut]
    gaps = [(b - a).total_seconds() / 3600.0 for a, b in zip(ts, ts[1:])]
    print("  %-22s %6d %8.2f %8.2f %8.2f"
          % (vol, len(gaps), q(gaps, .5), q(gaps, .9), max(gaps) if gaps else float('nan')))

print("\n=== T3-D  lo que NO se pudo medir ===")
print("  1. Latencia POR RECORD (pasada -> escritura). Requiere un sello de proceso")
print("     por record; el schema no lo tiene (T3-0). Solo hay 1 sello por archivo.")
print("  2. Distribucion temporal de la latencia (mediana/p90 sobre muchas corridas).")
print("     Con 1 sello por archivo hay 1 dato por volcan y por snapshot: los")
print("     percentiles de T3-A son ENTRE VOLCANES, no entre corridas.")
print("  3. Descontar el tiempo sin pasada. `updated - max_dt` mezcla latencia real")
print("     de proceso con el hueco diurno en que no hay granulo nocturno que")
print("     procesar (T3-C acota ese piso).")
print("  4. El tramo commit -> deploy de Pages por separado (prohibido usar git).")
