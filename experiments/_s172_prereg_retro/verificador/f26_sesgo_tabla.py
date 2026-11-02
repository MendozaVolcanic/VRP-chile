# -*- coding: utf-8 -*-
"""VPR172 V-4/V-3: (1) primera fecha con NOAA-21 etiquetado; (2) en F26 VIIRS, ¿la tabla expone las pasadas de forma selectiva por cenit?
(3) lista de pasadas F26 positivas con K publica. P1: control positivo = V2c MODIS reproduce 5110 neg_limpio (ya en k_en_tramos).
P2: imprime n por celda; celdas vacias = SIN DATO."""
import sys, os, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts"); os.chdir(EXP)
import numpy as np, csv
import banco_paridad as bp
from clase_mirova import alerta_protegida
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas_all = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR); cons=[f for f in filas_all if f["source"]=="CONS"]
V=("2026-02-01","2026-06-30")
recs = bp.cargar_nuestros(coords, inner, V)
por_vb, ns, nv, n = bp.indexar_referencia(cons, coords, V, regla_minimas="SN")
bp.etiquetar(recs, por_vb, ns, nv)
for r in recs:
    filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]); al=[f for f in filas if bp.es_alerta(f["tipo"])]
    r["prot"]=bool(al) and any(alerta_protegida(f) for f in al)
n21=[r for r in recs if r["sensor"].startswith("VIIRS_NOAA21") and r["lab"]!="sin_info"]
print("primer NOAA21 etiquetado (tabla):", min(r["noche"] for r in n21) if n21 else None, "n", len(n21))
by=collections.defaultdict(lambda:[0,0])
for r in recs:
    if r["sensor"].startswith("VIIRS_NOAA21"):
        m=r["noche"][:7]; by[m][0]+=1; by[m][1]+= (r["lab"]!="sin_info")
print("NOAA21 etiquetadas por mes (n etiquetadas / n records):", {k:tuple(v) for k,v in sorted(by.items())})
# SNPP etiquetadas por mes
by=collections.defaultdict(lambda:[0,0])
for r in recs:
    if r["sensor"].startswith("VIIRS_SNPP"):
        m=r["noche"][:7]; by[m][0]+=1; by[m][1]+= (r["lab"]!="sin_info")
print("SNPP etiquetadas por mes:", {k:tuple(v) for k,v in sorted(by.items())})
# sesgo de cenit: F26 VIIRS375 NOAA20/SNPP: cenit de etiquetadas vs sin_info
for b in ("VIIRS375","VIIRS750"):
    for sat in ("NOAA20","SNPP"):
        s=[r for r in recs if r["b"]==b and sat in r["sensor"] and "2026-02-01"<=r["noche"]<="2026-03-31" and r["z"] is not None]
        e=[r["z"] for r in s if r["lab"]!="sin_info"]; u=[r["z"] for r in s if r["lab"]=="sin_info"]
        print(b,sat,"F26 etiquetadas n",len(e),"cenit med",round(float(np.median(e)),1) if e else None,"| sin_info n",len(u),"cenit med",round(float(np.median(u)),1) if u else None)
# F26: pasadas por noche-volcan-sensor etiquetadas
for b in ("VIIRS375","VIIRS750"):
    s=[r for r in recs if r["b"]==b and "2026-02-01"<=r["noche"]<="2026-03-31"]
    g=collections.defaultdict(lambda:[0,0])
    for r in s: g[(r["vol"],r["noche"])][0]+=1; g[(r["vol"],r["noche"])][1]+=(r["lab"]!="sin_info")
    noches_con2=sum(1 for v in g.values() if v[1]>=2)
    print(b,"noche-volcan con >=2 pasadas etiquetadas (necesarias para la razon doble de cenit):",noches_con2,"de",len(g))
# F26 pos list MODIS
rows=[]
for r in recs:
    if "2026-02-01"<=r["noche"]<="2026-03-31" and r["lab"]=="pos":
        rows.append([r["vol"],r["b"],r["sensor"],r["dt"].strftime("%Y-%m-%d %H:%M"),"protegida" if r["prot"] else "bajo1", int(bool(r["pub"])), r["z"]])
with open(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\f26_pos_pasadas.csv","w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh); w.writerow(["vol","bucket","sensor","dt","clase","K_publica","cenit"]); w.writerows(rows)
print("F26 pos MODIS:", [(x[3],x[0],x[4],x[5]) for x in rows if x[1]=="MODIS"])
