"""Corre scripts/vigilancia_sombra.py del worktree con la salida en argv[1] (data/ sólo se lee)."""
import os, sys
RAIZ = r"D:/vrp-trabajo/worktrees/s172-modd-encendido"
sys.path.insert(0, os.path.join(RAIZ, "scripts")); sys.path.insert(0, RAIZ)
import vigilancia_sombra as vs
vs.OUTDIR = sys.argv[1]
os.makedirs(sys.argv[1], exist_ok=True)
vs.main([])
