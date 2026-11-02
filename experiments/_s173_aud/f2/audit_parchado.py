# -*- coding: utf-8 -*-
"""Envoltorio de MEDICIÓN (no es un arreglo del repo): corre main() de scripts/auto_audit_weekly.py del worktree con
REGIMENES ampliado con "VIA_MODIS" en memoria, sólo para ver qué diría el audit después de la caída del hallazgo 205."""
import importlib.util, os, sys
raiz = sys.argv[1]
os.chdir(raiz); sys.path.insert(0, raiz + "/scripts"); sys.path.insert(0, raiz)
spec = importlib.util.spec_from_file_location("auto_audit_weekly", raiz + "/scripts/auto_audit_weekly.py")
aa = importlib.util.module_from_spec(spec); sys.modules["auto_audit_weekly"] = aa; spec.loader.exec_module(aa)
aa.REGIMENES = aa.REGIMENES + ("VIA_MODIS",)
aa.main()
