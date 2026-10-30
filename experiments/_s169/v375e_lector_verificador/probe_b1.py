# B1: caminos para ver una lectura antes de la parada o elegir otro corte.
# P1 (si estuviera roto, ¿se vería?): T_a/T_b/T_f miran codigos de salida y archivos reales de main(); control positivo: T_b (parada de prueba) SI escribe lectura.
# P2 (instrumento muerto): si main() no corriera, T_b no daría rc 0 ni archivo; un 'no hay lectura' en T_a no se confunde con 'no corrió' porque T_a muestra rc 5 y los contadores.
import sys, json, csv, tempfile, io, contextlib, shutil, os
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol/experiments/_s168/v375e_sombra")
sys.path.insert(0,str(A))
import probar_sombra as P
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
LS=P.cargar(A)
import banco_paridad as B
deps,malos=LS.cargar_deps(); assert deps, malos
E=deps["E"]; inner=B.inner_desde_html()
def publicar(casos): return [(x[3],x[4]) for x in B.correr_node([[E.slim(r),inn] for r,inn in casos])]
pm,vm,km=P.escena(LS,publicar,inner,neg_aparte=12)
T=Path("D:/vrp-trabajo/temporales/s169_ver_lector/tmp_b1"); 
if T.exists(): shutil.rmtree(T)
T.mkdir()
(T/"k").mkdir(); (T/"s").mkdir()
for vol in B.VOLS:
    ks=ss=[]
    if vol=="Lascar":
        ks=[km[k] for k in sorted(km)]; ss=[vm[k] for k in sorted(vm)]
    (T/"k"/f"{vol}.json").write_text(json.dumps({"records":ks}),encoding="utf-8")
    (T/"s"/f"{vol}.json").write_text(json.dumps({"records":ss}),encoding="utf-8")
cab=["timestamp","Fecha_Satelite_UTC","Fecha_Captura_Chile","Volcan","Sensor","VRP_MW","Distancia_km","Tipo_Registro","Clasificacion Mirova","Ruta Foto","Fecha_Proceso_GitHub","Ultima_Actualizacion","Editado"]
def escribir_cons(ruta, rutina_bajo_hasta=None):
    with open(ruta,"w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh); w.writerow(cab)
        for o in pm:
            tipo={"pos_prot":"ALERTA_TERMICA","pos_bajo":"ALERTA_TERMICA","far_tabla":"FALSO_POSITIVO"}.get(o["clase"],"RUTINA")
            vrp=o["mirova_vrp"] if o["clase"].startswith("pos") else (0.4 if o["clase"]=="far_tabla" else 0.0)
            dist=1.0 if o["clase"].startswith("pos") else (15.0 if o["clase"]=="far_tabla" else 0.0)
            if rutina_bajo_hasta and o["clase"]=="pos_bajo" and o["hora_utc"][:10]<=rutina_bajo_hasta:
                tipo,vrp,dist="RUTINA",0.0,0.0
            w.writerow([0,o["hora_utc"]+":10","","Lascar","VIIRS375",vrp,dist,tipo,"Bajo","","","","NO"])
        w.writerow([0,"2026-12-08 05:00:10","","Lascar","VIIRS375",0.0,0.0,"RUTINA","Bajo","","","","NO"])
escribir_cons(T/"cons.csv"); escribir_cons(T/"cons2.csv","2026-11-10")
with open(T/"ocr.csv","w",newline="",encoding="utf-8") as fh: csv.writer(fh).writerow(cab+["Nota_Validacion"])
def correr(cons,dsal,*extra,hasta="2026-11-30"):
    args=["--data-k",str(T/"k"),"--data-sombra",str(T/"s"),"--cons",str(T/cons),"--ocr",str(T/"ocr.csv"),"--hasta",hasta,"--commit",P.COMMIT,"--dir-salida",str(T/dsal)]
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        cod=LS.main(args+list(extra))
    return cod,sorted(x.name for x in (T/dsal).glob("*")) if (T/dsal).exists() else []
R={}
# T_a: umbrales de verdad, 25 noches -> provisional
R["T_a provisional (30/40 reales)"]=correr("cons.csv","a")
# T_b / T_c / T_d con parada de prueba (12 noches, 20 alertas)
with P.parada_de_prueba(LS,12,20):
    R["T_b lectura que decide (dir X)"]=correr("cons.csv","X")
    R["T_c MISMOS insumos, OTRO dir-salida Y"]=correr("cons.csv","Y")
    R["T_c2 mismos insumos, mismo dir X"]=correr("cons.csv","X")
    R["T_d referencia distinta (menos alertas) en dir X"]=correr("cons2.csv","X")
    R["T_e --desde 2026-11-10 (nombre del archivo)"]=correr("cons.csv","E","--desde","2026-11-10")
    R["T_h --hasta 2026-11-14 (antes de N)"]=correr("cons.csv","H",hasta="2026-11-14")
for k,v in R.items(): print(k,"->",v)
(T/"resumen.json").write_text(json.dumps(R,ensure_ascii=False,indent=1),encoding="utf-8")
