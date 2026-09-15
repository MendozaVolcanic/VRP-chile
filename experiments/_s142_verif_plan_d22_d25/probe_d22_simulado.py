# -*- coding: utf-8 -*-
"""Verificador S142: simula D22 SIN tocar pipeline/, envolviendo SOLO los tres helpers contextuales
(no el camino B NTI>K1 ni el C) con bt_sanity_k=-inf, que equivale a exigir BT no-NaN. Compara con
la corrida sin parche en la escena principal del arnés del plan."""
import json, os, sys
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np
import arnes_copia_del_plan as A
import pipeline.process_viirs as pv
import pipeline.detection_context as dc

def envolver(f):
    def g(*a, **k):
        if "bt_sanity_k" in k: k["bt_sanity_k"] = -np.inf
        return f(*a, **k)
    return g

def resumen(r):
    return dict(fp=r.get("diag_n_first_pass_pixels"), sp=r.get("diag_n_second_pass_recapture"),
                n_dnti_ctx=r.get("n_dnti_ctx_path_pixels", r.get("n_dnti_ctx_path")),
                src=r.get("final_hotspot_source"), pix=[(p["bt_k"], p["vrp_mw"]) for p in r["anomaly_pixels"]],
                pc=r.get("primary_cluster"))

out = {}
for tipo in ("nevado_vecino_tibio", "foco_3x3", "plana"):
    for k in (False, True):
        base = A.correr_v375(tipo, k, {})
        with patch.object(pv, "dual_roi_contextual_dnti_hot_mask", envolver(dc.dual_roi_contextual_dnti_hot_mask)), \
             patch.object(pv, "contextual_dnti_hot_mask", envolver(dc.contextual_dnti_hot_mask)), \
             patch.object(pv, "first_pass_tests_2_and_3", envolver(dc.first_pass_tests_2_and_3)):
            sim = A.correr_v375(tipo, k, {})
        out[f"{tipo}|kernel={k}"] = {"hoy": resumen(base), "d22_sim": resumen(sim),
                                     "claves_distintas": sorted(x for x in set(base)|set(sim) if json.dumps(base.get(x),sort_keys=True,default=str)!=json.dumps(sim.get(x),sort_keys=True,default=str))}
# helpers con compuerta en -inf: índices del cráter
e = A.entradas_helpers()
c = A.CENTRO_V375*A.N_V375 + A.CENTRO_V375
fp, d = dc.first_pass_tests_2_and_3(nti=e["nti"], nti_app=e["nti_app"], bt=e["bt"], roi_mask=e["roi"], dist_km=e["dist"],
        t_bg=e["t_bg"], bt_sanity_k=-np.inf, inner_km=5.0, c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10)
ctx = dc.contextual_dnti_hot_mask(nti=e["nti"], bt=e["bt"], roi_mask=e["roi"], t_bg=e["t_bg"], c1=0.003, bt_sanity_k=-np.inf, apply_unsuitable_filters=True)
dual = dc.dual_roi_contextual_dnti_hot_mask(nti=e["nti"], bt=e["bt"], roi_mask=e["roi"], dist_km=e["dist"], t_bg=e["t_bg"], c1_summit=0.003, c1_scene=0.010, inner_km=5.0, bt_sanity_k=-np.inf, apply_unsuitable_filters=True)
out["helpers_menos_inf"] = {"crater": c, "vecino": c+1, "t_bg": e["t_bg"], "fp": np.flatnonzero(fp).tolist(),
                            "ctx": np.flatnonzero(ctx).tolist(), "dual": np.flatnonzero(dual).tolist(),
                            "diag": {kk: d[kk] for kk in ("mu_dnti","sd_dnti","n_bg_used")}}
print(json.dumps(out, indent=1, default=str))
