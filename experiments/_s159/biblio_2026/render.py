# -*- coding: utf-8 -*-
"""render.py <pdf> <pagina_idx_1based> <png_out> [dpi]: renderiza una pagina a imagen (A95)."""
import sys, fitz
pdf, pag, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 150
doc = fitz.open(pdf)
doc[pag - 1].get_pixmap(dpi=dpi).save(out)
print(out, doc.page_count, "paginas")
