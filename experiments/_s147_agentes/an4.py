# -*- coding: utf-8 -*-
import json, sys, collections
recs=json.load(open(sys.argv[1],encoding="utf-8"))
pos=[r for r in recs if r["lab"]=="pos"]
print("== La red de seguridad de 0,5 MW: cuantas positivas podria perder el brazo sin tocarla ==")
for b in ("VIIRS375","VIIRS750","MODIS"):
    sub=[r for r in pos if r["b"]==b and r["pub"]]
    nones=[r for r in sub if r.get("vrp_ref") is None]
    ge=[r for r in sub if (r.get("vrp_ref") or 0)>=0.5]
    lt=[r for r in sub if r.get("vrp_ref") is not None and r["vrp_ref"]<0.5]
    print("  %-9s publicadas=%3d | vrp_ref None=%d | >=0,5 MW=%3d | <0,5 MW=%3d"%(b,len(sub),len(nones),len(ge),len(lt)))
print()
print("  -> en VIIRS375 el piso 0,825 tolera perder 25 de 143. De esas 143,")
sub=[r for r in pos if r["b"]=="VIIRS375" and r["pub"]]
vals=sorted((r.get("vrp_ref") or 0) for r in sub)
print("     mediana del VRP de MIROVA = %.3f MW ; cuantas bajo 0,5 = %d de %d"%(vals[len(vals)//2],sum(1 for v in vals if v<0.5),len(vals)))
print("     o sea: se pueden perder hasta 25 pasadas con alerta de MIROVA y ADOPTAR igual,")
print("     siempre que ninguna llegue a 0,5 MW.")
print()
print("== Cuantas pasadas perdidas 'grandes' harian falta para que C1 falle por la via del 0,5 ==")
print("   basta UNA. Pasadas positivas publicadas con >=0,5 MW por sensor:",
      {b:sum(1 for r in pos if r["b"]==b and r["pub"] and (r.get("vrp_ref") or 0)>=0.5) for b in ("VIIRS375","VIIRS750","MODIS")})
print()
print("== C4: el estrato se compara sobre conjuntos DISTINTOS (no pareados) ==")
g=collections.defaultdict(list)
for r in recs:
    if r["lab"]=="pos" and r["pub"] and r.get("vrp_ref"): g[(r["vol"],r["b"])].append(r)
import statistics
for k,v in sorted(g.items(),key=lambda kv:-len(kv[1]))[:6]:
    raz=sorted(x["disp"]/x["vrp_ref"] for x in v)
    # simula que el brazo pierde las 20% de menor magnitud publicada: la mediana se mueve sola
    keep=sorted(v,key=lambda x:x["disp"])[int(0.2*len(v)):]
    raz2=sorted(x["disp"]/x["vrp_ref"] for x in keep)
    print("   %-28s n=%2d mediana=%.3f -> si el brazo pierde el 20%% mas debil: n=%2d mediana=%.3f (delta |r-1| = %+.3f)"%(
        "|".join(k),len(raz),statistics.median(raz),len(raz2),statistics.median(raz2),
        abs(statistics.median(raz2)-1)-abs(statistics.median(raz)-1)))
