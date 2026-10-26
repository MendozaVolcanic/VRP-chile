"""Verificador S163 O2. Preguntas del instrumento en cada bloque:
 (a) mide lo que dice: se comparan matrices por indice de escena con el orden verificado contra IDX_O1 y etiquetas;
 (b) puede dar distinto de cero: control positivo = Octave propio (shim) vs MATLAB; deben salir diferencias."""
import json, hashlib, sys
from pathlib import Path
import numpy as np, scipy.io as sio
R = Path(r"C:\vrp-trabajo\s163-verif-o2"); B = R/"rama/experiments/_s163_o2"
O1D = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1"); P = O1D/"o2_paquete"
EXP = O1D.parents[1]
sys.path.insert(0, str(EXP/"_s158_audit_r2"/"oraculo")); import mirova_v750_r2 as R2
import importlib.util
sp = importlib.util.spec_from_file_location("o1p", EXP/"_s158_oraculo_mirova"/"mirova_v750.py"); O1 = importlib.util.module_from_spec(sp); sp.loader.exec_module(O1)
md5 = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()
print("== 1. md5 de entradas (rama vs paquete S159 vs md5 declarado)")
decl = {"entradas_o2.mat":"fb849b6a96a9d348e75cf502e21a326c","MIROVA_VIIRS750_VRP.m":"b0ceebb2b7864cd27c145dc8d41968cc","MIROVA_VIIRS750_hotspot_detection.m":"ddffea3672a08e5aa17c702f72d72170","correr_o2.m":"e6761d861b61009b32991afd3f350986"}
for f,d in decl.items(): print(f, md5(B/f)==d, md5(P/f)==d, md5(B/f))
print("resultado_o2.mat rama/paquete:", md5(B/"resultado_o2.mat"), md5(P/"resultado_o2.mat"))
print("== 2. orden de escenas")
etq = json.loads((B/"entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
etq0 = json.loads((P/"entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
E = sio.loadmat(B/"entradas_o2.mat"); E0 = sio.loadmat(O1D/"entradas.mat")
idx = E["IDX_O1"].ravel().astype(int) - 1   # IDX_O1 de MATLAB es 1-based
print("IDX_O1-1 == json idx_o1:", list(idx)==[e["idx_o1"] for e in etq]); print("etiquetas rama==paquete:", etq==etq0, "| unicos:", len(set(idx)))
ok = all(np.array_equal(E["M13"][:,:,j], E0["M13"][:,:,idx[j]], equal_nan=True) and np.array_equal(E["M15"][:,:,j], E0["M15"][:,:,idx[j]], equal_nan=True) and np.array_equal(E["BOX"][:,:,j], E0["BOX"][:,:,idx[j]]) and E["DAY"][0,j]==E0["DAY"][0,idx[j]] and E["SG"][0,j]==E0["SG"][0,idx[j]] for j in range(311))
print("escena j de entradas_o2 == escena IDX_O1[j] de entradas.mat (M13,M15,BOX,DAY,SG) en 311:", ok)
M = sio.loadmat(B/"resultado_o2.mat"); print("version_matlab:", M["version_matlab"])
al = [np.asarray(x).ravel().astype(int) for x in M["ALERTAS"].ravel()]
print("len ALERTAS", len(al), "VRP", M["VRP"].shape, "con alerta", sum(len(a)>0 for a in al))
print("== 3. deteccion vs Octave S159 (salida_original) y vs Octave PROPIO (corrida hoy)")
D = sio.loadmat(O1D/"salida_original.mat"); A = D["ALERTAS"].ravel().astype(int); off = D["OFFSET"].ravel().astype(int); n = D["NALERT"].ravel().astype(int)
OP = sio.loadmat(R/"octave/resultado_octave_propio.mat"); alp = [np.asarray(x).ravel().astype(int) for x in OP["ALERTAS"].ravel()]
d1 = sum(1 for j in range(311) if list(al[j]) != A[off[idx[j]]:off[idx[j]]+n[idx[j]]].tolist())
d2 = sum(1 for j in range(311) if list(al[j]) != list(alp[j]))
d2set = sum(1 for j in range(311) if sorted(al[j]) != sorted(alp[j]))
print("distintas (secuencia exacta) vs S159:", d1, "| vs Octave propio:", d2, "| como conjunto:", d2set)
print("control: n escenas con alerta MATLAB/Octave propio:", sum(len(a)>0 for a in al), sum(len(a)>0 for a in alp), "| total pixeles alertados", sum(len(a) for a in al))
print("== 4. consistencia interna de resultado_o2.mat: VRP == (LHOT-LBK)*1.97e7*0.5625/1e6; LBK == sum(BK[a]); DL")
VRP = M["VRP"].ravel(); LH = M["LHOT"].ravel(); LB = M["LBK"].ravel(); DL = M["DL"].ravel(); NP = M["NPIX"].ravel()
con = np.array([len(a)>0 for a in al])
f = (LH-LB)*1.97e7*0.5625/1e6
print("max |VRP-formula|/|VRP| (166):", np.max(np.abs(VRP[con]/f[con]-1)), "| DL==LHOT-LBK:", np.max(np.abs(DL[con]-(LH[con]-LB[con]))))
print("NPIX==len(alert) en todas:", all(NP[j]==len(al[j]) for j in range(311)))
BK = M["BK"].ravel(); mx=0; nb=0
for j in range(311):
    if con[j] and j<=190:
        bk = np.asarray(BK[j]); 
        if bk.size==0: print("BK vacio", j); continue
        s = np.nansum(bk.ravel(order="F")[al[j]-1]); mx=max(mx,abs(s-LB[j])); nb+=1
print("BK guardadas con alerta:", nb, "max |sum(BK[a])-LBK|:", mx)
LHr = np.array([np.nansum(E["M13"][:,:,j].ravel(order="F")[al[j]-1]) if con[j] else np.nan for j in range(311)])
print("max |LHOT - sum(M13[a]) recomputado|:", np.nanmax(np.abs(LHr[con]-LH[con])))
print("== 5. VRP: conteos del punto 4 (recomputados con script propio)")
V = sio.loadmat(O1D/"salida_vrp_octave_shim.mat"); Vs = V["VRP"].ravel()
Vp = OP["VRP"].ravel()
rows=[]
for j in np.where(con)[0]:
    m13 = E["M13"][:,:,j]; mk = np.zeros(m13.shape,bool); mk[np.unravel_index(al[j]-1, m13.shape, order="F")] = True
    rows.append((j, VRP[j], Vs[idx[j]], R2.vrp(m13,mk)["VRP_MW"], O1.vrp(m13, al[j]-1)[0], Vp[j]))
X = np.array(rows)
print("n con alerta:", len(X))
for c,nom in ((2,"shim S159"),(5,"shim Octave propio"),(3,"segundo port R2"),(4,"primer port O1")):
    r = np.abs(X[:,c]/X[:,1]-1); print(f"{nom:20s} >1%: {(r>0.01).sum():3d}  <1e-9: {(r<1e-9).sum():3d}  intermedios(1e-9..1%): {((r>=1e-9)&(r<=0.01)).sum():3d}  max {r.max():.4f}  med {np.median(r):.2e}  nan:{np.isnan(r).sum()}")
print("min VRP MATLAB:", X[:,1].min(), "(division por cero no aplica si >0)")
print("shim S159 == shim propio (control reproducibilidad):", np.max(np.abs(X[:,2]/X[:,5]-1)))
print("MATLAB vs ensayo Octave de S159 (prueba_o2_en_octave):")
EN = sio.loadmat(O1D/"prueba_o2_en_octave"/"resultado_o2_ENSAYO_OCTAVE_CON_SHIM_no_es_MATLAB.mat"); print(" version:", EN.get("version_matlab"))
r = np.abs(EN["VRP"].ravel()[con]/VRP[con]-1); print(" ensayo/MATLAB-1 >1%:", (r>0.01).sum(), "<1e-9:", (r<1e-9).sum(), "| ensayo == shim propio:", np.max(np.abs(EN['VRP'].ravel()[con]/Vp[con]-1)))
print("Etna: MATLAB LBK %.9f VRP %.1f | Octave propio LBK %.9f VRP %.1f" % (LB[0], VRP[0]*1e6, OP["LBK"].ravel()[0], Vp[0]*1e6))
print("== 6. quienes son las diferencias >1% (por npix y familia)")
r = np.abs(X[:,2]/X[:,1]-1); bad = X[r>0.01]
import collections
print("shim >1% por npix:", sorted(collections.Counter(int(NP[int(j)]) for j in bad[:,0]).items()))
print("todas por npix (n escenas):", sorted(collections.Counter(int(NP[int(j)]) for j in X[:,0]).items()))
one = [int(j) for j in X[:,0] if NP[int(j)]==1]
for c,nom in ((2,"shim"),(3,"R2"),(4,"O1")):
    rr = np.array([abs(X[X[:,0]==j][0,c]/X[X[:,0]==j][0,1]-1) for j in one]); print(f" npix==1 ({len(one)}): {nom} >1%: {(rr>0.01).sum()}")
# ninguno de los tres calza
nada=[j for j in one if all(abs(X[X[:,0]==j][0,c]/X[X[:,0]==j][0,1]-1)>0.01 for c in (2,3,4))]
print(" npix==1 donde NINGUN modelo calza (>1% los tres):", len(nada), [etq[j]["id"]+"|"+str(etq[j].get("metodo",""))+"|"+str(etq[j].get("caja","")) for j in nada])
print("max diferencia entre los tres modelos y MATLAB, por modelo y hasta 3 peores:")
for c,nom in ((2,"shim"),(3,"R2"),(4,"O1")):
    r = np.abs(X[:,c]/X[:,1]-1); o = np.argsort(-r)[:3]; print(nom, [(etq[int(X[i,0])]["id"], int(NP[int(X[i,0])]), round(float(r[i]),4)) for i in o])
print("== 7. Villarrica 2026-09-19 05:48 nearest")
for j,e in enumerate(etq):
    if e["id"].startswith("Villarrica_2026-09-19_0548"):
        print(j, e, "alertas MATLAB", al[j], "Octave", alp[j], "VRP MATLAB %.4f shim %.4f R2 %.4f O1 %.4f" % tuple(X[X[:,0]==j][0,[1,2,3,4]]) if con[j] else "sin alerta")

print("== 8. Villarrica 05:48 nearest, fondo de MATLAB vs modelos simples (BK guardada de MATLAB)")
for j in (79,80,86):
    a=al[j]; r0,c0=(a[0]-1)%67,(a[0]-1)//67
    m13=E["M13"][:,:,j]; bk=np.asarray(M["BK"].ravel()[j])
    print("escena",j,etq[j]["id"],etq[j]["metodo"],etq[j]["caja"],"pixel(fila,col)",(r0,c0),"npix",len(a))
    print(" M13 vecindad 5x5 (L):"); print(np.round(m13[r0-2:r0+3,c0-2:c0+3],4))
    print(" L pixel", m13[r0,c0], "| fondo MATLAB", bk[r0,c0], "| fondo shim Octave propio", np.asarray(OP["BK"].ravel()[j])[r0,c0])
    n=m13[r0-2:r0+3,c0-2:c0+3]
    print(" prueba de modelos simples: media diag(1,5)/(2,4)?", (n[0,0]+n[4,4])/2,(n[0,4]+n[4,0])/2,"| media 4 esquinas",(n[0,0]+n[0,4]+n[4,0]+n[4,4])/4,"| media 4 bordes",(n[0,2]+n[4,2]+n[2,0]+n[2,4])/4,"| media anillo 16", (n.sum()-n[1:4,1:4].sum())/16)
    print(" hueco NaN en la BK de MATLAB? nan:", int(np.isnan(bk).sum()))
