"""S135 — el script único de números del paper (`scripts/paper_numbers.py`).

Lo que se fija acá no son los valores (cambian con la data) sino las DEFINICIONES:
denominadores coherentes, buckets según la convención real del repo (A48), Tier A = 11,
y que el markdown y el JSON salgan del mismo cómputo.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("paper_numbers", os.path.join(ROOT, "scripts", "paper_numbers.py"))
pn = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
spec.loader.exec_module(pn)


def test_bucket_sigue_la_convencion_a48():
    assert pn.bucket_of("VIIRS_SNPP") == "VIIRS375"
    assert pn.bucket_of("VIIRS_NOAA21") == "VIIRS375"
    assert pn.bucket_of("VIIRS_NOAA20_750") == "VIIRS750"
    assert pn.bucket_of("MODIS_TERRA") == "MODIS"
    assert pn.bucket_of("OTRO") is None


def test_tier_a_son_los_11_de_radio_25():
    vols, tier_a = pn.load_volcanoes()
    assert len(tier_a) == 11
    assert all(v["radius_km"] == 25 for v in tier_a)


def test_magnitud_operador_usa_f5_en_v375_y_pc_en_el_resto():
    r = {"primary_cluster": {"vrp_mw": 1.0}, "f5_core_vrp_mw": 0.4}
    assert pn.magnitud_operador(r, "VIIRS375") == (0.4, "f5_core_vrp_mw")
    assert pn.magnitud_operador(r, "VIIRS750") == (1.0, "pc.vrp_mw")
    r2 = {"primary_cluster": {"vrp_mw": 1.0}}
    assert pn.magnitud_operador(r2, "VIIRS375") == (1.0, "pc.vrp_mw")


def test_crater_y_dashboard():
    inner = 5
    ok = {"primary_cluster": {"vrp_mw": 0.1, "centroid_dist_km": 1.0}, "distance_class": "summit"}
    far = {"primary_cluster": {"vrp_mw": 0.1, "centroid_dist_km": 1.0}, "distance_class": "far"}
    lejos = {"primary_cluster": {"vrp_mw": 0.1, "centroid_dist_km": 9.0}, "distance_class": "summit"}
    cero = {"primary_cluster": {"vrp_mw": 0.0, "centroid_dist_km": 1.0}}
    assert pn.es_crater(ok, inner) and pn.es_dashboard(ok, inner)
    assert pn.es_crater(far, inner) and not pn.es_dashboard(far, inner)   # A46: cráter pero etiqueta far
    assert not pn.es_crater(lejos, inner) and not pn.es_crater(cero, inner)


def test_tabla4_denominadores_coherentes_en_una_ventana_corta():
    _, tier_a = pn.load_volcanoes()
    t4 = pn.tabla4(tier_a, "2026-08-01", "2026-08-31")
    gt = t4.pop("_ventana_ground_truth")
    assert gt["hasta"] <= "2026-08-31" and gt["fin_csv_mirova"]
    assert len(t4) == 11 * 3
    for x in t4.values():
        assert 0 <= x["tp_dashboard"] <= x["tp_crater"] <= x["noches_alerta_mirova"]
        if x["noches_alerta_mirova"]:
            assert 0 <= x["recall_dashboard"] <= x["recall_crater"] <= 1
        else:
            assert x["recall_dashboard"] is None
        assert x["noches_dashboard_sin_alerta"] <= x["n_noches_dashboard"]
        if x["razon_mediana"] is not None:
            assert x["pares_pasada"] > 0 and x["razon_q25"] <= x["razon_mediana"] <= x["razon_q75"]
    agg = pn.agregados(t4)
    assert sum(a["noches_alerta_mirova"] for a in agg.values()) == sum(x["noches_alerta_mirova"] for x in t4.values())


def test_la_comparacion_no_pasa_del_fin_del_ground_truth():
    """Sin ground truth no hay comparación: una noche nuestra posterior al último dato de
    MIROVA no puede contarse como «detectamos y ella no». El recorte es del script, no del
    que lo llama."""
    _, tier_a = pn.load_volcanoes()
    t4 = pn.tabla4(tier_a, "2026-01-01", "2099-12-31")
    gt = t4["_ventana_ground_truth"]
    assert gt["hasta"] == gt["fin_csv_mirova"] < "2099-12-31"


def test_tabla3_lee_los_coeficientes_del_codigo_y_la_validacion_osf():
    t3 = pn.tabla3()
    for s in ("MODIS_1000m", "VIIRS_750m", "VIIRS_375m"):
        assert t3["sensores"][s]["coef_codigo"], s
        assert t3["sensores"][s]["a_pix_mode"] == "nadir_fijo"
        assert t3["sensores"][s]["matched_error_pct"] < 0.2
