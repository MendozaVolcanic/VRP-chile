# -*- coding: utf-8 -*-
"""S162 MOD-D, diagnóstico S-1 (informa, no decide): cuánto depende la decisión de cumbre del código de MIROVA de la
sigma de TODA la grilla de 51 km.

POR QUÉ. En el .m de MIROVA (oráculo `mirova_v750_r2._pasada_contextual`, l. 303-308 y 373-382 del .m) el umbral de
la caja de cumbre es u2 = max(mu + 5 sigma, piso), con mu y sigma del NTI contextual y del ETI contextual calculados
sobre todos los píxeles válidos de la grilla, no sobre la vecindad del cráter. Una nube, una costa o un borde de barrido
a 20 km del volcán sube sigma y apaga la cumbre; un borde limpio la enciende. El verificador de la ablación del bow tie
(MOD-E, S-1) lo vio: todo A/B que cambia el remuestreo (D17, D28) cambia también el borde de la escena y, por esa vía,
el umbral del cráter. Este diagnóstico mide, pasada por pasada, el umbral de cumbre con la sigma de la grilla entera
(el del código) y con la sigma de la caja ROI1 de 15 x 15 km (contrafactual), y cuántos píxeles de cumbre pasan con
cada uno. Es una lectura del mecanismo, no una variante a adoptar.

QUÉ REIMPLEMENTA Y CÓMO SE CONTROLA. Las líneas del oráculo que arman c_nti y c_eti de la primera pasada (preproceso de
`detectar`, l. 101-171 del .m, y `_pasada_contextual`, l. 275-369), copiadas de `mirova_v750_r2.py` (blob 07da7010)
sin cambiar nada, llamando a sus funciones auxiliares. Control de identidad en cada pasada: mu, sigma y los umbrales
globales recalculados aquí tienen que ser los que el oráculo devuelve en su diagnóstico (`identidad_ok`), y los
píxeles de cumbre que pasan con el umbral global tienen que ser los de la máscara de cumbre del oráculo en la primera
pasada. Si no coinciden, la pasada sale con `identidad_ok` falso y el evaluador no la usa.

Las dos preguntas del instrumento:
1. Si la sigma de escena no importara nunca, ¿se vería? Sí: u2 global y u2 ROI1 coincidirían y n2 también; la prueba
   `probar_diagnostico_s1` arma una grilla con un borde ruidoso y exige que u2 global suba y n2 global baje.
2. Si este diagnóstico estuviera muerto, ¿se vería distinto? Sí: sin grilla devuelve `estado` distinto de "ok", y la
   identidad con el oráculo se comprueba en cada pasada.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
import mirova_port as MP  # noqa: E402

ORA = MP.ORA
TOL_IDENTIDAD = 1e-12


def _contextos(nti_roi, bt15, m15, excl, excluidos):
    """c_nti y c_eti de una pasada contextual, copiados de ORA._pasada_contextual (l. 275-369 del .m)."""
    pob = nti_roi.copy()
    pob[excluidos] = np.nan
    fondo_loc = ORA._media_3x3_omitnan(pob)
    fondo_loc[excl] = np.nan
    c_nti = pob - fondo_loc
    with np.errstate(invalid="ignore"):
        c_nti[c_nti < -0.1] = np.nan
    m13_esp = ORA.temperatura_a_radiancia(bt15, ORA.LAMBDA_M13)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti_esp = (m13_esp - m15) / (m13_esp + m15)
    nti_esp[excluidos] = np.nan
    nti_esp[excl] = np.nan
    ok = np.isfinite(nti_esp) & np.isfinite(pob)
    if ok.sum() < 3:
        return c_nti, None
    coef = np.polyfit(nti_esp[ok], pob[ok], 2)
    eti = pob - np.polyval(coef, nti_esp)
    c_eti = eti - ORA._media_3x3_omitnan(eti)
    c_eti[excl] = np.nan
    return c_nti, c_eti


def _umbral(x, sel, s, piso):
    mu, sd = ORA._mean_omitnan(x[sel]), ORA._std_omitnan(x[sel])
    u = max(mu + s * sd, piso) if np.isfinite(mu + s * sd) else piso
    return mu, sd, u


def medir(mir, tir, box, dayflag, sunglint, cfg):
    """Diagnóstico de la primera pasada de una grilla (mir, tir en radiancia, box del port). Nunca lanza: devuelve
    {"estado": ...} con lo que pudo medir."""
    try:
        mask, _l, d = MP.detectar(mir, tir, box, dayflag, sunglint, cfg)
        if d.get("motivo"):
            return {"estado": d["motivo"]}
        if dayflag != 0:
            return {"estado": "diurna"}
        with MP.longitudes(cfg):
            m13 = np.asarray(mir, float)
            m15 = np.array(tir, float)
            b = np.array(box, float)
            b[:, [0, -1]] = np.nan
            b[[0, -1], :] = np.nan
            m2 = b == 2
            excl = np.isnan(b)
            bt15 = ORA.radiancia_a_temperatura(m15, ORA.LAMBDA_M15)
            with np.errstate(invalid="ignore"):
                frio = bt15 <= 200
            bt15[frio] = np.nan
            m15[frio] = np.nan
            with np.errstate(invalid="ignore", divide="ignore"):
                nti = (m13 - m15) / (m13 + m15)
            nti_roi = nti.copy()
            nti_roi[excl] = np.nan
            with np.errstate(invalid="ignore"):
                absol = nti_roi > -0.7
            c_nti, c_eti = _contextos(nti_roi, bt15, m15, excl, absol)
        p1 = d["pasada1"]
        todo = np.ones(c_nti.shape, bool)
        roi1 = np.nan_to_num(b, nan=0) >= 1
        mu_g, sd_g, u2_g = _umbral(c_nti, todo, 5, 0.003)
        out = {"estado": "ok", "sd_nti_g": sd_g, "u_nti2_g": u2_g}
        ident = [abs(mu_g - p1["mu_nti"]) if np.isfinite(mu_g) else 0.0, abs(sd_g - p1["sd_nti"]) if np.isfinite(sd_g)
                 else 0.0, abs(u2_g - p1["u_nti2"])]
        _mu_r, sd_r, u2_r = _umbral(c_nti, roi1, 5, 0.003)
        out.update({"sd_nti_roi1": sd_r, "u_nti2_roi1": u2_r})
        if c_eti is None or "u_eti2" not in p1:
            out["estado"] = "sin_regresion"
            out["identidad_ok"] = max(ident) <= TOL_IDENTIDAD
            return out
        mue_g, sde_g, ue2_g = _umbral(c_eti, todo, 5, 0.003)
        ident += [abs(ue2_g - p1["u_eti2"])]
        _mue_r, sde_r, ue2_r = _umbral(c_eti, roi1, 5, 0.003)
        with np.errstate(invalid="ignore"):
            pasa_g = m2 & (c_nti > u2_g) & (c_eti > ue2_g)
            pasa_r = m2 & (c_nti > u2_r) & (c_eti > ue2_r)
        # identidad de máscaras: la cumbre de la primera pasada del oráculo (a2 de pasada 1) es pasa_g; el oráculo no
        # la devuelve sola, así que se compara contra la máscara final restringida a la cumbre: pasa_g tiene que estar
        # contenida en ella (la final suma absolutos y la segunda pasada).
        contenida = bool(np.all(~pasa_g | mask))
        with np.errstate(invalid="ignore"):
            cn2 = np.where(m2, c_nti, np.nan)
            ce2 = np.where(m2, c_eti, np.nan)
        out.update({"sd_eti_g": sde_g, "u_eti2_g": ue2_g, "sd_eti_roi1": sde_r, "u_eti2_roi1": ue2_r,
                    "n2_g": int(pasa_g.sum()), "n2_roi1": int(pasa_r.sum()),
                    "max_cnti_cumbre": None if np.all(np.isnan(cn2)) else float(np.nanmax(cn2)),
                    "max_ceti_cumbre": None if np.all(np.isnan(ce2)) else float(np.nanmax(ce2)),
                    "cumbre_contenida_en_mascara": contenida,
                    "identidad_max": float(max(ident)),
                    "identidad_ok": bool(max(ident) <= TOL_IDENTIDAD and contenida)})
        return out
    except Exception as e:  # noqa: BLE001  (un diagnóstico nunca tumba la pasada)
        return {"estado": f"error: {type(e).__name__}: {e}"[:300]}


def probar_diagnostico_s1():
    """Sin red. (1) Identidad con el oráculo en una escena sintética de MODIS. (2) Control positivo: con un borde
    ruidoso fuera de la ROI1 la sigma global sube, el umbral global sube y la cumbre pierde píxeles; con la sigma de la
    ROI1 no. Devuelve el par de diagnósticos (sin borde, con borde)."""
    rng = np.random.default_rng(162)
    n = 51
    g = {"ul_x": 0.0, "ul_y": 51000.0, "n": n, "celda": 1000.0}
    X0, Y0 = 25500.0, 25500.0
    cfg = MP.SENSORES["MODIS"]
    box = MP.caja(g, X0, Y0, "fisica")
    T = 265 + rng.normal(0, 0.3, (n, n))
    tir = ORA.temperatura_a_radiancia(T, cfg["lam_tir"])
    mir = ORA.temperatura_a_radiancia(T - 3, cfg["lam_mir"])
    mir[25, 25] *= 1.13
    a = medir(mir, tir, box, 0, 100.0, cfg)
    mir2 = mir.copy()
    borde = np.ones((n, n), bool)
    borde[8:43, 8:43] = False
    mir2[borde] *= 1.0 + np.abs(rng.normal(0, 0.06, borde.sum()))
    b = medir(mir2, tir, box, 0, 100.0, cfg)
    assert a["estado"] == "ok" and a["identidad_ok"], a
    assert b["estado"] == "ok" and b["identidad_ok"], b
    assert a["n2_g"] >= 1, ("sin borde la cumbre tiene que pasar", a)
    assert b["sd_nti_g"] > 2 * a["sd_nti_g"], ("el borde ruidoso tiene que subir la sigma global", a, b)
    assert b["n2_g"] < a["n2_g"], ("con la sigma global la cumbre tiene que perder píxeles", a, b)
    assert b["n2_roi1"] == a["n2_roi1"] == a["n2_g"], ("con la sigma de la ROI1 el borde no tiene que importar", a, b)
    return a, b


if __name__ == "__main__":
    sa, sb = probar_diagnostico_s1()
    print("PRUEBA DIAGNOSTICO S-1 OK", {k: sa[k] for k in ("sd_nti_g", "u_nti2_g", "n2_g", "n2_roi1")},
          {k: sb[k] for k in ("sd_nti_g", "u_nti2_g", "n2_g", "n2_roi1")})
