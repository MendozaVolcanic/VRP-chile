"""Corre scripts/auto_audit_weekly.main() del worktree con la referencia fresca y la salida desviada.
Uso: python correr_audit.py <raiz_worktree> <dir_ref> <dir_out>"""
import sys
import os

raiz, ref, out = sys.argv[1:4]
sys.path.insert(0, raiz)
sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.auto_audit_weekly as aa  # noqa: E402

aa.CONS = os.path.join(ref, "registro_vrp_consolidado.csv")
aa.OCR = os.path.join(ref, "registro_vrp_ocr.csv")
aa.OUTDIR = out
d = list(aa.alertas_mirova.__defaults__)
d[0], d[1] = aa.CONS, aa.OCR
aa.alertas_mirova.__defaults__ = tuple(d)
aa.main()
