# -*- coding: utf-8 -*-
"""S128 Fase 2 · P2(b) — EL CONTROL DE LA SONDA. Intento de REFUTAR mi propio hallazgo.

P2 dijo que en 463 de 482 pasadas donde publicamos VRP>0 la escena de MIROVA no
muestra realce al crater. Antes de creerlo hay que descartar la explicacion
alternativa, que es fuerte y es la de A69:

  el indice z se mide sobre RADIANCIA MIR ABSOLUTA, y el MIR absoluto es
  justamente la variable que el gradiente topografico contamina. MIROVA no detecta
  por MIR absoluto: detecta por NTI, que cancela la topografia. Si el TIF no trae
  banda TIR —y no la trae—, el NTI no se puede reconstruir.

Entonces: **z podria ser un mal instrumento**, y "no hay contraste" podria significar
"este indice no ve lo que MIROVA ve", no "no hay nada".

EL CONTROL, pre-registrado: tomar las pasadas donde **MIROVA misma publico una
ALERTA_TERMICA** en su CSV y medirles el mismo z sobre su propio TIF.

  · Si las alertas de MIROVA tienen z alto y nuestras detecciones sin contraparte
    tienen z bajo -> el instrumento SEPARA, y el hallazgo de P2 se sostiene.
  · Si las alertas de MIROVA tambien tienen z bajo -> el instrumento NO SEPARA y
    P2 no prueba nada sobre nosotros. El hallazgo se cae.

Y una segunda comprobacion, de poder estadistico: cuanto z produciria un foco del
tamano que publicamos. Si un VRP de 0,3 MW implica un salto de radiancia por debajo
del ruido de la escena, la sonda es ciega por construccion y hay que decirlo.

Read-only.
"""
import collections
import csv
import datetime as dt
import io
import json
import os
import statistics as st
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import ALIAS                                    # noqa: E402

P2 = json.load(open(os.path.join(AQUI, "02_contraste_al_crater.json"), encoding="utf-8"))
esc = P2["escenas"]
SEN_CSV = {"MODIS": "modis", "VIIRS": "v750", "VIIRS375": "v375"}
TOL_MIN = 45

# ── 1. Las pasadas donde MIROVA misma alerto ───────────────────────────────
alertas = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(ROOT, "latest_consolidado.csv"),
                             encoding="utf-8", errors="replace")):
    tipo = (r.get("Tipo_Registro") or "").strip()
    nom = (r.get("Volcan") or "").strip()
    vol = next((v for v, al in ALIAS.items() if nom in al), None)
    b = SEN_CSV.get((r.get("Sensor") or "").strip().upper())
    f = (r.get("Fecha_Satelite_UTC") or "").strip()
    if vol is None or b is None or len(f) < 16:
        continue
    try:
        t = dt.datetime.fromisoformat(f[:19].replace("Z", ""))
    except ValueError:
        continue
    if not ("2026-05-08" <= f[:10] <= "2026-05-20"):
        continue
    try:
        vrp = float(r.get("VRP_MW") or 0)
    except ValueError:
        vrp = 0.0
    alertas[(vol, b)].append((t, tipo, vrp))

# ── 2. Pegar z a cada tipo de registro de MIROVA ──────────────────────────
por_tipo = collections.defaultdict(list)
detalle_alertas = []
for e in esc:
    te = dt.datetime.fromisoformat(e["ts"])
    cand = alertas.get((e["vol"], e["sensor"]), [])
    if not cand:
        continue
    t, tipo, vrp = min(cand, key=lambda c: abs((c[0] - te).total_seconds()))
    if abs((t - te).total_seconds()) / 60.0 > TOL_MIN:
        continue
    por_tipo[tipo].append(e["z_crater"])
    if tipo == "ALERTA_TERMICA":
        detalle_alertas.append({"vol": e["vol"], "sensor": e["sensor"], "ts": e["ts"],
                                "vrp_mirova": vrp, "z_crater": e["z_crater"],
                                "z_max_escena": e["z_max_escena"],
                                "dist_max_km": e["dist_max_al_crater_km"]})


def resu(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), 2),
            "p25": round(xs[len(xs) // 4], 2), "p75": round(xs[3 * len(xs) // 4], 2),
            "max": round(xs[-1], 2),
            "pct_z_ge_3": round(100.0 * sum(1 for x in xs if x >= 3) / len(xs), 1),
            "pct_z_ge_5": round(100.0 * sum(1 for x in xs if x >= 5) / len(xs), 1)}


# ── 3. Nuestras detecciones sin contraparte, para comparar en la misma escala ─
nuestros_sin_apoyo = [p["z_crater"] for p in P2["pares"] if p["vrp_nuestro"] > 0]

# ── 4. Poder estadistico: ¿que z produce el VRP que publicamos? ───────────
# ΔL = VRP / (A_pix · k)  ->  z = ΔL / sigma_MAD de la escena.
K = {"modis": 18.9, "v750": 19.7, "v375": 18.0}
A = {"modis": 1.0e6, "v750": 562500.0, "v375": 140625.0}
poder = {}
for s in ("modis", "v750", "v375"):
    sig = [e["sigma_mad"] for e in esc if e["sensor"] == s and e["sigma_mad"] > 0]
    if not sig:
        continue
    sm = float(np.median(sig))
    poder[s] = {"sigma_mad_mediano_escena": round(sm, 5),
                "z_esperado_por_vrp_mw": {
                    str(v): round((v * 1e6 / (A[s] * K[s])) / sm, 2)
                    for v in (0.05, 0.1, 0.3, 1.0, 3.0, 10.0)}}

R = {"_meta": {"pregunta": "¿el indice z separa lo que MIROVA alerta de lo que no?",
               "tolerancia_min": TOL_MIN,
               "caveat": "el TIF no trae banda TIR: el NTI no se puede reconstruir. "
                         "z se mide sobre MIR absoluto, la variable que A69 dice "
                         "contaminada por el gradiente topografico."},
     "z_por_tipo_de_registro_MIROVA": {k: resu(v) for k, v in sorted(por_tipo.items())},
     "z_de_nuestras_detecciones_vrp_pos": resu(nuestros_sin_apoyo),
     "poder_estadistico": poder,
     "alertas_mirova_con_z": sorted(detalle_alertas, key=lambda d: -d["vrp_mirova"])[:40]}
json.dump(R, open(os.path.join(AQUI, "02b_control.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("== z_crater segun lo que MIROVA misma dijo de esa pasada ==")
for k, v in sorted(por_tipo.items()):
    print(" %-18s %s" % (k, json.dumps(resu(v), ensure_ascii=False)))
print("\n== z_crater de NUESTRAS pasadas con vrp>0 ==")
print(" ", json.dumps(resu(nuestros_sin_apoyo), ensure_ascii=False))
print("\n== PODER: z que produciria un foco del tamano que publicamos ==")
for s, d in poder.items():
    print(" %-6s sigma_MAD escena = %.5f" % (s, d["sigma_mad_mediano_escena"]))
    print("        z esperado:", json.dumps(d["z_esperado_por_vrp_mw"]))
print("\n== Las ALERTAS de MIROVA con mayor VRP, y su z en su propio TIF ==")
print(" %-20s %-7s %-20s %9s %8s %9s %8s" % ("volcan", "sensor", "ts", "vrp_MIR",
                                             "z_crater", "z_max_esc", "d_max_km"))
for d in R["alertas_mirova_con_z"][:20]:
    print(" %-20s %-7s %-20s %9.3f %8.2f %9.2f %8.2f" % (
        d["vol"], d["sensor"], d["ts"], d["vrp_mirova"], d["z_crater"],
        d["z_max_escena"] or 0, d["dist_max_km"]))
