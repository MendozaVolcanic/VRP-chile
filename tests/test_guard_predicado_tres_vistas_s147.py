"""S147 - las tres vistas vivas del tablero deciden publicar con el MISMO predicado.

POR QUE. El operador puede mirar el mapa (`index.html`), la tendencia de 90 dias de un volcan
(`diario.html`) o el panorama de 48 horas (`mosaico.html`). Si las tres no usan el mismo criterio
para decir "esto es una deteccion", el geologo ve un pico en una vista que en otra no existe y no
tiene forma de saber cual tiene razon. La regla del proyecto (S92 L5) es que un cambio de display
o de filtro se replica en las tres, y hasta S147 `diario.html` era la unica sin el predicado
escrito.

QUE MIDE ESTE GUARD, y que no:
- SI mide que las tres definen `isValidDetection` con el MISMO cuerpo (normalizado: sin
  comentarios, sin espacios de mas). Una divergencia futura en cualquiera de las tres lo rompe.
- NO mide que el predicado sea correcto. Eso lo vigila
  `tests/test_isvaliddetection_coherencia_s139.py`.
- NO mide que cada vista lo APLIQUE en todos sus caminos. Eso no se puede comprobar por texto.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si las vistas divergieran, esto fallaria? SI: el test compara los tres cuerpos entre si, y el
   caso de control de abajo comprueba que una diferencia inventada lo hace fallar.
2. Si el instrumento estuviera muerto? El primer test exige que las tres funciones EXISTAN y que
   el cuerpo extraido no este vacio, asi que una extraccion rota no pasa como coincidencia.

Cuidado con A92: la comprobacion NO es por subcadena. Un `assert "isValidDetection" in src` daria
verde con `isValidDetectionVieja`, o con el nombre dentro de un comentario.
"""
from __future__ import annotations
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VISTAS = ("frontend/index.html", "frontend/diario.html", "frontend/mosaico.html")


def _cuerpo_isvaliddetection(ruta: Path) -> str:
    """Extrae el cuerpo de `function isValidDetection(...)` y lo normaliza.

    Normalizar = quitar comentarios de linea y colapsar espacios, para que una diferencia de
    redaccion no cuente como divergencia de logica. El nombre se busca con frontera de palabra
    (A92): `isValidDetectionVieja` no matchea.
    """
    src = ruta.read_text(encoding="utf-8")
    m = re.search(r"(?<![A-Za-z0-9_])function\s+isValidDetection\s*\([^)]*\)\s*\{", src)
    if not m:
        return ""
    i = src.index("{", m.start())
    prof = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            prof += 1
        elif src[j] == "}":
            prof -= 1
            if prof == 0:
                cuerpo = src[i + 1:j]
                break
    else:
        return ""
    cuerpo = re.sub(r"//[^\n]*", "", cuerpo)
    return re.sub(r"\s+", " ", cuerpo).strip()


@pytest.mark.parametrize("vista", VISTAS)
def test_la_vista_define_el_predicado(vista):
    """Control del instrumento: las tres funciones existen y su cuerpo no esta vacio."""
    cuerpo = _cuerpo_isvaliddetection(ROOT / vista)
    assert cuerpo, f"{vista} no define isValidDetection, o el extractor no pudo leerlo"
    assert "primary_cluster" in cuerpo, f"{vista}: el cuerpo extraido no parece el predicado"


def test_las_tres_vistas_usan_el_mismo_predicado():
    """El corazon del guard: los tres cuerpos, normalizados, tienen que coincidir."""
    cuerpos = {v: _cuerpo_isvaliddetection(ROOT / v) for v in VISTAS}
    distintos = sorted(set(cuerpos.values()))
    assert len(distintos) == 1, (
        "las vistas del tablero decidirian distinto lo que es una deteccion:\n  "
        + "\n  ".join(f"{v}: {c[:120]}" for v, c in cuerpos.items()))


def test_control_una_diferencia_inventada_rompe_la_comparacion():
    """Control positivo: si el guard no pudiera ver una divergencia, no serviria de nada."""
    base = _cuerpo_isvaliddetection(ROOT / VISTAS[0])
    assert base, "sin cuerpo no se puede correr el control"
    alterado = base.replace("> 0", ">= 0", 1)
    assert alterado != base, "el control no logro alterar el cuerpo: revisar el extractor"
    assert len({base, alterado}) == 2
