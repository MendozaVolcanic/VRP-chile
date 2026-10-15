# -*- coding: utf-8 -*-
"""Tarea 1.14: definiciones compartidas del presupuesto de magnitud (una sola copia).

POR QUE un modulo comun: las tres partes (OSF 2025, NRT 2026, brazos de A/B) descomponen la misma
identidad, R = F_rec * F_n * F_hot * F_bg (PREREGISTRO.md), y si cada script escribiera su Planck o su
reparto del deficit, una diferencia de codigo se leeria como diferencia fisica.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

import numpy as np

# Coeficiente de Wooster por area nadir fija (CLAUDE.md del proyecto, calibrado S14; S139 paso 1 verifico
# que MIROVA usa exactamente estos tres en el OSF v2.5).
KA = {"VIIRS375": 18.0 * 140625.0, "VIIRS750": 19.7 * 562500.0, "MODIS": 18.9 * 1.0e6}
# Banda MIR que usa NUESTRO codigo (MODIS banda 21, D21): process_viirs.py I04_LAMBDA,
# process_viirs_mod.py M13, process_modis.py BAND21_LAMBDA.
LAM = {"VIIRS375": 3.74, "VIIRS750": 4.05, "MODIS": 3.929}
C1, C2 = 1.191042e8, 14388.0
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5,
         "Chaiten": 5, "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
# volcanoes.yaml `local_kernel_bg: true` (D25): ahi el fondo NO es la mediana del anillo.
KERNEL = {"PuyehueCordonCaulle", "Villarrica", "Chaiten", "PlanchonPeteroa", "Lastarria"}
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
SEMILLA = 114
N_BOOT = 2000
BANDAS_Z = [(0, 20), (20, 35), (35, 50), (50, 90)]


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def planck(t_k, b):
    lam = LAM[b]
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t_k)) - 1.0))


def banda_z(z):
    if z is None or not np.isfinite(z):
        return None
    z = abs(z)
    for lo, hi in BANDAS_Z:
        if lo <= z < hi:
            return f"{lo}-{hi}"
    return None


def pixeles_inner(rec, vol):
    """(S_in en MW, n+, Lh medio de los n+, n con vrp 0) de los anomaly_pixels a dist_km <= inner."""
    b = bucket(rec.get("sensor"))
    px = [p for p in (rec.get("anomaly_pixels") or [])
          if p.get("dist_km") is not None and p["dist_km"] <= INNER[vol]]
    pos = [p for p in px if (p.get("vrp_mw") or 0) > 0 and p.get("bt_k")]
    s_in = sum(p["vrp_mw"] for p in pos)
    lh = float(np.mean([planck(p["bt_k"], b) for p in pos])) if pos else float("nan")
    return s_in, len(pos), lh, len(px) - len(pos)


def fondo_implicito(s_in_mw, n_pos, lh, b):
    """Fondo medio que hace exacta la suma: Lbg = Lh - S_in / (kA n+)."""
    if n_pos <= 0:
        return float("nan")
    return lh - s_in_mw * 1e6 / (KA[b] * n_pos)


def hav_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def control_un_pixel(rec):
    """C2: si el cumulo es de un pixel, ese pixel esta entre los anomaly_pixels. None si no aplica."""
    pc = rec.get("primary_cluster") or {}
    if pc.get("n_pixels") != 1 or pc.get("vrp_mw") is None or pc.get("centroid_lat") is None:
        return None
    for p in rec.get("anomaly_pixels") or []:
        if p.get("lat") is None or p.get("vrp_mw") is None:
            continue
        if (abs(p["vrp_mw"] - pc["vrp_mw"]) <= 0.0006
                and hav_km(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= 0.05):
            return True
    return False


# ---------------------------------------------------------------- reparto del deficit
def gm(x):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v) and v > 0], dtype=float)
    return float(np.exp(np.log(x).mean())) if len(x) else float("nan")


def _reparto(filas, factores):
    lr = np.array([math.log(f["R"]) for f in filas])
    m = lr.mean()
    out = {"lnR": m, "R_gm": math.exp(m)}
    for k in factores:
        v = np.array([f[k] for f in filas], dtype=float)
        out[k] = float(v.mean())
        out["frac_" + k] = float(v.mean() / m) if m != 0 else float("nan")
    return out


def reparto_con_ic(filas, factores, semilla=SEMILLA, n_boot=N_BOOT):
    """Reparto del deficit en escala log (media de ln F_k / media de ln R), con bootstrap por noche.

    `filas`: dicts con "R" (>0), "noche_id" y, para cada nombre en `factores`, el LOGARITMO del factor
    por pasada. Devuelve el punto y los percentiles 2,5 y 97,5 de: R_gm, exp(media ln F_k), frac_k.
    """
    filas = [f for f in filas if f["R"] > 0 and all(np.isfinite(f[k]) for k in factores)]
    if not filas:
        return None
    punto = _reparto(filas, factores)
    por_noche = defaultdict(list)
    for f in filas:
        por_noche[f["noche_id"]].append(f)
    noches = list(por_noche)
    rng = random.Random(semilla)
    boots = []
    for _ in range(n_boot):
        muestra = [f for _ in noches for f in por_noche[noches[rng.randrange(len(noches))]]]
        boots.append(_reparto(muestra, factores))
    res = {"n_pasadas": len(filas), "n_noches": len(noches), "R_mediana": float(np.median([f["R"] for f in filas]))}
    claves = ["R_gm"] + [k for k in factores] + ["frac_" + k for k in factores]
    for c in claves:
        vals = np.array([b[c] for b in boots], dtype=float)
        if c in factores:   # se informa el factor en escala lineal (media geometrica)
            p, lo, hi = math.exp(punto[c]), math.exp(np.nanpercentile(vals, 2.5)), math.exp(np.nanpercentile(vals, 97.5))
        else:
            p, lo, hi = punto[c], np.nanpercentile(vals, 2.5), np.nanpercentile(vals, 97.5)
        res[c] = [round(float(p), 4), round(float(lo), 4), round(float(hi), 4)]
    return res


def frac_angulo_con_ic(filas, clave_log, semilla=SEMILLA, n_boot=1000):
    """Fraccion del deficit (media ln R) que se va en la dependencia cenital de `clave_log`, con bootstrap por noche.

    Por pasada, el aporte del angulo es el efecto de su banda contra 0-20 (efecto_cenital, efecto fijo por
    volcan); la fraccion es la media de esos aportes sobre la media de ln R. Las pasadas cuya banda no tiene
    efecto estimable aportan 0 (se declara: sesga la fraccion hacia abajo, nunca hacia arriba).
    """
    filas = [f for f in filas if f["R"] > 0 and np.isfinite(f[clave_log])]
    if len(filas) < 10:
        return None

    def una(sub):
        ef = efecto_cenital(sub, clave_log)
        ap = [(ef.get(f.get("banda_z"), (None,))[0] or 0.0) for f in sub]
        m = np.mean([math.log(f["R"]) for f in sub])
        return float(np.mean(ap) / m) if m else float("nan"), float(np.mean(ap))

    p_frac, p_ap = una(filas)
    por_noche = defaultdict(list)
    for f in filas:
        por_noche[f["noche_id"]].append(f)
    noches = list(por_noche)
    rng = random.Random(semilla)
    bf, ba = [], []
    for _ in range(n_boot):
        sub = [f for _ in noches for f in por_noche[noches[rng.randrange(len(noches))]]]
        a, b = una(sub)
        bf.append(a)
        ba.append(b)
    return {"frac": [round(p_frac, 4), round(float(np.nanpercentile(bf, 2.5)), 4), round(float(np.nanpercentile(bf, 97.5)), 4)],
            "factor_medio": [round(math.exp(p_ap), 4), round(math.exp(np.nanpercentile(ba, 2.5)), 4),
                             round(math.exp(np.nanpercentile(ba, 97.5)), 4)]}


def efecto_cenital(filas, clave_log):
    """Efecto de cada banda de angulo cenital sobre `clave_log` (log), contra 0-20, con efecto fijo por volcan.

    Estimador simple y transparente: para cada volcan, media del log en cada banda menos la media en
    0-20; se promedia entre volcanes pesando por el minimo de pasadas de las dos bandas. Devuelve
    {banda: (efecto, n_volcanes)}. Una banda sin volcanes con las dos bandas pobladas (>= 3 pasadas
    cada una) queda en None.
    """
    por = defaultdict(lambda: defaultdict(list))
    for f in filas:
        bz = f.get("banda_z")
        if bz is not None and np.isfinite(f[clave_log]):
            por[f["vol"]][bz].append(f[clave_log])
    out = {}
    ref = "0-20"
    for lo, hi in BANDAS_Z:
        bz = f"{lo}-{hi}"
        if bz == ref:
            out[bz] = (0.0, None)
            continue
        num, den, nv = 0.0, 0.0, 0
        for vol, d in por.items():
            if len(d.get(ref, [])) >= 3 and len(d.get(bz, [])) >= 3:
                w = min(len(d[ref]), len(d[bz]))
                num += w * (np.mean(d[bz]) - np.mean(d[ref]))
                den += w
                nv += 1
        out[bz] = (num / den, nv) if den else (None, 0)
    return out
