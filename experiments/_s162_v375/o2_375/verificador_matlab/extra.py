import numpy as np, scipy.io as sio, json, hashlib
from pathlib import Path
D=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375")
S=sio.loadmat(D/"entradas_v375.mat"); R=sio.loadmat(D/"resultado_v375.mat")
RAD,ALE,NAL=S["RAD"],S["ALE"].astype(int),np.ravel(S["NAL"]).astype(int); BK=R["BK"]
N=134; nanal=0; nanrad=0; escs=[]
for n in range(RAD.shape[2]):
    idx=ALE[n,:NAL[n]]-1; r,c=idx%N,idx//N
    a=np.isnan(BK[r,c,n]).sum(); b=np.isnan(RAD[r,c,n]).sum()
    nanal+=a; nanrad+=b
    if a or b: escs.append(n+1)
print("NaN de BK en pixeles de alerta (total):",nanal,"| NaN de RAD en alertas:",nanrad,"| escenas:",escs)
# valores atipicos: BK en alertas fuera del rango de RAD vecino? razonabilidad
mx=0
for n in range(RAD.shape[2]):
    idx=ALE[n,:NAL[n]]-1; r,c=idx%N,idx//N
    v=RAD[:,:,n]; lo,hi=np.nanmin(v),np.nanmax(v)
    b=BK[r,c,n]; mx=max(mx,float(((b<lo)|(b>hi)).sum()))
print("BK en alertas fuera del rango [min,max] de la escena:",mx)
# fechas: nan por escena RAD
print("escenas con NaN en RAD:",[n+1 for n in range(RAD.shape[2]) if np.isnan(RAD[:,:,n]).any()])
# hash: probar variantes
E=json.loads((D/"entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
tgt=E[0]["grilla_sha256"]; g=RAD[:,:,0]
for nom,b in [("single C",np.ascontiguousarray(g).tobytes()),("single F",np.asfortranarray(g).tobytes()),("f64 C",np.ascontiguousarray(g.astype(float)).tobytes()),("f64 F",np.asfortranarray(g.astype(float)).tobytes())]:
    print(nom, hashlib.sha256(b).hexdigest()==tgt)
