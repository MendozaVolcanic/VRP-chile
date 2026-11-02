# -*- coding: utf-8 -*-
"""Diferencias entre perfiles leidas con pipeline.profile (todas las constantes en mayusculas del modulo).
Pregunta: ¿la guardia es K (= produccion salvo la via, carpeta, nombre y sensores VIIRS)? ¿el laboratorio difiere de
produccion en lo declarado? Control: un perfil contra si mismo da 0 diferencias; produccion contra guardia tiene que
mostrar al menos ENABLE_MODIS_CODIGO_MIROVA en B (si no, el instrumento no ve nada).
Uso: python m_diff_perfiles.py <worktree> <perfil_a> <perfil_b> [...pares]"""
import json
import os
import subprocess
import sys

WT = sys.argv[1]
pares = list(zip(sys.argv[2::2], sys.argv[3::2]))
COD = ("import json,pipeline.profile as p;"
       "print(json.dumps({k:repr(getattr(p,k)) for k in dir(p) if k.isupper()}))")


def leer(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", COD], cwd=WT, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


for a, b in pares:
    A, B = leer(a), leer(b)
    dif = sorted(k for k in set(A) | set(B) if A.get(k) != B.get(k))
    print(f"== {a} vs {b}: {len(dif)} constantes distintas (de {len(set(A) | set(B))})")
    for k in dif:
        print(f"   {k}: {A.get(k)} | {B.get(k)}")
