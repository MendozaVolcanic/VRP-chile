# -*- coding: utf-8 -*-
"""Guard de experiments/_s151_ab_diurno/unir_intentos.py (decision D-13: los A/B largos se repiten y se unen).

Por que: la version de la vuelta 68 comparaba los records comunes con `!=` y en el re-run del A/B F/K V2a
(run 38648773684, mismo commit en los dos intentos) se negaba a unir 8 de 22 archivos por el ultimo bit de
np.polyfit (OpenBLAS cambia de kernel segun la CPU) y por un pixel en el borde del umbral. Este guard fija los
dos lados (A116): cada estado de la comparacion tiene un caso que lo produce, y los casos que deben bloquear
bloquean.
"""
import ast
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA = RAIZ / "experiments" / "_s151_ab_diurno" / "unir_intentos.py"
spec = importlib.util.spec_from_file_location("unir_intentos", RUTA)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)

HAY_NODE = shutil.which("node") is not None


def rec_modis(**cambios):
    """Record MODIS 'far' de campo difuso, con la forma de los del control de V2a."""
    r = {
        "sensor": "MODIS_TERRA", "datetime_utc": "2026-03-17 02:10", "granule": "MOD021KM.A2026076.0210.061.x.hdf",
        "product_version": "standard", "processed_utc": "2026-10-16T03:00:00Z", "first_processed_utc": "x",
        "distance_class": "far", "vrp_mw": 5.0, "vrp_mir_mw": 48.2, "vrp_vent_mw": 0.0, "t_max_k": 281.4,
        "triggered_test1": False, "discarded_reason": None, "n_anomalous_pixels": 326, "f5_core_vrp_mw": None,
        "final_hotspot_source": "pixel", "sensor_zenith_deg": 31.2, "diag_mu_deti": 0.0123,
        "diag_sd_deti": 0.0071, "diag_n_eti_path": 4,
        "primary_cluster": {"n_pixels": 78, "vrp_mw": 5.0, "centroid_lat": -37.9, "centroid_lon": -71.1,
                            "centroid_dist_km": 14.2, "d9_capped": True},
        "anomaly_pixels": [{"lat": -37.90 - 0.01 * i, "lon": -71.10, "vrp_mw": 0.1 + 0.01 * i, "bt_k": 280.0}
                           for i in range(5)],
        "discarded_anomaly_pixels": [], "discarded_n_pixels": 0,
    }
    r.update(cambios)
    return r


def doc(*recs):
    return {"volcano": "Copahue", "updated": "x", "records": list(recs)}


def unir(*docs):
    return ui.unir([copy.deepcopy(d) for d in docs], "Copahue")


def test_tolerancias_son_las_del_g3_del_evaluador_diurno():
    """Misma tolerancia que G3 (#833), leida del codigo con ast, no por subcadena (A92)."""
    arbol = ast.parse((RAIZ / "experiments" / "_s151_ab_diurno" / "evaluar_diurno.py").read_text(encoding="utf-8"))
    for n in arbol.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and \
                [t.id for t in n.targets[0].elts] == ["G3_REL_TOL", "G3_ABS_TOL"]:
            assert ast.literal_eval(n.value) == (ui.REL_TOL, ui.ABS_TOL)
            return
    pytest.fail("evaluar_diurno.py ya no define G3_REL_TOL, G3_ABS_TOL")


def test_identicos_unen():
    salida, inf = unir(doc(rec_modis()), doc(rec_modis()))
    assert inf["ok"] and inf["comunes"] == 1 and inf["estados"]["igual"] == 1


def test_ruido_5e10_relativo_une():
    b = rec_modis(diag_mu_deti=0.0123 * (1 + 5e-10))
    assert ui.iguales(0.0123, 0.0123 * (1 + 5e-10))
    salida, inf = unir(doc(rec_modis()), doc(b))
    assert inf["ok"] and inf["estados"]["tolerancia"] == 1


def test_ruido_1e3_relativo_no_une():
    b = rec_modis(diag_mu_deti=0.0123 * (1 + 1e-3))
    salida, inf = unir(doc(rec_modis()), doc(b))
    assert not inf["ok"] and salida is None
    assert inf["estados"]["distinto"] == 1
    assert "diag_mu_deti" in inf["distintos"][0]["campos"]


def test_entero_distinto_no_une():
    salida, inf = unir(doc(rec_modis()), doc(rec_modis(diag_n_eti_path=5)))
    assert not inf["ok"]


def test_pixeles_reordenados_unen():
    a = rec_modis()
    b = rec_modis(anomaly_pixels=list(reversed(a["anomaly_pixels"])))
    salida, inf = unir(doc(a), doc(b))
    assert inf["ok"] and inf["estados"]["orden"] == 1 and inf["borde"] == []


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_pixel_de_borde_con_decision_igual_une_e_informa():
    a = rec_modis()
    extra = {"lat": -37.99, "lon": -71.12, "vrp_mw": 0.05, "bt_k": 279.0}
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"] + [extra], vrp_mir_mw=48.2,
                  hotspot_lat=-37.99, discarded_anomaly_pixels=[extra], discarded_n_pixels=1)
    a["hotspot_lat"] = -37.90
    salida, inf = unir(doc(a), doc(b))
    assert inf["ok"] and inf["estados"]["borde"] == 1
    (x,) = inf["borde"]
    assert x["pixeles"]["anomaly_pixels"] == [5, 6]
    assert "hotspot_lat" in x["campos_derivados"]
    # se conserva el record del primer intento
    assert len(salida["records"][0]["anomaly_pixels"]) == 5
    assert salida["_union_intentos"]["borde"] == inf["borde"]


@pytest.mark.parametrize("campo, valor", [("vrp_mw", 4.0), ("distance_class", "summit"),
                                          ("sensor_zenith_deg", 31.9), ("n_anomalous_pixels", 327),
                                          ("primary_cluster", {"n_pixels": 77, "vrp_mw": 5.0,
                                                               "centroid_lat": -37.9, "centroid_lon": -71.1,
                                                               "centroid_dist_km": 14.2, "d9_capped": True})])
def test_pixel_de_borde_con_decision_distinta_no_une(campo, valor):
    a = rec_modis()
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"][:-1], **{campo: valor})
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and inf["estados"]["distinto"] == 1
    assert campo in inf["distintos"][0]["campos"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_pixel_de_borde_mueve_vrp_mir_mw_con_cumulo_une():
    """Con primary_cluster el predicado no lee vrp_mir_mw (frontend/index.html:1148-1149): es derivado."""
    a = rec_modis()
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"][:-1], vrp_mir_mw=49.5)
    salida, inf = unir(doc(a), doc(b))
    assert inf["ok"] and inf["borde"][0]["campos_derivados"] == ["vrp_mir_mw"]


def test_pixel_de_borde_mueve_vrp_mir_mw_sin_cumulo_no_une():
    """Sin primary_cluster ni vrp_mw, vrp_mir_mw es la magnitud que publica el tablero."""
    a = rec_modis(primary_cluster=None, vrp_mw=None)
    b = rec_modis(primary_cluster=None, vrp_mw=None, anomaly_pixels=a["anomaly_pixels"][:-1], vrp_mir_mw=49.5)
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and "vrp_mir_mw" in inf["distintos"][0]["campos"]


def test_pixel_de_borde_con_campo_no_derivado_distinto_no_une():
    a = rec_modis()
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"][:-1], diag_n_eti_path=7)
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and "diag_n_eti_path" in inf["distintos"][0]["campos"]


def test_pixel_de_borde_en_viirs375_sin_nucleo_no_une():
    """En VIIRS 375 sin f5_core_vrp_mw el tablero recalcula la magnitud desde anomaly_pixels
    (frontend/index.html:1238-1239 y 1289), asi que los pixeles deciden."""
    a = rec_modis(sensor="VIIRS_SNPP")
    b = rec_modis(sensor="VIIRS_SNPP", anomaly_pixels=a["anomaly_pixels"][:-1])
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and "anomaly_pixels" in inf["distintos"][0]["campos"]


def test_conserva_el_primer_intento_y_agrega_los_que_faltan():
    a = rec_modis(processed_utc="INTENTO1")
    b = rec_modis(processed_utc="INTENTO2", diag_mu_deti=0.0123 * (1 + 5e-10))
    solo2 = rec_modis(datetime_utc="2026-03-18 02:10", granule="otro.hdf")
    salida, inf = unir(doc(a), doc(b, solo2))
    assert inf["ok"] and len(salida["records"]) == 2
    assert salida["records"][0]["processed_utc"] == "INTENTO1"
    assert inf["por_intento"] == [1, 2] and inf["nuevos_por_intento"] == [1, 1]


B = Path(r"C:/Users/nmend/AppData/Local/Temp/claude/v2a_38648773684")
CHAITEN = (B / "i1/experiments/_s146_ab_sin_test1/salidas/38648773684/_s146_ab_control/Chaiten.json",
           B / "i2/_s146_ab_control/Chaiten.json")


@pytest.mark.skipif(not all(p.exists() for p in CHAITEN), reason="salidas de V2a (run 38648773684) no estan en disco")
def test_real_chaiten_control_v2a_une():
    """Los dos intentos de Chaiten control de V2a (mismo commit) se negaban a unir con la version de la
    vuelta 68: 574 de 590 comunes difieren, 570 sólo por floats bajo la tolerancia y 4 además por el orden de
    anomaly_pixels; ninguno por pixel de borde."""
    docs = [json.loads(p.read_text(encoding="utf-8")) for p in CHAITEN]
    salida, inf = ui.unir(docs, "Chaiten")
    assert inf["ok"], inf["distintos"][:3]
    assert inf["comunes"] == 590 and inf["estados"]["distinto"] == 0
    assert inf["estados"] == {"igual": 16, "tolerancia": 570, "orden": 4, "borde": 0, "distinto": 0}
    assert inf["borde"] == [] and inf["nuevos_por_intento"] == [590, 11]
    assert len(salida["records"]) == 601


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_el_predicado_puede_dar_distinto():
    """El chequeo (d) no es decorativo: con un record summit publicado y el mismo far, node da distinto."""
    pc = {"n_pixels": 2, "vrp_mw": 0.4, "centroid_lat": -37.85, "centroid_lon": -71.16, "centroid_dist_km": 1.0}
    a = rec_modis(distance_class="summit", vrp_mw=0.4, primary_cluster=pc)
    b = rec_modis(distance_class="far", vrp_mw=0.4, primary_cluster=pc)
    assert ui._predicado([(a, a), (a, b)], "Copahue") == [1]


def test_sin_predicado_un_record_de_borde_no_une(monkeypatch):
    def roto(pares, volcan):
        raise RuntimeError("sin node")
    monkeypatch.setattr(ui, "_predicado", roto)
    a = rec_modis()
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"][:-1])
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and inf["distintos"][0]["campos"] == ["predicado del tablero"]
    assert "sin node" in inf["distintos"][0]["predicado"]
