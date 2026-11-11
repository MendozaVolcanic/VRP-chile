# Lista los tallos (lineas verticales) del panel "Last Month": x, color, y del tope del conjunto tallo+marcador.
# uso: stems.py imagen [xmin xmax]
import sys
from PIL import Image
import numpy as np
f=sys.argv[1]; xmin=int(sys.argv[2]) if len(sys.argv)>2 else 277; xmax=int(sys.argv[3]) if len(sys.argv)>3 else 806
a=np.asarray(Image.open(f).convert('RGB')).astype(int)
R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
lum=(R+G+B)/3
neutral=(abs(R-G)<25)&(abs(G-B)<25)
dark=neutral&(lum<150)
red=(R>180)&(G<110)&(B<110)
pink=(R>200)&(G>=110)&(G<215)&(B>=110)&(B<215)&(R-G>30)
green=(G>180)&(R<120)&(B<120)
Y0,Y1=112,293   # interior del panel (marco en 110-111 y 294-295)
def runs(mask,x):
    col=mask[Y0:Y1+1,x]; out=[]; s=None
    for i,v in enumerate(col):
        if v and s is None: s=i
        if (not v) and s is not None: out.append((Y0+s,Y0+i-1)); s=None
    if s is not None: out.append((Y0+s,Y1))
    return out
for x in range(xmin,xmax+1):
    line=[]
    for name,m in (('negro',dark),('rojo',red),('rosa',pink),('verde',green)):
        r=[(u,v) for (u,v) in runs(m,x) if v-u>=1]
        if r: line.append(f"{name}:{r}")
    if line: print(x,' '.join(line))
