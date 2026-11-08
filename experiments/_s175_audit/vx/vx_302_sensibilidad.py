# -*- coding: utf-8 -*-
"""VX S175, verificación del hallazgo 302 (F5) por otro camino.

Qué mide: la prueba de «extensión» del auditor (i2_extension.py) dice que un acierto por misma pasada es «mismo cúmulo»
cuando la distancia de MIROVA (Distancia_km de la tabla, medida desde mirova_center) cae dentro del rango radial
[min - tol, max + tol] de NUESTROS píxeles anómalos. Es una prueba escalar (un radio, no una posición; regla A107), así que
acá se mide (1) su sensibilidad al origen (mirova_center contra vent/cumbre de volcanoes.yaml, 0,385 km aparte en
Chillán) y a la tolerancia; (2) su nulo por permutación (regla A110): se barajan las distancias de MIROVA entre pares del
mismo volcán y sensor y se cuenta cuántos pares «ajenos» igual salen «mismo cúmulo». Si el nulo da casi lo mismo que lo
observado, la prueba no distingue y «son el mismo foco» no está medido; (3) una cota 2-D para el caso Chillán
2026-10-18 06:48: el alcance máximo de nuestro cúmulo (píxel más lejano más una diagonal de píxel) contra 1,88 km.

Las dos preguntas: (1) si los aciertos fueran de focos distintos (p. ej. a 5 km), la prueba lo vería: el control positivo
son los pares OCR de Tupungatito y Cordón Caulle que el auditor ya clasificó «fuera»; acá tienen que salir incompatibles.
(2) si el instrumento estuviera muerto, el nulo por permutación daría 100 % o 0 %, no un valor intermedio; y el conteo de
pares leídos tiene que ser 881 (el del auditor).
Denominador: los pares de i2_pares.csv del auditor (881; lab pos y pub=1, ventana 2026-06-11 a 2026-11-07), estrato
CONS (distancia de la tabla) 715, de los cuales clase iii 54. Records: base 752d348bc (copia en vx/base_data, sha256
igual a git show). volcanoes.yaml: git show 752d348bc:volcanoes.yaml.
Salida: vx_302_sensibilidad_salida.txt y vx_302_sensibilidad_out.json al lado.
"""
import csv
import io
import json
import math
import os
import random
import subprocess
import sys
from collections import Counter, defaultdict

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
F5 = os.path.join(os.path.dirname(AQUI), "f5")
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
DATOS = r"C:\Users\nmend\vrp-temporales\s175_audit\vx\base_data"
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}          # la del auditor (tarea, A91)
DIAG_PIX_KM = {"VIIRS375": 0.375 * math.sqrt(2), "VIIRS750": 0.75 * math.sqrt(2), "MODIS": 1.0 * math.sqrt(2)}


def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


y = subprocess.run(["git", "-C", REPO, "show", f"{BASE}:volcanoes.yaml"], capture_output=True).stdout.decode("utf-8")
V = {v["name"]: v for v in yaml.safe_load(y)["volcanoes"]}
pares = list(csv.DictReader(open(os.path.join(F5, "i2_pares.csv"), encoding="utf-8")))
assert len(pares) == 881, len(pares)
recs = {}
for vol in {p["vol"] for p in pares}:
    for x in json.load(open(os.path.join(DATOS, vol + ".json"), encoding="utf-8"))["records"]:
        recs[(vol, x["sensor"], x["datetime_utc"])] = x


def rangos(p, origen):
    """(d_min, d_max, n) de los píxeles anómalos del record desde el origen (lat, lon)."""
    x = recs[(p["vol"], p["sensor"], p["dt"])]
    ds = [hav(q["lat"], q["lon"], *origen) for q in (x.get("anomaly_pixels") or []) if q.get("lat") is not None]
    return (min(ds), max(ds), len(ds)) if ds else (None, None, 0)


def compatible(rng, dm, tol):
    if rng[2] == 0 or dm is None:
        return None
    return (rng[0] - tol) <= dm <= (rng[1] + tol)


out = {"n_pares": len(pares)}
cons = [p for p in pares if p["fuente_dist"] == "CONS" and p["dist_mirova"]]
ocr = [p for p in pares if p["fuente_dist"] == "OCR" and p["dist_mirova"]]
out["n_cons"] = len(cons)
out["n_cons_iii"] = sum(p["clase"] == "iii" for p in cons)
orig = {"mirova_center": lambda v: (V[v]["mirova_center_lat"], V[v]["mirova_center_lon"]),
        "vent": lambda v: (V[v].get("vent_lat") or V[v]["lat"], V[v].get("vent_lon") or V[v]["lon"])}

# (1) sensibilidad: origen x factor de tolerancia, sobre los 54 iii y sobre los 715 CONS
tabla = {}
for on, of in orig.items():
    for fac in (0.0, 0.5, 1.0, 2.0):
        for sub, lst in (("iii", [p for p in cons if p["clase"] == "iii"]), ("todos_CONS", cons)):
            c = Counter()
            fuera = []
            for p in lst:
                r = compatible(rangos(p, of(p["vol"])), float(p["dist_mirova"]), TOL[p["b"]] * fac)
                c["sin_pixeles" if r is None else ("mismo_cumulo" if r else "fuera")] += 1
                if r is False:
                    fuera.append(f'{p["vol"]} {p["sensor"]} {p["dt"]} dm={p["dist_mirova"]} prot={p["protegida"]}')
            tabla[f"{on}|tol_x{fac}|{sub}"] = {"conteo": dict(c), "fuera": fuera}
out["sensibilidad"] = tabla

# control positivo: los pares OCR que el auditor dio «fuera» (Tupungatito, Cordón Caulle, 5 a 8 km) salen incompatibles
ctrl = Counter()
for p in ocr:
    if p["clase"] != "iii":
        continue
    r = compatible(rangos(p, orig["mirova_center"](p["vol"])), float(p["dist_mirova"]), TOL[p["b"]])
    ctrl["sin_pixeles" if r is None else ("mismo_cumulo" if r else "fuera")] += 1
out["control_positivo_ocr_iii_mc_tol1"] = dict(ctrl)

# (2) nulo por permutación (A110): barajar dm dentro de (vol, b) entre pares CONS; 300 barajados
random.seed(175)
grupos = defaultdict(list)
for p in cons:
    grupos[(p["vol"], p["b"])].append(p)
rng_mc = {id(p): rangos(p, orig["mirova_center"](p["vol"])) for p in cons}
obs = Counter()
for p in cons:
    r = compatible(rng_mc[id(p)], float(p["dist_mirova"]), TOL[p["b"]])
    obs["mismo_cumulo" if r else "fuera"] += (r is not None)
nulos = []
nulos_por_b = defaultdict(list)
for _ in range(300):
    c = Counter()
    cb = defaultdict(Counter)
    for (vol, b), lst in grupos.items():
        dms = [float(p["dist_mirova"]) for p in lst]
        random.shuffle(dms)
        for p, dm in zip(lst, dms):
            r = compatible(rng_mc[id(p)], dm, TOL[b])
            if r is not None:
                c["mismo_cumulo" if r else "fuera"] += 1
                cb[b]["mismo_cumulo" if r else "fuera"] += 1
    tot = c["mismo_cumulo"] + c["fuera"]
    nulos.append(c["mismo_cumulo"] / tot if tot else None)
    for b, cc in cb.items():
        t = cc["mismo_cumulo"] + cc["fuera"]
        nulos_por_b[b].append(cc["mismo_cumulo"] / t if t else None)
tot_obs = obs["mismo_cumulo"] + obs["fuera"]
out["nulo_permutacion"] = {"observado_mismo_cumulo": obs["mismo_cumulo"], "observado_total": tot_obs,
                           "observado_frac": round(obs["mismo_cumulo"] / tot_obs, 4),
                           "nulo_frac_mediana": round(sorted(nulos)[len(nulos) // 2], 4),
                           "nulo_frac_min": round(min(nulos), 4), "nulo_frac_max": round(max(nulos), 4),
                           "por_sensor": {b: {"nulo_mediana": round(sorted(l)[len(l) // 2], 4)} for b, l in nulos_por_b.items()}}
obs_b = defaultdict(Counter)
for p in cons:
    r = compatible(rng_mc[id(p)], float(p["dist_mirova"]), TOL[p["b"]])
    if r is not None:
        obs_b[p["b"]]["mismo_cumulo" if r else "fuera"] += 1
for b, cc in obs_b.items():
    t = cc["mismo_cumulo"] + cc["fuera"]
    out["nulo_permutacion"]["por_sensor"][b]["observado"] = round(cc["mismo_cumulo"] / t, 4)
    out["nulo_permutacion"]["por_sensor"][b]["n"] = t

# (3) Chillán 2026-10-18 06:48: cota 2-D y la fila V750 de la misma pasada
ch = [p for p in cons if p["vol"] == "NevadosDeChillan" and p["dt"] == "2026-10-18 06:48"]
det = []
for p in ch:
    for on, of in orig.items():
        r = rangos(p, of(p["vol"]))
        dm = float(p["dist_mirova"])
        det.append({"sensor": p["sensor"], "origen": on, "d_min": round(r[0], 3), "d_max": round(r[1], 3), "n_pix": r[2],
                    "dist_mirova": dm, "margen_km_(dm - (d_max + tol))": round(dm - (r[1] + TOL[p["b"]]), 3),
                    "alcance_2d_max_(d_max + diagonal_pixel)": round(r[1] + DIAG_PIX_KM[p["b"]], 3),
                    "compatible_tol_auditor": compatible(r, dm, TOL[p["b"]])})
out["chillan_20261018_0648"] = det

print(f"pares leídos {out['n_pares']}; CONS {out['n_cons']} (iii {out['n_cons_iii']})")
print("\n(1) sensibilidad origen x tolerancia (conteo; lista de «fuera»):")
for k, v in tabla.items():
    print(f"  {k}: {v['conteo']}")
    for f in v["fuera"][:6]:
        print(f"      fuera: {f}")
print("\ncontrol positivo (pares OCR clase iii, origen mirova_center, tol x1):", out["control_positivo_ocr_iii_mc_tol1"])
print("\n(2) nulo por permutación:", json.dumps(out["nulo_permutacion"], ensure_ascii=False))
print("\n(3) Chillán 2026-10-18 06:48:")
for d in det:
    print("  ", d)
json.dump(out, open(os.path.join(AQUI, "vx_302_sensibilidad_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
