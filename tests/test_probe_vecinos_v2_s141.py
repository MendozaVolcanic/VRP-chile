# -*- coding: utf-8 -*-
"""S141, Fase 1: tests del instrumento v2 del vecino del foco (VIIRS 375 m).

POR QUÉ. El v1 dio INDETERMINADO y el verificador le encontró ocho defectos
(`experiments/_s141_fase1_probe/VERIFICADOR.md` §4 y §6). Cada test de aquí fija una de las
ocho correcciones, o una de las dos trampas operativas del v1 (runner que cerraba stdout al
correr como script, yml sin pipefail que dejaba verde un crash). Lo que tiene que ser verdad
antes de gastar una corrida en CI:

  1. la muestra filtra por la posición del foco de MIROVA y excluye las pasadas del v1;
  2. la captura distingue las dos rutas y guarda qué etapas corrieron, sin inferirlo de None;
  3. el cúmulo publicado se identifica contra el record, no por la última llamada;
  4. el centro es nuestro píxel pico, el núcleo F5 se replica y la brecha es de la misma corrida;
  5. el fondo local usa la máscara de alertas de la ruta publicada, no el halo del Test 1;
  6. el contraste usa un píxel de control lejos del foco, con fondo simétrico;
  7. el criterio es por volcán, con mínimo, y ningún volcán solo sostiene un patrón;
  8. el control del instrumento se puede aprobar por construcción.

Plan y criterio pre-registrado: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md
"""
import json
import math
import os
import re
import subprocess
import sys

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


def _km(lat1, lon1, lat2, lon2):
    r = math.pi / 180
    a = (math.sin((lat2 - lat1) * r / 2) ** 2
         + math.cos(lat1 * r) * math.cos(lat2 * r) * math.sin((lon2 - lon1) * r / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------- 1. muestra

def _pares():
    t = pd.date_range("2025-03-01 05:00", periods=8, freq="3D")
    lat0, lon0 = VENT_LASCAR
    lejos = lat0 + 15 / 111.195                                     # 15 km al norte
    filas = []
    for k in range(8):
        filas.append(dict(vol="Lascar", res=375, Npix=4, pub_n=1, t_osf=t[k], t_ours=t[k] + pd.Timedelta(minutes=2),
                          sensor="VIIRS_SNPP", osf_mw=1.0, pub_mw=0.4, satzen=20.0, pc_n=1, t_bg=260.0,
                          lat=lat0, lon=lon0, pico_lat=lat0, pico_lon=lon0))
    filas[1]["lat"] = lejos                                          # foco de MIROVA en otra anomalía
    filas[2].update(lat=lat0 + 3 / 111.195, pico_lat=lat0 + 3 / 111.195)  # lejos del cráter, junto a nuestro pico
    filas[3]["lat"] = float("nan")                                   # sin posición en el OSF
    filas.append(dict(filas[0], t_osf=t[7] + pd.Timedelta(days=3), t_ours=t[7] + pd.Timedelta(days=3, minutes=2),
                      Npix=3, pub_n=3))                              # control
    return pd.DataFrame(filas)


def test_muestra_filtra_por_posicion_del_foco_de_mirova_y_reporta_excluidas():
    from muestra import seleccionar
    out = seleccionar(_pares(), vents={"Lascar": VENT_LASCAR}, excluir=set(), por_volcan=10, controles_por_volcan=10)
    exc = {x["pasada_utc"]: x for x in out["excluidas"]}
    assert "2025-03-04 05:02" in exc and exc["2025-03-04 05:02"]["motivo"] == "foco_mirova_lejos"
    assert exc["2025-03-04 05:02"]["dist_foco_crater_km"] == pytest.approx(15.0, abs=0.1)
    assert exc["2025-03-10 05:02"]["motivo"] == "sin_posicion_osf"
    usadas = {x["pasada_utc"] for x in out["pasadas"]}
    assert "2025-03-07 05:02" in usadas, "el foco junto a nuestro pico entra aunque esté lejos del cráter"
    for x in out["pasadas"]:
        assert min(x["osf"]["dist_crater_km"], x["osf"]["dist_pico_km"]) <= 0.75


def test_muestra_excluye_las_pasadas_del_v1_y_es_determinista():
    from muestra import seleccionar
    d = _pares()
    excluir = {("Lascar", "2025-03-01 05:02")}
    a = seleccionar(d, vents={"Lascar": VENT_LASCAR}, excluir=excluir, por_volcan=3, controles_por_volcan=1)
    b = seleccionar(d, vents={"Lascar": VENT_LASCAR}, excluir=excluir, por_volcan=3, controles_por_volcan=1)
    assert a == b
    assert ("Lascar", "2025-03-01 05:02") not in {(x["volcan"], x["pasada_utc"]) for x in a["pasadas"]}
    assert any(x["motivo"] == "pasada_del_v1" for x in a["excluidas"])
    cand = [x for x in a["pasadas"] if x["clase"] == "candidato"]
    ctl = [x for x in a["pasadas"] if x["clase"] == "control"]
    assert len(cand) == 3 and len(ctl) == 1
    assert all(x["pasada_utc"].count(":") == 1 for x in a["pasadas"]), "formato del probe S135"


def test_muestra_commiteada_no_repite_el_v1_y_respeta_el_radio():
    nueva = json.load(open(os.path.join(V2, "pasadas.json"), encoding="utf-8"))
    vieja = json.load(open(os.path.join(V1, "pasadas.json"), encoding="utf-8"))
    assert nueva, "la muestra v2 no puede estar vacía"
    assert not ({(x["volcan"], x["pasada_utc"]) for x in nueva} & {(x["volcan"], x["pasada_utc"]) for x in vieja})
    assert all(min(x["osf"]["dist_crater_km"], x["osf"]["dist_pico_km"]) <= 0.75 for x in nueva)


# ---------------------------------------------------------------- 2. captura

def _grilla(n=41):
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    lat = -23.30 - i * DLAT
    lon = -67.70 + j * DLAT / math.cos(math.radians(23.3))
    return lat, lon


def test_captura_rotula_la_ruta_del_cumulo_y_copia_la_entrada():
    from captura import Captura
    cap = Captura()
    lat, lon = _grilla(4)
    salida = [{"n_pixels": 2, "centroid_lat": 1.0, "centroid_lon": 2.0, "centroid_dist_km": 0.1, "vrp_mw": 0.3,
               "pixel_indices": [(1, 1), (1, 2)]}]
    f = cap.envolver_cluster(lambda *a, **kw: salida)
    m = np.zeros((4, 4), bool)
    m[1, 1] = m[1, 2] = True
    v = np.zeros((4, 4))
    f(m, lat, lon, 0.0, 0.0, vrp_per_pixel=v, strategy="vent_anchored", inner_radius_km=5)   # process_viirs.py:1467
    f(m, lat, lon, 0.0, 0.0, connectivity=8, vrp_per_pixel=v, strategy="vent_anchored",       # process_viirs.py:1910
      inner_radius_km=5)
    m[0, 0] = True
    ev = cap.de_tipo("cluster")
    assert [e["ruta"] for e in ev] == ["contextual", "test1"]
    assert ev[0]["clusters"][0]["pixel_indices"] == [(1, 1), (1, 2)]
    assert not ev[0]["entrada"][0, 0], "la máscara de entrada se copia"
    assert ev[0]["seq"] < ev[1]["seq"]


def test_captura_etapas_que_corrieron_son_booleanos_y_no_se_infieren_de_none():
    from captura import Captura
    cap = Captura()
    c = cap.corrio()
    assert c and all(v is False for v in c.values()), c
    fp = cap.envolver_first_pass(lambda **kw: (np.zeros((3, 3), bool), {"n_first_pass_pixels": 0}))
    fp(bt=np.zeros((3, 3)))
    sp = cap.envolver_second_pass(lambda *a, **kw: np.zeros((3, 3), bool))
    sp(None, None, np.zeros((3, 3), bool))                          # posicional: ETI de escena, :1149
    c = cap.corrio()
    assert c["first_pass"] is True, "corrió aunque quedó vacío"
    assert c["second_pass_por_nombre"] is False, "la llamada posicional no es el segundo pase de :1287"
    sp(nti=None, eti=None, active_mask=np.zeros((3, 3), bool))
    assert cap.corrio()["second_pass_por_nombre"] is True
    cap.reset()
    assert all(v is False for v in cap.corrio().values())


# ---------------------------------------------------------------- 3. publicado

def _ev(seq, ruta, n, clat, clon, idx, forma=(41, 41)):
    e = np.zeros(forma, bool)
    for a, b in idx:
        e[a, b] = True
    return {"tipo": "cluster", "seq": seq, "ruta": ruta, "entrada": e, "vrp_per_pixel": np.zeros(forma),
            "clusters": [{"n_pixels": n, "centroid_lat": clat, "centroid_lon": clon, "pixel_indices": idx}] if idx else []}


def test_publicado_se_identifica_contra_el_record_y_no_por_la_ultima_llamada():
    from analisis_v2 import identificar_publicado
    ctx = _ev(1, "contextual", 3, -23.10000, -67.20000, [(5, 5), (5, 6), (6, 5)])
    t1 = _ev(2, "test1", 1, -23.20000, -67.30000, [(9, 9)])
    pc = {"n_pixels": 3, "centroid_lat": -23.1, "centroid_lon": -67.2, "single_pixel_mode": True, "vrp_mw": 0.1}
    p = identificar_publicado([ctx, t1], pc)
    assert p["identificado"] and not p["ambiguo"] and p["ruta"] == "contextual"
    assert p["indices"] == [(5, 5), (5, 6), (6, 5)]
    vacio = _ev(3, "test1", 0, None, None, [])                      # V8: Test 1 que vuelve vacío no publica
    assert identificar_publicado([ctx, vacio], pc)["ruta"] == "contextual"
    assert identificar_publicado([ctx, t1], {"n_pixels": 7, "centroid_lat": 0.0, "centroid_lon": 0.0})["identificado"] is False
    otro = _ev(4, "test1", 3, -23.10000, -67.20000, [(1, 1), (1, 2), (2, 1)])
    assert identificar_publicado([ctx, otro], pc)["ambiguo"] is True


def test_nucleo_f5_replica_coincide_con_el_pipeline_y_da_el_conteo():
    from analisis_v2 import n_publicado_hoy, nucleo_f5
    from pipeline.f5_core import f5_core_vrp_mw
    lat0, lon0 = VENT_LASCAR
    rec = {"primary_cluster": {"centroid_lat": lat0, "centroid_lon": lon0, "n_pixels": 3, "single_pixel_mode": True},
           "anomaly_pixels": [
               {"lat": lat0, "lon": lon0, "bt_k": 300.0, "vrp_mw": 0.30},                 # pico
               {"lat": lat0 + DLAT, "lon": lon0, "bt_k": 280.0, "vrp_mw": 0.05},          # a 0,375 km: núcleo
               {"lat": lat0 + 4 * DLAT, "lon": lon0, "bt_k": 296.0, "vrp_mw": 0.04},      # 1,5 km pero ≥ 295 K
               {"lat": lat0 + 4 * DLAT, "lon": lon0 + 0.01, "bt_k": 270.0, "vrp_mw": 0.02}]}
    r = nucleo_f5(rec, 5.0)
    assert r["total"] == pytest.approx(f5_core_vrp_mw(rec, 5.0))
    assert r["n"] == 3
    assert n_publicado_hoy(rec, r) == 3
    sin = dict(rec, anomaly_pixels=[])
    assert nucleo_f5(sin, 5.0) == {"total": None, "n": None, "pixeles": []}
    assert n_publicado_hoy(sin, nucleo_f5(sin, 5.0)) == 1, "single_pixel_mode publica el píxel máximo"
    rec2 = dict(sin, primary_cluster=dict(rec["primary_cluster"], single_pixel_mode=False))
    assert n_publicado_hoy(rec2, nucleo_f5(rec2, 5.0)) == 3


# ---------------------------------------------------------------- 4. rótulos por ruta

def test_rotulo_dentro_de_la_ruta():
    from analisis_v2 import rotular
    assert rotular(True, True, True) == "incluido"
    assert rotular(False, True, False) == "alertado_fuera_del_cumulo"
    assert rotular(False, False, True) == "marcado_y_quitado"
    assert rotular(False, False, False) == "nunca_marcado"


def test_marcado_por_pixel_nunca_usa_la_mascara_del_test1():
    from analisis_v2 import marcado_por_pixel
    forma = (5, 5)

    def m(*ij):
        x = np.zeros(forma, bool)
        for a, b in ij:
            x[a, b] = True
        return x
    ev = [{"tipo": "first_pass", "hot": m((0, 0))},
          {"tipo": "second_pass", "via_kw": True, "salida": m((0, 0), (0, 1))},
          {"tipo": "second_pass", "via_kw": False, "salida": m((4, 4))},
          {"tipo": "test1", "mask_contributing": m((2, 2), (2, 3), (3, 3))},
          {"tipo": "ctx_filter", "dnti_ctx": m((2, 2), (1, 1))}]
    assert np.array_equal(marcado_por_pixel("contextual", ev, forma), m((0, 0), (0, 1)))
    assert np.array_equal(marcado_por_pixel("test1", ev, forma), m((2, 2), (1, 1)))
    assert not marcado_por_pixel("test1", [], forma).any()


def _escena():
    lat, lon = _grilla()
    bt = np.full(lat.shape, 270.0)
    bt[20, 20] = 300.0
    bt[20, 21] = 290.0                     # vecino más caliente, dentro del cúmulo publicado (pico de BT)
    bt[19, 20] = 285.0                     # vecino tibio, marcado y quitado
    bt[21, 20] = 284.0                     # vecino tibio, nunca marcado
    bt[20, 22] = 279.0                     # halo del Test 1, fuera de la ruta: debe entrar al fondo local
    bt[20, 33] = 276.0                     # píxel de control: el más caliente del anillo 3 a 6 km
    return lat, lon, bt


def _publicado(ruta="contextual"):
    lat, lon, bt = _escena()
    entrada = np.zeros(bt.shape, bool)
    entrada[20, 20] = entrada[20, 21] = True
    vrp = np.zeros(bt.shape)
    vrp[20, 20], vrp[20, 21] = 0.2, 0.5    # el pico de VRP no es el píxel más cercano al OSF
    return {"ruta": ruta, "indices": [(20, 20), (20, 21)], "entrada": entrada, "vrp_per_pixel": vrp}


def _resumen(**kw):
    from analisis_v2 import resumir_pasada
    lat, lon, bt = _escena()
    marcado = np.zeros(bt.shape, bool)
    marcado[20, 20] = marcado[20, 21] = marcado[19, 20] = True
    halo = np.zeros(bt.shape, bool)
    halo[20, 22] = True
    base = dict(bt=bt, lat=lat, lon=lon, publicado=_publicado(), marcado=marcado, npix_osf=4,
                osf_lat=float(lat[20, 20]), osf_lon=float(lon[20, 20]),
                vent_lat=float(lat[20, 20]), vent_lon=float(lon[20, 20]),
                brecha_mw=1.0, t_bg_anillo_k=268.0, mask_contributing=halo)
    base.update(kw)
    return resumir_pasada(**base)


def test_centro_es_el_pico_del_cumulo_publicado_y_la_distancia_al_osf_es_variable_de_pareo():
    r = _resumen()
    assert r["grilla_ok"] is True
    assert r["centro"] == [20, 21]
    assert r["dist_centro_osf_km"] == pytest.approx(0.375, abs=0.02)
    assert r["foco_ok"] is True


def test_foco_ok_falla_si_el_osf_esta_lejos_del_pico_de_hoy_y_del_crater():
    lat, lon, _ = _escena()
    r = _resumen(osf_lat=float(lat[0, 0]), osf_lon=float(lon[0, 0]))
    assert r["foco_ok"] is False
    assert r["dist_osf_crater_km"] > 5


def test_rotulos_del_resumen_y_consistencia_con_el_cumulo():
    r = _resumen()
    por_ij = {tuple(v["ij"]): v for v in r["vecinos"]}
    # centro (20,21): sus vecinos incluyen (20,20) del cúmulo
    assert por_ij[(20, 20)]["rotulo"] == "incluido"
    assert por_ij[(20, 22)]["rotulo"] == "nunca_marcado"
    assert por_ij[(20, 22)]["en_mask_contributing"] is True, "el halo del Test 1 se guarda, pero no marca"
    assert r["consistencia_rotulos"] is True


def test_consistencia_detecta_un_rotulo_roto():
    from analisis_v2 import consistencia_rotulos
    vec = [{"ij": [1, 1], "rotulo": "incluido"}, {"ij": [1, 2], "rotulo": "nunca_marcado"}]
    assert consistencia_rotulos(vec, [(1, 1), (0, 0)], centro=(0, 0)) is True
    assert consistencia_rotulos(vec, [(1, 2), (0, 0)], centro=(0, 0)) is False
    assert consistencia_rotulos(vec, [(1, 1)], centro=(0, 0)) is False, "el centro tiene que estar en el cúmulo"


def test_fondo_local_usa_la_mascara_de_la_ruta_y_no_excluye_el_halo_del_test1():
    from analisis_v2 import fondo_local_k, planck_i04
    r = _resumen()
    lat, lon, bt = _escena()
    v = {tuple(x["ij"]): x for x in r["vecinos"]}[(20, 22)]
    # (21,21) tiene en su entorno al halo del Test 1 (20,22), que no es alerta de la ruta: entra al fondo.
    # Sus vecinos alertados (20,20) y (20,21) no entran.
    ls =[planck_i04(bt[a, b]) for a, b in ((20, 22), (21, 22), (22, 20), (22, 21), (22, 22), (21, 20))]
    esperado = 14388.0 / (3.74 * math.log(1 + 1.191042e8 / (3.74 ** 5 * (sum(ls) / len(ls)))))
    alerta = _publicado()["entrada"]
    assert fondo_local_k(bt, alerta, 21, 21) == pytest.approx(esperado, abs=1e-6)
    assert v["fondo_local_k"] is not None


def test_contraste_con_pixel_de_control_lejos_del_foco_y_fondo_simetrico():
    r = _resumen()
    c = r["control"]
    assert c["ij"] == [20, 33]
    assert 3.0 <= c["dist_km"] <= 6.0
    # los vecinos del control están a 270 K y su fondo excluye al control (276 K): exceso 0.
    assert c["exceso_mediano_calientes_k"] == pytest.approx(0.0, abs=1e-6)
    assert r["exceso_mediano_calientes_k"] > 1.0
    assert r["exceso_mediano_restantes_k"] is not None


def test_fraccion_de_brecha_suma_solo_los_calientes_no_incluidos():
    r = _resumen()
    perd = sum(v["aporte_local_mw"] for v in r["vecinos"] if v["caliente"] and v["rotulo"] != "incluido")
    assert r["aporte_perdido_local_mw"] == pytest.approx(perd)
    assert r["fraccion_brecha"] == pytest.approx(perd / 1.0)
    assert sum(v["caliente"] for v in r["vecinos"]) == 3, "Npix 4 del OSF: los 3 vecinos más calientes"
    assert _resumen(brecha_mw=-0.2)["fraccion_brecha"] is None


def test_grilla_distinta_se_marca():
    from analisis_v2 import resumir_pasada
    lat, lon, bt = _escena()
    p = _publicado()
    p["entrada"] = np.zeros((5, 5), bool)
    r = resumir_pasada(bt=bt, lat=lat, lon=lon, publicado=p, marcado=np.zeros(bt.shape, bool), npix_osf=4,
                       osf_lat=0.0, osf_lon=0.0, vent_lat=0.0, vent_lon=0.0, brecha_mw=1.0, t_bg_anillo_k=268.0)
    assert r["grilla_ok"] is False


# ---------------------------------------------------------------- 4b. ensamblado sintético por ruta

def _ensamblado(test1_publica):
    """Recorre las llamadas en el orden de process_viirs.py (Test 1 :1099, primer pase :1240, segundo pase
    :1287, cúmulo contextual :1467, prioridad :1712, filtro :1798, cúmulo Test 1 :1910) con funciones falsas."""
    from captura import Captura
    lat, lon, bt = _escena()
    forma = bt.shape

    def m(*ij):
        x = np.zeros(forma, bool)
        for a, b in ij:
            x[a, b] = True
        return x

    def cum(idx, vrp):
        return [{"n_pixels": len(idx), "centroid_lat": float(np.mean([lat[ij] for ij in idx])),
                 "centroid_lon": float(np.mean([lon[ij] for ij in idx])), "vrp_mw": sum(vrp[ij] for ij in idx),
                 "pixel_indices": idx}]
    cap = Captura()
    cap.reset()
    cap.envolver_test1(lambda **kw: {"triggered": True, "mask_contributing": m((20, 20), (20, 21), (19, 20), (20, 22))})(
        bt=bt, lat=lat, lon=lon)
    fp = m((20, 20), (19, 20))
    cap.envolver_first_pass(lambda **kw: (fp, {}))(bt=bt)
    cap.envolver_second_pass(lambda **kw: kw["active_mask"])(nti=None, eti=None, active_mask=fp)
    v_ctx = np.zeros(forma)
    v_ctx[20, 20], v_ctx[19, 20] = 0.2, 0.1
    ctx = cap.envolver_cluster(lambda *a, **kw: cum([(20, 20), (19, 20)], v_ctx))(
        fp, lat, lon, 0.0, 0.0, vrp_per_pixel=v_ctx, strategy="vent_anchored", inner_radius_km=5)
    cap.envolver_prioridad(lambda **kw: test1_publica)(cluster_vrp_mw=0.3)
    idx_pub, vpub, c = [(20, 20), (19, 20)], v_ctx, ctx[0]
    if test1_publica:
        v_t1 = np.zeros(forma)
        v_t1[20, 20], v_t1[20, 21] = 0.2, 0.5
        salida = cap.envolver_ctx(lambda t, d, keep_peak_rc=None: m((20, 20), (20, 21)))(
            m((20, 20), (20, 21), (19, 20), (20, 22)), m((20, 20)), keep_peak_rc=(20, 21))
        t1 = cap.envolver_cluster(lambda *a, **kw: cum([(20, 20), (20, 21)], v_t1))(
            salida, lat, lon, 0.0, 0.0, connectivity=8, vrp_per_pixel=v_t1, strategy="vent_anchored", inner_radius_km=5)
        idx_pub, vpub, c = [(20, 20), (20, 21)], v_t1, t1[0]
    cap.record ={"sensor": "VIIRS_SNPP", "t_bg_k": 268.0,
                  "primary_cluster": {"n_pixels": 2, "vrp_mw": 0.5, "single_pixel_mode": True,
                                      "centroid_lat": round(c["centroid_lat"], 5), "centroid_lon": round(c["centroid_lon"], 5)},
                  "anomaly_pixels": [{"lat": round(float(lat[ij]), 5), "lon": round(float(lon[ij]), 5),
                                      "bt_k": float(bt[ij]), "vrp_mw": float(vpub[ij])} for ij in idx_pub]}
    x = {"osf": {"vrp_mw": 1.0, "Npix": 4, "lat": float(lat[20, 20]), "lon": float(lon[20, 20])}}
    vol = {"inner_radius_km": 5, "vent_lat": float(lat[20, 20]), "vent_lon": float(lon[20, 20])}
    return analizar_(dict(vent={}), vol, x, cap)


def analizar_(fila, vol, x, cap):
    from ensamblar import analizar
    return analizar(fila, vol, x, cap)


def test_ensamblado_ruta_test1_publica_y_los_vecinos_se_rotulan_dentro_de_ella():
    f = _ensamblado(test1_publica=True)
    assert f["publicado"]["identificado"] and not f["publicado"]["ambiguo"]
    assert f["publicado"]["ruta"] == "test1"
    assert f["corrio"] == {"first_pass": True, "second_pass_por_nombre": True, "test1": True, "test1_disparo": True,
                           "filtro_contextual": True, "cumulo_contextual": True, "cumulo_test1": True}
    assert f["test1_gana"] is True
    assert f["hoy"]["f5_replica_mw"] == pytest.approx(f["hoy"]["f5_pipeline_mw"])
    assert f["hoy"]["n_publicado"] == 2
    assert f["hoy"]["brecha_mw"] == pytest.approx(1.0 - f["hoy"]["f5_pipeline_mw"])
    r = f["resumen"]
    assert r["centro"] == [20, 21] and r["consistencia_rotulos"] is True
    v = {tuple(x["ij"]): x for x in r["vecinos"]}
    # (19,20) pasó el primer pase contextual y está en la máscara del Test 1, pero en la ruta que publicó
    # (Test 1) ningún test por píxel lo marcó: el v1 lo habría rotulado "perdido en el filtro".
    assert v[(19, 20)]["rotulo"] == "nunca_marcado"
    assert v[(19, 20)]["en_mask_contributing"] is True


def test_ensamblado_ruta_contextual_publica_cuando_el_test1_no_corre():
    f = _ensamblado(test1_publica=False)
    assert f["publicado"]["ruta"] == "contextual"
    assert f["corrio"]["cumulo_test1"] is False and f["corrio"]["filtro_contextual"] is False
    r = f["resumen"]
    assert r["centro"] == [20, 20]
    assert {tuple(x["ij"]): x for x in r["vecinos"]}[(19, 20)]["rotulo"] == "incluido"


# ---------------------------------------------------------------- 5. criterio

def test_constantes_pre_registradas():
    import analisis_v2 as a
    assert (a.RADIO_FOCO_KM, a.N_MIN_VOLCAN, a.MIN_VOLCANES, a.FRAC_DOMINANTE, a.FRAC_VOLCANES) == (0.75, 3, 3, 0.6, 2 / 3)
    assert (a.CONTRASTE_MIN_K, a.CIERRA, a.NO_CIERRA, a.C1_MIN, a.C2_MIN, a.ANILLO_CONTROL_KM) == \
        (1.0, 0.5, 0.2, 0.9, 0.95, (3.0, 6.0))


def _fila(vol, regimen="focal", ruta="contextual", rotulo="nunca_marcado", n_perdidos=2, exc=3.0, exc_ctl=0.0,
          frac=0.6, clase="candidato", identificado=True, ambiguo=False, foco_ok=True, npix=4, n_hoy=1,
          f5=(0.1, 0.1), consistencia=True):
    vec = [{"ij": [0, k], "caliente": True, "rotulo": rotulo} for k in range(n_perdidos)]
    vec.append({"ij": [1, 0], "caliente": True, "rotulo": "incluido"})
    return {"volcan": vol, "regimen": regimen, "clase": clase, "ok": True,
            "osf": {"Npix": npix, "vrp_mw": 1.0},
            "publicado": {"identificado": identificado, "ambiguo": ambiguo, "ruta": ruta},
            "hoy": {"n_publicado": n_hoy, "f5_replica_mw": f5[0], "f5_pipeline_mw": f5[1]},
            "resumen": {"grilla_ok": True, "foco_ok": foco_ok, "vecinos": vec, "exceso_mediano_calientes_k": exc,
                        "control": {"exceso_mediano_calientes_k": exc_ctl}, "fraccion_brecha": frac,
                        "consistencia_rotulos": consistencia}}


def test_criterio_patron_estable_con_tres_volcanes():
    from analisis_v2 import evaluar
    filas = [_fila(v) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)]
    e = evaluar(filas, "focal")
    assert e["control"]["estado"] == "OK"
    assert e["n_volcanes_evaluables"] == 3
    assert e["destino"] == "PATRON:contextual:nunca_marcado"
    assert e["contraste"] == "VECINOS_TIBIOS"
    assert e["fondo"] == "CIERRA"
    assert e["justifica_brazo"] is True


def test_criterio_un_volcan_con_mucho_peso_no_sostiene_el_patron():
    """Lo que pasó con Nevados de Chillán en el v1: un volcán con muchos vecinos domina el agregado."""
    from analisis_v2 import evaluar
    filas = [_fila("NevadosDeChillan", "nevado", ruta="test1", rotulo="alertado_fuera_del_cumulo", n_perdidos=8)
             for _ in range(3)]
    filas += [_fila(v, "nevado", n_perdidos=1) for v in ("Villarrica", "Chaiten", "Llaima") for _ in range(3)]
    e = evaluar(filas, "nevado")
    assert e["destino"] == "HETEROGENEO"
    assert e["justifica_brazo"] is False


def test_criterio_dejando_un_volcan_fuera_cambia_el_destino():
    from analisis_v2 import evaluar
    filas = [_fila("Lascar", n_perdidos=6) for _ in range(3)]
    filas += [_fila("Isluga", n_perdidos=1) for _ in range(3)]
    filas += [_fila("Lastarria", ruta="test1", rotulo="alertado_fuera_del_cumulo", n_perdidos=2) for _ in range(3)]
    e = evaluar(filas, "focal")
    assert e["loo"]["destino"]["Lascar"] != "contextual:nunca_marcado"
    assert e["destino"] == "HETEROGENEO"


def test_criterio_minimo_de_pasadas_por_volcan_y_de_volcanes():
    from analisis_v2 import evaluar
    filas = [_fila(v) for v in ("Lascar", "Isluga") for _ in range(3)] + [_fila("Lastarria") for _ in range(2)]
    e = evaluar(filas, "focal")
    assert e["por_volcan"]["Lastarria"]["evaluable"] is False
    assert e["n_volcanes_evaluables"] == 2
    assert e["veredicto"] == "INDETERMINADO:pocos_volcanes"


def test_control_del_instrumento_alcanzable_y_bloqueante():
    from analisis_v2 import evaluar
    perfectas = [_fila(v) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)]
    c = evaluar(perfectas)["control"]
    assert (c["c1"], c["c2"], c["c3"], c["estado"]) == (1.0, 1.0, 1.0, "OK")
    rotas = perfectas + [_fila("Lascar", ambiguo=True)]
    assert evaluar(rotas)["control"]["c1"] == pytest.approx(9 / 10)
    rotas += [_fila("Isluga", f5=(0.1, 0.3)), _fila("Isluga", consistencia=False)]
    e = evaluar(rotas)
    assert e["control"]["estado"] == "FALLA"
    assert e["veredicto"] == "INDETERMINADO:instrumento"


def test_fila_valida_cuenta_cada_motivo():
    from analisis_v2 import evaluar, fila_valida
    assert fila_valida(_fila("Lascar")) == (True, None)
    assert fila_valida(_fila("Lascar", foco_ok=False))[1] == "foco_mirova_lejos_hoy"
    assert fila_valida(_fila("Lascar", n_hoy=4))[1] == "ya_no_publica_menos"
    assert fila_valida(_fila("Lascar", identificado=False))[1] == "publicado_no_identificado"
    assert fila_valida(_fila("Lascar", clase="control"))[1] == "control"
    e = evaluar([_fila("Lascar"), _fila("Lascar", foco_ok=False)])
    assert e["motivos_fuera"] == {"foco_mirova_lejos_hoy": 1}


def test_sin_contraste_no_justifica_brazo():
    from analisis_v2 import evaluar
    filas = [_fila(v, exc=0.4, exc_ctl=0.2) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)]
    e = evaluar(filas)
    assert e["contraste"] == "SIN_CONTRASTE"
    assert e["justifica_brazo"] is False


# ---------------------------------------------------------------- 6. runner y workflow

def _llamadas(src, nombre):
    """Texto de cada llamada a `nombre(` con paréntesis balanceados; frontera de palabra (A92)."""
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
              "cluster_hotspots", "read_viirs_l1b", "calculate_vrp", "resolve_test1_source_priority"):
        assert callable(getattr(pv, n, None)), n


def test_a89_llamadas_de_cluster_distinguibles():
    """La ruta se reconoce por `connectivity=`: sólo la llamada del Test 1 (:1910) lo pasa. Y el segundo
    pase de la ruta contextual (:1287) es la única llamada con `active_mask=` por nombre."""
    src = open(os.path.join(ROOT, "pipeline", "process_viirs.py"), encoding="utf-8").read()
    cl = [c for c in _llamadas(src, "cluster_hotspots") if "hot_mask" in c or "test1_hot" in c]
    assert len(cl) == 2, cl
    assert sum("connectivity=" in c for c in cl) == 1
    assert "connectivity=" in [c for c in cl if "test1_hot_filtered" in c][0]
    sp = _llamadas(src, "second_pass_adjacent")
    assert sum("active_mask=" in c for c in sp) == 1


def test_runner_como_script_no_cierra_stdout():
    """Corrida 34928488409 (v1): el runner envolvía sys.stdout y S135 lo volvía a envolver; el primer
    envoltorio quedaba huérfano y cerraba la salida. Sólo se reproduce corriendo el archivo como script."""
    env = dict(os.environ, PROBE_VOL="VolcanQueNoExiste", VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(V2, "probe_vecinos_v2.py")], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert "closed file" not in r.stderr, r.stderr[-800:]
    assert r.returncode == 0, r.stderr[-800:]
    assert "sin pasadas" in r.stdout


def test_yml_pipefail_on_entre_comillas_y_no_pushea():
    txt = open(YML, encoding="utf-8").read()
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d, "A43"
    assert "set -o pipefail" in txt
    assert "git push" not in txt and "contents: write" not in txt and "pyhdf" not in txt
    assert "probe_vecinos_v2.py" in txt


def test_yml_matriz_cubre_los_volcanes_de_la_muestra():
    d = yaml.safe_load(open(YML, encoding="utf-8"))
    matriz = set(d["jobs"]["probe"]["strategy"]["matrix"]["vol"])
    muestra = {x["volcan"] for x in json.load(open(os.path.join(V2, "pasadas.json"), encoding="utf-8"))}
    assert matriz == muestra


def test_juntar_aplica_el_criterio_sobre_los_artefactos(tmp_path):
    from juntar import resumen_total
    import analisis_v2
    for k, v in enumerate(("Lascar", "Isluga", "Lastarria") * 3):
        p = tmp_path / f"s141-v2-{v}" / f"{v}_{k}.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(_fila(v)), encoding="utf-8")
    (tmp_path / "s141-v2-Lascar" / "criterio.json").write_text("{}", encoding="utf-8")
    out = resumen_total(tmp_path)
    assert out["n_filas"] == 9
    directo = analisis_v2.evaluar([_fila(v) for v in ("Lascar", "Isluga", "Lastarria") for _ in range(3)], "focal")
    assert out["criterio"]["focal"]["destino"] == directo["destino"] == "PATRON:contextual:nunca_marcado"
    assert set(out["criterio"]) == {"total", "focal", "nevado"}
