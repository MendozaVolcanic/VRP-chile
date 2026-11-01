"""Wrapper del verificador 2: corre vigilancia_sombra.main con OUTDIR desviado.
Uso: python correr.py <raiz> <ref> <out>"""
import os
import sys

raiz, ref, out = sys.argv[1:4]
sys.path.insert(0, raiz)
sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.vigilancia_sombra as vs  # noqa: E402

vs.OUTDIR = out
vs.main(["--cons", os.path.join(ref, "registro_vrp_consolidado.csv"),
         "--ocr", os.path.join(ref, "registro_vrp_ocr.csv")])
