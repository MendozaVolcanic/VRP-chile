# B1 (2a parte). T_d: ¿una referencia distinta mueve N y deja una segunda lectura en el MISMO dir? T_i: pocas noches, ¿rc 3 sin contadores? T_s9: ¿una fila de MODIS fresca basta para S9?
# P1: si N no se moviera con otra referencia, T_d lo mostraria (mismo nombre y rc 2). P2: control: cons base debe dar corte 2026-11-11.
import sys, json, csv, io, contextlib, shutil
from pathlib import Path
sys.dont_write_bytecode=True
exec(open("D:/vrp-trabajo/temporales/s169_ver_lector/probe_b1.py",encoding="utf-8").read().split("R={}")[0])
def escribir_cons2(ruta, tardia_sensor="VIIRS375"):
    with open(ruta,"w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh); w.writerow(cab)
        for o in pm:
            tipo={"pos_prot":"ALERTA_TERMICA","pos_bajo":"ALERTA_TERMICA","far_tabla":"FALSO_POSITIVO"}.get(o["clase"],"RUTINA")
            vrp=o["mirova_vrp"] if o["clase"].startswith("pos") else (0.4 if o["clase"]=="far_tabla" else 0.0)
            dist=1.0 if o["clase"].startswith("pos") else (15.0 if o["clase"]=="far_tabla" else 0.0)
            w.writerow([0,o["hora_utc"]+":10","","Lascar","VIIRS375",vrp,dist,tipo,"Bajo","","","","NO"])
        if tardia_sensor: w.writerow([0,"2026-12-08 05:00:10","","Lascar",tardia_sensor,0.0,0.0,"RUTINA","Bajo","","","","NO"])
escribir_cons2(T/"cons_modis.csv","MODIS"); escribir_cons2(T/"cons_sin_tardia.csv",None)
R={}
with P.parada_de_prueba(LS,8,12):
    R["T_d0 base (8 noches,12 alertas) dir X2"]=correr("cons.csv","X2")
    R["T_d1 otra referencia (7 pos_bajo -> RUTINA), MISMO dir X2"]=correr("cons2.csv","X2")
with P.parada_de_prueba(LS,12,20):
    R["T_s9a fila tardia solo de MODIS (VIIRS375 sin fila posterior al corte)"]=correr("cons_modis.csv","S9a")
    R["T_s9b sin fila tardia (control: S9 debe caer)"]=correr("cons_sin_tardia.csv","S9b")
for k,v in R.items(): print(k,"->",v)
for d in ("S9a","S9b"):
    for f in sorted((T/d).glob("*.txt")):
        t=f.read_text(encoding="utf-8"); print(d,f.name, [l for l in t.splitlines() if l.strip().startswith("S9")])
# T_i: 2 noches, umbrales reales
for sub in ("k","s"):
    for vol in B.VOLS:
        p=T/sub/f"{vol}.json"; d=json.loads(p.read_text(encoding="utf-8"))
        d["records"]=[r for r in d["records"] if r["datetime_utc"][:10] in ("2026-11-04","2026-11-05")]
        p.write_text(json.dumps(d),encoding="utf-8")
buf=io.StringIO()
cod,arch=correr("cons.csv","I",hasta="2026-11-06")
print("T_i 2 noches, umbrales reales ->",cod,arch)
print([l for l in (T/"I"/[a for a in arch if a.endswith(".txt")][0]).read_text(encoding="utf-8").splitlines() if "parada" in l or "CAE" in l or "NO LEGIBLE" in l])
