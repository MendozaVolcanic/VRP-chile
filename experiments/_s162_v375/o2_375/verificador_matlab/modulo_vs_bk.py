# La regla Python de la vara (modulo de cd812c746) contra el BK COMPLETO (134x134) de MATLAB, escenas muestreadas.
import numpy as np, scipy.io as sio, importlib.util, sys, time, hashlib
from scipy.ndimage import binary_dilation
from pathlib import Path
D=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375")
spec=importlib.util.spec_from_file_location("dp",sys.argv[1]); DP=importlib.util.module_from_spec(spec); spec.loader.exec_module(DP)
print("sha256 modulo",hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()[:16],flush=True)
S=sio.loadmat(D/"entradas_v375.mat"); R=sio.loadmat(D/"resultado_v375.mat")
RAD,ALE,NAL=S["RAD"],S["ALE"].astype(int),np.ravel(S["NAL"]).astype(int); BK=R["BK"]; N=134
nan_sc=[n for n in range(422) if np.isnan(RAD[:,:,n]).any()]
sel=sorted(set(range(0,422,10))|set(nan_sc))
mx=0; t0=time.time(); peor=None; nnan_dif=0
for n in sel:
    rad=RAD[:,:,n].astype(float); idx=ALE[n,:NAL[n]]-1
    m=np.zeros((N,N),bool); m[idx%N,idx//N]=True
    enm=rad.copy(); enm[m]=np.nan; k=3 if NAL[n]<=4 else 5
    enm[binary_dilation(np.isnan(enm),structure=np.ones((k,k),bool))]=np.nan
    f,info=DP.rellenar(enm,ejes="xy_fila_col")
    b=BK[:,:,n].astype(float)
    nn=(np.isnan(f)!=np.isnan(b)).sum(); nnan_dif+=nn
    ok=~np.isnan(f)&~np.isnan(b)
    d=np.abs(f[ok]-b[ok]).max(); 
    if d>mx: mx,peor=d,n
    print(n,round(time.time()-t0,1),f"{d:.2e}","dif patron NaN",nn,flush=True)
print(f"escenas {len(sel)} (cada 10 + las 12 con NaN en RAD): max |dif| fondo completo {mx:.2e} (escena indice {peor}); celdas con patron NaN distinto: {nnan_dif}")
