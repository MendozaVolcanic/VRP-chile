# -*- coding: utf-8 -*-
"""P-E: el evaluador comun y el banco de paridad fijan VRP_PROFILE con setdefault; una variable ya presente gana.

P1: si el perfil del entorno cambiara la lectura, esta medicion lo veria? Si: se llama a la funcion REAL
banco_paridad.es_pasada_diurna_descartada (la que usan evaluador_comun.cargar_lado y pasadas_nocturnas) con una pasada
diurna de VIIRS 375 sobre Lascar, en dos procesos con distinto VRP_PROFILE. P2: control = el proceso sin la variable
(perfil de produccion) debe dar True (descarta la pasada diurna); si el instrumento estuviera muerto daria igual en ambos.
Pasada sintetica: Lascar -23.37, -67.73, 2026-11-05 15:00 UTC (sol alto).
"""
import os, subprocess, sys
ARBOL = r"D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol"
codigo = r"""
import sys, os
sys.path.insert(0, r'%s'); sys.path.insert(0, r'%s/scripts')
import evaluador_comun, banco_paridad as bp
from datetime import datetime, timezone
import pipeline.profile as p
r = bp.es_pasada_diurna_descartada('VIIRS375', -23.37, -67.73, datetime(2026,11,5,15,0,tzinfo=timezone.utc))
print('perfil_efectivo=%%s | descarta_pasada_diurna_V375=%%s' %% (p.PROFILE_NAME, r))
""" % (ARBOL, ARBOL)
for perfil in (None, "_s154_ab_diurno_k_on", "experimental"):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("VRP_PROFILE", None)
    if perfil: env["VRP_PROFILE"] = perfil
    r = subprocess.run([sys.executable, "-I", "-c", codigo], capture_output=True, text=True, encoding="utf-8", env=env, cwd=ARBOL)
    print(f"VRP_PROFILE={perfil!s:24} ->", [l for l in r.stdout.splitlines() if l.startswith("perfil_efectivo")] or r.stderr[-300:])
