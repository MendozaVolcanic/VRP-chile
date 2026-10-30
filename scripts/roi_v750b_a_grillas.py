# -*- coding: utf-8 -*-
"""S169: lleva la ROI de VIIRS 750 que elija V750-B a pipeline/grillas_mirova.yaml (una variante por brazo).

POR QUÉ. La vía «código MIROVA» de VIIRS 750 lee la región sensible de cada volcán de la clave `roi_v750` del YAML
(`mirova_v750_codigo.grilla_del_volcan`), y el YAML dice que esa clave se cambia con la lectura de V750-B, nunca
antes. V750-B elige UN brazo (experiments/_s162_v750b/PREREGISTRO_V750B.md §2 y §6); este script traduce ese brazo a
los tipos de `caja_roi` y reescribe sólo esos valores, sin tocar comentarios, grillas ni coordenadas (A63: el YAML no
se regenera desde otra fuente). Se deja listo antes de la lectura para que el día del resultado el cambio sea uno
solo y probado; aplicarlo a main y encender la vía van con la frase de Nicolás (A45).

Brazos de V750-B -> `roi_v750` (caja_roi, pipeline/mirova_v750_codigo.py):
  B0 def    en los 11 (la matriz de ejemplo del .m; es lo que hay hoy, así que B0 no cambia el archivo)
  B1 sens   en los 11
  B2 crater en los 11 (el 7 x 7 sensible movido a la celda del cráter de volcanoes.yaml)
  B3 inner  en los 11 (el círculo de inner_radius_km del tablero)
  B4 sens   en PuyehueCordonCaulle y Tupungatito, def en los otros nueve
  B5 corona en los 11 (la corona 21 x 21 menos el 7 x 7 central)
Uso: python scripts/roi_v750b_a_grillas.py --brazo B4 [--escribir]   (sin --escribir sólo muestra el diff)
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

YAML = Path(__file__).resolve().parents[1] / "pipeline" / "grillas_mirova.yaml"
VOLCANES = ("Chaiten", "NevadosDeChillan", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica")
SENSIBLES_B4 = ("PuyehueCordonCaulle", "Tupungatito")     # PREREGISTRO_V750B.md §2, tabla de brazos
TIPO = {"B0": "def", "B1": "sens", "B2": "crater", "B3": "inner", "B5": "corona"}
COMENTARIO_VIEJO = '# roi_v750: la región sensible del código de MIROVA para el volcán. Hoy "def" en todos'
COMENTARIO_NUEVO = '# roi_v750: la región sensible del código de MIROVA para el volcán. Hasta la lectura de V750-B, "def" en todos'
# la línea que cierra el comentario: sin nota (hoy) o con la nota del brazo puesto. VF1-02 del verificador S169: una
# segunda aplicación la reemplaza, no la deja con el brazo anterior
NOTA = re.compile(r"^# caja_roi\(\)\.(?: Puesto por la lectura de V750-B: brazo B\d \(scripts/roi_v750b_a_grillas\.py\)\.)?$",
                  re.M)


def roi_por_volcan(brazo):
    """{volcán: tipo de caja_roi} para el brazo de V750-B."""
    if brazo == "B4":
        return {v: ("sens" if v in SENSIBLES_B4 else "def") for v in VOLCANES}
    if brazo not in TIPO:
        raise ValueError(f"brazo desconocido: {brazo!r} (válidos B0 a B5)")
    return {v: TIPO[brazo] for v in VOLCANES}


def variante(texto, brazo):
    """El YAML con `roi_v750` de cada volcán puesto según el brazo; todo lo demás, igual. Si una línea de volcán no
    aparece exactamente una vez, se niega (ValueError): el archivo no es el que este script conoce."""
    roi = roi_por_volcan(brazo)
    for v, tipo in roi.items():
        patron = re.compile(rf"^(  {v}:\s*\{{.*\broi_v750: )([a-z]+)(\}})$", re.M)
        n = len(patron.findall(texto))
        if n != 1:
            raise ValueError(f"la línea de {v} con roi_v750 aparece {n} veces, no 1")
        texto = patron.sub(lambda m: m.group(1) + tipo + m.group(3), texto)
    # el comentario dice qué ROI rige. En el archivo de hoy (todo def, sin nota) B0 no cambia nada; en cualquier otro
    # caso, incluido volver a B0 después de otro brazo, queda la nota del brazo puesto ahora
    if brazo != "B0" or texto.count(COMENTARIO_NUEVO) == 1:
        texto = texto.replace(COMENTARIO_VIEJO, COMENTARIO_NUEVO)
        if len(NOTA.findall(texto)) != 1:
            raise ValueError("la línea «# caja_roi().» del comentario no aparece exactamente una vez")
        texto = NOTA.sub(f"# caja_roi(). Puesto por la lectura de V750-B: brazo {brazo} (scripts/roi_v750b_a_grillas.py).",
                         texto)
    return texto


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazo", required=True, choices=("B0", "B1", "B2", "B3", "B4", "B5"))
    ap.add_argument("--escribir", action="store_true", help="escribe el YAML; sin esto sólo muestra el diff")
    a = ap.parse_args(argv)
    viejo = YAML.read_text(encoding="utf-8")
    nuevo = variante(viejo, a.brazo)
    sys.stdout.writelines(difflib.unified_diff(viejo.splitlines(True), nuevo.splitlines(True),
                                               "grillas_mirova.yaml", f"grillas_mirova.yaml ({a.brazo})"))
    if a.escribir and nuevo != viejo:
        YAML.write_text(nuevo, encoding="utf-8", newline="")
        print(f"escrito {YAML}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
