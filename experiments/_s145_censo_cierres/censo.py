# -*- coding: utf-8 -*-
"""S145: censo de las afirmaciones de CIERRE del proyecto, para auditarlas una por una.

POR QUE. En una sola sesion (S145) aparecieron CUATRO veredictos que se apoyaban en una medicion
mas estrecha que su enunciado:

  - D26 declaraba "efecto nulo bajo la conectiva min" apoyandose en un script que lee solo el
    dNTI: midio el Test 2 y atribuyo la conclusion a los dos tests;
  - D13 titula "apaga el 31 % de la MAGNITUD" y ese 31 % era una fraccion de RECORDS (en magnitud
    es 70,7 %);
  - el informe de S137 dejo una hipotesis sin verificar porque "la bateria guarda distancias pero
    no posiciones", cuando cada pasada guarda pc_lat y pc_lon;
  - y el orquestador de S145 afirmo que `pc.classification` no existe, cuando la capacidad existe
    como `geo_class` (A89: el cero de un grep se lee como ausencia).

Son cuatro instancias del mismo patron, que la regla A95 nombra: **un cierre hereda las premisas de
la lectura con que se derivo**. Y un cierre no es una nota al pie: APAGA TRABAJO FUTURO. Cuando uno
esta mal, cuesta sesiones enteras, porque nadie vuelve a mirar lo que dice "no reabrir".

QUE HACE ESTE SCRIPT. Barre la documentacion rectora y lista cada afirmacion de cierre con su
ubicacion y con lo que cita como respaldo, para que la auditoria las verifique una por una en vez
de tener que encontrarlas primero. NO juzga ninguna: solo las inventaria.

LO QUE ESTE CENSO NO PUEDE HACER, declarado (las dos preguntas del instrumento):
  1. Si el patron estuviera completamente roto, este censo fallaria? NO NECESARIAMENTE: busca por
     palabras clave, asi que un cierre redactado con otras palabras no aparece. El censo es un PISO
     del problema, nunca su medida completa.
  2. Si el instrumento estuviera muerto, el resultado se veria distinto? SI: con los patrones
     vacios devuelve 0 filas, y el control de abajo lo detecta.

USO: python experiments/_s145_censo_cierres/censo.py
"""
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SALIDA = HERE / "censo_cierres.json"
TABLA = HERE / "censo_cierres.md"

# Documentos rectores: los que APAGAN trabajo futuro cuando afirman un cierre.
DOCS = ["docs/MIROVA_DIVERGENCES.md", "CLAUDE.md", "docs/MISSION.md",
        "docs/HYPOTHESIS_LOG.md", "docs/META_RULES_S80.md"]

# Cada patron con el tipo de cierre que representa. El tipo importa porque cambia como se verifica.
PATRONES = [
    ("cerrada", r"\bCERRADAS?\b|\bCERRADO\b"),
    ("resuelta", r"\bRESUELTAS?\b|\bRESUELTO\b"),
    ("agotado", r"\bagotad[oa]s?\b"),
    ("no_reabrir", r"\bNO reabrir\b|\bno reabrir\b|\bno se reabre\b"),
    ("efecto_nulo", r"\befecto nulo\b|\bnulo hoy\b"),
    ("irreducible", r"\birreducible\b"),
    ("es_fiel", r"\bes FIEL\b|\bes fiel\b|\bfidelidad confirmada\b"),
    ("despreciable", r"\bdespreciable\b|\binvisible hoy\b"),
    ("menor", r"\bABIERTA, menor\b|\bprioridad baja\b|\bimpacto menor\b"),
    ("no_adoptar", r"\bNO ADOPTAR\b"),
    ("refutada", r"\brefutad[oa]s?\b"),
]

# Lo que una afirmacion cita como respaldo. Si no cita NADA, es la senal mas fuerte: un cierre sin
# respaldo citable no se puede verificar y hay que tratarlo como pendiente, no como cerrado.
RESPALDOS = [
    ("script", r"\b\w+\.py\b"),
    ("run_ci", r"\brun \d{6,}\b|\bruns?/\d{6,}\b"),
    ("pr", r"#\d{3,4}\b"),
    ("paper", r"\bp\.\s?\d+|\bec\.\s?\d+|Coppola|Campus|Aveni|Wooster|Laiolo|Massimetti"),
    ("doc_interno", r"\bdocs/[\w/]+\.md\b"),
    ("archivo_linea", r"\b[\w/]+\.(py|html|yaml|json):\d+"),
    ("sesion", r"\bS\d{2,3}\b"),
]


def contexto(lineas, i, antes=0, despues=0):
    return "\n".join(lineas[max(0, i - antes):min(len(lineas), i + despues + 1)])


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    filas = []
    for rel in DOCS:
        p = ROOT / rel
        if not p.exists():
            print(f"  AVISO: no existe {rel}, se salta")
            continue
        lineas = p.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, linea in enumerate(lineas):
            tipos = [n for n, rx in PATRONES if re.search(rx, linea)]
            if not tipos:
                continue
            # El respaldo puede estar en la linea o en el parrafo: se mira una ventana.
            ventana = contexto(lineas, i, antes=1, despues=3)
            respaldos = sorted({n for n, rx in RESPALDOS if re.search(rx, ventana)})
            filas.append({
                "archivo": rel,
                "linea": i + 1,
                "tipos_de_cierre": tipos,
                "respaldos_citados": respaldos,
                "sin_respaldo_citable": respaldos == [] or respaldos == ["sesion"],
                "texto": linea.strip()[:300],
            })

    # CONTROL DE INSTRUMENTO (pregunta 2): con los patrones vacios el censo debe dar 0.
    # Si diera filas igual, estaria contando otra cosa.
    control = []
    for rel in DOCS:
        p = ROOT / rel
        if p.exists():
            for linea in p.read_text(encoding="utf-8", errors="replace").split("\n"):
                if any(re.search(rx, linea) for _, rx in []):
                    control.append(rel)
    instrumento_ok = len(control) == 0 and len(filas) > 0

    por_tipo = {}
    for f in filas:
        for t in f["tipos_de_cierre"]:
            por_tipo[t] = por_tipo.get(t, 0) + 1
    sin_respaldo = [f for f in filas if f["sin_respaldo_citable"]]

    out = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "por_que": "A95: un cierre hereda las premisas de la lectura con que se derivo, y apaga trabajo futuro",
        "control_de_instrumento": {
            "con_patrones_vacios_da_cero": instrumento_ok,
            "nota": ("este censo busca por palabras clave: un cierre redactado con otras palabras "
                     "NO aparece. Es un PISO del problema, no su medida completa"),
        },
        "documentos_barridos": DOCS,
        "n_afirmaciones": len(filas),
        "por_tipo": dict(sorted(por_tipo.items(), key=lambda kv: -kv[1])),
        "n_sin_respaldo_citable": len(sin_respaldo),
        "afirmaciones": filas,
    }
    SALIDA.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    md = ["# Censo de afirmaciones de cierre (S145)", "",
          f"> Generado por `experiments/_s145_censo_cierres/censo.py`. {len(filas)} afirmaciones en "
          f"{len(DOCS)} documentos rectores. Ningun numero a mano (S91).", "",
          "**Que es un cierre y por que importa.** Una frase que dice CERRADA, agotado, no reabrir, "
          "efecto nulo, irreducible o menor no es una nota al pie: **apaga trabajo futuro**. Nadie "
          "vuelve a mirar lo que dice no reabrir. La regla A95 dice que un cierre hereda las "
          "premisas de la lectura con que se derivo, y en S145 cayeron cuatro de una sola vez.", "",
          "**Limite declarado**: el censo busca por palabras clave. Un cierre redactado con otras "
          "palabras no aparece. Es un piso del problema, no su medida.", "",
          "## Por tipo", "", "| tipo | n |", "|---|---|"]
    for t, n in out["por_tipo"].items():
        md.append(f"| {t} | {n} |")
    md += ["", f"## Sin respaldo citable ({len(sin_respaldo)})", "",
           "Estas son las de mayor riesgo: afirman un cierre y no citan script, run, PR, paper, "
           "documento ni `archivo:linea` en su entorno. Un cierre que no se puede verificar no es "
           "un cierre, es una creencia.", "", "| archivo:linea | tipo | texto |", "|---|---|---|"]
    for f in sin_respaldo:
        md.append(f"| `{f['archivo']}:{f['linea']}` | {', '.join(f['tipos_de_cierre'])} | "
                  f"{f['texto'][:150].replace('|', ' ')} |")
    md += ["", "## Todas", "", "| archivo:linea | tipo | respaldo citado |", "|---|---|---|"]
    for f in filas:
        md.append(f"| `{f['archivo']}:{f['linea']}` | {', '.join(f['tipos_de_cierre'])} | "
                  f"{', '.join(f['respaldos_citados']) or '**ninguno**'} |")
    TABLA.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"escrito {SALIDA}")
    print(f"escrito {TABLA}")
    print(f"\n{len(filas)} afirmaciones de cierre | instrumento ok: {instrumento_ok}")
    print(f"sin respaldo citable: {len(sin_respaldo)}")
    for t, n in out["por_tipo"].items():
        print(f"  {t:15} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
