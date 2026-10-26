# Sensibilidad: Delaunay de scipy (sin perturbar) contra MATLAB; muestra que el instrumento distingue triangulaciones.
import numpy as np, scipy.io as sio, time, sys
from scipy.ndimage import binary_dilation
from scipy.spatial import Delaunay
from pathlib import Path
D=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375")
S=sio.loadmat(D/"entradas_v375.mat"); R=sio.loadmat(D/"resultado_v375.mat",squeeze_me=True)
RAD,ALE,NAL=S["RAD"],S["ALE"].astype(int),np.ravel(S["NAL"]).astype(int); LBK=R["LBK"]; N=134
dif=0; nan_=0; mx=0; t0=time.time()
cnt=0
for n in [x for x in range(0,180,3) if not np.isnan(RAD[:,:,x]).any()]:
    cnt+=1
    rad=RAD[:,:,n].astype(float); idx=ALE[n,:NAL[n]]-1; q=np.c_[idx%N,idx//N].astype(float)
    m=np.zeros((N,N),bool); m[idx%N,idx//N]=True
    k=3 if NAL[n]<=4 else 5
    ex=binary_dilation(m|np.isnan(rad),structure=np.ones((k,k),bool))
    ii,jj=np.nonzero(~ex)
    tri=Delaunay(np.c_[ii,jj].astype(float)); s=tri.find_simplex(q)
    if (s<0).any(): nan_+=1; continue
    T=tri.transform[s]; b=np.einsum('nij,nj->ni',T[:,:2],q-T[:,2]); bc=np.c_[b,1-b.sum(1)]
    v=rad[ii[tri.simplices[s]],jj[tri.simplices[s]]]
    lb=(v*bc).sum()
    r=abs(lb-LBK[n])/abs(LBK[n]); mx=max(mx,r); dif+= r>1e-9
    if cnt%20==0: print(n,round(time.time()-t0,1),flush=True)
print(f"scipy Delaunay sin perturbar vs MATLAB: escenas con rel L_bk > 1e-9: {dif} de {cnt-nan_} (cada 3.a escena sin NaN en RAD); fuera de envolvente: {nan_}; max rel {mx:.3f}")
