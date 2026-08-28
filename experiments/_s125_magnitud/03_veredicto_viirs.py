# -*- coding: utf-8 -*-
"""S125 — veredicto del A/B de VIIRS375, ESTRATIFICADO POR SENSOR.

Por que estratificado: mezclar MODIS con VIIRS en una mediana unica fabrico la
falsa "bimodalidad" de Lascar (48 noches sub-reportando y outliers de 19x que
resultaron ser todos MODIS). El ratio agregado por volcan esconde el fenomeno.

Las dos piezas que se prueban existen SOLO en VIIRS375, asi que MODIS y VIIRS750
funcionan como CONTROL INTERNO: no deben cambiar. Si cambian, el A/B esta mal
montado y el resultado no vale.

Reglas aplicadas (todas verificables en el codigo de abajo):
  · pc.vrp_mw, NUNCA record.vrp_mw (A10).
  · interseccion de pasadas (datetime_utc + sensor), no conteos de series.
  · ground truth CONS union OCR (A11) con el diccionario de alias COMPLETO.
  · SOLO pasadas nocturnas: las alertas diurnas de MIROVA son artefacto de
    reflexion solar (A76) y nuestro pipeline es night-only — compararlas seria
    contar como fallo algo que hacemos bien.
  · distribucion, no mediana sola (T3), e IC bootstrap (T8).

Persiste en 03_veredicto_viirs.json (regla S91).
"""
import csv, json, os, random, statistics as st
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
BRAZOS = {
    # OJO (S125): el control NO puede ser `mirova_equivalent` a secas. Esa data es
    # el acumulado operacional, reprocesado en momentos distintos y con versiones
    # de codigo distintas, asi que introduce diferencias ESPURIAS ajenas al A/B —
    # se vio en el primer intento: MODIS se movia +4.03 con piezas que ni lo tocan.
    # El control valido es el clon REPROCESADO en la misma ventana y con los flags
    # operacionales (ctx_filter=True, intermediate_bg=True, igual que produccion).
    "control": "_s125_mag_control",
    "E": "_s125_viirs_e",       # sin filtro contextual
    "F": "_s125_viirs_f",       # sin anillo intermedio (vuelve al global 5-25 km)
    "G": "_s125_viirs_g",       # sin ambas
}
VOLS = ["Villarrica", "PlanchonPeteroa", "Lascar", "PuyehueCordonCaulle"]
VENTANA = ("2026-06-25", "2026-08-24")
BANDA = (0.7, 1.4)

ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}
SENSOR_MAP = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}


def bucket(sensor):
    s = (sensor or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


def cargar_mirova():
    out = defaultdict(dict)
    diurnas = 0
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            if not b or v <= 0:
                continue
            fecha = (r.get("Fecha_Satelite_UTC") or "")
            f = fecha[:10]
            if not (VENTANA[0] <= f <= VENTANA[1]):
                continue
            h = int(fecha[11:13] or 12)
            if not (3 <= h <= 9):        # A76: diurna = artefacto solar
                diurnas += 1
                continue
            out[vol][(f, b)] = max(out[vol].get((f, b), 0), v)
    return out, diurnas


def cargar(subdir, vol):
    p = os.path.join(ROOT, "data", subdir, vol + ".json")
    if not os.path.exists(p):
        return None, None
    recs = json.load(open(p, encoding="utf-8"))["records"]
    por, pasadas = {}, set()
    for r in recs:
        b = bucket(r.get("sensor"))
        f = r["datetime_utc"][:10]
        if b is None or not (VENTANA[0] <= f <= VENTANA[1]):
            continue
        pasadas.add((r["datetime_utc"], r.get("sensor")))
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if v > 0:
            por[(f, b)] = max(por.get((f, b), 0), v)
    return por, pasadas


def ic(xs, n=4000, seed=20260828):
    if len(xs) < 3:
        return [None, None]
    rnd = random.Random(seed)
    meds = sorted(st.median([xs[rnd.randrange(len(xs))] for _ in range(len(xs))])
                  for _ in range(n))
    return [round(meds[int(0.025 * n)], 3), round(meds[int(0.975 * n)], 3)]


mir, diurnas = cargar_mirova()
disponibles = {k: v for k, v in BRAZOS.items()
               if os.path.exists(os.path.join(ROOT, "data", v))}

datos, pasadas = {}, {}
for nom, sub in disponibles.items():
    datos[nom], pasadas[nom] = {}, {}
    for vol in VOLS:
        d, p = cargar(sub, vol)
        if d is not None:
            datos[nom][vol], pasadas[nom][vol] = d, p

# interseccion de pasadas entre TODOS los brazos disponibles
comunes = {}
for vol in VOLS:
    sets = [pasadas[n][vol] for n in disponibles if vol in pasadas[n]]
    comunes[vol] = set.intersection(*sets) if sets else set()

res = {"ventana": list(VENTANA), "brazos": list(disponibles),
       "diurnas_descartadas": diurnas, "por_sensor": {}}

print(f"A/B VIIRS375 — ventana {VENTANA[0]} a {VENTANA[1]}")
print(f"brazos con datos: {', '.join(disponibles)}")
print(f"alertas diurnas de MIROVA descartadas (artefacto solar A76): {diurnas}\n")

for b in ["v375", "v750", "modis"]:
    fila = {}
    print(f"{'='*74}\n{b.upper()}" + ("   <- lo que el A/B modifica"
          if b == "v375" else "   <- CONTROL INTERNO: no debe cambiar"))
    print(f"{'brazo':<10}{'n':>5}{'mediana':>10}{'IC95':>18}{'p25':>8}{'p75':>8}")
    for nom in disponibles:
        ratios = []
        for vol in VOLS:
            if vol not in datos[nom]:
                continue
            noches = {(dt[:10], bucket(s)) for dt, s in comunes[vol]}
            for k, vm in mir.get(vol, {}).items():
                if k[1] != b or k not in noches:
                    continue
                vn = datos[nom][vol].get(k)
                if vn:
                    ratios.append(vn / vm)
        if len(ratios) < 3:
            print(f"{nom:<10}{len(ratios):>5}   (muestra insuficiente)")
            continue
        rs = sorted(ratios)
        d = {"n": len(rs), "mediana": round(st.median(rs), 3), "ic95": ic(rs),
             "p25": round(rs[len(rs) // 4], 3), "p75": round(rs[3 * len(rs) // 4], 3),
             "min": round(rs[0], 3), "max": round(rs[-1], 3)}
        fila[nom] = d
        print(f"{nom:<10}{d['n']:>5}{d['mediana']:>10.3f}{str(d['ic95']):>18}"
              f"{d['p25']:>8.3f}{d['p75']:>8.3f}")
    res["por_sensor"][b] = fila
    # control interno
    if b != "v375" and "control" in fila:
        for nom in fila:
            if nom == "control":
                continue
            delta = abs(fila[nom]["mediana"] - fila["control"]["mediana"])
            if delta > 0.001:
                print(f"   !! {nom} movio {b} en {delta:+.3f} — NO deberia. "
                      "Revisar el montaje del A/B.")
    print()

dest = os.path.join(os.path.dirname(__file__), "03_veredicto_viirs.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("persistido en", dest)
