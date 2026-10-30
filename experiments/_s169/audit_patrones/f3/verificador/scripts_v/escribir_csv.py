import csv, sys
B = "D:/vrp-trabajo/temporales/s169_audit_patrones/f3_verificador/"
PY = "python -I -B "
filas = [
 ("P3-01","Evaluador da COBERTURA OK con 0 pasadas de MIROVA (ref vieja, vacia o sensor que no calza); BOM refutado con encabezado real","scripts/evaluador_comun.py:169,856-857,898","CONFIRMADO EN PARTE",4,"P-F",PY+"scripts_v/p01_ref_vieja_vacia_bom.py <arbol> <carpeta>",B+"p01_salida.txt"),
 ("P3-02","revisar_sombra no ve corrida vacia desde el 2.o dia ni Cobertura INCOMPLETA","scripts/revisar_sombra.py:27,40; sombra-codigo-mirova.yml:147-151","CONFIRMADO",3,"P-F",PY+"scripts_v/p02_p03_revisar.py <arbol>",B+"p02_p03_salida.txt"),
 ("P3-03","revisar_sombra no exige records por sensor","scripts/revisar_sombra.py:28,40; scripts/run_pipeline.py:248-250","CONFIRMADO",3,"P-F",PY+"scripts_v/p02_p03_revisar.py <arbol>",B+"p02_p03_salida.txt"),
 ("P3-04","return None de la via silencioso; sin --cobertura-json ni artefacto (la cobertura si queda en log/summary/warnings)","pipeline/process_viirs.py:773,781; process_viirs_mod.py:509,517; process_modis.py:657; pipeline/mirova_v750_codigo.py:756-757,798-808; sombra-codigo-mirova.yml:122-123","CONFIRMADO EN PARTE",2,"P-F","lectura de codigo",B+"INFORME_VERIFICADOR_F3.md"),
 ("P3-05","Linea de log VIIRS 375 identica con y sin deteccion en la via","scripts/run_pipeline.py:321-327","CONFIRMADO",1,"P-F",PY+"-X utf8 scripts_v/p05_linea_log.py <arbol>",B+"p05_salida.txt"),
 ("P3-06","VRP_PROFILE ambiental cambia el filtro diurno; nulo con mirova_equivalent, sombra y experimental","scripts/evaluador_comun.py:53; scripts/banco_paridad.py:60; scripts/auto_audit_weekly.py:295-300","CONFIRMADO EN PARTE",2,"P-E",PY+"scripts_v/p06_perfil_diurno.py <arbol> <perfil>",B+"p06_salida.txt"),
 ("P3-07","Evaluador sin sha de referencia, rutas de lados, sha de codigo ni de index.html; --salida pisa (canal, regla y excluidos si se registran)","scripts/evaluador_comun.py:837-848,897","CONFIRMADO EN PARTE",3,"P-C","grep -n 'sha|hashlib' scripts/evaluador_comun.py",B+"INFORME_VERIFICADOR_F3.md"),
 ("P3-08","sha del record = GITHUB_SHA (si es el codigo corrido); commit sin sha; sin sha de arbol de pipeline/","pipeline/store.py:89-94,549; sombra-codigo-mirova.yml:135","CONFIRMADO EN PARTE",2,"P-C","lectura de codigo",B+"INFORME_VERIFICADOR_F3.md"),
 ("P3-09","Ningun monitor mira el workflow de la sombra ni abre issue","reproc-watchdog.yml:109-115; nrt-monitor.yml:44; scripts/medir_cadencia_cron.py:37-40; sombra-codigo-mirova.yml","CONFIRMADO",3,"P-F","grep -rn sombra .github/workflows/",B+"INFORME_VERIFICADOR_F3.md"),
 ("P3-10","cargar_lado carga records de K caido como via y descarta sin conteo fechas ilegibles y sensor None","scripts/evaluador_comun.py:760-768","CONFIRMADO",3,"P-B",PY+"scripts_v/p10_p11_p13.py <arbol> <carpeta>",B+"p10_p11_p13_salida.txt"),
 ("P3-11","--ref: respaldo con nombre distinto al del repo se omite en silencio (aporta 0 con historico); historico puede faltar en silencio","scripts/evaluador_comun.py:806-807,818-821; scripts/referencia_mirova_unificada.py:74,76","CONFIRMADO EN PARTE",2,"P-F",PY+"scripts_v/p10_p11_p13.py <arbol> <carpeta>",B+"p10_p11_p13_salida.txt"),
 ("P3-12","VRP nan o inf cuenta como protegida; sustrato 0 de 57907 filas","scripts/clase_mirova.py:72,281","CONFIRMADO",2,"P-D",PY+"scripts_v/p12_nan.py <arbol> ref_snap",B+"p12_salida.txt"),
 ("P3-13","cargar_filas_referencia cae a None en silencio","scripts/auto_audit_weekly.py:659-665,549-552","CONFIRMADO",2,"P-F",PY+"scripts_v/p10_p11_p13.py <arbol> <carpeta>",B+"p10_p11_p13_salida.txt"),
 ("P3-14","evaluador_comun no llama avisar; 0 avisos en ventana de sombra","scripts/evaluador_comun.py (ausencia); scripts/banco_paridad.py:221-225","CONFIRMADO",1,"P-C","ver p14_salida.txt",B+"p14_salida.txt"),
 ("P3-15","Fecha minima sobre fechas pedidas; granulo de borde de medianoche entraria con fecha anterior (sustrato probablemente nulo)","scripts/ventana_sombra.py:39-46; pipeline/fetch.py:608-637","CONFIRMADO",1,"P-C","lectura de codigo",B+"INFORME_VERIFICADOR_F3.md"),
 ("VF3-01","Un record de K caido deja el job rojo 8 dias seguidos y tapa fallas nuevas","scripts/revisar_sombra.py:27-39","CONFIRMADO",2,"P-F",PY+"-X utf8 scripts_v/vf_rojo_arrastrado.py <arbol>",B+"vf_rojo_arrastrado_salida.txt"),
]
with open(B + "hallazgos.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["id","titulo","archivo_linea","confianza","gravedad","eje","comando_reproduccion","salida_cruda"]); w.writerows(filas)
print(len(filas))
