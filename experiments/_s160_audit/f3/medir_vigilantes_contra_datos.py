"""F3 (S160): los umbrales de los vigilantes, medidos contra los datos de la instantánea de main.

Vigilantes y umbrales (leídos en el árbol de d516b9d8c):
  - nrt-healthcheck.yml:38  THRESHOLD_H = 48  (edad del ÚLTIMO record del volcán, cualquier sensor; issue)
  - nrt.yml:302             72 h             (mismo dato, sólo aviso en el run)
  - vigilancia_sombra.py:61 MAX_DIAS_SOMBRA_SIN_DATOS = 3 (por volcán y bucket MODIS/VIIRS375/VIIRS750)
  - auto_audit_weekly.py:109 MAX_GT_STALE_DAYS = 7 (días sin fila nueva en la referencia; sombra la aplica a
    TODAS las filas, RUTINA incluidas: vigilancia_sombra.avisos_referencia)
  - rama s159-cese-snpp: vigilar_plataformas.VENTANA_H = 72 por plataforma (medida por su autor, no se repite acá)

Qué mide:
  A) para cada Tier A, el hueco más largo entre records consecutivos (cualquier sensor) desde 2026-01-29
     (fin del hueco del backfill, dato de medicion.txt de la rama) y cuántos días a las 12:00 UTC el
     healthcheck habría alarmado con 48 h (falsas alarmas del umbral contra la historia real);
  B) lo mismo por bucket (MODIS, VIIRS375, VIIRS750) con el umbral de 3 días de la sombra;
  C) en la referencia (tabla sola y combinado), el hueco más largo entre filas consecutivas y entre
     ALERTAS consecutivas de cualquier volcán, contra los 7 días;
  D) edad de los datos al cierre de la instantánea (hora del servidor 2026-10-22 03:11:55 UTC).

Pregunta 1: si un umbral fuera demasiado corto, aquí saldrían días con alarma sobre la historia sana;
si fuera demasiado largo, el hueco máximo real quedaría muy por debajo del umbral y la latencia de
aviso sería el umbral entero. Pregunta 2: un archivo ilegible sale como SIN DATO, no como 0 huecos.
Control positivo: el hueco del backfill (2025-11-16 a 2026-01-28, AUDIT_S146 V-15) debe aparecer
como el máximo si se mide desde 2025-02, y no aparece al medir desde 2026-01-29.

Uso: python -I medir_vigilantes_contra_datos.py <instantanea_main> > salida.txt
"""
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1]).resolve()
DATOS = RAIZ / "data" / "mirova_equivalent"
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
          "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
AHORA = datetime(2026, 10, 22, 3, 11, 55, tzinfo=timezone.utc)
DESDE = datetime(2026, 1, 29, tzinfo=timezone.utc)
DESDE_TODO = datetime(2025, 2, 1, tzinfo=timezone.utc)


def parse(s):
    s = s.replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


def huecos(ts, desde):
    ts = sorted(t for t in ts if t >= desde)
    if len(ts) < 2:
        return None, None
    g = max((b - a) for a, b in zip(ts, ts[1:]))
    return g.total_seconds() / 3600, ts[-1]


def dias_alarma(ts, desde, hasta, umbral_h):
    """Regla repetida a las 12:00 UTC: alarma si el último record antes de esa hora es más viejo que umbral_h."""
    ts = sorted(t for t in ts if t >= desde)
    n = alarma = 0
    i = 0
    d = desde.replace(hour=12)
    while d <= hasta:
        while i + 1 < len(ts) and ts[i + 1] <= d:
            i += 1
        if ts and ts[i] <= d:
            n += 1
            if (d - ts[i]).total_seconds() / 3600 > umbral_h:
                alarma += 1
        d += timedelta(days=1)
    return n, alarma


print("A) records por volcán (cualquier sensor), healthcheck 48 h y nrt.yml 72 h")
print("volcán | n records | último record | edad al 2026-10-22 03:11 UTC (h) | hueco máx desde 2026-01-29 (h) | hueco máx desde 2025-02 (h) | días 12:00 UTC | alarmas 48 h | alarmas 72 h")
por_vol = {}
for v in TIER_A:
    p = DATOS / f"{v}.json"
    try:
        recs = json.loads(p.read_text(encoding="utf-8")).get("records", [])
    except Exception as e:
        print(f"{v} | SIN DATO: {e}")
        continue
    ts = []
    por_b = defaultdict(list)
    for r in recs:
        s = r.get("datetime_utc") or r.get("acq_datetime_utc")
        if not s:
            continue
        t = parse(s)
        ts.append(t)
        por_b[bucket(r.get("sensor", "?"))].append(t)
    por_vol[v] = por_b
    ultimo_lista = parse(recs[-1].get("datetime_utc") or recs[-1].get("acq_datetime_utc"))
    ultimo_max = max(ts)
    nota = "" if ultimo_lista == ultimo_max else f" (records[-1]={ultimo_lista.isoformat()} != max)"
    g, _ = huecos(ts, DESDE)
    g2, _ = huecos(ts, DESDE_TODO)
    n, a48 = dias_alarma(ts, DESDE, AHORA, 48)
    _, a72 = dias_alarma(ts, DESDE, AHORA, 72)
    edad = (AHORA - ultimo_max).total_seconds() / 3600
    print(f"{v} | {len(recs)} | {ultimo_max.isoformat()}{nota} | {edad:.1f} | {g:.1f} | {g2:.1f} | {n} | {a48} | {a72}")

print("\nB) por volcán y bucket, sombra MAX_DIAS_SOMBRA_SIN_DATOS = 3 (72 h)")
print("volcán | bucket | hueco máx desde 2026-01-29 (h) | alarmas 72 h sobre días 12:00 UTC")
for v, por_b in por_vol.items():
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        g, _ = huecos(por_b[b], DESDE)
        n, a = dias_alarma(por_b[b], DESDE, AHORA, 72)
        print(f"{v} | {b} | {g if g is None else round(g, 1)} | {a} de {n}")

print("\nC) referencia de MIROVA: hueco máx entre filas y entre alertas, contra MAX_GT_STALE_DAYS = 7")


def leer_csv(p):
    with open(p, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


tabla = RAIZ / "latest_consolidado.csv"
ocr = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_ocr.csv"
for nombre, p in (("tabla sola", tabla), ("OCR", ocr)):
    filas = leer_csv(p)
    print(f"{nombre}: {p.name} sha256={sha(p)} filas={len(filas)} columnas={list(filas[0].keys())[:8]}")
    col_f = next((c for c in filas[0] if "Fecha" in c and "UTC" in c), None)
    col_t = next((c for c in filas[0] if c.lower().startswith("tipo")), None)
    ts = []
    ts_alerta = []
    for f in filas:
        s = (f.get(col_f) or "")[:16]
        try:
            t = datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        ts.append(t)
        if "ALERTA" in (f.get(col_t) or "").upper():
            ts_alerta.append(t)
    for et, lst in (("todas las filas", ts), ("solo ALERTA*", ts_alerta)):
        g, ult = huecos(lst, DESDE)
        print(f"  {et}: n={len(lst)} última={ult.isoformat() if ult else None} "
              f"edad={(AHORA - ult).total_seconds()/3600:.1f} h hueco máx desde 2026-01-29={g:.1f} h "
              f"(= {g/24:.1f} d; umbral 7 d = 168 h)")
    print(f"  (columnas usadas: fecha={col_f}, tipo={col_t})")

print("\nD) control positivo del instrumento")
print("D1) el hueco del backfill de AUDIT_S146 V-15 (2025-11-16 a 2026-01-28) NO aparece en la columna 'desde 2025-02':")
print("    medido aparte, Lascar tiene 277/285/291 records en nov/dic-2025/ene-2026 en d516b9d8c: el hueco ya no existe")
print("    en estos datos (S158 reemplazo el historico con K, #883/#884). La afirmacion de S146 envejecio; no sirve de control.")
print("D2) control sintetico: a los records de Lascar se les quita todo lo del 2026-05-01 al 2026-05-06 y la regla de")
print("    48 h a las 12:00 UTC tiene que alarmar los dias 2 a 6 de mayo (5 dias: el ultimo record previo es del 30-abr ~08:00,")
print("    a las 12:00 del 2-may ya pasaron ~52 h) y la de 72 h los dias 3 a 6 (4 dias). (Primera version de este control")
print("    esperaba 4 y 3 por contar mal la ventana; el instrumento no cambio.)")
ts_l = sorted(t for b in por_vol["Lascar"].values() for t in b)
ini, fin = datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 7, tzinfo=timezone.utc)
ts_sint = [t for t in ts_l if not (ini <= t < fin)]
n, a48 = dias_alarma(ts_sint, DESDE, AHORA, 48)
_, a72 = dias_alarma(ts_sint, DESDE, AHORA, 72)
print(f"    quitados {len(ts_l) - len(ts_sint)} records; alarmas 48 h = {a48} (esperado 5), alarmas 72 h = {a72} (esperado 4)"
      f" -> {'INSTRUMENTO OK' if (a48, a72) == (5, 4) else 'INSTRUMENTO FALLA'}")
