# -*- coding: utf-8 -*-
"""S192: la reversión pre-autorizada de los tres sensores está SUSPENDIDA (decisión de Nicolás del 2026-11-21).

POR QUÉ: desde el reemplazo del 2026-11-12 toda la historia publicada es de la vía y el tablero sólo marca el paso de K a
la vía (hallazgo F11-102, auditoría Codex ronda 2, frente 11). Un revert haría caer la potencia a cerca de la mitad sin
marca, y el operador lo leería como una baja de actividad. Lo que llega a la sesión que actuaría es el issue de la
vigilancia y lo que imprime el script: si alguno vuelve a decir «pre-autoriza revertir», una sesión podría revertir sola.
Esta prueba fija que los textos que se leen al momento de decidir digan SUSPENDIDA, y que el veredicto no cambie de
nombre (la vigilancia sigue detectando la candidata igual).
"""
import contextlib
import io
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_guardia_modis as vgm  # noqa: E402
import scripts.vigilancia_guardia_viirs as vgv  # noqa: E402

REGLA_MODD = ROOT / "experiments" / "_s171_modd_adopcion" / "REGLA_REVERSION_MODD_BORRADOR.md"
REGLA_VIIRS = ROOT / "experiments" / "_s176_v375e_adopcion" / "REGLA_REVERSION_V375E_BORRADOR.md"
WF_MODIS = ROOT / ".github" / "workflows" / "vigilancia-guardia-modis.yml"
WF_VIIRS = ROOT / ".github" / "workflows" / "vigilancia-guardia-viirs.yml"

CANDIDATA = {"volcano": "NevadosDeChillan", "fecha_utc": "2026-11-21 06:00", "vrp_mirova_mw": 3.2}


def _leer(p):
    return p.read_text(encoding="utf-8")


def _seccion(txt, titulo):
    i = txt.index(titulo)
    j = txt.find("\n### ", i + len(titulo))
    return txt[i: j if j > 0 else len(txt)]


def test_las_dos_reglas_llevan_la_marca_s192_en_la_cabecera_y_en_la_reversion_inmediata():
    for regla in (REGLA_MODD, REGLA_VIIRS):
        txt = _leer(regla)
        cabecera = txt[: txt.index("## ")]
        assert "S192" in cabecera and "SUSPENDIDA" in cabecera, regla.name
        assert "«Sí, suspéndela»" in cabecera, regla.name
        sec = _seccion(txt, "### 4.3 Reversión inmediata, pre-autorizada")
        assert "S192" in sec and "SUSPENDIDA" in sec, regla.name


def _cuerpo_issue_candidata(wf):
    d = yaml.safe_load(_leer(wf))
    run = next(p for p in d["jobs"]["vigilar"]["steps"] if p.get("name") == "Open issue")["run"]
    m = re.search(r'REVERSION_CANDIDATA\)\s*\n\s*abrir "([^"]+)" "(.+)" ;;', run)
    assert m, wf.name
    return m.group(1), m.group(2)


def test_el_issue_de_la_candidata_dice_suspendida_y_no_pre_autoriza():
    for wf in (WF_MODIS, WF_VIIRS):
        titulo, cuerpo = _cuerpo_issue_candidata(wf)
        assert titulo.endswith("candidata a reversion"), "el título lo leen otras pruebas y quien busca issues"
        assert "SUSPENDIDA" in cuerpo and "NO revertir" in cuerpo, wf.name
        assert "pre-autoriza revertir" not in cuerpo, wf.name
        assert "Nicolas" in cuerpo, wf.name


def _impreso(fn, out):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(out)
    return buf.getvalue()


def test_el_script_de_modis_imprime_suspendida_para_la_candidata():
    txt = _impreso(vgm.imprimir, {"veredicto": "REVERSION_CANDIDATA", "reversion": [CANDIDATA]})
    linea = next(l for l in txt.splitlines() if "REVERSIÓN CANDIDATA" in l)
    assert "SUSPENDIDA" in linea and "Nicolás" in linea


def test_el_script_de_viirs_imprime_suspendida_para_la_candidata():
    for sensor in ("VIIRS375", "VIIRS750"):
        out = {"veredicto": "REVERSION_CANDIDATA", "reversion": [CANDIDATA], "sensor": sensor}
        txt = _impreso(vgv.imprimir, out)
        linea = next(l for l in txt.splitlines() if "REVERSIÓN CANDIDATA" in l)
        assert "SUSPENDIDA" in linea and "Nicolás" in linea, sensor


def test_el_veredicto_conserva_su_nombre():
    """La suspensión cambia qué se hace con la candidata, no si se detecta: el JSON y los issues la siguen llamando así."""
    assert "REVERSION_CANDIDATA" in _leer(ROOT / "scripts" / "vigilancia_guardia_modis.py")
    for wf in (WF_MODIS, WF_VIIRS):
        assert "REVERSION_CANDIDATA)" in _leer(wf)


def test_claude_md_y_la_ficha_dicen_que_esta_suspendida():
    claude = _leer(ROOT / "CLAUDE.md")
    mision = claude[claude.index("## Misión vinculante"): claude.index("**Objetivo: clon literal MIROVA NRT.**")]
    assert "S192" in mision and "SUSPENDIDA" in mision
    ficha = _leer(ROOT / "docs" / "FICHA_SDA_VRP_CHILE.md")
    linea = next(l for l in ficha.splitlines() if l.startswith("- **Funcionamiento/lógica:**"))
    assert "esa reversión está suspendida por decisión de Nicolás" in linea
