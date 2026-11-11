# Recorta y amplia (vecino mas cercano) una zona de un PNG. uso: crop.py in x0 y0 x1 y1 escala out
import sys
from PIL import Image
f,x0,y0,x1,y1,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open(f).convert('RGB').crop((x0,y0,x1,y1))
im=im.resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST); im.save(out); print(out,im.size)
