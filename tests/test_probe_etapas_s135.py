"""S135 — tests del probe por etapa (D19, AUDIT_S134 §D D1-b).

Tres cosas que tienen que ser verdad ANTES de gastar una corrida en CI:
  1. Los nombres que el probe parchea existen en el namespace de `pipeline.process_viirs`
     (trampa A89: parchear el módulo origen no cambia nada; parchear un nombre que no
     está ahí tampoco falla, sólo captura vacío).
  2. El análisis puro reproduce, sobre una escena sintética con el mecanismo D19
     construido a mano, exactamente los números que el criterio pre-registrado usa.
  3. El criterio da CONFIRMADA / REFUTADA / INDETERMINADA en los casos que lo definen,
     y el yml no pushea, no instala pyhdf y tiene `on` entre comillas (A43).
"""
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROBE_DIR = os.path.join(ROOT, "experiments", "_s135_probe_etapas")
sys.path.insert(0, PROBE_DIR)

from analisis import (  # noqa: E402
    CRATER_KM, PICO_LEJOS_KM, a_json, evaluar_criterio, haversine_km, octante,
    perfil_bt_vs_distancia, resumir_pasada, rumbo_deg,
)

PATCH_NAMES = ("compute_test1_mir", "apply_contextual_test1_filter",
               "first_pass_tests_2_and_3", "second_pass_adjacent", "cluster_hotspots")


# ---------- 1. A89: los nombres existen donde el probe los parchea ----------

def test_a89_los_nombres_parcheados_existen_en_process_viirs():
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import pipeline.process_viirs as pv
    faltan = [n for n in PATCH_NAMES if not callable(getattr(pv, n, None))]
    assert not faltan, f"el probe parchearía nombres que no están en process_viirs: {faltan}"


def test_el_runner_declara_los_mismos_nombres_que_este_test():
    src = open(os.path.join(PROBE_DIR, "probe_etapas.py"), encoding="utf-8").read()
    for n in PATCH_NAMES:
        assert f'"{n}"' in src, f"{n} no está en PATCH_NAMES del runner"
        assert f"pv.{n} = " in src, f"el runner no asigna pv.{n}"


# ---------- 2. Escena sintética con el mecanismo D19 ----------

VENT = (-39.420227, -71.939876)  # Villarrica, volcanoes.yaml


def _escena(n=41, paso_km=0.375, t_cima=272.0, gradiente_k_por_km=3.0, crater_extra_k=0.0):
    """Grilla n×n centrada en el vent. BT sube con la distancia (cono nevado, A69):
    el borde del disco es lo más caliente. `crater_extra_k` agrega calor al píxel central."""
    c = n // 2
    dlat = paso_km / 111.0
    dlon = paso_km / (111.0 * np.cos(np.radians(VENT[0])))
    ii, jj = np.mgrid[0:n, 0:n]
    lat = VENT[0] + (ii - c) * dlat
    lon = VENT[1] + (jj - c) * dlon
    d = haversine_km(VENT[0], VENT[1], lat, lon)
    bt = t_cima + gradiente_k_por_km * d
    bt[c, c] += crater_extra_k
    return lat, lon, bt, d, c


def _cap_d19(crater_extra_k=0.0):
    """Captura como la produciría el pipeline en una noche D19: Test 1 marca todo el
    disco de 3 km por encima de la mediana del anillo [1,3]; dNTI_ctx vacía; keep_peak
    = argmax(BT) de la máscara; first pass vacío; second pass agrega 2 píxeles tibios."""
    lat, lon, bt, d, c = _escena(crater_extra_k=crater_extra_k)
    disco = d < 3.0
    med = np.median(bt[(d >= 1.0) & (d < 3.0)])
    mask = disco & (bt > med)
    if crater_extra_k > 0:
        mask[c, c] = True
    rr, cc = np.where(mask)
    k = int(np.argmax(bt[rr, cc]))
    peak = (int(rr[k]), int(cc[k]))
    fp_hot = np.zeros_like(mask)
    sp_out = np.zeros_like(mask)
    sp_out[c + 8, c + 8] = True   # ~4,2 km, tibio pero bajo la compuerta de 3 K
    sp_out[c - 8, c - 8] = True
    return {
        "test1": {"bt": bt, "lat": lat, "lon": lon, "mask_contributing": mask,
                  "triggered": True, "n_contributing": int(mask.sum()), "roi_km": 3.0,
                  "k_sigma_observed": 5.0},
        "ctx_filter": {"mask_in": mask, "dnti_ctx": np.zeros_like(mask),
                       "keep_peak_rc": peak, "mask_out": _solo(mask.shape, peak)},
        "first_pass": {"hot": fp_hot, "dist_km": d, "t_bg": 284.0, "diag": {"n_bg_used": 100}},
        "second_pass": [{"active_in": fp_hot, "out": sp_out}],
        "clusters": [],
    }, bt, d, c


def _solo(shape, rc):
    m = np.zeros(shape, dtype=bool)
    m[rc] = True
    return m


def test_geometria_basica():
    assert abs(haversine_km(0, 0, 0, 1) - 111.19) < 0.1
    assert octante(rumbo_deg(0, 0, 1, 0)) == "N"
    assert octante(rumbo_deg(0, 0, 0, 1)) == "E"
    assert octante(rumbo_deg(0, 0, -1, 0)) == "S"
    assert octante(rumbo_deg(0, 0, 0, -1)) == "W"


def test_en_la_escena_d19_el_pico_es_el_borde_y_el_crater_esta_en_la_mascara_o_no():
    # Sin calor en el cráter: el centro está BAJO la mediana del anillo → no está en la
    # máscara. Eso es la rama «REFUTADA» del criterio, y hay que poder medirla.
    cap, bt, d, c = _cap_d19(crater_extra_k=0.0)
    t_bg = 284.0   # fondo global 5-25 km: valles tibios, más caliente que TODO el disco (A69)
    r = resumir_pasada(cap, VENT[0], VENT[1], VENT[0], VENT[1], t_bg)
    assert r["test1"]["corrio"] and r["test1"]["triggered"]
    assert r["test1"]["n_mask_a_menos_0_5km"] == 0
    assert r["test1"]["pixel_mas_cercano_al_vent"]["en_mask_contributing"] is False
    kp = r["keep_peak"]
    assert kp["dist_vent_km"] > PICO_LEJOS_KM        # el borde del disco
    assert kp["dist_vent_km"] < 3.0
    assert kp["es_argmax_del_disco"] is True
    assert kp["bt_menos_t_bg_global_k"] < 0            # más frío que el fondo global (D19)
    assert r["interseccion_sin_pico"]["n"] == 0        # dNTI_ctx vacía → sólo queda el pico
    assert r["interseccion_sin_pico"]["n_mask_out"] == 1
    # H2: first pass vacío, 2 newly_active, los 2 bajo la compuerta de 3 K
    assert r["first_pass"]["n_hot"] == 0
    assert r["second_pass"][0]["n_newly_active"] == 2
    assert r["second_pass"][0]["n_newly_bajo_compuerta_3k"] == 2
    # Perfil: la mediana de BT crece con la distancia en TODOS los octantes (borde, no valle)
    perfil = r["perfil_bt"]
    meds = [f["bt_mediana"] for f in perfil if f["bt_mediana"] is not None]
    assert meds == sorted(meds)
    for o in ("N", "E", "S", "W"):
        serie = [f["por_octante"][o]["bt_mediana"] for f in perfil[2:]
                 if f["por_octante"][o]["bt_mediana"] is not None]
        assert serie == sorted(serie), o


def test_con_calor_en_el_crater_la_mascara_lo_contiene_pero_keep_peak_igual_elige_el_borde():
    # Cráter 2 K sobre su entorno pero el borde del disco está 9 K más caliente por cota:
    # el cráter ESTÁ en mask_contributing y aun así keep_peak lo descarta. Es la rama
    # «CONFIRMADA» del criterio, la que motiva el A/B.
    cap, bt, d, c = _cap_d19(crater_extra_k=2.0)
    r = resumir_pasada(cap, VENT[0], VENT[1], VENT[0], VENT[1], 284.0)
    assert r["test1"]["n_mask_a_menos_0_5km"] >= 1
    assert r["test1"]["pixeles_crater_en_mask"][0]["dist_vent_km"] < CRATER_KM
    assert r["test1"]["rango_bt_crater_en_mask"] > 1    # no es el más caliente de la máscara
    assert r["keep_peak"]["dist_vent_km"] > PICO_LEJOS_KM


def test_sin_test1_no_revienta():
    r = resumir_pasada({}, *VENT, *VENT, 270.0)
    assert r["test1"] == {"corrio": False}


def test_a_json_convierte_numpy_y_nan():
    out = a_json({"a": np.float64(1.5), "b": np.int64(2), "c": np.bool_(True),
                  "d": float("nan"), "e": np.array([1, 2])})
    assert out == {"a": 1.5, "b": 2, "c": True, "d": None, "e": [1, 2]}


# ---------- 3. El criterio pre-registrado ----------

def _pasada(vol, clase, n_crater, d_pico, n_fp=0, newly=(0, 0), ok=True):
    return {"volcan": vol, "pasada_utc": "x", "clase": clase, "ok": ok, "resumen": {
        "test1": {"corrio": True, "n_mask_a_menos_0_5km": n_crater},
        "keep_peak": (None if d_pico is None else
                      {"dist_vent_km": d_pico, "bt_menos_t_bg_global_k": -2.0}),
        "first_pass": {"n_hot": n_fp},
        "second_pass": [{"n_newly_active": newly[0], "n_newly_bajo_compuerta_3k": newly[1]}],
    }}


def test_criterio_confirmada():
    ps = [_pasada("Villarrica", "nevado", 3, 2.8, newly=(10, 10))] * 3 + \
         [_pasada("Lascar", "control", 5, 0.1)] * 2 + [_pasada("Lascar", "control", 5, None)]
    c = evaluar_criterio(ps)
    assert c["h1"].startswith("CONFIRMADA")
    assert c["n_nevado_confirman"] == "3/3" and c["n_control_ok"] == "3/3"
    assert c["h2"].startswith("CONFIRMADA")


def test_criterio_refutada_si_el_crater_no_esta_en_el_test1():
    ps = [_pasada("Villarrica", "nevado", 3, 2.8), _pasada("Villarrica", "nevado", 0, 2.8),
          _pasada("Villarrica", "nevado", 2, 2.8), _pasada("Lascar", "control", 5, 0.1)]
    assert evaluar_criterio(ps)["h1"].startswith("REFUTADA")


def test_criterio_indeterminada_si_el_control_falla_o_una_pasada_no_confirma():
    ps = [_pasada("Villarrica", "nevado", 3, 2.8)] * 3 + [_pasada("Lascar", "control", 5, 2.5)]
    assert evaluar_criterio(ps)["h1"].startswith("INDETERMINADA")
    ps = [_pasada("Villarrica", "nevado", 3, 1.0)] + [_pasada("Villarrica", "nevado", 3, 2.8)] * 2
    assert evaluar_criterio(ps)["h1"].startswith("INDETERMINADA")


def test_criterio_h2_no_confirmada_y_no_evaluable():
    ps = [_pasada("Villarrica", "nevado", 3, 2.8, newly=(10, 5))]
    assert evaluar_criterio(ps)["h2"].startswith("NO CONFIRMADA")
    ps = [_pasada("Villarrica", "nevado", 3, 2.8, n_fp=4, newly=(10, 10))]  # first pass no vacío
    assert evaluar_criterio(ps)["h2"].startswith("NO EVALUABLE")


def test_pasada_fallida_no_evaluable_y_no_confirma():
    ps = [_pasada("Villarrica", "nevado", 3, 2.8)] * 2 + [_pasada("Villarrica", "nevado", 3, 2.8, ok=False)]
    c = evaluar_criterio(ps)
    assert c["detalle"][2]["h1"] == "no_evaluable"
    assert not c["h1"].startswith("CONFIRMADA")


# ---------- 4. El yml ----------

YML = os.path.join(ROOT, ".github", "workflows", "probe-s135-etapas.yml")


@pytest.mark.skipif(not os.path.exists(YML), reason="yml archivado (regla S80 de plantillas)")
def test_yml_read_only_sin_pyhdf_y_on_quoteado():
    txt = open(YML, encoding="utf-8").read()
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d, "A43: 'on' debe ir entre comillas"
    assert "git push" not in txt, "el probe es read-only"
    assert "pyhdf" not in txt, "sólo VIIRS: sin pyhdf"
    assert "probe_etapas.py" in txt
