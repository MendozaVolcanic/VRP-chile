# -*- coding: utf-8 -*-
"""S203: chequeo externo R5C-103 (acta de cierre de la ronda 5 de Codex) antes de calibrar.
POR QUÉ: el evaluador recibe una carpeta por brazo y confía en que la carpeta es del brazo que dice ser. Si dos
carpetas se intercambian (p250 en el lugar de p200), la elección del piso sale con otro número sin que ningún control
lo vea. Cada record trae regimen.perfil; aquí se exige que todos los records de cada carpeta digan `_s196_lab_<brazo>`
y sólo eso. Control del instrumento: también se cuenta cuántos records se miraron (tiene que ser > 0 en cada carpeta).
Uso: python chequeo_perfil_r5c103.py <carpeta de la unión>"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
U = Path(sys.argv[1])
BRAZOS = ["_s196_lab_sinzona", "_s196_lab_control", "_s196_lab_p300", "_s196_lab_p275", "_s196_lab_p250",
          "_s196_lab_p225", "_s196_lab_p200", "_s196_lab_p175", "_s196_lab_p150"]
malos = 0
for b in BRAZOS:
    perfiles = Counter()
    n = 0
    for f in sorted((U / b).glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            n += 1
            perfiles[(r.get("regimen") or {}).get("perfil")] += 1
    ok = n > 0 and set(perfiles) == {b}
    malos += 0 if ok else 1
    print("%s: %d records, perfiles %s -> %s" % (b, n, dict(perfiles), "OK" if ok else "MAL"))
print("RESULTADO:", "OK, cada carpeta es del brazo que dice ser" if malos == 0 else "%d carpetas MAL" % malos)
sys.exit(0 if malos == 0 else 1)
