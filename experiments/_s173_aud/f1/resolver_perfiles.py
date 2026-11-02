# -*- coding: utf-8 -*-
"""Valor efectivo de la via de MODIS en cada perfil, leido con el cargador real (pipeline.profile, A89).

Preguntas del instrumento:
1. Si un perfil resolviera mal (p. ej. la clave en la seccion equivocada), ¿se veria? Si: se lee la constante
   ENABLE_MODIS_CODIGO_MIROVA que leen los procesadores, no el YAML.
2. Si el cargador estuviera muerto, ¿se veria distinto? Si: cada perfil corre en su propio subproceso y un error
   sale como ERROR con su mensaje (no como False). Control: produccion tiene que dar True en B y False en A, y la
   guardia False en los dos; si no, el instrumento esta mal.
Uso: python resolver_perfiles.py <worktree> <salida.tsv>
"""
import os
import subprocess
import sys
from pathlib import Path

WT = Path(sys.argv[1])
OUT = sys.argv[2]
COD = ("import pipeline.profile as p;"
       "print(p.ENABLE_MODIS_CODIGO_MIROVA, p.SENSOR_MODIS, p.DATA_SUBDIR,"
       " getattr(p,'ENABLE_V750_CODIGO_MIROVA',None), getattr(p,'ENABLE_V375_CODIGO_MIROVA',None), sep='|')")
filas = []
for y in sorted((WT / "pipeline" / "profiles").glob("*.yaml")):
    name = y.stem
    env = dict(os.environ, VRP_PROFILE=name, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", COD], cwd=WT, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    txt = y.read_text(encoding="utf-8", errors="replace")
    ext = next((ln.split(":", 1)[1].strip() for ln in txt.splitlines() if ln.startswith("extends:")), "")
    declara = "enable_modis_codigo_mirova" in txt
    if r.returncode == 0:
        out = r.stdout.strip().splitlines()[-1]
        via, modis, sub, v750, v375 = out.split("|")
    else:
        via = "ERROR:" + (r.stderr.strip().splitlines() or ["?"])[-1][:80]
        modis = sub = v750 = v375 = ""
    filas.append((name, ext, declara, via, modis, sub, v750, v375))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("perfil\textends\tdeclara_clave\tvia_modis\tsensor_modis\tdata_subdir\tvia_v750\tvia_v375\n")
    for f in filas:
        fh.write("\t".join(map(str, f)) + "\n")
n_true = sum(1 for f in filas if f[3] == "True")
n_err = sum(1 for f in filas if f[3].startswith("ERROR"))
prod = next(f for f in filas if f[0] == "mirova_equivalent")
guard = next((f for f in filas if f[0] == "guardia_k_modis"), None)
print(f"perfiles={len(filas)} via_True={n_true} via_True_y_MODIS={sum(1 for f in filas if f[3]=='True' and f[4]=='True')} "
      f"errores={n_err} | control produccion={prod[3]} guardia={guard[3] if guard else 'NO EXISTE'}")
