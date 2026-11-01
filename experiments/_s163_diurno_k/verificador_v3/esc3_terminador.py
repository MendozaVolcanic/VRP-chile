# Verificador v3: pasadas de la referencia cuya marca dia/noche cambia si el instante se redondea al minuto o se mueve +-3 min
# (el record trae HH:MM del gránulo; la pasada de MIROVA trae segundos).
import os, sys, datetime as D
os.environ["VRP_PROFILE"]="mirova_equivalent"
R, SP = sys.argv[1], sys.argv[2]
sys.path[:0]=[R, R+"/scripts", R+"/experiments/_s163_diurno_k"]
import evaluar_diurno_k as ev, sustrato_k as sk
from pathlib import Path
filas=sk.cargar_ref(Path(SP)/"ref047")
vent=[(w[0],w[1],w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas=[p for p in ev.pasadas_de(filas,"union",vent) if p.sensor_bucket in ev.SENSORES_DIA]
for dm in (0,1,3,5):
    n=0
    for p in pas:
        a=ev.es_dia_vol(p.volcano,p.instante)
        t=p.instante.replace(second=0,microsecond=0)
        b=ev.es_dia_vol(p.volcano,t-D.timedelta(minutes=dm)) != a or ev.es_dia_vol(p.volcano,t+D.timedelta(minutes=dm)) != a
        n+=b
    print("desplazamiento +-%d min (y segundos a 0): %d de %d pasadas VIIRS cambian de marca" % (dm,n,len(pas)))
