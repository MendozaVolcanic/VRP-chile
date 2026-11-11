# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Escribe hallazgos.csv con el modulo csv (una fila por hallazgo del INFORME.md)."""
import csv

C = "C:\\Users\\nmend\\OneDrive\\Escritorio\\claude\\Volcanologia\\VRP Chile\\experiments\\_s179_audit\\c\\"
T = "D:\\vrp-trabajo\\temporales\\s179-audit\\c\\"
L = "experiments/_s172_retro_paquete/leer_retro.py"
P = "experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md"
EJE = "C instrumento y retrospectiva"
c03 = f'python "{C}c03_lectura_propia.py" "{T}tabla_tag.json" "{T}lectura\\lectura.json"'
filas = [
    (501, "El veredicto fila 6 de VIIRS 375 depende de la exencion N-3 del lector (L4); con la letra del §4.1 seria "
          "fila 4, y 3 protegidas solo del OCR que K publica y la via radiante no nunca se listaron",
     f"{L}:42-43,417-431,1309 (main 438a60a1e); {P}:232-234,312,487 (tag s173-prereg-retro-sellado)", "CONFIRMADO", 3,
     f'python "{C}c05_ocr_solo_cercano.py"', C + "c05_ocr_solo_cercano_salida.txt"),
    (502, "En VIIRS 750 P2 GANA (B 17) baja a EMPATE (B 9, neto -3) sin las pasadas miradas por nombre, y el lector "
          "no lo informa",
     f"{L}:1326-1328,520-541 (main 438a60a1e); {P}:155-157,171-173", "CONFIRMADO", 3, c03,
     C + "c03_lectura_propia_salida.txt"),
    (503, "El sorteo de etiquetas del §7 no se corrio con la lectura aprobada por Nicolas (decision 2 de S174); "
          "corrido aqui lo observado se sostiene pero GANA sale por azar en 8,4 % (MODIS) y 10,3 % (VIIRS 375)",
     f"{L}:1156-1177 (main 438a60a1e); tasks/LOOP_OBJETIVOS.md:1179 (0472cd95e); {P}:469-470", "CONFIRMADO", 2,
     f'python "{C}c07_sorteo_s7.py" "{T}tabla_tag.json" 1000', C + "c07_sorteo_s7_salida.txt"),
    (504, "C-K cubre 12 de las 70 pasadas que deciden P2 (MODIS 2 de 7, VIIRS 375 4 de 46, VIIRS 750 6 de 17); los "
          "tres dias del K-gemelo se eligieron tras el sello",
     f"{P}:402,568; tasks/LOOP_OBJETIVOS.md:738 (0472cd95e)", "CONFIRMADO", 2, c03,
     C + "c03_lectura_propia_salida.txt"),
    (505, "El candado compara contra un manifiesto armado desde la misma ref de lectura (31 s antes): no ve que el "
          "lector cambio con los datos en disco, y deja fuera cambio_detector.js, auto_audit_weekly.py, "
          "volcanoes.yaml y las capas de la referencia; efecto medido 0",
     f"experiments/_s172_retro_paquete/armar_manifiesto.py:68-69,94 y {L}:890-893,910-920 (tag s178-retro-lectura); "
     f"{P}:410,604-610", "CONFIRMADO", 2,
     f'python "{C}c11_candado_y_reproduccion.py"; bash "{C}c12_identidad_git.sh"',
     C + "c11_candado_y_reproduccion_salida.txt"),
    (506, "La pregunta del cenit quedo sin veredicto en los tres sensores (curva SIN SUSTRATO, sabido desde S174) y "
          "el lector no calcula la curva de R25 que piden el §5.3 y la prediccion 5; calculada: K/OSF cae con el "
          "cenit y via/OSF no",
     f"{L}:1310,1239-1242 (main 438a60a1e); {P}:89-92,342-344,530", "CONFIRMADO", 2,
     f'python "{C}c04_r25_osf_propio.py" "{T}tabla_tag.json" "{T}lectura\\lectura.json"',
     C + "c04_r25_osf_propio_salida.txt"),
    (507, "El lector no informa las alertas bajo 1 MW del OSF en R25 que el §4.2 manda informar; calculado: VIIRS "
          "375 via 1.440 de 1.485 (97,0 %) contra K 1.399 (94,2 %), 8 volcanes",
     f"{L}:971-1038 (main 438a60a1e); {P}:280", "CONFIRMADO", 2, f'python "{C}c10_r25_bajo1_y_solo_via.py"',
     C + "c10_r25_bajo1_y_solo_via_salida.txt"),
    (508, "La noche del operador (§5.5) esta vacia en VIIRS: 0 noches limpias de 627 porque toda noche tiene una "
          "pasada NOAA-21 sin fila; el lector imprime 0 de 0 sin avisar",
     f"{L}:1203-1224 (main 438a60a1e); {P}:369-370", "CONFIRMADO", 2, c03, C + "c03_lectura_propia_salida.txt"),
    (509, "El nombre del veredicto de VIIRS 375 lista cuatro volcanes con alertas sin conteos ni tramo: en F26 las "
          "26 protegidas son todas de Lascar; los otros tres vienen del OSF de 2025",
     f"{L}:1260-1265 (main 438a60a1e); {P}:492", "CONFIRMADO", 2, c03, C + "c03_lectura_propia_salida.txt"),
    (510, "C-montaje con la banda post hoc de VIIRS 375: el rotulo no viaja con la lectura (montaje.json dice OK), "
          "la causa triangulacion no se probo re-corriendo, y el rango es -3,4 % a +7,4 %, no 0,3 a 3 %; la banda "
          "conserva poder (48 de 51 con 5 % de mas)",
     f"experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md:93,103 (0472cd95e); experiments/_s178_lectura/montaje.json "
     f"(claude/s178-retro-lectura); {P}:403", "CONFIRMADO", 2, f'python "{C}c08_montaje_v375_propio.py"',
     C + "c08_montaje_v375_propio_salida.txt"),
    (511, "El control «el nulo de runner puede fallar» no puede fallar: B contra placebo es 0 por construccion y la "
          "mediana de d del placebo es -0,0792 siempre",
     f"{L}:716-721 (main 438a60a1e); {P}:407", "CONFIRMADO", 2, c03, T + "lectura\\lectura.json"),
    (512, "La decision 6 de S174 (fijar tags de origen y campos de C-montaje antes de despachar D3) no se cumplio: "
          "se fijaron el 2026-11-10 con D2 a D4 ya en disco",
     "tasks/LOOP_OBJETIVOS.md:1183,662-668 (0472cd95e); experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md:3",
     "CONFIRMADO", 2, f'bash "{C}c12_identidad_git.sh"', C + "c12_identidad_git_salida.txt"),
    (513, "El M MEJORA informado es el criterio d, que K x 1,2 tambien cumple; con d prima propio MODIS queda en el "
          "borde: -0,034 [-0,171; 0,000], n 11, todo Lascar",
     "experiments/_s172_retro_paquete/reglas/evaluar_f4.py:292-305 (tag s178-retro-lectura)", "CONFIRMADO", 1, c03,
     C + "c03_lectura_propia_salida.txt"),
    (514, "La lista «alertas de la tabla sin pasada nuestra» del lector cuenta abril a septiembre (1.094); dentro "
          "de F26 son 0 protegidas y 2 bajo 1 MW",
     f"{L}:344-355,1430 (main 438a60a1e)", "CONFIRMADO", 1, f'python "{C}c06_alertas_sin_pasada.py"',
     C + "c06_alertas_sin_pasada_salida.txt"),
    (515, "Tres decisiones del instrumento (2, 3 y 4 del bloque S175: VPR952-04, pre-registro l. 409, fila 4 por la "
          "curva) salieron de la cola sin respuesta registrada",
     "tasks/BLOQUE_ARRANQUE_S175.md:50-52; tasks/BLOQUE_ARRANQUE_S176.md:46; tasks/BLOQUE_ARRANQUE_S177.md:45 "
     "(0472cd95e)", "CONFIRMADO", 1, f'python "{C}c09_controles_con_insumo_vacio.py"',
     C + "c09_controles_con_insumo_vacio_salida.txt"),
    (516, "El sello no dejo el sha256 LF del pre-registro en el mensaje del commit ni en el tag, como pide el §11; "
          "la identidad descansa en el blob de git",
     f"{P}:614-616; tag s173-prereg-retro-sellado", "CONFIRMADO", 1, f'bash "{C}c12_identidad_git.sh"',
     C + "c12_identidad_git_salida.txt"),
    (517, "Las cifras del §7 no se recalcularon al cambiar el commit de K (47cdc446f, a7a6ae360, e7cfbaf54) como "
          "manda el §7; medido: K identico en las ventanas (46.468 records)",
     f"{P}:472-474,622-624", "CONFIRMADO", 1, f'python "{C}c01_armar_insumos.py"',
     C + "c01_armar_insumos_salida.txt"),
]
with open(C + "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for i, t, a, c, g, cmd, sal in filas:
        w.writerow([i, t, a, c, g, EJE, cmd, sal])
with open(C + "hallazgos.csv", newline="", encoding="utf-8") as fh:
    rs = list(csv.reader(fh))
print("filas:", len(rs) - 1, "| columnas por fila:", sorted({len(r) for r in rs}))
