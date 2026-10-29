# -*- coding: utf-8 -*-
"""Verificador S168: corre escenarios de la bateria contra una copia mutada y dice POR QUE falla cada uno (aserción o
la excepcion original, con su traza). Uso: python vs_traza.py NOMBRE_MUT|--ad-hoc VIEJO NUEVO  E53,E58"""
import os, sys, tempfile, traceback
from pathlib import Path
F = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/elated-bell-62d203/experiments/_s166_modd_f4")
sys.path.insert(0, str(F)); os.environ["F4_RAIZ"] = str(F.parents[1])
import mutar_evaluar_f4 as M
a = sys.argv[1:]
if a[0] == "--ad-hoc":
    viejo, nuevo, esc = a[1], a[2], a[3]
elif a[0] == "--identidad":
    viejo = nuevo = ""; esc = a[1]
else:
    esc = a[1]; viejo, nuevo = [(v, n) for (nm, v, n) in M.MUTACIONES if nm.startswith(a[0])][0]
src = M.FUENTE
if viejo:
    assert src.count(viejo) == 1, src.count(viejo)
    src = src.replace(viejo, nuevo)
ruta = Path(tempfile.mkdtemp(prefix="vs_")) / "ev_mut.py"; ruta.write_text(src, encoding="utf-8")
import probar_evaluar_f4 as P
P.EV = P.cargar(str(ruta))
for e in P.ESCENARIOS:
    if e.__name__.split("_")[0] not in esc.split(","):
        continue
    P._ID[0] = 0
    try:
        e(); print("OK", e.__name__)
    except AssertionError as x:
        print("ASERCION", e.__name__, "|", str(x)[:200])
        tb = traceback.extract_tb(x.__traceback__)
        print("   __context__:", repr(x.__context__)[:200])
    except Exception as x:
        print("CAE", e.__name__, type(x).__name__, str(x)[:200])
