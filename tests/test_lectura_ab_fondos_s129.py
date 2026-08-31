# -*- coding: utf-8 -*-
"""Tests de la lectura del A/B de fondos (S129), sobre datos sintéticos.

Se escriben antes que el script y antes que el reproceso. Lo que fijan es la
ARITMÉTICA de las cuatro firmas, que es donde aparecen los errores silenciosos:
emparejar sobre la intersección, un par por noche, y la brecha por régimen.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "experiments", "_s129_ab_fondos"))
from lectura import brecha_por_regimen, firmas_de_brazo, pares_intersectados


def _rec(fecha, vrp, tmax, tbg, sensor="VIIRS_SNPP", thr=300.0):
    return {"datetime_utc": fecha + "T05:00:00", "sensor": sensor,
            "primary_cluster": {"vrp_mw": vrp}, "t_max_i04_k": tmax,
            "t_bg_k": tbg, "diag_eff_threshold_k": thr,
            "solar_zenith_deg": 150.0}


def test_un_par_por_noche_toma_el_maximo():
    """Dos pasadas la misma noche cuentan UNA vez, con el mayor VRP."""
    recs = [_rec("2026-03-01", 1.0, 290, 280), _rec("2026-03-01", 3.0, 292, 280)]
    pares = pares_intersectados({"x": recs}, {"x": {("2026-03-01", "v375"): 2.0}},
                                pasadas=None)
    assert len(pares) == 1
    assert pares[0]["nuestro"] == 3.0


def test_interseccion_descarta_noches_que_faltan_en_un_brazo():
    """Sin intersección, un brazo con más pasadas 'detecta más' por procesar más."""
    a = [_rec("2026-03-01", 1.0, 290, 280), _rec("2026-03-02", 1.0, 290, 280)]
    comunes = {p["fecha"] for p in pares_intersectados(
        {"x": a}, {"x": {("2026-03-01", "v375"): 1.0,
                         ("2026-03-02", "v375"): 1.0}},
        pasadas={"2026-03-01"})}
    assert comunes == {"2026-03-01"}


def test_firmas_cuenta_detecciones_y_umbral():
    recs = [_rec("2026-03-01", 1.0, 290, 280, thr=305.0),
            _rec("2026-03-02", 0.0, 285, 280, thr=295.0)]
    f = firmas_de_brazo({"x": recs}, {"x": {("2026-03-01", "v375"): 1.0}},
                        pasadas=None)
    assert f["n_detecciones"] == 1          # sólo el de vrp>0
    assert f["umbral_mediano"] == 300.0     # mediana de 305 y 295


def test_brecha_por_regimen_es_debil_menos_fuerte():
    """F3: ratio del tercil débil menos el del fuerte. Negativa = el débil sufre."""
    pares = [{"ratio": 0.4, "delta_t": 5.0}, {"ratio": 0.5, "delta_t": 6.0},
             {"ratio": 0.6, "delta_t": 10.0}, {"ratio": 0.9, "delta_t": 20.0},
             {"ratio": 1.0, "delta_t": 22.0}, {"ratio": 1.1, "delta_t": 25.0}]
    b = brecha_por_regimen(pares)
    assert b["debil"] < b["fuerte"]
    assert b["brecha"] == round(b["debil"] - b["fuerte"], 3)
    assert b["brecha"] < 0
