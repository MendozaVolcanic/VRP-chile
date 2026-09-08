"""Tests del probe de 3 brazos de S136 (interseccion contextual del Test 1).

POR QUE. El probe reasigna dos flags en el namespace de `pipeline.process_viirs` para separar
los brazos. Si un flag se renombra, o si `process_viirs` deja de importarlo por nombre, el probe
seguiria corriendo y los tres brazos darian LO MISMO en silencio: un A/B sin sustrato, que es
justo el modo de fallo que S130 y S133 documentaron. Estos tests atan esa suposicion.

Los asserts sobre codigo fuente usan frontera de palabra, no subcadena (A92, S133): con
subcadena, `ENABLE_TEST1_CONTEXTUAL_FILTER` matchea dentro de otro identificador mas largo y el
guard pasaria por la razon equivocada.
"""
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PROBE = RAIZ / "experiments" / "_s136" / "probe_3brazos.py"
PASADAS = RAIZ / "experiments" / "_s136" / "pasadas_s136.json"
PROCESS_VIIRS = RAIZ / "pipeline" / "process_viirs.py"

FLAGS = ("ENABLE_TEST1_CONTEXTUAL_FILTER", "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK")


def _tiene_identificador(src, token):
    """True si `token` aparece como identificador entero (A92: no como subcadena)."""
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])",
                     src) is not None


def test_los_flags_existen_en_el_namespace_de_process_viirs():
    """A89: el probe los reasigna en `pv`; si no estuvieran ahi, no separaria nada."""
    import pipeline.process_viirs as pv
    for flag in FLAGS:
        assert hasattr(pv, flag), (
            "{} no esta en el namespace de pipeline.process_viirs: el probe de S136 "
            "reasignaria un atributo nuevo sin efecto y los 3 brazos serian identicos".format(flag))


def test_process_viirs_importa_los_flags_por_nombre():
    """Si pasara a leerlos como `profile.X`, reasignarlos en `pv` dejaria de tener efecto."""
    src = PROCESS_VIIRS.read_text(encoding="utf-8")
    for flag in FLAGS:
        assert _tiene_identificador(src, flag), "{} ya no aparece en process_viirs.py".format(flag)
    assert not re.search(r"profile\.ENABLE_TEST1_CONTEXTUAL", src), (
        "process_viirs lee el flag como atributo de profile: el monkeypatch del probe "
        "sobre pv dejaria de separar los brazos (trampa A89)")


def test_el_filtro_se_decide_con_el_flag_y_con_el_source_legacy():
    """El bloque que el probe estudia sigue existiendo y sigue gateado por el flag."""
    src = PROCESS_VIIRS.read_text(encoding="utf-8")
    assert re.search(r"if\s*\(\s*ENABLE_TEST1_CONTEXTUAL_FILTER\s+and\s+"
                     r"final_hotspot_source\s*==\s*[\"']test1[\"']", src), (
        "el gate del filtro contextual cambio de forma; revisar process_viirs.py y "
        "el pre-registro docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md")


def test_los_brazos_son_tres_y_distintos():
    src = PROBE.read_text(encoding="utf-8")
    ns = {}
    exec(re.search(r"^BRAZOS = \(.*?\)$", src, re.M | re.S).group(0), ns)
    brazos = ns["BRAZOS"]
    assert len(brazos) == 3
    combos = {(f, k) for _, f, k in brazos}
    assert len(combos) == 3, "dos brazos tienen la misma combinacion de flags: A/B sin sustrato"
    assert ("ACTUAL", True, True) in brazos, "falta el brazo de linea base (la produccion de hoy)"
    assert any(n == "SIN_FILTRO" and not f for n, f, _ in brazos), "falta el brazo de la hipotesis"


def test_el_brazo_actual_refleja_el_perfil_operacional():
    """Si produccion cambiara los flags, el brazo 'ACTUAL' dejaria de ser la linea base."""
    import pipeline.profile as prof
    assert prof.ENABLE_TEST1_CONTEXTUAL_FILTER is True
    assert prof.ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK is True


def test_el_probe_no_escribe_en_data_ni_hace_push():
    """A45/A71: es read-only sobre la data operacional."""
    src = PROBE.read_text(encoding="utf-8")
    assert "git push" not in src
    assert not re.search(r"data\s*/\s*[\"']mirova_equivalent", src)
    assert "store.append_record" not in src, "el probe no debe persistir records"


@pytest.mark.skipif(not PASADAS.exists(), reason="pasadas_s136.json aun no generado")
def test_las_pasadas_tienen_control_no_nevado():
    """En S136 fue un control el que refuto un indicador: el probe no puede quedarse sin uno."""
    casos = json.loads(PASADAS.read_text(encoding="utf-8"))
    assert casos, "no hay pasadas seleccionadas"
    clases = {c["clase"] for c in casos}
    assert "control" in clases and "nevado" in clases
    assert sum(1 for c in casos if c["clase"] == "control") >= 3
    for c in casos:
        assert c.get("mirova_vrp_mw"), "toda pasada necesita ground truth con que comparar"
        assert c["sensor"].startswith("VIIRS"), "el filtro solo existe en VIIRS 375 m"
