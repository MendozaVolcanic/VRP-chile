"""Frente C S146: LOCALIZA (no valida) en que pagina de un PDF aparece una cadena, usando la capa de texto.
La capa de texto corrompe simbolos: esto solo sirve para saber que pagina renderizar.
P1: si estuviera roto, fallaria? da 0 paginas y se reporta SIN LOCALIZAR, nunca OK. P2: instrumento muerto = excepcion visible.
Uso: python localizar.py <pdf> <cadena1> [<cadena2> ...]   (busqueda sin distinguir mayusculas, espacios normalizados)
"""
import sys, re, fitz
pdf = sys.argv[1]
d = fitz.open(pdf)
for k in sys.argv[2:]:
    hits = []
    for i, p in enumerate(d):
        t = re.sub(r"\s+", " ", p.get_text()).lower()
        if k.lower() in t:
            j = t.index(k.lower())
            hits.append((i+1, t[max(0, j-70): j+110]))
    print(f"== {k!r}: {[h[0] for h in hits]}")
    for h in hits[:3]:
        print("   p", h[0], "|", h[1].encode("ascii", "replace").decode())
