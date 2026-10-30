# Caminos por los que cada afirmacion podria estar mal (escritos antes de abrir ningun archivo citado ni INFORME.md)

Verificador corto, ronda 3, delta f743d7b8f..cd8b7074f.

## T1 (VR2-01 y VR2-02): revision exige record de la via por dia/volcan/sensor o prueba de no-pasada de ESTA corrida

C1.1 La "cobertura de esta corrida" solo cubre los dias que la corrida proceso (dias nuevos). Un dia anterior de la ventana sin pasada real no tiene prueba en esta corrida: falso rojo permanente hasta salir de la ventana de 8 dias.
C1.2 La cobertura sobrescribe en vez de acumular: el artefacto de ayer no existe hoy.
C1.3 Dias anteriores a 2026-11-03 no se excluyen: el primer dia de la ventana (p.ej. 2026-10-26..10-31) cuenta como perdido, FALLA el 3-nov y los siguientes 7 dias.
C1.4 Comparacion de fechas por string vs datetime con zona: un record a las 23:59 UTC o con "Z" / "+00:00" / sin tz cae en otro dia, o el parse falla.
C1.5 Suomi NPP: tras su cese (fecha?) se exige record de VIIRS_SNPP para todos los dias: falso rojo permanente. O al reves, la exclusion se aplica a fechas anteriores al cese (falso verde).
C1.6 Dia con granulos pero todos "sin_grilla" o fuera del volcan: se exige record cuando no puede haberlo (falso rojo); o, al reves, "sin_grilla" se acepta como prueba de no-pasada aunque sea una falla (falso verde).
C1.7 "Algo escrito de la via" se satisface con un solo record de un solo volcan: falso verde si 10 de 11 volcanes no escribieron nada (depende de la revision por volcan/sensor: ver C1.8).
C1.8 La revision corre dentro de cada job matriz (1 volcan) o en un job agregador? Si el job agregador ve solo artefactos de un volcan, el "cada volcan" no se cumple.
C1.9 La prueba de no-pasada se toma de la cobertura pero la cobertura la escribe el mismo codigo que debia fallar (circular): cobertura vacia = "no hubo pasada" = verde (falso verde).
C1.10 Ventana desde 2026-11-03 con hora actual: "hoy" aun incompleto (el cron 15:00 UTC no ha visto pasadas de la tarde) se exige completo; frontera de 6 h.
C1.11 Un record de K (no de la via) en el JSON cuenta como record de la via si la clave que distingue es opcional o falta.
C1.12 Mismo datetime-dia pero otro sensor (MODIS vs VIIRS750 vs VIIRS375) satisface a los tres.
C1.13 El JSON de datos tiene records de dias futuros / duplicados que satisfacen dias distintos.

## T2 (VR2-03): tachado falla cerrado, tacha variantes URL y JSON

C2.1 En el yml el paso de upload tiene `if: always()` o no depende del paso de tachado (continue-on-error, orden): el artefacto se sube igual con el token.
C2.2 El tachado sale 1 pero el yml tiene `|| true` o `set +e`.
C2.3 El tachado imprime el token (en el mensaje de error, en un diff, en un repr de excepcion, en una traza).
C2.4 Variantes que no cubre: base64, percent-encoding del token, mayusculas, token partido por salto de linea, token en query-string con `%3D`, JSON con escape unicode (\uXXXX), token dentro de una cadena larga con comillas escapadas.
C2.5 Token vacio: el regex vacio tacha todo o nada; la guarda de token vacio sale 0 (falso verde) o 1 (falso rojo cuando el secreto legitimamente no esta).
C2.6 strip() del token: un token con espacio/salto final no se tacha si no se hace strip; la mutacion de quitar strip no es atrapada.
C2.7 Archivos binarios o de otra codificacion no se leen / se saltan sin falla.
C2.8 El tachado cubre solo algunos archivos del artefacto (no subdirectorios, no .json.gz).

## T3 (VR2-04): JSON/cobertura corruptos o --desde-utc vacio dan FALLA con mensaje, sin traceback; "K caidos" sale igual

C3.1 Una excepcion distinta de JSONDecodeError (UnicodeDecodeError, TypeError por raiz lista en vez de dict, KeyError, AttributeError por null) escapa con traceback.
C3.2 JSON valido pero de forma inesperada (records = null, datetime null, datetime no string) -> traceback.
C3.3 --desde-utc con formato invalido (no solo vacio), con espacios, solo fecha, con zona.
C3.4 Archivo ausente vs vacio (0 bytes) vs truncado.
C3.5 La linea "K caidos" se imprime despues de la revision y una salida temprana por FALLA la salta; o sale pero con exit code distinto.
C3.6 El codigo de salida es 0 pese al mensaje FALLA.
C3.7 Mensaje FALLA se imprime pero a stdout y el traceback a stderr tambien.

## T4 (VR2-05): cuatro pruebas existen y atrapan las mutaciones

C4.1 Las pruebas existen pero pasan igual si se muta (frontera 6 h: < vs <=, 6 vs 5/7; falla sin fecha: continue en vez de FALLA; strip(); guarda de token vacio).
C4.2 Las pruebas prueban una copia de la logica, no el codigo real (reimplementan).
C4.3 Las pruebas no se ejecutan en CI (marcadas skip, fuera del patron de pytest).
C4.4 Una de las "cuatro" pruebas cubre solo el camino feliz.
C4.5 La frontera de 6 h se prueba en un punto lejano (5 h y 7 h) y no en 5:59/6:00/6:01.

## T5: cifras de pruebas y del nulo

C5.1 56 de 56 / 225 de 225 / 4 saltadas: la cifra viene de otro arbol (no el commit cd8b7074f) o con el arbol sucio.
C5.2 Conteo de saltadas: skips preexistentes vs nuevas; conteo no incluye xfail.
C5.3 Nulo m4_mutaciones_r3.py: "48 de 48 atrapadas por asercion" lee el XML de pytest; si una mutacion rompe la importacion (error de coleccion) el XML tiene error y no failure: el script debe contar solo aserciones; revisar que la clasificacion no cuente errores de sintaxis como atrapadas; revisar que el control positivo (mutacion que seguro cae) y el nulo (sin mutar = 0 fallas) existan.
C5.4 Mutaciones que son equivalentes o que no tocan T1.
C5.5 El nulo muta una copia pero las pruebas importan del arbol original (no ven la mutacion -> las 48 "atrapadas" serian por otra razon).
C5.6 Estado del arbol: arbol/ difiere de cd8b7074f (hash de archivos).

## Otras (propias de un delta de arreglos)

C6.1 El delta toca pipeline/ (congelado).
C6.2 El delta introduce regresion en lo que R2 ya habia aprobado (VR2-06...).
C6.3 Cita de lineas del INFORME que ya no corresponde al codigo.
C6.4 Nuevas rutas por las que el workflow queda verde con algo faltante (falso verde) o rojo sin falla real (falso rojo), p.ej. el paso de revision se salta con `if:` en dias sin cron o en workflow_dispatch.
