# P1: si un archivo usara sintaxis solo valida en 3.12 (PEP 701: comillas iguales o barra invertida dentro de {} de un f-string), el runner (3.11) fallaria; este escaneo la veria? Si: tokeniza con 3.12 y marca STRING anidado con la misma comilla que el delimitador.
# P2: control positivo: un texto de prueba con f"{d["k"]}" debe ser marcado.
import tokenize, io, sys, glob, re
def escanear(src):
    mal=[]
    toks=list(tokenize.generate_tokens(io.StringIO(src).readline))
    stack=[]  # (comilla delimitadora, profundidad de {})
    for t in toks:
        if t.type==getattr(tokenize,'FSTRING_START',-1):
            q=t.string[-1] if t.string[-3:] not in ('"""',"'''") else t.string[-3:]
            stack.append([q,0])
        elif t.type==getattr(tokenize,'FSTRING_END',-1):
            stack.pop()
        elif stack:
            if t.type==tokenize.OP and t.string=='{': stack[-1][1]+=1
            elif t.type==tokenize.OP and t.string=='}' : stack[-1][1]-=1 if stack[-1][1]>0 else 0
            elif stack[-1][1]>0:
                if t.type==tokenize.STRING and t.string.lstrip('rbfuRBFU')[:1]==stack[-1][0][:1]:
                    mal.append((t.start[0],'comilla igual dentro de {}',t.string[:30]))
                if t.type==getattr(tokenize,'FSTRING_START',-1) and t.string[-1]==stack[-1][0][:1]:
                    mal.append((t.start[0],'f-string anidado con la misma comilla',t.string))
    # nota: una barra invertida dentro de una expresion {} tambien es solo 3.12
    return mal
ctl = 'd={"k":1}\nx=f"{d["k"]}"\n'
print('control positivo marcado:', bool(escanear(ctl)))
archivos=sorted(glob.glob('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/*.py')+glob.glob('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s162_mxd03/k_en_sha.py')+glob.glob('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s157_prereg_d25/*.py'))
tot=0
for a in archivos:
    r=escanear(open(a,encoding='utf-8').read())
    if r: print(a.split('arbol/')[1], r[:5]); tot+=len(r)
print('archivos escaneados', len(archivos), 'hallazgos', tot)
