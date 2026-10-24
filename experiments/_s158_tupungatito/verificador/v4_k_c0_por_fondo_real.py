# -*- coding: utf-8 -*-
"""Verificador S158. La tabla K contra C0 del README (§4) separa las 127 pasadas por `final_hotspot_source` de C0
(test1_roi = fondo local de 1 a 3 km; ctx_cluster = fondo del anillo). Aquí se despeja, para cada record C0 de
esas pasadas, el fondo que reproduce el VRP guardado de sus píxeles (mismo método que e_fondo_local.py) y se
reclasifica por el fondo EFECTIVO: «anillo» si el fondo despejado está a menos de 0,3 K de t_bg_k, «más frío»
si está más de 0,3 K bajo t_bg_k. Si la etiqueta y el fondo efectivo no coinciden, la tabla del README mezcla.

Uso: python -I v4_k_c0_por_fondo_real.py <Tupungatito_pre883.json>
"""
import io
import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

LAM, KW, AREA = pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2


def L(t):
    return C1_PLANCK / (LAM ** 5 * (math.exp(C2_PLANCK / (LAM * t)) - 1.0))


def T_de_L(l):
    return C2_PLANCK / (LAM * math.log(1.0 + C1_PLANCK / (LAM ** 5 * l)))


d = json.load(open(AQUI.parent / "d_pasadas_salida.json", encoding="utf-8"))
pre = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(sys.argv[1], encoding="utf-8"))["records"]
       if not (r.get("regimen") or {}).get("codigo_sha")}
out = []
P = out.append
grupos = defaultdict(list)
cruce = Counter()
for f in d["pasadas"]:
    if not f.get("D_C0"):
        continue
    rc = pre[(f["sensor"], f["pasada"])]
    pix = [p for p in (rc.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= 7.0
           and p["vrp_mw"] > 0]
    ts = [T_de_L(L(p["bt_k"]) - p["vrp_mw"] * 1e6 / (KW * AREA)) for p in pix
          if L(p["bt_k"]) - p["vrp_mw"] * 1e6 / (KW * AREA) > 0]
    if not ts:
        clase = "sin píxel despejable"
    else:
        dT = rc["t_bg_k"] - st.median(ts)
        clase = "anillo" if abs(dT) < 0.3 else ("más frío" if dT > 0 else "más tibio")
    cruce[(f["fuente_C0"], clase)] += 1
    grupos[clase].append(f)
    grupos[(f["fuente_C0"], clase)].append(f)
P(f"pasadas K con C0 publicado (d_pasadas): {sum(1 for f in d['pasadas'] if f.get('D_C0'))}")
P("etiqueta final_hotspot_source de C0 contra fondo efectivo despejado del VRP de sus píxeles:")
for k, v in sorted(cruce.items(), key=str):
    P(f"  {k[0]:12s} {k[1]:22s} {v}")
P("")
P("grupo                                   n    R_C0   R_K   K/C0 (medianas por pasada)")
for k in sorted(grupos, key=str):
    g = grupos[k]
    P(f"  {str(k):38s} {len(g):3d}  {st.median(x['R_C0'] for x in g):.3f}  {st.median(x['R'] for x in g):.3f}  "
      f"{st.median(x['D_sobre_D_C0'] for x in g):.3f}")
txt = "\n".join(out)
print(txt)
(AQUI / "v4_k_c0_por_fondo_real_salida.txt").write_text(txt + "\n", encoding="utf-8")
