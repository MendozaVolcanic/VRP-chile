# Renderiza paginas de PDF a PNG (A95: citar sólo desde la imagen).
# Uso: python render.py <pdf> <idx0> [idx0 ...] ; idx0 = índice 0-based de PyMuPDF
import sys, fitz, os
DOC = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")
pdf = sys.argv[1]
d = fitz.open(os.path.join(DOC, pdf))
tag = os.path.splitext(pdf)[0][:28].replace(" ", "_")
for s in sys.argv[2:]:
    i = int(s)
    pix = d[i].get_pixmap(dpi=int(os.environ.get("DPI", "200")))
    fn = os.path.join(OUT, f"{tag}_idx{i:03d}.png")
    pix.save(fn); print(fn)
