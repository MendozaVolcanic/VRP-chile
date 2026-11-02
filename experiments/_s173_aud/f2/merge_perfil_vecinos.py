# -*- coding: utf-8 -*-
"""S173 F2 (f) y reversión: ¿un cambio futuro de una clave VECINA del flag de B en mirova_equivalent.yaml choca con B o
con su revert? Usa git merge-file (3 vías, el mismo algoritmo de línea que git merge/revert) sobre los textos reales.
Pregunta 1: un conflicto da código de salida > 0; control positivo: editar la MISMA línea que B (flag en false) choca.
Pregunta 2: control negativo: un cambio lejos (otra sección, línea 1) no choca."""
import subprocess, sys, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent / "mf"
main, B = (D / "main.yaml").read_text(encoding="utf-8"), (D / "B.yaml").read_text(encoding="utf-8")
L140 = "  enable_modis_dist_desde_crater: false  # dist_km del pixel anomalo y etiqueta summit/far desde el crater (A61 H5)\n"
assert L140 in main and L140 in B
def mf(nom, base, ours, theirs):
    for n, t in (("base", base), ("ours", ours), ("theirs", theirs)):
        (D / f"_{n}.yaml").write_text(t, encoding="utf-8", newline="\n")
    r = subprocess.run(["git", "merge-file", "-p", str(D / "_ours.yaml"), str(D / "_base.yaml"), str(D / "_theirs.yaml")],
                       capture_output=True, text=True, encoding="utf-8")
    print(f"{nom}: {'CONFLICTO (' + str(r.returncode) + ' bloques)' if r.returncode > 0 else 'limpio'}")
flip140 = lambda t: t.replace(L140, L140.replace("false ", "true  "))
v750 = lambda t: t.replace(L140, L140 + "  enable_v750_codigo_mirova: true\n")
lejos = lambda t: "# comentario de control\n" + t
print("== B contra un cambio futuro de main (merge de B sobre ese main)")
mf("flip de enable_modis_dist_desde_crater (línea vecina, arriba del bloque de B)", main, B, flip140(main))
mf("enable_v750_codigo_mirova agregado tras el bloque de MxD03 (mismo lugar que B)", main, B, v750(main))
mf("CONTROL NEG: cambio en la línea 1", main, B, lejos(main))
mf("CONTROL POS: misma línea que B con false", main, B, B.replace("enable_modis_codigo_mirova: true", "enable_modis_codigo_mirova: false  # otro"))
print("== revert de B sobre un main que ya trae ese cambio (base = B, ours = B + cambio, theirs = main sin B)")
mf("revert de B tras el flip de la línea vecina", B, flip140(B), main)
mf("revert de B tras agregar enable_v750_codigo_mirova pegado al bloque de MxD03", B, v750(B), main)
mf("revert de B tras agregar enable_v750_codigo_mirova al final de thresholds (después del bloque de B)", B,
   B.replace("  enable_modis_codigo_mirova: true\n", "  enable_modis_codigo_mirova: true\n  enable_v750_codigo_mirova: true\n"), main)
mf("CONTROL NEG revert: cambio en la línea 1", B, lejos(B), main)
