# X6: tasa de falsos GANA/PIERDE de P2 (prueba de signos con pesos reales) cuando los dos brazos son intercambiables.
import pickle,sys,io,collections,copy
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,'..'); sys.path.insert(0,'../../..'); sys.path.insert(0,'../../../scripts')
import evaluar as EV
filas,N_neg,tk,meta=pickle.load(open('verificador_filas.pkl','rb'))
R=("M14","cercano"); A=("SIM","cercano")
rng=np.random.default_rng(11)
# SIM: permuta, dentro de (clase, volcan), la publicacion de M14 entre pasadas => mismos totales, discordancia simetrica
grupos=collections.defaultdict(list)
for i,x in enumerate(filas): grupos[(x['c'],x['vol'])].append(i)
cnt=collections.Counter(); Bs=[]
for rep in range(400):
    pub=[x['X'][R] for x in filas]
    new=list(pub)
    for g in grupos.values():
        idx=np.array(g); perm=rng.permutation(len(g))
        for a,b in zip(idx,idx[perm]): new[a]=pub[b]
    fs=[{**x,'X':{**x['X'],A:new[i]}} for i,x in enumerate(filas)]
    p=EV.p2(fs,A,R); cnt[p['veredicto']]+=1; Bs.append(p['B'])
print('H0 intercambiable, 400 reps, B mediano',int(np.median(Bs)),dict(cnt))
