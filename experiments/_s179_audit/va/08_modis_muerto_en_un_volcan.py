# -*- coding: utf-8 -*-
"""VA-08 (afirmación 410): si MODIS deja de escribir en UN volcán (los demás sensores y volcanes siguen), ¿qué control
lo ve? Simulación en memoria sobre los records reales de 438a60a1e: se borran los records MODIS de Lascar desde el
2026-11-05 (5 días antes del HOY fijo 2026-11-10 23:00 UTC) y se pasa lo mismo a cada control.

Controles probados, con su código real:
- nrt-healthcheck.yml paso «Detect stale Tier A» (438a60a1e, l. 40-90): edad del último record del volcán, cualquier
  sensor, umbral 48 h. Se replica su lógica (está embebida en el YAML): records[-1] del JSON.
- scripts/vigilar_plataformas.py::evaluar (conteo por plataforma sumando los 11 Tier A, 72 h).
- scripts/auto_audit_weekly.py::cobertura_de_ventana (días con cualquier record de cualquier volcán y sensor).
- scripts/vigilancia_guardia_modis.py::avisos_produccion (frescura por volcán y sensor, 3 días).
Preguntas del instrumento:
1. Control positivo: si borro TODO (todos los volcanes y sensores) los tres primeros controles tienen que avisar; si no,
   la réplica está mal. Y sin borrar nada, ninguno debe avisar por Lascar MODIS.
2. Instrumento muerto: imprime cuántos records se borraron (0 invalida).
"""
import io, sys, os, json, copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilar_plataformas as vp
import auto_audit_weekly as aa
import vigilancia_guardia_modis as vg
AHORA = datetime(2026, 11, 10, 23, 0, tzinfo=timezone.utc)
HOY = "2026-11-10"
CORTE = "2026-11-05"
raw = {}
for v in vp.TIER_A:
    raw[v] = json.load(open(os.path.join(BASE, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]


def borrar(raw, vol=None, sensor_pref="MODIS"):
    out, n = {}, 0
    for v, recs in raw.items():
        keep = []
        for r in recs:
            if (vol is None or v == vol) and str(r.get("sensor", "")).startswith(sensor_pref) \
                    and str(r.get("datetime_utc", ""))[:10] >= CORTE:
                n += 1; continue
            keep.append(r)
        out[v] = keep
    return out, n


def healthcheck(raw):
    stale = []
    for v, recs in raw.items():
        if not recs:
            stale.append((v, "0 records")); continue
        last = recs[-1].get("datetime_utc")
        dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if (AHORA - dt).total_seconds() / 3600 > 48:
            stale.append((v, last))
    return stale


def plataformas(raw):
    regs = []
    for v, recs in raw.items():
        for r in recs:
            s, t = r.get("sensor"), r.get("datetime_utc")
            if s and t:
                regs.append((s, vp._utc(t)))
    e = vp.evaluar(regs, AHORA, vp.cargar_ceses())
    return e["estado"], e["alarmas"]


def cobertura(raw):
    dias = {str(r.get("datetime_utc"))[:10] for recs in raw.values() for r in recs if r.get("datetime_utc")}
    win = ((AHORA - timedelta(days=59)).date().isoformat(), HOY)
    return aa.cobertura_de_ventana(dias, win, AHORA.date())["avisos"]


def guardia_prod(raw):
    prod = []
    for v, recs in raw.items():
        for r in recs:
            b = aa.our_bucket(str(r.get("sensor") or ""))
            dt = str(r.get("datetime_utc") or "")
            if b == "MODIS" and "2026-10-19" <= dt[:10] <= HOY:
                prod.append({"vol": v, "b": b, "noche": dt[:10]})
    return [a for a in vg.avisos_produccion(prod, HOY) if "Lascar" in a or "ninguno" in a]


for nombre, (r, n) in (("SIN borrar", (raw, 0)), ("borra MODIS de Lascar desde 11-05", borrar(raw, "Lascar")),
                      ("CONTROL borra TODO (todos los volcanes y sensores) desde 11-05", borrar(raw, None, ""))):
    print(f"== {nombre}: records borrados {n}")
    print("   healthcheck (48 h, por volcán, cualquier sensor):", healthcheck(r) or "sin stale")
    print("   vigilar_plataformas (72 h, por plataforma, suma 11):", plataformas(r))
    print("   audit semanal cobertura_de_ventana:", cobertura(r) or "sin aviso")
    print("   vigilancia guardia MODIS avisos_produccion (Lascar):", guardia_prod(r) or "sin aviso")
