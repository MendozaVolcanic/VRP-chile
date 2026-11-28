"""S163: censo de las reglas A del CLAUDE.md del proyecto (sesion de origen y si cayeron despues).

POR QUE: las reglas A1-A119 son el registro de cada leccion; el plan
(docs/PLAN_PROCESO_VRP_CHILE_S163.md) las usa como columna vertebral. Este script dice, por
regla, en que sesion nacio y si lleva una marca posterior de auditoria (el simbolo de
advertencia seguido de OBSOLETA / REBAJADA / FALSA / CORRUPTA / SIN VERIFICAR / Hereda la
rebaja / matizado), que es la prueba de que el propio registro se audito.
Sesion de origen: primer "(SNN" del parrafo; si no hay, el "SNN" suelto; si no, el encabezado
"## Reglas operacionales SNN" que la precede. Limite: es inferencia por patron de texto.
Lee CLAUDE.md de la raiz del worktree (rama del plan, igual a origin/main al crearla).
"""
import collections
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "CLAUDE.md")
txt = open(RUTA, encoding="utf-8").read()

MARCA = re.compile(
    "⚠️?[^\\n]{0,80}?(OBSOLET[AO]|REBAJADA|Rebajada|FALS[AO]\\b|CORRUPTA|"
    "SIN VERIFICAR|Hereda la rebaja|matizado|corregida)", re.I)

reglas = {}
for m in re.finditer(r"\n- \*\*A(\d+)[.\s,]", txt):
    n = int(m.group(1))
    if n in reglas:
        continue  # la primera aparicion es la regla; las enmiendas posteriores van aparte
    ini = m.start()
    sig = re.search(r"\n- \*\*A\d+[.\s,]|\n## ", txt[ini + 5:])
    cuerpo = txt[ini: ini + 5 + (sig.start() if sig else 4000)]
    # el origen se busca SOLO antes de la primera marca de advertencia: las marcas citan la
    # sesion que rebajo la regla, no la que la escribio (verificador S163: A3, A10, A23 salian
    # con la sesion de la marca)
    antes = cuerpo.split("⚠", 1)[0]
    ses = re.search(r"\(S(\d+)", antes)
    suelta = re.search(r"\bS(\d+)\b", antes)  # una "SNN" suelta puede ser un ejemplo (A25 cita S33)
    if ses is not None:
        origen = int(ses.group(1))
    elif n <= 26:  # A1-A26 viven bajo los encabezados "## Reglas operacionales SNN"
        hs = re.findall(r"## Reglas operacionales S(\d+)", txt[:ini])
        origen = int(hs[-1]) if hs else None
    elif suelta is not None:
        origen = int(suelta.group(1))
    else:  # despues de A26 no hay encabezado: se hereda la sesion de la regla anterior
        origen = reglas[max(reglas)][0] if reglas else None
    marcas = sorted({x.upper() for x in MARCA.findall(cuerpo)})
    reglas[n] = (origen, marcas)

faltan = [n for n in range(1, 120) if n not in reglas]
print(f"reglas A con parrafo propio={len(reglas)} de A1-A119; sin parrafo propio: {faltan}")
con = sorted(n for n, (_, mk) in reglas.items() if mk)
print(f"con marca posterior de auditoria: {len(con)} -> {con}")
tramos = collections.Counter()
for n, (s, _) in reglas.items():
    tramos["?" if s is None else (s - 1) // 20 * 20 + 1] += 1
orden = sorted((k for k in tramos if k != "?"))
print("reglas por tramo de 20 sesiones:",
      ", ".join(f"S{k}-S{k + 19}: {tramos[k]}" for k in orden), f"| sin sesion: {tramos['?']}")
for n in sorted(reglas):
    print(f"A{n}\tS{reglas[n][0]}\t{','.join(reglas[n][1])}")
