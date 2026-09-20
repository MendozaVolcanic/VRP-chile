"""Frente C S146: renderiza paginas de un PDF a PNG para cotejar citas.
Pregunta 1 (si lo medido estuviera roto, fallaria?): si, la pagina renderizada mostraria otro texto.
Pregunta 2 (si el instrumento estuviera muerto?): si, no habria PNG; el script imprime tamano de cada PNG.
Uso: python render.py <pdf> <outdir> <prefijo> <dpi> <paginas 1-based separadas por coma | all> [clip x0,y0,x1,y1 en fraccion]
"""
import sys, os, fitz
pdf, out, pref, dpi, pages = sys.argv[1:6]
clip = sys.argv[6] if len(sys.argv) > 6 else None
doc = fitz.open(pdf)
print("paginas:", len(doc))
pp = range(1, len(doc)+1) if pages == "all" else [int(x) for x in pages.split(",")]
os.makedirs(out, exist_ok=True)
for p in pp:
    page = doc[p-1]
    r = page.rect
    c = None
    if clip:
        x0,y0,x1,y1 = [float(v) for v in clip.split(",")]
        c = fitz.Rect(r.x0+x0*r.width, r.y0+y0*r.height, r.x0+x1*r.width, r.y0+y1*r.height)
    pix = page.get_pixmap(dpi=int(dpi), clip=c)
    fn = os.path.join(out, f"{pref}_p{p:02d}{'_clip' if clip else ''}.png")
    pix.save(fn)
    print(fn, os.path.getsize(fn), pix.width, pix.height)
