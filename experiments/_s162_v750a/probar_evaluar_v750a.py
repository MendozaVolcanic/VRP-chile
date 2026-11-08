# -*- coding: utf-8 -*-
"""S162 V750-A: pruebas del analizador `evaluar_v750a.py` (PREREGISTRO_V750A.md §5 a §7), escritas ANTES del analizador.

POR QUÉ. La regla de adopción de V750-A se aplica una sola vez sobre el censo y otra sobre la sombra; si el analizador
diera un veredicto por una razón que no es la escrita, no se corrige después. Cada escenario arma una población
sintética en el formato que el analizador lee (objetivos + resultados_00.json + pasadas sin gránulo + salida de la
prueba de equivalencia local), corre el analizador ENTERO (predicado del tablero con node incluido) y comprueba SOLO lo
que la regla escrita predice. Contra un analizador vacío cada escenario tiene que fallar POR ASERCIÓN (falta la línea
esperada), no por excepción.

Escenarios (población base B: 5 noches x Láscar y Villarrica con una protegida en T y otras tantas en O, donde P da la
magnitud de MIROVA y K un factor 0,3 a 0,75; 6 negativos limpios por ventana que K publica y P no; en O una protegida de
Cordón Caulle que P publica y P-def no, decidida por la escena (con u1 distinto de u2 en la zona 2); una alerta baja de
Láscar que P-def no publica con el cráter muy sobre los dos umbrales; una alerta baja de Villarrica que P-def no publica
porque cambió el cráter con el mismo umbral; un negativo lejano que sólo P-sinfiltro publica):
  E00 base: CUMPLE el censo; S-1 nombra la protegida de Cordón Caulle y no la de Láscar; P-sinfiltro +1 contra P.
  E01 P pierde una protegida que K publica (O): NO CUMPLE por P1.
  E02 una protegida que ni K ni P publican: no es veto, se lista; CUMPLE.
  E03 P2 PIERDE en T: NO CUMPLE (no «informar por canal»).
  E04 P2 PIERDE sólo en O: INFORMAR POR CANAL ANTES DE DECIDIR.
  E05 P2 SIN SUSTRATO en T: NO CUMPLE (LECTURA: §6.2 pide GANA o EMPATE).
  E06 P = 1,3 x MIROVA: NO CUMPLE por la razón de M.
  E07 P = K x ganancia uniforme (razón ~1): NO CUMPLE por el comparador.
  E08 P distinto de O fuera de la banda: §6.1 NO SE CUMPLE, sin veredicto del censo (salida 6).
  E09 P distinto de O dentro de la banda: se lista aparte; CUMPLE.
  E10 sin la salida de la equivalencia local: §6.1 NO SE CUMPLE (salida 6).
  E11 equivalencia local con una mutación no atrapada: §6.1 NO SE CUMPLE (salida 6).
  E12 P-def publica la protegida de Cordón Caulle: control positivo de la ROI cae, compuerta cerrada (salida 3).
  E13 el gemelo de K publica 6 negativos que K no: control nulo cae, compuerta cerrada (salida 3).
  E14 K distinto de producción en 2 pasadas: compuerta cerrada (salida 3).
  E15 2 pasadas en error: cobertura INSUFICIENTE, compuerta cerrada (salida 3).
  E16 lo mismo con --leer-con-faltantes: veredicto marcado (salida 5).
  E17 una pasada «ok» a la que le falta el brazo O: cuenta como SIN DATO y cierra la cobertura (es protegida), no
      desaparece en silencio del denominador.
  E18 sombra base: CUMPLE §6.3.
  E19 sombra, P pierde una protegida que K publica: NO CUMPLE.
  E20 sombra sin bloques bajo 1 MW y P1 = 0: CUMPLE sólo por veto (SIN SUSTRATO).
  E21 sombra con P2 PIERDE: NO CUMPLE.
  E22 el archivo de pasadas sin gránulo es de otra lista: cobertura INSUFICIENTE (salida 3).
  E24 P2 BLOQUEA en T (neto +2 en 6 bloques): NO CUMPLE (§6.2 excluye PIERDE y BLOQUEA).
  E25 P2 en T decidido por 6 alertas bajo 1 MW que P publica y K no (sin negativos): CUMPLE.
  E26 protegida sólo del OCR en O que K publica y P no: NO CUMPLE en tabla más OCR y no con la tabla sola.
  E27 O alerta otra celda con el mismo VRP (máscara distinta): §6.1 NO SE CUMPLE (salida 6).
  E23 sombra con P2 BLOQUEA (neto +2 en 6 bloques): CUMPLE (LECTURA: §6.3 sólo excluye PIERDE).
Agregados tras el verificador limpio (verificador/INFORME.md, VA-01 a VA-08), cada uno fija una regla que una rotura de
una línea dejaba pasar:
  E28 una sola pasada no protegida con K distinto de producción entre 109: control OK (hasta 1 %, L18 por D-48), la
      pasada sale de los brazos (P2 en T pasa de 6 a 5 bloques) y se lista; CUMPLE.
  E29 K publica igual pero su VRP difiere 0,01 MW de producción: compuerta cerrada.
  E30 K de 9,0 MW con t_max 270 K: K x 1,2 cae en el filtro de cirro del tablero; la diferencia la explica el filtro
      (t_max bajo 278,15 K), se lista y el control no cae (L7 por D-48); CUMPLE.
  E31 12 protegidas que K no publica y P publica al doble: entran a la razón (L4 por D-48): NO CUMPLE por M razón 2,0;
      la razón sobre las que publican K y P (1,0) se imprime al lado.
  E32 y E33 P = 0,85 y 1,15 x MIROVA: NO CUMPLE por la razón (bordes de la banda).
  E34 2 pasadas sin gránulo del generador: cobertura INSUFICIENTE.
  E35 y E36 con 10 negativos de relleno, 1 pasada en error: SUFICIENTE si no es protegida, INSUFICIENTE si lo es.
  E37 una pasada diurna: SIN DATO «diurna».
  E38 a E41 prueba local con 4 mutaciones atrapadas, sin el control caído, ROJA, o con 100 casos de E1: §6.1 no se cumple.
  E42 --solo-controles: sin veredicto, salida 0.
  E43 6 bloques en 2 noches x 3 volcanes: el bloque de P2 lleva el volcán; GANA.
  E44 T con 2 noches de alertas (4 pares): M SIN SUSTRATO.
  E45 protegida con `decide` falso que P pierde: no es veto; CUMPLE.
  E46 el gemelo de K da la magnitud de MIROVA: el nulo K contra K cae por M.
  E47 sombra con una protegida sólo del OCR que P pierde: NO CUMPLE en tabla más OCR, no con la tabla sola.
  E48 P = 1,3 x MIROVA sólo en T: NO CUMPLE por la razón en T y no en O.
  E49 sombra sin protegidas: CUMPLE marcado «SIN PROTEGIDAS».
Agregados al resolver L2, L4, L7 y L18 por D-48 (relevo VIIRS 750, 2026-10-25):
  E50 dos pasadas no protegidas con K distinto entre 110 (más del 1 %): compuerta cerrada (L18).
  E51 prueba local con 5 mutaciones atrapadas: §6.1 no se cumple (L2: son 6 de 6).
  E52 una sola protegida con el VRP de K distinto de producción entre 110 (bajo el 1 %): cierra igual (L18).
Agregados tras la segunda vuelta del verificador (verificador_v2/INFORME.md, VB-A01 a VB-A07):
  E53 y E54 P = 0,9 y 1,1 x MIROVA: la razón no entra a los motivos (los bordes de la banda están incluidos; el
      comparador da NEUTRO a esa ganancia pareja, conducta de evaluar_d25.py anotada por el verificador).
  E55 la pasada con K distinto (dentro del 1 %) y P distinto de O: §6.1 la sigue mirando y no se cumple (la
      equivalencia P = O se exige sobre todas las observadas, con K o sin K).
  E56 sombra, 1 pasada con K distinto de 24 (más del 1 %): compuerta cerrada. E57 la misma con 114: no cierra, se lista.
  E58 una protegida sólo del OCR con K distinto, entre 111: cierra («ninguna protegida» es tabla más OCR).
  E59 K de 45.000 MW con t_max tibio: K x 1,2 pasa el tope de 50.000 MW del tablero; explicada, se lista y no cierra.
  E60 prueba local con seis líneas «atrapada» pero una de otra pieza: §6.1 no se cumple (las seis se exigen por nombre).
Agregados con los brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27). Tres escenas de píxeles: «cerca y
lejos» (un alertado débil en el cráter y otro más radiante a 11,25 km: radiante y pico lejos, cercano en la cumbre),
«línea» (el más radiante en el cráter y 15 más débiles contiguos hacia el este: el centroide del cúmulo a 5,6 km, fuera
del radio de 5 km; pico y cercano en el cráter) y la de Llaima con el cráter corrido del centro de la grilla:
  E61 6 alertas bajo 1 MW «cerca y lejos»: P-cercano gana en P2' y es elegible; el §6 se evalúa sobre P-cercano (P2 contra
      K en T pasa de neto -6 a -12) y las 6 pasadas que cambian salen por nombre.
  E62 6 bajas «línea» y 6 negativos «cerca y lejos»: P-pico gana solo (P-cercano empata) y el §6 se evalúa sobre él.
  E63 3 bajas «cerca y lejos» (SIN SUSTRATO): ninguno gana y queda P (radiante).
  E64 una protegida «cerca y lejos» que K publica: P y P-pico no son elegibles, P-cercano sí y no es peor: se elige.
  E65 la protegida de E64 y 6 negativos que sólo P-cercano publica (PIERDE): NINGUNA POSICIÓN ELEGIBLE, NO CUMPLE.
  E66 ganan los dos, P-cercano con menor E + E_lejana: se elige P-cercano.
  E67 ganan los dos con el mismo E + E_lejana: se elige P-pico.
  E68 6 bajas que P-cercano gana y 6 far_ref que publica de más: con E_lejana empata y queda P.
  E69 P-cercano gana con el canal que decide (bajas del OCR en O) y con la tabla sola es SIN SUSTRATO con neto +1: no gana.
  E70 Llaima con el cráter a 6,4 km del centro y un alertado en el centro: medido desde el cráter, P-cercano no publica.
  E71 3 far_ref sin alertados que K publica: E_lejana 0 marcado «no dice nada», y las far_ref no entran a P2 contra K.
  E72 base sin far_ref: la vara lejana es SIN DATO y la regla se lee igual (queda P).
  E73 4 alertas sólo del OCR antes del 2026-06-13: no entran a la distancia contra MIROVA (A119).
Agregados tras el verificador limpio de los brazos de posición (verificador_posicion/INFORME.md, LISTO CON CAMBIOS;
W3 y W4 son suyos, W5 adaptado):
  E74 (W3) una protegida sólo del OCR que K y P publican y cercano y pico pierden (escena «anillo»): «elegible» mira
      también tabla más OCR, así que P-cercano no es elegible aunque gane P2' y queda P (radiante).
  E75 (W4) bajas y far_ref sólo del OCR en O: con la tabla sola E_lejana no cuenta los FALSO_POSITIVO_OCR (SIN SUSTRATO
      con neto 0, no peor) y P-cercano gana con el canal que decide (neto -8 en 16 bloques).
  E76 (W5) 24 pasadas que cambian contra P: la lista impresa dice que se cortó a 20 (VP-01).
Agregados por la regla N-3 (§6 ter, S170), rojos contra el analizador sin N-3:
  E77 la protegida sólo del OCR de E26, pero de Suomi NPP y antes del 2026-10-09: no veta (CUMPLE), se lista aparte
      con el brazo que la publica (K) y el P1 que la cuenta queda al lado.
  E78 la misma, el 2026-10-09: ya no es de la clase y veta (O/todo: P1 1).
  E79 la misma antes del 2026-10-09 pero con alerta de la tabla: veta con la tabla sola y con tabla más OCR.
  E80 en la sombra (§6.3) la regla no se aplica: la protegida sólo del OCR de Suomi NPP anterior al 2026-10-09 veta.
Agregados en S173 por VPR939-03 (verificador del PR #939, la ROI B4 de VIIRS 750): la sombra trae pasadas de Cordón
Caulle con la ROI vieja (def, sha anterior al merge) y con la nueva (sens); el lector no puede mezclarlas (A104). Todas
las pasadas de la sombra llevan en el record de P `diag_codigo_mirova.roi` y `regimen.codigo_sha`, como los reales
(ids ER, no E5x, porque la rama de V750-A `claude/s162-viirs750-2-918174` ya usa E50 a E80):
  ER1 mezcla de dos ROI sin --roi-brazo: compuerta cerrada (salida 3), sin veredicto. El lector de antes daba veredicto (NO CUMPLE por la pasada vieja).
  ER2 la misma mezcla con --roi-brazo B4: la pasada def de Cordón Caulle queda fuera por otra ROI. S174 (VPR945-R2-02):
      con el corte de prueba (anterior a las dos ROI) esa pasada def desciende del corte, la ROI de Cordón Caulle cambió
      dentro de lo leído y la compuerta se cierra (salida 3); antes daba CUMPLE. El corte por cenit pasó a ER5.
  ER3 la misma mezcla con --roi-brazo B0: quedan fuera las dos sens (cuenta «otra ROI 2») y, por lo mismo que ER2, la
      compuerta se cierra (salida 3); antes daba NO CUMPLE por P1 en la def.
  ER4 una protegida cuyo record de P no trae régimen: SIN DATO «sin_regimen», cobertura INSUFICIENTE (salida 3).
  ER5 shas reales del repo con --sha-desde el merge de #939: 6 protegidas de sha anterior quedan fuera como anteriores
      al corte (git merge-base --is-ancestor) y la def de Cordón Caulle por otra ROI; CUMPLE. S174 (R2): imprime la hora
      del commit del corte y la ventana desde ella; 16 noches, 38,9 días; el corte por cenit (30°, el borde de 30 va
      arriba) informa 2 pasadas sobre 30° y 18 bajo 30°.
  ER6 lo mismo con una pasada cuyo sha no existe en el repo: SIN DATO «sha_desconocido» (salida 3); «dentro» no la
      cuenta.
Agregados en S174 por VPR945 (verificador limpio del PR #945; ids ER8 en adelante porque la rama
`claude/s162-viirs750-2-918174` ya usa ER7). Las pasadas de la sombra base cubren ahora más de 4 semanas (los negativos
de Villarrica del 10 al 15 de diciembre) para que los escenarios de siempre sigan leyendo un veredicto final; la mezcla
suma una pasada de Cordón Caulle def fuera del gránulo (no observada: no entra al régimen):
  ER8 una protegida con sha pero sin ROI en el record de P: SIN DATO «sin_regimen» (salida 3), no «otra ROI».
  ER9 una protegida con ROI pero sin sha: SIN DATO «sin_regimen» (salida 3).
  ER10 dos protegidas de un volcán que no está en el mapa de ROI («Nevados de Chillan»): SIN DATO «volcan_sin_roi»,
      cobertura INSUFICIENTE (salida 3); antes salían como «otra ROI» y la sombra daba CUMPLE (VPR945-02).
  ER11 todas las pasadas de antes del corte: «cobertura: SIN PASADAS OBSERVADAS», sin «SUFICIENTE» ni «control nulo»
      (salida 3, VPR945-03).
  ER12 sombra de 21 días con dos pasadas de octubre que no se leen (una de otra ROI, una fuera del gránulo y, desde
      R2-03, fuera de la ventana): PROVISORIO (salida 4), el reloj parte en la primera pasada leída (VPR945-01).
  ER13 (rehecho en R2-03) una noche del 2 de noviembre reprocesada con el código nuevo: fuera de la ventana (la sombra
      empieza el 2026-11-03), no la ven ni el reloj ni las noches ni la lectura; 26 días: PROVISORIO (salida 4).
  ER15 --sha-desde HEAD: compuerta cerrada con su mensaje (una referencia móvil no se acepta, VPR945-04).
  ER16 una protegida sobre 30° que K publica y P no: NO CUMPLE por P1 (el cenit informa, no cierra la compuerta).
  ER17 --sha-desde con el sha abreviado a 7 caracteres (el piso): la salida lleva el sha completo resuelto.
  ER18 sombra de 21 días con una protegida perdida: NO CUMPLE por P1 (el veto vale antes de las 4 semanas, LR2).
  ER19 sombra de 21 días con P2 PIERDE: PROVISORIO (salida 4), no NO CUMPLE.
  ER2 y ER5 afirman además la línea «protegidas fuera de esta lectura» con las protegidas que salen.
Agregados en S174 por VPR945-R2 (segunda ronda del verificador; LECTURA LR3). --sha-desde es obligatorio en la sombra, así
que todas las pasadas llevan shas reales y los escenarios que no prueban el corte usan SHA_CORTE_PRUEBA (5b13bfed8,
committer 2026-11-02 13:36 UTC, autor 02:27 UTC); los negativos de Villarrica pasan a las 06:00 para que el reloj dé días
enteros. E18 afirma la hora del committer, la ventana desde el 2026-11-03 y las 18 noches; E49 suma dos negativos de
Villarrica para llegar a 14 noches:
  ER20 una pasada del 5 de noviembre 02:00 con el sha de #939, anterior a la hora de su commit (03:23): fuera de la
      ventana aunque descienda del corte («anteriores a la hora del corte 1»); el resto como ER5, CUMPLE.
  ER21 sin --sha-desde: compuerta cerrada con su mensaje (salida 3), antes de leer nada (R2-02).
  ER22 y ER23 el borde de 28,0 días: del 4 de noviembre 06:00 al 2 de diciembre 06:00 da CUMPLE; a las 05:59 da
      PROVISORIO y se lee «27.9» (los días se truncan al décimo, no se redondean).
  ER24 y ER25 (rehechos en R3, ver abajo) el borde de 14 noches (con 34 y 35 días): 13 noches en 14 pasadas (dos la noche del 12) dan PROVISORIO;
      14 noches dan CUMPLE (R2-01).
  ER26 --sha-desde con 6 caracteres: compuerta cerrada aunque git lo resuelva sin ambigüedad (el piso es 7).
  ER27 un PROVISORIO leído con --leer-con-faltantes sale 5 y lleva la marca (R2-04).
  ER28 una pasada def de Cordón Caulle dentro de la ventana con un sha que git no conoce: compuerta cerrada (no se puede
      descartar que su código sea posterior al corte).
  ER29 y ER30 las pasadas sin gránulo del generador se cortan con la misma ventana: una protegida de octubre no frena la
      sombra; una de la ventana deja la cobertura INSUFICIENTE (R2-03).
Agregados en S174 por VPR945-R3 (tercera ronda del verificador; LECTURA LR3). Con B4 cada volcán cuya ROI difiere de B0
(Cordón Caulle y Tupungatito) pide sus noches, y las noches se reparten (7 en cada mitad del lapso). La sombra base suma
negativos sens de esos dos volcanes en cada fecha desde el 7 de noviembre (16 noches cada uno, 9 y 7 por mitad) y un
séptimo negativo de Villarrica (del 9 al 15 de diciembre, la misma última pasada), así que los conteos «dentro» y de
noches de E18, ER2, ER5, ER12, ER13, ER17 y ER20 suben; los villa_dia0 de ER12, ER13, ER18, ER19, ER22, ER23 y ER27 bajan
un día para conservar sus días. ER3 y ER6 van sin el relleno sens (con B0 sería «otra ROI»; en ER6, 1 SIN DATO de 53
dejaría de pasar el 2 %). E49 pasa a 29 noches seguidas. ER24 y ER25 se rehicieron (ver abajo):
  ER24 (rehecho) con B0: 13 noches seguidas y una suelta a 28 días (14 noches, 28,0 días, 13 y 1 por mitad): PROVISORIO.
  ER25 (rehecho) con B0: 7 y 7 por mitad, con una noche justo en la mitad del lapso (va a la segunda): CUMPLE.
  ER31 Cordón Caulle con sens una sola noche y las otras 15 con la ROI def y el sha anterior al merge (fuera por otra ROI
      sin cerrar la compuerta): PROVISORIO, «PuyehueCordonCaulle 1 (0 y 1, faltan)» (R3-01; el lector de antes, CUMPLE).
  ER32 Cordón Caulle y Tupungatito ausentes de los objetivos: 0 noches, PROVISORIO (R3-01, variante).
  ER33 Cordón Caulle con 14 noches, 13 seguidas y una a 38 días: PROVISORIO por su reparto (13 y 1) (R3-02 por volcán).
  ER34 una pasada en el minuto exacto del commit del corte entra a la lectura (R3-04, MV1 del verificador).
  ER35 una pasada de otra ROI con el código del corte en ese minuto cierra la compuerta (R3-04, MV2).
  ER36 control positivo: los 11 volcanes con 14 noches cada uno repartidas en 28 días, B4 desde el merge de #939: CUMPLE.
  E18 afirma además la línea de noches por volcán (los 11, también con 0) y la de horas UTC de las pasadas leídas (R3-05).
Quinta vuelta en S174 por VPR945-R4 (cuarta ronda del verificador; LECTURA LR3, decisión de Nicolás «Ventana fija, una
vuelta»): la ventana de la lectura es fija, [inicio, inicio + 28 días), con 4 semanas fijas desde el inicio, y «ahora» se
fija en las pruebas (AHORA_PRUEBA, el 2026-12-10, después del fin de las dos ventanas; con --sin-ahora no se pasa, sólo
para el rojo contra un lector anterior). La sombra base pone ahora sus noches en las 4 semanas (14 negativos de Villarrica
del 17 al 30 de noviembre y el relleno sens desde el 5), así que cambian los conteos de E18, ER2, ER3, ER5, ER6, ER17,
ER20, ER31 y ER34; E49 lleva negativos de Villarrica cada noche de la ventana; los escenarios «de 21 días» (ER12, ER18,
ER19, ER27) y el de 26 (ER13) se arman con --ahora en vez de correr la última pasada. Rehechos y nuevos:
  ER22 y ER23 el borde de «ahora»: en el fin justo (2026-12-01 00:00) CUMPLE; un segundo antes, PROVISORIO con «27.9».
  ER24 (R3-02) 13 noches seguidas y una al día 28, que cae fuera de ventana: semanas 7, 6, 0, 0, PROVISORIO.
  ER25 (R4-02) con B0, una noche el día 0, 14 seguidas en el centro y una el día 28: semanas 1, 7, 7, 0, PROVISORIO (el
      lector de antes daba CUMPLE).
  ER29 suma una pasada sin gránulo protegida posterior al fin: tampoco cuenta.
  ER33 Cordón Caulle con 13 noches seguidas desde el 7 de noviembre y una el 15 de diciembre (fuera de ventana).
  ER36 control positivo: los 11 volcanes con 5 noches en cada semana y ahora después del fin: CUMPLE.
  ER37 (R4-01) Cordón Caulle y Tupungatito con 14 noches seguidas sólo en las semanas 1 y 2 (los otros nueve en las
      cuatro y una más al día 28): PROVISORIO (el lector de antes, CUMPLE).
  ER38 (R4-03) una protegida con fecha posterior a «ahora» (ahora = inicio + 21 días) que P pierde: fuera de ventana,
      listada, sin veto; PROVISORIO (el lector de antes, NO CUMPLE por esa pasada).
  ER39 borde de semana: una pasada en el minuto exacto de inicio + 7 días va a la semana 2; la 1 queda con 4: PROVISORIO.
  ER40 borde del fin: un minuto antes del fin entra a la semana 4, en el minuto del fin queda fuera de ventana, y una ROI
      distinta después del fin no cierra la compuerta: CUMPLE.
  ER41 (R4-04, MW10) Cordón Caulle con la semana 4 sólo en pasadas no observadas y SIN DATO, en noches distintas de las
      de los otros volcanes: 0 noches en esa semana, PROVISORIO.
  ER42 un volcán sin cambio de ROI con dos semanas vacías informa y no decide: CUMPLE.
  ER43 sin --ahora, la salida dice que usó el reloj de la máquina (el veredicto no depende del día).
Sexta vuelta en S174 por VPR945-R5 (quinta ronda del verificador; decisión de Nicolás del 2026-11-06, «Sí, sexta
vuelta»): cada volcán de ROI igual a B0 pide 14 noches en la ventana (sin mínimo semanal), cada noche cuenta una vez (en la
semana de su primera pasada) y --ahora acepta ISO con zona. La sombra base suma un negativo que nadie publica en cada
fecha desde el 5 de noviembre para cada uno de los nueve volcanes sin cambio con B4 (nueve, por omisión igual a sens):
cambian «dentro» y las noches de los nueve en E18 y en los demás escenarios de la sombra base; las etiquetas «informa»
pasan a «sin cambio, completas» o «sin cambio, faltan». Rehechos y nuevos:
  ER36 afirma además que la línea CUMPLE nombra a los nueve con sus noches.
  ER42 (rehecho) el volcán sin cambio con dos semanas vacías tiene ahora 14 noches (7, 7, 0, 0): CUMPLE.
  ER44 (R5-01) --ahora con Z: CUMPLE (el lector de antes se caía con TypeError; en ER44 y ER45 el Traceback es la
      aserción «no se cae», no una caída).
  ER45 (R5-01) --ahora con -03:00 en el fin justo (00:23 en UTC-3 = 03:23 UTC): CUMPLE; con la zona ignorada, PROVISORIO.
  ER46 (R5-04, MX13) una pasada en el minuto exacto de «ahora» entra («fuera de ventana 0»).
  ER47 (R5-04, MX11) sin --ahora y con TZ en UTC+12, «ahora» es el reloj UTC (30 minutos de tolerancia).
  ER48 (R5-03, el caso del verificador) sólo Cordón Caulle y Tupungatito con pasadas: PROVISORIO, nombra a los nueve con
      0 (el lector de antes, CUMPLE).
  ER49 (R5-03) uno de los nueve con 13 noches: PROVISORIO, lo nombra (el lector de antes, CUMPLE).
  ER50 (R5-02) la noche del 12 de noviembre con pasadas a los dos lados del borde de la semana 2 en los 11 volcanes: cuenta
      en la semana 1, la 2 queda con 4: PROVISORIO (el lector de antes, CUMPLE con la noche contada en las dos).
  ER51 (R5-03) control positivo en el borde: los nueve con 14 noches justas (5, 5, 4, 0), los dos cambiados con 5 por
      semana: CUMPLE.
  ER52 (R5-01) una fecha ilegible en --ahora: error de argparse con su mensaje, salida 2, sin veredicto.
Retoques en S174 por VPR945-R6 (sexta ronda del verificador limpio, tras el merge de #945; sin cambio de regla):
  ER45 (R6-03) corre con TZ en UTC+12, como ER47: convertir --ahora a la zona local en vez de a UTC se ve también en una
      máquina en UTC.
  ER53 (R6-01) --ahora con zona en una fecha extrema (9999-12-31T23:59:59-03:00): error de argparse, salida 2 (el lector
      de 235ba7918 se caía con OverflowError, salida 1).
  ER54 (R6-02) con B0 uno de los once con 13 noches: PROVISORIO, lo nombra. ER55 su par con 14 justas: CUMPLE.
Retoques en S174 por VPR953 (verificador de #953; sin cambio de regla):
  ER55 (VPR953-03) afirma la lista entera de los once con sus noches en la línea CUMPLE (antes, «Chaiten 14, Copahue 20»).
  ER56 (VPR953-02) con B0, Copahue (el segundo por orden alfabético) y Villarrica (el último) con 13 noches: PROVISORIO,
      nombra a los dos. ER57 su par con 14 justas: CUMPLE, con los once en la línea.
Reconciliación en S175 de las dos líneas (origin/main con el régimen de la sombra y la rama de V750-A con N-3 y los
brazos de posición; ver LECTURAS y el pre-registro). Los ER1 a ER6 de la rama eran los de #945 y quedan los de main;
cuatro escenarios de la rama se reescriben porque la sombra de main los dejaba sin sustrato, y conservan lo que vigilan:
  E56 sombra chica (sin el relleno de los volcanes): 1 pasada con K distinto de 32, más del 1 %, cierra la compuerta.
  E57 sombra base: 1 pasada con K distinto de 266, no cierra y se lista, CUMPLE (antes se llegaba a 114 con relleno de
      diciembre, que ahora cae fuera de la ventana).
  E80 la protegida sólo del OCR de Suomi NPP del 2026-10-08 está antes del inicio de la sombra (§6 ter: «no tiene
      pasadas de esta clase»): sale de la lectura, se lista y no veta. Antes afirmaba que vetaba, lo que supone una
      sombra sin ventana. El M91 de antes (exención N-3 en §6.3) quedó equivalente: ver mutar_evaluar_v750a.py.
  ER7 la protegida def de Cordón Caulle sale por otra ROI, listada por nombre y motivo, ahora con el corte en #939
      (con el corte de prueba la compuerta se cierra, ER2).
La población base suma para el S-1: celda de Cordón Caulle en el pase 2 y la zona 2 (el pase 1 y la zona 1 con otro
umbral), una alerta de Tupungatito cuyo NTI cruza entre los umbrales pero el ETI no, y un diagnóstico mal formado.
Una caída nativa del analizador (código fuera de 0, 3, 4, 5 y 6, sin Traceback) se reintenta 2 veces y si sigue es CAÍDA,
nunca falla por aserción (VA-08).
Uso: python probar_evaluar_v750a.py --dest <carpeta temporal> [--analizador <ruta>] [--evaluador <evaluar_d25.py>]
     [--solo E00,E03]
Salida: 0 si todos los escenarios dan lo esperado; 1 si alguno falla por aserción; 2 si el analizador se cayó en alguno.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SENSOR = "VIIRS_NOAA20_750"
C = 33
# S173 (VPR939-03): régimen del record de P en la sombra, con commits reales de origin/main (git los resuelve):
# 636b3426e es un sha de corrida de la sombra anterior al merge de #939 (58edb9788).
# S174 (VPR945-R2-02): --sha-desde es obligatorio en la sombra, así que ya no hay shas falsos: todo escenario de sombra
# corta en un commit real. SHA_CORTE_PRUEBA (5b13bfed8, ancestro de los dos) es un commit de main cuya hora de committer
# (2026-11-02 13:36 UTC) difiere de la de autor (02:27 UTC) y es anterior al inicio de la sombra: la ventana de la
# lectura parte en el 2026-11-03 y la salida tiene que imprimir la hora del committer.
SHA_REAL_B0 = "636b3426e69e9c6dd79ffacde601eed3c111dc48"
SHA_REAL_B4 = "58edb978825ff08677fc1b3e803a2ca601dd4598"
SHA_CORTE_PRUEBA = "5b13bfed80240c14a14d491b795b2a1e2965436e"
CRATER = {"Lascar": [33, 33], "Villarrica": [33, 33], "PuyehueCordonCaulle": [30, 36], "Tupungatito": [33, 33],
          "Nevados de Chillan": [33, 33],   # S174 (ER10): un nombre que no está en el mapa de ROI
          "Llaima": [27, 39]}   # §6 bis (E70): cráter a 6,4 km del centro de la grilla, radio interior de 5 km
# S174 (VPR945-R3, control positivo ER36): los 11 volcanes del mapa de ROI (scripts/roi_v750b_a_grillas.py::VOLCANES);
# si un nombre no coincidiera, el lector lo marcaría SIN DATO «volcan_sin_roi» y ER36 fallaría
VOLCANES_MAPA = ("Chaiten", "NevadosDeChillan", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "PlanchonPeteroa",
                 "PuyehueCordonCaulle", "Tupungatito", "Villarrica")
for _v in VOLCANES_MAPA:
    CRATER.setdefault(_v, [33, 33])
CAMBIAN_B4 = ("PuyehueCordonCaulle", "Tupungatito")   # los que B4 traduce distinto de B0 (sólo para armar pasadas)
# S174 (VPR945-R4, quinta vuelta): la ventana fija necesita «ahora». Las pruebas lo fijan después del fin de las dos
# ventanas que usan (SHA_CORTE_PRUEBA: 2026-11-03 00:00 a 2026-12-01 00:00; SHA_REAL_B4: 2026-11-05 03:23 a
# 2026-12-03 03:23), salvo los escenarios que prueban el reloj, que pasan su propio --ahora (o sin_ahora=True).
AHORA_PRUEBA = "2026-12-10 00:00"
# la cola de negativos de Villarrica de la sombra base: 14 noches seguidas, del 17 al 30 de noviembre (semanas 3 y 4)
VILLA_FECHAS = tuple(str(datetime.date(2026, 11, 17) + datetime.timedelta(days=n)) for n in range(14))
# esc_once: noches de cada volcán en días desde el 2026-11-05, 5 en cada una de las 4 semanas de la ventana de #939
OFFS_4SEM = (0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25)
PAQ = ("P", "Pdef", "O")

VERDE = """VERDE: E1 1020 casos, E3 10 recortes
   mutación k1_y_minimos         atrapada por aserción (sintético)
   mutación ocho_vecinos         atrapada por aserción (sintético)
   mutación fondo_sin_halo       atrapada por aserción (sintético)
   mutación recorte              atrapada por aserción (sintético)
   mutación fondo_anillo         atrapada por aserción (sintético)
   mutación remuestreo_vecino    atrapada por aserción (sintético)
   mutación control_que_se_cae   caída (RuntimeError)
mutaciones: TODAS COMO SE ESPERA
"""


def diag(c=0.2, u=0.04, sd=0.010, zona=2, u1=None, c_eti=None, pase=1, u_otro_pase=None):
    """Diagnóstico del .m que deja el productor del artefacto para el S-1: sd y umbrales de cada pase y la celda
    decisiva del cráter (contraste NTI y ETI, pase y zona). u es el umbral de la zona 2 (u2); u1 el de las zonas 0 y 1;
    u_otro_pase, si se da, es TODO umbral del pase que no es el de la celda (para distinguir pase 1 de pase 2)."""
    u1 = u if u1 is None else u1
    p = {"sd_nti": sd, "sd_eti": sd, "u_nti1": u1, "u_nti2": u, "u_eti1": u1, "u_eti2": u}
    q = dict(p) if u_otro_pase is None else {"sd_nti": sd, "sd_eti": sd, "u_nti1": u_otro_pase,
                                             "u_nti2": u_otro_pase, "u_eti1": u_otro_pase, "u_eti2": u_otro_pase}
    pases = {"pasada1": dict(p), "pasada2": dict(q)} if pase == 1 else {"pasada1": dict(q), "pasada2": dict(p)}
    return dict(pases, celda_decisiva={"pase": pase, "zona": zona, "c_nti": c, "c_eti": c if c_eti is None else c_eti})


def salida_paquete(vrp, volcan, far=False, d=None):
    """Salida del .m (como la del oráculo): npix, vrp_mw, píxeles [fila, col, zona, -, M13] y diagnóstico."""
    if vrp is None:
        return {"npix": 0, "vrp_mw": None, "pixeles": [], "diag": d or diag(c=0.0)}
    f, c = CRATER[volcan]
    if far:
        c += 15                                   # 11,25 km del cráter: fuera de cualquier inner salvo Cordón Caulle
    return {"npix": 1, "vrp_mw": vrp, "pixeles": [[f, c, 2, 0.0, 1.0]], "diag": d or diag()}


def k_record(vrp, t_max=300.0):
    if vrp is None:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": t_max, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, K=None, P=None, Pdef="=P", O="=P", gemelo="=K", mirova_vrp=None,
               tabla=True, z=20.0, dP=None, dPdef=None, dO=None, far=False, banda=False, estado="ok",
               pub_prod="=K", falta=(), decide=True, dayflag=0, k_tmax=300.0, px=None, dist_ref=11.0,
               sensor=SENSOR, roi="def", sha=SHA_REAL_B4, regimen=True):
        """px (§6 bis): píxeles alertados de P, P-def y O cuando no es el de un solo píxel en el cráter (los tres
        iguales, así la equivalencia P = O se mantiene). lab «far_ref»: MIROVA publicó una fuente lejana (fila
        FALSO_POSITIVO de la tabla, o del OCR con tabla=False, a dist_ref km, y ninguna ALERTA). roi, sha y regimen
        (S173, VPR939-03): la ROI y el sha del código que lleva el record de P, como el real; regimen=False los quita."""
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "CONS"})
            else:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "OCR"})
        elif lab == "far_ref":
            filas.append({"fecha_utc": hora + ":00", "tipo": "FALSO_POSITIVO" if tabla else "FALSO_POSITIVO_OCR",
                          "vrp_mw": 0.5, "dist_km": dist_ref, "source": "CONS" if tabla else "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None,
                          "source": "CONS"})
        Pdef = P if Pdef == "=P" else Pdef
        O = P if O == "=P" else O
        gemelo = K if gemelo == "=K" else gemelo
        pp = (K is not None) if pub_prod == "=K" else pub_prod
        self.objs.append({"id": i, "volcan": volcan, "hora_utc": hora, "sensor": sensor, "lab": lab,
                          "decide": lab == "pos" and decide, "alerta_tabla": lab == "pos" and tabla,
                          "protegida": lab == "pos" and (mirova_vrp or 0) >= 1.0, "mirova": filas,
                          "mirova_vrp": mirova_vrp if lab == "pos" else None, "pub_prod": pp,
                          "pc_vrp": K or 0.0, "z": z, "pos_crater": CRATER[volcan]})
        if lab == "far_ref":
            self.objs[-1]["dist_ref"] = dist_ref
        rp = k_record(P)
        if regimen:   # como el record real de la vía: ROI en el diagnóstico, sha del código en la marca de régimen
            # S174 (VPR945-06): "sin_roi" deja el diagnóstico sin la ROI, "sin_sha" la marca de régimen sin el sha
            rp["diag_codigo_mirova"] = {} if regimen == "sin_roi" else {"roi": roi}
            rp["regimen"] = {"perfil": "sombra_codigo_mirova", "origen": "actions"}
            if regimen != "sin_sha":
                rp["regimen"]["codigo_sha"] = sha
        r = {"id": i, "estado": estado, "dayflag": dayflag, "cobertura": {"nan_7_crater": 0, "nan_crater": False},
             "brazos": {"K": {"record": k_record(K, k_tmax)}, "Kgemelo": {"record": k_record(gemelo, k_tmax)},
                        "Kgeo": {"record": k_record(K)}, "P": {"record": rp}},
             "paquete": {"P": salida_paquete(P, volcan, far, dP), "Pdef": salida_paquete(Pdef, volcan, far, dPdef),
                         "O": salida_paquete(O, volcan, far, dO)},
             "banda_triangulacion": banda}
        if px is not None:
            for b in PAQ:
                if r["paquete"][b]["vrp_mw"] is not None:
                    r["paquete"][b]["pixeles"] = copy.deepcopy(px)
                    r["paquete"][b]["npix"] = len(px)
        for b in falta:
            r["paquete"].pop(b, None)
        self.res.append(r)
        return i

    def escribir(self, d, verde=VERDE, sin_granulo_otra_lista=False, sin_granulo=()):
        d.mkdir(parents=True, exist_ok=True)
        art = d / "art"
        art.mkdir(exist_ok=True)
        fo = d / "objetivos.json"
        fo.write_text(json.dumps(self.objs, ensure_ascii=False), encoding="utf-8")
        (art / "resultados_00.json").write_text(json.dumps(self.res, ensure_ascii=False), encoding="utf-8")
        sha = hashlib.sha256(fo.read_bytes()).hexdigest()
        if sin_granulo_otra_lista:
            sha = "0" * 64
        (d / "sin_granulo.json").write_text(json.dumps({"objetivos_sha256": sha, "pasadas": list(sin_granulo)}),
                                            encoding="utf-8")
        if verde is not None:
            (d / "equivalencia_local.txt").write_text(verde, encoding="utf-8")


# factores de K respecto de MIROVA: distintos por volcán para que la mediana de d′ sea negativa en los dos
F_LASCAR = (0.30, 0.35, 0.40, 0.60, 0.70)
F_VILLA = (0.32, 0.38, 0.62, 0.68, 0.75)
M_ALERTA = (2.0, 3.0, 1.5, 4.0, 2.5)


def base(p_de=None, negs_T="gana", negs_O="gana", extra=None, pcc_pdef=None, gemelo_negs=False, p_de_T=None,
         noches_T=5, gemelo_mirova=False, relleno=0):
    """Población base. p_de(m, k) da el VRP de P a partir del de MIROVA y del de K (por defecto, el de MIROVA);
    p_de_T lo reemplaza sólo en la ventana T. noches_T: noches con alertas en T. gemelo_mirova: el gemelo de K da la
    magnitud de MIROVA en las alertas (publica lo mismo que K). relleno: negativos que nadie publica, de más."""
    p_def = p_de or (lambda m, k: m)
    pb = Pob()
    for v_ in ("T", "O"):
        mes = "2026-04" if v_ == "T" else "2026-07"
        p_de = (p_de_T or p_def) if v_ == "T" else p_def
        for n in range(noches_T if v_ == "T" else 5):
            dia = f"{mes}-{10 + n:02d}"
            for vol, F in (("Lascar", F_LASCAR), ("Villarrica", F_VILLA)):
                m = M_ALERTA[n]
                k = round(m * F[n], 3)
                pb.pasada(vol, f"{dia} 06:{10 + 5 * n:02d}", "pos", K=k, P=round(p_de(m, k), 3), mirova_vrp=m,
                          gemelo=m if gemelo_mirova else "=K")
        modo = negs_T if v_ == "T" else negs_O
        for n in range(6):
            dia = f"{mes}-{20 + n:02d}"
            vol = ("Lascar", "Villarrica", "Tupungatito")[n % 3]
            if modo == "gana" or (modo == "bloquea" and n >= 4):   # K publica y P no: el error es de K
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
            elif modo in ("pierde", "bloquea"):                    # P publica y K no: el error es de P
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=0.2)
            elif modo == "gana_misma_noche":   # 6 bloques en 2 noches x 3 volcanes: el bloque lleva el volcán
                pb.pasada(vol, f"{mes}-{20 + n // 3:02d} 05:{n:02d}", "neg_limpio", K=0.2, P=None)
            else:                     # ninguno publica: no hay bloque
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=None)
        for n in range(6):            # negativos que nadie publica: sustrato del nulo del contador
            pb.pasada("Lascar", f"{mes}-0{1 + n} 04:00", "neg_limpio", K=None, P=None)
    # O: protegida de Cordón Caulle que P publica y P-def no (control positivo de la ROI), decidida por la escena: el
    # contraste del cráter (0,05) queda entre el umbral de P (0,04) y el de P-def (0,06)
    # (celda en el pase 2, zona 2; el pase 1 y la zona 1 tienen umbral 0,10: si el analizador mira otro pase u otra zona,
    # ningún brazo alerta y la marca desaparece)
    pb.pasada("PuyehueCordonCaulle", "2026-07-28 06:30", "pos", K=1.2, P=3.0,
              Pdef=3.0 if pcc_pdef == "publica" else None, mirova_vrp=3.0,
              dP=diag(c=0.05, u=0.04, u1=0.10, pase=2, u_otro_pase=0.10),
              dPdef=diag(c=0.05, u=0.06, sd=0.012, u1=0.10, pase=2, u_otro_pase=0.10),
              dO=diag(c=0.05, u=0.04, u1=0.10, pase=2, u_otro_pase=0.10), z=35.0)
    # O: alerta baja de Láscar que P-def no publica con el cráter muy sobre los dos umbrales (no la decide la escena)
    pb.pasada("Lascar", "2026-07-29 06:30", "pos", K=0.3, P=0.6, Pdef=None, mirova_vrp=0.6,
              dP=diag(c=0.2, u=0.04), dPdef=diag(c=0.2, u=0.06, sd=0.012))
    # O: alerta baja de Villarrica que P-def no publica porque cambió el CRÁTER (0,03 contra 0,05) con el mismo umbral
    pb.pasada("Villarrica", "2026-07-29 06:40", "pos", K=0.25, P=0.5, Pdef=None, mirova_vrp=0.5,
              dP=diag(c=0.05, u=0.04), dPdef=diag(c=0.03, u=0.04))
    # O: alerta baja de Tupungatito que P-def no publica; el NTI de la celda queda entre los dos umbrales pero el ETI
    # (0,01) queda bajo los dos: el .m exige los dos tests, así que el cambio de umbral NO cambia su alerta
    pb.pasada("Tupungatito", "2026-07-29 06:50", "pos", K=0.2, P=0.4, Pdef=None, mirova_vrp=0.4,
              dP=diag(c=0.05, c_eti=0.01, u=0.04), dPdef=diag(c=0.05, c_eti=0.01, u=0.06))
    # O: negativo lejano que P detecta a 11 km: P no lo publica (far), P-sinfiltro sí; P-def sin diagnóstico válido
    pb.pasada("Lascar", "2026-07-30 05:00", "neg_limpio", K=None, P=0.4, far=True, dPdef={"roto": True})
    if gemelo_negs:
        for n in range(6):
            pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 05:00", "neg_limpio", K=None, P=None,
                      gemelo=0.2)
    for n in range(relleno):
        pb.pasada("Villarrica", f"2026-{8 + n // 28:02d}-{1 + n % 28:02d} 04:00", "neg_limpio", K=None, P=None)
    if extra:
        extra(pb)
    return pb


def esc_sombra(p1=False, negs="gana", prot_ocr=False, sin_prot=False, mezcla=False, sin_reg=False, sha_real=False,
               sha_rara=False, temprana=False, reproc=False, vol_fuera=False, z_perdida=20.0,
               sha_todas=None, cc_def_sha=None, sensor_ocr=SENSOR,
               cc_def_hora="2026-11-04 06:30", sens=True, sens_fechas=None, cc_viejo=False, villa_fechas=None,
               nueve=None):
    """Sombra: sólo K y P (record del perfil sombra), desde el 2026-11-03. S173 (VPR939-03): mezcla agrega tres pasadas
    de Cordón Caulle, una con la ROI def y sha de antes del cambio (P pierde la protegida que K publica) y dos con sens
    (z 30 y 35); sin_reg quita el régimen del record de P de la primera protegida de Láscar; sha_real usa shas del repo
    y pone las tres primeras noches de protegidas con el sha anterior al merge; sha_rara da a un negativo un sha que no
    existe en el repo.
    S174 (VPR945): villa_dia0 es el primer día de los 6 negativos de Villarrica que cierran la sombra (por omisión del 10
    al 15 de diciembre, más de 4 semanas desde el 4 de noviembre; "2026-11-20" la deja en 21 días; desde R3, "2026-11-19"); sin_reg "roi" o "sha"
    quita sólo una de las dos marcas; temprana agrega dos pasadas de octubre que la lectura con B4 no lee (Cordón Caulle
    def y una de Láscar fuera del gránulo); reproc, un negativo del 1 de noviembre con el sha posterior al corte (una noche
    vieja reprocesada); vol_fuera, dos protegidas de un volcán fuera del mapa de ROI; z_perdida, el cenit de la protegida
    que pierde P con p1; sha_todas, un mismo sha para todas las pasadas.
    S174 (VPR945-R2): todas las pasadas llevan shas reales (sha_real sólo pone las tres primeras noches de protegidas con
    el sha anterior al merge); los negativos de Villarrica que cierran la sombra van a las 06:00 (villa_hora), así los días
    del reloj son enteros y el borde de 28,0 se puede tocar; n_villa es cuántos son (cuántas noches suman); reproc es la
    hora de una pasada de Villarrica con el sha posterior al merge; doble_noche suma un negativo de Villarrica la noche del
    primer negativo de Láscar (una pasada más, ninguna noche más); cc_def_sha, el sha de la pasada def observada de Cordón
    Caulle en la mezcla, y cc_def_hora su hora.
    S174 (VPR945-R3): con B4 cada volcán cuya ROI cambió (Cordón Caulle y Tupungatito) pide sus propias noches, así que
    sens agrega negativos sens de los dos (nadie publica) a las 05:30 y 05:40 en cada fecha de las pasadas anteriores
    desde el 7 de noviembre (no suma noches, no corre la primera ni la última pasada); sens_fechas {volcán: fechas} las
    reemplaza; cc_viejo deja a Cordón Caulle con sens sólo la primera fecha y las demás con la ROI def y el sha anterior
    al merge; villa_fechas reemplaza las fechas de los negativos de Villarrica. Los negativos de Villarrica pasan a 7
    (del 9 al 15 de diciembre: la misma última pasada) para que la segunda mitad del lapso tenga sus 7 noches.
    S174 (VPR945-R4, quinta vuelta): con la ventana fija la sombra base tiene que poner sus noches en las 4 semanas de la
    ventana. Los negativos de Villarrica son ahora 14, del 17 al 30 de noviembre (VILLA_FECHAS, a las 06:00), y el relleno
    sens va en cada fecha desde el 5 de noviembre (5 noches en la primera semana de las dos ventanas). Con SHA_CORTE_PRUEBA
    (semanas desde el 3, el 10, el 17 y el 24 de noviembre) el conjunto tiene 6, 5, 7 y 7 noches y Cordón Caulle y
    Tupungatito 5, 5, 7 y 7. villa_dia0, n_villa, villa_hora y doble_noche se retiraron (los escenarios que movían la
    última pasada para tocar el reloj usan ahora --ahora).
    S174 (VPR945-R5-03, sexta vuelta): cada volcán de ROI igual a B0 pide 14 noches en la ventana, así que nueve (por
    omisión, lo mismo que sens) agrega a cada uno de los nueve volcanes sin cambio con B4 un negativo que nadie publica a
    las 05:1k en cada fecha de las pasadas anteriores desde el 5 de noviembre en que ese volcán no tenga pasada (no suma
    noches al conjunto ni bloques a P2: nadie publica). Con la sombra base son 24 fechas: 186 pasadas (24 en cada uno de
    los 7 que no estaban, 13 en Láscar y 5 en Villarrica)."""
    pb = Pob()
    sha0, sha4 = SHA_REAL_B0, SHA_REAL_B4
    for n in range(0 if sin_prot else 6):
        dia = f"2026-11-{4 + n:02d}"
        for vol in ("Lascar", "Villarrica"):
            perder = p1 and n == 0 and vol == "Lascar"
            quitar = sin_reg and n == 0 and vol == "Lascar"
            pb.pasada(vol, f"{dia} 06:00", "pos", K=1.0, P=None if perder else 2.0, mirova_vrp=2.0,
                      sha=sha0 if (sha_real and n < 3) else sha4, z=z_perdida if perder else 20.0,
                      regimen={"roi": "sin_roi", "sha": "sin_sha"}.get(sin_reg, False) if quitar else True)
    if mezcla:
        pb.pasada("PuyehueCordonCaulle", cc_def_hora, "pos", K=1.5, P=None, mirova_vrp=2.0, roi="def",
                  sha=cc_def_sha or sha0, z=25.0)
        pb.pasada("PuyehueCordonCaulle", "2026-11-06 06:30", "pos", K=1.5, P=2.0, mirova_vrp=2.0, roi="sens",
                  sha=sha4, z=30.0)
        pb.pasada("PuyehueCordonCaulle", "2026-11-07 06:30", "pos", K=1.5, P=2.0, mirova_vrp=2.0, roi="sens",
                  sha=sha4, z=35.0)
        # S174 (VPR945-07, MY16): una pasada def fuera del gránulo no es observada y no entra al régimen ni a «otra ROI»
        pb.pasada("PuyehueCordonCaulle", "2026-11-05 06:30", "pos", K=None, P=None, mirova_vrp=2.0, roi="def",
                  sha=sha0, estado="volcan_fuera_del_granulo")
    if vol_fuera:   # S174 (VPR945-02): el nombre no coincide con ninguna clave de roi_por_volcan
        for n in range(2):
            pb.pasada("Nevados de Chillan", f"2026-11-{8 + n:02d} 06:20", "pos", K=1.0, P=2.0, mirova_vrp=2.0)
    if temprana:    # S174 (VPR945-01): dos pasadas de octubre que esta lectura no lee (otra ROI, no observada)
        pb.pasada("PuyehueCordonCaulle", "2026-10-01 05:00", "neg_limpio", K=None, P=None, roi="def", sha=sha4)
        pb.pasada("Lascar", "2026-10-02 05:00", "neg_limpio", K=None, P=None, estado="volcan_fuera_del_granulo")
    if reproc:      # S174 (VPR945-01, R2-03): noche vieja reprocesada con el código posterior al corte
        pb.pasada("Villarrica", reproc, "neg_limpio", K=None, P=None, sha=sha4)
    if prot_ocr:   # protegida sólo del OCR que K publica y P no: P1 en tabla más OCR, no con la tabla sola
        hora = "2026-11-11 06:30" if sensor_ocr == SENSOR else "2026-10-08 06:30"   # E80: Suomi NPP antes del 9-oct
        pb.pasada("Villarrica", hora, "pos", K=1.0, P=None, mirova_vrp=2.0, tabla=False, sensor=sensor_ocr)
    for n in range(6):
        dia = f"2026-11-{12 + n:02d}"
        if negs == "gana":
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=0.2, P=None,
                      sha="e" * 40 if (sha_rara and n == 0) else sha4)
        elif negs == "pierde" or (negs == "bloquea" and n < 4):
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=None, P=0.2)
        elif negs == "bloquea":
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
        else:
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=None, P=None)
    for f in villa_fechas or VILLA_FECHAS:
        pb.pasada("Villarrica", f"{f} 06:00", "neg_limpio", K=None, P=None)
    fechas = sorted({o["hora_utc"][:10] for o in pb.objs if o["hora_utc"][:10] >= "2026-11-05"})
    if sens if nueve is None else nueve:   # S174 (VPR945-R5-03): los nueve sin cambio, con sus 14 noches o más
        for k, vol in enumerate(SIN_CAMBIO_B4):
            ya = {o["hora_utc"][:10] for o in pb.objs if o["volcan"] == vol}
            for f in fechas:
                if f not in ya:
                    pb.pasada(vol, f"{f} 05:{10 + k}", "neg_limpio", K=None, P=None, sha=sha4)
    if sens:   # S174 (VPR945-R3-01): las pasadas de los volcanes que B4 cambia (R4: desde el 5 de noviembre)
        for k, vol in enumerate(CAMBIAN_B4):
            for n, f in enumerate((sens_fechas or {}).get(vol, fechas)):
                viejo = cc_viejo and vol == "PuyehueCordonCaulle" and n > 0
                pb.pasada(vol, f"{f} 05:{30 + 10 * k}", "neg_limpio", K=None, P=None, roi="def" if viejo else "sens",
                          sha=sha0 if viejo else sha4)
    if sha_todas:
        for r in pb.res:
            reg = r["brazos"]["P"]["record"].get("regimen")
            if reg and reg.get("codigo_sha"):
                reg["codigo_sha"] = sha_todas
    return pb


def esc_once(offs=OFFS_4SEM, offs_vol=None, brazo="B4", extra=None):
    """S174 (VPR945-R3, control positivo; R4, quinta vuelta): los 11 volcanes del mapa con una pasada por noche en los
    días `offs` desde el 5 de noviembre (offs_vol {volcán: días} los reemplaza en un volcán), a las 05:00 + 5 min por
    volcán (siempre después de las 03:23 del merge de #939, así el día d cae en la semana d // 7), con la ROI que
    `brazo` espera y el sha del merge de #939. Láscar y Villarrica traen 6 protegidas en sus primeras noches y Láscar 6
    negativos que K publica y P no en las siguientes (P2 GANA); el resto, negativos que nadie publica. extra(pb, d0)
    agrega pasadas. Por omisión, 5 noches en cada una de las 4 semanas: con el lector correcto da CUMPLE."""
    pb = Pob()
    d0 = datetime.date(2026, 11, 5)
    for k, vol in enumerate(VOLCANES_MAPA):
        roi = "sens" if brazo == "B4" and vol in CAMBIAN_B4 else "def"
        for n, off in enumerate((offs_vol or {}).get(vol, offs)):
            hora = f"{d0 + datetime.timedelta(days=off)} 05:{5 * k:02d}"
            if vol in ("Lascar", "Villarrica") and n < 6:
                pb.pasada(vol, hora, "pos", K=1.0, P=2.0, mirova_vrp=2.0, roi=roi)
            elif vol == "Lascar" and n < 12:
                pb.pasada(vol, hora, "neg_limpio", K=0.2, P=None, roi=roi)
            else:
                pb.pasada(vol, hora, "neg_limpio", K=None, P=None, roi=roi)
    if extra:
        extra(pb, d0)
    return pb


def _r404_cc_semana4_no_leida(pb, d0):
    """R4-04 (MW10 del verificador): Cordón Caulle trae en la semana 4 sólo pasadas que no se leen, en noches distintas
    de las de los otros volcanes: 3 fuera del gránulo (días 23 a 25) y 2 diurnas (SIN DATO, días 26 y 27)."""
    for off, est, dflag in ((23, "volcan_fuera_del_granulo", 0), (24, "volcan_fuera_del_granulo", 0),
                            (25, "volcan_fuera_del_granulo", 0), (26, "ok", 1), (27, "ok", 1)):
        pb.pasada("PuyehueCordonCaulle", f"{d0 + datetime.timedelta(days=off)} 05:40", "neg_limpio", K=None, P=None,
                  roi="sens", estado=est, dayflag=dflag)


def _r403_protegida_futura(pb, d0):
    """R4-03: una protegida de Láscar con fecha posterior a «ahora» (día 27) que K publica y P pierde."""
    pb.pasada("Lascar", f"{d0 + datetime.timedelta(days=27)} 06:30", "pos", K=1.0, P=None, mirova_vrp=2.0, roi="def")


def _borde_7_dias(pb, d0):
    """Borde de semana: una pasada de Villarrica en el minuto exacto de inicio + 7 días (2026-11-12 03:23)."""
    pb.pasada("Villarrica", "2026-11-12 03:23", "neg_limpio", K=None, P=None, roi="def")


def _borde_fin(pb, d0):
    """Borde del fin (2026-12-03 03:23): Villarrica un minuto antes entra a la semana 4; Láscar en el minuto del fin queda
    fuera de ventana; una pasada def de Cordón Caulle con el sha de #939 después del fin no cierra la compuerta."""
    pb.pasada("Villarrica", "2026-12-03 03:22", "neg_limpio", K=None, P=None, roi="def")
    pb.pasada("Lascar", "2026-12-03 03:23", "neg_limpio", K=None, P=None, roi="def")
    pb.pasada("PuyehueCordonCaulle", "2026-12-05 05:00", "neg_limpio", K=None, P=None, roi="def")


# S174 (VPR945-R5, sexta vuelta; decisión de Nicolás del 2026-11-06, «Sí, sexta vuelta»)
SIN_CAMBIO_B4 = tuple(v for v in VOLCANES_MAPA if v not in CAMBIAN_B4)   # los nueve que B4 deja como B0


def _r502_noche_en_la_frontera(pb, d0):
    """R5-02: cada volcán suma una pasada el 2026-11-12 a las 03:0k, antes del borde de la semana 2 (03:23); la noche del
    12 tiene así pasadas a los dos lados del borde (la de las 05:xx va en la semana 2)."""
    for k, vol in enumerate(VOLCANES_MAPA):
        pb.pasada(vol, f"2026-11-12 03:{k:02d}", "neg_limpio", K=None, P=None,
                  roi="sens" if vol in CAMBIAN_B4 else "def")


def _ahora_es_utc(lineas):
    """R5-04 (MX11 del verificador): sin --ahora, «ahora» es el reloj UTC; el escenario corre con TZ en UTC+12, así que
    leer el reloj local lo correría 12 horas. Tolerancia de 30 minutos (lo que tarda una corrida, con holgura)."""
    pref = "== ventana fija de la sombra"
    lin = next((x for x in lineas if x.startswith(pref)), "")
    if " ahora " not in lin:
        return [f"falta la línea «{pref}» con «ahora»"]
    t = datetime.datetime.strptime(lin.split(" ahora ", 1)[1][:19], "%Y-%m-%d %H:%M:%S")
    utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    dif = abs((t - utc).total_seconds())
    return [] if dif <= 1800 else [f"«ahora» impreso {t} difiere {dif / 3600:.1f} h del reloj UTC {utc:%Y-%m-%d %H:%M:%S}"]


# S173 (VPR939-03): toda lectura de la sombra declara la ROI que lee; S174 (VPR945-R2-02) y el commit desde el que lee
ROI_B4 = ["--roi-brazo", "B4"]
B4 = ROI_B4 + ["--sha-desde", SHA_CORTE_PRUEBA]
B0 = ["--roi-brazo", "B0", "--sha-desde", SHA_CORTE_PRUEBA]   # S174 (R3-02): ningún volcán cambia de ROI


def _p1_en_O(pb):
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Lascar" and o["hora_utc"].startswith("2026-07-12"))
    for b in ("P", "Pdef", "O"):
        pb.res[j]["paquete"][b] = salida_paquete(None, "Lascar")


def _prot_nadie(pb):
    pb.pasada("Villarrica", "2026-07-31 06:00", "pos", K=None, P=None, mirova_vrp=2.0)


def _p_distinto_de_o(banda):
    def f(pb):
        j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Villarrica"
                 and o["hora_utc"].startswith("2026-07-11"))
        pb.res[j]["paquete"]["O"]["vrp_mw"] += 1e-5   # sobre la tolerancia de 1e-6 MW, bajo cualquier redondeo
        pb.res[j]["banda_triangulacion"] = banda
    return f


def _bajas_T(pb):
    """6 alertas bajo 1 MW en T que P publica y K no: P2 se decide por las bajas, no por los negativos."""
    for n in range(6):
        pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-05-{10 + n:02d} 06:00", "pos", K=None, P=0.3,
                  mirova_vrp=0.4)


def _prot_solo_ocr(pb):
    """Protegida sólo del OCR en O que K publica y P no: P1 en tabla más OCR, no con la tabla sola."""
    pb.pasada("Villarrica", "2026-07-31 06:40", "pos", K=0.9, P=None, mirova_vrp=2.0, tabla=False)


def _o_otra_celda(pb):
    """O alerta la celda vecina con el mismo VRP: la máscara difiere aunque el VRP no."""
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Villarrica"
             and o["hora_utc"].startswith("2026-07-11"))
    px = pb.res[j]["paquete"]["O"]["pixeles"][0]
    pb.res[j]["paquete"]["O"]["pixeles"] = [[px[0], px[1] + 1] + px[2:]]
    # y la diferencia la explica la escena: la celda (0,05) queda entre el umbral de P (0,04) y el de O (0,06)
    pb.res[j]["paquete"]["P"]["diag"] = diag(c=0.05, u=0.04)
    pb.res[j]["paquete"]["O"]["diag"] = diag(c=0.05, u=0.06)


def _k_distinto_uno(pb):
    """Una sola pasada no protegida con K distinto de producción (§7: «en todas las pasadas ok»)."""
    j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
    pb.objs[j]["pub_prod"] = False


def _k_distinto_dos(pb):
    """Dos pasadas no protegidas con K distinto de producción: más del 1 % de 110 (L18)."""
    js = [i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"]][:2]
    for j in js:
        pb.objs[j]["pub_prod"] = False


def _k_distinto_y_p_distinto_de_o(pb):
    """La pasada con K distinto (negativo de Láscar del 2026-04-20) tiene además una celda que O alerta y P no."""
    _k_distinto_uno(pb)
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Lascar" and o["hora_utc"] == "2026-04-20 05:00")
    pb.res[j]["paquete"]["O"] = salida_paquete(0.1, "Lascar")


def _sombra_k_distinto(**kw):
    """Una pasada con K distinto de producción en la sombra. S175: el tamaño lo da esc_sombra (kw), no un relleno, porque
    las pasadas posteriores al fin de la ventana fija ya no se leen."""
    def f():
        pb = esc_sombra(**kw)
        j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
        pb.objs[j]["pub_prod"] = False
        return pb
    return f


def _protegida_ocr_k_distinto(pb):
    """Protegida sólo del OCR (O) que K publica pero producción no: K distinto en una protegida."""
    pb.pasada("Villarrica", "2026-08-05 06:40", "pos", K=0.9, P=0.9, mirova_vrp=2.0, tabla=False, pub_prod=False)


def _k_en_el_tope(pb):
    """K de 45.000 MW con t_max 300 K publica; por 1,2 = 54.000 MW el tablero lo lleva a 0 (tope de 50.000 MW)."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=45000.0, P=None, k_tmax=300.0)


def _pc_vrp_distinto(pb):
    """K publica igual que producción pero su VRP difiere en 0,01 MW (más que 0,001)."""
    pb.objs[0]["pc_vrp"] = round(pb.objs[0]["pc_vrp"] + 0.01, 3)


def _placebo_publica_distinto(pb):
    """K de 9,0 MW con t_max 270 K publica; K x 1,2 = 10,8 MW cae en el filtro de cirro del tablero (>10 MW, <273 K)."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=9.0, P=None, k_tmax=270.0)


def _protegidas_que_k_no(pb):
    """12 protegidas en O que K no publica y P publica al doble de MIROVA: entran a la razón de §6.2 (L4 por D-48)."""
    for n in range(12):
        pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 06:00", "pos", K=None, P=4.0,
                  mirova_vrp=2.0)


def _un_error(protegida):
    def f(pb):
        j = next(i for i, o in enumerate(pb.objs) if o["protegida"] == protegida)
        pb.res[j]["estado"] = "error_K"
    return f


def _diurna(pb):
    pb.res[0]["dayflag"] = 1


def _prot_no_decide(pb):
    """Protegida que no decide (flag `decide` falso): K la publica y P no, y no es veto."""
    pb.pasada("Villarrica", "2026-07-31 06:20", "pos", K=0.9, P=None, mirova_vrp=2.0, decide=False)


SIN_G = [{"volcan": "Lascar", "hora_utc": "2026-07-31 05:00", "protegida": False},
         {"volcan": "Villarrica", "hora_utc": "2026-07-31 05:10", "protegida": False}]


def _sin_lineas(*claves):
    return "\n".join(x for x in VERDE.splitlines() if not any(k in x for k in claves)) + "\n"


def _k_distinto(pb):
    for o in pb.objs[:2]:
        o["pub_prod"] = not o["pub_prod"]


def _errores(pb):
    for r in pb.res[:2]:
        r["estado"] = "error_K"


def _falta_o(pb):
    pb.res[0]["paquete"].pop("O")


def ganancia_uniforme():
    """P = K x g con g fija por ventana igual a 1 / mediana de los factores de K: razón ~1, comparador NEUTRO."""
    import statistics
    g = 1.0 / statistics.median(F_LASCAR + F_VILLA)
    return lambda m, k: k * g


def _noches_once(menos):
    """VPR953-03: la lista «volcán noches» de los once, en el orden en que la imprime el lector (alfabético), con 20
    noches (esc_once por omisión) salvo los de `menos`."""
    return ", ".join(f"{v} {menos.get(v, 20)}" for v in sorted(VOLCANES_MAPA))


# ---------------------------------------------------------------- §6 bis, brazos de posición
def px_cerca_lejos(volcan):
    """Un alertado débil (M13 1,0) en el cráter y uno más radiante (M13 2,0) 15 celdas al este (11,25 km): el cúmulo
    del más radiante y el pico quedan lejos; el más cercano, en la cumbre."""
    f, c = CRATER[volcan]
    return [[f, c, 2, 0.0, 1.0], [f, c + 15, 2, 0.0, 2.0]]


def px_linea(volcan):
    """El alertado más radiante en el cráter y 15 más débiles contiguos hacia el este: el centroide del cúmulo queda a
    7,5 celdas (5,6 km, fuera del radio de 5 km); el pico y el más cercano, en el cráter."""
    f, c = CRATER[volcan]
    return [[f, c, 2, 0.0, 2.0]] + [[f, c + k, 2, 0.0, 1.0] for k in range(1, 16)]


def px_llaima_centro(volcan):
    """E70: un alertado débil en el CENTRO de la grilla (a 6,4 km del cráter de Llaima) y uno más radiante 15 celdas al
    este del cráter. Medido desde el cráter, el más cercano es el del centro y queda lejos; medido desde el centro de la
    grilla quedaría a 0 km."""
    f, c = CRATER[volcan]
    return [[C, C, 2, 0.0, 1.0], [f, c + 15, 2, 0.0, 2.0]]


def _escena(volcan, dias, lab, px, mes="2026-05", hora="06:00", K=None, P=0.3, mirova_vrp=0.4, tabla=True):
    """Una pasada por día (cada una en su propio bloque noche-volcán) con los píxeles de la escena."""
    def f(pb):
        for d in dias:
            pb.pasada(volcan, f"{mes}-{d:02d} {hora}", lab, K=K, P=P, px=None if px is None else px(volcan),
                      mirova_vrp=mirova_vrp if lab == "pos" else None, tabla=tabla)
    return f


def _y(*fs):
    def f(pb):
        for g in fs:
            g(pb)
    return f


def _prot_cerca_lejos(pb):
    """E64: protegida de Láscar en O que K publica; sólo el brazo cercano la publica."""
    pb.pasada("Lascar", "2026-09-01 06:00", "pos", K=1.2, P=3.0, mirova_vrp=3.0, px=px_cerca_lejos("Lascar"))


def px_anillo(volcan):
    """Verificador de posición (W2, W3): borde de un cuadrado de 8 celdas de radio centrado en el cráter. Es 8-conexo y su
    centroide cae EN el cráter (summit para el radiante), pero todos sus píxeles quedan a 6 km o más (far para cercano y
    pico). El más radiante es una esquina."""
    f, c = CRATER[volcan]
    pts = set()
    for k in range(-8, 9):
        pts.update({(f - 8, c + k), (f + 8, c + k), (f + k, c - 8), (f + k, c + 8)})
    px = [[a, b, 2, 0.0, 1.0] for a, b in sorted(pts)]
    px[0][4] = 2.0
    return px


def _prot_ocr_anillo(pb):
    """E74 (W3): protegida de Láscar en O, sólo del OCR, que K y el radiante publican y cercano y pico pierden."""
    pb.pasada("Lascar", "2026-09-01 06:00", "pos", K=1.2, P=3.0, mirova_vrp=3.0, px=px_anillo("Lascar"), tabla=False)


def _n3(hora, tabla=False):
    """§6 ter (N-3): la protegida de E26 (Villarrica en O, K la publica y P no), de Suomi NPP a la hora dada."""
    def f(pb):
        pb.pasada("Villarrica", hora, "pos", K=0.9, P=None, mirova_vrp=2.0, tabla=tabla, sensor="VIIRS_SNPP_750")
    return f


SEIS = range(1, 7)
NEGS_CERCANO = _escena("Villarrica", range(11, 17), "neg_limpio", px_cerca_lejos, hora="05:00")


ESCENARIOS = {
    "E00": dict(pob=lambda: base(), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("== compuerta del veredicto", ["ABIERTA"]),
                       ("== §6.1 equivalencia: CUMPLE", []),
                       ("   S-1 al lado del veredicto", ["PuyehueCordonCaulle 2026-07-28 06:30"]),
                       ("== S-1 par (P, Pdef)", ["publicación distinta 4", "decididas por la escena 1",
                                                 "PuyehueCordonCaulle 2026-07-28 06:30", "c/u 1.25/1.25",
                                                 "Δsd nti1 mediana 0.0000 máx 0.0020", "(SIN DATO 1)"]),
                       ("== S-1 par (Pdef, O)", ["publicación distinta 4", "decididas por la escena 1",
                                                 "PuyehueCordonCaulle 2026-07-28 06:30", "(SIN DATO 1)"]),
                       ("== S-1 por pasada", ["filas"]),
                       ("== §6.2 ventana O, canal tabla", ["M comparador MEJORA (pares 14"]),
                       ("== P-sinfiltro contra P", ["neto 1"])],
                no_tiene=["== §6 censo: NO CUMPLE", "== §6 censo: INFORMAR"],
                no_contiene=[("== S-1 par (P, Pdef)", "Lascar 2026-07-29 06:30"),
                             ("== S-1 par (P, Pdef)", "Villarrica 2026-07-29 06:40"),
                             ("== S-1 par (P, Pdef)", "Tupungatito 2026-07-29 06:50")]),
    "E01": dict(pob=lambda: base(extra=_p1_en_O), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P1"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E02": dict(pob=lambda: base(extra=_prot_nadie), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("   protegidas que ni K ni P publican", ["Villarrica 2026-07-31 06:00"])],
                no_tiene=["== §6 censo: NO CUMPLE"]),
    "E03": dict(pob=lambda: base(negs_T="pierde"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P2"])],
                no_tiene=["== §6 censo: CUMPLE", "== §6 censo: INFORMAR"]),
    "E04": dict(pob=lambda: base(negs_O="pierde"), rc=0,
                tiene=[("== §6 censo: INFORMAR POR CANAL ANTES DE DECIDIR", [])],
                no_tiene=["== §6 censo: CUMPLE", "== §6 censo: NO CUMPLE"]),
    "E05": dict(pob=lambda: base(negs_T="nada"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P2", "SIN SUSTRATO"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    "E06": dict(pob=lambda: base(p_de=lambda m, k: 1.3 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E07": dict(pob=lambda: base(p_de=ganancia_uniforme()), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M comparador"])],
                no_tiene=["== §6 censo: CUMPLE"], no_contiene=[("== §6 censo: NO CUMPLE", "M razón")]),
    "E08": dict(pob=lambda: base(extra=_p_distinto_de_o(False)), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["Villarrica 2026-07-11"])],
                no_tiene=["== §6 censo:"]),
    "E09": dict(pob=lambda: base(extra=_p_distinto_de_o(True)), rc=0,
                tiene=[("== §6.1 equivalencia: CUMPLE", []),
                       ("   P distinto de O dentro de la banda de triangulación", ["Villarrica 2026-07-11"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E10": dict(pob=lambda: base(), verde=None, rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E11": dict(pob=lambda: base(), verde=VERDE.replace("TODAS COMO SE ESPERA", "1 FUERA DE LO ESPERADO"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E12": dict(pob=lambda: base(pcc_pdef="publica"), rc=3,
                tiene=[("== control positivo de la ROI", ["FALLA"]), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E13": dict(pob=lambda: base(gemelo_negs=True), rc=3,
                tiene=[("== control nulo K contra K gemelo", ["FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E14": dict(pob=lambda: base(extra=_k_distinto), rc=3,
                tiene=[("== control K = producción", ["FALLA"]), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E15": dict(pob=lambda: base(extra=_errores), rc=3,
                tiene=[("== cobertura: INSUFICIENTE", []), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E16": dict(pob=lambda: base(extra=_errores), args=["--leer-con-faltantes", "prueba sintética"], rc=5,
                tiene=[("== §6 censo: CUMPLE", ["LEÍDO CON FALTANTES"])]),
    "E17": dict(pob=lambda: base(extra=_falta_o), rc=3,
                tiene=[("   SIN DATO por motivo", ["falta_brazo"]), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6 censo:"]),
    "E18": dict(pob=lambda: esc_sombra(), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: CUMPLE", ["ventana 2026-11-03 00:00 a 2026-12-01 00:00 UTC, 28.0 de 28 días, "
                                                   "semanas 6, 5, 7, 7 (25), PuyehueCordonCaulle 5, 5, 7, 7 (24), "
                                                   "Tupungatito 5, 5, 7, 7 (24)"]),
                       # S174 (VPR945-R2-04): la hora del corte es la del committer (13:36), no la del autor (02:27)
                       ("== régimen de la sombra: brazo B4", [f"desde {SHA_CORTE_PRUEBA} (commit del 2026-11-02 13:36 UTC)",
                                                              "ventana desde 2026-11-03 00:00 UTC", "dentro 266",
                                                              "fuera de ventana (posteriores a 2026-12-01 00:00:00) 0 {}"]),
                       # S174 (VPR945-R4): la ventana fija, sus 4 semanas y «ahora» se imprimen siempre
                       ("== ventana fija de la sombra", ["inicio 2026-11-03 00:00 UTC, fin 2026-12-01 00:00 UTC",
                                                         "semanas fijas desde 11-03 00:00, 11-10 00:00, 11-17 00:00, 11-24 00:00",
                                                         "ahora 2026-12-10 00:00:00 UTC (--ahora)",
                                                         "se lee hasta 2026-12-01 00:00:00 UTC"]),
                       ("== duración de la sombra", ["primera 2026-11-04 06:00", "última 2026-11-30 06:00",
                                                     "28.0 de 28 (completos)", "por semana 6, 5, 7, 7 (25) (completas)",
                                                     "sin sus noches ninguno;", "con menos de 14 noches ninguno: COMPLETA"]),
                       # S174 (VPR945-R3-01, R4): las noches por semana de los 11 volcanes, también los de 0
                       ("== noches por semana y volcán", ["ROI distinta de B0 en ['PuyehueCordonCaulle', 'Tupungatito']",
                                                          "Chaiten 5, 5, 7, 7 (24) sin cambio, completas",
                                                          "Lascar 6, 5, 7, 7 (25) sin cambio, completas",
                                                          "Villarrica 6, 5, 7, 7 (25) sin cambio, completas",
                                                          "PuyehueCordonCaulle 5, 5, 7, 7 (24) decide, completas",
                                                          "Tupungatito 5, 5, 7, 7 (24) decide, completas"]),
                       # S174 (VPR945-R3-05): el rango horario se mide en cada lectura
                       ("   horas UTC de las pasadas leídas", ["de 05:00 a 06:00"])],
                no_tiene=["== §6.3 sombra: NO CUMPLE"]),
    "E19": dict(pob=lambda: esc_sombra(p1=True), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["P1"])], no_tiene=["== §6.3 sombra: CUMPLE"]),
    "E20": dict(pob=lambda: esc_sombra(negs="nada"), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: CUMPLE", ["SIN SUSTRATO"])]),
    "E21": dict(pob=lambda: esc_sombra(negs="pierde"), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["P2"])], no_tiene=["== §6.3 sombra: CUMPLE"]),
    "E24": dict(pob=lambda: base(negs_T="bloquea"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: P2 BLOQUEA"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E25": dict(pob=lambda: base(negs_T="nada", extra=_bajas_T), rc=0,
                tiene=[("== §6 censo: CUMPLE", [])], no_tiene=["== §6 censo: NO CUMPLE"]),
    "E26": dict(pob=lambda: base(extra=_prot_solo_ocr), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/todo: P1 1"]),
                       ("== §6.2 ventana O, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"])], no_tiene=["== §6 censo: CUMPLE"],
                no_contiene=[("== §6 censo: NO CUMPLE", "O/tabla: P1")]),
    "E27": dict(pob=lambda: base(extra=_o_otra_celda), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["Villarrica 2026-07-11", "decidida por la escena"])],
                no_tiene=["== §6 censo:"]),
    "E28": dict(pob=lambda: base(relleno=60, extra=_k_distinto_uno), rc=0,
                tiene=[("== control K = producción", ["distintas 1 de 109", "OK", "Lascar 2026-04-20"]),
                       ("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -5, bloques 5"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E50": dict(pob=lambda: base(relleno=61, extra=_k_distinto_dos), rc=3,
                tiene=[("== control K = producción", ["distintas 2 de 110", "FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E29": dict(pob=lambda: base(extra=_pc_vrp_distinto), rc=3,
                tiene=[("== control K = producción", ["FALLA"])], no_tiene=["== §6 censo:"]),
    "E30": dict(pob=lambda: base(extra=_placebo_publica_distinto), rc=0,
                tiene=[("== control placebo K×1,2 (publicación)", ["explicadas por los filtros de artefacto del tablero "
                                                                   "(t_max bajo 278.15 K) o su tope de 50000 MW 1", "Lascar 2026-07-31 05:30",
                                                                   "sin explicar 0", "OK"]),
                       ("== compuerta del veredicto", ["ABIERTA"]), ("== §6 censo: CUMPLE", [])]),
    "E31": dict(pob=lambda: base(extra=_protegidas_que_k_no), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/tabla: M razón 2.000"]),
                       ("   razón en protegidas que publican K y P", ["1.000"])],
                no_tiene=["== §6 censo: CUMPLE"], no_contiene=[("== §6 censo: NO CUMPLE", "T/tabla: M razón")]),
    "E53": dict(pob=lambda: base(p_de=lambda m, k: round(0.9 * m, 3)), rc=0,
                tiene=[("== §6 censo:", []), ("== §6.2 ventana T, canal tabla", ["M razón en protegidas 0.900"])],
                no_contiene=[("== §6 censo:", "M razón")]),
    "E54": dict(pob=lambda: base(p_de=lambda m, k: round(1.1 * m, 3)), rc=0,
                tiene=[("== §6 censo:", []), ("== §6.2 ventana T, canal tabla", ["M razón en protegidas 1.100"])],
                no_contiene=[("== §6 censo:", "M razón")]),
    "E55": dict(pob=lambda: base(relleno=60, extra=_k_distinto_y_p_distinto_de_o), rc=6,
                tiene=[("== control K = producción", ["distintas 1 de 109", "OK"]),
                       ("== §6.1 equivalencia: NO SE CUMPLE", ["Lascar 2026-04-20 05:00"])], no_tiene=["== §6 censo:"]),
    "E56": dict(pob=_sombra_k_distinto(sens=False), fase="sombra", rc=3, args=B4,
                tiene=[("== control K = producción", ["distintas 1 de 32", "FALLA"])],
                no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "E57": dict(pob=_sombra_k_distinto(), fase="sombra", rc=0, args=B4,
                tiene=[("== control K = producción", ["distintas 1 de 266", "OK", "Lascar 2026-11-12 05:00"]),
                       ("== §6.3 sombra: CUMPLE", [])]),
    "E58": dict(pob=lambda: base(relleno=62, extra=_protegida_ocr_k_distinto), rc=3,
                tiene=[("== control K = producción", ["distintas 1 de 112", "Villarrica 2026-08-05 06:40", "FALLA"])],
                no_tiene=["== §6 censo:"]),
    "E59": dict(pob=lambda: base(extra=_k_en_el_tope), rc=0,
                tiene=[("== control placebo K×1,2 (publicación)", ["tope de 50000 MW 1", "Lascar 2026-07-31 05:30",
                                                                   "sin explicar 0", "OK"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E60": dict(pob=lambda: base(), verde=VERDE.replace("mutación fondo_anillo ", "mutación otra_pieza   "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["por nombre: 5 de 6"])], no_tiene=["== §6 censo:"]),
    "E52": dict(pob=lambda: base(relleno=61, extra=_pc_vrp_distinto), rc=3,
                tiene=[("== control K = producción", ["distintas 1 de 110", "FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E51": dict(pob=lambda: base(), verde=_sin_lineas("recorte "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["atrapadas 5", "mínimo 6"])], no_tiene=["== §6 censo:"]),
    "E32": dict(pob=lambda: base(p_de=lambda m, k: 0.85 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón 0.850"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E33": dict(pob=lambda: base(p_de=lambda m, k: 1.15 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón 1.150"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E34": dict(pob=lambda: base(), sin_granulo=SIN_G, rc=3,
                tiene=[("   pasadas sin gránulo (del generador): 2", []), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6 censo:"]),
    "E35": dict(pob=lambda: base(relleno=10, extra=_un_error(False)), rc=0,
                tiene=[("== cobertura: SUFICIENTE", []), ("== §6 censo: CUMPLE", [])]),
    "E36": dict(pob=lambda: base(relleno=10, extra=_un_error(True)), rc=3,
                tiene=[("== cobertura: INSUFICIENTE", [])], no_tiene=["== §6 censo:"]),
    "E37": dict(pob=lambda: base(extra=_diurna), rc=3,
                tiene=[("   SIN DATO por motivo", ["diurna"]), ("== cobertura: INSUFICIENTE", [])]),
    "E38": dict(pob=lambda: base(), verde=_sin_lineas("ocho_vecinos", "recorte "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["atrapadas 4"])], no_tiene=["== §6 censo:"]),
    "E39": dict(pob=lambda: base(), verde=_sin_lineas("control_que_se_cae"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["control caído False"])], no_tiene=["== §6 censo:"]),
    "E40": dict(pob=lambda: base(), verde=VERDE.replace("VERDE: E1 1020 casos, E3 10 recortes",
                                                       "ROJA: el módulo pipeline.mirova_v750_codigo no existe"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E41": dict(pob=lambda: base(), verde=VERDE.replace("E1 1020 casos", "E1 100 casos"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E42": dict(pob=lambda: base(), args=["--solo-controles"], rc=0,
                tiene=[("== sin veredicto: --solo-controles", [])], no_tiene=["== §6 censo:", "== §6.1"]),
    "E43": dict(pob=lambda: base(negs_T="gana_misma_noche"), rc=0,
                tiene=[("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E44": dict(pob=lambda: base(noches_T=2), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: M comparador SIN SUSTRATO"])]),
    "E45": dict(pob=lambda: base(extra=_prot_no_decide), rc=0, tiene=[("== §6 censo: CUMPLE", [])]),
    "E46": dict(pob=lambda: base(gemelo_mirova=True), rc=3,
                tiene=[("== control nulo K contra K gemelo", ["FALLA"])], no_tiene=["== §6 censo:"]),
    "E47": dict(pob=lambda: esc_sombra(prot_ocr=True), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["todo: P1 1"])],
                no_contiene=[("== §6.3 sombra: NO CUMPLE", "tabla: P1")]),
    "E48": dict(pob=lambda: base(p_de_T=lambda m, k: 1.3 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: M razón 1.300"])],
                no_contiene=[("== §6 censo: NO CUMPLE", "O/tabla: M razón")]),
    # S174 (VPR945-R2-01): sin protegidas la sombra base tiene 12 noches; con 8 negativos de Villarrica llega a 14
    # S174 (VPR945-R3-02): con 7 noches por mitad del lapso, los negativos de Villarrica siguen a los de Láscar del 18 de
    # noviembre al 10 de diciembre (29 noches seguidas, 28 días)
    "E49": dict(pob=lambda: esc_sombra(sin_prot=True, villa_fechas=[
                    str(datetime.date(2026, 11, 3) + datetime.timedelta(days=n)) for n in range(28)]), fase="sombra",
                rc=0, args=B4, tiene=[("== §6.3 sombra: CUMPLE", ["SIN PROTEGIDAS"])]),
    "E23": dict(pob=lambda: esc_sombra(negs="bloquea"), fase="sombra", rc=0, args=B4,
                tiene=[("== §6.3 sombra: CUMPLE", ["BLOQUEA"])]),
    # S173, VPR939-03: la sombra no mezcla la ROI B0 con la B4 (A104)
    # S174 (R2): con --sha-desde presente, para que lo que cierre sea la falta de brazo y no la del corte (MR2)
    "ER1": dict(pob=lambda: esc_sombra(mezcla=True), fase="sombra", rc=3, args=["--sha-desde", SHA_REAL_B4],
                tiene=[("== régimen de la sombra: SIN --roi-brazo", ["compuerta cerrada", "PuyehueCordonCaulle"])],
                no_tiene=["== §6.3 sombra:", "== régimen de la sombra: brazo"]),
    # S174 (VPR945-R2-02): con el corte viejo, la pasada def de Cordón Caulle (sha 636b3426e) desciende del corte: la
    # ROI de ese volcán cambió dentro de lo que se lee y la compuerta se cierra (antes daba CUMPLE con el reloj global)
    "ER2": dict(pob=lambda: esc_sombra(mezcla=True), fase="sombra", rc=3, args=B4,
                tiene=[("== régimen de la sombra: brazo B4", ["dentro 268", "otra ROI 1", "PuyehueCordonCaulle"]),
                       ("   protegidas fuera de esta lectura", ["PuyehueCordonCaulle 2026-11-04 06:30 (otra ROI)"]),
                       ("== régimen de la sombra: el corte 5b13bfed8 no aísla el brazo B4",
                        ["['PuyehueCordonCaulle']", "compuerta cerrada"])],
                no_tiene=["== §6.3 sombra:", "== cobertura:", "== duración de la sombra"]),
    # S174 (R3): sin las pasadas sens de relleno, que con B0 serían «otra ROI» (sólo cuenta las dos sens de la mezcla)
    "ER3": dict(pob=lambda: esc_sombra(mezcla=True, sens=False), fase="sombra", rc=3,
                args=["--roi-brazo", "B0", "--sha-desde", SHA_CORTE_PRUEBA],
                tiene=[("== régimen de la sombra: brazo B0", ["dentro 33", "otra ROI 2"]),
                       ("== régimen de la sombra: el corte 5b13bfed8 no aísla el brazo B0",
                        ["['PuyehueCordonCaulle']", "compuerta cerrada"])],
                no_tiene=["== §6.3 sombra:"]),
    "ER4": dict(pob=lambda: esc_sombra(sin_reg=True), fase="sombra", rc=3, args=B4,
                tiene=[("   SIN DATO por motivo:", ["sin_regimen"]), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6.3 sombra:"]),
    "ER5": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True), fase="sombra", rc=0,
                args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                tiene=[("== régimen de la sombra: brazo B4", ["dentro 262", "otra ROI 1", "anteriores al corte 6",
                                                               f"desde {SHA_REAL_B4} (commit del 2026-11-05 03:23 UTC)",
                                                               "ventana desde 2026-11-05 03:23 UTC",
                                                               "anteriores a la hora del corte 0"]),
                       ("== ventana fija de la sombra", ["inicio 2026-11-05 03:23 UTC, fin 2026-12-03 03:23 UTC",
                                                         "11-05 03:23, 11-12 03:23, 11-19 03:23, 11-26 03:23"]),
                       ("   protegidas fuera de esta lectura", ["Lascar 2026-11-04 06:00 (anterior al corte)",
                                                               "PuyehueCordonCaulle 2026-11-04 06:30 (otra ROI)"]),
                       ("== duración de la sombra", ["primera 2026-11-05 05:10", "28.0 de 28 (completos)",
                                                     "por semana 5, 7, 7, 5 (24) (completas)", ": COMPLETA"]),
                       ("== §6.3 sombra: CUMPLE", []),
                       ("   sobre 30°", ["observadas 2", "protegidas 2"]),
                       ("   bajo 30°", ["observadas 260", "protegidas 6"])],
                no_tiene=["== §6.3 sombra: NO CUMPLE", "== régimen de la sombra: el corte"]),
    # S174 (R3): sin las pasadas sens de relleno, para que 1 SIN DATO siga pasando el 2 % de la cobertura (con ellas, 1 de 53)
    "ER6": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True, sha_rara=True, sens=False), fase="sombra", rc=3,
                args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                tiene=[("   SIN DATO por motivo:", ["sha_desconocido"]),
                       ("== régimen de la sombra: brazo B4", ["dentro 27"])],
                no_tiene=["== §6.3 sombra:"]),
    # S174, VPR945 (verificador limpio del PR #945)
    "ER8": dict(pob=lambda: esc_sombra(sin_reg="roi"), fase="sombra", rc=3, args=B4,
                tiene=[("   SIN DATO por motivo:", ["sin_regimen"]), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6.3 sombra:"]),
    "ER9": dict(pob=lambda: esc_sombra(sin_reg="sha"), fase="sombra", rc=3, args=B4,
                tiene=[("   SIN DATO por motivo:", ["sin_regimen"]), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6.3 sombra:"]),
    "ER10": dict(pob=lambda: esc_sombra(vol_fuera=True), fase="sombra", rc=3, args=B4,
                 tiene=[("   SIN DATO por motivo:", ["volcan_sin_roi"]), ("== cobertura: INSUFICIENTE", []),
                        ("== régimen de la sombra: brazo B4", ["otra ROI 0"])],
                 no_tiene=["== §6.3 sombra:"]),
    "ER11": dict(pob=lambda: esc_sombra(sha_real=True, sha_todas=SHA_REAL_B0), fase="sombra", rc=3,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== cobertura: SIN PASADAS OBSERVADAS", ["observadas 0", "compuerta cerrada"]),
                        ("== sin veredicto:", ["ninguna pasada observada"])],
                 no_tiene=["== cobertura: SUFICIENTE", "== control nulo", "== §6.3 sombra:"]),
    # S174 (VPR945-R2-03): de las dos pasadas de octubre, la def de Cordón Caulle sale por otra ROI (antes del
    # inicio de la sombra no cierra la compuerta) y la no observada por la ventana
    "ER12": dict(pob=lambda: esc_sombra(temprana=True), fase="sombra", rc=4, args=B4 + ["--ahora", "2026-11-24 00:00"],
                 tiene=[("== régimen de la sombra: brazo B4", ["otra ROI 1", "anteriores al inicio de la sombra 1", "dentro 189",
                                                               "fuera de ventana (posteriores a 2026-11-24 00:00:00) 77"]),
                        ("== duración de la sombra", ["primera 2026-11-04 06:00",
                                                      "21.0 de 28 (faltan: ahora es anterior al fin)",
                                                      "por semana 6, 5, 7, 0 (18) (faltan)", ": INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["21.0 de 28 días", "(ahora es anterior al fin)", "P1 = 0"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # S174 (VPR945-R2-03): una noche del 2 de noviembre reprocesada con el código nuevo no entra (la sombra empieza el 3)
    # aunque su sha descienda del corte; el reloj, las noches y la lectura no la ven
    "ER13": dict(pob=lambda: esc_sombra(reproc="2026-11-02 20:00"), fase="sombra", rc=4,
                 args=B4 + ["--ahora", "2026-11-29 00:00"],
                 tiene=[("== régimen de la sombra: brazo B4", ["anteriores al inicio de la sombra 1", "dentro 244",
                                                               "fuera de ventana (posteriores a 2026-11-29 00:00:00) 22"]),
                        ("== duración de la sombra", ["primera 2026-11-04 06:00", "26.0 de 28 (faltan",
                                                      "por semana 6, 5, 7, 5 (23)"]),
                        ("== §6.3 sombra: PROVISORIO", ["26.0 de 28 días"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "ER15": dict(pob=lambda: esc_sombra(), fase="sombra", rc=3, args=ROI_B4 + ["--sha-desde", "HEAD"],
                 tiene=[("== régimen de la sombra: --sha-desde HEAD", ["no es el sha", "compuerta cerrada"])],
                 no_tiene=["== §6.3 sombra:", "== cobertura:"]),
    "ER16": dict(pob=lambda: esc_sombra(p1=True, z_perdida=35.0), fase="sombra", rc=0, args=B4,
                 tiene=[("   sobre 30°", ["protegidas 1", "protegidas que K publica y P no 1"]),
                        ("== §6.3 sombra: NO CUMPLE", ["P1"])],
                 no_tiene=["== §6.3 sombra: CUMPLE"]),
    # S174 (VPR945-R2-04): el piso de 7 caracteres se acepta (y ER26 rechaza 6)
    "ER17": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True), fase="sombra", rc=0,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4[:7]],
                 tiene=[("== régimen de la sombra: brazo B4", [f"desde {SHA_REAL_B4}", "dentro 262"]),
                        ("== §6.3 sombra: CUMPLE", [])]),
    "ER18": dict(pob=lambda: esc_sombra(p1=True), fase="sombra", rc=0, args=B4 + ["--ahora", "2026-11-24 00:00"],
                 tiene=[("== §6.3 sombra: NO CUMPLE", ["P1", "21.0 de 28 días"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: PROVISORIO"]),
    "ER19": dict(pob=lambda: esc_sombra(negs="pierde"), fase="sombra", rc=4, args=B4 + ["--ahora", "2026-11-24 00:00"],
                 tiene=[("== §6.3 sombra: PROVISORIO", ["P2 PIERDE", "21.0 de 28 días"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # S174, VPR945-R2 (segunda ronda del verificador limpio)
    # R2-03: una pasada del 5 de noviembre a las 02:00 con el sha de #939 es anterior a la hora de su commit (03:23 UTC):
    # queda fuera aunque descienda del corte (sin ella, los conteos son los de ER5)
    "ER20": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True, reproc="2026-11-05 02:00"), fase="sombra", rc=0,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["dentro 262", "anteriores a la hora del corte 1"]),
                        ("== duración de la sombra", ["primera 2026-11-05 05:10"]),
                        ("== §6.3 sombra: CUMPLE", [])]),
    # R2-02: sin --sha-desde la compuerta se cierra con su mensaje, antes de leer nada
    "ER21": dict(pob=lambda: esc_sombra(), fase="sombra", rc=3, args=ROI_B4,
                 tiene=[("== régimen de la sombra: SIN --sha-desde", ["compuerta cerrada"])],
                 no_tiene=["== §6.3 sombra:", "== cobertura:", "== régimen de la sombra: brazo"]),
    # R2-04: el borde exacto de 28,0 días (del 4 de noviembre 06:00 al 2 de diciembre 06:00) cumple; un minuto menos, no
    "ER22": dict(pob=lambda: esc_sombra(), fase="sombra", rc=0, args=B4 + ["--ahora", "2026-12-01 00:00"],
                 tiene=[("== ventana fija de la sombra", ["ahora 2026-12-01 00:00:00 UTC (--ahora)"]),
                        ("== duración de la sombra", ["28.0 de 28 (completos)", ": COMPLETA"]),
                        ("== §6.3 sombra: CUMPLE", ["28.0 de 28 días"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO"]),
    "ER23": dict(pob=lambda: esc_sombra(), fase="sombra", rc=4, args=B4 + ["--ahora", "2026-11-30 23:59:59"],
                 tiene=[("== duración de la sombra", ["27.9 de 28 (faltan: ahora es anterior al fin)",
                                                      "por semana 6, 5, 7, 7 (25) (completas)", ": INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["27.9 de 28 días", "(ahora es anterior al fin)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R2-01 y R2-04: 13 noches distintas (14 pasadas: dos en la noche del 12 de noviembre) dan PROVISORIO con 34 días;
    # 14 noches dan CUMPLE
    # S174 (VPR945-R3-02): rehechos. Con 7 noches por mitad del lapso, 13 noches nunca alcanzan, así que el borde ya no es
    # el de 14 sino el del reparto. Se leen con B0 y sin las pasadas sens de relleno: con B0 ningún volcán cambió de ROI,
    # y lo que decide es sólo el reparto del conjunto. ER24: el caso del verificador, 13 noches seguidas (Láscar del 12 al
    # 17 de noviembre y Villarrica del 18 al 24) más una suelta el 10 de diciembre: 14 noches y 28,0 días, pero 13 y 1
    # por mitad: PROVISORIO. ER25: 7 y 7 justas, con la noche del 26 de noviembre justo en la mitad (va a la segunda): CUMPLE.
    "ER24": dict(pob=lambda: esc_once(offs=tuple(range(13)) + (28,)), fase="sombra", rc=4,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["fuera de ventana (posteriores a 2026-12-03 03:23:00) 11"]),
                        ("== duración de la sombra", ["28.0 de 28 (completos)", "por semana 7, 6, 0, 0 (13) (faltan)",
                                                      ": INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["semanas 7, 6, 0, 0 (13)", "PuyehueCordonCaulle 7, 6, 0, 0 (13)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "ER25": dict(pob=lambda: esc_once(offs=(0,) + tuple(range(7, 21)) + (28,), brazo="B0"), fase="sombra", rc=4,
                 args=["--roi-brazo", "B0", "--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B0", ["fuera de ventana (posteriores a 2026-12-03 03:23:00) 11"]),
                        ("== noches por semana y volcán", ["ROI distinta de B0 en ninguno", "Lascar 1, 7, 7, 0 (15) sin cambio, completas"]),
                        ("== duración de la sombra", ["28.0 de 28 (completos)", "por semana 1, 7, 7, 0 (15) (faltan)",
                                                      "sin sus noches ninguno;", "con menos de 14 noches ninguno: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["semanas 1, 7, 7, 0 (15)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R2-04: 6 caracteres no bastan aunque git los resuelva sin ambigüedad (el piso es 7)
    "ER26": dict(pob=lambda: esc_sombra(), fase="sombra", rc=3, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4[:6]],
                 tiene=[(f"== régimen de la sombra: --sha-desde {SHA_REAL_B4[:6]}", ["no es el sha", "compuerta cerrada"])],
                 no_tiene=["== §6.3 sombra:", "== cobertura:"]),
    # R2-04: un PROVISORIO leído con faltantes sale 5 (la marca de faltantes manda), no 4
    "ER27": dict(pob=lambda: esc_sombra(sin_reg=True), fase="sombra", rc=5,
                 args=B4 + ["--leer-con-faltantes", "prueba sintética", "--ahora", "2026-11-24 00:00"],
                 tiene=[("== cobertura: INSUFICIENTE", []),
                        ("== §6.3 sombra: PROVISORIO", ["21.0 de 28 días", "LEÍDO CON FALTANTES"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R2-02: una pasada de otra ROI dentro de la ventana con un sha que git no conoce tampoco deja leer (no se puede
    # descartar que sea posterior al corte)
    "ER28": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True, cc_def_sha="e" * 40, cc_def_hora="2026-11-08 06:30"),
                 fase="sombra", rc=3,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: el corte 58edb9788 no aísla el brazo B4",
                         ["['PuyehueCordonCaulle']", "compuerta cerrada"])],
                 no_tiene=["== §6.3 sombra:"]),
    # R2-03: las pasadas sin gránulo del generador se cortan con la misma ventana: una protegida de octubre no frena la
    # sombra; una de la ventana sí
    "ER29": dict(pob=lambda: esc_sombra(), fase="sombra", rc=0, args=B4,
                 sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-10-20 05:00", "protegida": True},
                              # S174 (VPR945-R4): una del 20 de diciembre, después del fin de la ventana, tampoco
                              {"volcan": "Lascar", "hora_utc": "2026-12-20 05:00", "protegida": True}],
                 tiene=[("   pasadas sin gránulo (del generador): 0", []), ("== cobertura: SUFICIENTE", []),
                        ("== §6.3 sombra: CUMPLE", [])]),
    "ER30": dict(pob=lambda: esc_sombra(), fase="sombra", rc=3, args=B4,
                 sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-11-20 05:00", "protegida": True}],
                 tiene=[("   pasadas sin gránulo (del generador): 1", []), ("== cobertura: INSUFICIENTE", [])],
                 no_tiene=["== §6.3 sombra:"]),
    # S174, VPR945-R3 (tercera ronda del verificador limpio; cuarta vuelta del autor)
    # R3-01: Cordón Caulle con sens una sola noche y sus otras 15 con la ROI def y el sha anterior al merge (fuera por
    # otra ROI, sin cerrar la compuerta porque su código no desciende del corte): los otros volcanes completan reloj y
    # noches, pero Cordón Caulle tiene 1 noche leída: PROVISORIO (el lector de antes daba CUMPLE, sint_cc_old)
    "ER31": dict(pob=lambda: esc_sombra(cc_viejo=True), fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["otra ROI 23 {'PuyehueCordonCaulle': 23}"]),
                        ("== noches por semana y volcán", ["PuyehueCordonCaulle 1, 0, 0, 0 (1) decide, faltan",
                                                           "Tupungatito 5, 7, 7, 5 (24) decide, completas"]),
                        ("== duración de la sombra", ["(completos)", "por semana 5, 7, 7, 5 (24) (completas)",
                                                      "sin sus noches ['PuyehueCordonCaulle'];", "con menos de 14 noches ninguno: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes con ROI cambiada sin sus noches: PuyehueCordonCaulle "
                                                        "1, 0, 0, 0 (1)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE", "== régimen de la sombra: el corte"]),
    # R3-01, variante: Cordón Caulle y Tupungatito no están en los objetivos (0 noches): PROVISORIO, no transparente
    "ER32": dict(pob=lambda: esc_sombra(sens=False), fase="sombra", rc=4, args=B4,
                 tiene=[("== noches por semana y volcán", ["PuyehueCordonCaulle 0, 0, 0, 0 (0) decide, faltan",
                                                           "Tupungatito 0, 0, 0, 0 (0) decide, faltan"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes con ROI cambiada sin sus noches: PuyehueCordonCaulle "
                                                        "0, 0, 0, 0 (0), Tupungatito 0, 0, 0, 0 (0)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R3-02 en un volcán cambiado: Cordón Caulle con 14 noches, 13 seguidas (7 al 19 de noviembre) y una el 15 de
    # diciembre; el conjunto reparte bien: PROVISORIO por Cordón Caulle (13 y 1)
    "ER33": dict(pob=lambda: esc_sombra(sens_fechas={"PuyehueCordonCaulle": [
                     f"2026-11-{d:02d}" for d in range(7, 20)] + ["2026-12-15"]}), fase="sombra", rc=4, args=B4,
                 tiene=[("== régimen de la sombra: brazo B4", ["fuera de ventana (posteriores a 2026-12-01 00:00:00) 1 "
                                                               "{'PuyehueCordonCaulle': 1}"]),
                        ("== noches por semana y volcán", ["PuyehueCordonCaulle 3, 7, 3, 0 (13) decide, faltan",
                                                           "Tupungatito 5, 5, 7, 7 (24) decide, completas"]),
                        ("== duración de la sombra", ["por semana 6, 7, 7, 7 (27) (completas)",
                                                      "sin sus noches ['PuyehueCordonCaulle'];", "con menos de 14 noches ninguno: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["PuyehueCordonCaulle 3, 7, 3, 0 (13)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R3-04: una pasada en el minuto exacto del commit del corte (#939, 2026-11-05 03:23 UTC) entra a la lectura
    "ER34": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True, reproc="2026-11-05 03:23"), fase="sombra", rc=0,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["dentro 263", "anteriores a la hora del corte 0"]),
                        ("== duración de la sombra", ["primera 2026-11-05 03:23", "por semana 5, 7, 7, 5 (24)"]),
                        ("   horas UTC de las pasadas leídas", ["de 03:23 a 06:30"]),
                        ("== §6.3 sombra: CUMPLE", [])]),
    # R3-04: una pasada de otra ROI con el código del corte en ese mismo minuto cierra la compuerta
    "ER35": dict(pob=lambda: esc_sombra(mezcla=True, sha_real=True, cc_def_sha=SHA_REAL_B4,
                                        cc_def_hora="2026-11-05 03:23"), fase="sombra", rc=3,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: el corte 58edb9788 no aísla el brazo B4",
                         ["['PuyehueCordonCaulle']", "compuerta cerrada"])],
                 no_tiene=["== §6.3 sombra:"]),
    # control positivo: los 11 volcanes con 14 noches cada uno repartidas en 28 días (7 y 7), B4 desde el merge de #939
    "ER36": dict(pob=esc_once, fase="sombra", rc=0, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Chaiten 5, 5, 5, 5 (20) sin cambio, completas",
                                                           "Villarrica 5, 5, 5, 5 (20) sin cambio, completas",
                                                           "PuyehueCordonCaulle 5, 5, 5, 5 (20) decide, completas",
                                                           "Tupungatito 5, 5, 5, 5 (20) decide, completas"]),
                        ("== duración de la sombra", ["28.0 de 28 (completos)", "por semana 5, 5, 5, 5 (20) (completas)",
                                                      "sin sus noches ninguno;", "con menos de 14 noches ninguno: COMPLETA"]),
                        ("== cobertura: SUFICIENTE", []),
                        ("== §6.3 sombra: CUMPLE", ["ventana 2026-11-05 03:23 a 2026-12-03 03:23 UTC, 28.0 de 28 días, "
                                                   "semanas 5, 5, 5, 5 (20), PuyehueCordonCaulle 5, 5, 5, 5 (20), "
                                                   "Tupungatito 5, 5, 5, 5 (20)",
                                                   # S174 (R5-03): la línea CUMPLE nombra a los nueve con sus noches
                                                   "sin cambio de ROI, 14 noches o más cada uno: Chaiten 20, Copahue 20"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO", "== §6.3 sombra: NO CUMPLE"]),
    # S174, VPR945-R4 (cuarta ronda del verificador; quinta vuelta del autor: ventana fija, LECTURA LR3)
    # R4-01: Cordón Caulle y Tupungatito con 14 noches seguidas sólo en las semanas 1 y 2; los otros nueve, en las cuatro
    "ER37": dict(pob=lambda: esc_once(offs=OFFS_4SEM + (28,), offs_vol={v: tuple(range(14)) for v in CAMBIAN_B4}),
                 fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["fuera de ventana (posteriores a 2026-12-03 03:23:00) 9"]),
                        ("== noches por semana y volcán", ["PuyehueCordonCaulle 7, 7, 0, 0 (14) decide, faltan",
                                                           "Tupungatito 7, 7, 0, 0 (14) decide, faltan",
                                                           "Chaiten 5, 5, 5, 5 (20) sin cambio, completas"]),
                        ("== duración de la sombra", ["por semana 7, 7, 5, 5 (24) (completas)",
                                                      "sin sus noches ['PuyehueCordonCaulle', 'Tupungatito'];", "con menos de 14 noches ninguno: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["PuyehueCordonCaulle 7, 7, 0, 0 (14), Tupungatito 7, 7, 0, 0 (14)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R4-03: una protegida con fecha posterior a «ahora» (día 27, ahora = inicio + 21 días) no entra a la lectura: se
    # cuenta fuera de ventana y se lista; sin ella no hay P1 que vete (con ella entrando, NO CUMPLE por P1)
    "ER38": dict(pob=lambda: esc_once(offs=OFFS_4SEM[:15], extra=_r403_protegida_futura), fase="sombra", rc=4,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "2026-11-26 03:23"],
                 tiene=[("== régimen de la sombra: brazo B4", ["fuera de ventana (posteriores a 2026-11-26 03:23:00) 1 "
                                                               "{'Lascar': 1}"]),
                        ("   protegidas fuera de esta lectura", ["Lascar 2026-12-02 06:30 (fuera de ventana)"]),
                        ("== §6.3 sombra: PROVISORIO", ["21.0 de 28 días", "(ahora es anterior al fin)",
                                                        "semanas 5, 5, 5, 0 (15)", "P1 = 0"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # borde de semana (R4-04, equivalente con la ventana fija): una pasada en el minuto exacto de inicio + 7 días va a la
    # semana 2; la semana 1 queda con 4 noches (bajo el umbral de 5)
    "ER39": dict(pob=lambda: esc_once(offs=(0, 1, 2, 3, 8, 9, 10, 11) + OFFS_4SEM[10:], extra=_borde_7_dias),
                 fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== duración de la sombra", ["por semana 4, 5, 5, 5 (19) (faltan)", ": INCOMPLETA"]),
                        ("== noches por semana y volcán", ["Villarrica 4, 5, 5, 5 (19) sin cambio, completas",
                                                           "PuyehueCordonCaulle 4, 4, 5, 5 (18) decide, faltan"]),
                        ("== §6.3 sombra: PROVISORIO", ["semanas 4, 5, 5, 5 (19)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # borde del fin: un minuto antes del fin entra a la semana 4; en el minuto del fin queda fuera de ventana; una ROI
    # distinta después del fin no cierra la compuerta
    "ER40": dict(pob=lambda: esc_once(extra=_borde_fin), fase="sombra", rc=0, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== régimen de la sombra: brazo B4", ["otra ROI 1 {'PuyehueCordonCaulle': 1}",
                                                               "fuera de ventana (posteriores a 2026-12-03 03:23:00) 1 "
                                                               "{'Lascar': 1}"]),
                        ("== duración de la sombra", ["última 2026-12-03 03:22", "por semana 5, 5, 5, 6 (21) (completas)"]),
                        ("== §6.3 sombra: CUMPLE", [])],
                 no_tiene=["== §6.3 sombra: PROVISORIO", "== régimen de la sombra: el corte"]),
    # R4-04 (MW10): las pasadas no observadas o SIN DATO de un volcán cambiado no cuentan como noches, ni suyas ni del
    # conjunto, aunque caigan en noches distintas
    "ER41": dict(pob=lambda: esc_once(offs_vol={"PuyehueCordonCaulle": OFFS_4SEM[:15]}, extra=_r404_cc_semana4_no_leida),
                 fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("   SIN DATO por motivo:", ["'diurna': 2"]), ("== cobertura: SUFICIENTE", []),
                        ("== noches por semana y volcán", ["PuyehueCordonCaulle 5, 5, 5, 0 (15) decide, faltan"]),
                        ("== duración de la sombra", ["por semana 5, 5, 5, 5 (20) (completas)"]),
                        ("== §6.3 sombra: PROVISORIO", ["PuyehueCordonCaulle 5, 5, 5, 0 (15)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # decisión de la coordinadora (SEMANA_EXIGE_SIN_CAMBIO = False): un volcán sin cambio de ROI con dos semanas vacías
    # no decide por semana. S174 (R5-03, sexta vuelta): sí pide 14 noches en total, así que el escenario pasa de 10
    # noches (5, 5, 0, 0) a 14 (7, 7, 0, 0): sigue CUMPLE; con 10 sería PROVISORIO (lo prueba ER49 con 13)
    "ER42": dict(pob=lambda: esc_once(offs_vol={"Chaiten": tuple(range(14))}), fase="sombra", rc=0,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Chaiten 7, 7, 0, 0 (14) sin cambio, completas"]),
                        ("== §6.3 sombra: CUMPLE", [])],
                 no_tiene=["== §6.3 sombra: PROVISORIO"]),
    # sin --ahora, «ahora» es el reloj de la máquina y la salida lo dice (el veredicto no depende del día: faltan las
    # noches de Cordón Caulle y Tupungatito)
    "ER43": dict(pob=lambda: esc_sombra(sens=False), fase="sombra", rc=4, args=B4, sin_ahora=True,
                 tiene=[("== ventana fija de la sombra", ["(reloj de esta máquina, UTC)"]),
                        ("== §6.3 sombra: PROVISORIO", [])]),
    # S174, VPR945-R5 (quinta ronda del verificador; sexta vuelta del autor, decisión de Nicolás del 2026-11-06)
    # R5-01: --ahora con zona se convierte a UTC (antes: TypeError al comparar con fechas sin zona). Z es UTC.
    "ER44": dict(pob=esc_once, fase="sombra", rc=0, no_traceback=True,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "2026-12-10T00:00:00Z"],
                 tiene=[("== ventana fija de la sombra", ["ahora 2026-12-10 00:00:00 UTC (--ahora)"]),
                        ("== §6.3 sombra: CUMPLE", [])]),
    # R5-01: una zona distinta de UTC se convierte, no se ignora: 00:23 en UTC-3 son las 03:23 UTC, el fin justo (CUMPLE);
    # ignorada, «ahora» quedaría tres horas antes del fin (PROVISORIO, «27.8»)
    # S174 (VPR945-R6-03): con TZ en UTC+12, como ER47. POR QUÉ: convertir a la zona local de la máquina en vez de a UTC
    # (MR75) sólo se veía si la máquina no estaba en UTC; en un runner de Actions (UTC) era equivalente. Con TZ fija la
    # zona local queda 15 horas lejos de la de --ahora y la línea «ahora» cambia en cualquier máquina.
    "ER45": dict(pob=esc_once, fase="sombra", rc=0, no_traceback=True, env={"TZ": "XXX-12"},
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "2026-12-03T00:23:00-03:00"],
                 tiene=[("== ventana fija de la sombra", ["ahora 2026-12-03 03:23:00 UTC (--ahora)"]),
                        ("== §6.3 sombra: CUMPLE", ["28.0 de 28 días"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO"]),
    # R5-04 (MX13): una pasada en el minuto exacto de «ahora» entra (Villarrica, la última del día 25, a las 05:50)
    "ER46": dict(pob=esc_once, fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "2026-11-30 05:50"],
                 tiene=[("== régimen de la sombra: brazo B4", ["fuera de ventana (posteriores a 2026-11-30 05:50:00) 0 {}"]),
                        ("== duración de la sombra", ["última 2026-11-30 05:50"])]),
    # R5-04 (MX11): sin --ahora, el reloj es el UTC aunque la zona local de la máquina sea otra (TZ en UTC+12)
    "ER47": dict(pob=lambda: esc_sombra(sens=False), fase="sombra", rc=4, args=B4, sin_ahora=True,
                 env={"TZ": "XXX-12"}, chequeo=_ahora_es_utc,
                 tiene=[("== ventana fija de la sombra", ["(reloj de esta máquina, UTC)"])]),
    # R5-03 (el caso del verificador): sólo Cordón Caulle y Tupungatito tienen pasadas (5 noches por semana); los otros
    # nueve, ninguna. Antes daba CUMPLE con datos de 2 de 11 volcanes; ahora cada uno de los nueve pide 14 noches
    "ER48": dict(pob=lambda: esc_once(offs_vol={v: () for v in SIN_CAMBIO_B4}), fase="sombra", rc=4,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Chaiten 0, 0, 0, 0 (0) sin cambio, faltan",
                                                           "Villarrica 0, 0, 0, 0 (0) sin cambio, faltan",
                                                           "PuyehueCordonCaulle 5, 5, 5, 5 (20) decide, completas"]),
                        ("== duración de la sombra", ["por semana 5, 5, 5, 5 (20) (completas)",
                                                      "sin cambio de ROI con menos de 14 noches ['Chaiten', "
                                                      "'Copahue', 'Isluga', 'Lascar', 'Lastarria', 'Llaima', "
                                                      "'NevadosDeChillan', 'PlanchonPeteroa', 'Villarrica']: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes sin cambio de ROI con menos de 14 noches: Chaiten 0, "
                                                        "Copahue 0, Isluga 0, Lascar 0"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R5-03, borde: uno de los nueve con 13 noches (los demás con 20) deja PROVISORIO y se nombra
    "ER49": dict(pob=lambda: esc_once(offs_vol={"Chaiten": OFFS_4SEM[:13]}), fase="sombra", rc=4,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Chaiten 5, 5, 3, 0 (13) sin cambio, faltan",
                                                           "Lascar 5, 5, 5, 5 (20) sin cambio, completas"]),
                        ("== duración de la sombra", ["sin cambio de ROI con menos de 14 noches ['Chaiten']: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes sin cambio de ROI con menos de 14 noches: Chaiten 13"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R5-02: la noche del 12 de noviembre tiene pasadas antes (03:0k) y después (05:xx) del borde de la semana 2 (03:23)
    # en los 11 volcanes. Cuenta una vez, en la semana de su primera pasada (la 1): la semana 2 queda con 4 noches propias
    # y da PROVISORIO. Antes contaba en las dos y daba CUMPLE con 4 noches propias en la semana 2.
    "ER50": dict(pob=lambda: esc_once(offs=(0, 1, 2, 3, 7, 8, 9, 10, 11) + OFFS_4SEM[10:], extra=_r502_noche_en_la_frontera),
                 fase="sombra", rc=4, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== duración de la sombra", ["por semana 5, 4, 5, 5 (19) (faltan)", ": INCOMPLETA"]),
                        ("== noches por semana y volcán", ["PuyehueCordonCaulle 5, 4, 5, 5 (19) decide, faltan",
                                                           "Chaiten 5, 4, 5, 5 (19) sin cambio, completas"]),
                        ("== §6.3 sombra: PROVISORIO", ["semanas 5, 4, 5, 5 (19)"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    # R5-03, control positivo en el borde: los nueve con 14 noches justas (5, 5, 4, 0), los dos cambiados con 5 por
    # semana: CUMPLE (a los nueve no se les pide el mínimo semanal)
    "ER51": dict(pob=lambda: esc_once(offs_vol={v: OFFS_4SEM[:14] for v in SIN_CAMBIO_B4}), fase="sombra", rc=0,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Chaiten 5, 5, 4, 0 (14) sin cambio, completas",
                                                           "Tupungatito 5, 5, 5, 5 (20) decide, completas"]),
                        ("== duración de la sombra", ["por semana 5, 5, 5, 5 (20) (completas)",
                                                      "sin cambio de ROI con menos de 14 noches ninguno: COMPLETA"]),
                        ("== §6.3 sombra: CUMPLE", ["sin cambio de ROI, 14 noches o más cada uno: Chaiten 14"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO", "== §6.3 sombra: NO CUMPLE"]),
    # R5-01: una fecha ilegible en --ahora sale con un error claro (argparse, salida 2), sin veredicto
    "ER52": dict(pob=esc_once, fase="sombra", rc=2, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "2026-13-45 00:00"],
                 tiene_err=["--ahora '2026-13-45 00:00' no es una fecha ISO"],
                 no_tiene=["== §6.3 sombra:"]),
    # S174, VPR945-R6 (sexta ronda del verificador limpio; retoques sin cambio de regla)
    # R6-01: una fecha con zona que al pasarla a UTC sale del rango de datetime (año 9999 con zona -03:00) sale con el
    # error de argparse (salida 2), sin veredicto; el lector de 235ba7918 se caía con OverflowError (salida 1, Traceback),
    # que aquí es la aserción «no se cae» (no_traceback), no una caída
    "ER53": dict(pob=esc_once, fase="sombra", rc=2, no_traceback=True,
                 args=ROI_B4 + ["--sha-desde", SHA_REAL_B4, "--ahora", "9999-12-31T23:59:59-03:00"],
                 tiene_err=["--ahora '9999-12-31T23:59:59-03:00' no es una fecha ISO"],
                 no_tiene=["== §6.3 sombra:"]),
    # R6-02: con --roi-brazo B0 ningún volcán cambia de ROI y los once piden NOCHES_MIN_SIN_CAMBIO = 14 noches. Uno con 13
    # (Chaiten; los demás con 20, el conjunto con 5 por semana) deja PROVISORIO y se nombra; con 14 justas, CUMPLE. Sin
    # este par, apagar la regla cuando no hay volcanes cambiados (MR72) o vaciar con B0 la lista de los sin cambio (MR73)
    # sobrevivían a todas las pruebas (MY7 y MY8 del verificador): el único escenario con B0 (ER25) ya es PROVISORIO por
    # las semanas
    "ER54": dict(pob=lambda: esc_once(offs_vol={"Chaiten": OFFS_4SEM[:13]}, brazo="B0"), fase="sombra", rc=4,
                 args=["--roi-brazo", "B0", "--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["ROI distinta de B0 en ninguno",
                                                           "Chaiten 5, 5, 3, 0 (13) sin cambio, faltan",
                                                           "Lascar 5, 5, 5, 5 (20) sin cambio, completas"]),
                        ("== duración de la sombra", ["por semana 5, 5, 5, 5 (20) (completas)",
                                                      "sin cambio de ROI con menos de 14 noches ['Chaiten']: INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes sin cambio de ROI con menos de 14 noches: Chaiten 13"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "ER55": dict(pob=lambda: esc_once(offs_vol={"Chaiten": OFFS_4SEM[:14]}, brazo="B0"), fase="sombra", rc=0,
                 args=["--roi-brazo", "B0", "--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["ROI distinta de B0 en ninguno",
                                                           "Chaiten 5, 5, 4, 0 (14) sin cambio, completas"]),
                        ("== duración de la sombra", ["sin cambio de ROI con menos de 14 noches ninguno: COMPLETA"]),
                        # VPR953-03: la lista entera; con sólo «Chaiten 14, Copahue 20», recortarla a dos (MR79) sobrevivía
                        ("== §6.3 sombra: CUMPLE", ["sin cambio de ROI, 14 noches o más cada uno: "
                                                    + _noches_once({"Chaiten": 14}) + ")"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO", "== §6.3 sombra: NO CUMPLE"]),
    # S174 (VPR953-02, verificador de #953): ER54 y ER55 sólo bajan a Chaiten, el primero de los once por orden
    # alfabético, así que la regla aplicada sólo al primero (MR76), sin el último (MR77) o sin el segundo (MR78)
    # sobrevivía a toda la batería. Copahue (el segundo) y Villarrica (el último) con 13 noches: PROVISORIO, nombra a
    # los dos; su par con 14 justas: CUMPLE, con los once en la línea.
    "ER56": dict(pob=lambda: esc_once(offs_vol={"Copahue": OFFS_4SEM[:13], "Villarrica": OFFS_4SEM[:13]}, brazo="B0"),
                 fase="sombra", rc=4, args=["--roi-brazo", "B0", "--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["ROI distinta de B0 en ninguno",
                                                           "Chaiten 5, 5, 5, 5 (20) sin cambio, completas",
                                                           "Copahue 5, 5, 3, 0 (13) sin cambio, faltan",
                                                           "Villarrica 5, 5, 3, 0 (13) sin cambio, faltan"]),
                        ("== duración de la sombra", ["sin cambio de ROI con menos de 14 noches ['Copahue', 'Villarrica']: "
                                                      "INCOMPLETA"]),
                        ("== §6.3 sombra: PROVISORIO", ["volcanes sin cambio de ROI con menos de 14 noches: Copahue 13, "
                                                        "Villarrica 13"])],
                 no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "ER57": dict(pob=lambda: esc_once(offs_vol={"Copahue": OFFS_4SEM[:14], "Villarrica": OFFS_4SEM[:14]}, brazo="B0"),
                 fase="sombra", rc=0, args=["--roi-brazo", "B0", "--sha-desde", SHA_REAL_B4],
                 tiene=[("== noches por semana y volcán", ["Copahue 5, 5, 4, 0 (14) sin cambio, completas",
                                                           "Villarrica 5, 5, 4, 0 (14) sin cambio, completas"]),
                        ("== duración de la sombra", ["sin cambio de ROI con menos de 14 noches ninguno: COMPLETA"]),
                        ("== §6.3 sombra: CUMPLE", ["sin cambio de ROI, 14 noches o más cada uno: "
                                                    + _noches_once({"Copahue": 14, "Villarrica": 14}) + ")"])],
                 no_tiene=["== §6.3 sombra: PROVISORIO", "== §6.3 sombra: NO CUMPLE"]),
    "E22": dict(pob=lambda: base(), sg_otra=True, rc=3,
                tiene=[("== cobertura: INSUFICIENTE", []), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    # ------------------------------------------------------------ §6 bis, brazos de posición
    "E61": dict(pob=lambda: base(extra=_escena("Lascar", SEIS, "pos", px_cerca_lejos)), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) sí", "P-cercano sí", "P-pico sí"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -6, bloques 6)",
                                                  "tabla sola GANA (neto -6, bloques 6)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P-cercano", ["gana contra P"]),
                       ("   §6 bis cambian de publicación contra P (radiante), P-cercano: 6",
                        ["Lascar 2026-05-01 06:00", "baja", "publica"]),
                       ("   §6 bis cambian de publicación contra P (radiante), P-pico: 0", []),
                       ("== §6.2 ventana T, canal tabla", ["posición P-cercano", "P2 contra K GANA (neto -12, bloques 12"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-cercano]"])]),
    "E62": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_linea), NEGS_CERCANO)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide EMPATE (neto 0, bloques 12)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-pico", []),
                       ("== §6.2 ventana T, canal tabla", ["posición P-pico", "P2 contra K GANA (neto -12, bloques 12"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-pico]"])]),
    "E63": dict(pob=lambda: base(extra=_escena("Lascar", (1, 2, 3), "pos", px_cerca_lejos)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide SIN SUSTRATO (neto -3, bloques 3)"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("== §6.2 ventana T, canal tabla", ["posición P (radiante)", "P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P (radiante)]"])]),
    "E64": dict(pob=lambda: base(extra=_prot_cerca_lejos), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) no", "P-cercano sí", "P-pico no"]),
                       ("== §6 bis posición elegida: P-cercano", ["P no es elegible"]),
                       ("== §6.2 ventana O, canal tabla", ["posición P-cercano", "P1 0"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-cercano]"])],
                no_tiene=["== §6 censo: NO CUMPLE"]),
    "E65": dict(pob=lambda: base(extra=_y(_prot_cerca_lejos, NEGS_CERCANO)), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) no", "P-cercano sí", "P-pico no"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide PIERDE (neto 6, bloques 6)"]),
                       ("== §6 bis posición elegida: NINGUNA POSICIÓN ELEGIBLE", ["P no se adopta"]),
                       ("== §6 censo: NO CUMPLE", ["§6 bis: NINGUNA POSICIÓN ELEGIBLE"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    "E66": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_linea),
                                          _escena("Villarrica", range(11, 17), "pos", px_cerca_lejos))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -12, bloques 12)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-cercano", ["ganan los dos", "menor E + E_lejana"])]),
    "E67": dict(pob=lambda: base(extra=_escena("Lascar", SEIS, "pos", px_linea)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-pico", ["ganan los dos", "a igual valor, P-pico"])]),
    "E68": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_cerca_lejos),
                                          _escena("Villarrica", SEIS, "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00"))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide EMPATE (neto 0, bloques 12)",
                                                  "tabla sola EMPATE (neto 0, bloques 12)", "E_lejana 6"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("== §6 bis vara lejana: far_ref en los objetivos 6, observadas 6", []),
                       ("   §6 bis pasadas lejanas", ["con algún alertado 6 de 6", "P (radiante) publica 0",
                                                     "P-cercano publica 6", "P-pico publica 0"])],
                no_tiene=["== §6 bis vara lejana: far_ref en los objetivos 6, observadas 6: SIN DATO"]),
    "E69": dict(pob=lambda: base(extra=_y(_escena("Villarrica", range(1, 9), "pos", px_cerca_lejos, mes="2026-09",
                                                  tabla=False),
                                          _escena("Lascar", (1,), "neg_limpio", px_cerca_lejos, hora="05:00"))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -7, bloques 9)",
                                                  "tabla sola SIN SUSTRATO (neto 1, bloques 1)"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"])]),
    "E70": dict(pob=lambda: base(extra=_escena("Llaima", SEIS, "pos", px_llaima_centro)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P (radiante)", [])]),
    "E71": dict(pob=lambda: base(extra=_escena("Lascar", (1, 2, 3), "far_ref", None, hora="05:00", K=0.2, P=None)),
                rc=0,
                tiene=[("== §6 bis vara lejana: far_ref en los objetivos 3, observadas 3", []),
                       ("   §6 bis pasadas lejanas", ["con algún alertado 0 de 3", "un cero de E_lejana no dice nada"]),
                       ("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", [])],
                no_tiene=["== §6 bis vara lejana: far_ref en los objetivos 3, observadas 3: SIN DATO"]),
    "E72": dict(pob=lambda: base(), rc=0,
                tiene=[("== §6 bis vara lejana: far_ref en los objetivos 0, observadas 0: SIN DATO", []),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("   §6 bis multiplicidad", ["mayor que 5 %"]),
                       ("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                        ["P (radiante) 0.50 km, 0.96, n=24"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P (radiante)]"])]),
    "E73": dict(pob=lambda: base(extra=_escena("Villarrica", (1, 2, 3, 4), "pos", None, tabla=False)), rc=0,
                tiene=[("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                        ["P (radiante) 0.50 km, 0.96, n=24", "P-cercano 0.50 km, 0.96, n=24"])],
                no_contiene=[("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                              "n=28")]),
    "E74": dict(pob=lambda: base(extra=_y(_prot_ocr_anillo,
                                          _escena("Lascar", range(10, 16), "pos", px_cerca_lejos, mes="2026-09"))), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) sí", "P-cercano no", "P-pico no"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide GANA"]),
                       ("== §6 bis posición elegida: P (radiante)", [])]),
    "E75": dict(pob=lambda: base(extra=_y(_escena("Villarrica", range(1, 13), "pos", px_cerca_lejos, mes="2026-09",
                                                  tabla=False),
                                          _escena("Lascar", range(15, 19), "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00", tabla=False))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -8, bloques 16)",
                                                  "tabla sola SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P-cercano", ["gana contra P"])]),
    "E76": dict(pob=lambda: base(extra=_y(_escena("Lascar", range(1, 15), "pos", px_linea),
                                          _escena("Villarrica", range(1, 5), "pos", px_cerca_lejos),
                                          _escena("Villarrica", range(11, 17), "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00"))), rc=0,
                tiene=[("   §6 bis cambian de publicación contra P (radiante), P-cercano: 24", ["(y 4 más, cortada a 20)"]),
                       ("== §6 bis posición elegida: P-pico", ["ganan los dos", "menor E + E_lejana"])]),
    "E77": dict(pob=lambda: base(extra=_n3("2026-07-31 06:40")), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("== §6 ter N-3", ["Villarrica 2026-07-31 06:40 (K)"]),
                       ("   §6 ter P1 por brazo", ["P (radiante) 0 (contándolas 1)"]),
                       ("== §6.2 ventana O, canal todo", ["P1 0 (", "contando las N-3 1"]),
                       ("== §6 bis elegibles", ["P (radiante) sí"])],
                no_tiene=["== §6 censo: NO CUMPLE"]),
    "E78": dict(pob=lambda: base(extra=_n3("2026-10-09 06:40")), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/todo: P1 1"]),
                       ("== §6 ter N-3", ["ninguna"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    "E79": dict(pob=lambda: base(extra=_n3("2026-07-31 06:40", tabla=True)), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/tabla: P1 1", "O/todo: P1 1"]),
                       ("== §6 ter N-3", ["ninguna"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    # S175: la clase N-3 (antes del 2026-10-09) es anterior al inicio de la sombra: sale de la lectura y se lista, sin vetar
    "E80": dict(pob=lambda: esc_sombra(prot_ocr=True, sensor_ocr="VIIRS_SNPP_750"), fase="sombra", rc=0, args=B4,
                tiene=[("   protegidas fuera de esta lectura", ["Villarrica 2026-10-08 06:30 (anterior al inicio de la sombra)"]),
                       ("== régimen de la sombra: brazo B4", ["anteriores al inicio de la sombra 1"]),
                       ("== §6.3 canal todo", ["P1 0 "]),
                       ("== §6.3 sombra: CUMPLE", [])],
                no_tiene=["== §6.3 sombra: NO CUMPLE"]),
    # S173, de la rama de V750-A: la protegida que sale por otra ROI se lista por nombre y motivo (LR1; MR8). S175: con el
    # corte en #939, porque con el corte de prueba la compuerta se cierra antes de esa línea (ER2)
    "ER7": dict(pob=lambda: esc_sombra(mezcla=True), fase="sombra", rc=0, args=ROI_B4 + ["--sha-desde", SHA_REAL_B4],
                tiene=[("   protegidas fuera de esta lectura", ["PuyehueCordonCaulle 2026-11-04 06:30 (otra ROI)"]),
                       ("== §6.3 sombra: CUMPLE", [])],
                no_contiene=[("   protegidas fuera de esta lectura", "2026-11-06")]),
}


def correr(nombre, e, analizador, evaluador, dest):
    d = dest / nombre
    pb = e["pob"]()
    pb.escribir(d, verde=e.get("verde", VERDE), sin_granulo_otra_lista=e.get("sg_otra", False),
                sin_granulo=e.get("sin_granulo", ()))
    cmd = [sys.executable, str(analizador), "--fase", e.get("fase", "censo"), "--art", str(d / "art"),
           "--objetivos", str(d / "objetivos.json"), "--evaluador", str(evaluador),
           "--sin-granulo", str(d / "sin_granulo.json"), "--salida", str(d / "salida.txt")]
    if (d / "equivalencia_local.txt").exists():
        cmd += ["--equivalencia-local", str(d / "equivalencia_local.txt")]
    args = list(e.get("args", []))
    if SIN_AHORA and "--ahora" in args:   # S174 (R4): para el rojo contra un lector que no conoce --ahora
        j = args.index("--ahora")
        del args[j:j + 2]
    elif e.get("fase") == "sombra" and "--ahora" not in args and not e.get("sin_ahora") and not SIN_AHORA:
        args += ["--ahora", AHORA_PRUEBA]   # S174 (VPR945-R4): las pruebas fijan «ahora» para ser deterministas
    cmd += args
    # VA-08 del verificador: una caída nativa del proceso (0xC0000005 bajo carga, sin Traceback) no es una falla por
    # aserción. Los códigos que el analizador puede dar son 0, 3, 4 (S174), 5 y 6; cualquier otro es caída. Una caída nativa se
    # reintenta hasta 2 veces y el reintento queda escrito en la salida.
    # S174 (VPR945-R5): rc=2 sólo vale si el escenario lo espera (argparse rechaza un argumento, sin Traceback, ER52)
    codigos = (0, 3, 4, 5, 6) + ((2,) if e["rc"] == 2 else ())
    env = None
    if e.get("env"):   # S174 (R5-04): p. ej. TZ en UTC+12, para que leer el reloj local en vez del UTC se vea
        import os
        env = dict(os.environ, **e["env"])
    reint = 0
    while True:
        # S162 relevo: el plazo es de reloj y corre con el equipo suspendido (M5 y M6 cayeron así); 6 h
        o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=21600,
                           env=env)
        txt = o.stdout + o.stderr
        nativa = o.returncode not in codigos and "Traceback (most recent call last)" not in txt
        if not nativa or reint >= 2:
            break
        reint += 1
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    # S174 (VPR945-R5-01): en un escenario con no_traceback=True el defecto que se prueba ES el traceback (el lector de
    # 106db8941 se caía con --ahora con zona); ahí «no se cae» es una aserción del escenario y su violación es FALLA, no
    # CAÍDA. Lo usan ER44, ER45 y ER53 (S174, VPR953-05). La mutación de la zona (MR68) cae por aserción sobre la
    # salida en ER45 y ER53 sin caerse (A116); la del OverflowError (MR74) cae en ER53 SÓLO por esta bandera, y el
    # medidor la rotula aparte, «sólo por la bandera "no se cae"» (VPR953-01).
    if e.get("no_traceback") and "Traceback (most recent call last)" in txt:
        return "FALLA", [f"se cayó (código {o.returncode}, Traceback) y el escenario afirma que no se cae: "
                         + (txt.strip().splitlines() or [""])[-1][:300]]
    if "Traceback (most recent call last)" in txt or o.returncode not in codigos:
        return "CAÍDA", [f"código {o.returncode}, reintentos {reint}", (txt.strip().splitlines() or [""])[-1][:300]]
    lineas = o.stdout.splitlines()
    fallas = []
    for s in e.get("tiene_err", []):   # S174 (R5-01): el mensaje de argparse va a stderr
        if s not in o.stderr:
            fallas.append(f"falta en stderr «{s}»")
    if e.get("chequeo"):               # S174 (R5-04): un chequeo que no se escribe como subcadena fija
        fallas += e["chequeo"](lineas)
    if o.returncode != e["rc"]:
        fallas.append(f"código de salida {o.returncode}, se esperaba {e['rc']}")
    for pref, subs in e.get("tiene", []):
        if not any(l.startswith(pref) and all(s in l for s in subs) for l in lineas):
            fallas.append(f"falta una línea «{pref}» con {subs}")
    for pref in e.get("no_tiene", []):
        if any(l.startswith(pref) for l in lineas):
            fallas.append(f"sobra una línea «{pref}»")
    for pref, s in e.get("no_contiene", []):
        if any(l.startswith(pref) and s in l for l in lineas):
            fallas.append(f"la línea «{pref}» no debería contener «{s}»")
    if reint:
        fallas.append(f"(nota: {reint} reintento(s) por caída nativa)")
        return ("OK" if len(fallas) == 1 else "FALLA"), fallas
    return ("OK" if not fallas else "FALLA"), fallas


SIN_AHORA = False


def main():
    global SIN_AHORA
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--analizador", default=str(AQUI / "evaluar_v750a.py"))
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura")
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-ahora", action="store_true",
                    help="S174 (R4): no pasar --ahora (sólo para el rojo contra un lector anterior a la quinta vuelta)")
    a = ap.parse_args()
    SIN_AHORA = a.sin_ahora
    sel = [x for x in a.solo.split(",") if x] or list(ESCENARIOS)
    L, n_falla, n_caida = [], 0, 0
    for nom in sel:
        est, det = correr(nom, ESCENARIOS[nom], Path(a.analizador), Path(a.evaluador), a.dest)
        n_falla += est == "FALLA"
        n_caida += est == "CAÍDA"
        s = f"{nom} | {est}" + (" | " + " ; ".join(det) if det else "")
        print(s, flush=True)
        L.append(s)
    if n_caida:
        res = f"== PRUEBAS: CAÍDAS {n_caida} (fallas por aserción {n_falla}) de {len(sel)}"
    elif n_falla:
        res = f"== PRUEBAS: FALLAS {n_falla} de {len(sel)}"
    else:
        res = f"== PRUEBAS: TODOS LOS ESCENARIOS COMO SE ESPERA ({len(sel)})"
    print(res)
    L.append(res)
    (a.dest / "probar_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 2 if n_caida else (1 if n_falla else 0)


if __name__ == "__main__":
    sys.exit(main())
