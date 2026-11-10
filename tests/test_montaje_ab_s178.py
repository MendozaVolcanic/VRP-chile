# -*- coding: utf-8 -*-
"""S178: comparadores de C-montaje por A/B (experiments/_s172_retro_paquete/montaje_ab.py), declaración aprobada por
Nicolás (opción A) en experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md de loop/activo, commit c592ac2d2.

POR QUÉ. C-montaje decide si se puede leer la retrospectiva: si un comparador no pudiera ver una celda distinta, un VRP
fuera de tolerancia o una pasada faltante, daría verde a una vía distinta de la medida. Cada prueba arma una pasada
donde la respuesta se sabe y la exige. Las mutaciones del módulo viven en mutar_montaje_ab.py (control de caída).
"""
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_RUTA = Path(os.environ.get("MONTAJE_AB_MODULO") or ROOT / "experiments" / "_s172_retro_paquete" / "montaje_ab.py")
_spec = importlib.util.spec_from_file_location("montaje_ab_bajo_prueba", _RUTA)
M = importlib.util.module_from_spec(_spec)
sys.modules["montaje_ab_bajo_prueba"] = M
_spec.loader.exec_module(M)

G750 = "VJ102MOD.A2026278.0518.021.2026278103120.nc"
G375 = "VJ102IMG.A2026278.0518.021.2026278103120.nc"
GMOD = "MOD021KM.A2026278.0150.061.2026278131414.hdf"


def rec_viirs(sensor, gran, vrp, celdas, dt="2026-10-05 05:18"):
    pix = [{"fila": f, "col": c, "lat": 0.0, "lon": 0.0} for f, c in celdas]
    return {"sensor": sensor, "datetime_utc": dt, "granule": gran, "via_codigo_mirova": True,
            "primary_cluster": {"vrp_mw": vrp} if celdas else None, "anomaly_pixels": pix,
            "distance_class": "summit" if celdas else None}


def via(vol, rec):
    return M.indexar_via({(vol, rec["sensor"], rec["datetime_utc"]): rec})


def e750(vol, vrp, celdas, banda=None, gran=G750, hora="2026-10-05 05:18", brazo=None):
    o = {"vrp_mw": vrp, "pixeles": [[f, c, 2, 1.0, 0.1] for f, c in celdas], "vrp_banda": banda, "npix": len(celdas)}
    otro = {"vrp_mw": 99.0, "pixeles": [[0, 0, 0, 0, 0]], "vrp_banda": None}
    brazo = brazo or M.brazo_b4(vol)
    return {"volcan": vol, "hora_utc": hora, "archivos": [gran],
            "oraculo": {brazo: o, ("B0" if brazo == "B1" else "B1"): otro}}


def e375(vol, vrp, celdas, gran=G375, hora="2026-10-05 05:18", banda=None):
    return {"volcan": vol, "hora_utc": hora, "granule": gran, "archivos": [gran],
            "port": {"C13": {"vrp_mw": vrp, "pixeles": [[f, c, 0, 1.0, 0.1, 280.0] for f, c in celdas],
                             "vrp_banda": banda},
                     "M13": {"vrp_mw": 99.0, "pixeles": []}}}


def lmodd(vol, vrp, celdas_latlon, dc="summit", gran=GMOD, dt="2026-10-05 01:50", sensor="MODIS_TERRA"):
    pix = [{"lat": a, "lon": b, "bt_k": 300.0} for a, b in celdas_latlon]
    return {"tipo": "pasada", "vol": vol, "sensor": sensor, "dt": dt, "l1b_usado": gran,
            "v_slim": {"granule": gran, "primary_cluster": {"vrp_mw": vrp} if pix else None, "anomaly_pixels": pix,
                       "distance_class": dc if pix else None, "sensor": sensor}}


def rmodis(vrp, celdas_latlon, dc="summit", gran=GMOD, dt="2026-10-05 01:50", sensor="MODIS_TERRA"):
    pix = [{"lat": a, "lon": b} for a, b in celdas_latlon]
    return {"sensor": sensor, "datetime_utc": dt, "granule": gran, "via_codigo_mirova": True,
            "primary_cluster": {"vrp_mw": vrp} if pix else None, "anomaly_pixels": pix,
            "distance_class": dc if pix else None}


# ---------------------------------------------------------------------------------------------------- identidad
def test_identidad_de_granulo_sin_version_ni_producto():
    assert M.identidad_granulo(G750) == M.identidad_granulo(G375) == ("VJ1", "2026278", "0518")
    assert M.identidad_granulo("MOD021KM.A2026278.0150.061.NRT.hdf") == M.identidad_granulo(GMOD)
    assert M.identidad_granulo("VJ202MOD.A2026278.0518.021.x.nc")[0] == "VJ2"
    assert M.identidad_granulo("basura") is None


def test_b4_es_el_del_script():
    import importlib.util as iu
    sp = iu.spec_from_file_location("roi_v750b", ROOT / "scripts" / "roi_v750b_a_grillas.py")
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    assert set(M.SENSIBLES_B4) == set(m.SENSIBLES_B4)
    assert M.brazo_b4("PuyehueCordonCaulle") == "B1" and M.brazo_b4("Lascar") == "B0"


# ---------------------------------------------------------------------------------------------------- VIIRS 750
def test_v750_igual_no_da_diferencia():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750, 0.452, [(30, 33), (31, 33)]))
    refs = M.cargar_v750b([e750("Lascar", 0.45151, [(30, 33), (31, 33)], banda=[0.45151, 0.45152])])
    assert len(refs) == 1
    assert M.comparar(v, refs, "V750-B") == []


def test_v750_usa_b1_en_cordon_caulle_y_b0_en_lascar():
    v = via("PuyehueCordonCaulle", rec_viirs("VIIRS_NOAA20_750", G750, 1.0, [(10, 10)]))
    refs = M.cargar_v750b([e750("PuyehueCordonCaulle", 1.0, [(10, 10)])])
    assert M.comparar(v, refs, "V750-B") == []
    # el mismo dato bajo el brazo equivocado tiene que dar diferencia
    refs_mal = M.cargar_v750b([e750("PuyehueCordonCaulle", 1.0, [(10, 10)], brazo="B0")])
    assert M.comparar(v, refs_mal, "V750-B")


def test_v750_una_celda_distinta_es_diferencia_sin_explicar():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750, 0.452, [(30, 33)]))
    refs = M.cargar_v750b([e750("Lascar", 0.452, [(30, 34)])])
    d = M.comparar(v, refs, "V750-B")
    assert len(d) == 1 and d[0]["campos"] == ["celdas"] and d[0]["explicada_por"] is None


def test_v750_vrp_fuera_de_la_banda_por_mas_de_0001_es_diferencia():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750, 0.454, [(30, 33)]))
    refs = M.cargar_v750b([e750("Lascar", 0.452, [(30, 33)], banda=[0.4520, 0.4525])])
    d = M.comparar(v, refs, "V750-B")
    assert len(d) == 1 and d[0]["campos"] == ["vrp_mw"]
    v2 = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750, 0.4534, [(30, 33)]))
    assert M.comparar(v2, refs, "V750-B") == []                      # a 0,0009 del borde: dentro


def test_v750_vacio_en_los_dos_no_da_diferencia_y_vacio_en_uno_si():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750, 0.0, []))
    assert M.comparar(v, M.cargar_v750b([e750("Lascar", None, [])]), "V750-B") == []
    d = M.comparar(v, M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])]), "V750-B")
    assert set(d[0]["campos"]) == {"celdas", "vrp_mw"}


def test_falta_en_via_es_diferencia_sin_explicar():
    refs = M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])])
    d = M.comparar({}, refs, "V750-B")
    assert d[0]["campos"] == ["falta_en_via"] and d[0]["explicada_por"] is None


def test_otro_granulo_explica():
    otro = "VJ102MOD.A2026278.0524.021.2026278103120.nc"
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", otro, 0.9, [(1, 2)]))
    refs = M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])])
    d = M.comparar(v, refs, "V750-B")
    assert d[0]["explicada_por"] == "otro_granulo"


def test_otra_version_de_proceso_no_es_otro_granulo():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20_750", G750.replace(".021.", ".002."), 0.9, [(1, 2)]))
    d = M.comparar(v, M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])]), "V750-B")
    assert d[0]["explicada_por"] is None


def test_fuera_de_dm_no_se_compara():
    refs = M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)], hora="2026-10-17 05:18")])
    assert refs == {}
    assert M.indexar_via({("Lascar", "VIIRS_NOAA20_750", "2026-09-30 05:18"): rec_viirs(
        "VIIRS_NOAA20_750", G750, 1.0, [(1, 1)], dt="2026-09-30 05:18")}) == {}


def test_la_plataforma_separa_pasadas():
    v = via("Lascar", rec_viirs("VIIRS_NOAA21_750", G750.replace("VJ1", "VJ2"), 0.4, [(1, 1)]))
    d = M.comparar(v, M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])]), "V750-B")
    assert d and d[0]["campos"] == ["falta_en_via"]


# ---------------------------------------------------------------------------------------------------- VIIRS 375
def test_v375_usa_c13_y_compara_celdas_y_vrp():
    v = via("Lascar", rec_viirs("VIIRS_NOAA20", G375, 0.453, [(17, 63), (18, 63)]))
    assert M.comparar(v, M.cargar_v375e([e375("Lascar", 0.45269, [(17, 63), (18, 63)])]), "V375-E") == []
    d = M.comparar(v, M.cargar_v375e([e375("Lascar", 0.45269, [(17, 63)])]), "V375-E")
    assert len(d) == 1 and d[0]["campos"] == ["celdas"]
    d = M.comparar(v, M.cargar_v375e([e375("Lascar", 0.4550, [(17, 63), (18, 63)])]), "V375-E")
    assert len(d) == 1 and d[0]["campos"] == ["vrp_mw"]


# ---------------------------------------------------------------------------------------------------- MODIS
def test_modis_igual_y_clase_distinta():
    c = [(-23.36098, -67.73009)]
    v = via("Lascar", rmodis(0.359, c))
    assert M.comparar(v, M.cargar_modd([lmodd("Lascar", 0.359, c)]), "MOD-D fase 4", comparar_dc=True) == []
    d = M.comparar(v, M.cargar_modd([lmodd("Lascar", 0.359, c, dc="far")]), "MOD-D fase 4", comparar_dc=True)
    assert len(d) == 1 and d[0]["campos"] == ["distance_class"]


def test_modis_celda_por_lat_lon():
    v = via("Lascar", rmodis(0.359, [(-23.36098, -67.73009)]))
    d = M.comparar(v, M.cargar_modd([lmodd("Lascar", 0.359, [(-23.37, -67.73009)])]), "MOD-D fase 4",
                   comparar_dc=True)
    assert d[0]["campos"] == ["celdas"]


def test_modis_ignora_cabecera_y_lineas_sin_v():
    lineas = [{"tipo": "cabecera", "dt": "2026-10-05"}, dict(lmodd("Lascar", 0.3, []), v_slim=None)]
    assert M.cargar_modd(lineas) == {}


def test_la_pasada_lleva_un_sensor_que_el_lector_reconoce_y_queda_en_dm():
    import importlib.util as iu
    sp = iu.spec_from_file_location("leer_retro_para_montaje_ab", ROOT / "experiments" / "_s172_retro_paquete" / "leer_retro.py")
    L = iu.module_from_spec(sp)
    sys.modules["leer_retro_para_montaje_ab"] = L
    sp.loader.exec_module(L)
    refs = M.cargar_v750b([e750("Lascar", 0.4, [(1, 1)])])
    d = M.comparar({}, refs, "V750-B")
    assert d[0]["pasada"] == "Lascar|VIIRS_NOAA20_750|2026-10-05 05:18"
    assert L._pasada_de_dm(d[0]["pasada"])
    assert M.nombre_sensor("MODIS", "TERRA") == "MODIS_TERRA" and L.bucket("MODIS_TERRA") == "MODIS"
    assert L.bucket(M.nombre_sensor("VIIRS375", "SNPP")) == "VIIRS375"


# S178, decisión de Nicolás («Sí, opción 1», post hoc): en VIIRS 375 el VRP se compara contra la banda de
# triangulación del port C13, como en VIIRS 750 (las 12 diferencias de DM caían todas dentro de ella).
def test_v375_usa_la_banda_de_triangulacion_del_port():
    v = via("Isluga", rec_viirs("VIIRS_NOAA20", G375, 0.788, [(67, 64)]))
    dentro = M.cargar_v375e([e375("Isluga", 0.7768, [(67, 64)], banda=[0.7711, 0.8002])])
    assert M.comparar(v, dentro, "V375-E") == []
    fuera = M.cargar_v375e([e375("Isluga", 0.7768, [(67, 64)], banda=[0.7711, 0.7760])])
    d = M.comparar(v, fuera, "V375-E")
    assert len(d) == 1 and d[0]["campos"] == ["vrp_mw"]
    sin_banda = M.cargar_v375e([e375("Isluga", 0.7768, [(67, 64)])])
    assert len(M.comparar(v, sin_banda, "V375-E")) == 1
