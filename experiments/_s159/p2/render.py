"""Renderiza paginas (indice 1-based del PDF) a PNG a 200 dpi, opcionalmente recortadas.
Uso: python render.py <pdf> <pagina> <salida.png> [y0_frac y1_frac]"""
import sys, fitz
pdf, pg, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = fitz.open(pdf); p = d[pg-1]
clip = None
if len(sys.argv) > 5:
    r = p.rect; y0, y1 = float(sys.argv[4]), float(sys.argv[5])
    clip = fitz.Rect(r.x0, r.y0 + y0*r.height, r.x1, r.y0 + y1*r.height)
p.get_pixmap(dpi=200, clip=clip).save(out)
print(out)
