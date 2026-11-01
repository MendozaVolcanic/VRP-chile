import sys; sys.argv=['x']
import numpy as np
exec(open('mi_regla.py').read().split('if __name__')[0])
P=[(r,c) for r in range(4) for c in range(4)]
for s in (1,-1):
    T,info=triangular(P,s)
    print(s,info, sorted(tuple(sorted(t)) for t in T)[:6])
print(incircle_sign((0,0),(1,0),(0,1),(1,1),1), incircle_sign((0,0),(1,0),(0,1),(1,1),-1))
