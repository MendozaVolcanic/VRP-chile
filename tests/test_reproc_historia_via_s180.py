# -*- coding: utf-8 -*-
"""S180: despacho de la vía «código MIROVA» para Tupungatito antes del 2026-02-23 (reemplazo de la historia).

POR QUÉ. Nicolás decidió el 2026-11-11 (opción 1 del plan docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md, §3) que la serie
publicada de Tupungatito sea de un solo método también antes del 2026-02-23. El planificador SELLADO de la retrospectiva
(experiments/_s172_retro_paquete/plan_trozos.py, §3.2 del pre-registro) recorta Tupungatito a esa fecha por una razón
de la REFERENCIA de la prueba (MIROVA no lo cubre antes), no de la vía. No se toca el sellado: un workflow aparte,
copia fiel del de la retrospectiva, usa un planificador que llama al sellado con el inicio de Tupungatito corrido al
2025-02-15 y sólo con el brazo de la vía.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) El job de reproceso del workflow nuevo es IGUAL, clave por clave, al de la
retrospectiva: si alguien cambia uno sin el otro, la prueba cae. (2) Cada guarda tiene su caso que falla: el perfil K,
un perfil ajeno, y el sellado que tiene que seguir recortando Tupungatito después de llamar al nuevo.
"""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WF_NUEVO = ROOT / ".github" / "workflows" / "reproc-historia-via.yml"
WF_RETRO = ROOT / ".github" / "workflows" / "reproc-retro-paquete.yml"
sys.path.insert(0, str(ROOT / "experiments" / "_s172_retro_paquete"))
sys.path.insert(0, str(ROOT / "experiments" / "_s180_reemplazo_via"))

import plan_trozos as PT  # noqa: E402

TODOS = "Lascar,PuyehueCordonCaulle,Lastarria,Isluga,Tupungatito,PlanchonPeteroa,Chaiten,Villarrica," \
        "NevadosDeChillan,Llaima,Copahue"
VENT_TUPU = ("Tupungatito@2025-02-15:2025-12-31,Tupungatito@2026-01-01:2026-01-31,"
             "Tupungatito@2026-02-01:2026-02-22")


def _ph():
    import plan_trozos_historia as PH
    return PH


def _yml(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_tupungatito_desde_el_15_de_febrero_de_2025_sin_huecos():
    jobs, saltados = _ph().planificar("_s172_retro_paquete", "Tupungatito", VENT_TUPU)
    assert saltados == []
    dias = sorted(t for j in jobs for t in j["tramos"].split())
    assert dias[0].startswith("2025-02-15:") and dias[-1].endswith(":2026-02-22")
    assert sum(j["dias"] for j in jobs) == 373
    assert {j["tramo"] for j in jobs} == {"R25", "OTRO", "F26"}
    assert all(j["esperado"] == "via" for j in jobs)
    assert all(j["minimo"] == ("0.90" if j["tramo"] == "R25" else "1.0") for j in jobs)


def test_el_sellado_sigue_recortando_tupungatito_despues_de_llamar_al_nuevo():
    _ph().planificar("_s172_retro_paquete", "Tupungatito", VENT_TUPU)
    assert PT.INICIO_TUPUNGATITO == "2026-02-23"
    with pytest.raises(SystemExit):   # todo antes del 02-23: el sellado no deja ningún trozo
        PT.planificar("_s172_retro_paquete", "Tupungatito", VENT_TUPU)
    jobs, saltados = PT.planificar("_s172_retro_paquete", "Tupungatito", VENT_TUPU + ",Tupungatito@2026-02-23:2026-03-01")
    assert jobs and len(saltados) == 3
    assert min(j["start"] for j in jobs) == "2026-02-23"


@pytest.mark.parametrize("perfil", ["_s172_retro_k", "mirova_equivalent", "_s172_retro_otro"])
def test_rehusa_todo_perfil_que_no_sea_el_brazo_de_la_via(perfil):
    with pytest.raises(SystemExit):
        _ph().planificar(perfil, "Tupungatito", VENT_TUPU)


def test_el_workflow_nuevo_llama_al_planificador_nuevo_y_no_al_sellado():
    d = _yml(WF_NUEVO)
    run = "\n".join(s.get("run", "") for s in d["jobs"]["plan"]["steps"])
    assert "experiments/_s180_reemplazo_via/plan_trozos_historia.py" in run
    assert "experiments/_s172_retro_paquete/plan_trozos.py" not in run


def test_el_job_de_reproceso_es_igual_al_de_la_retrospectiva():
    assert _yml(WF_NUEVO)["jobs"]["reproc"] == _yml(WF_RETRO)["jobs"]["reproc"]


def test_on_entre_comillas_solo_dispatch_permisos_de_lectura_y_grupo_propio():
    texto = WF_NUEVO.read_text(encoding="utf-8")
    assert texto.count('\n"on":') == 1
    d = _yml(WF_NUEVO)
    assert list(d["on"]) == ["workflow_dispatch"]
    assert d["permissions"] == {"contents": "read"}
    assert "git push" not in texto and "git commit" not in texto
    assert d["concurrency"]["group"].startswith("reproc-historia-via")
    assert d["concurrency"]["group"] != _yml(WF_RETRO)["concurrency"]["group"]
