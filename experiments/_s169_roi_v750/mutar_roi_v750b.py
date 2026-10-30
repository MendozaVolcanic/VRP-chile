# -*- coding: utf-8 -*-
"""Nulo de tests/test_roi_v750b_variantes_s169.py: mutaciones de una línea de scripts/roi_v750b_a_grillas.py.

POR QUÉ (S156, A110; P1-13 del verificador S169). Una prueba que pasa no dice nada si tampoco falla cuando el script
se rompe. Cada mutación es una copia con UNA línea cambiada en un árbol temporal, y cuenta como atrapada sólo si
pytest sale 1 con al menos una prueba «failed» y ninguna caída de colección; la identidad tiene que pasar y el control
que rompe el import tiene que salir caído. Incluye las cuatro de main() que el verificador dejó sin atrapar (M1 a M4,
f1/verificador/p113_mutar_roi.py en loop/activo) y la que reintroduce su VF1-02.
Uso (desde la raíz de un árbol con pipeline/, tests/ y scripts/): python experiments/_s169_roi_v750/mutar_roi_v750b.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path.cwd()
SCRIPT = "scripts/roi_v750b_a_grillas.py"
PRUEBA = "tests/test_roi_v750b_variantes_s169.py"
MUT = [
    ("identidad", None, None, "PASA"),
    ("C1 la variante pone siempre def", "texto = patron.sub(lambda m: m.group(1) + tipo + m.group(3), texto)",
     "texto = patron.sub(lambda m: m.group(1) + 'def' + m.group(3), texto)", "ATRAPADA"),
    ("M1 --escribir no escribe", '        YAML.write_text(nuevo, encoding="utf-8", newline="")\n', "        pass\n", "ATRAPADA"),
    ("M2 escribe el YAML viejo", "YAML.write_text(nuevo,", "YAML.write_text(viejo,", "ATRAPADA"),
    ("M3 ignora --brazo (siempre B4)", "nuevo = variante(viejo, a.brazo)", "nuevo = variante(viejo, 'B4')", "ATRAPADA"),
    ("M4 acepta B6", 'choices=("B0", "B1", "B2", "B3", "B4", "B5")', 'choices=("B0", "B1", "B2", "B3", "B4", "B5", "B6")',
     "ATRAPADA"),
    ("M5 comentario sólo con B1", '    if brazo != "B0" or texto.count(COMENTARIO_NUEVO) == 1:',
     '    if brazo == "B1":', "ATRAPADA"),
    ("M6 VF1-02: la nota sólo se pone la primera vez", "        texto = NOTA.sub(",
     "        texto = texto if 'Puesto por' in texto else NOTA.sub(", "ATRAPADA"),
    ("M7 B4 sin Tupungatito", 'SENSIBLES_B4 = ("PuyehueCordonCaulle", "Tupungatito")',
     'SENSIBLES_B4 = ("PuyehueCordonCaulle",)', "ATRAPADA"),
    ("control: import roto", "import difflib\n", "import difflib\nimport modulo_que_no_existe\n", "CAÍDA"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    orig = (RAIZ / SCRIPT).read_text(encoding="utf-8")
    malas = 0
    with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as tmp:
        arbol = Path(tmp) / "a"
        for d in ("pipeline", "tests", "scripts", "experiments/_s158_d17_diseno", "experiments/_s158_audit_r2"):
            if (RAIZ / d).exists():
                shutil.copytree(RAIZ / d, arbol / d)
        shutil.copy(RAIZ / "volcanoes.yaml", arbol / "volcanoes.yaml")
        env = {k: v for k, v in os.environ.items() if k != "VRP_PROFILE"}
        env["PYTHONIOENCODING"] = "utf-8"
        for nombre, viejo, nuevo, espera in MUT:
            if viejo is not None and orig.count(viejo) != 1:
                print(f"{nombre}: la línea aparece {orig.count(viejo)} veces, no 1: MUTACIÓN INVÁLIDA", flush=True)
                malas += 1
                continue
            (arbol / SCRIPT).write_text(orig if viejo is None else orig.replace(viejo, nuevo), encoding="utf-8")
            o = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", PRUEBA],
                               cwd=arbol, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
            fin = ([x for x in o.stdout.splitlines() if re.search(r" (passed|failed|error)", x)] or ["?"])[-1]
            if o.returncode == 0:
                estado = "PASA"
            elif o.returncode == 1 and "failed" in fin and "error" not in fin:
                estado = "ATRAPADA"
            else:
                estado = "CAÍDA"
            print(f"{nombre}: {estado} (se espera {espera}) | {fin}", flush=True)
            malas += estado != espera
    print("== mutaciones:", "TODAS COMO SE ESPERA, con identidad y control" if not malas else f"{malas} NO COMO SE ESPERA")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
