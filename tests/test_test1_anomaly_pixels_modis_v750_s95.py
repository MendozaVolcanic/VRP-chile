"""S95 (A45) — TDD: portar el fix del gap Test1 anomaly_pixels a MODIS y VIIRS750.

Contexto: el fix S94 (PR #294) pobló anomaly_pixels en el path Test1 de
process_viirs.py (VIIRS I-band 375m) usando el helper build_anomaly_pixels. Pero
process_modis.py (MODIS 1km) y process_viirs_mod.py (VIIRS M-band 750m) tienen su
PROPIO path Test1 con el mismo gap A07: arman primary_cluster con la magnitud
(pc.vrp_mw>0) pero dejan anomaly_pixels=[] vacío, aunque tienen los píxeles en
t1_vrp_2d. Verificado en data/mirova_equivalent/ (18 MODIS + 108 VIIRS750 records).

Estos tests fallan ANTES del fix (el helper no está importado/llamado en esos
módulos) y pasan DESPUÉS. El fix es ADITIVO: solo serializa píxeles ya calculados
que alimentan pc.vrp_mw; no cambia detección ni magnitud.

Ver docs/AUDIT_S95_gaps_sistemicos.md §Eje 1.
"""
import ast
import os

PIPELINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "pipeline")


def _module_source(name):
    with open(os.path.join(PIPELINE, name), encoding="utf-8") as fh:
        return fh.read()


def _imports_build_anomaly_pixels(src):
    """True si el módulo importa build_anomaly_pixels (helper del fix)."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and \
                node.module.endswith("anomaly_pixels"):
            if any(a.name == "build_anomaly_pixels" for a in node.names):
                return True
    return False


def _calls_in_test1_block(src):
    """True si build_anomaly_pixels se llama en el bloque Test1.

    Heurística robusta: existe una asignación `anomaly_pixels = build_anomaly_pixels(`
    que aparece DESPUÉS de la línea que asigna `t1_vrp_2d[t1_rows, t1_cols]`
    (marca inequívoca del bloque de cómputo Test1, idéntica en los 3 procesadores).
    """
    lines = src.splitlines()
    t1_assign_idx = None
    for i, ln in enumerate(lines):
        if "t1_vrp_2d[t1_rows, t1_cols]" in ln and "=" in ln:
            t1_assign_idx = i
            break
    if t1_assign_idx is None:
        return False
    for ln in lines[t1_assign_idx:t1_assign_idx + 12]:
        s = ln.strip()
        if s.startswith("anomaly_pixels = build_anomaly_pixels("):
            return True
    return False


# --- MODIS ---------------------------------------------------------------

def test_modis_imports_helper():
    assert _imports_build_anomaly_pixels(_module_source("process_modis.py")), \
        "process_modis.py debe importar build_anomaly_pixels (fix gap Test1 S95)"


def test_modis_populates_anomaly_pixels_in_test1_block():
    assert _calls_in_test1_block(_module_source("process_modis.py")), \
        ("process_modis.py debe poblar anomaly_pixels en el bloque Test1 "
         "(tras t1_vrp_2d[...]=t1_vrp_arr), espejo de process_viirs.py:1486")


# --- VIIRS 750m (M-band) -------------------------------------------------

def test_viirs750_imports_helper():
    assert _imports_build_anomaly_pixels(_module_source("process_viirs_mod.py")), \
        "process_viirs_mod.py debe importar build_anomaly_pixels (fix gap Test1 S95)"


def test_viirs750_populates_anomaly_pixels_in_test1_block():
    assert _calls_in_test1_block(_module_source("process_viirs_mod.py")), \
        ("process_viirs_mod.py debe poblar anomaly_pixels en el bloque Test1 "
         "(tras t1_vrp_2d[...]=t1_vrp_arr), espejo de process_viirs.py:1486")


# --- guardia de no-regresión: VIIRS375 ya lo tiene (PR #294) -------------

def test_viirs375_still_has_fix():
    src = _module_source("process_viirs.py")
    assert _imports_build_anomaly_pixels(src) and _calls_in_test1_block(src), \
        "process_viirs.py (PR #294) NO debe perder el fix existente"
