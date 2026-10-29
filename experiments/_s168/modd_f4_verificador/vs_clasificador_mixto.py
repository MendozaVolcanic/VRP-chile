# -*- coding: utf-8 -*-
"""Verificador S168: una mutacion que hace CAER la mayoria de los escenarios con ValueError (en vez de RuntimeError)
¿como la clasifica el medidor? Corre una bateria reducida (E01,E02,E03,E53) y aplica la MISMA formula de clasificacion
de mutar_evaluar_f4.correr (codigo 1 con alguna linea FALLA ASERCION => ATRAPADA)."""
import os, subprocess, sys, tempfile
from pathlib import Path
F = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/elated-bell-62d203/experiments/_s166_modd_f4")
sys.path.insert(0, str(F)); os.environ["F4_RAIZ"] = str(F.parents[1])
import mutar_evaluar_f4 as M
viejo = [v for (n, v, _) in M.MUTACIONES if n == "CONTROL_CAIDA"][0]
for exc in ("RuntimeError", "ValueError"):
    nuevo = viejo.replace("raise RuntimeError(", "raise %s(" % exc) if False else \
        "    raise %s(\"caida de control\")\n    armar_tabla(filas, predicado)" % exc
    src = M.FUENTE.replace(viejo, nuevo)
    ruta = Path(tempfile.mkdtemp(prefix="vs_")) / "ev_mut.py"; ruta.write_text(src, encoding="utf-8")
    env = dict(os.environ, F4_RAIZ=str(M.RAIZ), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(F / "probar_evaluar_f4.py"), "--modulo", str(ruta), "--solo", "E01,E02,E03,E53"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    fallan = [ln.split()[2] for ln in p.stdout.splitlines() if ln.startswith("FALLA ASERCION")]
    clase = {0: "VIVA", 1: "ATRAPADA" if fallan else "ROTA", 2: "CAE", 3: "ROTA"}.get(p.returncode)
    print("excepcion de control =", exc, "| returncode", p.returncode, "| clase del medidor:", clase)
    print("\n".join(l for l in p.stdout.splitlines() if l.startswith(("OK", "CAE", "FALLA", "RESUMEN"))))
