"""Lee flags resueltos desde pipeline.profile (A89) para un perfil dado por VRP_PROFILE."""
import os, importlib, sys
sys.path.insert(0,'.')
import pipeline.profile as p
names=[n for n in dir(p) if n.isupper() and any(k in n for k in ('TEST1','PROSE','B22','BT_','D22','COMPUERTA','GATE','ROI1','KEEP','LOCAL','CLOUD','FLOOR','D25','VENT','DAYTIME'))]
print('PERFIL', os.environ.get('VRP_PROFILE'))
for n in sorted(names):
    v=getattr(p,n)
    if isinstance(v,(bool,int,float,str)) or v is None: print(f'  {n} = {v!r}')
