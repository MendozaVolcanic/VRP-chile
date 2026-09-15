# -*- coding: utf-8 -*-
"""S141, Fase 1: análisis puro del vecindario del foco (sin red, sin pipeline).

POR QUÉ. MIROVA suma los píxeles tibios que rodean al foco y calcula el fondo de cada píxel
alertado como la media de sus vecinos no alertados (Campus et al. 2024, Bull. Volcanol. 86:25,
p. 3, ec. 1 y 2; verificado S141 en docs/audit_s141/lectura/VERIFICADOR_LECTORES.md V-07).
Nosotros publicamos 1 píxel donde MIROVA suma 3 o más (S139, F_n 0,553). Este módulo dice, para
cada uno de los 8 vecinos nativos del foco, en qué etapa del ensamblado se perdió y cuánto habría
aportado con el fondo del anillo y con fondo local.

ETAPAS, en el orden del ensamblado VIIRS 375 m: primer pase (Tests 2 y 3), segundo pase
(adyacencia), Test 1, filtro contextual con keep_peak, cúmulo final.

INSTRUMENTO. P1: en pasadas control (publicamos tantos píxeles como MIROVA) los vecinos deben
salir mayormente "incluido"; si no, el veredicto es INDETERMINADO. P2: si alguna máscara no tiene
la forma de la escena de BT, la pasada se marca grilla_ok=False y no entra al criterio.
Plan y criterio pre-registrado: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md
"""
import math
import statistics

import numpy as np

ORDEN = ("first_pass", "second_pass", "test1", "ctx_filter_out", "cluster")
LAMBDA_I04_UM = 3.74
C1, C2 = 1.191042e8, 14388.0
KA_375 = 18.0 * 140625          # coeficiente de Wooster por área nadir, igual que el pipeline
UMBRAL_CONCENTRA = 0.5
N_MIN = 10


def planck(t_k, lam=LAMBDA_I04_UM):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t_k)) - 1))


def aporte_mw(bt_k, fondo_k):
    """VRP de un píxel con ese fondo, en MW; nunca negativo (así lo publica el pipeline)."""
    if bt_k is None or fondo_k is None or not np.isfinite(bt_k) or not np.isfinite(fondo_k):
        return 0.0
    return max(planck(bt_k) - planck(fondo_k), 0.0) * KA_375 / 1e6


def _vecinos(shape, i, j):
    return [(i + di, j + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)
            if (di or dj) and 0 <= i + di < shape[0] and 0 <= j + dj < shape[1]]


def fondo_local_k(bt, alertado, i, j):
    """BT equivalente a la radiancia media de los vecinos no alertados del píxel (i, j)."""
    ls = [planck(bt[a, b]) for a, b in _vecinos(bt.shape, i, j)
          if not alertado[a, b] and np.isfinite(bt[a, b])]
    if not ls:
        return None
    lm = sum(ls) / len(ls)
    return C2 / (LAMBDA_I04_UM * math.log(1 + C1 / (LAMBDA_I04_UM ** 5 * lm)))


def etapa_de_perdida(estado):
    if estado.get("cluster"):
        return "incluido"
    vistos = [e for e in ORDEN if estado.get(e)]
    if not vistos:
        return "nunca_candidato"
    for e in ORDEN[ORDEN.index(vistos[-1]) + 1:]:
        if estado.get(e) is False:
            return f"perdido_en_{e}"
    return f"perdido_despues_de_{vistos[-1]}"


def resumir_vecindario(bt, lat, lon, mascaras, osf_lat, osf_lon, t_bg_anillo):
    bt = np.asarray(bt, dtype=float)
    formas = {k: np.asarray(v).shape for k, v in mascaras.items() if v is not None}
    if any(s != bt.shape for s in formas.values()) or np.asarray(lat).shape != bt.shape:
        return {"grilla_ok": False, "formas": {k: list(s) for k, s in formas.items()},
                "forma_bt": list(bt.shape)}
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    d2 = (lat - osf_lat) ** 2 + ((lon - osf_lon) * math.cos(math.radians(osf_lat))) ** 2
    i, j = np.unravel_index(np.nanargmin(d2), d2.shape)
    dist_km = float(math.sqrt(d2[i, j]) * 111.195)
    alertado = np.zeros(bt.shape, bool)
    for v in mascaras.values():
        if v is not None:
            alertado |= np.asarray(v, bool)
    conteo, vecinos = {}, []
    perd_anillo = perd_local = 0.0
    for a, b in _vecinos(bt.shape, i, j):
        estado = {e: (bool(mascaras[e][a, b]) if mascaras.get(e) is not None else None) for e in ORDEN}
        etapa = etapa_de_perdida(estado)
        conteo[etapa] = conteo.get(etapa, 0) + 1
        fl = fondo_local_k(bt, alertado, a, b)
        ap_anillo, ap_local = aporte_mw(bt[a, b], t_bg_anillo), aporte_mw(bt[a, b], fl)
        if etapa != "incluido":
            perd_anillo += ap_anillo
            perd_local += ap_local
        vecinos.append({"ij": [int(a), int(b)], "bt_k": round(float(bt[a, b]), 2), "etapa": etapa,
                        "fondo_local_k": None if fl is None else round(fl, 2),
                        "aporte_fondo_anillo_mw": round(ap_anillo, 4),
                        "aporte_fondo_local_mw": round(ap_local, 4)})
    return {"grilla_ok": True, "centro": [int(i), int(j)], "dist_centro_a_osf_km": round(dist_km, 3),
            "bt_centro_k": round(float(bt[i, j]), 2), "conteo": conteo, "vecinos": vecinos,
            "aporte_perdidos_fondo_anillo_mw": round(perd_anillo, 4),
            "aporte_perdidos_fondo_local_mw": round(perd_local, 4)}


def _dominante(filas):
    total = {}
    for f in filas:
        for k, v in f["resumen"]["conteo"].items():
            if k != "incluido":
                total[k] = total.get(k, 0) + v
    n = sum(total.values())
    if not n:
        return None, 0.0, total
    k = max(total, key=total.get)
    return k, total[k] / n, total


def evaluar_criterio(filas, regimen=None):
    buenas = [f for f in filas if f.get("ok") and (f.get("resumen") or {}).get("grilla_ok")
              and (regimen is None or f.get("regimen") == regimen)]
    cand = [f for f in buenas if f["clase"] == "candidato"]
    ctl = [f for f in buenas if f["clase"] == "control"]
    out = {"n_candidatos": len(cand), "n_controles": len(ctl)}
    # P3 (S141, pregunta de Nicolás): la muestra se eligió con records de 2025 procesados con el
    # código del backfill; el probe reprocesa con el de hoy. Se cuenta cuántos candidatos siguen
    # publicando un solo píxel hoy, para no atribuir al código actual una pérdida que ya no ocurre.
    out["candidatos_hoy_pc_n_1"] = sum(1 for f in cand if (f.get("hoy") or {}).get("pc_n") == 1)
    out["candidatos_hoy_pc_n_otro"] = sum(1 for f in cand if (f.get("hoy") or {}).get("pc_n") not in (None, 1))
    inc = sum(f["resumen"]["conteo"].get("incluido", 0) for f in ctl)
    tot = sum(sum(f["resumen"]["conteo"].values()) for f in ctl)
    out["control"] = "OK" if tot and inc / tot >= UMBRAL_CONCENTRA else "FALLA"
    k, frac, total = _dominante(cand)
    out["perdidas_por_etapa"] = total
    out["fraccion_etapa_dominante"] = round(frac, 4)
    out["etapa"] = f"PALANCA:{k}" if k and frac >= UMBRAL_CONCENTRA else "DISPERSA"
    fr = [f["resumen"].get("fraccion_brecha_fondo_local") for f in cand]
    fr = [x for x in fr if x is not None]
    med = statistics.median(fr) if fr else None
    out["mediana_fraccion_brecha_fondo_local"] = med
    out["fondo"] = (None if med is None else "FONDO_LOCAL_CIERRA_BRECHA" if med >= 0.5
                    else "NO_CIERRA" if med < 0.2 else "PARCIAL")
    if len(cand) < N_MIN or out["control"] != "OK":
        out["veredicto"] = "INDETERMINADO"
    else:
        out["veredicto"] = f"{out['etapa']} | {out['fondo']}"
    return out
