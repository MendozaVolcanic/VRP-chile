# -*- coding: utf-8 -*-
"""S141, Fase 1: tests del instrumento v2 del vecino del foco (VIIRS 375 m), rediseño por H3.

POR QUÉ. El verificador pre-corrida (`experiments/_s141_fase1_probe/VERIFICADOR_V2_PRE_CORRIDA.md`)
mostró que el destino por vecino del v2 estaba decidido antes de correr: `cluster_hotspots` agrupa
componentes 8-conexas (`clustering.py:91-96`), así que un vecino alertado del centro siempre queda en
el cúmulo, y en la ruta contextual todo lo marcado queda en la entrada (`detection_context.py:948`).
La pérdida de los vecinos tibios está en la DETECCIÓN. La pregunta pasa a ser: ¿qué test deja fuera
a cada vecino tibio y por cuánto? Estos tests fijan:

  1. la muestra y `foco_ok` miden contra NUESTRO pico, sin rama del cráter (H1);
  2. los márgenes a cada test se replican contra las funciones REALES del pipeline, y la réplica
     puede fallar (C4);
  3. el test limitante se nombra dentro de la ruta que publicó;
  4. las imposibilidades por construcción están probadas, no afirmadas;
  5. C3 es un control que falla ante un índice corrido (H2); C1 no castiga pasadas sin cúmulo (H4);
  6. el filtro de distancia de store.py se aplica antes de F5 (H5); los flags se afirman (H10);
  7. el criterio es por volcán, con mínimo y dejando uno fuera.

Plan y criterio pre-registrado: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md
"""
import json
import math
import os
import re
import subprocess
import sys
import types

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V2 = os.path.join(ROOT, "experiments", "_s141_fase1_probe_v2")
V1 = os.path.join(ROOT, "experiments", "_s141_fase1_probe")
YML = os.path.join(ROOT, ".github", "workflows", "probe-s141-vecinos-v2.yml")
sys.path.insert(0, ROOT)
sys.path.insert(0, V2)

VENT_LASCAR = (-23.36293, -67.731416)
DLAT = 0.375 / 111.195                       # un píxel de 375 m en latitud


# ---------------------------------------------------------------- 1. muestra (H1: sólo nuestro pico)

def _pares():
    t = pd.date_range("2025-03-01 05:00", periods=8, freq="3D")
    lat0, lon0 = VENT_LASCAR
    filas = []
    for k in range(8):
        filas.append(dict(vol="Lascar", res=375, Npix=4, pub_n=1, t_osf=t[k], t_ours=t[k] + pd.Timedelta(minutes=2),
                          sensor="VIIRS_SNPP", osf_mw=1.0, pub_mw=0.4, satzen=20.0, pc_n=1, t_bg=260.0,
                          lat=lat0, lon=lon0, pico_lat=lat0, pico_lon=lon0))
    filas[1]["lat"] = lat0 + 15 / 111.195                            # foco de MIROVA en otra anomalía
    filas[2].update(lat=lat0 + 3 / 111.195, pico_lat=lat0 + 3 / 111.195)  # lejos del cráter, junto a nuestro pico
    filas[3]["lat"] = float("nan")                                   # sin posición en el OSF
    filas[4]["pico_lat"] = lat0 + 16 / 111.195                       # MIROVA en el cráter, nuestro pico a 16 km (Puyehue 2025-07-18)
    filas[5]["pico_lat"] = float("nan")                              # sin pico persistido
    filas.append(dict(filas[0], t_osf=t[7] + pd.Timedelta(days=3), t_ours=t[7] + pd.Timedelta(days=3, minutes=2),
                      Npix=3, pub_n=3))                              # control
    return pd.DataFrame(filas)


def test_muestra_mide_el_foco_contra_nuestro_pico_sin_rama_del_crater():
    from muestra import seleccionar
    out = seleccionar(_pares(), vents={"Lascar": VENT_LASCAR}, excluir=set(), por_volcan=10, controles_por_volcan=10)
    exc = {x["pasada_utc"]: x for x in out["excluidas"]}
    assert exc["2025-03-04 05:02"]["motivo"] == "foco_mirova_lejos"
    assert exc["2025-03-10 05:02"]["motivo"] == "sin_posicion_osf"
    assert exc["2025-03-13 05:02"]["motivo"] == "foco_mirova_lejos", "H1: MIROVA en el cráter no basta"
    assert exc["2025-03-13 05:02"]["dist_foco_crater_km"] < 0.1
    assert exc["2025-03-16 05:02"]["motivo"] == "sin_pico_persistido"
    usadas = {x["pasada_utc"] for x in out["pasadas"]}
    assert "2025-03-07 05:02" in usadas
    assert all(x["osf"]["dist_pico_km"] <= 0.75 for x in out["pasadas"])


def test_muestra_excluye_las_pasadas_del_v1_y_es_determinista():
    from muestra import seleccionar
    d = _pares()
    excluir = {("Lascar", "2025-03-01 05:02")}
    a = seleccionar(d, vents={"Lascar": VENT_LASCAR}, excluir=excluir, por_volcan=2, controles_por_volcan=1)
    assert a == seleccionar(d, vents={"Lascar": VENT_LASCAR}, excluir=excluir, por_volcan=2, controles_por_volcan=1)
    assert ("Lascar", "2025-03-01 05:02") not in {(x["volcan"], x["pasada_utc"]) for x in a["pasadas"]}
    assert any(x["motivo"] == "pasada_del_v1" for x in a["excluidas"])
    assert len([x for x in a["pasadas"] if x["clase"] == "candidato"]) == 2
    assert all(x["pasada_utc"].count(":") == 1 for x in a["pasadas"]), "formato del probe S135"


def test_muestra_commiteada_no_repite_el_v1_y_respeta_el_radio_al_pico():
    nueva = json.load(open(os.path.join(V2, "pasadas.json"), encoding="utf-8"))
    vieja = json.load(open(os.path.join(V1, "pasadas.json"), encoding="utf-8"))
    assert nueva
    assert not ({(x["volcan"], x["pasada_utc"]) for x in nueva} & {(x["volcan"], x["pasada_utc"]) for x in vieja})
    assert all(x["osf"]["dist_pico_km"] is not None and x["osf"]["dist_pico_km"] <= 0.75 for x in nueva)


# ---------------------------------------------------------------- 2. captura

def test_captura_rotula_la_ruta_del_cumulo_y_copia_la_entrada():
    from captura import Captura
    cap = Captura()
    lat = lon = np.zeros((4, 4))
    salida = [{"n_pixels": 2, "centroid_lat": 1.0, "centroid_lon": 2.0, "vrp_mw": 0.3, "pixel_indices": [(1, 1), (1, 2)]}]
    f = cap.envolver_cluster(lambda *a, **kw: salida)
    m = np.zeros((4, 4), bool)
    m[1, 1] = m[1, 2] = True
    f(m, lat, lon, 0.0, 0.0, vrp_per_pixel=np.zeros((4, 4)), strategy="vent_anchored", inner_radius_km=5)   # :1467
    f(m, lat, lon, 0.0, 0.0, connectivity=8, vrp_per_pixel=np.zeros((4, 4)), strategy="vent_anchored",     # :1910
      inner_radius_km=5)
    m[0, 0] = True
    ev = cap.de_tipo("cluster")
    assert [e["ruta"] for e in ev] == ["contextual", "test1"]
    assert ev[0]["clusters"][0]["pixel_indices"] == [(1, 1), (1, 2)]
    assert not ev[0]["entrada"][0, 0]
    assert ev[0]["seq"] < ev[1]["seq"]


def test_captura_etapas_que_corrieron_y_argumentos_de_los_tests():
    from captura import Captura
    cap = Captura()
    assert all(v is False for v in cap.corrio().values())
    fp = cap.envolver_first_pass(lambda **kw: (np.zeros((3, 3), bool), {"mu_dnti": 0.0, "eti": np.ones((3, 3))}))
    fp(nti=np.zeros((3, 3)), bt=np.zeros((3, 3)))
    sp = cap.envolver_second_pass(lambda *a, **kw: np.zeros((3, 3), bool))
    sp(None, None, np.zeros((3, 3), bool))                          # posicional: ETI de escena, :1149
    ctx = cap.envolver_dnti_ctx(lambda **kw: np.zeros((3, 3), bool))
    ctx(nti=np.zeros((3, 3)))
    c = cap.corrio()
    assert c["first_pass"] and c["dnti_ctx"] and not c["second_pass_por_nombre"]
    ev = cap.de_tipo("first_pass")[0]
    assert "nti" in ev["kw"] and ev["diag"]["mu_dnti"] == 0.0 and ev["diag"]["eti"] is not None
    lbg = cap.envolver_lbg(lambda **kw: 1.5)
    lbg(intermediate_enabled=False)
    assert cap.lbg_test1() == 1.5


def test_flags_de_la_taxonomia_se_afirman():
    from flags import FLAGS_ESPERADOS, verificar_flags
    bueno = types.SimpleNamespace(**FLAGS_ESPERADOS)
    verificar_flags(bueno)
    malo = types.SimpleNamespace(**dict(FLAGS_ESPERADOS, ENABLE_SECOND_PASS_INTRA_RADIO_GATE=True))
    with pytest.raises(AssertionError, match="ENABLE_SECOND_PASS_INTRA_RADIO_GATE"):
        verificar_flags(malo)
    falta = types.SimpleNamespace(**{k: v for k, v in FLAGS_ESPERADOS.items() if k != "ENABLE_FINAL_PIXEL_FILTER"})
    with pytest.raises(AssertionError, match="ENABLE_FINAL_PIXEL_FILTER"):
        verificar_flags(falta)
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import pipeline.process_viirs as pv
    verificar_flags(pv)                                              # el perfil de hoy cumple


# ---------------------------------------------------------------- 3. márgenes contra las funciones reales

def _campo(n=15, seed=3):
    rng = np.random.default_rng(seed)
    nti = -0.90 + 0.002 * rng.standard_normal((n, n))
    nti_app = -0.90 + 0.002 * rng.standard_normal((n, n))
    bt = 265.0 + 0.4 * rng.standard_normal((n, n))
    c = n // 2
    nti[c, c], bt[c, c] = -0.40, 300.0              # foco
    nti[c, c + 1], bt[c, c + 1] = -0.80, 266.0      # vecino con NTI alto pero BT bajo la compuerta
    nti[c + 1, c], bt[c + 1, c] = -0.899, 272.0     # vecino tibio sin contraste de NTI
    ii, jj = np.indices((n, n))
    dist = np.hypot(ii - c, jj - c) * 0.375
    return nti, nti_app, bt, dist, c


def _kw_fp(nti, nti_app, bt, dist):
    return dict(nti=nti, nti_app=nti_app, bt=bt, roi_mask=np.ones(bt.shape, bool), dist_km=dist, roi1_mask=None,
                t_bg=265.0, bt_sanity_k=3.0, c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5.0,
                c2_deti_summit=5.0, inner_km=1.0, c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10.0,
                c2_deti_scene=10.0, test1_mask=None, unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1,
                use_prose_branch=False)


def _todos(shape):
    return [(i, j) for i in range(shape[0]) for j in range(shape[1])]


def test_margenes_primer_pase_replican_la_funcion_real():
    from captura import Captura
    from margenes import margenes_primer_pase
    from pipeline.detection_context import first_pass_tests_2_and_3
    nti, nti_app, bt, dist, c = _campo()
    cap = Captura()
    hot, _ = cap.envolver_first_pass(first_pass_tests_2_and_3)(**_kw_fp(nti, nti_app, bt, dist))
    m = margenes_primer_pase(cap.de_tipo("first_pass")[0], _todos(bt.shape))
    assert hot.any() and not hot.all(), "el caso no puede ser trivial"
    assert all(v["replica_ok"] for v in m.values())
    assert all(v["pasa"] == bool(hot[ij]) for ij, v in m.items())
    v = m[(c, c + 1)]
    assert v["margen_bt_k"] <= 0 < v["margen_dnti"], "el vecino frío pasa el dNTI y cae por la compuerta (D22)"


def test_margenes_segundo_pase_replican_la_funcion_real_y_no_tienen_compuerta_bt():
    from captura import Captura
    from margenes import margenes_segundo_pase
    from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent
    nti, nti_app, bt, dist, c = _campo()
    cap = Captura()
    hot, diag = cap.envolver_first_pass(first_pass_tests_2_and_3)(**_kw_fp(nti, nti_app, bt, dist))
    out = cap.envolver_second_pass(second_pass_adjacent)(
        nti=nti, eti=diag["eti"], active_mask=hot, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5.0, c2_deti=5.0,
        is_summit=dist <= 1.0, c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10.0, c2_deti_scene=10.0,
        conditioned=False, use_prose_branch=False)
    m = margenes_segundo_pase(cap.de_tipo("second_pass")[0], _todos(bt.shape))
    assert all(v["replica_ok"] for v in m.values())
    assert all(v["pasa"] == bool(out[ij]) for ij, v in m.items())
    assert "margen_bt_k" not in m[(c, c + 1)], "el segundo pase no tiene compuerta de BT (detection_context.py:939-940)"


def test_margenes_dnti_contextual_replican_la_funcion_real():
    from captura import Captura
    from margenes import margenes_dnti_ctx
    from pipeline.detection_context import dual_roi_contextual_dnti_hot_mask
    nti, _, bt, dist, c = _campo()
    cap = Captura()
    out = cap.envolver_dnti_ctx(dual_roi_contextual_dnti_hot_mask)(
        nti=nti, bt=bt, roi_mask=np.ones(bt.shape, bool), dist_km=dist, roi1_mask=None, t_bg=265.0,
        c1_summit=0.003, c1_scene=0.010, inner_km=1.0, bt_sanity_k=3.0, apply_unsuitable_filters=True)
    m = margenes_dnti_ctx(cap.de_tipo("dnti_ctx")[0], _todos(bt.shape))
    assert out.any() and all(v["replica_ok"] for v in m.values())
    assert all(v["pasa"] == bool(out[ij]) for ij, v in m.items())
    assert m[(0, 0)]["no_apto"] is True, "borde de la matriz (§267-273)"


def test_la_replica_puede_fallar():
    """C4 no aprueba por construcción: con un umbral distinto del que usó la función, discrepa."""
    from captura import Captura
    from margenes import margenes_primer_pase
    from pipeline.detection_context import first_pass_tests_2_and_3
    nti, nti_app, bt, dist, _ = _campo()
    cap = Captura()
    cap.envolver_first_pass(first_pass_tests_2_and_3)(**_kw_fp(nti, nti_app, bt, dist))
    ev = cap.de_tipo("first_pass")[0]
    ev["kw"] = dict(ev["kw"], bt_sanity_k=-50.0)
    assert not all(v["replica_ok"] for v in margenes_primer_pase(ev, _todos(bt.shape)).values())


# ---------------------------------------------------------------- 4. limitante e imposibilidades

def test_limitante_dentro_de_la_ruta():
    from margenes import limitante
    assert limitante("contextual", m2p={"margen_dnti": -0.001, "margen_deti": 0.002}) == "dnti_2p"
    assert limitante("contextual", m2p={"margen_dnti": -0.001, "margen_deti": -0.1}) == "deti_2p+dnti_2p"
    assert limitante("contextual", m1p={"margen_dnti": 0.01, "margen_deti": 0.01, "margen_bt_k": -1.0, "en_roi": True}) \
        == "bt_1p", "sin segundo pase la compuerta sí puede ser la limitante"
    assert limitante("test1", mctx={"margen_dnti": 0.01, "margen_bt_k": 2.0, "no_apto": False, "en_roi": True},
                     en_disco=False) == "test1_disco"
    assert limitante("test1", mctx={"margen_dnti": -0.01, "margen_bt_k": -2.0, "no_apto": False, "en_roi": True},
                     en_disco=True) == "bt_ctx+dnti_ctx"
    assert limitante("contextual") == "sin_datos"


def test_imposible_por_construccion_vecino_alertado_fuera_del_cumulo():
    """H3: cluster_hotspots agrupa componentes 8-conexas (clustering.py:91-96)."""
    from pipeline.clustering import cluster_hotspots
    lat, lon = np.meshgrid(np.linspace(-23.30, -23.34, 9), np.linspace(-67.70, -67.74, 9), indexing="ij")
    for di, dj in [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]:
        m = np.zeros((9, 9), bool)
        m[4, 4] = m[4 + di, 4 + dj] = True
        cl = cluster_hotspots(m, lat, lon, float(lat[4, 4]), float(lon[4, 4]), strategy="vent_anchored",
                              inner_radius_km=5)
        assert (4 + di, 4 + dj) in cl[0]["pixel_indices"]


def test_imposible_por_construccion_la_compuerta_sola_tras_el_segundo_pase():
    """Un vecino que el primer pase deja fuera sólo por BT entra en el segundo pase, que no tiene compuerta."""
    from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent
    nti, nti_app, bt, dist, c = _campo()
    hot, diag = first_pass_tests_2_and_3(**_kw_fp(nti, nti_app, bt, dist))
    assert hot[c, c] and not hot[c, c + 1]
    out = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=hot, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5.0,
                               c2_deti=5.0, is_summit=dist <= 1.0, c1_dnti_scene=0.010, c1_deti_scene=0.010,
                               c2_dnti_scene=10.0, c2_deti_scene=10.0)
    assert out[c, c + 1]


# ---------------------------------------------------------------- 5. publicado, F5, C3 y filtro de store.py

def _ev(seq, ruta, n, clat, clon, idx, forma=(41, 41)):
    e = np.zeros(forma, bool)
    for a, b in idx:
        e[a, b] = True
    return {"tipo": "cluster", "seq": seq, "ruta": ruta, "entrada": e, "vrp_per_pixel": np.zeros(forma),
            "clusters": [{"n_pixels": n, "centroid_lat": clat, "centroid_lon": clon, "pixel_indices": idx}] if idx else []}


def test_publicado_se_identifica_contra_el_record():
    from analisis_v2 import identificar_publicado
    ctx = _ev(1, "contextual", 3, -23.10000, -67.20000, [(5, 5), (5, 6), (6, 5)])
    t1 = _ev(2, "test1", 1, -23.20000, -67.30000, [(9, 9)])
    pc = {"n_pixels": 3, "centroid_lat": -23.1, "centroid_lon": -67.2}
    p = identificar_publicado([ctx, t1], pc)
    assert p["identificado"] and not p["ambiguo"] and p["ruta"] == "contextual"
    assert identificar_publicado([ctx, _ev(3, "test1", 0, None, None, [])], pc)["ruta"] == "contextual"
    assert identificar_publicado([ctx], None)["motivo"] == "sin_primary_cluster"
    otro = _ev(4, "test1", 3, -23.10000, -67.20000, [(1, 1), (1, 2), (2, 1)])
    assert identificar_publicado([ctx, otro], pc)["ambiguo"] is True


def test_nucleo_f5_replica_y_conteo():
    from analisis_v2 import n_publicado_hoy, nucleo_f5
    from pipeline.f5_core import f5_core_vrp_mw
    lat0, lon0 = VENT_LASCAR
    rec = {"primary_cluster": {"centroid_lat": lat0, "centroid_lon": lon0, "n_pixels": 3, "single_pixel_mode": True},
           "anomaly_pixels": [
               {"lat": lat0, "lon": lon0, "bt_k": 300.0, "vrp_mw": 0.30},
               {"lat": lat0 + DLAT, "lon": lon0, "bt_k": 280.0, "vrp_mw": 0.05},
               {"lat": lat0 + 4 * DLAT, "lon": lon0, "bt_k": 296.0, "vrp_mw": 0.04},
               {"lat": lat0 + 4 * DLAT, "lon": lon0 + 0.01, "bt_k": 270.0, "vrp_mw": 0.02}]}
    r = nucleo_f5(rec, 5.0)
    assert r["total"] == pytest.approx(f5_core_vrp_mw(rec, 5.0)) and r["n"] == 3
    assert n_publicado_hoy(rec, r) == 3
    sin = dict(rec, anomaly_pixels=[])
    assert n_publicado_hoy(sin, nucleo_f5(sin, 5.0)) == 1


def _escena():
    i, j = np.meshgrid(np.arange(41), np.arange(41), indexing="ij")
    lat = -23.30 - i * DLAT
    lon = -67.70 + j * DLAT / math.cos(math.radians(23.3))
    bt = np.full(lat.shape, 270.0)
    bt[20, 20] = 300.0
    bt[20, 21] = 290.0
    bt[19, 20] = 285.0
    bt[21, 20] = 284.0
    bt[20, 22] = 279.0
    bt[20, 33] = 276.0
    return lat, lon, bt


def _record_de(lat, lon, bt, idx, vrp, n=None, desplazar=0):
    return {"primary_cluster": {"n_pixels": len(idx) if n is None else n},
            "anomaly_pixels": [{"lat": round(float(lat[a + desplazar, b]), 5), "lon": round(float(lon[a + desplazar, b]), 5),
                                "bt_k": round(float(bt[a, b]), 2), "vrp_mw": float(vrp[a, b])} for a, b in idx]}


def test_c3_alineacion_bt_falla_ante_un_indice_corrido():
    from analisis_v2 import alineacion_bt
    lat, lon, bt = _escena()
    idx = [(20, 20), (20, 21)]
    vrp = np.zeros(bt.shape)
    vrp[20, 20], vrp[20, 21] = 0.2, 0.5
    assert alineacion_bt(bt, lat, lon, idx, _record_de(lat, lon, bt, idx, vrp)) is True
    corrido = [(a + 1, b) for a, b in idx]
    assert alineacion_bt(bt, lat, lon, corrido, _record_de(lat, lon, bt, idx, vrp)) is False
    assert alineacion_bt(bt, lat, lon, idx, _record_de(lat, lon, bt, idx, vrp, n=5)) is False, "n_pixels distinto"
    assert alineacion_bt(bt, lat, lon, idx, {"primary_cluster": {"n_pixels": 2}, "anomaly_pixels": []}) is None


def test_filtro_de_distancia_de_store_se_aplica_antes_del_nucleo_f5():
    from analisis_v2 import aplicar_filtro_store
    from pipeline.f5_core import f5_core_vrp_mw
    lat0, lon0 = -40.5255, -72.1461
    rec = {"sensor": "VIIRS_SNPP", "primary_cluster": {"centroid_lat": lat0, "centroid_lon": lon0, "n_pixels": 2},
           "anomaly_pixels": [{"lat": lat0, "lon": lon0, "bt_k": 300.0, "vrp_mw": 1.0, "dist_km": 7.0},
                              {"lat": lat0 + 0.1, "lon": lon0, "bt_k": 299.0, "vrp_mw": 5.0, "dist_km": 26.0}]}
    filtrado = aplicar_filtro_store(rec, radius_km=25, habilitado=True)
    assert f5_core_vrp_mw(rec, 20) != f5_core_vrp_mw(filtrado, 20)
    assert len(rec["anomaly_pixels"]) == 2, "el record original no se toca"
    assert aplicar_filtro_store(rec, radius_km=25, habilitado=False)["anomaly_pixels"] == rec["anomaly_pixels"]


# ---------------------------------------------------------------- 6. resumen de la pasada

def _publicado(ruta="contextual"):
    lat, lon, bt = _escena()
    entrada = np.zeros(bt.shape, bool)
    entrada[20, 20] = entrada[20, 21] = True
    vrp = np.zeros(bt.shape)
    vrp[20, 20], vrp[20, 21] = 0.2, 0.5
    return {"ruta": ruta, "indices": [(20, 20), (20, 21)], "entrada": entrada, "vrp_per_pixel": vrp}


def _resumen(**kw):
    from analisis_v2 import resumir_pasada
    lat, lon, bt = _escena()
    base = dict(bt=bt, lat=lat, lon=lon, publicado=_publicado(), eventos=[], npix_osf=4,
                osf_lat=float(lat[20, 20]), osf_lon=float(lon[20, 20]), brecha_mw=1.0, t_bg_anillo_k=268.0)
    base.update(kw)
    return resumir_pasada(**base)


def test_centro_es_el_pico_del_cumulo_y_foco_ok_mide_contra_el_centro():
    lat, lon, _ = _escena()
    r = _resumen()
    assert r["centro"] == [20, 21] and r["foco_ok"] is True
    assert r["dist_centro_osf_km"] == pytest.approx(0.375, abs=0.02)
    lejos = _resumen(osf_lat=float(lat[20, 30]), osf_lon=float(lon[20, 30]), vent_lat=float(lat[20, 30]),
                     vent_lon=float(lon[20, 30]))
    assert lejos["foco_ok"] is False, "H1: el foco de MIROVA en el cráter no basta si nuestro centro está lejos"


def test_fondo_local_con_mascara_de_la_ruta_y_fondo_del_cumulo():
    from analisis_v2 import aporte_mw, fondo_local_k, planck_i04
    lat, lon, bt = _escena()
    ls = [planck_i04(bt[a, b]) for a, b in ((20, 22), (21, 22), (22, 20), (22, 21), (22, 22), (21, 20))]
    esperado = 14388.0 / (3.74 * math.log(1 + 1.191042e8 / (3.74 ** 5 * (sum(ls) / len(ls)))))
    assert fondo_local_k(bt, _publicado()["entrada"], 21, 21) == pytest.approx(esperado, abs=1e-6)
    r = _resumen()
    assert r["vrp_ruta_cumulo_mw"] == pytest.approx(0.7)
    alerta = _publicado()["entrada"]
    local = sum(aporte_mw(bt[ij], fondo_local_k(bt, alerta, *ij)) for ij in [(20, 20), (20, 21)])
    assert r["aporte_local_cumulo_mw"] == pytest.approx(local)
    assert r["fraccion_fondo"] == pytest.approx((local - 0.7) / 1.0)


def test_contraste_con_pixel_de_control_y_exceso_del_centro():
    r = _resumen()
    assert r["control"]["ij"] == [20, 33] and 3.0 <= r["control"]["dist_km"] <= 6.0
    assert r["control"]["exceso_mediano_calientes_k"] == pytest.approx(0.0, abs=1e-6)
    assert r["exceso_mediano_calientes_k"] > 1.0
    assert r["exceso_centro_k"] > r["control"]["exceso_centro_k"], "H6: se reporta la intensidad de ambos"


def test_vecinos_calientes_llevan_limitante_y_sin_eventos_la_replica_no_aprueba():
    r = _resumen()
    cal = [v for v in r["vecinos"] if v["caliente"]]
    assert len(cal) == 3
    assert {v["incluido"] for v in cal} == {True, False}
    assert all(v["limitante"] == "sin_datos" for v in cal if not v["incluido"])
    assert r["replica_ok"] is None, "sin eventos no hay réplica: no cuenta como aprobada"
    assert r["fraccion_brecha"] == pytest.approx(
        sum(v["aporte_local_mw"] for v in cal if not v["incluido"]) / 1.0)


def test_grilla_distinta_se_marca():
    lat, lon, bt = _escena()
    p = _publicado()
    p["entrada"] = np.zeros((5, 5), bool)
    assert _resumen(publicado=p)["grilla_ok"] is False


# ---------------------------------------------------------------- 7. ensamblado con funciones reales

def _flujo(test1_publica):
    """Recorre las llamadas en el orden de process_viirs.py con las funciones REALES de detección, cúmulo y
    filtro contextual; sólo el Test 1 integrado es falso (su máscara)."""
    from captura import Captura
    from ensamblar import analizar
    from pipeline.clustering import cluster_hotspots
    from pipeline.detection_context import (dual_roi_contextual_dnti_hot_mask, first_pass_tests_2_and_3,
                                            second_pass_adjacent)
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    nti, nti_app, bt, dist, c = _campo()
    ii, jj = np.indices(bt.shape)
    lat = -23.30 - ii * DLAT
    lon = -67.70 + jj * DLAT / math.cos(math.radians(23.3))
    cap = Captura()
    cap.reset()
    roi = np.ones(bt.shape, bool)
    ctx = cap.envolver_dnti_ctx(dual_roi_contextual_dnti_hot_mask)(
        nti=nti, bt=bt, roi_mask=roi, dist_km=dist, roi1_mask=None, t_bg=265.0, c1_summit=0.003, c1_scene=0.010,
        inner_km=1.0, bt_sanity_k=3.0, apply_unsuitable_filters=True)
    disco = dist <= 1.2
    cap.envolver_test1(lambda **kw: {"triggered": True, "mask_contributing": disco})(bt=bt, lat=lat, lon=lon)
    hot, diag = cap.envolver_first_pass(first_pass_tests_2_and_3)(**_kw_fp(nti, nti_app, bt, dist))
    fin = cap.envolver_second_pass(second_pass_adjacent)(
        nti=nti, eti=diag["eti"], active_mask=hot, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5.0, c2_deti=5.0,
        is_summit=dist <= 1.0, c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10.0, c2_deti_scene=10.0,
        conditioned=False, use_prose_branch=False)
    vrp = np.where(bt > 265.0, (bt - 265.0) * 0.01, 0.0)
    vlat, vlon = float(lat[c, c]), float(lon[c, c])
    cl = cap.envolver_cluster(cluster_hotspots)(fin, lat, lon, vlat, vlon, vrp_per_pixel=vrp * fin,
                                                 strategy="vent_anchored", inner_radius_km=5)
    cap.envolver_prioridad(lambda **kw: test1_publica)(x=1)
    top = cl[0]
    if test1_publica:
        sal = cap.envolver_ctx(apply_contextual_test1_filter)(disco, ctx, keep_peak_rc=(c, c))
        cl = cap.envolver_cluster(cluster_hotspots)(sal, lat, lon, vlat, vlon, connectivity=8, vrp_per_pixel=vrp * sal,
                                                     strategy="vent_anchored", inner_radius_km=5)
        top = cl[0]
    cap.record = {"sensor": "VIIRS_SNPP", "t_bg_k": 265.0,
                  "primary_cluster": {"n_pixels": top["n_pixels"], "vrp_mw": 0.5, "single_pixel_mode": False,
                                      "centroid_lat": round(top["centroid_lat"], 5),
                                      "centroid_lon": round(top["centroid_lon"], 5)},
                  "anomaly_pixels": [{"lat": round(float(lat[ij]), 5), "lon": round(float(lon[ij]), 5), "dist_km": 1.0,
                                      "bt_k": round(float(bt[ij]), 2), "vrp_mw": float(vrp[ij])} for ij in top["pixel_indices"]]}
    x = {"osf": {"vrp_mw": 5.0, "Npix": 4, "lat": vlat, "lon": vlon}}
    vol = {"inner_radius_km": 5, "radius_km": 25, "vent_lat": vlat, "vent_lon": vlon}
    return analizar({"vent": {}}, vol, x, cap, filtro_distancia=True), c


def test_ensamblado_contextual_con_funciones_reales():
    f, c = _flujo(test1_publica=False)
    assert f["publicado"]["ruta"] == "contextual"
    r = f["resumen"]
    assert r["replica_ok"] is True and r["alineacion_bt"] is True
    v = {tuple(x["ij"]): x for x in r["vecinos"]}
    assert v[(c, c + 1)]["incluido"], "el vecino frío entra por el segundo pase, que no tiene compuerta"
    fuera = [x for x in r["vecinos"] if x["caliente"] and not x["incluido"]]
    assert fuera and all(x["limitante"].endswith("_2p") or "_2p+" in x["limitante"] for x in fuera)


def test_ensamblado_test1_con_funciones_reales():
    f, c = _flujo(test1_publica=True)
    assert f["publicado"]["ruta"] == "test1"
    assert f["corrio"]["dnti_ctx"] and f["corrio"]["cumulo_test1"]
    r = f["resumen"]
    assert r["replica_ok"] is True and r["alineacion_bt"] is True
    fuera = [x for x in r["vecinos"] if x["caliente"] and not x["incluido"]]
    assert fuera and all(set(x["limitante"].split("+")) <= {"test1_disco", "dnti_ctx", "bt_ctx", "no_apto_ctx", "fuera_roi"}
                         for x in fuera)
    assert f["hoy"]["f5_replica_mw"] == pytest.approx(f["hoy"]["f5_pipeline_mw"])


# ---------------------------------------------------------------- 8. criterio

def test_constantes_pre_registradas():
    import analisis_v2 as a
    assert (a.RADIO_FOCO_KM, a.N_MIN_VOLCAN, a.MIN_VOLCANES, a.FRAC_DOMINANTE, a.FRAC_VOLCANES) == (0.75, 3, 3, 0.6, 2 / 3)
    assert (a.CONTRASTE_MIN_K, a.CIERRA, a.NO_CIERRA, a.C1_MIN, a.C2_MIN, a.ANILLO_CONTROL_KM) == \
        (1.0, 0.5, 0.2, 0.9, 0.95, (3.0, 6.0))


def _fila(vol, regimen="focal", ruta="contextual", lim="dnti_2p", n_perdidos=2, exc=3.0, exc_ctl=0.0, frac=0.6,
          frac_fondo=0.1, clase="candidato", identificado=True, ambiguo=False, foco_ok=True, npix=4, n_hoy=1,
          f5=(0.1, 0.1), alineacion=True, replica=True, motivo=None, error=None):
    vec = [{"ij": [0, k], "caliente": True, "incluido": False, "limitante": lim, "margen_limitante_rel": -0.3}
           for k in range(n_perdidos)]
    vec.append({"ij": [1, 0], "caliente": True, "incluido": True, "limitante": None, "margen_limitante_rel": None})
    return {"volcan": vol, "regimen": regimen, "clase": clase, "ok": True, "error_analisis": error,
            "osf": {"Npix": npix, "vrp_mw": 1.0},
            "publicado": {"identificado": identificado, "ambiguo": ambiguo, "ruta": ruta, "motivo": motivo},
            "hoy": {"n_publicado": n_hoy, "f5_replica_mw": f5[0], "f5_pipeline_mw": f5[1]},
            "resumen": {"grilla_ok": True, "foco_ok": foco_ok, "vecinos": vec, "exceso_mediano_calientes_k": exc,
                        "control": {"exceso_mediano_calientes_k": exc_ctl}, "fraccion_brecha": frac,
                        "fraccion_fondo": frac_fondo, "alineacion_bt": alineacion, "replica_ok": replica}}


def test_criterio_patron_estable_con_tres_volcanes():
    from analisis_v2 import evaluar
    e = evaluar([_fila(v) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)], "focal")
    assert e["control"]["estado"] == "OK"
    assert e["limitante"] == "PATRON:contextual:dnti_2p"
    assert e["contraste"] == "VECINOS_TIBIOS" and e["fondo_vecinos"] == "CIERRA" and e["fondo_cumulo"] == "NO_CIERRA"
    assert e["justifica_brazo"] is True
    assert e["por_volcan"]["Lascar"]["margen_rel_mediano"] == pytest.approx(-0.3)


def test_criterio_un_volcan_con_mucho_peso_no_sostiene_el_patron():
    from analisis_v2 import evaluar
    filas = [_fila("NevadosDeChillan", "nevado", ruta="test1", lim="test1_disco", n_perdidos=8) for _ in range(3)]
    filas += [_fila(v, "nevado", n_perdidos=1) for v in ("Villarrica", "Chaiten", "Llaima") for _ in range(3)]
    e = evaluar(filas, "nevado")
    assert e["limitante"] == "HETEROGENEO" and e["justifica_brazo"] is False


def test_criterio_dejando_un_volcan_fuera_cambia_la_limitante():
    from analisis_v2 import evaluar
    filas = [_fila("Lascar", n_perdidos=6) for _ in range(3)] + [_fila("Isluga", n_perdidos=1) for _ in range(3)]
    filas += [_fila("Lastarria", ruta="test1", lim="dnti_ctx", n_perdidos=2) for _ in range(3)]
    e = evaluar(filas, "focal")
    assert e["loo"]["limitante"]["Lascar"] != "contextual:dnti_2p"
    assert e["limitante"] == "HETEROGENEO"


def test_criterio_minimo_de_pasadas_y_de_volcanes():
    from analisis_v2 import evaluar
    filas = [_fila(v) for v in ("Lascar", "Isluga") for _ in range(3)] + [_fila("Lastarria") for _ in range(2)]
    e = evaluar(filas, "focal")
    assert e["por_volcan"]["Lastarria"]["evaluable"] is False
    assert e["veredicto"] == "INDETERMINADO:pocos_volcanes"


def test_control_del_instrumento_c1_c3_c4():
    from analisis_v2 import evaluar
    perfectas = [_fila(v) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)]
    c = evaluar(perfectas)["control"]
    assert (c["c1"], c["c2"], c["c3"], c["c4"], c["estado"]) == (1.0, 1.0, 1.0, 1.0, "OK")
    # H4: una pasada sin cúmulo hoy no es falla del instrumento; un error del análisis sí lo es.
    sin_cumulo = _fila("Lascar", identificado=False, motivo="sin_primary_cluster")
    c = evaluar(perfectas + [sin_cumulo])["control"]
    assert c["c1"] == 1.0 and c["n_sin_primary_cluster"] == 1
    c = evaluar(perfectas + [_fila("Lascar", error="KeyError")])["control"]
    assert c["c1"] == pytest.approx(9 / 10)
    assert evaluar(perfectas + [_fila("Lascar", alineacion=False)])["control"]["estado"] == "FALLA"
    assert evaluar(perfectas + [_fila("Lascar", replica=None)])["control"]["c4"] < 1.0
    assert evaluar(perfectas + [_fila("Lascar", replica=False)])["veredicto"] == "INDETERMINADO:instrumento"


def test_fila_valida_cuenta_cada_motivo():
    from analisis_v2 import evaluar, fila_valida
    assert fila_valida(_fila("Lascar")) == (True, None)
    assert fila_valida(_fila("Lascar", foco_ok=False))[1] == "foco_mirova_lejos_hoy"
    assert fila_valida(_fila("Lascar", n_hoy=4))[1] == "ya_no_publica_menos"
    assert fila_valida(_fila("Lascar", identificado=False, motivo="sin_primary_cluster"))[1] == "sin_primary_cluster"
    assert fila_valida(_fila("Lascar", error="x"))[1] == "error_analisis"
    assert fila_valida(_fila("Lascar", clase="control"))[1] == "control"
    assert evaluar([_fila("Lascar"), _fila("Lascar", foco_ok=False)])["motivos_fuera"] == {"foco_mirova_lejos_hoy": 1}


def test_sin_contraste_no_justifica_brazo():
    from analisis_v2 import evaluar
    e = evaluar([_fila(v, exc=0.4, exc_ctl=0.2) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)])
    assert e["contraste"] == "SIN_CONTRASTE" and e["justifica_brazo"] is False


# ---------------------------------------------------------------- 9. runner, workflow, pre-registro

def _llamadas(src, nombre):
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9_.])" + re.escape(nombre) + r"\s*\(", src):
        k, prof = m.end(), 1
        while prof:
            prof += {"(": 1, ")": -1}.get(src[k], 0)
            k += 1
        out.append(src[m.end():k - 1])
    return out


def test_a89_nombres_parcheados_existen_en_process_viirs():
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import pipeline.process_viirs as pv
    for n in ("compute_test1_mir", "apply_contextual_test1_filter", "first_pass_tests_2_and_3", "second_pass_adjacent",
              "cluster_hotspots", "read_viirs_l1b", "calculate_vrp", "resolve_test1_source_priority",
              "dual_roi_contextual_dnti_hot_mask", "select_test1_effective_lbg"):
        assert callable(getattr(pv, n, None)), n


def test_a89_llamadas_distinguibles_en_el_fuente():
    src = open(os.path.join(ROOT, "pipeline", "process_viirs.py"), encoding="utf-8").read()
    cl = [c for c in _llamadas(src, "cluster_hotspots") if "hot_mask" in c or "test1_hot" in c]
    assert len(cl) == 2 and sum("connectivity=" in c for c in cl) == 1
    assert "connectivity=" in [c for c in cl if "test1_hot_filtered" in c][0]
    assert sum("active_mask=" in c for c in _llamadas(src, "second_pass_adjacent")) == 1
    assert len(_llamadas(src, "dual_roi_contextual_dnti_hot_mask")) == 1
    assert len(_llamadas(src, "first_pass_tests_2_and_3")) == 1


def test_runner_como_script_no_cierra_stdout():
    env = dict(os.environ, PROBE_VOL="VolcanQueNoExiste", VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(V2, "probe_vecinos_v2.py")], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert "closed file" not in r.stderr, r.stderr[-800:]
    assert r.returncode == 0, r.stderr[-800:]
    assert "flags de la taxonomía verificados" in r.stdout
    assert "sin pasadas" in r.stdout


def test_yml_pipefail_on_entre_comillas_y_no_pushea():
    txt = open(YML, encoding="utf-8").read()
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d
    assert "set -o pipefail" in txt and "probe_vecinos_v2.py" in txt
    assert "git push" not in txt and "contents: write" not in txt and "pyhdf" not in txt


def test_yml_matriz_cubre_los_volcanes_de_la_muestra():
    d = yaml.safe_load(open(YML, encoding="utf-8"))
    matriz = set(d["jobs"]["probe"]["strategy"]["matrix"]["vol"])
    assert matriz == {x["volcan"] for x in json.load(open(os.path.join(V2, "pasadas.json"), encoding="utf-8"))}


def test_hipotesis_pre_registrada_antes_de_correr():
    txt = open(os.path.join(ROOT, "docs", "HYPOTHESIS_LOG.md"), encoding="utf-8").read()
    k = txt.find("## H_S141_VECINO_FOCO_V2")
    assert k >= 0
    bloque = txt[k:k + 6000]
    assert "imposible por construcción" in bloque and "Estado**: abierta" in bloque


def test_juntar_aplica_el_criterio_sobre_los_artefactos(tmp_path):
    from juntar import resumen_total
    for k, v in enumerate(("Lascar", "Isluga", "Lastarria") * 3):
        p = tmp_path / f"s141-v2-{v}" / f"{v}_{k}.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(_fila(v)), encoding="utf-8")
    (tmp_path / "s141-v2-Lascar" / "criterio.json").write_text("{}", encoding="utf-8")
    out = resumen_total(tmp_path)
    assert out["n_filas"] == 9 and set(out["criterio"]) == {"total", "focal", "nevado"}
    assert out["criterio"]["focal"]["limitante"] == "PATRON:contextual:dnti_2p"
