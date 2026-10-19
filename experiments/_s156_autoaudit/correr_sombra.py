"""Corre scripts/vigilancia_sombra.main() con una referencia dada y la salida desviada (no escribe en data/).
Uso: python correr_sombra.py <raiz_worktree> <dir_ref> <dir_out>"""
import os
import sys

raiz, ref, out = sys.argv[1:4]
sys.path.insert(0, raiz)
sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.vigilancia_sombra as vs  # noqa: E402

vs.aa.CONS = os.path.join(ref, "registro_vrp_consolidado.csv")
vs.aa.OCR = os.path.join(ref, "registro_vrp_ocr.csv")
vs.OUTDIR = out
vs.main()
