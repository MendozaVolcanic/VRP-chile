# -*- coding: utf-8 -*-
"""VERIFICADOR S138 (discrepancia d): de las noches ALERTA de MIROVA que perdemos en un sensor con
el cumulo del crater en 0,0 MW, cuantas quedan CUBIERTAS por otra pasada del mismo volcan esa misma
noche en otro sensor.

POR QUE IMPORTA. La unidad en que el operador vive el recall es la NOCHE del volcan (A94), no la
noche-sensor. Una noche perdida en VIIRS750 que VIIRS375 si publica no es una alerta perdida: es un
sensor perdido. El eje 4 conto 33 de 246 noches-sensor; falta el paso a noches de volcan.

DOS PREGUNTAS DEL INSTRUMENTO.
 1. Si TODAS las noches perdidas estuvieran cubiertas por otro sensor, esto lo veria (cubierta=33) y
    si NINGUNA lo estuviera tambien (cubierta=0). Se imprimen las dos caras.
 2. Si el instrumento estuviera muerto (no encuentra records), la columna "n_records_esa_noche"
    saldria 0 y se marca SIN DATO, no "no cubierta".
Control positivo: se imprime una noche perdida en V750 con una pasada V375 visible el mismo dia,
con sus numeros, para poder mirarla a mano.

Mismo loader, mismo filtro diurno y mismo criterio de visible que el eje 4 (importados de sus
modulos originales, no reimplementados). READ-ONLY.
"""
import collections, io, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

# stdout: PYTHONIOENCODING=utf-8 (no re-envolver: el modulo del eje 4 tambien lo envuelve)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s138_audit" / "eje4"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.mirova_csv_loader import load_mirova_alertas
from auto_audit_weekly import es_pasada_diurna_descartada, _coords_por_volcan
import importlib.util
spec = importlib.util.spec_from_file_location(
    "eje4_01", ROOT / "experiments" / "_s138_audit" / "eje4" / "01_pc0_noches.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bucket, visible_dashboard, VOLS, BUCKETS, SNAP = m.bucket, m.visible_dashboard, m.VOLS, m.BUCKETS, m.SNAP

alertas = load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"),
                              ocr_path=str(SNAP / "registro_vrp_ocr.csv"))
coords = _coords_por_volcan()
fechas = sorted(a["fecha_utc"][:10] for a in alertas)
GT_INI, GT_FIN = fechas[0], fechas[-1]
print(f"Ventana de la referencia MIROVA: {GT_INI} a {GT_FIN}; {len(alertas)} pasadas-ALERTA CONS u OCR")

mir = {}
for a in alertas:
    if a["volcano"] not in VOLS or a["sensor_bucket"] not in BUCKETS:
        continue
    dt = a["fecha_utc"]; ll = coords.get(a["volcano"])
    try: dto = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
    except ValueError: dto = None
    if ll and dto and es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], dto):
        continue
    k = (a["volcano"], a["sensor_bucket"], dt[:10])
    mir[k] = max(mir.get(k, 0.0), a["vrp_mw"] or 0.0)

# records por (vol, fecha) y por (vol, bucket, fecha)
vis_vol_fecha = collections.defaultdict(lambda: collections.defaultdict(int))  # (vol,f) -> bucket -> n visibles
pc0_vb = collections.defaultdict(int)
vis_vb = collections.defaultdict(int)
rec_vb = collections.defaultdict(int)
for vol in VOLS:
    d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        b = bucket(r.get("sensor"))
        f = (r.get("datetime_utc") or "")[:10]
        if not b or not (GT_INI <= f <= GT_FIN):
            continue
        rec_vb[(vol, b, f)] += 1
        if visible_dashboard(r, vol):
            vis_vb[(vol, b, f)] += 1
            vis_vol_fecha[(vol, f)][b] += 1
        pc = r.get("primary_cluster") or {}
        if pc.get("n_pixels", 0) > 0 and (pc.get("vrp_mw") or 0) == 0:
            pc0_vb[(vol, b, f)] += 1

for SENS in ("VIIRS750", "VIIRS375", "MODIS"):
    perdidas_pc0 = [(v, f) for (v, b, f) in mir
                    if b == SENS and vis_vb[(v, b, f)] == 0 and pc0_vb[(v, b, f)] > 0]
    n_alertas = sum(1 for (v, b, f) in mir if b == SENS)
    cub_otro = [(v, f) for (v, f) in perdidas_pc0 if sum(vis_vol_fecha[(v, f)].values()) > 0]
    sin_dato = [(v, f) for (v, f) in perdidas_pc0
                if sum(rec_vb[(v, bb, f)] for bb in BUCKETS if bb != SENS) == 0]
    print(f"\n== {SENS}: {n_alertas} noches-sensor con ALERTA; {len(perdidas_pc0)} perdidas con pc0 ==")
    print(f"   de esas {len(perdidas_pc0)}: CUBIERTAS por otro sensor del mismo volcan esa noche = "
          f"{len(cub_otro)}; NO cubiertas = {len(perdidas_pc0)-len(cub_otro)} "
          f"(de las no cubiertas, sin ningun record de otro sensor esa noche = {len(sin_dato)}: SIN DATO, no falla)")
    por_vol = collections.Counter(v for v, f in perdidas_pc0)
    por_vol_cub = collections.Counter(v for v, f in cub_otro)
    for v in sorted(por_vol):
        print(f"     {v:22s} perdidas {por_vol[v]:3d}  cubiertas por otro sensor {por_vol_cub[v]:3d}  "
              f"= perdidas de NOCHE {por_vol[v]-por_vol_cub[v]:3d}")
    if SENS == "VIIRS750" and cub_otro:
        v, f = sorted(cub_otro)[0]
        print(f"   CONTROL POSITIVO (una noche cubierta): {v} {f} -> visibles por sensor "
              f"{dict(vis_vol_fecha[(v,f)])}; MIROVA V750 {mir[(v,'VIIRS750',f)]} MW")
    if SENS == "VIIRS750":
        nc = sorted(set(perdidas_pc0) - set(cub_otro))
        print(f"   NOCHES REALMENTE PERDIDAS PARA EL OPERADOR ({len(nc)}): {nc}")
