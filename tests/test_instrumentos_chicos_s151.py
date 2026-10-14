# -*- coding: utf-8 -*-
"""Tarea 0.4 del loop: instrumentos chicos que callaban o dejaban colas muertas.

(a) `evaluar_ventana.py` mandaba el stderr de `armar_tabla.py` a DEVNULL, y el aviso A119 (calidad de la
    referencia de MIROVA por tramo) sale justo por stderr: el evaluador corria sin enterarse de que la
    ventana pisaba un tramo malo de la referencia.
(d) `ENABLE_TEST1_NULL_CORRECTED` lo lee `pipeline/profile.py` pero ningun procesador pasa
    `null_corrected` a las funciones del Test 1 (VERIFICADOR_DATOS S150 D8): un brazo que lo encienda sale
    identico al control (A118). Mientras siga sin cablear, ningun perfil puede encenderlo.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVALUAR = ROOT / "experiments" / "_s149_prereg_invierno" / "evaluar_ventana.py"
PROCESADORES = [ROOT / "pipeline" / n for n in ("process_modis.py", "process_viirs.py", "process_viirs_mod.py")]


def test_a_evaluar_ventana_no_silencia_stderr():
    src = EVALUAR.read_text(encoding="utf-8")
    assert "armar_tabla.py" in src
    assert not re.search(r"stderr\s*=\s*subprocess\.DEVNULL", src), "el aviso A119 sale por stderr"


def test_b_hitos_de_noaa21_y_suomi_npp():
    from scripts.calidad_referencia_mirova import avisos_de_ventana
    # Ventana de la prueba de Chillan (S150): pisa el arreglo de Mirova-v1#20 del 2026-10-09.
    assert any("Suomi NPP" in a for a in avisos_de_ventana("2026-09-14", "2026-10-07"))
    # Una ventana de marzo pisa la ausencia de NOAA-21 en la tabla.
    assert any("NOAA-21" in a for a in avisos_de_ventana("2026-03-01", "2026-03-31"))
    # Control: una ventana posterior a los dos hitos no los nombra.
    assert not any("NOAA-21" in a or "Suomi NPP" in a for a in avisos_de_ventana("2026-10-10", "2026-10-14"))


def perfiles_que_encienden(clave: str, perfiles_dir: Path = ROOT / "pipeline" / "profiles") -> list[str]:
    out = []
    for p in sorted(perfiles_dir.glob("*.yaml")):
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        secciones = [d] + [v for v in d.values() if isinstance(v, dict)]
        if any(s.get(clave) is True for s in secciones):
            out.append(p.name)
    return out


def _cableado(param: str) -> bool:
    patron = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(param) + r"\s*=")
    return any(patron.search(p.read_text(encoding="utf-8")) for p in PROCESADORES)


def test_d_flag_null_corrected_sin_cablear_no_se_enciende():
    if _cableado("null_corrected"):
        return  # el dia que se cablee, este guard deja de aplicar (y conviene borrarlo)
    assert perfiles_que_encienden("enable_test1_null_corrected") == []


def test_d_control_el_detector_de_perfiles_encuentra_un_flag_encendido(tmp_path):
    (tmp_path / "x.yaml").write_text("thresholds:\n  enable_test1_null_corrected: true\n", encoding="utf-8")
    (tmp_path / "y.yaml").write_text("enable_test1_null_corrected: false\n", encoding="utf-8")
    assert perfiles_que_encienden("enable_test1_null_corrected", tmp_path) == ["x.yaml"]


def test_d_control_hoy_ningun_procesador_lo_pasa():
    # Si esto falla, alguien cableo el flag: revisar D8 y este archivo.
    assert not _cableado("null_corrected")
