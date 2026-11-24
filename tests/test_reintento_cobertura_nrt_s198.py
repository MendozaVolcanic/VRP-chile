# -*- coding: utf-8 -*-
"""S198 (auditoría de Codex, ronda 2, F6-104, opción (b) aprobada por Nicolás el 2026-11-24): `nrt-retry.yml` también
reintenta las corridas VERDES del NRT que tuvieron búsquedas o descargas fallidas.

POR QUÉ. El NRT no corre en modo estricto: si CMR de NASA cae (el 2026-11-24 de 07:18 a 08:50 UTC respondió «An
Internal Error has occurred»), la corrida queda verde con un `::warning` de cobertura incompleta. `nrt-retry.yml` sólo
miraba corridas rojas, así que nunca reintentaba ésas; y pasados 8 días nadie vuelve a buscar el día (F6-114, ver
tests/test_barrido_huecos_s198.py). El reintento no agrega alarmas: el NRT sigue verde; sólo se relanza una corrida.

MECANISMO (estructurado, no texto libre). `run_pipeline.py` ya escribe la cobertura en JSON (`--cobertura-json`). El NRT
la resume por volcán (sólo números, fechas y etapas: ningún mensaje de error ni nada que pueda llevar un secreto) y la
sube como artefacto `cobertura-<volcán>`. `nrt-retry.yml` baja esos artefactos de la última corrida y decide con
`scripts/reintento_cobertura_nrt.py`.

TOPES. (a) Una corrida que ya es un reintento (la despachó `nrt-retry` con el GITHUB_TOKEN, actor `github-actions[bot]`)
no se reintenta por cobertura: no hay cadena. (b) Como mucho `MAX_REINTENTOS_24H` reintentos en 24 h: una falla
determinista (un gránulo roto en LAADS) no duplica el NRT por 8 días. (c) Sin dato (sin artefactos, sin actor, sin la
lista de corridas): no se reintenta. El camino de las corridas rojas por NASA_DOWN no cambia.

LAS DOS PREGUNTAS DEL INSTRUMENTO. ¿Puede dar rojo? Sí: antes del cambio el módulo no existe y el workflow no tiene el
camino verde. Controles: verde sin fallas, roja, reintento, tope cumplido y sin artefactos dan «no».
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

NRT = ROOT / ".github" / "workflows" / "nrt.yml"
RETRY = ROOT / ".github" / "workflows" / "nrt-retry.yml"

AHORA = datetime(2026, 11, 24, 9, 30, tzinfo=timezone.utc)


def _mod():
    import reintento_cobertura_nrt as m
    return m


def _run(id_=1, conclusion="success", actor="MendozaVolcanic", horas_atras=1.5, status="completed"):
    r = {"id": id_, "status": status, "conclusion": conclusion,
         "created_at": (AHORA - timedelta(hours=horas_atras)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if actor is not None:
        r["triggering_actor"] = {"login": actor}
    return r


CON_FALLAS = [{"volcan": "Lascar", "n_fallas": 3, "etapas": {"busqueda": 3}, "fechas": ["2026-11-24"]},
              {"volcan": "Llaima", "n_fallas": 0, "etapas": {}, "fechas": []}]
SIN_FALLAS = [{"volcan": "Lascar", "n_fallas": 0, "etapas": {}, "fechas": []}]


# ── resumir ──────────────────────────────────────────────────────────────────────────────────────

def test_resumir_deja_solo_conteos_fechas_y_etapas():
    cob = {"fallas": [{"volcan": "Lascar", "fecha": "2026-11-24", "plataforma": "VIIRS_SNPP", "producto": "X",
                       "etapa": "busqueda", "motivo": "RuntimeError: An Internal Error has occurred token=abc"},
                      {"volcan": "Lascar", "fecha": "2026-11-23", "plataforma": "MODIS_AQUA", "producto": "Y",
                       "etapa": "descarga", "motivo": "corte"},
                      {"volcan": "Lascar", "fecha": "2026-11-24", "plataforma": "MODIS_AQUA", "producto": "Y",
                       "etapa": "busqueda", "motivo": "otra"}],
           "n": 3, "incidencias": [{"tipo": "dia_parcial"}]}
    r = _mod().resumir(cob, "Lascar")
    assert r == {"volcan": "Lascar", "n_fallas": 3, "etapas": {"busqueda": 2, "descarga": 1},
                 "fechas": ["2026-11-23", "2026-11-24"]}
    assert "motivo" not in json.dumps(r) and "abc" not in json.dumps(r)


def test_resumir_sin_fallas_da_cero_aunque_haya_incidencias():
    """El día en curso es siempre parcial (incidencia): eso no es una falla y no debe reintentar."""
    r = _mod().resumir({"fallas": [], "n": 0, "incidencias": [{"tipo": "dia_parcial"}]}, "Lascar")
    assert r["n_fallas"] == 0


# ── decidir ──────────────────────────────────────────────────────────────────────────────────────

def test_verde_con_fallas_se_reintenta():
    ok, motivo = _mod().decidir_verde(_run(), [_run()], CON_FALLAS, ahora=AHORA)
    assert ok and "Lascar" in motivo


def test_control_verde_sin_fallas_no_se_reintenta():
    ok, _ = _mod().decidir_verde(_run(), [_run()], SIN_FALLAS, ahora=AHORA)
    assert not ok


@pytest.mark.parametrize("conclusion,status", [("failure", "completed"), ("cancelled", "completed"),
                                               ("", "in_progress")])
def test_control_no_verde_no_pasa_por_este_camino(conclusion, status):
    run = _run(conclusion=conclusion, status=status)
    ok, _ = _mod().decidir_verde(run, [run], CON_FALLAS, ahora=AHORA)
    assert not ok


def test_un_reintento_no_se_reintenta():
    run = _run(actor="github-actions[bot]")
    ok, motivo = _mod().decidir_verde(run, [run], CON_FALLAS, ahora=AHORA)
    assert not ok and "reintento" in motivo


def test_sin_actor_no_se_reintenta():
    run = _run(actor=None)
    ok, _ = _mod().decidir_verde(run, [run], CON_FALLAS, ahora=AHORA)
    assert not ok


def test_sin_artefactos_no_se_reintenta():
    ok, motivo = _mod().decidir_verde(_run(), [_run()], [], ahora=AHORA)
    assert not ok and "sin dato" in motivo.lower()


def test_tope_de_reintentos_en_24_horas():
    m = _mod()
    ultimo = _run(id_=100)
    previos = [_run(id_=i, actor="github-actions[bot]", horas_atras=2 + i) for i in range(m.MAX_REINTENTOS_24H)]
    ok, motivo = m.decidir_verde(ultimo, [ultimo] + previos, CON_FALLAS, ahora=AHORA)
    assert not ok and "tope" in motivo
    # control: los reintentos de hace más de 24 h no cuentan
    viejos = [_run(id_=i, actor="github-actions[bot]", horas_atras=25 + i) for i in range(m.MAX_REINTENTOS_24H)]
    ok, _ = m.decidir_verde(ultimo, [ultimo] + viejos, CON_FALLAS, ahora=AHORA)
    assert ok
    # control: uno menos que el tope deja reintentar
    ok, _ = m.decidir_verde(ultimo, [ultimo] + previos[1:], CON_FALLAS, ahora=AHORA)
    assert ok


def test_sin_lista_de_corridas_no_se_reintenta():
    ok, _ = _mod().decidir_verde(_run(), None, CON_FALLAS, ahora=AHORA)
    assert not ok


def test_cli_decidir_escribe_la_salida_de_github(tmp_path):
    m = _mod()
    (tmp_path / "runs.json").write_text(json.dumps({"workflow_runs": [_run(id_=7)]}), encoding="utf-8")
    d = tmp_path / "cob" / "cobertura-Lascar"
    d.mkdir(parents=True)
    (d / "Lascar.json").write_text(json.dumps(CON_FALLAS[0]), encoding="utf-8")
    salida = tmp_path / "out.txt"
    codigo = m.main(["decidir", "--runs", str(tmp_path / "runs.json"), "--id", "7", "--dir", str(tmp_path / "cob"),
                     "--salida", str(salida), "--ahora", AHORA.strftime("%Y-%m-%dT%H:%M:%SZ")])
    assert codigo == 0
    lineas = salida.read_text(encoding="utf-8").splitlines()
    assert "should_retry=true" in lineas and any(x.startswith("motivo=") for x in lineas)


def test_cli_decidir_sin_archivos_dice_no_y_sale_cero(tmp_path):
    m = _mod()
    salida = tmp_path / "out.txt"
    codigo = m.main(["decidir", "--runs", str(tmp_path / "no.json"), "--id", "7", "--dir", str(tmp_path / "nada"),
                     "--salida", str(salida)])
    assert codigo == 0 and "should_retry=false" in salida.read_text(encoding="utf-8").splitlines()


def test_cli_resumir_sin_entrada_no_escribe_y_sale_cero(tmp_path):
    m = _mod()
    codigo = m.main(["resumir", "--entrada", str(tmp_path / "no.json"), "--volcan", "Lascar",
                     "--salida", str(tmp_path / "s" / "Lascar.json")])
    assert codigo == 0 and not (tmp_path / "s" / "Lascar.json").exists()


# ── workflows ────────────────────────────────────────────────────────────────────────────────────

def _pasos(wf, job):
    return yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"][job]["steps"]


def test_nrt_escribe_la_cobertura_y_la_sube_sin_poder_ponerse_rojo():
    pasos = _pasos(NRT, "process")
    pipe = next(s for s in pasos if s.get("id") == "pipeline_mireq")
    assert '--cobertura-json "cobertura_nrt/${{ matrix.volcano }}.json"' in pipe["run"]
    assert "--estricto-cobertura" not in pipe["run"], "el NRT no se pone rojo por cobertura"
    i_pipe = pasos.index(pipe)
    resumir = next(s for s in pasos if "reintento_cobertura_nrt.py resumir" in s.get("run", ""))
    subir = next(s for s in pasos if "upload-artifact" in str(s.get("uses", "")))
    assert i_pipe < pasos.index(resumir) < pasos.index(subir)
    for paso in (resumir, subir):
        assert paso.get("continue-on-error") is True
        assert "!cancelled()" in paso["if"] and "steps.pipeline_mireq.outcome" in paso["if"]
    assert subir["with"]["name"] == "cobertura-${{ matrix.volcano }}"
    assert subir["with"]["path"] == "cobertura_resumen/${{ matrix.volcano }}.json"


def test_nrt_retry_tiene_el_camino_verde_y_conserva_el_rojo():
    txt = RETRY.read_text(encoding="utf-8")
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d
    run = next(s for s in d["jobs"]["check-and-retry"]["steps"] if s.get("id") == "check")["run"]
    i_verde = run.index('"$LAST_CONCLUSION" = "success"')
    assert "gh run download" in run[i_verde:] and "reintento_cobertura_nrt.py decidir" in run[i_verde:]
    assert "--pattern 'cobertura-*'" in run
    # el camino rojo (NASA_DOWN) sigue igual
    assert '[ "$LAST_CONCLUSION" != "failure" ]' in run and 'select(.title == "NASA_DOWN")' in run
    chk = [s for s in d["jobs"]["check-and-retry"]["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
    assert len(chk) == 1 and "scripts/reintento_cobertura_nrt.py" in chk[0]["with"]["sparse-checkout"]
    assert d["jobs"]["check-and-retry"]["permissions"]["actions"] == "write"
