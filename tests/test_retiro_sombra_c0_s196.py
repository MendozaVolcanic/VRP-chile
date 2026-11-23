# -*- coding: utf-8 -*-
"""S196 (P10 de docs/PLAN_EXPERIMENTAL_MEJORAS_S196.md; decisión D-B de Nicolás del 2026-11-23, «lo que recomiendas»):
retiro de la sombra C0.

EL FENÓMENO (del sistema). La sombra C0 (perfil `experimental`, data/experimental_v2/) guardaba lo que veía el detector
anterior para disparar la reversión de K. Desde el 2026-11-11 ningún sensor de producción corre K y su vigilancia daba
SIN_OBJETO cada día. Se apagaron los dos workflows y se congelaron sus datos.

QUÉ VIGILA.
  R1 ninguno de los dos workflows vuelve a tener disparo automático (cron o workflow_run) sin que alguien lo decida;
  R2 ningún otro workflow escucha a experimental-diario (un workflow_run colgado de un workflow sin cron no corre
     nunca y nadie se entera);
  R3 los datos siguen ahí (congelar no es borrar, A38) y llevan su README;
  R4 scripts/vigilancia_sombra.py sigue existiendo mientras las guardias lo importen (son la única alarma de la vía
     mientras la reversión está suspendida, S192);
  R5 la pestaña Laboratorio dice que la serie está congelada.

LAS DOS PREGUNTAS DEL INSTRUMENTO. Cada lectura tiene su control: el mismo lector encuentra el cron de un workflow que
sí lo tiene (nrt.yml) y el import en el archivo de la guardia (A92, A116).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
WF = RAIZ / ".github" / "workflows"
RETIRADOS = ("experimental-diario.yml", "vigilancia-sombra.yml")
AUTOMATICOS = ("schedule", "workflow_run", "push", "pull_request", "repository_dispatch")


def _on(nombre: str) -> dict:
    datos = yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))
    on = datos.get("on", datos.get(True))  # A43: sin comillas, YAML 1.1 lee «on» como True
    return on if isinstance(on, dict) else {k: None for k in ([on] if isinstance(on, str) else on)}


def test_control_el_lector_ve_el_cron_de_un_workflow_vivo():
    assert "schedule" in _on("nrt.yml"), "control: el lector no encuentra el cron de nrt.yml"


@pytest.mark.parametrize("nombre", RETIRADOS)
def test_r1_el_workflow_retirado_no_tiene_disparo_automatico(nombre):
    on = _on(nombre)
    assert "workflow_dispatch" in on, f"{nombre}: se conserva el despacho manual"
    vivos = [k for k in AUTOMATICOS if k in on]
    assert not vivos, (f"{nombre} volvió a tener disparo automático {vivos}: reencender la sombra C0 lo decide "
                       f"Nicolás (D-B, S196) y descongela data/experimental_v2/")
    texto = (WF / nombre).read_text(encoding="utf-8")
    assert re.search(r"^# RETIRADO \(S196, 2026-11-23", texto, re.M), f"{nombre}: falta la cabecera del retiro"


def test_r2_ningun_workflow_escucha_a_experimental_diario():
    nombre = yaml.safe_load((WF / "experimental-diario.yml").read_text(encoding="utf-8"))["name"]
    escuchan = []
    for p in sorted(WF.glob("*.yml")):
        on = _on(p.name)
        wr = on.get("workflow_run") if isinstance(on, dict) else None
        if isinstance(wr, dict) and nombre in (wr.get("workflows") or []):
            escuchan.append(p.name)
    assert not escuchan, f"workflow_run colgado de un workflow sin cron: {escuchan}"


def test_r3_los_datos_quedan_congelados_no_borrados():
    carpeta = RAIZ / "data" / "experimental_v2"
    jsons = sorted(p.stem for p in carpeta.glob("*.json"))
    assert len(jsons) == 11, jsons
    readme = (carpeta / "README.md").read_text(encoding="utf-8")
    assert "CONGELADA desde el 2026-11-23" in readme


def test_r4_vigilancia_sombra_sigue_mientras_las_guardias_la_importen():
    guardia = (RAIZ / "scripts" / "vigilancia_guardia_modis.py").read_text(encoding="utf-8")
    importa = re.search(r"^import vigilancia_sombra as vs\b", guardia, re.M)
    assert importa, "control: la guardia MODIS ya no importa vigilancia_sombra; si se desacopló, actualizar R4"
    assert (RAIZ / "scripts" / "vigilancia_sombra.py").is_file()


def test_r5_la_pestana_laboratorio_avisa_que_la_serie_esta_congelada():
    html = (RAIZ / "frontend" / "experimental" / "index.html").read_text(encoding="utf-8")
    assert "data/experimental_v2/" in html, "control: la pestaña ya no lee la sombra; actualizar R5"
    assert re.search(r'id="aviso-congelado">SERIE CONGELADA', html)
