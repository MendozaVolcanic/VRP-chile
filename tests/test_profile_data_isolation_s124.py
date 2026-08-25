"""S124 — cada perfil escribe en SU base de datos. Nunca dos en la misma.

Requisito de Nicolás: los perfiles deben poder manejarse por separado y sus
bases de datos no deben mezclarse.

Por qué importa, en concreto: un JSON de records no guarda con qué configuración
se generó cada registro. Si dos perfiles escriben en el mismo directorio, la
serie queda con registros de dos algoritmos distintos y se vuelve
ininterpretable — no se puede auditar, ni comparar A/B, ni saber si un salto de
magnitud es actividad del volcán o un cambio de configuración.

Ya pasó dos veces:
  - `mirova_equivalent_villarrica_test1` escribe en `data/mirova_equivalent/`,
    así que la serie operacional de Villarrica salió de otra configuración que
    los otros 10 volcanes (detectado en S124; ver el issue de seguimiento).
  - `experimental` iba a heredar la serie vieja de S15 tras su reescritura, que
    es de otra configuración; por eso ahora escribe en `experimental_v2`.

Este test es el guard: si alguien crea un perfil que reusa un `data_subdir`
ajeno, falla acá y no en una auditoría tres meses después.
"""
from collections import defaultdict
from pathlib import Path

import pytest
import yaml

PROFILES = Path(__file__).parent.parent / "pipeline" / "profiles"

# Excepción conocida y acotada, con fecha de revisión. NO agregar entradas sin
# entender qué serie se está contaminando.
EXCEPCIONES_CONOCIDAS = {
    # perfil -> subdir que comparte a propósito (hoy)
    "mirova_equivalent_villarrica_test1": "mirova_equivalent",
}


def _subdir(path: Path):
    """data_subdir efectivo, resolviendo `extends` una vez."""
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = (cfg.get("output") or {}).get("data_subdir")
    if out:
        return out
    parent = cfg.get("extends")
    if parent:
        ppath = PROFILES / f"{parent}.yaml"
        if ppath.exists():
            return _subdir(ppath)
    return None


def _perfiles_vivos():
    """Perfiles activos: excluye los de A/B histórico (prefijo _) y _archive."""
    return [p for p in PROFILES.glob("*.yaml") if not p.name.startswith("_")]


def test_ningun_par_de_perfiles_comparte_base_de_datos():
    por_subdir = defaultdict(list)
    for p in _perfiles_vivos():
        sub = _subdir(p)
        if sub:
            por_subdir[sub].append(p.stem)

    colisiones = {}
    for sub, perfiles in por_subdir.items():
        reales = [n for n in perfiles if EXCEPCIONES_CONOCIDAS.get(n) != sub]
        if len(reales) > 1:
            colisiones[sub] = sorted(reales)

    assert not colisiones, (
        "Perfiles distintos escribiendo en la misma base de datos: "
        f"{colisiones}. Cada perfil necesita su propio `output.data_subdir`, "
        "o la serie queda con registros de dos configuraciones y no se puede "
        "auditar. Si la mezcla es deliberada, documentala en "
        "EXCEPCIONES_CONOCIDAS con la razón.")


def test_todo_perfil_vivo_declara_donde_escribe():
    sin_subdir = [p.stem for p in _perfiles_vivos() if not _subdir(p)]
    assert not sin_subdir, (
        f"Perfiles sin `output.data_subdir` (ni heredado): {sin_subdir}. "
        "Sin eso el destino de escritura es implícito.")


@pytest.mark.parametrize("perfil,esperado", [
    ("mirova_equivalent", "mirova_equivalent"),
    ("experimental", "experimental_v2"),
    ("experimental_ndc_focus", "experimental_ndc_focus"),
])
def test_los_tres_perfiles_en_uso_escriben_donde_corresponde(perfil, esperado):
    """El operacional NO debe moverse; los experimentales van cada uno al suyo."""
    assert _subdir(PROFILES / f"{perfil}.yaml") == esperado
