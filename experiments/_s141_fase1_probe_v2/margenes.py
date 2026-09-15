# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): margen de cada vecino a cada test de la detección que le correspondía.

POR QUÉ (VERIFICADOR_V2_PRE_CORRIDA.md H3). Un vecino alertado del centro siempre queda en el cúmulo
(`clustering.py:91-96`, componentes 8-conexas), así que la pregunta "en qué etapa del ensamblado se
pierde" tiene respuesta antes de correr. La pérdida de los vecinos tibios que MIROVA suma está en la
DETECCIÓN: algún test los deja fuera. Este módulo dice cuál y por cuánto, en las unidades del test:

  * dNTI y dETI contra su umbral efectivo, con la conectiva del código de hoy
    (`combinar = max if use_prose_branch else min`, detection_context.py:510 y :924);
  * la compuerta de temperatura bt > t_bg + 3 K del primer pase y del dNTI contextual (D22,
    detection_context.py:532 y :269); el segundo pase NO la tiene (:939-940);
  * en la ruta del Test 1, pertenecer al disco (`mask_contributing`) y los filtros "no aptos" (§267-273).

CÓMO. No reimplementa la detección de memoria: toma los argumentos con que el pipeline llamó a cada
función (capturados por `captura.py`), los enlaza con la firma REAL (`inspect.signature`, así los
valores por defecto son los de la función) y recalcula el test en esos píxeles. Cada margen trae
`replica_ok`: si el "pasa" recalculado no coincide con la máscara que devolvió la función, el
instrumento está mal y el control C4 del criterio lo detecta.
"""
import inspect
import math

import numpy as np

from pipeline.detection_context import (_nanmean_8neighbors_fast, _vecindad_8, dual_roi_contextual_dnti_hot_mask,
                                        first_pass_tests_2_and_3, roi1_summit_mask, second_pass_adjacent)


def _args(ev, fn):
    b = inspect.signature(fn).bind(*ev.get("a", ()), **ev.get("kw", {}))
    b.apply_defaults()
    return b.arguments


def _f(x):
    return float(x) if x is not None else None


def _fin(*xs):
    return all(x is not None and math.isfinite(x) for x in xs)


def _vecinos8(forma, i, j):
    return [(i + a, j + b) for a in (-1, 0, 1) for b in (-1, 0, 1)
            if (a or b) and 0 <= i + a < forma[0] and 0 <= j + b < forma[1]]


def margenes_primer_pase(ev, pixeles):
    """Tests 2 ∧ 3 + compuerta de BT del primer pase (detection_context.py:463-533)."""
    A = _args(ev, first_pass_tests_2_and_3)
    d = ev.get("diag") or {}
    nti, bt, roi = np.asarray(A["nti"], float), np.asarray(A["bt"], float), np.asarray(A["roi_mask"], bool)
    eti, hot = d.get("eti"), np.asarray(ev["hot"], bool)
    comb = max if A["use_prose_branch"] else min
    compuerta = float(A["t_bg"]) + float(A["bt_sanity_k"])
    con_estadistica = d.get("mu_dnti") is not None and eti is not None
    if con_estadistica:
        eti = np.asarray(eti, float)
        dnti = nti - _nanmean_8neighbors_fast(nti)
        deti = eti - _nanmean_8neighbors_fast(eti)
        summit = np.asarray(roi1_summit_mask(A["dist_km"], A["inner_km"], A["roi1_mask"]), bool)
        dual = A["c1_dnti_scene"] is not None
    out = {}
    for ij in pixeles:
        ij = tuple(ij)
        b = float(bt[ij])
        r = {"bt_k": b, "compuerta_bt_k": compuerta, "margen_bt_k": b - compuerta, "en_roi": bool(roi[ij])}
        if not con_estadistica:
            r.update(sin_estadistica=True, pasa=False)
        else:
            s = "summit" if (bool(summit[ij]) or not dual) else "scene"
            tn = comb(A[f"c1_dnti_{s}"], d["mu_dnti"] + A[f"c2_dnti_{s}"] * d["sd_dnti"])
            te = comb(A[f"c1_deti_{s}"], d["mu_deti"] + A[f"c2_deti_{s}"] * d["sd_deti"])
            dn, de = float(dnti[ij]), float(deti[ij])
            r.update(roi1=s, dnti=dn, umbral_dnti=tn, margen_dnti=dn - tn, deti=de, umbral_deti=te,
                     margen_deti=de - te)
            r["pasa"] = bool(r["en_roi"] and _fin(dn, de) and dn > tn and de > te and b > compuerta)
        r["replica_ok"] = r["pasa"] == bool(hot[ij])
        out[ij] = r
    return out


def margenes_segundo_pase(ev, pixeles):
    """Tests 2 ∧ 3 recalculados excluyendo los activos de la media de vecinos, sin compuerta de BT
    (detection_context.py:884-948)."""
    A = _args(ev, second_pass_adjacent)
    nti, eti = np.asarray(A["nti"], float), np.asarray(A["eti"], float)
    act, sal = np.asarray(A["active_mask"], bool), np.asarray(ev["salida"], bool)
    comb = max if A["use_prose_branch"] else min
    stats = None
    if not (A["conditioned"] and not act.any()):
        dnti = nti - _nanmean_8neighbors_fast(np.where(act, np.nan, nti))
        deti = eti - _nanmean_8neighbors_fast(np.where(act, np.nan, eti))
        bg = (~act) & np.isfinite(dnti) & np.isfinite(deti)
        if int(np.count_nonzero(bg)) >= A["min_bg_pixels"]:
            stats = {"mu_dnti": float(np.mean(dnti[bg])), "sd_dnti": float(np.std(dnti[bg])),
                     "mu_deti": float(np.mean(deti[bg])), "sd_deti": float(np.std(deti[bg]))}
    if stats is not None:
        dual = (A["is_summit"] is not None and A["c1_dnti_scene"] is not None and A["c1_deti_scene"] is not None
                and A["c2_dnti_scene"] is not None and A["c2_deti_scene"] is not None)
        summit = np.asarray(A["is_summit"], bool) if dual else None
        vec8 = _vecindad_8(act) if A["conditioned"] else None
    out = {}
    for ij in pixeles:
        ij = tuple(ij)
        r = {"activo_previo": bool(act[ij])}
        if stats is None:
            r.update(sin_estadistica=True, pasa=bool(act[ij]))
        else:
            if dual and not bool(summit[ij]):
                c1n, c2n, c1e, c2e, s = A["c1_dnti_scene"], A["c2_dnti_scene"], A["c1_deti_scene"], A["c2_deti_scene"], "scene"
            else:
                c1n, c2n, c1e, c2e, s = A["c1_dnti"], A["c2_dnti"], A["c1_deti"], A["c2_deti"], "summit"
            tn = comb(c1n, stats["mu_dnti"] + c2n * stats["sd_dnti"])
            te = comb(c1e, stats["mu_deti"] + c2e * stats["sd_deti"])
            dn, de = float(dnti[ij]), float(deti[ij])
            nuevo = _fin(dn, de) and dn > tn and de > te and (vec8 is None or bool(vec8[ij]))
            r.update(roi1=s, dnti=dn, umbral_dnti=tn, margen_dnti=dn - tn, deti=de, umbral_deti=te,
                     margen_deti=de - te, pasa=bool(act[ij] or nuevo))
        r["replica_ok"] = r["pasa"] == bool(sal[ij])
        out[ij] = r
    return out


def margenes_dnti_ctx(ev, pixeles):
    """dNTI contextual dual-ROI de la ruta del Test 1 (detection_context.py:241-284, :359-378)."""
    A = _args(ev, dual_roi_contextual_dnti_hot_mask)
    nti, bt = np.asarray(A["nti"], float), np.asarray(A["bt"], float)
    roi, sal = np.asarray(A["roi_mask"], bool), np.asarray(ev["salida"], bool)
    summit = np.asarray(roi1_summit_mask(A["dist_km"], A["inner_km"], A["roi1_mask"]), bool)
    compuerta = float(A["t_bg"]) + float(A["bt_sanity_k"])
    H, W = nti.shape
    out = {}
    for ij in pixeles:
        ij = tuple(ij)
        i, j = ij
        vals = np.array([nti[v] for v in _vecinos8(nti.shape, i, j) if not np.isnan(nti[v])], float)
        media = float(np.mean(vals)) if vals.size else float("nan")     # _nanmean_ignore_self (:192-205)
        dn = float(nti[ij]) - media
        c1 = float(A["c1_summit"] if summit[ij] else A["c1_scene"])
        b = float(bt[ij])
        no_apto = False
        if A["apply_unsuitable_filters"]:
            no_apto = bool(i in (0, H - 1) or j in (0, W - 1) or dn < A["unsuitable_dnti_floor"]
                           or (A["deti"] is not None and A["deti"][ij] < A["unsuitable_deti_floor"])
                           or (A["test1_mask"] is not None and bool(A["test1_mask"][ij])))
        r = {"roi1": "summit" if summit[ij] else "scene", "en_roi": bool(roi[ij]), "dnti": dn, "umbral_dnti": c1,
             "margen_dnti": dn - c1, "bt_k": b, "compuerta_bt_k": compuerta, "margen_bt_k": b - compuerta,
             "no_apto": no_apto}
        r["pasa"] = bool(r["en_roi"] and _fin(dn, b) and dn > c1 and b > compuerta and not no_apto)
        r["replica_ok"] = r["pasa"] == bool(sal[ij])
        out[ij] = r
    return out


def _falla(v):
    return v is None or not (v > 0)


def _tests(ruta, m1p=None, m2p=None, mctx=None, en_disco=None):
    if ruta == "contextual":
        if m2p and not m2p.get("sin_estadistica"):
            return {"dnti_2p": m2p.get("margen_dnti"), "deti_2p": m2p.get("margen_deti")}
        if m1p:
            if m1p.get("sin_estadistica"):
                t = {"sin_estadistica_1p": -1.0, "bt_1p": m1p.get("margen_bt_k")}
            else:
                t = {"dnti_1p": m1p.get("margen_dnti"), "deti_1p": m1p.get("margen_deti"), "bt_1p": m1p.get("margen_bt_k")}
            if not m1p.get("en_roi", True):
                t["fuera_roi"] = -1.0
            return t
        return None
    if ruta == "test1":
        if mctx is None and en_disco is None:
            return None
        t = {}
        if en_disco is not None:
            t["test1_disco"] = 1.0 if en_disco else -1.0
        if mctx:
            t.update(dnti_ctx=mctx.get("margen_dnti"), bt_ctx=mctx.get("margen_bt_k"))
            if mctx.get("no_apto"):
                t["no_apto_ctx"] = -1.0
            if not mctx.get("en_roi", True):
                t["fuera_roi"] = -1.0
        return t
    return None


def limitante(ruta, m1p=None, m2p=None, mctx=None, en_disco=None):
    """Los tests de la ruta publicada que el vecino no pasa, unidos por '+'; 'ninguno' si pasa todos
    (contradicción con no estar incluido: la cuenta C4); 'sin_datos' si no hay márgenes."""
    t = _tests(ruta, m1p, m2p, mctx, en_disco)
    if t is None:
        return "sin_datos"
    return "+".join(sorted(k for k, v in t.items() if _falla(v))) or "ninguno"


def margen_relativo(ruta, m1p=None, m2p=None, mctx=None):
    """El margen más negativo de los tests de índice que fallan, en fracción de su umbral (|umbral|).
    La compuerta de BT se reporta aparte, en K."""
    fuente = {"contextual": (m2p if (m2p and not m2p.get("sin_estadistica")) else m1p), "test1": mctx}.get(ruta)
    if not fuente:
        return None
    rel = []
    for n, u in (("margen_dnti", "umbral_dnti"), ("margen_deti", "umbral_deti")):
        m, um = fuente.get(n), fuente.get(u)
        if m is not None and um not in (None, 0) and math.isfinite(m) and m <= 0:
            rel.append(m / abs(um))
    return min(rel) if rel else None
