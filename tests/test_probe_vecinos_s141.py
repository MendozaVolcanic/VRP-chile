# -*- coding: utf-8 -*-
"""S141, Fase 1: tests del probe por etapa del vecino del foco (VIIRS 375 m).

Lo que tiene que ser verdad antes de gastar una corrida en CI: el pareo OSF expone las horas,
la muestra es determinista, el análisis clasifica bien la etapa de pérdida sobre escenas
sintéticas construidas a mano, el criterio pre-registrado da cada veredicto en su caso, los
nombres parcheados existen en process_viirs (A89) y el yml no pushea (A43).
Plan: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROBE_DIR = os.path.join(ROOT, "experiments", "_s141_fase1_probe")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, PROBE_DIR)


# ---------- Task 1: el pareo expone las horas de la pasada ----------

def test_build_expone_horas_de_la_pasada():
    import scripts.descomponer_magnitud_osf as m
    if not m.OSF_DEFECTO.exists():
        pytest.skip("OSF no disponible en este entorno")
    m.cargar(str(m.OSF_DEFECTO))
    d = m.build(0)
    assert {"t_osf", "t_ours"} <= set(d.columns)
    delta = (pd.to_datetime(d.t_ours) - pd.to_datetime(d.t_osf)).dt.total_seconds() / 60
    assert np.allclose(delta, d.dt_min)


# ---------- Task 2: selector determinista ----------

def _pares_sinteticos():
    t = pd.date_range("2025-03-01 05:00", periods=12, freq="3D")
    return pd.DataFrame({
        "vol": ["Lascar"] * 8 + ["Villarrica"] * 4, "res": [375] * 12,
        "Npix": [4, 3, 5, 3, 6, 3, 3, 4, 3, 3, 1, 3], "pub_n": [1, 1, 1, 1, 1, 1, 6, 4, 1, 1, 1, 3],
        "t_osf": t, "t_ours": t + pd.Timedelta(minutes=2), "sensor": ["VIIRS_SNPP"] * 12,
        "osf_mw": 1.0, "pub_mw": 0.5, "satzen": 20.0, "pc_n": 1, "t_bg": 260.0,
        "lat": -23.37, "lon": -67.73,
    })


def test_selector_toma_candidatos_y_controles_deterministas():
    from seleccionar_pasadas import seleccionar
    d = _pares_sinteticos()
    a = seleccionar(d, por_volcan=2, controles_por_volcan=1)
    b = seleccionar(d, por_volcan=2, controles_por_volcan=1)
    assert a == b, "la muestra debe ser determinista"
    cand = [x for x in a if x["clase"] == "candidato"]
    ctl = [x for x in a if x["clase"] == "control"]
    assert cand and ctl
    assert all(x["osf"]["Npix"] >= 3 and x["persistido"]["pub_n"] == 1 for x in cand)
    assert all(x["persistido"]["pub_n"] >= x["osf"]["Npix"] >= 3 for x in ctl)
    assert sum(x["volcan"] == "Lascar" for x in cand) == 2
    assert {x["regimen"] for x in a} <= {"focal", "nevado"}
    assert all(x["pasada_utc"].count(":") == 1 for x in a), "formato YYYY-MM-DD HH:MM del probe S135"


# ---------- Task 3: análisis puro ----------

def test_etapa_de_perdida_en_cada_caso():
    from analisis_vecinos import ORDEN, etapa_de_perdida
    assert etapa_de_perdida({"first_pass": True, "second_pass": True, "test1": True,
                             "ctx_filter_out": True, "cluster": True}) == "incluido"
    assert etapa_de_perdida({e: False for e in ORDEN}) == "nunca_candidato"
    assert etapa_de_perdida({"first_pass": False, "second_pass": False, "test1": True,
                             "ctx_filter_out": False, "cluster": False}) == "perdido_en_ctx_filter_out"
    assert etapa_de_perdida({"first_pass": True, "second_pass": None, "test1": None,
                             "ctx_filter_out": None, "cluster": False}) == "perdido_en_cluster"


def test_aporte_y_fondo_local():
    from analisis_vecinos import aporte_mw, fondo_local_k
    assert aporte_mw(300.0, 300.0) == 0.0
    assert aporte_mw(310.0, 300.0) > 0
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 300.0
    bt[2, 3] = 290.0            # vecino alertado: no entra al fondo
    alertado = np.zeros((5, 5), bool)
    alertado[2, 2] = alertado[2, 3] = True
    assert fondo_local_k(bt, alertado, 2, 2) == pytest.approx(270.0, abs=0.01)


def test_resumir_vecindario_escena_sintetica():
    from analisis_vecinos import resumir_vecindario
    bt = np.full((7, 7), 260.0)
    bt[3, 3], bt[3, 4], bt[2, 3] = 300.0, 275.0, 272.0
    lat, lon = np.meshgrid(np.linspace(-23.30, -23.40, 7), np.linspace(-67.70, -67.80, 7), indexing="ij")
    z = np.zeros((7, 7), bool)
    fp = z.copy(); fp[3, 3] = True
    t1 = z.copy(); t1[3, 3] = t1[3, 4] = True
    ctx = z.copy(); ctx[3, 3] = True
    cl = z.copy(); cl[3, 3] = True
    r = resumir_vecindario(bt, lat, lon, {"first_pass": fp, "second_pass": fp, "test1": t1,
                                          "ctx_filter_out": ctx, "cluster": cl},
                           osf_lat=lat[3, 3], osf_lon=lon[3, 3], t_bg_anillo=268.0)
    assert r["grilla_ok"] is True
    assert r["centro"] == [3, 3]
    assert r["conteo"]["perdido_en_ctx_filter_out"] == 1      # (3,4): Test 1 lo tenía, keep_peak lo sacó
    assert r["conteo"]["nunca_candidato"] == 7
    # (2,3) a 272 K: con el anillo a 268 K aporta; con fondo local (vecinos a 260 K) aporta más.
    assert r["aporte_perdidos_fondo_local_mw"] > r["aporte_perdidos_fondo_anillo_mw"]


def test_grilla_distinta_se_marca():
    from analisis_vecinos import resumir_vecindario
    bt = np.full((5, 5), 260.0)
    lat = lon = np.zeros((5, 5))
    r = resumir_vecindario(bt, lat, lon, {"first_pass": np.zeros((4, 4), bool)}, 0.0, 0.0, 260.0)
    assert r["grilla_ok"] is False


def _fila(clase, conteo, cierre, regimen="focal"):
    return {"ok": True, "clase": clase, "regimen": regimen,
            "resumen": {"grilla_ok": True, "conteo": conteo, "fraccion_brecha_fondo_local": cierre}}


def test_criterio_palanca_fondo_y_control():
    from analisis_vecinos import evaluar_criterio
    cand = [_fila("candidato", {"perdido_en_ctx_filter_out": 3, "nunca_candidato": 1, "incluido": 0}, 0.6)
            for _ in range(10)]
    ctl = [_fila("control", {"incluido": 6, "nunca_candidato": 2}, None) for _ in range(2)]
    c = evaluar_criterio(cand + ctl)
    assert c["etapa"] == "PALANCA:perdido_en_ctx_filter_out"
    assert c["fondo"] == "FONDO_LOCAL_CIERRA_BRECHA"
    assert c["control"] == "OK"
    assert c["veredicto"] != "INDETERMINADO"


def test_criterio_cuenta_candidatos_que_hoy_publican_otro_conteo():
    """P3: la muestra sale de records del backfill; el código de hoy puede publicar otro conteo."""
    from analisis_vecinos import evaluar_criterio
    cand = [_fila("candidato", {"nunca_candidato": 8}, 0.1) for _ in range(3)]
    cand[0]["hoy"] = {"pc_n": 1}
    cand[1]["hoy"] = {"pc_n": 3}
    c = evaluar_criterio(cand)
    assert c["candidatos_hoy_pc_n_1"] == 1 and c["candidatos_hoy_pc_n_otro"] == 1


def test_criterio_indeterminado_si_control_falla_o_n_chico():
    from analisis_vecinos import evaluar_criterio
    cand = [_fila("candidato", {"nunca_candidato": 8}, 0.1) for _ in range(10)]
    ctl = [_fila("control", {"nunca_candidato": 8}, None)]
    assert evaluar_criterio(cand + ctl)["veredicto"] == "INDETERMINADO"
    assert evaluar_criterio(cand[:5] + [_fila("control", {"incluido": 8}, None)])["veredicto"] == "INDETERMINADO"


# ---------- Task 4: runner y workflow ----------

def test_a89_nombres_parcheados_existen():
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import pipeline.process_viirs as pv
    for n in ("compute_test1_mir", "apply_contextual_test1_filter", "first_pass_tests_2_and_3",
              "second_pass_adjacent", "cluster_hotspots", "read_viirs_l1b", "calculate_vrp"):
        assert callable(getattr(pv, n, None)), n


def test_runner_como_script_no_cierra_stdout():
    """Corrida 34928488409: el runner envolvía sys.stdout y el probe S135 lo volvía a envolver al
    importarse; el primer envoltorio quedaba huérfano, al recolectarse cerraba el buffer, y
    run_pipeline.py fallaba con 'I/O operation on closed file' antes de procesar una sola pasada.
    Se reproduce corriendo el archivo como script (el import desde un test no toca __main__)."""
    import subprocess
    env = dict(os.environ, PROBE_VOL="VolcanQueNoExiste", VRP_PROFILE="mirova_equivalent",
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(PROBE_DIR, "probe_vecinos.py")], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert "closed file" not in r.stderr, r.stderr[-800:]
    assert r.returncode == 0, r.stderr[-800:]
    assert "sin pasadas" in r.stdout


def test_yml_con_pipefail_para_que_un_crash_no_salga_verde():
    """En la misma corrida el job salió success con el script caído: `python ... | tee` sin
    pipefail devuelve el código de tee."""
    txt = open(os.path.join(ROOT, ".github", "workflows", "probe-s141-vecinos.yml"), encoding="utf-8").read()
    assert "set -o pipefail" in txt


def test_yml_no_pushea_y_on_entre_comillas():
    p = os.path.join(ROOT, ".github", "workflows", "probe-s141-vecinos.yml")
    txt = open(p, encoding="utf-8").read()
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d, "A43: la clave on debe ir entre comillas"
    assert "git push" not in txt and "contents: write" not in txt
    assert "pyhdf" not in txt
