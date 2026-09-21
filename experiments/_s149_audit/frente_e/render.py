# Renderiza paginas de un PDF a PNG (regla A95: la capa de texto corrompe operadores). Uso: render.py pdf prefijo dpi idx...
import sys, fitz
pdf, pref, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = fitz.open(pdf)
for i in map(int, sys.argv[4:]):
    pm = d[i].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    out = f"experiments/_s149_audit/frente_e/{pref}_idx{i}.png"; pm.save(out); print(out, pm.width, pm.height)
