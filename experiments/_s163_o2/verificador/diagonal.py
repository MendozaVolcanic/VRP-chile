"""Hipotesis propia: en alertas de un pixel (hueco 3x3) el fondo en el centro cae en 4 puntos cocirculares (cruz a +-2); la
interpolacion lineal depende de que diagonal elija la triangulacion. Pregunta 1: el fondo de MATLAB (BK guardada) coincide con
UNO de los dos promedios diagonales? Pregunta 2 (puede dar distinto de cero): cuando no coincide con ninguno, el script lo cuenta."""
import json, numpy as np, scipy.io as sio
from pathlib import Path
B=Path(r"C:\vrp-trabajo\s163-verif-o2\rama\experiments\_s163_o2"); R=Path(r"C:\vrp-trabajo\s163-verif-o2")
E=sio.loadmat(B/"entradas_o2.mat"); M=sio.loadmat(B/"resultado_o2.mat"); OP=sio.loadmat(R/"octave/resultado_octave_propio.mat")
etq=json.loads((B/"entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
al=[np.asarray(x).ravel().astype(int) for x in M["ALERTAS"].ravel()]
BKm=M["BK"].ravel(); BKo=OP["BK"].ravel()
out=[]
for j in range(191):
    if len(al[j])!=1: continue
    r,c=(al[j][0]-1)%67,(al[j][0]-1)//67
    if r<3 or c<3 or r>63 or c>63: continue
    m13=E["M13"][:,:,j]
    cr=[m13[r-2,c],m13[r+2,c],m13[r,c-2],m13[r,c+2]]
    blk=m13[r-2:r+3,c-2:c+3]
    if not np.isfinite(blk).all(): out.append((j,'NaN en 5x5')); continue
    vert=(m13[r-2,c]+m13[r+2,c])/2   # misma columna, filas +-2 (diagonal "vertical")
    horz=(m13[r,c-2]+m13[r,c+2])/2
    bm=np.asarray(BKm[j])[r,c]; bo=np.asarray(BKo[j])[r,c]
    tag=lambda b: 'vert' if abs(b-vert)<1e-9 else ('horz' if abs(b-horz)<1e-9 else 'otro')
    out.append((j,etq[j]['id'],etq[j].get('metodo',''),round(vert,5),round(horz,5),round(bm,5),tag(bm),round(bo,5),tag(bo)))
import collections
for o in out: print(o)
print("MATLAB:",collections.Counter(o[6] for o in out if len(o)>6),"| shim Octave:",collections.Counter(o[8] for o in out if len(o)>6))
print("MATLAB elige el mayor de los dos?:",collections.Counter(('mayor' if o[5]>=max(o[3],o[4])-1e-9 else 'menor' if o[5]<=min(o[3],o[4])+1e-9 else 'otro') for o in out if len(o)>6))
