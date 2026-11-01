import numpy as np, scipy.io as sio, importlib.util, sys
from scipy.ndimage import binary_dilation
from pathlib import Path
D=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375")
spec=importlib.util.spec_from_file_location("dp",sys.argv[1]); DP=importlib.util.module_from_spec(spec); spec.loader.exec_module(DP)
S=sio.loadmat(D/"entradas_v375.mat"); R=sio.loadmat(D/"resultado_v375.mat")
RAD,ALE,NAL=S["RAD"],S["ALE"].astype(int),np.ravel(S["NAL"]).astype(int); BK=R["BK"]; N=134
for n in [22,60]:
    rad=RAD[:,:,n].astype(float); idx=ALE[n,:NAL[n]]-1
    m=np.zeros((N,N),bool); m[idx%N,idx//N]=True
    enm=rad.copy(); enm[m]=np.nan; k=3
    enm[binary_dilation(np.isnan(enm),structure=np.ones((k,k),bool))]=np.nan
    f,_=DP.rellenar(enm,ejes="xy_fila_col"); b=BK[:,:,n].astype(float)
    py_nan_only=np.isnan(f)&~np.isnan(b); ml_nan_only=~np.isnan(f)&np.isnan(b)
    print("escena idx",n,"NaN solo en Python",py_nan_only.sum(),"NaN solo en MATLAB",ml_nan_only.sum(),"NaN en RAD",np.isnan(rad).sum(),"NaN en entrada tras hueco",np.isnan(enm).sum(),"NaN BK",np.isnan(b).sum(),"NaN f",np.isnan(f).sum())
    # distancia minima de esas celdas a las alertas
    rr,cc=np.nonzero(py_nan_only|ml_nan_only)
    if len(rr): print("  distancia minima a una alerta (celdas):", min(np.hypot(rr[:,None]-(idx%N)[None],cc[:,None]-(idx//N)[None]).min(1)))
