# -*- coding: utf-8 -*-
import json, collections, sys
recs=json.load(open(sys.argv[1],encoding="utf-8"))
def _tasa(a,n): return round(a/n,4) if n else None
print("== A. El piso de VIIRS750 con el redondeo que usa el evaluador ==")
print("   evaluar._tasa(12,18) =", _tasa(12,18), " piso parametros =", 0.667)
print("   cumple (rb >= piso)?", _tasa(12,18) >= 0.667, "   <-- el prereg dice que 12 de 18 DEBE pasar")
print("   sin redondeo: 12/18 =", 12/18, ">= 0.667 ?", (12/18)>=0.667)
for num,den,piso in ((118,143,0.825),(123,143,0.86),(13,18,0.722),(12,18,0.667),(117,143,0.825)):
    print("   %3d/%3d -> _tasa=%s  piso=%s  cumple=%s"%(num,den,_tasa(num,den),piso,_tasa(num,den)>=piso))
print()
print("== B. C2: las dos listas de noches esperadas son consistentes? ==")
par=json.load(open(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s146_ab_sin_test1/parametros.json",encoding="utf-8"))
vol_list=set(par["perdidas_esperadas_noche_volcan"]); sen_list=par["perdidas_esperadas_noche_sensor"]
for s in sen_list:
    v,b,d=s.split("|")
    k=f"{v}|{d}"
    print("   sensor-noche %-42s -> noche de volcan %-28s %s"%(s,k,"EN la lista de volcan" if k in vol_list else "*** NO esta en la lista de volcan ***"))
print()
print("== C. En esas dos noches, publica ALGUN otro sensor? (si no, perder la del sensor")
print("      arrastra la noche del volcan y C2 falla por una perdida que el propio prereg predice) ==")
for v,d in (("Isluga","2026-09-05"),("PuyehueCordonCaulle","2026-09-07")):
    sel=[r for r in recs if r["vol"]==v and r["noche"]==d]
    print("   %s %s:"%(v,d))
    for r in sorted(sel,key=lambda x:(x["b"],x["dt"])):
        print("      %-9s %s pub=%d lab=%-10s disp=%s t1=%s"%(r["b"],r["dt"],r["pub"],r["lab"],r["disp"],r["t1"]))
    otros=[r for r in sel if r["pub"] and r["b"]!="VIIRS750"]
    print("      -> publican otros sensores esa noche: %d"%len(otros))
