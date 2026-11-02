# -*- coding: utf-8 -*-
"""Censo de consumidores del flag de la via «codigo MIROVA» de MODIS (auditor F1, S173).

Las dos preguntas del instrumento:
1. Si un consumidor existiera y la busqueda estuviera rota, ¿se veria? Control positivo: cinco consumidores
   conocidos por lectura previa (process_modis.py lee ENABLE_MODIS_CODIGO_MIROVA; vigilancia_sombra.py lee
   claves_via_modis, alias de via_codigo_mirova; index.html lee "codigo_mirova" por esAnclaHonesta;
   guardia_k_modis.yaml declara la clave; nrt.yml corre el perfil). Si alguno no aparece, la busqueda esta ciega
   y el censo se marca INVALIDO.
2. Si el instrumento estuviera muerto (git grep sin salida), ¿se veria distinto? Si: el total de lineas seria 0 y
   el control positivo fallaria. Ademas se cuenta un patron de control negativo (cadena inventada) que tiene que dar 0.

Formas buscadas (sobre `git grep` de un commit, sin tocar el arbol de trabajo):
  F1 ENABLE_MODIS_CODIGO_MIROVA (constante de pipeline.profile)
  F2 enable_modis_codigo_mirova (clave de perfil)
  F3 via_codigo_mirova (campo del record)
  F4 "codigo_mirova" / 'codigo_mirova' (valor de final_hotspot_source)
  F5 lecturas indirectas: _CODIGO_MIROVA y codigo_mirova con getattr/format, FAMILIAS, alias es_record_via_modis /
     claves_via_modis / claves_via, import de vigilancia o auditoria que las usa
  F6 supone "MODIS de produccion = K": codigo_sha (identifica K por sha), frontera K, final_hotspot_source enumerado
  F7 perfiles que heredan la via por `extends: mirova_equivalent` sin declarar la clave (resuelto aparte con
     pipeline.profile, ver resolver_perfiles.py)
Uso: python censo_consumidores.py <repo> <commit> <salida.tsv>
"""
import re
import subprocess
import sys
from collections import defaultdict

REPO, COMMIT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

FORMAS = {
    "F1": r"ENABLE_MODIS_CODIGO_MIROVA",
    "F2": r"enable_modis_codigo_mirova",
    "F3": r"via_codigo_mirova",
    "F4": r"[\"']codigo_mirova[\"']",
    "F5": r"_CODIGO_MIROVA|CODIGO_MIROVA\b|es_record_via_modis|claves_via_modis|claves_via\b|FAMILIAS\[|codigo_mirova\b",
    "F6": r"codigo_sha|frontera_k|FRONTERA_K|ADOPCION_K|final_hotspot_source",
    "NEG": r"zzq_cadena_que_no_existe_s173",
}
EXCLUIR = ("data/", "experiments/", "tasks/", "docs/superpowers/", "pipeline/profiles/_archive/", ".github/workflows/_archive/")
DOCS_OPERATIVOS = ("docs/FICHA_SDA_VRP_CHILE.md", "docs/MISSION.md", "CLAUDE.md", "README.md", "docs/SINTOMAS.md",
                   "docs/MIROVA_DIVERGENCES.md")


def grep(pat):
    r = subprocess.run(["git", "-C", REPO, "grep", "-n", "-I", "-E", pat, COMMIT, "--"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    filas = []
    for ln in r.stdout.splitlines():
        # formato COMMIT:ruta:linea:texto
        _, ruta, nl, txt = ln.split(":", 3)
        filas.append((ruta, int(nl), txt.strip()))
    return filas


def categoria(ruta):
    if ruta.startswith(".github/workflows/"):
        return "workflow"
    if ruta.startswith("pipeline/profiles/"):
        return "perfil"
    if ruta.startswith("pipeline/"):
        return "pipeline"
    if ruta.startswith("scripts/"):
        return "script"
    if ruta.startswith("tests/"):
        return "prueba"
    if ruta.startswith("frontend/"):
        return "tablero"
    if ruta in DOCS_OPERATIVOS:
        return "doc_operativo"
    return "otro"


por_archivo = defaultdict(lambda: defaultdict(list))
totales = {}
for f, pat in FORMAS.items():
    filas = grep(pat)
    totales[f] = len(filas)
    for ruta, nl, txt in filas:
        if ruta.startswith(EXCLUIR):
            continue
        por_archivo[ruta][f].append(nl)

CONTROL = {
    "pipeline/process_modis.py": "F1",
    "scripts/vigilancia_sombra.py": "F5",
    "frontend/index.html": "F4",
    "pipeline/profiles/guardia_k_modis.yaml": "F2",
}
fallas = [r for r, f in CONTROL.items() if f not in por_archivo.get(r, {})]

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(f"# commit {COMMIT}\n# totales por forma (todo el repo, antes de excluir): {totales}\n")
    fh.write(f"# control positivo {CONTROL}: {'OK' if not fallas else 'FALLA ' + str(fallas)}\n")
    fh.write(f"# control negativo NEG = {totales['NEG']} (tiene que ser 0)\n")
    fh.write("categoria\truta\tformas\tlineas\n")
    for ruta in sorted(por_archivo, key=lambda r: (categoria(r), r)):
        fs = por_archivo[ruta]
        fs = {k: v for k, v in fs.items() if k != "NEG"}
        if not fs:
            continue
        # F6 solo no basta para ser consumidor del flag: se lista aparte
        formas = ",".join(sorted(fs))
        lineas = "; ".join(f"{k}:" + ",".join(map(str, v[:12])) + ("..." if len(v) > 12 else "") for k, v in sorted(fs.items()))
        fh.write(f"{categoria(ruta)}\t{ruta}\t{formas}\t{lineas}\n")
print("control positivo:", "OK" if not fallas else fallas, "| NEG:", totales["NEG"], "| totales:", totales)
print("archivos:", len(por_archivo))
