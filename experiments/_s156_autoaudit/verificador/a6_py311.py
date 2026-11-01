"""A6: busca sintaxis de f-string de 3.12 (PEP 701) que rompe en Python 3.11 (version del CI)."""
import sys, tokenize, io
for path in sys.argv[1:]:
    src = open(path, encoding="utf-8").read()
    pila, malos = [], []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.FSTRING_START:
            q = tok.string.lstrip("fFrRbB")
            if pila and (q[0] in pila[-1] or "\\" in tok.string):
                malos.append((tok.start, "f-string anidada con la misma comilla"))
            pila.append(q)
        elif tok.type == tokenize.FSTRING_END:
            pila.pop()
        elif pila and tok.type == tokenize.STRING:
            if pila[-1][0] in tok.string or "\\" in tok.string:
                malos.append((tok.start, tok.string[:40]))
        elif pila and tok.type == tokenize.COMMENT:
            malos.append((tok.start, "comentario en f-string"))
    print(path, "violaciones 3.11:", malos)
