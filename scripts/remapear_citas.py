# -*- coding: utf-8 -*-
"""Remapea citas `archivo:línea` de la documentación cuando cambia un archivo de código.

POR QUÉ (S141, propuesta A101 de S140): insertar una línea en un procesador corre las citas
`file:line` en tres lugares (contrato del guard G8, CLAUDE.md, docs/MIROVA_DIVERGENCES.md). S140
las remapeó a mano dos veces y la tarea 7 corrió 1, 2 y 3 líneas según la zona: sumar un
desplazamiento fijo produce citas que apuntan a otra cosa sin que nada falle.

CÓMO, y por qué así. Se alinea la versión vieja del archivo (en `--base`, por defecto
origin/main) con la nueva (el árbol de trabajo) usando difflib. Una línea sólo se remapea si cae
dentro de un bloque idéntico en ambas versiones: entonces es la misma línea de código y la cita
sigue diciendo lo mismo. Si cae en una línea editada o borrada, no hay forma segura de saber a
dónde fue, y se reporta como PENDIENTE para revisión humana en vez de adivinar.

Los rangos (`676-683`) y las listas (`212/1082`) se remapean extremo por extremo: validado contra
el remapeo manual de la tarea 7 de S140, mover sólo el inicio dejaba el final corrido.

Citas históricas. Las notas «era 208 antes de S135» no llevan nombre de archivo y el patrón no las
toca. Pero algunas citas históricas SÍ lo llevan: A6 cita `process_viirs.py:518` como lo que se
leyó en S21, y A49 cita `process_modis.py:316` como la línea del bug de S80. Esas no deben
moverse y no hay forma sintáctica de distinguirlas, así que van en `HISTORICAS` (con un fragmento
del texto de su línea, para sobrevivir a que el documento cambie de largo); cualquier otra se
excluye con `--excluir`. El informe muestra cada cambio antes de `--aplicar`: la revisión humana
es parte del método. El script tampoco escribe las notas «era N» de historia: eso es redacción.

El nombre se compara con frontera de palabra: `process_viirs.py` no captura
`process_viirs_mod.py` (A92).

USO:
    python scripts/remapear_citas.py pipeline/process_viirs.py            # informe
    python scripts/remapear_citas.py pipeline/process_viirs.py --aplicar  # escribe
    python scripts/remapear_citas.py --base HEAD~1 pipeline/process_modis.py
"""
from __future__ import annotations

import argparse
import difflib
import io
import os
import re
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DOCS_POR_DEFECTO = [
    "CLAUDE.md",
    "docs/MIROVA_DIVERGENCES.md",
    "tests/test_guard_declarado_vs_efectivo_s131.py",
]

# (fragmento de la línea del documento, archivo citado, línea citada): citas históricas deliberadas.
HISTORICAS = [
    ("(vent_dist=haversine", "process_viirs.py", 518),  # CLAUDE.md, regla A6
    ("desempaca `None`", "process_modis.py", 316),  # CLAUDE.md, regla A49
]


def mapa_lineas(viejo: list[str], nuevo: list[str]) -> dict[int, int]:
    """Línea vieja (1-based) -> línea nueva, sólo para líneas en bloques idénticos."""
    sm = difflib.SequenceMatcher(None, viejo, nuevo, autojunk=False)
    m: dict[int, int] = {}
    for tag, i1, i2, j1, _j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                m[i1 + k + 1] = j1 + k + 1
    return m


def _patron_cita(base: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(base) + r":(\d+(?:[-/]\d+)*)")


def _patron_contrato(base: str) -> re.Pattern:
    return re.compile(r'(\("(?:[^"]*/)?' + re.escape(base) + r'",\s*)(\d+)(\s*,)')


def _remapear_linea(linea, mapas, protegidas, cambios, pendientes):
    for base, m in mapas.items():
        def _num(n, base=base, m=m):
            if (base, n) in protegidas:
                return n
            if n in m:
                if m[n] != n:
                    cambios.append((base, n, m[n]))
                return m[n]
            pendientes.append((base, n))
            return n

        def _rep_cita(mo, base=base, _num=_num):
            partes = re.split(r"([-/])", mo.group(1))
            out = [p if p in ("-", "/") else str(_num(int(p))) for p in partes]
            return base + ":" + "".join(out)

        def _rep_contrato(mo, _num=_num):
            return mo.group(1) + str(_num(int(mo.group(2)))) + mo.group(3)

        linea = _patron_cita(base).sub(_rep_cita, linea)
        linea = _patron_contrato(base).sub(_rep_contrato, linea)
    return linea


def remapear_texto(texto: str, mapas: dict[str, dict[int, int]], excluir=()):
    """Devuelve (texto_nuevo, cambios, pendientes).

    cambios: [(archivo, línea_vieja, línea_nueva)]; pendientes: [(archivo, línea)] sin mapa seguro.
    excluir: pares (archivo, línea) que no se tocan, además de HISTORICAS.
    """
    cambios: list[tuple[str, int, int]] = []
    pendientes: list[tuple[str, int]] = []
    excluidas = set(excluir)
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        protegidas = {(b, n) for frag, b, n in HISTORICAS if frag in linea} | excluidas
        lineas[i] = _remapear_linea(linea, mapas, protegidas, cambios, pendientes)
    return "\n".join(lineas), cambios, pendientes


def _leer_base(rev: str, ruta: str) -> list[str]:
    out = subprocess.run(["git", "show", rev + ":" + ruta], cwd=RAIZ, capture_output=True,
                         check=True)
    return out.stdout.decode("utf-8").splitlines()


def main(argv=None) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codigo", nargs="+", help="archivos de código cuyas líneas cambiaron")
    ap.add_argument("--base", default="origin/main", help="revisión con la versión vieja")
    ap.add_argument("--docs", nargs="*", default=DOCS_POR_DEFECTO, help="archivos con citas")
    ap.add_argument("--excluir", nargs="*", default=[], metavar="ARCHIVO:LINEA",
                    help="citas que no se tocan (ej. process_modis.py:316)")
    ap.add_argument("--aplicar", action="store_true", help="escribir los cambios")
    a = ap.parse_args(argv)
    excluir = [(x.rsplit(":", 1)[0], int(x.rsplit(":", 1)[1])) for x in a.excluir]

    bases = [os.path.basename(c) for c in a.codigo]
    if len(set(bases)) != len(bases):
        print("dos archivos de código con el mismo nombre: la cita sería ambigua")
        return 2
    mapas = {}
    for ruta in a.codigo:
        viejo = _leer_base(a.base, ruta.replace("\\", "/"))
        with io.open(os.path.join(RAIZ, ruta), encoding="utf-8") as fh:
            nuevo = fh.read().splitlines()
        mapas[os.path.basename(ruta)] = mapa_lineas(viejo, nuevo)

    total_pend = 0
    for doc in a.docs:
        p = os.path.join(RAIZ, doc)
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8", newline="") as fh:
            texto = fh.read()
        nuevo, cambios, pendientes = remapear_texto(texto, mapas, excluir)
        total_pend += len(pendientes)
        if cambios or pendientes:
            print("\n" + doc)
        for base, v, n in cambios:
            print("   %s:%d -> %d" % (base, v, n))
        for base, v in pendientes:
            print("   PENDIENTE %s:%d (cae en una línea editada o borrada: revisar a mano)" % (base, v))
        if a.aplicar and cambios:
            with io.open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(nuevo)
    if not a.aplicar:
        print("\n(informe solamente; volver a correr con --aplicar para escribir)")
    return 1 if total_pend else 0


if __name__ == "__main__":
    sys.exit(main())
