# -*- coding: utf-8 -*-
"""
S133 - Que guards de la suite pueden pasar por COINCIDENCIA DE TEXTO en vez de por el hecho.

FICHA SDA - auditoria read-only sobre el codigo de tests. No toca pipeline ni datos.

POR QUE. Esta sesion encontro que el guard de cableado de S103 seguia en verde despues de
que la llamada que vigilaba habia desaparecido: comprobaba `"viirs_pixel_areas(" in src` y
el codigo nuevo decia `resolve_viirs_pixel_areas(`, que lo contiene como subcadena. Un guard
que pasa por la razon equivocada es peor que no tenerlo, porque da permiso para el cambio
que deberia frenar. Nicolas lo dijo directo: "muchas veces arreglos que haciamos rompian
otras funciones".

La pregunta que responde este script: ¿de todos los tokens que la suite verifica por
subcadena, cuales son a su vez PREFIJO/SUBCADENA ESTRICTA de otro identificador que existe
de verdad en pipeline/? Esos son los que pueden dar falso verde HOY o en cuanto alguien
renombre. Los demas no corren ese riesgo aunque usen `in`.

Es deliberadamente conservador: reporta candidatos para revisar a mano, no dictamina.
"""
import ast
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))

# Un assert de la forma  assert "TOKEN" in <algo que huele a fuente>
PATRON_ASSERT = re.compile(
    r"""assert\s+(?:not\s+)?["']([A-Za-z_][A-Za-z0-9_.\[\]"'()= ]{2,})["']\s+in\s+"""
    r"""(src|src_nospace|source|fuente|contenido|texto|sin_espacios)\b""")


def identificadores_de_pipeline():
    """Todos los nombres definidos o asignados en pipeline/ (funciones, clases, globals)."""
    nombres = set()
    for ruta in glob.glob(os.path.join(REPO, "pipeline", "**", "*.py"), recursive=True):
        with open(ruta, encoding="utf-8") as fh:
            try:
                arbol = ast.parse(fh.read())
            except SyntaxError:
                continue
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nombres.add(nodo.name)
            elif isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
                nombres.add(nodo.id)
            elif isinstance(nodo, ast.arg):
                nombres.add(nodo.arg)
    return nombres


def main():
    universo = identificadores_de_pipeline()
    hallazgos = []
    n_asserts = 0

    for ruta in sorted(glob.glob(os.path.join(REPO, "tests", "*.py"))):
        rel = os.path.relpath(ruta, REPO).replace("\\", "/")
        with open(ruta, encoding="utf-8") as fh:
            lineas = fh.read().splitlines()
        for i, linea in enumerate(lineas, 1):
            m = PATRON_ASSERT.search(linea)
            if not m:
                continue
            n_asserts += 1
            token = m.group(1)
            # El riesgo solo aplica a tokens que son identificadores limpios: si el token
            # ya trae parentesis o comillas, es una expresion y no un nombre suelto.
            nucleo = token.rstrip("(")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nucleo):
                continue
            # ¿Existe en pipeline/ otro identificador que lo CONTENGA estrictamente?
            envolventes = sorted(n for n in universo
                                 if n != nucleo and nucleo in n)
            if envolventes:
                hallazgos.append({
                    "test": "%s:%d" % (rel, i),
                    "token_verificado": token,
                    "identificadores_que_lo_contienen": envolventes[:6],
                    "n_envolventes": len(envolventes),
                    "linea": linea.strip()[:120],
                    "cierra_con_parentesis": token.endswith("("),
                })

    res = {
        "sesion": "S133",
        "proposito": ("guards que verifican por subcadena y cuyo token es subcadena "
                      "estricta de otro identificador real de pipeline/"),
        "n_asserts_por_subcadena_revisados": n_asserts,
        "n_identificadores_en_pipeline": len(universo),
        "n_candidatos_a_falso_verde": len(hallazgos),
        "candidatos": hallazgos,
        "nota": ("Candidato NO significa roto: significa que el assert pasaria igual si el "
                 "codigo solo tuviera el identificador largo. Revisar a mano cual de esos "
                 "casos importa. El de S103 (viirs_pixel_areas dentro de "
                 "resolve_viirs_pixel_areas) ya se corrigio en esta rama."),
    }
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "auditar_guards_por_subcadena.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    print("asserts por subcadena revisados:", n_asserts)
    print("candidatos a falso verde:", len(hallazgos))
    for h in hallazgos:
        print("\n  %s" % h["test"])
        print("    verifica: %r" % h["token_verificado"])
        print("    contenido en: %s%s" % (
            ", ".join(h["identificadores_que_lo_contienen"]),
            " (+%d)" % (h["n_envolventes"] - 6) if h["n_envolventes"] > 6 else ""))
    print("\nJSON:", destino)


if __name__ == "__main__":
    main()
