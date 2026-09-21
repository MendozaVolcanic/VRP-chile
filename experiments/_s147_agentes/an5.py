# -*- coding: utf-8 -*-
import json, sys, math, collections
recs=json.load(open(sys.argv[1],encoding="utf-8"))
def _tasa(a,n): return round(a/n,4) if n else None
print("== Brazo C: cuantas pasadas TIENE que apagar para pasar C3 (techo 0,82 / 0,21) ==")
for b,techo,pred in (("VIIRS375",0.82,21),("VIIRS750",0.21,3)):
    neg=[r for r in recs if r["b"]==b and r["lab"]=="neg_limpio"]
    n=len(neg); pub=sum(r["pub"] for r in neg)
    # el evaluador redondea a 4 decimales antes de comparar
    k=0
    while k<=pub and _tasa(pub-k,n)>techo: k+=1
    print("  %-9s control %d/%d=%s techo %.2f -> hay que apagar AL MENOS %d de las %d publicadas"
          " (la Fase 1 predice %d) -> margen %d"%(b,pub,n,_tasa(pub,n),techo,k,pub,pred,pred-k))
print()
print("== Brazo B: idem con techo 0,45 / 0,12 ==")
for b,techo,lo,hi in (("VIIRS375",0.45,0.214,0.365),("VIIRS750",0.12,0.053,0.071)):
    neg=[r for r in recs if r["b"]==b and r["lab"]=="neg_limpio"]
    n=len(neg); pub=sum(r["pub"] for r in neg)
    k=0
    while k<=pub and _tasa(pub-k,n)>techo: k+=1
    print("  %-9s control %d/%d=%s -> apagar al menos %d; la banda de la Fase 1 (%.3f a %.3f) implica apagar de %d a %d"
          %(b,pub,n,_tasa(pub,n),k,lo,hi,pub-round(hi*n),pub-round(lo*n)))
print()
print("== El canal de GANANCIA que el pre-registro no mide: pasadas con t1=True y pub=0 ==")
print("   (el Test 1 gana la fuente, su recomputo da 0 y TAPA la publicacion: apagarlo puede AGREGAR)")
for b in ("VIIRS375","VIIRS750","MODIS"):
    sel=[r for r in recs if r["b"]==b]
    t1p0=[r for r in sel if r["t1"] and not r["pub"]]
    print("   %-9s t1=True y pub=0: %3d de %3d pasadas (%s)"%(b,len(t1p0),len(sel),
          collections.Counter(r["lab"] for r in t1p0)))
print()
print("== Posicion del cumulo: se calcula y NO entra en ningun criterio ==")
print("   evaluar.py calcula n_movidos_mas_de_500_m y mediana/p90; los criterios C0..C6 no lo usan.")
print("== nulo_barajado: se calcula 'fuera_del_nulo' y tampoco entra en el veredicto.")
print()
print("== Estrato sin_info: ni premia ni castiga ==")
c=collections.Counter(r["lab"] for r in recs)
print("  ",dict(c), " -> sin_info es el %.1f%% del corpus y publicamos en %d de ellas"
      %(100*c["sin_info"]/len(recs), sum(r["pub"] for r in recs if r["lab"]=="sin_info")))
