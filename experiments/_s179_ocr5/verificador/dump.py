# Vuelca los pixeles RGB de una ventana como codigos: K negro/gris oscuro, g gris, R rojo, p rosa, G verde, . blanco/claro
import sys
from PIL import Image
import numpy as np
f,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6])
a=np.asarray(Image.open(f).convert('RGB')).astype(int)
def code(p):
    r,g,b=p; lum=(r+g+b)/3
    if abs(r-g)<25 and abs(g-b)<25:
        return 'K' if lum<100 else ('k' if lum<160 else ('g' if lum<215 else '.'))
    if g>180 and r<120: return 'G'
    if r>180 and g<110: return 'R'
    if r>200 and r-g>30: return 'p'
    if r-g>20 and lum<180: return 'm'   # mezcla rojo oscuro/negro
    return '?'
print('     '+''.join(str(x%10) for x in range(x0,x1+1)), ' (x desde',x0,')')
for y in range(y0,y1+1):
    print(f'{y:4d} '+''.join(code(a[y,x]) for x in range(x0,x1+1)))
if len(sys.argv)>6:
    for y in range(y0,y1+1): print(y,[tuple(a[y,x]) for x in range(x0,x1+1)])
