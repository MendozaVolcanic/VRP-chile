"""S112 (A45) — TDD: portar la magnitud núcleo-focal del cluster Test1 a VIIRS750.

Contexto (frente A69/D11): el recompute Test1 de VIIRS750 (process_viirs_mod.py) suma
radiancia MIR ABSOLUTA del gradiente topográfico cráter-vs-nieve sobre píxeles grandes
(562.500 m²) → magnitud inflada 10-25× vs MIROVA en los nevados (Tupungatito/Isluga/NdC/
Copahue/Llaima/PP), EXCEPTO Lascar (foco real, coincide ~2 MW). MODIS (process_modis.py,
S109) y VIIRS375 (process_viirs.py, contextual filter) YA tienen la cura; VIIRS750 quedó
sin ella (asimetría de schema A46). El fix porta `cluster_focal_vrp_mw` (S109, ya testeada
en test_focal_cluster_magnitude.py) al bloque Test1 de VIIRS750: suma SOLO los píxeles
contextualmente anómalos (dnti_ctx ∪ {pico}, keep_peak protege el foco real de Lascar/
lava lake). Usa un flag SEPARADO ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 (default OFF):
el flag global ENABLE_FOCAL_CLUSTER_MAGNITUDE YA está ON (MODIS adoptado S109 #423), así
que reusarlo dejaría V750 live sin A/B (violaría A45). El flag V750 separado mantiene el
port inerte hasta su propio A/B con Lascar de canario.

Discriminante validado en datos (probe S112): ctx_fraction = n_dnti_ctx_path/pc_n_pixels
separa Lascar (1.25, sus píxeles SON las anomalías) del artefacto (0.0, campo difuso sin
soporte contextual). cluster_focal_vrp_mw lo implementa por construcción.

Tests ESTRUCTURALES (precedente S95): el fix es un mirror exacto del bloque MODIS
process_modis.py:1213-1219; la de-inflación per-se está cubierta por la función pura.
RED antes del port (process_viirs_mod no importa ni llama cluster_focal_vrp_mw en Test1).
"""
import ast
import os

PIPELINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "pipeline")


def _src(name):
    with open(os.path.join(PIPELINE, name), encoding="utf-8") as fh:
        return fh.read()


def _imports_focal(src):
    """True si el módulo importa cluster_focal_vrp_mw."""
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module and \
                node.module.endswith("vrp_regimes"):
            if any(a.name == "cluster_focal_vrp_mw" for a in node.names):
                return True
    return False


def _focal_in_test1_block(src, flag_token):
    """True si cluster_focal_vrp_mw se aplica en el bloque del cluster Test1, gateado
    por `flag_token`.

    Marcador inequívoco (idéntico en los 3 procesadores): la línea
    `_vrp_t = float(top["vrp_mw"])` abre el bloque del cluster Test1. Dentro de las
    ~12 líneas siguientes debe aparecer la llamada a cluster_focal_vrp_mw gateada por
    flag_token (espejo de process_modis.py:1215-1219).
    """
    lines = src.splitlines()
    t1_idx = next((i for i, ln in enumerate(lines)
                   if '_vrp_t = float(top["vrp_mw"])' in ln), None)
    if t1_idx is None:
        return False
    window = "\n".join(lines[t1_idx:t1_idx + 12])
    return (flag_token in window and "cluster_focal_vrp_mw(" in window)


# --- VIIRS 750m (M-band) — el fix S112 ----------------------------------

def test_viirs750_imports_cluster_focal_vrp_mw():
    assert _imports_focal(_src("process_viirs_mod.py")), \
        "process_viirs_mod.py debe importar cluster_focal_vrp_mw (fix focal V750 S112)"


def test_viirs750_applies_focal_in_test1_block():
    assert _focal_in_test1_block(_src("process_viirs_mod.py"),
                                 "ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750"), (
        "process_viirs_mod.py debe aplicar cluster_focal_vrp_mw gateado por el flag "
        "SEPARADO ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 (no el global, que ya está ON "
        "para MODIS) en el bloque del cluster Test1, espejo de process_modis.py:1215-1219")


def test_viirs750_persists_focal_diag():
    """Transparencia (espejo MODIS): persistir focal_magnitude/focal_degraded en
    primary_cluster cuando el focal corre (no fallback silencioso)."""
    src = _src("process_viirs_mod.py")
    assert 'primary_cluster["focal_magnitude"]' in src or \
           '"focal_magnitude"' in src, \
        "process_viirs_mod.py debe persistir focal_magnitude en primary_cluster (Test1)"


# --- guardas de no-regresión --------------------------------------------

def test_modis_still_has_focal():
    src = _src("process_modis.py")
    assert _imports_focal(src) and _focal_in_test1_block(
        src, "ENABLE_FOCAL_CLUSTER_MAGNITUDE"), \
        "process_modis.py (S109) NO debe perder la magnitud focal"


def test_v750_focal_flag_default_off_unset(monkeypatch):
    """El flag es default OFF cuando un perfil no lo activa (perfil base)."""
    monkeypatch.setenv("VRP_PROFILE", "_baseline_s44")
    import importlib
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 is False


def test_v750_focal_ADOPTED_operacional_s112(monkeypatch):
    """S112 ADOPTADO (2026-06-17): la magnitud núcleo-focal V750 está ON en operacional
    (cura el artefacto topográfico A69 inflado 8-20×; A/B run 27762249160 24/24, Lascar
    canario preservado). Tag pre-s112-focal-v750."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import importlib
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 is True


def test_modis_focal_flag_still_on(monkeypatch):
    """No-regresión: el flag global de MODIS (adoptado S109 #423) sigue ON."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import importlib
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_FOCAL_CLUSTER_MAGNITUDE is True
