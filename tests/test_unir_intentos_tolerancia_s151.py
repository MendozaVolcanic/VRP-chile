# -*- coding: utf-8 -*-
"""Guard de experiments/_s151_ab_diurno/unir_intentos.py (decision D-13: los A/B largos se repiten y se unen).

Por que: la version de la vuelta 68 comparaba los records comunes con `!=` y en el re-run del A/B F/K V2a
(run 38648773684, mismo commit en los dos intentos) se negaba a unir 8 de 22 archivos por el ultimo bit de
np.polyfit (OpenBLAS cambia de kernel segun la CPU) y por empates en el recorte TOP-100 de la lista de pixeles
(`np.argsort` no estable en pipeline/process_modis.py:1085: ningun pixel cruza un umbral, la mascara de deteccion
es la misma). Ademas la clave llevaba el granulo, y la misma pasada con otro granulo salia dos veces (verificador
del PR #841). Este guard fija los dos lados (A116): cada estado de la comparacion tiene un caso que lo produce, los
casos que deben bloquear bloquean, y cada mutacion que sobrevivia al verificador tiene un test que la mata.
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
        # el ultimo guardado empata con el minimo de la lista (0,05, el de los descartados): es el que un desempate
        # en el puesto 100 puede cambiar (verificador V2 del PR #847)
        "anomaly_pixels": [{"lat": -37.90 - 0.01 * i, "lon": -71.10, "vrp_mw": 0.1 + 0.01 * i if i < 4 else 0.05,
                            "bt_k": 280.0} for i in range(5)],
        # La lista guardada viene del recorte top-100 (pipeline/process_modis.py:1085) y store la reparte por
        # distancia: 5 dentro y 95 descartados suman los 100 del recorte, que es donde el empate puede actuar.
        "discarded_anomaly_pixels": [{"lat": -38.30 - 0.001 * i, "lon": -71.40, "vrp_mw": 0.05, "bt_k": 278.0}
                                     for i in range(95)], "discarded_n_pixels": 95,
    }
    r.update(cambios)
    return r


def empate(a):
    """El ultimo pixel guardado sale y entra otro del mismo VRP: lo que deja un desempate distinto en el corte."""
    ultimo = a["anomaly_pixels"][-1]
    return a["anomaly_pixels"][:-1] + [dict(ultimo, lat=ultimo["lat"] - 0.005)]


SOLO1 = rec_modis(datetime_utc="2026-03-01 02:10", granule="solo1.hdf")
SOLO2 = rec_modis(datetime_utc="2026-03-02 02:10", granule="solo2.hdf")


def doc(*recs):
    return {"volcano": "Copahue", "updated": "x", "records": list(recs)}


def unir(*docs):
    return ui.unir([copy.deepcopy(d) for d in docs], "Copahue")


def mezcla(a, b):
    """Dos intentos con el record comun a/b y una pasada propia cada uno: ninguno cubre la union, asi que la
    herramienta TIENE que mezclar record a record (y aplicar la regla estricta)."""
    salida, inf = unir(doc(SOLO1, a), doc(b, SOLO2))
    assert inf["modo"] == "mezcla"
    return salida, inf


def test_tolerancias_son_las_del_g3_del_evaluador_diurno():
    """Misma tolerancia que G3 (#833), leida del codigo con ast, no por subcadena (A92)."""
    arbol = ast.parse((RAIZ / "experiments" / "_s151_ab_diurno" / "evaluar_diurno.py").read_text(encoding="utf-8"))
    for n in arbol.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and \
                [t.id for t in n.targets[0].elts] == ["G3_REL_TOL", "G3_ABS_TOL"]:
            assert ast.literal_eval(n.value) == (ui.REL_TOL, ui.ABS_TOL)
            return
    pytest.fail("evaluar_diurno.py ya no define G3_REL_TOL, G3_ABS_TOL")


# ---------------------------------------------------------------- comparacion elemental
def test_bool_no_es_entero():
    assert not ui.iguales(True, 1) and not ui.iguales(False, 0) and ui.iguales(True, True)


def test_multiconjunto_no_reutiliza_elementos():
    p, q = {"lat": 1.0, "vrp_mw": 0.5}, {"lat": 2.0, "vrp_mw": 0.5}
    assert ui.mismo_multiconjunto([p, q], [q, p])
    assert not ui.mismo_multiconjunto([p, p], [p, q])


def test_identicos_unen():
    salida, inf = mezcla(rec_modis(), rec_modis())
    assert inf["ok"] and inf["comunes"] == 1 and inf["estados"]["igual"] == 1


def test_ruido_5e10_relativo_une():
    b = rec_modis(diag_mu_deti=0.0123 * (1 + 5e-10))
    assert ui.iguales(0.0123, 0.0123 * (1 + 5e-10))
    salida, inf = mezcla(rec_modis(), b)
    assert inf["ok"] and inf["estados"]["tolerancia"] == 1


def test_ruido_1e3_relativo_no_une():
    b = rec_modis(diag_mu_deti=0.0123 * (1 + 1e-3))
    salida, inf = mezcla(rec_modis(), b)
    assert not inf["ok"] and salida is None
    assert inf["estados"]["distinto"] == 1
    assert "diag_mu_deti" in inf["distintos"][0]["campos"]


def test_piso_absoluto_une_valores_casi_cero():
    """mu del dETI casi cero: 1e-13 contra 1e-13 + 5e-15 es 5 % relativo pero 5e-15 absoluto. Pasa sólo por el
    piso ABS_TOL = 1e-14 (mata la mutacion «quitar abs_tol»)."""
    a, b = rec_modis(diag_mu_deti=1e-13), rec_modis(diag_mu_deti=1e-13 + 5e-15)
    salida, inf = mezcla(a, b)
    assert inf["ok"] and inf["estados"]["tolerancia"] == 1


def test_ausente_contra_none_no_une():
    a = rec_modis(vrp_vent_mw=None)
    b = rec_modis()
    del b["vrp_vent_mw"]
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and "vrp_vent_mw" in inf["distintos"][0]["campos"]


def test_entero_distinto_no_une():
    salida, inf = mezcla(rec_modis(), rec_modis(diag_n_eti_path=5))
    assert not inf["ok"]


def test_pixeles_reordenados_unen():
    a = rec_modis()
    b = rec_modis(anomaly_pixels=list(reversed(a["anomaly_pixels"])))
    salida, inf = mezcla(a, b)
    assert inf["ok"] and inf["estados"]["orden"] == 1 and inf["borde"] == []


# ---------------------------------------------------------------- empates del recorte («borde»)
@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_pixel_de_borde_con_decision_igual_une_e_informa():
    a = rec_modis()
    extra = {"lat": -37.99, "lon": -71.12, "vrp_mw": 0.05, "bt_k": 279.0}
    b = rec_modis(anomaly_pixels=a["anomaly_pixels"] + [extra], vrp_mir_mw=48.2,
                  hotspot_lat=-37.99, discarded_anomaly_pixels=a["discarded_anomaly_pixels"][:-1],
                  discarded_n_pixels=94)
    a["hotspot_lat"] = -37.90
    salida, inf = mezcla(a, b)
    assert inf["ok"] and inf["estados"]["borde"] == 1
    (x,) = inf["borde"]
    assert x["pixeles"]["anomaly_pixels"] == [5, 6]
    assert "hotspot_lat" in x["campos_derivados"]
    # se conserva el record del primer intento
    comun = [r for r in salida["records"] if r["datetime_utc"] == a["datetime_utc"]]
    assert len(comun) == 1 and len(comun[0]["anomaly_pixels"]) == 5
    assert salida["_union_intentos"]["borde"] == inf["borde"]


@pytest.mark.parametrize("campo, valor", [("vrp_mw", 4.0), ("distance_class", "summit"),
                                          ("n_anomalous_pixels", 327), ("triggered_test1", True),
                                          ("primary_cluster", {"n_pixels": 77, "vrp_mw": 5.0,
                                                               "centroid_lat": -37.9, "centroid_lon": -71.1,
                                                               "centroid_dist_km": 14.2, "d9_capped": True})])
def test_pixel_de_borde_con_decision_distinta_no_une(campo, valor):
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a), **{campo: valor})
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and inf["estados"]["distinto"] == 1
    assert campo in inf["distintos"][0]["campos"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_pixel_de_borde_mueve_vrp_mir_mw_con_cumulo_une():
    """Con primary_cluster el predicado no lee vrp_mir_mw (frontend/index.html:1148-1149): es derivado."""
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a), vrp_mir_mw=49.5)
    salida, inf = mezcla(a, b)
    assert inf["ok"] and inf["borde"][0]["campos_derivados"] == ["vrp_mir_mw"]


def test_pixel_de_borde_mueve_vrp_mir_mw_sin_cumulo_no_une():
    """Sin primary_cluster ni vrp_mw, vrp_mir_mw es la magnitud que publica el tablero."""
    a = rec_modis(primary_cluster=None, vrp_mw=None)
    b = rec_modis(primary_cluster=None, vrp_mw=None, anomaly_pixels=empate(a), vrp_mir_mw=49.5)
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and "vrp_mir_mw" in inf["distintos"][0]["campos"]


def test_pixel_de_borde_con_campo_no_derivado_distinto_no_une():
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a), diag_n_eti_path=7)
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and "diag_n_eti_path" in inf["distintos"][0]["campos"]


def test_lista_de_100_sin_recorte_no_une():
    """Verificador V2 del PR #847: con exactamente 100 pixeles detectados la lista tambien mide 100, pero el recorte
    no corto nada (n_anomalous_pixels = 100). Un pixel distinto ahi es otra deteccion."""
    a = rec_modis(n_anomalous_pixels=100)
    b = rec_modis(n_anomalous_pixels=100, anomaly_pixels=empate(a))
    est, det = ui.comparar(a, b)
    assert est == "distinto" and det["sin_recorte"] == [100, 100] and det["n_anomalous_pixels"] == [100, 100]


def test_pixel_cambiado_fuera_del_corte_no_une():
    """Verificador V2 del PR #847: un desempate en el puesto 100 solo cambia pixeles del VRP minimo de la lista.
    Cambiar el mas caliente, con la lista llena y todo lo demas igual, es otra deteccion."""
    a = rec_modis()
    caliente = max(a["anomaly_pixels"], key=lambda p: p["vrp_mw"])
    otros = [p for p in a["anomaly_pixels"] if p is not caliente]
    b = rec_modis(anomaly_pixels=otros + [dict(caliente, lat=caliente["lat"] - 0.005)])
    est, det = ui.comparar(a, b)
    assert est == "distinto" and det.get("fuera_del_corte") is True
    assert ui.comparar(a, rec_modis(anomaly_pixels=empate(a)))[0] == "borde"   # control: el del puesto 100 si


def test_conjunto_distinto_con_lista_corta_no_une():
    """Verificador del PR #847: con menos de 100 pixeles el recorte top-100 no corta nada, asi que un conjunto
    distinto no puede venir del desempate. Es un cambio de deteccion y bloquea, aunque todo lo demas sea igual."""
    a = rec_modis(discarded_anomaly_pixels=[], discarded_n_pixels=0)
    b = rec_modis(discarded_anomaly_pixels=[], discarded_n_pixels=0, anomaly_pixels=empate(a))
    est, det = ui.comparar(a, b)
    assert est == "distinto" and det["sin_recorte"] == [5, 5] and "anomaly_pixels" in det["campos"]
    salida, inf = mezcla(a, b)
    assert not inf["ok"]


@pytest.mark.parametrize("lado", [0, 1])
def test_conjunto_distinto_con_lista_llena_en_un_solo_lado_no_une(lado):
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a), discarded_anomaly_pixels=a["discarded_anomaly_pixels"][:-1])
    x, y = (a, b) if lado == 0 else (b, a)
    assert ui.comparar(x, y)[0] == "distinto"


def test_conjunto_distinto_con_lista_corta_en_viirs_no_une():
    """El caso sembrado por el verificador del PR #847: VIIRS 375 con nucleo y 4 pixeles, uno desplazado y
    vrp_mir_mw x 1,3. El tablero no lee los pixeles, pero el recorte no pudo actuar."""
    v = dict(sensor="VIIRS_NOAA20", f5_core_vrp_mw=0.3, discarded_anomaly_pixels=[], discarded_n_pixels=0)
    a = rec_modis(**v)
    b = rec_modis(anomaly_pixels=empate(a), vrp_mir_mw=48.2 * 1.3, **v)
    assert ui.comparar(a, b)[0] == "distinto"


def test_orden_con_lista_corta_sigue_uniendo():
    """Un orden distinto con el mismo conjunto no es un cambio de deteccion (el sort no es estable en ningun largo)."""
    a = rec_modis(discarded_anomaly_pixels=[], discarded_n_pixels=0)
    b = rec_modis(discarded_anomaly_pixels=[], discarded_n_pixels=0, anomaly_pixels=list(reversed(a["anomaly_pixels"])))
    assert ui.comparar(a, b)[0] == "orden"


def test_pixel_de_borde_en_viirs375_sin_nucleo_no_une():
    """En VIIRS 375 sin f5_core_vrp_mw el tablero recalcula la magnitud desde anomaly_pixels
    (frontend/index.html:1238-1239 y 1289), asi que los pixeles deciden."""
    a = rec_modis(sensor="VIIRS_SNPP")
    b = rec_modis(sensor="VIIRS_SNPP", anomaly_pixels=empate(a))
    salida, inf = unir(doc(dict(SOLO1, sensor="VIIRS_SNPP"), a), doc(b, dict(SOLO2, sensor="VIIRS_SNPP")))
    assert inf["modo"] == "mezcla"
    assert not inf["ok"] and "anomaly_pixels" in inf["distintos"][0]["campos"]


# ---------------------------------------------------------------- la red de seguridad del predicado
@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_el_predicado_puede_dar_distinto():
    """El chequeo (d) no es decorativo: con un record summit publicado y el mismo far, node da distinto."""
    pc = {"n_pixels": 2, "vrp_mw": 0.4, "centroid_lat": -37.85, "centroid_lon": -71.16, "centroid_dist_km": 1.0}
    a = rec_modis(distance_class="summit", vrp_mw=0.4, primary_cluster=pc)
    b = rec_modis(distance_class="far", vrp_mw=0.4, primary_cluster=pc)
    assert ui._predicado([(a, a), (a, b)], "Copahue") == [1]


def test_si_el_predicado_da_distinto_no_une(monkeypatch):
    """Mata la mutacion «ignorar el resultado del predicado» (malos = [])."""
    monkeypatch.setattr(ui, "_predicado", lambda pares, volcan: [0])
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a))
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and salida is None
    assert inf["distintos"][0]["campos"] == ["predicado del tablero"]
    assert inf["estados"]["borde"] == 0 and inf["estados"]["distinto"] == 1


def test_sin_predicado_un_record_de_borde_no_une(monkeypatch):
    def roto(pares, volcan):
        raise RuntimeError("sin node")
    monkeypatch.setattr(ui, "_predicado", roto)
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a))
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and inf["distintos"][0]["campos"] == ["predicado del tablero"]
    assert "sin node" in inf["distintos"][0]["predicado"]



# ---------------------------------------------------------------- la clave es la pasada, no el granulo
def test_misma_pasada_otro_granulo_bloquea_aunque_haya_intento_entero():
    """Verificador del PR #841, a6: con el granulo en la clave esto daba ok y 2 records de la misma pasada, y
    armar_tabla.py:43 se quedaba en silencio con el del intento 2 (mata «granule en la clave»). Y vuelta 2, a9:
    otro granulo u otra version en un comun es A108 (repetir el job), no se elige en silencio aunque los dos
    intentos cubran todo."""
    a = rec_modis()
    b = rec_modis(granule="MOD021KM.NRT.otro.hdf", product_version="nrt", vrp_mw=99.0)
    salida, inf = unir(doc(a), doc(b))
    assert not inf["ok"] and salida is None
    assert inf["comunes"] == 1 and inf["estados"]["distinto"] == 1
    assert {"granule", "product_version", "vrp_mw"} <= set(inf["distintos"][0]["campos"])


def test_misma_pasada_otro_granulo_bloquea_la_mezcla():
    a = rec_modis()
    b = rec_modis(granule="MOD021KM.NRT.otro.hdf", product_version="nrt")
    salida, inf = mezcla(a, b)
    assert not inf["ok"] and {"granule", "product_version"} <= set(inf["distintos"][0]["campos"])


# ---------------------------------------------------------------- intento entero: misma regla que la mezcla
@pytest.mark.parametrize("campo, valor", [("triggered_test1", True), ("distance_class", "summit"),
                                          ("vrp_mw", 99.0), ("product_version", "nrt")])
def test_intento_entero_bloquea_una_diferencia_real(campo, valor):
    """Vuelta 2 del verificador (v2_a9): con un intento que cubre todo, una diferencia de decision en un comun
    daba ok y sólo quedaba informada, y evaluar_fk.py no lee _union_intentos. Ahora bloquea igual que la mezcla."""
    a = rec_modis()
    b = rec_modis(**{campo: valor})
    salida, inf = unir(doc(a), doc(b, SOLO2))
    assert not inf["ok"] and salida is None
    assert campo in inf["distintos"][0]["campos"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_intento_que_cubre_todo_se_usa_entero_con_el_empate_como_borde():
    """Los dos residuales de V2a: el empate en el maximo mueve sensor_zenith_deg. En MODIS es derivado (su único
    lector en la cadena, banco_paridad.py:464-469, filtra VIIRS 375), así que es borde, pasa el predicado y se
    entrega el intento que cubre todo, entero."""
    a = rec_modis(processed_utc="INTENTO1")
    b = rec_modis(processed_utc="INTENTO2", anomaly_pixels=empate(a), sensor_zenith_deg=31.9)
    salida, inf = unir(doc(a), doc(b, SOLO2))
    assert inf["ok"] and inf["modo"] == "intento_entero" and inf["intento_entero"] == 2
    assert salida["records"] == doc(b, SOLO2)["records"]
    assert inf["estados"]["borde"] == 1 and inf["estados"]["distinto"] == 0
    assert "sensor_zenith_deg" in inf["borde"][0]["campos_derivados"]


def test_intento_entero_corre_el_predicado_sobre_el_borde(monkeypatch):
    monkeypatch.setattr(ui, "_predicado", lambda pares, volcan: [0])
    a = rec_modis()
    b = rec_modis(anomaly_pixels=empate(a))
    salida, inf = unir(doc(a), doc(b, SOLO2))
    assert not inf["ok"] and inf["distintos"][0]["campos"] == ["predicado del tablero"]


def test_cenit_en_viirs375_sigue_decidiendo():
    """En VIIRS 375 sensor_zenith_deg arma la zona del barrido (banco_paridad.py:464-469): un empate que lo mueve
    bloquea, aunque el núcleo esté guardado y el tablero no lea los píxeles."""
    v = dict(sensor="VIIRS_SNPP", f5_core_vrp_mw=0.3)
    a = rec_modis(**v)
    b = rec_modis(anomaly_pixels=empate(a), sensor_zenith_deg=31.9, **v)
    salida, inf = unir(doc(dict(SOLO1, **v), a), doc(b, dict(SOLO2, **v)))
    assert not inf["ok"] and "sensor_zenith_deg" in inf["distintos"][0]["campos"]


def test_intento_con_pasada_duplicada_no_se_usa_entero():
    """Mata la mutacion «quitar el chequeo de duplicados del modo entero»: un intento con la misma pasada dos
    veces no es una corrida limpia (store.py:650-653 deduplica por esa clave), así que no se entrega entero."""
    a = rec_modis(processed_utc="INTENTO1")
    salida, inf = unir(doc(a, copy.deepcopy(a)), doc(rec_modis(processed_utc="INTENTO2")))
    assert inf["ok"] and inf["intento_entero"] == 2 and len(salida["records"]) == 1


def test_con_dos_intentos_completos_gana_el_primero():
    a = rec_modis(processed_utc="INTENTO1")
    b = rec_modis(processed_utc="INTENTO2", diag_mu_deti=0.0123 * (1 + 5e-10))
    salida, inf = unir(doc(a), doc(b))
    assert inf["intento_entero"] == 1 and salida["records"][0]["processed_utc"] == "INTENTO1"


def test_mezcla_conserva_el_primer_intento_y_agrega_los_que_faltan():
    a = rec_modis(processed_utc="INTENTO1")
    b = rec_modis(processed_utc="INTENTO2", diag_mu_deti=0.0123 * (1 + 5e-10))
    salida, inf = mezcla(a, b)
    assert inf["ok"] and len(salida["records"]) == 3
    comun = [r for r in salida["records"] if r["datetime_utc"] == a["datetime_utc"]]
    assert comun[0]["processed_utc"] == "INTENTO1"
    assert inf["por_intento"] == [2, 2] and inf["nuevos_por_intento"] == [2, 1]


# ---------------------------------------------------------------- datos reales de V2a
B = Path(r"C:/Users/nmend/AppData/Local/Temp/claude/v2a_38648773684")
I1 = B / "i1/experiments/_s146_ab_sin_test1/salidas/38648773684"
I2 = B


def _par(brazo, vol):
    return (I1 / brazo / (vol + ".json"), I2 / "i2" / brazo / (vol + ".json"))


def _docs(vol):
    rutas = _par("_s146_ab_control", vol)
    if not all(p.exists() for p in rutas):
        pytest.skip("salidas de V2a (run 38648773684) no estan en disco")
    return [json.loads(p.read_text(encoding="utf-8")) for p in rutas]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
@pytest.mark.parametrize("vol, entero, n, borde", [
    ("Chaiten", 2, 601, 0),           # i2 cubre la union; 570 tolerancia + 4 orden
    ("Isluga", 1, 457, 3),            # residual: el empate en el maximo es borde, predicado igual
    ("NevadosDeChillan", 2, 550, 5),  # residual: idem
])
def test_real_control_v2a(vol, entero, n, borde):
    salida, inf = ui.unir(_docs(vol), vol)
    assert inf["ok"] and inf["modo"] == "intento_entero" and inf["intento_entero"] == entero
    assert len(salida["records"]) == n == inf["union"]
    assert inf["estados"]["borde"] == borde and inf["estados"]["distinto"] == 0


@pytest.mark.parametrize("campo", ["triggered_test1", "distance_class", "vrp_mw", "product_version"])
def test_real_lascar_con_un_comun_cambiado_no_une(campo):
    """v2_a9 del verificador sobre datos reales: Láscar control, un comun del intento que cubre todo cambiado."""
    docs = _docs("Lascar")
    r = docs[1]["records"][0]
    r[campo] = {"triggered_test1": not r.get("triggered_test1"), "distance_class": "summit",
                "vrp_mw": 99.0, "product_version": "nrt"}[campo]
    salida, inf = ui.unir(docs, "Lascar")
    assert not inf["ok"] and salida is None and campo in inf["distintos"][0]["campos"]
