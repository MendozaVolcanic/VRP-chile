# -*- coding: utf-8 -*-
"""S176: la guardia K de los dos VIIRS (perfil, workflow y revisión de su corrida), PR A del encendido de las vías.

POR QUÉ. Nicolás decidió (2026-11-08) preparar el encendido de la vía «código MIROVA» en VIIRS 375 y VIIRS 750 calcando
MODIS: K corre aparte como guardia y si la vía calla una alerta protegida se revierte el mismo día (diseño
docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 2 y 7). La guardia sólo sirve si mide K de
verdad: una guardia que heredara la vía publicaría lo mismo que producción y nunca dispararía. Estas pruebas fijan lo
que puede fallar en silencio.
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

PERFIL = "guardia_k_viirs"
WF = ROOT / ".github" / "workflows" / "guardia-k-viirs.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
GUARDIA_MODIS_WF = ROOT / ".github" / "workflows" / "guardia-k-modis.yml"


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
def test_la_guardia_resuelve_k_en_los_dos_viirs_y_carpeta_propia():
    g = _resuelto(PERFIL)
    assert g["ENABLE_V375_CODIGO_MIROVA"] == "False", "la guardia es K: la vía de VIIRS 375 va apagada"
    assert g["ENABLE_V750_CODIGO_MIROVA"] == "False", "la guardia es K: la vía de VIIRS 750 va apagada"
    assert g["DATA_SUBDIR"] == repr(PERFIL) and g["PROFILE_NAME"] == repr(PERFIL)
    # los flags de K, con el valor de producción (S153)
    assert g["ENABLE_TEST1_PATH"] == "False" and g["ENABLE_TESTS_23_PROSE_BRANCH"] == "True"


def test_la_guardia_corre_solo_los_dos_viirs():
    g = _resuelto(PERFIL)
    assert (g["SENSOR_MODIS"], g["SENSOR_VIIRS_375"], g["SENSOR_VIIRS_750"]) == ("False", "True", "True")
    cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert cfg["extends"] == "mirova_equivalent"
    assert cfg["thresholds"]["enable_v375_codigo_mirova"] is False
    assert cfg["thresholds"]["enable_v750_codigo_mirova"] is False


def test_la_guardia_difiere_de_produccion_solo_en_las_vias_los_sensores_y_la_carpeta():
    """Cualquier otra diferencia haría que la guardia midiera otro paquete que el K de producción."""
    prod, g = _resuelto("mirova_equivalent"), _resuelto(PERFIL)
    distintas = {k for k in set(prod) | set(g) if prod.get(k) != g.get(k)}
    # Con los flags de producción apagados (PR A) las vías de VIIRS no difieren; con B1 y B2 encendidos, sí. La de
    # MODIS está encendida en producción y apagada aquí porque la guardia no corre MODIS.
    permitidas = {"DATA_SUBDIR", "PROFILE_NAME", "SENSOR_MODIS", "ENABLE_V375_CODIGO_MIROVA",
                  "ENABLE_V750_CODIGO_MIROVA", "ENABLE_MODIS_CODIGO_MIROVA"}
    assert distintas <= permitidas, sorted(distintas - permitidas)
    assert {"DATA_SUBDIR", "PROFILE_NAME", "SENSOR_MODIS"} <= distintas


def test_ningun_otro_perfil_escribe_en_la_carpeta_de_la_guardia():
    otros = []
    for f in sorted((ROOT / "pipeline" / "profiles").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if f.stem != PERFIL and ((cfg.get("output") or {}).get("data_subdir") == PERFIL):
            otros.append(f.stem)
    assert not otros


def test_produccion_no_nombra_la_guardia():
    assert PERFIL not in NRT.read_text(encoding="utf-8")
    assert PERFIL not in (ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8")


def test_la_via_de_viirs_375_encendida_y_la_de_750_apagada_en_produccion():
    """PR A es inerte: encender un flag es B1 o B2. Esta prueba se cambia en esos PR, con la frase de Nicolás.

    S177 B1: enciende la vía de VIIRS 375 (A45 para escribirlo, dada a la coordinadora; merge y encendido siguen siendo
    de Nicolás). VIIRS 750 es B2. Nombre y texto originales: «las vías de VIIRS siguen apagadas en producción», los
    dos flags en False."""
    p = _resuelto("mirova_equivalent")
    assert p["ENABLE_V375_CODIGO_MIROVA"] == "True" and p["ENABLE_V750_CODIGO_MIROVA"] == "False"


# ------------------------------------------------------------------------------------- 2. el workflow
def _wf():
    txt = WF.read_text(encoding="utf-8")
    return txt, yaml.safe_load(txt)


def _paso_pipeline(d):
    return next(s for s in d["jobs"]["process"]["steps"] if "run_pipeline.py" in s.get("run", ""))


def _matriz(wf):
    return list(yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"]["process"]["strategy"]["matrix"]["volcano"])


def test_el_workflow_corre_una_vez_al_dia_con_despacho_manual():
    txt, d = _wf()
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    assert set(d["on"]) == {"workflow_dispatch", "schedule"}
    assert len(d["on"]["schedule"]) == 1
    assert d["on"]["workflow_dispatch"]["inputs"]["medir"]["default"] is False


def test_la_hora_no_choca_con_el_nrt_ni_con_la_guardia_de_modis():
    _, d = _wf()
    minuto, hora = d["on"]["schedule"][0]["cron"].split()[:2]
    assert minuto not in ("0", "30", "12", "20", "50", "7", "27", "45", "40"), "minutos ocupados por otros cron"
    gm = yaml.safe_load(GUARDIA_MODIS_WF.read_text(encoding="utf-8"))
    m_g, h_g = gm["on"]["schedule"][0]["cron"].split()[:2]
    fin_guardia_modis = int(h_g) * 60 + int(m_g) + gm["jobs"]["process"]["timeout-minutes"]
    assert int(hora) * 60 + int(minuto) > fin_guardia_modis


def test_los_volcanes_de_la_guardia_son_los_del_nrt():
    assert sorted(_matriz(WF)) == sorted(_matriz(NRT)) and len(_matriz(WF)) == 11


def test_el_workflow_afirma_el_perfil_desde_pipeline_profile_y_corta_por_token_vacio():
    txt, d = _wf()
    paso = _paso_pipeline(d)
    run = paso["run"]
    assert '-z "$EARTHDATA_TOKEN"' in run and run.index('-z "$EARTHDATA_TOKEN"') < run.index("run_pipeline.py")
    assert set(paso["env"]) >= {"EARTHDATA_TOKEN"}
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt       # A71: sólo token
    assert "--profile guardia_k_viirs" in run and "set -o pipefail" in run
    asercion = next(ln for ln in run.splitlines() if "VRP_PROFILE=guardia_k_viirs python -c" in ln)
    assert run.index(asercion) < run.index("run_pipeline.py")
    for pieza in ("p.DATA_SUBDIR == 'guardia_k_viirs'", "not p.ENABLE_V375_CODIGO_MIROVA",
                  "not p.ENABLE_V750_CODIGO_MIROVA", "not p.SENSOR_MODIS", "p.SENSOR_VIIRS_375", "p.SENSOR_VIIRS_750"):
        assert pieza in asercion, pieza
    assert paso["timeout-minutes"] >= 1.3 * 56 and d["jobs"]["process"]["timeout-minutes"] > paso["timeout-minutes"]


def test_la_asercion_del_workflow_pasa_con_la_guardia_y_cae_con_produccion_y_la_sombra():
    """Las dos preguntas del instrumento: la aserción tal cual está en el workflow pasa con el perfil de la guardia y cae
    con otro (la sombra trae las vías encendidas; producción escribe en otra carpeta)."""
    txt, d = _wf()
    run = _paso_pipeline(d)["run"]
    asercion = next(ln for ln in run.splitlines() if "VRP_PROFILE=guardia_k_viirs python -c" in ln)
    codigo = re.search(r'python -c "(.*)"\s*$', asercion).group(1)

    def correr(perfil):
        env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True,
                              text=True, encoding="utf-8").returncode
    assert correr(PERFIL) == 0
    assert correr("sombra_codigo_mirova") != 0 and correr("mirova_equivalent") != 0
    assert correr("guardia_k_modis") != 0


def test_el_workflow_commitea_solo_la_carpeta_de_la_guardia_con_grupo_propio_y_reintento():
    txt, d = _wf()
    commit = next(s for s in d["jobs"]["process"]["steps"] if "git push" in s.get("run", ""))
    assert re.findall(r'git add "([^"]+)"', commit["run"]) == ["data/guardia_k_viirs/${{ matrix.volcano }}.json"]
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
    i_rev = next(i for i, s in enumerate(pasos) if "scripts/revisar_guardia_viirs.py" in s.get("run", ""))
    assert i_rev > i_commit
    assert pasos[i_rev]["if"].startswith("always()") and "steps.correr.outputs.corrio == 'true'" in pasos[i_rev]["if"]
    assert "data/guardia_k_viirs/${{ matrix.volcano }}.json" in pasos[i_rev]["run"]
    i_tachar = next(i for i, s in enumerate(pasos) if "scripts/tachar_secreto_log.py" in s.get("run", ""))
    i_subir = next(i for i, s in enumerate(pasos) if "upload-artifact" in str(s.get("uses", "")))
    assert i_tachar < i_subir and "steps.tachar.outcome == 'success'" in pasos[i_subir]["if"]


# ------------------------------------------------------------------------------------- 3. la revisión de la corrida
DESDE = "2026-11-05T17:41:00Z"
COB = {"fallas": [], "plataformas": {"VIIRS_NOAA20": {}, "VIIRS_NOAA21": {}, "VIIRS_NOAA20_750": {},
                                     "VIIRS_NOAA21_750": {}}, "incidencias": []}


def _k(dt, sensor="VIIRS_NOAA20", proc="2026-11-05T17:50:00Z", perfil=PERFIL, **extra):
    return dict({"datetime_utc": dt, "sensor": sensor, "processed_utc": proc,
                 "regimen": {"perfil": perfil, "codigo_sha": "abc"}}, **extra)


AMBOS = [_k("2026-11-05 06:30"), _k("2026-11-05 06:30", sensor="VIIRS_NOAA20_750")]


def _rev(recs, log="", ini="2026-11-05", fin="2026-11-05", cob=COB, sha="abc", desde=DESDE):
    from revisar_guardia_viirs import revisar
    return revisar(recs, log, ini, fin, desde, cob, sha=sha)


def test_revision_verde_con_k_de_los_dos_viirs_escrito_en_esta_corrida():
    ok, resumen = _rev(AMBOS)
    assert ok is True, resumen


def test_revision_roja_si_falta_uno_de_los_dos_viirs():
    """Una guardia que dejó de escribir un sensor deja a ese sensor sin vigilar aunque el otro siga vivo."""
    ok, resumen = _rev(AMBOS[:1])
    assert ok is False and "VIIRS750" in resumen
    ok, resumen = _rev(AMBOS[1:])
    assert ok is False and "VIIRS375" in resumen


def test_revision_roja_si_esta_corrida_no_escribio_uno_de_los_dos_viirs():
    """El record de VIIRS 750 existe pero es de una corrida anterior: esta corrida no escribió ese sensor."""
    ok, resumen = _rev([AMBOS[0], dict(AMBOS[1], processed_utc="2026-11-04T17:50:00Z")])
    assert ok is False and "ningún record de VIIRS750 escrito" in resumen


def test_revision_roja_si_la_corrida_no_escribio_nada():
    ok, resumen = _rev([_k("2026-11-05 06:30", proc="2026-11-04T17:50:00Z"),
                        _k("2026-11-05 06:30", sensor="VIIRS_NOAA20_750", proc="2026-11-04T17:50:00Z")])
    assert ok is False and "no escribió" in resumen


def test_revision_roja_si_la_guardia_trae_records_de_la_via():
    """Una guardia con la vía no es K: guardia y producción dirían lo mismo y la vigilancia nunca dispararía."""
    for marca in (True, "sin_grilla"):
        ok, resumen = _rev(AMBOS + [_k("2026-11-05 07:10", via_codigo_mirova=marca)])
        assert ok is False and "vía" in resumen, marca


def test_revision_roja_si_la_guardia_trae_modis_u_otro_perfil():
    assert _rev(AMBOS + [_k("2026-11-05 06:31", sensor="MODIS_AQUA")])[0] is False
    assert _rev([dict(r, regimen={"perfil": "mirova_equivalent", "codigo_sha": "abc"}) for r in AMBOS])[0] is False


def test_revision_por_dia_un_dia_sin_viirs_es_falla_salvo_prueba_de_que_no_hubo_pasada():
    ok, resumen = _rev(AMBOS, ini="2026-11-04", fin="2026-11-05")
    assert ok is False and "2026-11-04" in resumen
    # prueba escrita de que una familia no tuvo pasada, y la otra sí escribió ese día
    recs = AMBOS + [_k("2026-11-04 06:30", proc="2026-11-05T17:50:00Z")]
    cob = dict(COB, incidencias=[{"tipo": "sin_granulos", "fecha": "2026-11-04", "plataforma": p}
                                 for p in COB["plataformas"] if p.endswith("_750")])
    ok, resumen = _rev(recs, ini="2026-11-04", fin="2026-11-05", cob=cob)
    assert ok is True and "NOTA" in resumen, resumen


def test_revision_roja_si_ningun_viirs_tuvo_pasada_el_mismo_dia():
    """Los dos VIIRS salen de los mismos satélites: si ninguno tiene pasada, es el catálogo vacío y no la órbita."""
    cob = dict(COB, incidencias=[{"tipo": "sin_granulos", "fecha": "2026-11-04", "plataforma": p}
                                 for p in COB["plataformas"]])
    ok, resumen = _rev(AMBOS, ini="2026-11-04", fin="2026-11-05", cob=cob)
    assert ok is False and "catálogo" in resumen


def test_revision_roja_con_error_de_granulo_o_cobertura_ausente():
    assert _rev(AMBOS, log="ERROR processing VJ102IMG...")[0] is False
    assert _rev(AMBOS, cob=None)[0] is False
    assert _rev(AMBOS, desde="")[0] is False


def test_revision_por_linea_de_comandos_no_cae_con_traceback(tmp_path):
    js = tmp_path / "g.json"
    js.write_text(json.dumps({"records": "no es lista"}), encoding="utf-8")
    cob = tmp_path / "c.json"
    cob.write_text(json.dumps(COB), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "revisar_guardia_viirs.py"), "--json", str(js),
                        "--log", str(tmp_path / "no.log"), "--cobertura-json", str(cob), "--ini", "2026-11-05",
                        "--fin", "2026-11-05", "--desde-utc", DESDE], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert r.returncode == 1 and "FALLA" in r.stdout and "Traceback" not in r.stderr
