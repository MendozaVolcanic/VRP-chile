# -*- coding: utf-8 -*-
"""Base comun de la medicion H2/H3 (S148). Reusa el cargador y el etiquetado del verificador
(experiments/_s148_verificador_conectiva/verif_base.py) sin modificarlo.

Uso de los scripts: python hX.py <dir_salidas_run> <dir_congelado> [fin=2026-09-17]
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_s148_verificador_conectiva"))
from verif_base import B, F, INNER, cargar_brazo, cargar_ref, etiquetar, hav, zona  # noqa: E402,F401

BT_GATE_K = 3.0   # NTI_BT_SANITY_K leido de pipeline.profile con VRP_PROFILE=_s147_ab_sin_test1_max
R_CORE_KM = 0.75  # pipeline/f5_core.py F5_R_CORE_KM


def cargar(argv):
    d, cong = argv[1], argv[2]
    fin = argv[3] if len(argv) > 3 else "2026-09-17"
    rb, _ = cargar_brazo(d + "/" + B)
    rf, _ = cargar_brazo(d + "/" + F)
    filas = cargar_ref(cong)
    lab, por = etiquetar(rb, filas, "2026-09-01", fin)
    comunes = [k for k in lab if k in rf]
    return rb, rf, lab, por, comunes


def mirova_mw(k, por):
    """Magnitud de MIROVA de la pasada: maximo de las ALERTAS a 2 min (igual que el verificador)."""
    t = datetime.strptime(k[2], "%Y-%m-%d %H:%M")
    fs = [f["vrp"] for f in por.get((k[0], k[1]), [])
          if abs((f["dt"] - t).total_seconds()) <= 120 and f["tipo"].startswith("ALERTA") and (f["vrp"] or 0) > 0]
    return (max(fs), len(fs)) if fs else (None, 0)


def nucleo(r, inner):
    """Port de pipeline/f5_core.py: devuelve (pixeles del nucleo, pixel pico) o (None, None)."""
    px = r.get("anomaly_pixels") or []
    pc = r.get("primary_cluster")
    if not px or not pc or pc.get("centroid_lat") is None:
        return None, None
    cand = [p for p in px if hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= inner]
    if not cand:
        return None, None
    peak = 0
    for i in range(1, len(cand)):
        if (cand[i].get("vrp_mw") or 0) > (cand[peak].get("vrp_mw") or 0):
            peak = i
    pk = cand[peak]
    keep = [p for i, p in enumerate(cand)
            if i == peak or hav(p["lat"], p["lon"], pk["lat"], pk["lon"]) <= R_CORE_KM or (p.get("bt_k") or 0) >= 295.0]
    return keep, pk


def clave_px(p):
    return (p["lat"], p["lon"])
