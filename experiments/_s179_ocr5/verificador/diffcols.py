import sys
from PIL import Image
import numpy as np
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int); b=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(int)
d=(abs(a-b).sum(axis=2)>60)[100:300]
cols=d.sum(axis=0)
out=[(x,int(c)) for x,c in enumerate(cols) if c>0]
# agrupar
groups=[]; 
for x,c in out:
    if groups and x-groups[-1][1]<=1: groups[-1][1]=x; groups[-1][2]+=c
    else: groups.append([x,x,c])
print(sys.argv[1]); print('  grupos (x0,x1,n):',[tuple(g) for g in groups])
