# Caminos de falla por afirmacion (fijados antes de abrir ningun archivo citado)

## R1 (VV169-01): control por volcan y sensor cuenta pasadas con datetime_utc[:10] == ultimo dia de la ventana o la vispera
1. "Ultimo dia de la ventana" se calcula como max de los datetime de los records y no como la fecha del run o de la ventana pedida: si un sensor trae datos viejos, el "ultimo dia" se corre y el control mira un dia equivocado (falso verde).
2. datetime_utc nulo, con formato distinto (sin T, con zona, como int) o ausente: [:10] da basura o excepcion; el record cae fuera del conteo en silencio o rompe el script.
3. Off by one: "vispera" calculada con timedelta sobre string, o a nivel de mes (dia 1 menos un dia), o comparacion lexicografica que falla en cambio de mes/ano.
4. Cuenta records (no pasadas): un volcan con 3 records de una misma pasada cuenta 3; o dos sensores comparten pasada y se mezclan (VIIRS_SNPP sin sufijo = 375, *_750 = 750, regla A48).
5. Mapeo sensor->MODIS/V750/V375 por substring ("375" in s) que clasifica mal (A48).
6. Un volcan sin ningun record: el bucle por volcan nunca lo visita y no sale como falla (el denominador es los volcanes con archivo, no los 11).
7. Ventana de 8 dias: cuando el ultimo dia aun no tiene datos por latencia (cron 15:00 UTC, NRT 3 h), la vispera cubre o no; y el primer dia de la primera corrida (2026-11-03) no tiene vispera.
8. Umbral minimo de pasadas: >=1 contra >=N.

## R2 (VV169-02): FALLA si quedan sin pasada los tres sensores, o V750 y V375 a la vez
1. Condicion mal implementada (and/or invertidos): falla solo si los tres, olvidando "V750 y V375".
2. MODIS solo sin pasada (que no puede correr en Windows pero si en Linux) queda como NOTA: falso verde aceptable? Debe documentarse.
3. V750 sin pasada y V375 con: NOTA, no FALLA; V375 sin pasada y V750 con: idem. Es el diseno, pero hay que ver que no se pierda del resumen.
4. Un sensor "sin pasada" por no ser noche (MIR solo nocturno) en la ventana: falso rojo.
5. Una pasada con datos pero con error en el record (sin pixel, vrp nulo) cuenta igual.
6. Sensor distinto en nombre (VIIRS_NOAA21) no contado.

## R3 (VV169-03): falla de cobertura (busqueda o descarga) de dia anterior al ultimo = NOTA; solo la del ultimo dia = FALLA
1. Dia X falla en la corrida de X, y el control (R1) mira solo ultimo dia y vispera: el dia X+1, el dia X es "la vispera" y cuenta; el dia X+2, X es "dia anterior" y cae a NOTA. Si en X+1 hubo cobertura de otras pasadas (de X+1) pero ninguna de X, R1 en X+1 solo exige que existan pasadas en [X, X+1] para cada sensor: una pasada de X+1 satisface "ultimo dia o vispera", y el hueco de X queda invisible. Perdida de un dia entero sin marca.
2. La falla de X en la corrida de X: si es FALLA ese dia, y el workflow solo notifica por issue que luego se cierra o se deduplica, y nadie mira. Depende de que el issue persista.
3. La ventana de 8 dias reprocesa dias anteriores; una falla de busqueda de X puede "curarse" en la corrida de X+1 (la ventana lo reintenta) pero si el reintento tambien falla es NOTA (ya es dia anterior).
4. Como se determina "dia de la falla": por el dia de la pasada, por el dia del log, por la fecha del run? Parseo de log con regex que no matchea el formato real (SEARCH_CMR_TIMEOUT, A108) -> cero matches = "sin fallas" (cero que no distingue no hay de no medi).
5. Falla de descarga sin dia asociado: se asigna a ultimo dia (falso rojo) o a ninguno (falso verde).
6. Control positivo ausente: no hay prueba que una falla del ultimo dia produzca FALLA con el log real de Actions.

## R4 (VV169-04): decidirSombra -> "pendiente" con corrida schedule queued/in_progress de <6 h; nrt-monitor sale sin tocar el issue; colgada >6 h alerta
1. Comparacion de edad con created_at vs run_started_at vs updated_at: una corrida en cola desde hace 20 h con run_started_at reciente parece nueva.
2. Zona horaria/parseo de fechas ISO con Z; comparacion de strings; Date.parse NaN -> comparacion con NaN siempre false -> o siempre pendiente (nunca alerta) o nunca pendiente.
3. Solo mira event == schedule; una corrida workflow_dispatch colgada no cuenta (correcto?) pero una schedule antigua completada con "success" de un dia anterior.
4. Estado "waiting"/"requested"/"pending" no incluido junto a queued/in_progress.
5. Paginacion: la lista de runs trae solo las ultimas N (per_page=1?), la corrida pendiente no sale.
6. "pendiente" no toca el issue: pero si el issue ya estaba abierto de antes por una falla real, y ahora hay corrida pendiente nueva, el issue no se cierra (correcto) ni se actualiza. Y si sale sin tocar mientras hay un issue viejo que deberia cerrarse. Verificar.
7. Corrida colgada >6 h: el 6 h es constante; el limite de GitHub para jobs es 6 h, asi una colgada >6 h ya fue cancelada por GitHub -> estado completed/cancelled; entonces el caso "queued >6 h" es el real (cola). Probar con un test que se alerte.
8. Reloj: la funcion usa Date.now() sin inyeccion (no testeable) o con ahora inyectado.

## R5 (VV169-05): la linea "K caidos en la ventana: N" sale siempre, en salida y en GITHUB_STEP_SUMMARY
1. Se emite solo en la rama de exito o solo cuando N>0 o solo en una de las dos salidas.
2. Una excepcion/exit temprano antes de imprimir (por FALLA) hace que no salga: "siempre" es falso en la rama de falla.
3. GITHUB_STEP_SUMMARY escrito con >> en un paso con `if: success()` o distinto del paso donde se calcula; o la variable de entorno no esta definida localmente y el script lo salta en silencio.
4. N calculado sobre otra cosa (records con K vs volcanes), o sobre records sin la ventana.
5. Salida con encoding: "caidos" con tilde en Windows cp1252 rompe (regla BAT/unicode) en la print de Python.
6. El "K caido" cuenta el estado actual, no uno guardado; si es no determinista.

## R6 (VV169-07): scripts/tachar_secreto_log.py tacha el token del log antes de subir el artefacto
1. El token se pasa por argv (visible en el log de Actions con `set -x`, en `ps`, y en el echo del comando del paso). GitHub enmascara secrets ${{ secrets.X }} en logs, pero un valor derivado (ej. url-encoded, base64, substring) no.
2. Token vacio: str.replace("", "***") inserta *** entre cada caracter y corrompe el log; o `if token:` lo omite y no tacha nada -> o el token vacio hace que el script pase sin error cuando el secreto faltaba (A: secret ausente = string vacio, regla 6 del workspace).
3. El artefacto se sube con `if: always()` pero el paso de tachado no corre si un paso anterior fallo (sin `if: always()`), o el tachado falla (exit != 0) y el upload se hace igual con el log crudo; o al reves, upload se omite.
4. cobertura.json u otros archivos subidos (no solo el log) no se tachan; glob que solo toma *.log.
5. Tachado solo exacto: el token puede aparecer en variantes (urlencoded, entre comillas, partido en lineas, en Authorization: Bearer ...). earthaccess .netrc o ~/.netrc subido.
6. El paso escribe el log tachado a disco, pero el original sin tachar queda en el directorio que se sube (se sube la carpeta entera).
7. Lectura con encoding errores (log con bytes invalidos) -> UnicodeDecodeError -> no se tacha y el paso falla o es ignorado.
8. El log completo de la corrida de Actions (no el artefacto) sigue teniendo lo que el paso imprima.
9. El test del tachado usa un token ficticio facil; no cubre tokens con caracteres especiales de regex si usa re.

## R7: pruebas 39/39 nuevas; 208/208 con guardias (4 saltadas preexistentes); nulo 32/32 mutaciones atrapadas por asercion, sin equivalentes; control sin mutar 39/39
1. "Atrapada" cuenta tambien mutaciones que hacen caer el test por excepcion/ImportError/sintaxis (A152: mutacion que cae no es atrapada); el script debe distinguir assertion de error.
2. Mutacion que no se aplica (patron no encontrado) cuenta como atrapada.
3. Los 4 saltados "preexistentes": confirmar contra 16d9e894d que son los mismos y no nuevos.
4. 32 mutaciones no cubren los 7 comportamientos de arriba (R3 dia anterior, R4 6 h, R6 token vacio).
5. Suites que corren con un hilo y tocan red/disco: ejecutar liviano.
6. Los conteos 39/208 dependen de seleccion de archivos; recontar.
7. Tests de workflow YAML parseados como texto: pasan por subcadena (A92).
8. Control sin mutar 39/39: ya puede ser sobre un arbol que cambio entre corridas (A112).
