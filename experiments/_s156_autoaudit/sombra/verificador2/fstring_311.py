"""¿Hay f-strings que sólo parsean en 3.12+ (PEP 701: misma comilla anidada o barra invertida en la expresión)?
El CI usa 3.11. Uso: python fstring_311.py <archivo>..."""
import sys
import tokenize

for path in sys.argv[1:]:
    malos = []
    with open(path, "rb") as fh:
        pila = []
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.FSTRING_START:
                q = tok.string.lstrip("fFrRbB")
                pila.append((q, 0))
            elif tok.type == tokenize.FSTRING_END:
                pila.pop()
            elif pila and tok.type == tokenize.STRING:
                qin = tok.string.lstrip("fFrRbBuU")[:1]
                if pila[-1][0][0] == qin:
                    malos.append((tok.start[0], tok.line.strip()[:100]))
            elif pila and tok.type == tokenize.FSTRING_START:
                pass
    print(path, "f-strings 3.12-only:", malos or "ninguno")
