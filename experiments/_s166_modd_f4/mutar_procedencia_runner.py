# -*- coding: utf-8 -*-
"""S170: mutaciones de las líneas nuevas de la procedencia del runner (procedencia_runner.py y la aceptación en
externos_f4.procedencia y datos_runner). Cada mutación cambia UNA condición en una copia de la carpeta fuera del repo y
corre probar_procedencia_runner.py contra la copia. Clasificación como mutar_evaluar_f4.py: ATRAPADA sólo con alguna
aserción y ninguna caída; ATRAPADA_CON_CAIDAS no cuenta. Controles: IDENTIDAD tiene que salir VIVA, CONTROL_CAIDA
(excepción al entrar a compatible) CAE y CONTROL_ROTA (error de sintaxis) ROTA; si no, NO VALE y código 1. Escribe una
línea por mutación en --progreso (corrida larga) y para si el disco del temporal baja de 3 GB.
Uso: python mutar_procedencia_runner.py --tmp DIR [--progreso ARCHIVO] [--salida ARCHIVO]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
PR, EX = "procedencia_runner.py", "externos_f4.py"
MUTACIONES = [
    ("IDENTIDAD", None, None, None),
    ("CONTROL_ROTA", PR, 'ALIAS_EVALUAR = "E"', 'ALIAS_EVALUAR = = "E"'),
    ("CONTROL_CAIDA", PR, '    raiz = Path(raiz)\n    desciende', '    raise RuntimeError("caida de control")\n    desciende'),
    ("R1_sin_ascendencia", PR, '"ok": desciende and not cambiados and not distinto', '"ok": not cambiados and not distinto'),
    ("R2_sin_archivos_runner", PR, '"ok": desciende and not cambiados and not distinto', '"ok": desciende and not distinto'),
    ("R3_sin_evaluar_alcanzable", PR, '"ok": desciende and not cambiados and not distinto', '"ok": desciende and not cambiados'),
    ("R4_sin_cierre", PR, "        pend += [m.id for m in ast.walk(defs[n])", "        pass\n        [m.id for m in ast.walk(defs[n])"),
    ("R5_sin_sentencias_de_modulo", PR, 'al_importar["sentencia_%03d" % len(al_importar)] = st', "pass"),
    ("R6_main_cuenta", PR, "elif _es_bloque_main(st):", "elif False:"),
    ("R7_pipeline_fuera", PR, '".github/workflows/probe-s168-modd-f4.yml", "pipeline/", ', '".github/workflows/probe-s168-modd-f4.yml", '),
    ("R8_numeracion_global", PR, 'al_importar["sentencia_%03d" % len(al_importar)] = st', 'al_importar["sentencia_%03d" % id(st)] = st'),
    ("X1_sin_compat", EX, 'runner and runner["compat"]["ok"] and all(', "runner and all("),
    ("X2_sin_todas_en_runner", EX, ' and all(c.get("commit") == runner["commit"] for c in cab))', ")"),
    ("X3_evaluar_de_la_lectura", EX, 'commit_tag, tag, sha_evaluar = runner["commit"], runner["tag"], runner["sha_evaluar"]',
     'commit_tag, tag = runner["commit"], runner["tag"]'),
    ("X4_compat_siempre_ok", EX, '"compat": PR.compatible(raiz, commit_r, commit_lectura)}', '"compat": {"ok": True}}'),
    ("X5_tag_de_la_lectura", EX, 'commit_tag, tag, sha_evaluar = runner["commit"], runner["tag"], runner["sha_evaluar"]',
     'commit_tag, sha_evaluar = runner["commit"], runner["sha_evaluar"]'),
]


def clasificar(codigo, fallan, caen):
    if codigo == 1:
        return ("ATRAPADA_CON_CAIDAS" if caen else "ATRAPADA") if fallan else "ROTA"
    return {0: "VIVA", 2: "CAE", 3: "ROTA"}.get(codigo, "CODIGO_%s" % codigo)


def correr(nombre, archivo, viejo, nuevo, tmp):
    base = Path(tempfile.mkdtemp(prefix="m_%s_" % nombre, dir=tmp))
    dest = base / "experiments" / "_s166_modd_f4"
    dest.mkdir(parents=True)
    for p in AQUI.glob("*.py"):
        shutil.copy(p, dest / p.name)
    if archivo:
        f = dest / archivo
        t = f.read_text(encoding="utf-8")
        if t.count(viejo) != 1:
            return nombre, "NO APLICA (%d apariciones)" % t.count(viejo), ""
        f.write_text(t.replace(viejo, nuevo), encoding="utf-8")
    env = dict(os.environ, F4_RAIZ=str(RAIZ), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(dest / "probar_procedencia_runner.py"), "--dir", str(dest),
                        "--tmp", str(base / "t")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=str(RAIZ))
    # F4_RAIZ: la copia de la batería usa el repo real en las partes C y D (tags y datos_runner)
    fallan = [ln.split()[2] for ln in p.stdout.splitlines() if ln.startswith("FALLA ASERCION")]
    caen = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("CAE ")]
    resumen = [ln for ln in p.stdout.splitlines() if ln.startswith("RESUMEN")]
    return nombre, clasificar(p.returncode, fallan, caen), "%s | aserción: %s | caen: %s" % (
        resumen[0] if resumen else (p.stdout + p.stderr)[-200:].replace("\n", " "), ",".join(fallan) or "-",
        ",".join(caen) or "-")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--progreso", default=None)
    ap.add_argument("--salida", default=str(AQUI / "mutar_procedencia_runner_salida.txt"))
    a = ap.parse_args()
    Path(a.tmp).mkdir(parents=True, exist_ok=True)
    res = []
    for m in MUTACIONES:
        if shutil.disk_usage(a.tmp).free < 3 * 1024 ** 3:
            res.append((m[0], "NO CORRIDA", "disco del temporal bajo 3 GB"))
            break
        r = correr(*m, a.tmp)
        res.append(r)
        if a.progreso:
            with open(a.progreso, "a", encoding="utf-8") as fh:
                fh.write("%s %s %s\n" % r)
    lineas = ["%-34s %-12s %s" % r for r in res]
    clase = dict((r[0], r[1]) for r in res)
    muts = [r for r in res if not r[0].startswith(("IDENTIDAD", "CONTROL_"))]
    malos = [c for c, debe in (("IDENTIDAD", "VIVA"), ("CONTROL_CAIDA", "CAE"), ("CONTROL_ROTA", "ROTA"))
             if clase.get(c) != debe]
    lineas += ["", "CONTROLES: identidad %s, caída %s, rota %s" % (clase.get("IDENTIDAD"), clase.get("CONTROL_CAIDA"),
                                                                 clase.get("CONTROL_ROTA")),
               "MUTACIONES: %d de %d atrapadas por aserción; otras: %s" % (
                   sum(1 for r in muts if r[1] == "ATRAPADA"), len(muts),
                   [(r[0], r[1]) for r in muts if r[1] != "ATRAPADA"])]
    if malos:
        lineas.append("NO VALE: controles que no salen como deben: %s" % malos)
    txt = "\n".join(lineas)
    print(txt)
    Path(a.salida).write_text(txt + "\n", encoding="utf-8")
    sys.exit(1 if malos or len(res) < len(MUTACIONES) else 0)


if __name__ == "__main__":
    main()
