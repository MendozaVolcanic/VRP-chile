import csv
R="D:/vrp-trabajo/temporales/s169_ver_lector/"
L="experiments/_s168/v375e_sombra/leer_sombra_v375e.py"
filas=[
("VL169-01","Una sola vez es por nombre de corte y carpeta, no por ventana",L+" main (n_pre/ya, base)","CONFIRMADO",3,"B1","python -I probe_b1.py ; python -I probe_b1b.py",R+"salidas/probe_b1b_salida.txt"),
("VL169-02","El nulo cuenta una caida en seccion como ATRAPADA","experiments/_s168/v375e_sombra/mutar_sombra.py correr ; probar_sombra.py seccion l.77","CONFIRMADO",2,"B5","python -I crash_vs_asercion.py",R+"salidas/crash_vs_asercion_salida.txt"),
("VL169-03","S8 compara todo pipeline/ y marca por cambios que VIIRS 375 no lee (roi_v750)",L+" diff_git/control_s8 ; pipeline/mirova_v750_codigo.py caja_v375","CONFIRMADO",2,"B7","python -I cierre_imports.py ; git log origin/main --since=2026-10-01 -- pipeline/ | wc -l",R+"salidas/cierre_imports_salida.txt"),
("VL169-04","S8 no compara volcanoes.yaml, scripts/run_pipeline.py ni el workflow de la sombra","pipeline/mirova_v750_codigo.py _volcanes_yaml ; scripts/run_pipeline.py l.92","CONFIRMADO (lectura) / SOSPECHA (efecto)",2,"B2","git diff --name-only c42ee0eb7 <sha> -- volcanoes.yaml scripts/run_pipeline.py",R+"salidas/cierre_imports_salida.txt"),
("VL169-05","S8 y la bateria dependen de objetos git (c42ee0eb7 no es ancestro del lector); sha de auto_audit_weekly distinto de main",L+" diff_git/BASE_REGIMEN ; probar_sombra.py l.403-405","CONFIRMADO",2,"B2/B4","python -I probar_sombra.py en arbol sin .git ; python -I git_check.py",R+"salidas/bateria_190.txt"),
("VL169-06","La poblacion depende de VRP_PROFILE y de modulos sin sha (store, profile, f5_core)","scripts/banco_paridad.py l.60 ; scripts/auto_audit_weekly.py l.295-300 ; pipeline/store.py l.203","CONFIRMADO (mecanismo) / SOSPECHA (efecto)",2,"B1","VRP_PROFILE=_s151_ab_diurno_on python -I env_check.py",R+"salidas/env_check_salida.txt"),
("VL169-07","S9 usa la fila mas nueva de la tabla de cualquier sensor y volcan",L+" main ultima_tabla","CONFIRMADO (codigo) / SOSPECHA (ocurrencia)",2,"B2","python -I probe_b1b.py (T_s9a)",R+"salidas/probe_b1b_salida.txt"),
("VL169-08","Antes de la parada con un control caido sale 3 y sin contadores",L+" analizar (if fallas) ; main cod","CONFIRMADO",1,"B1","python -I probe_b1b.py (T_i)",R+"salidas/probe_b1b_salida.txt"),
("VL169-09","La comprobacion en rojo es por grupos y atribuye por prefijo del nombre","experiments/_s169/v375e_lector_arreglos/ver_en_rojo.py GRUPOS/ESPERA ; rojo_D.txt","CONFIRMADO",1,"B4","leer rojo_A..E.txt",R+"salidas/bateria_190.txt"),
("VL169-10","V04 equivalente declarada en el texto antes de correr pero sin marca en mutar_sombra.py","experiments/_s168/v375e_sombra/mutar_sombra.py V04 ; PREREGISTRO_E.md 11.10","CONFIRMADO",1,"B5","python -I nulo_estatico.py",R+"salidas/nulo_estatico_salida.txt"),
]
with open(R+"hallazgos.csv","w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh); w.writerow("id,titulo,archivo_linea,confianza,gravedad,eje,comando_reproduccion,salida_cruda".split(",")); w.writerows(filas)
print(len(filas))
