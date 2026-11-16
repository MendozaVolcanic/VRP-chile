# -*- coding: utf-8 -*-
"""V33A (verificador S175): un solo paso sobre los 11 JSON de mirova_equivalent para medir por otro camino
cinco afirmaciones de F0 y F1.

Pregunta 1 (si estuviera roto, lo veria): cada seccion imprime un control positivo que SEGURO cambia (un conteo
no nulo de la misma clase de record en otro sensor u otra ventana). Pregunta 2 (instrumento muerto): si el JSON
no se leyera, el total de records seria 0 y se imprime primero.

Uso: python -I v33a_escaneo_datos.py <carpeta data/mirova_equivalent> <etiqueta commit> <ruta volcanoes.yaml>
Salida por stdout (se guarda al lado con >).
"""
import io
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CARPETA, ETIQUETA, YAML = sys.argv[1], sys.argv[2], sys.argv[3]
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---- 116: centro del volcan contra vent en volcanoes.yaml (lectura minima del YAML, sin yaml.safe_dump) ----
print(f"# datos: {CARPETA} ({ETIQUETA}); yaml: {YAML}")
print("\n## 116. Distancia centro (lat/lon) a vent (vent_lat/vent_lon) por volcan Tier A, volcanoes.yaml")
vols = {}
cur = None
with open(YAML, encoding="utf-8") as fh:
    for line in fh:
        s = line.rstrip("\n")
        if s.startswith("- name:"):
            cur = s.split(":", 1)[1].strip().strip('"')
            vols[cur] = {}
        elif cur and s.startswith("  ") and not s.startswith("   ") and ":" in s and not s.strip().startswith("#"):
            k, v = s.strip().split(":", 1)
            if k in ("lat", "lon", "vent_lat", "vent_lon", "inner_radius_km"):
                try:
                    vols[cur][k] = float(v.split("#")[0].strip())
                except ValueError:
                    pass
for v in VOLS:
    d = vols.get(v, {})
    if all(k in d for k in ("lat", "lon", "vent_lat", "vent_lon")):
        print(f"  {v:22s} centro-vent = {hav(d['lat'], d['lon'], d['vent_lat'], d['vent_lon']):5.2f} km  inner={d.get('inner_radius_km')}")
    else:
        print(f"  {v:22s} sin vent_lat/vent_lon en el YAML (campos: {sorted(d)})")

# ---- lectura de los JSON ----
recs_por_vol = {}
total = 0
for v in VOLS:
    with open(f"{CARPETA}/{v}.json", encoding="utf-8") as fh:
        recs_por_vol[v] = json.load(fh).get("records") or []
    total += len(recs_por_vol[v])
print(f"\n# records leidos (11 Tier A): {total}  (0 = instrumento muerto)")
ult = max((r.get("datetime_utc") or "") for rs in recs_por_vol.values() for r in rs)
print(f"# ultimo datetime_utc: {ult}")

# ---- 117: records por volcan y noche (denominador de la VRE con DT_HOURS fijo) ----
print("\n## 117. Records nocturnos (solar_zenith_deg > 90) por volcan y noche, ultimos 60 dias de datos; "
      "n sensores distintos por noche")
fin = datetime.strptime(ult[:10], "%Y-%m-%d")
for v in VOLS:
    por_noche = defaultdict(set)
    por_noche_n = Counter()
    for r in recs_por_vol[v]:
        dt = r.get("datetime_utc") or ""
        if not dt:
            continue
        try:
            d = datetime.strptime(dt[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if (fin - d).days > 60:
            continue
        sz = r.get("solar_zenith_deg")
        if sz is None or sz <= 90:
            continue
        por_noche[dt[:10]].add(r.get("sensor"))
        por_noche_n[dt[:10]] += 1
    if por_noche_n:
        n = sorted(por_noche_n.values())
        print(f"  {v:22s} noches={len(n):3d} records/noche mediana={n[len(n)//2]} max={n[-1]}  "
              f"sensores/noche mediana={sorted(len(s) for s in por_noche.values())[len(n)//2]}")

# ---- 118: tope de 50 GW en VIIRS 375 ----
print("\n## 118. Records con diag_rejected_sanity_cap_mw o vrp_exceeds_sanity_cap, por sensor; vrp_mw maximo por sensor")
cap = Counter()
exc = Counter()
vmax = {}
sin_tmax = Counter()
n_sensor = Counter()
for v in VOLS:
    for r in recs_por_vol[v]:
        s = r.get("sensor") or "?"
        n_sensor[s] += 1
        if "diag_rejected_sanity_cap_mw" in r:
            cap[s] += 1
        if r.get("vrp_exceeds_sanity_cap"):
            exc[s] += 1
        vm = r.get("vrp_mw")
        if isinstance(vm, (int, float)) and (s not in vmax or vm > vmax[s][0]):
            vmax[s] = (vm, v, r.get("datetime_utc"))
        if r.get("t_max_k") is None and "t_max_i04_k" in r:
            sin_tmax[s] += 1
for s in sorted(n_sensor):
    print(f"  {s:18s} n={n_sensor[s]:6d} rechazados_cap={cap[s]} exceeds={exc[s]} "
          f"t_max_k None con t_max_i04_k={sin_tmax[s]} vrp_max={vmax.get(s)}")
print("  (control positivo del instrumento: n por sensor > 0; el cap solo actua sobre vrp > 50000 MW)")

# ---- 126: ultimo record Suomi NPP ----
print("\n## 126. Ultimo datetime_utc por satelite (control: NOAA-20 y NOAA-21 siguen)")
ult_sat = {}
for v in VOLS:
    for r in recs_por_vol[v]:
        s = r.get("sensor") or "?"
        dt = r.get("datetime_utc") or ""
        if dt > ult_sat.get(s, ("", ""))[0]:
            ult_sat[s] = (dt, v)
for s in sorted(ult_sat):
    print(f"  {s:18s} ultimo {ult_sat[s][0]} ({ult_sat[s][1]})")

# ---- 161: pixeles de la via sin vrp_mw ----
print("\n## 161. Records MODIS con via_codigo_mirova True: claves de anomaly_pixels; cuantos con >1 pixel")
via = 0
via_multi = 0
via_multi_sin_vrp = 0
claves = Counter()
k_multi_sin_vrp = Counter()
ejemplos = []
for v in VOLS:
    for r in recs_por_vol[v]:
        if r.get("via_codigo_mirova") is not True:
            continue
        via += 1
        px = r.get("anomaly_pixels") or []
        for p in px:
            claves[tuple(sorted(p))] += 1
        if len(px) > 1:
            via_multi += 1
            if all("vrp_mw" not in p for p in px):
                via_multi_sin_vrp += 1
                if len(ejemplos) < 5:
                    ejemplos.append((v, r.get("datetime_utc"), len(px), r.get("vrp_mw")))
k_sin_vrp = Counter()
for v in VOLS:
    for r in recs_por_vol[v]:
        if r.get("via_codigo_mirova") is True:
            continue
        s = r.get("sensor") or "?"
        if s.startswith("MODIS") and len(r.get("anomaly_pixels") or []) > 1:
            k_sin_vrp["K_multi"] += 1
            if all("vrp_mw" not in p for p in r["anomaly_pixels"]):
                k_sin_vrp["K_multi_sin_vrp"] += 1
print(f"  records via={via}; con >1 pixel={via_multi}; de esos sin vrp_mw en ningun pixel={via_multi_sin_vrp}")
print(f"  claves de pixel (via): {dict(claves)}")
print(f"  control (MODIS no-via con >1 pixel): {dict(k_sin_vrp)}  (si K tambien careciera de vrp_mw, el hallazgo no seria de la via)")
print(f"  ejemplos via multi-pixel sin vrp_mw (volcan, pasada UTC, n_pix, vrp_mw): {ejemplos}")
