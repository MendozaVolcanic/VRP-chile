"""Corre scripts/auto_audit_weekly.py del worktree con la salida en otra carpeta (argv[1])."""
import sys, os
RAIZ = r"D:/vrp-trabajo/worktrees/s172-modd-encendido"
sys.path.insert(0, os.path.join(RAIZ, "scripts")); sys.path.insert(0, RAIZ)
import auto_audit_weekly as aa
aa.OUTDIR = sys.argv[1]
aa.main()
