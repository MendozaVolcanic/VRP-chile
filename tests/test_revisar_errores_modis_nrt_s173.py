# -*- coding: utf-8 -*-
"""S173 (hallazgo 209, V2-02): el job del NRT queda rojo si un gránulo MODIS terminó en `ERROR processing`.

POR QUÉ. Con la vía «código MIROVA» de MODIS encendida, una excepción de la vía en un gránulo no cae a K:
scripts/run_pipeline.py la atrapa, imprime `ERROR processing <archivo>: <error>` y sigue, y el job saldría verde con
esa pasada sin record de producción (regla de reversión de MODIS §4.4 (a), ronda 3). El paso
«Revisar errores de MODIS en el log» de .github/workflows/nrt.yml corre scripts/revisar_errores_modis_nrt.py sobre
pipeline.log. Estas pruebas fijan: (1) que el paso existe, va después del commit y corre cuando corrió el paso de
producción; (2) que el log de producción se captura con tee sin perder el código de salida; (3) que el revisor falla
con un error de MODIS y no con uno de VIIRS ni con un log limpio; (4) que los nombres que el revisor busca son los que
run_pipeline usa de verdad (si cambian, esto cae). Aserciones sobre texto con frontera de palabra (A92).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
SCRIPT = ROOT / "scripts" / "revisar_errores_modis_nrt.py"
RUN_PIPELINE = ROOT / "scripts" / "run_pipeline.py"
sys.path.insert(0, str(ROOT / "scripts"))
from revisar_errores_modis_nrt import clasificar  # noqa: E402

NOMBRE_PASO = "Revisar errores de MODIS en el log"


def _token(nombre):
    return re.compile(r"(?<![A-Za-z0-9_./-])" + re.escape(nombre) + r"(?![A-Za-z0-9_])")


def _pasos():
    d = yaml.safe_load(NRT.read_text(encoding="utf-8"))
    return d["jobs"]["process"]["steps"]


# ------------------------------------------------------------------------------------------------- 1. el paso
def test_el_paso_existe_va_despues_del_commit_y_lee_el_log():
    pasos = _pasos()
    nombres = [s.get("name", "") for s in pasos]
    assert nombres.count(NOMBRE_PASO) == 1, nombres
    i_rev = nombres.index(NOMBRE_PASO)
    i_commit = next(i for i, s in enumerate(pasos) if re.search(r"(?m)\bgit push\b", s.get("run", "")))
    i_nasa = next(i for i, s in enumerate(pasos) if re.search(r"\bNASA_AUTH_UNREACHABLE\b", s.get("run", "")))
    assert i_rev > i_commit and i_rev > i_nasa
    run = pasos[i_rev]["run"]
    assert _token("scripts/revisar_errores_modis_nrt.py").search(run), run
    assert re.search(r"--log\s+pipeline\.log(?![A-Za-z0-9_.])", run), run


def test_el_paso_corre_si_corrio_produccion_y_no_si_la_cancelaron():
    pasos = _pasos()
    prod = next(s for s in pasos if s.get("name", "").startswith("Run VRP pipeline") and "mirova_equivalent" in s["name"])
    rev = next(s for s in pasos if s.get("name") == NOMBRE_PASO)
    pid = prod.get("id")
    assert pid == "pipeline_mireq"
    cond = rev["if"]
    assert re.search(r"!cancelled\(\)", cond), cond
    assert re.search(r"steps\." + pid + r"\.outcome == 'success'", cond), cond
    assert re.search(r"steps\." + pid + r"\.outcome == 'failure'", cond), cond
    # sin always(): una corrida cancelada no se revisa (el log puede estar a medias)
    assert not re.search(r"\balways\(\)", cond), cond


def test_produccion_captura_el_log_con_tee_sin_perder_el_codigo_de_salida():
    pasos = _pasos()
    prod = next(s for s in pasos if s.get("id") == "pipeline_mireq")
    run = prod["run"]
    assert re.search(r"(?m)^\s*set -o pipefail\s*$", run), run
    assert re.search(r"--profile mirova_equivalent\b", run), run
    assert re.search(r"2>&1 \| tee -a pipeline\.log\s*$", run.rstrip()), run


# ---------------------------------------------------------------------------------------- 2. el revisor
LOG_LIMPIO = """[diag 12:25:46Z] SEARCH_START MODIS_TERRA
  MODIS_TERRA | VRP=0.31 MW | T_bg=262.1 K | T_max=270.4 K | anomalous_px=1
  VIIRS_NOAA20 (375m) | VRP_MIR=0.05 MW | VRP_TIR=None MW | T_max=280.1 K
"""
LOG_ERROR_MODIS = LOG_LIMPIO + "  ERROR processing MOD021KM.A2026306.0310.061.NRT.hdf: index 0 is out of bounds\n"
LOG_ERROR_AQUA = LOG_LIMPIO + "  ERROR processing MYD021KM.A2026306.0650.061.2026306123456.hdf: boom\n"
LOG_ERROR_VIIRS = LOG_LIMPIO + (
    "  ERROR processing VJ102IMG.A2026306.0600.021.2026306080000.nc: KeyError 'x'\n"
    "  ERROR processing VNP02MOD.A2026306.0548.002.2026306071234.nc: boom\n")


def _correr(tmp_path, texto, nombre="pipeline.log"):
    log = tmp_path / nombre
    if texto is not None:
        log.write_text(texto, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_STEP_SUMMARY"}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(SCRIPT), "--log", str(log), "--volcan", "Lascar"],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def test_error_de_modis_falla(tmp_path):
    r = _correr(tmp_path, LOG_ERROR_MODIS)
    assert r.returncode == 1, r.stdout + r.stderr
    assert re.search(r"(?m)^::error title=Error en un granulo MODIS \(Lascar\)::.*\bMOD021KM\.A2026306\.0310\b",
                     r.stdout), r.stdout


def test_error_de_modis_aqua_falla(tmp_path):
    r = _correr(tmp_path, LOG_ERROR_AQUA)
    assert r.returncode == 1, r.stdout
    assert re.search(r"(?m)^::error .*\bMYD021KM\.A2026306\.0650\b", r.stdout), r.stdout


def test_error_de_viirs_no_falla(tmp_path):
    r = _correr(tmp_path, LOG_ERROR_VIIRS)
    assert r.returncode == 0, r.stdout
    assert not re.search(r"(?m)^::error\b", r.stdout), r.stdout
    assert re.search(r"de otros sensores \(no hacen fallar\): 2\b", r.stdout), r.stdout


def test_log_limpio_no_falla(tmp_path):
    r = _correr(tmp_path, LOG_LIMPIO)
    assert r.returncode == 0, r.stdout
    assert re.search(r"gránulos MODIS con ERROR processing: 0\b", r.stdout), r.stdout


def test_sin_log_falla(tmp_path):
    """No haber mirado no es lo mismo que no haber errores (vigilancia ciega)."""
    r = _correr(tmp_path, None)
    assert r.returncode == 1, r.stdout
    assert re.search(r"(?m)^::error title=NRT sin log\b", r.stdout), r.stdout


def test_clasificar_separa_por_sensor_y_no_por_subcadena():
    modis, otros = clasificar(LOG_ERROR_MODIS + LOG_ERROR_VIIRS
                              + "  ERROR processing XMOD021KMX.hdf: no es MODIS\n"
                              + "  NO_ERROR processing MOD021KM.A1.hdf: no es la linea de run_pipeline\n")
    assert len(modis) == 1 and "MOD021KM.A2026306.0310" in modis[0]
    assert len(otros) == 3


# ------------------------------------------------------------------- 3. los nombres que usa run_pipeline de verdad
def test_run_pipeline_imprime_el_error_que_busca_el_revisor():
    src = RUN_PIPELINE.read_text(encoding="utf-8")
    n = len(re.findall(r'print\(f"  ERROR processing \{l1b\.name\}: \{e\}"\)', src))
    assert n == 3, n  # MODIS, VIIRS 375 y VIIRS 750


def test_run_pipeline_separa_los_l1b_de_modis_con_los_mismos_nombres():
    src = RUN_PIPELINE.read_text(encoding="utf-8")
    assert re.search(r'\[p for p in paths if "MOD021KM" in p\.name or "MYD021KM" in p\.name\]', src)
    for nombre in ("MOD021KM", "MYD021KM"):
        modis, otros = clasificar(f"  ERROR processing {nombre}.A2026306.0310.061.NRT.hdf: x\n")
        assert len(modis) == 1 and not otros, nombre


@pytest.mark.parametrize("nombre", ["VNP02IMG", "VJ102IMG", "VJ202IMG", "VNP02MOD", "VJ102MOD", "VJ202MOD"])
def test_ningun_l1b_de_viirs_cuenta_como_modis(nombre):
    src = RUN_PIPELINE.read_text(encoding="utf-8")
    assert re.search(r'"' + nombre + r'" in p\.name', src), nombre  # el nombre existe de verdad en run_pipeline
    modis, otros = clasificar(f"  ERROR processing {nombre}.A2026306.0600.021.nc: x\n")
    assert not modis and len(otros) == 1
