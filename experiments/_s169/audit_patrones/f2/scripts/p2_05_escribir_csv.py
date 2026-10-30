import csv
B = "D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/"
PY = "C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I "
S = B + "scripts/"
filas = [
("P2-01","Breaker de descarga pegado: bajar_por_nombre gasta 400 s por granulo","probe_f4.py:413-442,549-550; pipeline/fetch.py:950,1076","CONFIRMADO mecanismo; SOSPECHA frecuencia",4,"P-E/P-F",PY+S+"p2_01_breaker_pegado.py",S+"p2_01_breaker_pegado_salida.txt"),
("P2-02","Evaluador no ata poblacion, identidad ni externos; resultado sin procedencia","evaluar_f4.py:765-772,784","CONFIRMADO",3,"P-B/P-C",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-03","Manifiesto y procedencia no atan la lectura al commit del tag","manifiesto_candado_f4.py:36,89-98; externos_f4.py:112-118","CONFIRMADO",3,"P-C",PY+S+"p2_02_poblacion_manifiesto.py",S+"p2_02_poblacion_manifiesto_salida.txt"),
("P2-04","Identidad compara clase recalculada en local; 8 indicadores no deciden","identidad_f4.py:178-210,251-253; evaluar_f4.py:455","CONFIRMADO",3,"P-D",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-05","Ensayo en seco con JSON compacto no puede ver el P-A de CRLF","ensayo_en_seco_f4.py:130,135; reetiquetado_f4.py:171","CONFIRMADO",3,"P-A/P-D",PY+S+"p2_02_poblacion_manifiesto.py",S+"p2_02_poblacion_manifiesto_salida.txt"),
("P2-06","pub_runner de V, V-cercano y V-pico nunca se compara","evaluar_f4.py:635","CONFIRMADO",2,"P-D",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-07","Manifiesto omite run_pipeline.py, fetch.py, volcanic_features.yaml, externos_referencia.json","manifiesto_candado_f4.py:37-45","CONFIRMADO",2,"P-C",PY+S+"p2_02_poblacion_manifiesto.py",S+"p2_02_poblacion_manifiesto_salida.txt"),
("P2-08","Dependencias sin fijar y versiones de cabecera no comparadas entre tandas","probe-s168-modd-f4.yml:122,189-190; probe_f4.py:496; externos_f4.py:57-79","CONFIRMADO lectura; SOSPECHA impacto",2,"P-C/P-E","lectura de codigo",""),
("P2-09","VRP_PROFILE y F4_RAIZ cambian la lectura sin rastro","identidad_f4.py; run_pipeline.py:152-176; evaluar_f4.py:48; probe_f4.py:80,84","SOSPECHA",2,"P-E",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-10","Sin record guardado en data/ se lee como K no difiere","probe_f4.py registro_guardado/difiere; probe_mxd03_ab.py:113-121; probe_etiquetas.py:187-203","CONFIRMADO mecanismo; SOSPECHA impacto",2,"P-F","lectura de codigo",""),
("P2-11","MxD03 ilegible se lee como volcan fuera del granulo (motivo sellado)","mirova_v750_codigo.py:788-808,842-861; probe_f4.py motivo_y_marca","SOSPECHA",2,"P-F","lectura de codigo",""),
("P2-12","P2 con 21+ bloques depende del flujo de numpy; resultado sin version","evaluar_d25.py:542-546; evaluar_f4.py:564","SOSPECHA",2,"P-E",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-13","Fila del runner fuera de la poblacion hace caer evaluar() con KeyError","evaluar_f4.py:766-769","CONFIRMADO",1,"P-F",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-14","por_tramo informa P2 y no P2'","evaluar_f4.py:716","CONFIRMADO",1,"P-G",PY+S+"p2_03_evaluador_demos.py",S+"p2_03_evaluador_demos_salida.txt"),
("P2-15","Medidor sale con 0 con vivas; salida commiteada 82/3 vs codigo 86/4","mutar_evaluar_f4.py resumir; mutar_evaluar_f4_salida.txt","CONFIRMADO",1,"P-D",PY+S+"p2_04_medidor_mutaciones.py",S+"p2_04_medidor_mutaciones_salida.txt"),
("P2-16","head_e corre en todos los modos; concurrency desplaza tandas; glob incluye humo","probe-s168-modd-f4.yml:32-34,66-71; evaluar_f4.py cargar; identidad_f4.py leer_runner","CONFIRMADO lectura; SOSPECHA ocurrencia",1,"P-F/P-B","lectura de codigo",""),
]
with open(B+"hallazgos.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","titulo","archivo_linea","confianza","gravedad","eje","comando_reproduccion","salida_cruda"])
    w.writerows(filas)
print(len(filas))
