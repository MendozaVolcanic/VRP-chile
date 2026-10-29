# -*- coding: utf-8 -*-
"""Verificador S168: genera una copia mutada (de las MUTACIONES del medidor o a medida) y corre la bateria con --traza
sobre los escenarios pedidos. Uso: python vs_mutar_uno.py NOMBRE|--ad-hoc VIEJO NUEVO  ESCENARIOS"""
import os, subprocess, sys, tempfile
from pathlib import Path
F = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/elated-bell-62d203/experiments/_s166_modd_f4")
sys.path.insert(0, str(F))
import mutar_evaluar_f4 as M
nombre = sys.argv[1]
if nombre == "--ad-hoc":
    viejo, nuevo, esc = sys.argv[2], sys.argv[3], sys.argv[4]
else:
    esc = sys.argv[2]
    viejo, nuevo = [(v, n) for (nm, v, n) in M.MUTACIONES if nm.startswith(nombre)][0]
src = M.FUENTE
print("apariciones del texto viejo:", src.count(viejo))
src = src.replace(viejo, nuevo)
tmp = Path(tempfile.mkdtemp(prefix="vs_"))
ruta = tmp / "ev_mut.py"
ruta.write_text(src, encoding="utf-8")
env = dict(os.environ, F4_RAIZ=str(M.RAIZ), PYTHONIOENCODING="utf-8")
p = subprocess.run([sys.executable, str(F / "probar_evaluar_f4.py"), "--modulo", str(ruta), "--solo", esc, "--traza"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
print(p.stdout[-3500:]); print("returncode", p.returncode); print(p.stderr[-1500:])
