import sys,io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,'..'); sys.path.insert(0,'../../..'); sys.path.insert(0,'../../../scripts')
import evaluar as EV
# (1) disparador V375-D (b): codigo compara el limite superior del puerto con el PUNTO de K
pk=0.957; ne=198
lo_k,hi_k=EV.wilson(pk*ne,ne); pp=0.905; lo_p,hi_p=EV.wilson(pp*ne,ne)
print(f"K {pk} IC [{lo_k:.3f};{hi_k:.3f}]  puerto {pp} IC [{lo_p:.3f};{hi_p:.3f}]")
print("codigo (hi_puerto < punto K):", hi_p<pk, "| texto (IC puerto entero bajo IC K, hi_p < lo_k):", hi_p<lo_k)
# (2) VALIDA EN O: compuesto peor que M14 en 4 bloques
R=("M14","cercano"); P=("POR_VOLCAN","cercano")
def fila(d,peor):
    return {"c":"pos_bajo","w":4.7,"bloque":f"V|{d}","K":True,"X":{R:True,P:not peor},"V":{R:.5,P:.5},"vol":"V","tramo":"O1","prot":False}
for nb in (0,2,4,5):
    fs=[fila(d,d<nb) for d in range(10)]
    p=EV.p2(fs,P,R)
    print(f"compuesto pierde {nb} alertas bajo 1 MW vs M14 -> P2 {p['veredicto']} neto {p['neto']:+.1f} -> VvALIDA EN O = {p['veredicto'] not in ('PIERDE','BLOQUEA')}")
