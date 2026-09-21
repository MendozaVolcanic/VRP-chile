# -*- coding: utf-8 -*-
import json, sys
recs=json.load(open(sys.argv[1],encoding="utf-8"))
print("== Las 18 pasadas POSITIVAS de VIIRS750 en la ventana, con lo que hace el control ==")
pos=[r for r in recs if r["b"]=="VIIRS750" and r["lab"]=="pos"]
for r in sorted(pos,key=lambda x:x["dt"]):
    print("  %-22s %s pub=%d t1=%-5s disp=%-8s vrp_mirova=%s"%(r["vol"],r["dt"],r["pub"],r["t1"],r["disp"],r.get("vrp_ref")))
print("  publicadas por el control: %d de %d"%(sum(r["pub"] for r in pos),len(pos)))
print("  de las publicadas, cuantas con t1=True: %d"%sum(1 for r in pos if r["pub"] and r["t1"]))
print("  la 'perdida segura de PCC 07-sep' esta entre las publicadas?",
      [ (r["vol"],r["dt"],r["pub"]) for r in pos if r["vol"]=="PuyehueCordonCaulle" and r["dt"][:10]=="2026-09-07"])
print()
print("== Las positivas de VIIRS375 que el control NO publica (denominador del piso 0,825) ==")
p3=[r for r in recs if r["b"]=="VIIRS375" and r["lab"]=="pos"]
print("  publicadas %d de %d ; con t1=True entre las publicadas: %d"%(
    sum(r["pub"] for r in p3),len(p3),sum(1 for r in p3 if r["pub"] and r["t1"])))
print("  positivas V375 SIN t1 (inmunes al brazo B por construccion): %d"%sum(1 for r in p3 if r["pub"] and not r["t1"]))
print()
print("== MODIS: la unica positiva ==")
for r in [r for r in recs if r["b"]=="MODIS" and r["lab"]=="pos"]:
    print("  ",r["vol"],r["dt"],"pub",r["pub"],"t1",r["t1"],"disp",r["disp"],"mirova",r.get("vrp_ref"))
