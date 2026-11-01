"""Efecto real de M10: si leer_frontera_k devuelve None (JS reformateado), que veredicto sale."""
import sys, os
raiz, ref, out = sys.argv[1:4]
sys.path.insert(0, raiz); sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.auto_audit_weekly as aa
aa.CONS = os.path.join(ref, "registro_vrp_consolidado.csv"); aa.OCR = os.path.join(ref, "registro_vrp_ocr.csv")
aa.OUTDIR = out
d = list(aa.alertas_mirova.__defaults__); d[0], d[1] = aa.CONS, aa.OCR; aa.alertas_mirova.__defaults__ = tuple(d)
aa.leer_frontera_k = lambda path=None: None
aa.main()
