"""Schema-source tests: process_viirs.py y process_viirs_mod.py deben retornar
los mismos campos `diag_*` que process_modis.py para paridad (H_S21_11 S21).

Sin esto el diagnóstico de records VIIRS queda ciego (todos los `diag_*` quedan
None tras reproceso). Como Tupungatito es 100% VIIRS (H_S21_2), ese gap impide
investigar el cuello de recall sin descargar granules raw cada vez.

Tests son schema-source (leen el archivo como texto, no ejecutan calculate_vrp)
para evitar tener que mockear los loaders L1B/GEO. Si algún campo es removido
del return dict, el test falla.
"""
from pathlib import Path
import re

PIPELINE = Path(__file__).parent.parent / "pipeline"

# Campos diag_ que process_modis.py guarda y que process_viirs.py debe igualar.
# Lista canónica derivada de pipeline/process_modis.py:494-504 (S6 schema).
REQUIRED_DIAG_FIELDS = (
    '"diag_sigma_bg_k"',
    '"diag_eff_threshold_k"',
    '"diag_n_bt_path"',
    '"diag_n_nti_path"',
    '"diag_n_dnti_ctx_path"',
    '"diag_nti_bg"',
    '"diag_nti_max"',
    '"diag_nti_std"',
    '"diag_t_max_dist_km"',
    '"diag_roi_p95_k"',
)


def _return_dict_text(src: str) -> str:
    """Extrae el bloque del return dict de calculate_vrp para mirar solo ahí.

    Heurística: tomar desde el último `return {` o `record = {` (S76 F31 A2
    introdujo el patrón "build record then return record" en process_viirs
    para permitir merge condicional de diag VRPTIR) hasta el siguiente
    cierre `\n}\n`. Es robusto para los archivos actuales que tienen un
    solo dict literal en el retorno final.
    """
    matches = list(re.finditer(r"(?:return|record\s*=)\s*\{", src))
    if not matches:
        return src
    start = matches[-1].start()
    # Buscar cierre balanceado simple: la primera línea que es '\n    }\n' o '\n}\n'
    rest = src[start:]
    # Encontrar el primer match de un '}' al inicio de línea (con cualquier indent)
    end_match = re.search(r"\n\s{0,8}\}\n", rest)
    if end_match:
        return rest[: end_match.end()]
    return rest


def test_process_modis_has_canonical_diag_fields():
    """Sanity: process_modis.py — fuente canónica — tiene todos los diag_*."""
    src = (PIPELINE / "process_modis.py").read_text(encoding="utf-8")
    block = _return_dict_text(src)
    missing = [f for f in REQUIRED_DIAG_FIELDS if f not in block]
    assert not missing, (
        f"process_modis.py (canónico) le faltan campos esperados: {missing}. "
        f"Si fueron removidos a propósito, actualizar la lista REQUIRED_DIAG_FIELDS."
    )


def test_process_viirs_paridad_diag_fields():
    """process_viirs.py debe retornar los mismos diag_* que process_modis.py."""
    src = (PIPELINE / "process_viirs.py").read_text(encoding="utf-8")
    block = _return_dict_text(src)
    missing = [f for f in REQUIRED_DIAG_FIELDS if f not in block]
    assert not missing, (
        f"process_viirs.py NO tiene paridad con process_modis.py. "
        f"Faltan en el return dict: {missing}. "
        f"Esto causa H_S21_11 (records VIIRS sin diag_, diagnóstico ciego)."
    )


def test_process_viirs_mod_paridad_diag_fields():
    """process_viirs_mod.py debe retornar los mismos diag_* que process_modis.py."""
    src = (PIPELINE / "process_viirs_mod.py").read_text(encoding="utf-8")
    block = _return_dict_text(src)
    missing = [f for f in REQUIRED_DIAG_FIELDS if f not in block]
    assert not missing, (
        f"process_viirs_mod.py NO tiene paridad con process_modis.py. "
        f"Faltan en el return dict: {missing}. "
        f"Esto causa H_S21_11 (records VIIRS_*_750 sin diag_, diagnóstico ciego)."
    )
