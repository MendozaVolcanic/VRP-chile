"""S137 - compara caso a caso los brazos de la bateria del Apendice A.

POR QUE. La bateria da un veredicto por caso y por brazo, pero la decision sale de mirarlos
juntos: un brazo sirve si y solo si conserva los 6 positivos Y cura los 3 negativos (criterio
fijado en S136, no se mueve). Este script no decide nada nuevo, solo pone los brazos lado a lado.

Lee cada brazo por NOMBRE de directorio, nunca por glob: el runner hace checkout del repo y los
directorios de S136 vienen commiteados, asi que un glob puede leer el brazo equivocado (trampa
documentada en tasks/BLOQUE_ARRANQUE_S137.md).

Uso: python experiments/_s137/comparar_brazos_apendice.py [RAIZ_ARTEFACTOS]
Sin argumento lee experiments/_s136/. Brazos ausentes se reportan como ausentes, no se inventan.
"""
import io
import json
import sys
from pathlib import Path

BRAZOS = [
    ("out_apendice", "B21 min (hoy)"),
    ("out_apendice_prosa", "B21 max"),
    ("out_apendice_b22", "B22 min"),
    ("out_apendice_b22_prosa", "B22 max"),
]


def cargar(raiz):
    """{dirname: {caso: resultado_dict}} solo para los brazos presentes."""
    out = {}
    for d, _ in BRAZOS:
        p = Path(raiz) / d / "resultado_apendice.json"
        if p.exists():
            out[d] = {c["caso"]: c for c in json.loads(p.read_text(encoding="utf-8"))}
    return out


def corto(resultado):
    if resultado == "CONFORME":
        return "ok"
    if "falso negativo" in resultado:
        return "FN"
    if "falso positivo" in resultado:
        return "FP"
    if resultado.startswith("INDETERMINADO"):
        return "indet"
    return resultado[:8]


def puntaje(casos_brazo):
    """(positivos conformes, total positivos, negativos conformes, total negativos, indeterminados)."""
    pos = [c for c in casos_brazo.values() if c["veredicto_paper"] == "detecta"]
    neg = [c for c in casos_brazo.values() if c["veredicto_paper"] != "detecta"]
    ind = sum(1 for c in casos_brazo.values() if c["resultado"].startswith("INDETERMINADO"))
    return (sum(1 for c in pos if c["resultado"] == "CONFORME"), len(pos),
            sum(1 for c in neg if c["resultado"] == "CONFORME"), len(neg), ind)


def cumple(casos_brazo):
    """Criterio de S136: 6 de 6 positivos y 3 de 3 negativos, sin indeterminados."""
    pc, pt, nc, nt, ind = puntaje(casos_brazo)
    return pt == 6 and nt == 3 and pc == 6 and nc == 3 and ind == 0


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    raiz = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[1] / "_s136")
    datos = cargar(raiz)
    presentes = [(d, n) for d, n in BRAZOS if d in datos]
    for d, n in BRAZOS:
        if d not in datos:
            print(f"(ausente: {n}, {d}/)")
    if not presentes:
        return
    orden = []
    for d, _ in presentes:
        for k in datos[d]:
            if k not in orden:
                orden.append(k)
    orden.sort()
    ref = datos[presentes[0][0]]
    print("\ncaso  volcan              paper       " + "  ".join(f"{n:>13}" for _, n in presentes))
    for k in orden:
        c = ref.get(k) or next(datos[d][k] for d, _ in presentes if k in datos[d])
        celdas = [f"{corto(datos[d][k]['resultado']) if k in datos[d] else '-':>13}"
                  for d, _ in presentes]
        print(f"{k:5} {c['name'][:18]:18}  {c['veredicto_paper']:10}  " + "  ".join(celdas))
    print()
    for d, n in presentes:
        pc, pt, nc, nt, ind = puntaje(datos[d])
        print(f"{n:14} positivos {pc}/{pt}  negativos {nc}/{nt}  indeterminados {ind}"
              f"   -> {'CUMPLE' if cumple(datos[d]) else 'no cumple'}")


if __name__ == "__main__":
    main()
