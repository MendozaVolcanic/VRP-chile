import pickle,sys,io,collections
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,'..'); sys.path.insert(0,'../../..'); sys.path.insert(0,'../../../scripts')
import evaluar as EV, brazos as BR
filas,N_neg,tk,meta=pickle.load(open('verificador_filas.pkl','rb'))
R="cercano"
for vol in ("Tupungatito","PuyehueCordonCaulle"):
    T=[x for x in filas if x['tramo']=='T' and x['vol']==vol]
    O=[x for x in filas if x['tramo']!='T' and x['vol']==vol]
    print(vol,'T n',len(T),collections.Counter(x['c'] for x in T),'| O n',len(O),collections.Counter(x['c'] for x in O))
    for b in BR.BRAZOS:
        a=(b,R)
        eT=sum(x['w'] for x in T if EV.err(x,a)); pr=sum(1 for x in T if x['c']=='pos_prot' and not x['X'][a])
        eO=sum(x['w'] for x in O if EV.err(x,a))
        print(f"   {b:8s} errores T {eT:7.2f} (prot perdidas en T {pr}) errores O {eO:7.2f}")
# recall de arms por volcan en pos_bajo
