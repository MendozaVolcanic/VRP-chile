# -*- coding: utf-8 -*-
"""S172: la guardia K de MODIS (perfil, workflow y revisión de su corrida), parte del PR A del encendido de MOD-D.

POR QUÉ. Nicolás decidió (2026-10-31) encender la vía «código MIROVA» de MODIS sin esperar la sombra de 28 noches, con
K corriendo aparte como guardia: si la vía calla una alerta protegida que K habría publicado, se revierte el mismo día
(experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §3 y §4, rama loop/activo; diseño
docs/superpowers/specs/2026-11-01-encendido-modd-design.md, decisión 2). La guardia sólo sirve si mide K de verdad:
estas pruebas fijan lo que puede fallar en silencio:
  1. el perfil resuelve K en MODIS (la vía apagada), sólo MODIS, en su propia carpeta, leído como lo lee el código
     (A89), y difiere de producción sólo en eso; si heredara la vía, la guardia sería producción y nunca dispararía;
  2. el workflow afirma el perfil desde pipeline.profile antes de correr, autentica sólo con token (A71), tiene grupo
     propio, commitea sólo su carpeta y revisa la corrida después del commit;
  3. la revisión de la corrida pone rojo una guardia que no escribió nada, que escribió records de la vía o que dejó
     un día sin MODIS sin prueba de que no hubo pasada.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

PERFIL = "guardia_k_modis"
WF = ROOT / ".github" / "workflows" / "guardia-k-modis.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
SOMBRA_WF = ROOT / ".github" / "workflows" / "sombra-codigo-mirova.yml"


def _resuelto(perfil):
    """Constantes de pipeline.profile resueltas en un proceso aparte con VRP_PROFILE (A89: nunca el YAML)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    codigo = ("import json, pipeline.profile as p; "
              "print(json.dumps({k: repr(sorted(v) if isinstance(v, (set, frozenset)) else v) "
              "for k, v in ((k, getattr(p, k)) for k in dir(p) if k.isupper())}, sort_keys=True))")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------------------------------- 1. el perfil
def test_la_guardia_resuelve_k_en_modis_solo_modis_y_carpeta_propia():
    g = _resuelto(PERFIL)
    assert g["ENABLE_MODIS_CODIGO_MIROVA"] == "False", "la guardia es K: la vía de MODIS va apagada"
    assert g["DATA_SUBDIR"] == repr(PERFIL)
    assert g["PROFILE_NAME"] == repr(PERFIL)
    # los tres flags de K, con el valor de producción (S153); MxD03 apagado como en producción
    assert g["ENABLE_TEST1_PATH"] == "False" and g["ENABLE_TESTS_23_PROSE_BRANCH"] == "True"
    assert g["ENABLE_MODIS_B22_PRIMARY"] == "True"
    for k in ("ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER"):
        assert g[k] == "False", k


def test_la_guardia_difiere_de_produccion_solo_en_la_via_los_sensores_y_la_carpeta():
    """Cualquier otra diferencia haría que la guardia midiera otro paquete que el K de producción."""
    prod, g = _resuelto("mirova_equivalent"), _resuelto(PERFIL)
    distintas = {k for k in set(prod) | set(g) if prod.get(k) != g.get(k)}
    # Con el flag de producción apagado (PR A), la vía no difiere; con el PR B encendido, sí. Los dos casos valen.
    permitidas = {"DATA_SUBDIR", "PROFILE_NAME", "SENSOR_VIIRS_375", "SENSOR_VIIRS_750",
                  "ENABLE_MODIS_CODIGO_MIROVA"}
    assert distintas <= permitidas, sorted(distintas - permitidas)
    assert {"DATA_SUBDIR", "PROFILE_NAME"} <= distintas


def test_la_guardia_corre_solo_modis():
    cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert cfg["extends"] == "mirova_equivalent"
    assert cfg["sensors"] == {"modis": True, "viirs_375": False, "viirs_750": False}
    assert cfg["thresholds"]["enable_modis_codigo_mirova"] is False
    # leído por el código, no por el YAML (A89)
    g = _resuelto(PERFIL)
    assert (g["SENSOR_MODIS"], g["SENSOR_VIIRS_375"], g["SENSOR_VIIRS_750"]) == ("True", "False", "False")


def test_ningun_otro_perfil_escribe_en_la_carpeta_de_la_guardia():
    otros = []
    for f in sorted((ROOT / "pipeline" / "profiles").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if f.stem != PERFIL and ((cfg.get("output") or {}).get("data_subdir") == PERFIL):
            otros.append(f.stem)
    assert not otros


# ------------------------------------------------------------------------------------- 2. el workflow
def _wf():
    txt = WF.read_text(encoding="utf-8")
    return txt, yaml.safe_load(txt)


def _matriz(wf):
    return list(yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"]["process"]["strategy"]["matrix"]["volcano"])


def _cron(wf):
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    return [c["cron"] for c in (d["on"].get("schedule") or [])]


def test_el_workflow_corre_una_vez_al_dia_con_despacho_manual():
    txt, d = _wf()
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    assert set(d["on"]) == {"workflow_dispatch", "schedule"}
    assert d["on"]["schedule"] == [{"cron": "40 17 * * *"}]
    assert d["on"]["workflow_dispatch"]["inputs"]["medir"]["default"] is False


def test_la_hora_no_choca_con_el_nrt_ni_con_la_sombra():
    """El NRT corre a la hora en punto (cron externo cada hora y nrt.yml cada 2 h), su reintento a las :30 de las horas
    impares, la sombra a las 15:00 con hasta 100 min de job. 17:40 queda después de la sombra y fuera de esos minutos."""
    minuto, hora = _cron(WF)[0].split()[:2]
    assert minuto not in ("0", "30", "12", "20", "50"), "minutos ocupados por nrt, nrt-retry, sync, watchdog, pages"
    m_sombra, h_sombra = _cron(SOMBRA_WF)[0].split()[:2]
    inicio_sombra = int(h_sombra) * 60 + int(m_sombra)
    fin_sombra = inicio_sombra + yaml.safe_load(SOMBRA_WF.read_text(encoding="utf-8"))["jobs"]["process"][
        "timeout-minutes"]
    assert int(hora) * 60 + int(minuto) > fin_sombra


def test_los_volcanes_de_la_guardia_son_los_del_nrt():
    assert sorted(_matriz(WF)) == sorted(_matriz(NRT)) and len(_matriz(WF)) == 11


def test_el_workflow_afirma_el_perfil_desde_pipeline_profile_y_corta_por_token_vacio():
    txt, d = _wf()
    paso = next(s for s in d["jobs"]["process"]["steps"] if "run_pipeline.py" in s.get("run", ""))
    run = paso["run"]
    assert '-z "$EARTHDATA_TOKEN"' in run and run.index('-z "$EARTHDATA_TOKEN"') < run.index("run_pipeline.py")
    assert set(paso["env"]) >= {"EARTHDATA_TOKEN"}
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt       # A71: sólo token
    assert "--profile guardia_k_modis" in run and "set -o pipefail" in run
    # la aserción lee pipeline.profile (A89) y corre ANTES del pipeline
    asercion = next(ln for ln in run.splitlines() if "VRP_PROFILE=guardia_k_modis python -c" in ln)
    assert run.index(asercion) < run.index("run_pipeline.py")
    for pieza in ("p.DATA_SUBDIR == 'guardia_k_modis'", "not p.ENABLE_MODIS_CODIGO_MIROVA", "p.SENSOR_MODIS",
                  "not (p.SENSOR_VIIRS_375 or p.SENSOR_VIIRS_750)", "p.ENABLE_MODIS_B22_PRIMARY"):
        assert pieza in asercion, pieza
    assert paso["timeout-minutes"] >= 1.3 * 56 and d["jobs"]["process"]["timeout-minutes"] > paso["timeout-minutes"]


def test_la_asercion_del_workflow_pasa_con_la_guardia_y_cae_con_produccion_y_la_sombra():
    """Las dos preguntas del instrumento: la aserción tal cual está en el workflow pasa con el perfil de la guardia y cae
    con otro (la sombra tiene la vía encendida y VIIRS; producción escribe en otra carpeta)."""
    txt, d = _wf()
    run = next(s for s in d["jobs"]["process"]["steps"] if "run_pipeline.py" in s.get("run", ""))["run"]
    asercion = next(ln for ln in run.splitlines() if "VRP_PROFILE=guardia_k_modis python -c" in ln)
    codigo = re.search(r'python -c "(.*)"\s*$', asercion).group(1)

    def correr(perfil):
        env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True,
                              text=True, encoding="utf-8").returncode
    assert correr(PERFIL) == 0
    assert correr("sombra_codigo_mirova") != 0 and correr("mirova_equivalent") != 0


def test_el_workflow_commitea_solo_la_carpeta_de_la_guardia_con_grupo_propio_y_reintento():
    txt, d = _wf()
    commit = next(s for s in d["jobs"]["process"]["steps"] if "git push" in s.get("run", ""))
    assert re.findall(r'git add "([^"]+)"', commit["run"]) == ["data/guardia_k_modis/${{ matrix.volcano }}.json"]
    assert commit["if"] == "steps.correr.outputs.commit == 'true'"
    grupo = d["concurrency"]["group"]
    otros = {(yaml.safe_load(p.read_text(encoding="utf-8")).get("concurrency") or {}).get("group")
             for p in (ROOT / ".github" / "workflows").glob("*.yml") if p != WF}
    assert grupo not in otros and grupo != "push-main" and d["concurrency"]["cancel-in-progress"] is False
    assert "for attempt in 1 2 3 4 5" in commit["run"]


def test_la_revision_corre_despues_del_commit_aunque_algo_falle():
    txt, d = _wf()
    pasos = d["jobs"]["process"]["steps"]
    i_commit = next(i for i, s in enumerate(pasos) if "git push" in s.get("run", ""))
    i_rev = next(i for i, s in enumerate(pasos) if "scripts/revisar_guardia_modis.py" in s.get("run", ""))
    assert i_rev > i_commit
    assert pasos[i_rev]["if"].startswith("always()") and "steps.correr.outputs.corrio == 'true'" in pasos[i_rev]["if"]
    assert "data/guardia_k_modis/${{ matrix.volcano }}.json" in pasos[i_rev]["run"]
    # el log se tacha antes de subirse, como en la sombra (VR2-03)
    nombres = [s.get("name", "") for s in pasos]
    i_tachar = next(i for i, s in enumerate(pasos) if "scripts/tachar_secreto_log.py" in s.get("run", ""))
    i_subir = next(i for i, s in enumerate(pasos) if "upload-artifact" in str(s.get("uses", "")))
    assert i_tachar < i_subir and "steps.tachar.outcome == 'success'" in pasos[i_subir]["if"], nombres


def test_produccion_no_nombra_la_guardia():
    assert PERFIL not in NRT.read_text(encoding="utf-8")
    assert PERFIL not in (ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------- 3. la revisión de la corrida
DESDE = "2026-11-05T17:41:00Z"
COB = {"fallas": [], "plataformas": {"MODIS_TERRA": {}, "MODIS_AQUA": {}}, "incidencias": []}


def _k(dt, sensor="MODIS_AQUA", proc="2026-11-05T17:50:00Z", perfil=PERFIL, **extra):
    return dict({"datetime_utc": dt, "sensor": sensor, "processed_utc": proc,
                 "regimen": {"perfil": perfil, "codigo_sha": "abc"}}, **extra)


def _rev(recs, log="", ini="2026-11-05", fin="2026-11-05", cob=COB, sha="abc", desde=DESDE):
    from revisar_guardia_modis import revisar
    return revisar(recs, log, ini, fin, desde, cob, sha=sha)


def test_revision_verde_con_k_de_modis_escrito_en_esta_corrida():
    ok, resumen = _rev([_k("2026-11-05 06:30")])
    assert ok is True, resumen


def test_revision_roja_si_la_corrida_no_escribio_nada():
    ok, resumen = _rev([_k("2026-11-05 06:30", proc="2026-11-04T17:50:00Z")])      # el de ayer no cuenta
    assert ok is False and "no escribió" in resumen


def test_revision_roja_si_la_guardia_trae_records_de_la_via():
    """Una guardia con la vía no es K: guardia y producción dirían lo mismo y la vigilancia nunca dispararía."""
    for marca in (True, "sin_mxd03"):
        ok, resumen = _rev([_k("2026-11-05 06:30"), _k("2026-11-05 07:10", via_codigo_mirova=marca)])
        assert ok is False and "vía" in resumen, marca


def test_revision_roja_si_la_guardia_trae_viirs_o_otro_perfil():
    assert _rev([_k("2026-11-05 06:30"), _k("2026-11-05 06:31", sensor="VIIRS_NOAA20")])[0] is False
    assert _rev([_k("2026-11-05 06:30", perfil="mirova_equivalent")])[0] is False


def test_revision_por_dia_un_dia_sin_modis_es_falla_salvo_prueba_de_que_no_hubo_pasada():
    recs = [_k("2026-11-05 06:30")]
    ok, resumen = _rev(recs, ini="2026-11-04", fin="2026-11-05")
    assert ok is False and "2026-11-04" in resumen
    # prueba escrita: las dos plataformas respondieron sin gránulos ese día
    cob = dict(COB, incidencias=[{"tipo": "sin_granulos", "fecha": "2026-11-04", "plataforma": p}
                                 for p in ("MODIS_TERRA", "MODIS_AQUA")])
    ok, resumen = _rev(recs, ini="2026-11-04", fin="2026-11-05", cob=cob)
    assert ok is True and "NOTA" in resumen, resumen


def test_revision_roja_con_error_de_granulo_o_cobertura_ausente():
    assert _rev([_k("2026-11-05 06:30")], log="ERROR processing MOD021KM...")[0] is False
    assert _rev([_k("2026-11-05 06:30")], cob=None)[0] is False
    assert _rev([_k("2026-11-05 06:30")], desde="")[0] is False


def test_revision_por_linea_de_comandos_no_cae_con_traceback(tmp_path):
    js = tmp_path / "g.json"
    js.write_text(json.dumps({"records": "no es lista"}), encoding="utf-8")
    cob = tmp_path / "c.json"
    cob.write_text(json.dumps(COB), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "revisar_guardia_modis.py"), "--json", str(js),
                        "--log", str(tmp_path / "no.log"), "--cobertura-json", str(cob), "--ini", "2026-11-05",
                        "--fin", "2026-11-05", "--desde-utc", DESDE], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert r.returncode == 1 and "FALLA" in r.stdout and "Traceback" not in r.stderr
