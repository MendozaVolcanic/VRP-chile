# -*- coding: utf-8 -*-
"""Escribe hallazgos.csv del frente D (S179) con el modulo csv. Uso: python escribir_hallazgos_csv.py"""
import csv
import os

C = os.path.dirname(os.path.abspath(__file__))
MAIN = "D:/vrp-trabajo/temporales/s179-audit/main"
BASE = "D:/vrp-trabajo/temporales/s179-audit/d/base"
T = "D:/vrp-trabajo/temporales/s179-audit/d"
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
M4 = (f"python m4_reemplazo_efecto.py {MAIN} {BASE} C:/Users/nmend/vrp-temporales/s177_d2 "
      f"C:/Users/nmend/vrp-temporales/s177_d4 {T}/union_d2_d4 m4_reemplazo_efecto_salida.json")
M5 = f"python m5_cinco_protegidas_v375.py {MAIN} {BASE} {T}/union_d2_d4 m4_reemplazo_efecto_salida.json m5_cinco_protegidas_v375_salida.json"
M2 = f"python m2_estado_serie.py {BASE}/data/mirova_equivalent m2_estado_serie_salida.json"
M6 = f"node m6_vista_preliminar_34.js {MAIN} {BASE}/data/sombra_34 m6_vista_preliminar_34_salida.json"


def s(nombre):
    return os.path.join(C, nombre)


FILAS = [
    (551, "B1 enciende la posicion radiante; la evidencia que lo autoriza es de cercano; con el predicado del tablero la via calla 5 de 72 protegidas VIIRS 375 que K publica",
     "experiments/_s172_retro_paquete/leer_retro.py:1274 (438a60a1e); tasks/LOOP_OBJETIVOS.md:2256,2300,3005 (0472cd95e)",
     "CONFIRMADO lo medido; SOSPECHA que MIROVA alertara en el crater (falta la imagen)", 4, "orden de encendido B1",
     M4 + " ; " + M5, s("m5_cinco_protegidas_v375_salida.txt")),
    (552, "El paso MODIS del plan de reemplazo deja ciega la vigilancia de la guardia K de MODIS (nulo 167 a 0 pares, VERDE a VIGILANCIA_CIEGA)",
     "scripts/vigilancia_guardia_modis.py:296-313,374-379,526-528 (438a60a1e)", "CONFIRMADO", 3, "reemplazo de la historia",
     f"python m3_vigilancia_tras_reemplazo.py {MAIN} {BASE} {T}/sim_modis m3_vigilancia_tras_reemplazo_salida.json",
     s("m3_vigilancia_tras_reemplazo_salida.txt")),
    (553, "El paso VIIRS del plan de reemplazo corre el encendido de la regla sellada al 2026-11-08 18:04 UTC y borra el nulo de la guardia K de VIIRS (223 a 0 pares)",
     "experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md:55-59 (438a60a1e); scripts/vigilancia_guardia_modis.py:124-146",
     "CONFIRMADO", 3, "reemplazo de la historia",
     f"python m3b_vigilancia_viirs_tras_reemplazo.py {MAIN} {BASE} {T}/sim_viirs m3b_vigilancia_viirs_tras_reemplazo_salida.json",
     s("m3b_vigilancia_viirs_tras_reemplazo_salida.txt")),
    (554, "El plan de reemplazo no cuenta que deja de publicarse y se aplicaria sobre meses sin lectura contra MIROVA (P4)",
     "docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:6-7,272-274 (62ccb8830, fuera de main); docs/MISSION.md:113 (438a60a1e)",
     "CONFIRMADO en F26, DM y R25; SIN DATO en las ventanas de P4", 3, "reemplazo de la historia", M4, s("m4_reemplazo_efecto_salida.txt")),
    (555, "Un record K residual mueve la linea de cambio de detector a una fecha falsa en todas las vistas; la comprobacion del plan (sin aviso naranja) ya no puede fallar",
     "frontend/cambio_detector.js:211-226,273-303 (438a60a1e); docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:196-200,278 (62ccb8830)",
     "CONFIRMADO en el modulo; no visto en navegador", 2, "reemplazo de la historia",
     f"node m7_linea_via_con_k_residual.js {MAIN} {BASE}/data/mirova_equivalent", s("m7_linea_via_con_k_residual_salida.txt")),
    (556, "El orden de encendido escrito no se puede ejecutar como esta: #974 y #983 chocan con main en la ficha SDA; #983 trae B1 y B2",
     "tasks/BLOQUE_ARRANQUE_S179.md:38-39,110; tasks/LOOP_OBJETIVOS.md:582 (0472cd95e)", "CONFIRMADO en la base", 2, "orden de encendido",
     f'git -C "{REPO}" merge-tree $(git -C "{REPO}" merge-base 438a60a1e bbbe2068d) 438a60a1e bbbe2068d | grep -c "<<<<<<<"',
     s("INFORME_D.md")),
    (557, "Las compuertas A y B del plan de los 34 ya no se pueden ejecutar como estan escritas",
     "docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md:9-14,88-90,397-401 (0472cd95e); tasks/LOOP_OBJETIVOS.md:597,629-635,1599-1604",
     "CONFIRMADO", 2, "red de los 34", M6, s("m6_vista_preliminar_34_salida.txt")),
    (558, "Los 34 tienen pagina publica desde el 2026-11-09, antes de la compuerta B; 15 de 34 muestran foco lejano sin revisar; la frase de Nicolas no esta citada",
     "frontend/preliminar_34.html:39-43,66 (438a60a1e); tasks/LOOP_OBJETIVOS.md:699 (0472cd95e)",
     "CONFIRMADO lo medido; SIN RESPALDO documental de la frase", 2, "red de los 34", M6, s("m6_vista_preliminar_34_salida.txt")),
    (559, "La fase 4 del plan de los 34 escribe en data/mirova_equivalent, contra docs/MISSION.md; los JSON de abril de los 34 siguen en la carpeta de la replica",
     "docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md:631 (0472cd95e); docs/MISSION.md:78-81,408-409 (438a60a1e)",
     "CONFIRMADO", 2, "red de los 34", M2, s("m2_estado_serie_salida.txt")),
    (560, "El despliegue de Pages copia 586 MB de carpetas que el tablero no lee; la prueba solo vigila sombras y guardias; las carpetas nuevas del plan irian al sitio publico",
     ".github/workflows/pages-deploy.yml:77,81; tests/test_pages_sin_sombras_s173.py:29-36 (438a60a1e)",
     "CONFIRMADO el tamano; SOSPECHA que no haya otros consumidores", 2, "reemplazo de la historia",
     f'python m1_pages_tamano.py "{REPO}" 438a60a1e m1_pages_tamano_salida.json', s("m1_pages_tamano_salida.txt")),
    (561, "Ningun documento dice como se revierte la via de un sensor despues de reemplazar su historia",
     "experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md:108-110,128-130 (438a60a1e); docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:279-280 (62ccb8830)",
     "CONFIRMADO que no lo cubren; SOSPECHA sobre el tamano del trabajo", 2, "reemplazo de la historia",
     "lectura de las lineas citadas (no simulado)", s("INFORME_D.md")),
    (562, "Los records de la via que el plan necesita no estan en git: P4 solo en GitHub hasta cerca del 2026-12-10; D2 y D4 solo en un disco local",
     "docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:153-160 (62ccb8830)", "CONFIRMADO", 2, "reemplazo de la historia",
     "curl -s https://api.github.com/repos/MendozaVolcanic/VRP-chile/actions/runs/42749607584 ; ls C:/Users/nmend/vrp-temporales/",
     s("api_run_p4.json")),
    (563, "El plan de reemplazo quedo atras de main: razon basada en un aviso que ya no existe, el script pisaria 22 records de la via, P5 caera, nombra #975",
     "docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:13-16,142-147,266,282 (62ccb8830); scripts/reemplazar_ventana_reproceso.py:55-83; tests/test_guard_regla_c_s134.py:69-87 (438a60a1e)",
     "CONFIRMADO", 2, "reemplazo de la historia", M2, s("m2_estado_serie_salida.txt")),
    (564, "La pagina preliminar de los 34 usa un radio de cumbre sin decision de Nicolas y no marca el foco de un Tier A vecino",
     "frontend/preliminar_34.js:12-14 y funcion focosCompartidos (438a60a1e); tasks/BLOQUE_ARRANQUE_S178.md:47 (0472cd95e)",
     "CONFIRMADO por lectura; el caso del vecino es SOSPECHA", 1, "red de los 34", M6, s("m6_vista_preliminar_34_salida.txt")),
]

with open(os.path.join(C, "hallazgos.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for f in FILAS:
        w.writerow(f)
with open(os.path.join(C, "hallazgos.csv"), newline="", encoding="utf-8") as fh:
    filas = list(csv.reader(fh))
assert all(len(f) == 8 for f in filas), "columnas corridas"
assert all(os.path.exists(f[7]) for f in filas[1:]), [f[7] for f in filas[1:] if not os.path.exists(f[7])]
print(len(filas) - 1, "hallazgos; 8 columnas en todas las filas; todas las salidas existen")
