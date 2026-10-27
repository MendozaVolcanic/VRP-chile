# Lista de caminos de falla (escrita ANTES de leer probar_evaluar_v750a.py), 2026-10-24 ~23:45 hora local

Fuente leída hasta aquí: PREREGISTRO_V750A.md, evaluar_v750a.py, analizar_v750b.py, LECTURAS_EVALUAR_V750A.md.

C1  §7 dice K = producción "en todas las pasadas ok"; el analizador tolera 1 % de pasadas distintas (MAX_K_DISTINTO heredado de V750-B) y las saca de todos los brazos. Lectura no documentada en LECTURAS.
C2  leer_equivalencia_local: cuenta líneas con la subcadena "atrapada por aserción" (una línea "NO atrapada por aserción" también la contiene), "caída" por subcadena, sin ligar la salida al módulo ni a un sha; 5 en vez de 6.
C3  §6.1 en el runner: la máscara es el conjunto (fila, col) de `pixeles`; un paquete {} o sin `pixeles` cuenta como cero detecciones en P y en O; banda_triangulacion la pone el productor y exime máscara y VRP sin tope.
C4  P2 / M: el nombre de los estratos que devuelve decidir_estrato ("NEUTRO", "MEJORA", "SIN SUSTRATO") y las claves que pide el par ({k,d,m,clave,bloque}) tienen que coincidir con evaluar_d25.py; control del gemelo depende de la cadena "NEUTRO".
C5  p2(): bloques con suma 0 entran como ceros a la prueba de signos; `etiqueta` en canal "todo"/"tabla" deja "neg" igual para ambos canales.
C6  §6.2 P1 aplicado sólo a protegidas que K publica (L1) y sobre `oks` (sin las pasadas K≠producción).
C7  Veredicto: "INFORMAR POR CANAL" sólo si TODAS las fallas son P2 en O; P2 SIN SUSTRATO cuenta como falla; el exit code es 0 en NO CUMPLE.
C8  Sombra: BLOQUEA pasa (L3); SIN SUSTRATO sólo veta con P1; nulo del contador con rec_p = slim(record) y primary_cluster None => TypeError.
C9  S-1: decidida_por_escena usa `>` estricto en los dos tests y el u del pase/zona de la celda de A; no se verifica que la celda decisiva de P y O sea la misma celda; el diagnóstico faltante es SIN DATO que no cierra nada (las protegidas con S-1 SIN DATO sólo se listan).
C10 §5 pide "todo por tramo de cenit, por volcán y por canal": sólo se imprime el canal que decide, sólo conteos (no P2, M, razón por volcán/canal).
C11 P-sinfiltro: neutraliza distance_class y centroid_dist_km; si el predicado del tablero usa otros campos de distancia, la neutralización es incompleta.
C12 etiquetas: ventana T/O por comparación de cadenas con FRONTERA_OCR; lab/decide/protegida vienen del generador.
C13 Cobertura: motivo_sin sólo cuenta part None / diurna / falta_brazo; un `estado` None rompe `[:40]`.
C14 Robos de la gemela: Kgemelo/Kgeo con `record` ausente => KeyError (Kgeo opcional).
