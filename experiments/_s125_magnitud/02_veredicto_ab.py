# -*- coding: utf-8 -*-
"""S125 — veredicto del A/B de magnitud contra los criterios PRE-REGISTRADOS.

Criterio fijado ANTES de mirar resultados: docs/S125_AB_MAGNITUD_PREREGISTRO.md

Que hace este script, y por que cada cosa:

  · Ground truth CONS union OCR (A11), con el diccionario de alias COMPLETO —
    "Puyehue-Cordon Caulle" con guion, "PlanchonPeteroa" sin guion. Un alias
    faltante escondio PCC entero de la tabla del veredicto en S124 y era el
    unico volcan con dano real.
  · Compara sobre la INTERSECCION de pasadas (datetime_utc + sensor), nunca
    sobre conteos de series completas.
  · Usa `primary_cluster.vrp_mw` (A10), NUNCA `record.vrp_mw`: el segundo es la
    suma scene-wide y no es lo que MIROVA reporta ni lo que ve el dashboard.
  · Reporta DISTRIBUCION, no mediana sola (T3): una mediana de 1,00 puede ser
    "sin efecto" o "efectos opuestos que se cancelan".
  · IC bootstrap 5000 (T8): una mediana sin intervalo no decide nada.

Persiste todo en 02_veredicto.json (regla S91: ningun numero se transcribe).
"""
import csv, json, math, os, random, statistics as st
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
BRAZOS = {"control": "_s125_mag_control", "A": "_s125_mag_a",
          "B": "_s125_mag_b", "C": "_s125_mag_c"}
VOLS = ["Villarrica", "PlanchonPeteroa", "Lascar", "PuyehueCordonCaulle"]
BANDA = (0.7, 1.4)          # banda de paridad para la MEDIANA (no la de una deteccion suelta)

# Alias: nuestro nombre de archivo -> como aparece en el CSV del scraper.
# TODAS las variantes, incluidas las que mordieron en S124.
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}
SENSOR_MAP = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}


def bucket(sensor):
    """Convencion del proyecto (A48): VIIRS_SNPP/NOAA20/NOAA21 SIN sufijo = I-band 375m."""
    s = (sensor or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


def cargar_mirova():
    """CSV consolidado + OCR (A11: el universo MIROVA es CONS union OCR)."""
    out = defaultdict(dict)      # vol -> (fecha, bucket) -> vrp
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                nom = (r.get("Volcan") or "").strip()
                vol = next((v for v, al in ALIAS.items() if nom in al), None)
                if vol is None:
                    continue
                if "ALERTA" not in (r.get("Tipo_Registro") or ""):
                    continue
                try:
                    v = float(r.get("VRP_MW") or 0)
                except ValueError:
                    continue
                if v <= 0:
                    continue
                b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
                if b is None:
                    continue
                f = (r.get("Fecha_Satelite_UTC") or "")[:10]
                k = (f, b)
                out[vol][k] = max(out[vol].get(k, 0), v)
    return out


def cargar_brazo(subdir, vol):
    p = os.path.join(ROOT, "data", subdir, vol + ".json")
    recs = json.load(open(p, encoding="utf-8"))["records"]
    por_noche = {}
    pasadas = set()
    for r in recs:
        b = bucket(r.get("sensor"))
        if b is None:
            continue
        pasadas.add((r["datetime_utc"], r.get("sensor")))
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0            # A10: pc.vrp_mw, NUNCA record.vrp_mw
        if v <= 0:
            continue
        k = (r["datetime_utc"][:10], b)
        por_noche[k] = max(por_noche.get(k, 0), v)
    return por_noche, pasadas


def ic_mediana(xs, n=5000, seed=20260828):
    """IC 95% de la mediana por bootstrap. Semilla fija: Math.random no es reproducible."""
    if len(xs) < 3:
        return (None, None)
    rnd = random.Random(seed)
    meds = []
    for _ in range(n):
        meds.append(st.median([xs[rnd.randrange(len(xs))] for _ in range(len(xs))]))
    meds.sort()
    return (round(meds[int(0.025 * n)], 3), round(meds[int(0.975 * n)], 3))


def dist(xs):
    if not xs:
        return None
    xs = sorted(xs)
    n = len(xs)
    lo, hi = ic_mediana(xs)
    return {"n": n, "min": round(xs[0], 3), "p25": round(xs[n // 4], 3),
            "mediana": round(st.median(xs), 3), "p75": round(xs[3 * n // 4], 3),
            "max": round(xs[-1], 3), "ic95": [lo, hi],
            "suben": sum(1 for x in xs if x > 1.0), "bajan": sum(1 for x in xs if x < 1.0)}


mir = cargar_mirova()
res = {"banda": list(BANDA), "por_volcan": {}, "global": {}}

for vol in VOLS:
    datos = {}
    pasadas = {}
    for nombre, sub in BRAZOS.items():
        datos[nombre], pasadas[nombre] = cargar_brazo(sub, vol)
    comunes = pasadas["control"] & pasadas["C"]
    noches_com = {(dt[:10], bucket(s)) for dt, s in comunes}

    fila = {"alertas_mirova": len(mir.get(vol, {})), "pasadas_comunes": len(comunes)}
    ratios_por_brazo = {}
    for nombre in BRAZOS:
        ratios = []
        emparejadas = []
        for k, vm in mir.get(vol, {}).items():
            if k not in noches_com:
                continue                      # solo pasadas que AMBOS brazos procesaron
            vn = datos[nombre].get(k)
            if not vn:
                continue
            ratios.append(vn / vm)
            emparejadas.append(k)
        ratios_por_brazo[nombre] = ratios
        fila[nombre] = dist(ratios)
        fila[nombre + "_reproducidas"] = len(emparejadas)
    # FN: noches que el control reproduce y el brazo pierde
    rep_ctrl = {k for k in mir.get(vol, {}) if k in noches_com and datos["control"].get(k)}
    rep_c = {k for k in mir.get(vol, {}) if k in noches_com and datos["C"].get(k)}
    fila["fn_nuevos_en_C"] = sorted(rep_ctrl - rep_c)
    fila["ganadas_en_C"] = sorted(rep_c - rep_ctrl)
    res["por_volcan"][vol] = fila

# global
for nombre in BRAZOS:
    todos = []
    for vol in VOLS:
        d = res["por_volcan"][vol].get(nombre)
        if d:
            todos.append(d["mediana"])
    res["global"][nombre] = {"medianas_por_volcan": todos,
                             "en_banda": sum(1 for m in todos if BANDA[0] <= m <= BANDA[1]),
                             "de": len(todos)}

dest = os.path.join(os.path.dirname(__file__), "02_veredicto.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# ── salida legible ─────────────────────────────────────────────────────────
print(f"BANDA DE PARIDAD PARA LA MEDIANA: {BANDA[0]}–{BANDA[1]}\n")
hdr = f"{'volcan':<22}{'n':>5}{'control':>10}{'IC95 ctrl':>16}{'brazo C':>10}{'IC95 C':>16}  veredicto"
print(hdr); print("-" * len(hdr))
for vol in VOLS:
    f = res["por_volcan"][vol]
    c, b = f.get("control"), f.get("C")
    if not c or not b:
        print(f"{vol:<22}  sin datos suficientes"); continue
    def marca(d): return "OK " if BANDA[0] <= d["mediana"] <= BANDA[1] else "FUERA"
    solapan = not (c["ic95"][1] < b["ic95"][0] or b["ic95"][1] < c["ic95"][0])
    print(f"{vol:<22}{c['n']:>5}{c['mediana']:>10.3f}{str(c['ic95']):>16}"
          f"{b['mediana']:>10.3f}{str(b['ic95']):>16}  "
          f"{marca(c)}->{marca(b)}  {'IC SE SOLAPAN' if solapan else 'IC separados'}")
print()
for vol in VOLS:
    f = res["por_volcan"][vol]
    c, b = f.get("control"), f.get("C")
    if not c:
        continue
    print(f"{vol}: distribucion control  suben/bajan {c['suben']}/{c['bajan']}  "
          f"[{c['min']} .. p25 {c['p25']} .. p75 {c['p75']} .. {c['max']}]")
    print(f"{' '*len(vol)}  distribucion brazoC   suben/bajan {b['suben']}/{b['bajan']}  "
          f"[{b['min']} .. p25 {b['p25']} .. p75 {b['p75']} .. {b['max']}]")
    if f["fn_nuevos_en_C"]:
        print(f"{' '*len(vol)}  !! FN NUEVOS en C: {f['fn_nuevos_en_C']}")
    if f["ganadas_en_C"]:
        print(f"{' '*len(vol)}  ++ ganadas en C: {f['ganadas_en_C']}")
print("\nglobal:", json.dumps(res["global"], ensure_ascii=False))
print("persistido en", dest)
