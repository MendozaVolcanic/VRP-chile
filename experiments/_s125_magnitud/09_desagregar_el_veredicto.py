# -*- coding: utf-8 -*-
"""S126 — desagregar el veredicto de S125: ?quien produce la "mejora" a 1,043?

`03_veredicto_viirs.py` mezcla los 4 volcanes en una mediana unica de VIIRS375 y
concluye que apagar el filtro contextual lleva el ratio de 0,600 a 1,043. Pero el
script 05 mostro que el aumento del brazo E se reparte MUY desparejo:

    Villarrica  x16,3     PlanchonPeteroa x11,8     PCC x1,0     Lascar x1,0

Si la mediana agrupada mejora porque los dos volcanes cuyo pixel esta a 2,8 km
del crater se inflan hasta cruzar el 1,0, entonces la "paridad" no es calibracion:
es el ruido subiendo hasta la altura de la referencia. Es exactamente el error que
S124 documento (mezclar poblaciones fabrica un veredicto falso) y la razon por la
que el propio bloque de arranque manda estratificar.

Este script repite el calculo del veredicto pero SIN agrupar: mismo emparejamiento
(interseccion de pasadas, ground truth CONS union OCR, solo nocturnas A76, max por
noche), desagregado por volcan y por brazo.

Persiste en 09_desagregar_el_veredicto.json.
"""
import csv, io, json, os, random, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
BRAZOS = {"control": "_s125_mag_control", "E": "_s125_viirs_e",
          "F": "_s125_viirs_f", "G": "_s125_viirs_g"}
VOLS = ["Villarrica", "PlanchonPeteroa", "Lascar", "PuyehueCordonCaulle"]
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}
SENSOR_MAP = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}
BANDA = (0.7, 1.4)


def bucket(s):
    s = (s or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


def ic(xs, n=4000, seed=20260828):
    if len(xs) < 3:
        return [None, None]
    rnd = random.Random(seed)
    meds = sorted(st.median([xs[rnd.randrange(len(xs))] for _ in range(len(xs))])
                  for _ in range(n))
    return [round(meds[int(0.025 * n)], 3), round(meds[int(0.975 * n)], 3)]


def cargar_mirova():
    out = defaultdict(dict)
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, fname)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            f = (r.get("Fecha_Satelite_UTC") or "")
            if not b or v <= 0 or not (VENTANA[0] <= f[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(f[11:13] or 12) <= 9):
                continue
            out[vol][(f[:10], b)] = max(out[vol].get((f[:10], b), 0), v)
    return out


def cargar(subdir, vol):
    recs = json.load(open(os.path.join(ROOT, "data", subdir, vol + ".json"),
                          encoding="utf-8"))["records"]
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


mir = cargar_mirova()
datos, pasadas = {}, {}
for nom, sub in BRAZOS.items():
    datos[nom], pasadas[nom] = {}, {}
    for vol in VOLS:
        d, p = cargar(sub, vol)
        datos[nom][vol], pasadas[nom][vol] = d, p
comunes = {v: set.intersection(*[pasadas[n][v] for n in datos]) for v in VOLS}

res = {"ventana": list(VENTANA), "banda": list(BANDA), "v375_por_volcan": {},
       "v375_agrupado": {}, "aporte_a_la_mediana": {}}

print("VEREDICTO DESAGREGADO — VIIRS375, ratio nuestro/MIROVA")
print("%s a %s   banda de paridad [%.1f - %.1f]\n" % (VENTANA + BANDA))
print("%-22s %5s %10s %10s %10s %10s" % ("volcan", "n", "control", "E", "F", "G"))

todos = defaultdict(list)
for vol in VOLS:
    noches = {(dt[:10], bucket(s)) for dt, s in comunes[vol]}
    fila = {}
    for nom in BRAZOS:
        rs = []
        for k, vm in mir.get(vol, {}).items():
            if k[1] != "v375" or k not in noches:
                continue
            vn = datos[nom][vol].get(k)
            if vn:
                rs.append(vn / vm)
        fila[nom] = rs
        todos[nom] += rs
    n = len(fila["control"])
    if n < 3:
        print("%-22s %5d   (muestra insuficiente)" % (vol, n))
        continue
    d = {}
    for nom in BRAZOS:
        rs = fila[nom]
        d[nom] = {"n": len(rs), "mediana": round(st.median(rs), 3), "ic95": ic(rs),
                  "en_banda": bool(BANDA[0] <= st.median(rs) <= BANDA[1])}
    res["v375_por_volcan"][vol] = d
    print("%-22s %5d %10.3f %10.3f %10.3f %10.3f"
          % (vol, n, d["control"]["mediana"], d["E"]["mediana"],
             d["F"]["mediana"], d["G"]["mediana"]))

print("\n%-22s %5s %10s %10s %10s %10s" % ("AGRUPADO (S125)", len(todos["control"]),
      round(st.median(todos["control"]), 3), round(st.median(todos["E"]), 3),
      round(st.median(todos["F"]), 3), round(st.median(todos["G"]), 3)))
for nom in BRAZOS:
    res["v375_agrupado"][nom] = {"n": len(todos[nom]),
                                 "mediana": round(st.median(todos[nom]), 3),
                                 "ic95": ic(todos[nom])}

print("\n" + "=" * 74)
print("EN BANDA [%.1f - %.1f], por volcan" % BANDA)
print("%-22s %10s %10s %10s %10s" % ("volcan", "control", "E", "F", "G"))
cuenta = defaultdict(int)
for vol, d in res["v375_por_volcan"].items():
    print("%-22s %10s %10s %10s %10s"
          % (vol, *["SI" if d[n]["en_banda"] else "no" for n in BRAZOS]))
    for n in BRAZOS:
        cuenta[n] += int(d[n]["en_banda"])
print("%-22s %10s %10s %10s %10s" % ("TOTAL en banda",
      *["%d/%d" % (cuenta[n], len(res["v375_por_volcan"])) for n in BRAZOS]))
res["en_banda"] = {n: "%d/%d" % (cuenta[n], len(res["v375_por_volcan"])) for n in BRAZOS}

print("\n" + "=" * 74)
print("?DE DONDE SALE LA MEJORA AGRUPADA? — composicion de la muestra")
for vol, d in res["v375_por_volcan"].items():
    salto = d["E"]["mediana"] / d["control"]["mediana"] if d["control"]["mediana"] else None
    res["aporte_a_la_mediana"][vol] = {
        "n": d["control"]["n"],
        "pct_de_la_muestra": round(100 * d["control"]["n"] / len(todos["control"]), 1),
        "salto_E_sobre_control": round(salto, 2) if salto else None}
    a = res["aporte_a_la_mediana"][vol]
    print("  %-22s %3d pares (%4.1f%% de la muestra)   E/control = %.2fx"
          % (vol, a["n"], a["pct_de_la_muestra"], a["salto_E_sobre_control"]))

dest = os.path.join(os.path.dirname(__file__), "09_desagregar_el_veredicto.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
