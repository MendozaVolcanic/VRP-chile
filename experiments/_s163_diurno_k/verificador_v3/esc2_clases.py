# Verificador v3: que pasadas diurnas VIIRS pasan de "otra" a "negativo" con la variante d (otra como negativo).
import os, sys, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
R, SP = sys.argv[1], sys.argv[2]
sys.path[:0]=[R, R+"/scripts", R+"/experiments/_s163_diurno_k"]
import evaluar_diurno_k as ev, sustrato_k as sk, evaluador_comun as ec
from pathlib import Path
filas=sk.cargar_ref(Path(SP)/"ref047")
vent=[(w[0],w[1],w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas=ev.pasadas_de(filas,"union",vent)
res={}
for flag in (False, True):
    T=ec.tabla_por_pasada(pas,{"c":[]},"c")
    for f in T: f["es_dia"]=ev.es_dia_vol(f["pasada"].volcano,f["pasada"].instante)
    ev.banderas_por_periodo(T, flag)
    c=collections.Counter()
    for f in T:
        if f["es_dia"] and f["pasada"].sensor_bucket in ev.SENSORES_DIA:
            p=f["pasada"]
            cl = "protegida" if f["protegida"] else ec.clase_p2(f)
            c[(p.sensor_bucket, cl, p.estado, p.fuente if cl=="otra" else "-")]+=1
    res[flag]=c
for k in sorted(set(res[False])|set(res[True])):
    print(k, "principal", res[False][k], "variante d", res[True][k])
