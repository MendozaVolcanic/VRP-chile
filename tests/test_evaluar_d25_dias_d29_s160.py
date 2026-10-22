"""S160 (sesión nocturna), D-29: D25 se evalúa sin los días que CMR no sirvió.

POR QUE. Nicolás selló el 2026-10-21 (D-29, tasks/LOOP_OBJETIVOS.md §5): «D25 se evalúa sin el 17 al 20 de octubre ni
el 13 parcial, declarados en el veredicto». Esos días CMR no entregó los gránulos a los brazos del A/B, pero producción
sí los tiene (procesados en su momento por NRT), y la cobertura del evaluador compara los brazos contra producción: sin
la exclusión, V1 podía quedar INDECIDIBLE por cobertura o mezclar días con y sin datos. Hasta c44709e27 el evaluador no
excluía ningún día (hallazgo de la sesión nocturna S160).

Interpretación aplicada, a la vista de Nicolás en la bitácora: «el 13 parcial» se excluye entero y en los tres brazos
por igual, porque excluir pasada por pasada dependería de qué le faltó a cada brazo. El 19 y el 20 caen fuera de V1
(que termina el 18) y se listan igual, para que la regla diga lo mismo que la decisión.

Las pruebas fallan primero por ASERCIÓN (S152), por eso preguntan antes si el nombre existe.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_d29_s160", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)

V1_DIAS = ("2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")


def _tiene(nombre):
    assert hasattr(X, nombre), "falta %s (D-29)" % nombre


def test_los_dias_de_d29_estan_declarados_para_v1_y_ninguno_para_v2():
    _tiene("DIAS_EXCLUIDOS")
    assert tuple(sorted(X.DIAS_EXCLUIDOS["V1"])) == V1_DIAS
    assert tuple(X.DIAS_EXCLUIDOS.get("V2", ())) == ()


def test_filtrar_dias_saca_las_pasadas_de_esos_dias_y_deja_las_demas():
    _tiene("filtrar_dias")
    d = {"Lascar|VIIRS375|2026-10-17T05:18": 1, "Lascar|VIIRS375|2026-10-16T05:18": 2,
         "Isluga|VIIRS750|2026-10-13 06:06": 3, "Isluga|VIIRS750|2026-10-12T06:06": 4}
    out = X.filtrar_dias(d, V1_DIAS)
    assert out == {"Lascar|VIIRS375|2026-10-16T05:18": 2, "Isluga|VIIRS750|2026-10-12T06:06": 4}
    s = X.filtrar_dias(set(d), V1_DIAS)
    assert s == {"Lascar|VIIRS375|2026-10-16T05:18", "Isluga|VIIRS750|2026-10-12T06:06"}


def test_sin_dias_no_saca_nada():
    _tiene("filtrar_dias")
    d = {"Lascar|VIIRS375|2026-10-17T05:18": 1}
    assert X.filtrar_dias(d, ()) == d


def test_evaluar_aplica_el_filtro_a_tablas_crudos_y_cobertura():
    """A118: un umbral o una exclusión tiene que llegar a todos sus consumidores. Frontera de palabra (A92)."""
    src = (DIR / "evaluar_d25.py").read_text(encoding="utf-8")
    cuerpo = src[src.index("def evaluar(a):"):src.index("def combinar(")]
    llamadas = re.findall(r"(?<![A-Za-z0-9_])filtrar_dias\s*\(\s*([A-Za-z_][A-Za-z0-9_\[\]\"']*)", cuerpo)
    blancos = {x.split("[")[0] for x in llamadas}
    assert {"t", "R", "ks"} <= blancos, llamadas   # tablas K-brazo, crudos de cada brazo, referencia de cobertura


def test_el_veredicto_combinado_lo_dice_en_su_primera_linea(tmp_path, capsys):
    _tiene("DIAS_EXCLUIDOS")
    rs = []
    for v, dias in (("V1", list(V1_DIAS)), ("V2", [])):
        p = tmp_path / ("%s.json" % v)
        p.write_text(json.dumps({"ventana": v, "estado": "SIN EFECTO", "empeora": False, "mejora": False,
                                 "dias_excluidos": dias}), encoding="utf-8")
        rs.append(str(p))
    final = X.combinar(rs)
    assert final.startswith("EVALUADO SIN"), final
    assert "2026-10-17" in final and "2026-10-13" in final, final
