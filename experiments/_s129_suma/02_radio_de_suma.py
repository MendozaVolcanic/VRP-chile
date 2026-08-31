# -*- coding: utf-8 -*-
"""S129 — ¿A QUÉ RADIO suma MIROVA? Barrido, no un corte elegido a dedo.

EL FENÓMENO. Coppola 2019 dice que el VRP es la suma sobre **todos los píxeles
alertados**. Pero «alertado» ya lleva un criterio de distancia adentro: MIROVA no
suma un incendio a 20 km. La pregunta operativa no es «¿sumar o no?» sino **¿hasta
dónde**, y ésa tiene una respuesta empírica: el radio al que nuestra suma reproduce
la magnitud que ellos publican.

Por qué barrer en vez de elegir. La primera medición (01_suma_vs_cluster.py) usó un
corte plano de 5 km, tomado del corte proximal/distal de Coppola 2019 p.4. Funcionó
para nueve volcanes y **falló para PCC**, cuyo lacolito está a 7-10 km del punto de
referencia — por eso su `inner_radius_km` es 20, el único así. Un corte elegido a
dedo mide el corte, no el fenómeno.

⚠️ **LA RESTRICCIÓN QUE MANDA**: `docs/MISSION.md` **excluye lo per-volcán**. Un radio
distinto por volcán sería un parche disfrazado de calibración, del tipo que MISSION
documenta como anti-patrón. Así que la pregunta útil no es «cuál es el mejor radio
para cada uno» sino **¿existe un radio UNIFORME que mejore el conjunto?** — y si no
existe, decirlo, que también es un resultado.

CRITERIO PRE-REGISTRADO, fijado antes de mirar:
  · métrica = |mediana(ratio) − 1| agregada sobre los 11, más el conteo de volcanes
    dentro de la banda de paridad [0,7 – 1,4] de `_s126_lib`;
  · gana el radio uniforme que maximice volcanes-en-banda; a igualdad, el de menor
    error agregado;
  · se reporta TAMBIÉN el mejor radio por volcán, sólo para mostrar la dispersión —
    no como propuesta.

Read-only. Un par por noche, máximo de ambos lados; VIIRS375, que domina el volumen.
"""
import io
import json
import math
import os
import statistics as st
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import BANDA, VENTS, bucket, cargar_mirova, ic95   # noqa: E402

VENTANA = ("2026-01-01", "2026-08-30")
RADIOS = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 25.0]
BUCK = "v375"


def dkm(la, lo, vla, vlo):
    return 111.32 * math.hypot(la - vla, (lo - vlo) * math.cos(math.radians(vla)))


mir, _ = cargar_mirova(VENTANA)

# ── Acumular, por volcán y por radio, los ratios de una pasada por noche ──
por_vol = {}
for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    vla, vlo = VENTS[vol]
    noches = {}
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        d = r.get("datetime_utc", "")[:10]
        sz = r.get("solar_zenith_deg")
        if not (VENTANA[0] <= d <= VENTANA[1]) or (sz is not None and sz < 90):
            continue
        if bucket(r.get("sensor")) != BUCK:
            continue
        px = []
        for q in (r.get("anomaly_pixels") or []):
            v = q.get("vrp_mw") or 0.0
            if v <= 0:
                continue
            dd = q.get("dist_km")
            if dd is None and q.get("lat") is not None:
                dd = dkm(q["lat"], q["lon"], vla, vlo)
            if dd is not None:
                px.append((dd, v))
        pc = (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        # Una pasada por noche: la de mayor energía próxima (criterio estable).
        peso = sum(v for dd, v in px if dd <= 5.0) or pc
        if peso >= noches.get(d, (0, None, None))[0]:
            noches[d] = (peso, px, pc)

    fila = {"n_noches": 0, "por_radio": {}, "cluster": []}
    for d, (_w, px, pc) in noches.items():
        m = (mir.get(vol) or {}).get((d, BUCK))
        if not m or m <= 0:
            continue
        fila["n_noches"] += 1
        if pc > 0:
            fila["cluster"].append(pc / m)
        for R in RADIOS:
            s = sum(v for dd, v in px if dd <= R)
            if s > 0:
                fila["por_radio"].setdefault(R, []).append(s / m)
    if fila["n_noches"] >= 5:
        por_vol[vol] = fila

# ── El barrido, evaluado con el criterio pre-registrado ───────────────────
def en_banda(x):
    return x is not None and BANDA[0] <= x <= BANDA[1]


barrido = []
for R in RADIOS:
    meds, enb = {}, 0
    for vol, f in por_vol.items():
        rs = f["por_radio"].get(R, [])
        med = round(st.median(rs), 3) if len(rs) >= 5 else None
        meds[vol] = med
        if en_banda(med):
            enb += 1
    err = round(sum(abs(m - 1) for m in meds.values() if m is not None), 3)
    barrido.append({"radio_km": R, "en_banda": enb, "de": len(meds),
                    "error_agregado": err, "medianas": meds})

base = {v: (round(st.median(f["cluster"]), 3) if len(f["cluster"]) >= 5 else None)
        for v, f in por_vol.items()}
base_enb = sum(1 for m in base.values() if en_banda(m))
base_err = round(sum(abs(m - 1) for m in base.values() if m is not None), 3)

mejor = max(barrido, key=lambda b: (b["en_banda"], -b["error_agregado"]))

# Sólo para mostrar dispersión — NO es propuesta (MISSION excluye per-volcán).
mejor_por_vol = {}
for vol, f in por_vol.items():
    cand = [(R, st.median(rs)) for R, rs in f["por_radio"].items() if len(rs) >= 5]
    if cand:
        mejor_por_vol[vol] = min(cand, key=lambda c: abs(c[1] - 1))[0]

R_OUT = {"_meta": {"ventana": VENTANA, "sensor": BUCK, "radios": RADIOS,
                   "banda_paridad": list(BANDA),
                   "criterio": "gana el radio UNIFORME con más volcanes en banda; "
                               "a igualdad, menor error agregado. Per-volcán está "
                               "EXCLUIDO por MISSION y sólo se reporta como dispersión."},
         "control_cluster_actual": {"medianas": base, "en_banda": base_enb,
                                    "error_agregado": base_err},
         "barrido": barrido, "mejor_uniforme": mejor,
         "mejor_por_volcan_solo_dispersion": mejor_por_vol}
json.dump(R_OUT, open(os.path.join(AQUI, "02_radio_de_suma.json"), "w",
                      encoding="utf-8"), indent=1, ensure_ascii=False)

print("¿A qué radio suma MIROVA? — VIIRS375, %d volcanes\n" % len(por_vol))
print("%-10s %10s %16s" % ("radio", "en banda", "error agregado"))
print("%-10s %6d/%-3d %16.3f   <- lo que publicamos hoy (un clúster)"
      % ("cluster", base_enb, len(base), base_err))
for b in barrido:
    marca = "  <- mejor uniforme" if b is mejor else ""
    print("%-10s %6d/%-3d %16.3f%s"
          % ("%g km" % b["radio_km"], b["en_banda"], b["de"], b["error_agregado"], marca))

print("\nMedianas por volcán: clúster actual → mejor radio uniforme (%g km)"
      % mejor["radio_km"])
print("%-22s %10s %10s %8s" % ("volcán", "clúster", "%g km" % mejor["radio_km"], "Δ"))
for vol in sorted(por_vol):
    a, b = base.get(vol), mejor["medianas"].get(vol)
    d = "%+.3f" % (b - a) if (a and b) else "-"
    print("%-22s %10s %10s %8s%s" % (vol, a if a else "-", b if b else "-", d,
                                     "  ✓" if en_banda(b) and not en_banda(a) else
                                     ("  ✗ sale" if en_banda(a) and not en_banda(b) else "")))
print("\nDispersión del mejor radio por volcán (NO es propuesta — MISSION excluye "
      "per-volcán):")
print(" ", json.dumps(mejor_por_vol, ensure_ascii=False))
