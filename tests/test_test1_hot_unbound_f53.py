"""F53/S78 TDD — `test1_hot` UnboundLocalError defensive init en process_viirs.

Bug F53 detectado en sanity test S77 reproc local (Lastarria 2026-05-23):
1/14 granules fallaron con:
  ERROR processing VNP02IMG.A2026143.0648.002...:
  cannot access local variable 'test1_hot' where it is not associated with a value

Root cause: `test1_hot` solo se inicializa en línea ~775 de
`pipeline/process_viirs.py` DENTRO del bloque `if "I04" in bands and
"I05" in bands`. Otros (`bt_path_hot`, `nti_path_hot`, `dnti_ctx_hot`,
`nti_rel_hot`, `eti_path_hot`) tienen defaults en el mismo scope cuando
sus condicionales internos no se ejecutan. Pero `test1_hot` falta.

Cuando alguna rama interna corta el flow del bloque I04 antes de línea
775 pero llega al `combine_hot_paths(test1_hot=test1_hot)` línea ~866,
explota con UnboundLocalError.

Fix:
1. Agregar `test1_hot = None` en bloque de defaults (líneas 598-604,
   junto a otros test1_*).
2. Justo antes de `combine_hot_paths` call, si `test1_hot is None`,
   inicializar con `np.zeros_like(bt_path_hot)` (bt_path_hot ya está
   garantizado por flow control en ese punto).

Tests cubren el patrón defensivo a nivel de inspección de código (no
intentan reproducir el granule específico, que requeriría fixtures L1B
reales).

Refs:
- pipeline/process_viirs.py:598-604 (defaults area)
- pipeline/process_viirs.py:775 (test1_hot original init)
- pipeline/process_viirs.py:862-867 (combine_hot_paths call)
- tag defensivo: pre-s78-f53-test1-hot
"""
from __future__ import annotations

import re
from pathlib import Path

PIPELINE = Path(__file__).parent.parent / "pipeline" / "process_viirs.py"


def test_test1_hot_has_default_outside_i04_scope():
    """F53: `test1_hot` debe tener default `= None` fuera del scope I04.

    Patrón consistente con test1_triggered, test1_n_contrib, etc.
    (líneas 599-604) que ya tienen defaults para evitar UnboundLocalError.

    Validación: en las primeras ~30 líneas después del marker S25, debe
    aparecer `test1_hot = `.
    """
    src = PIPELINE.read_text(encoding="utf-8")
    marker = "# S25 Path Test 1"
    idx = src.find(marker)
    assert idx >= 0, (
        f"No encontré el marker {marker!r} en process_viirs.py. "
        "Si fue refactorizado, actualizar este test."
    )
    # Tomar las siguientes 30 líneas después del marker
    block_lines = src[idx:].split("\n")[:30]
    block = "\n".join(block_lines)
    assert "test1_hot" in block, (
        f"F53 fix faltante: 'test1_hot' NO está en las 30 líneas siguientes "
        f"al marker {marker!r}. Debe estar inicializado a None junto a "
        f"test1_triggered etc., antes del scope I04 para evitar "
        f"UnboundLocalError cuando alguna rama interna corta el flow antes "
        f"de la asignación dentro del bloque I04. Bloque actual:\n{block}"
    )


def test_test1_hot_defensive_check_before_combine_hot_paths():
    """F53: justo antes de `combine_hot_paths(test1_hot=...)`, debe haber
    check defensivo que reinicialice si quedó None.

    Patrón:
        if test1_hot is None:
            test1_hot = np.zeros_like(bt_path_hot)
    """
    src = PIPELINE.read_text(encoding="utf-8")
    # Buscar 30 líneas antes del call combine_hot_paths
    m = re.search(r"combine_hot_paths\(", src)
    assert m is not None, "combine_hot_paths call no encontrado"
    start = max(0, m.start() - 1500)
    context = src[start:m.start()]
    has_guard = (
        "if test1_hot is None" in context
        or "if test1_hot is None:" in context
    )
    assert has_guard, (
        "F53 fix faltante: NO hay guard `if test1_hot is None: test1_hot = ...` "
        "antes del call combine_hot_paths. Sin este guard, si el default S25 es "
        "None y la rama de init en línea 775 no corre, combine_hot_paths recibe "
        "None y rompe (firma exige np.ndarray)."
    )
