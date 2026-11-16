# VERIFICACION V5B: frente F5b (lamina PNG Latest10NTI como vara de posicion)

## 1. Encabezado

- Hora del servidor al cerrar: domingo 2026-11-08 14:16 UTC (header Date de la API de GitHub, leido en esta sesion).
- Commit de medicion: datos y codigo de vara en 752d348bc67190e53b610989877e2405d238a1bc (`git show` para Chillan JSON,
  frontend/index.html, frontend/cambio_detector.js, volcanoes.yaml y scripts/banco_paridad.py). Worktree de trabajo en 14dfb0d2e.
  Insumos verificados por sha256 contra el prompt: snapshot consolidado f833bfdef7c3fc5f, latest dee768374b84d49b, OCR 577a336e76383a67
  (salida: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5b\m6_recuentos.out.txt).
- Modelo: Claude Opus 5.5. Esfuerzo real: SIN DATO.
- CARPETA: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5b\
- caminos.md sellado antes de abrir nada citado: sha256 1856f3a9c61267fae118f1ab9efa63cf6459fb18764c7f1bc21209852b614313, 13:57:43 UTC.
- No mire: INFORME.md ni hallazgos.csv de F5b; no corri p8_clasificar completo (lo re-derive con m1 sobre sus paneles); no vi el
  poller de mirova-tif-archive; no contraste el indice png_index.csv con el remoto vivo; no audite la parte F5 (radios) ni el predicado del tablero mas alla de las 4 pasadas de 351.

## 2. En una pantalla

La georreferencia de la lamina vale fuera de muestra (VIIRS 375: 17 de 17 cuando el maximo del TIF reproduce la tabla; nulo azar 1 %), aunque la regla se ajusto y se valido sobre los mismos 4 casos.
Pero el selector de pixel falla justo en la erupcion: borra la mancha caliente saturada por confundirla con «sin dato» (35 de 303 laminas; Chillan V750 17 de 55, MODIS 12 de 22).
De las cuatro de 351, tres V750 son ese artefacto: nuestro punto cae dentro de la mancha, a 0,1 a 0,3 km de su celda mas cercana; la cuarta (V375 18-oct 05:06) es un empate entre dos saturados de una misma mancha.
Lo unico que queda de 351 es radial y sale de la tabla, sin la lamina: la Distancia_km V750 de MIROVA (2,12 a 2,37 km) dista 1,8 a 2,3 km de nuestro centroide, y su propia tabla V375 de esa misma pasada dice 1,06 a 1,19 km.
Veredictos: 351 CONFIRMADO EN PARTE (la conclusion «foco a 1 a 2,5 km» no se sostiene); 352 EN PARTE; 353 CONFIRMADO; 354 CONFIRMADO; 355 CONFIRMADO.

## 3. Veredicto por afirmacion

Las dos preguntas del instrumento y los controles van en el encabezado de cada script (m1 a m8). Todos los numeros salen de esos scripts, de sus salidas `.out.txt` al lado, en CARPETA.

### 351. Cuatro protegidas VIIRS de Chillan clase iii: foco de MIROVA a 1,0 a 2,5 km del punto publicado

- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad 2 (auditor 3).
- Lo que SI: publicamos en las 4 (predicado con node sobre frontend/index.html de 752d348bc da publica=1, y control far=0: m5_detalle.out.txt); final_hotspot de las 4 coincide con our_lat/lon; las filas de tabla son ALERTA_TERMICA Moderado, 21,25 / 29,35 / 15,26 / 14,02 MW (m5, m6); distancias que el auditor reporta reproducidas (1,02 y 2,16 km).
- Lo que NO: la conclusion «el foco de MIROVA esta a 1 a 2,5 km» y la etiqueta (iii) «otro foco» no se sostienen en ninguna de las cuatro:
  - Las 3 V750: lum del pixel elegido 196,7 / 237 / 171,7 contra 255 en la mancha. El metodo borro la mancha (componentes blancas de 48, 30 y 28 px, area >= 20 px, f5b_lib.py l. 118 a 122) y eligio un pixel de su borde. Conservando la mancha: nuestro punto a 0,14 / 0,106 / 0,292 km de su celda mas cercana (m1_mancha.out.txt), centroide 0,78 / 0,65 / 0,48 km, clase i. Se ve en las laminas: C:\Users\nmend\vrp-temporales\s175_audit\v5b\crops\VIIRS750_2026-10-10_0654.png y VIIRS750_2026-10-16_0642.png, VIIRS750_2026-10-29_0642.png (circulo rojo en el borde de la mancha blanca, circulo amarillo = mirova_center dentro de ella).
  - V375 2026-10-18 05:06 (la unica sin mancha grande borrada): dos componentes saturadas (lum 255), 1 px en (66,63) y 6 px en (67,65) a (68,66), parte de una misma mancha contigua (mapa de luminancia en m5_detalle.out.txt). np.argmax toma la primera en orden de barrido; la mayor contiene nuestro punto a 0,19 km. La saturacion no permite decidir cual es el maximo.
- Lo que queda, medido sin lamina (m8_cota_tabla.out.txt, valido solo si el origen de la tabla es mirova_center): la Distancia_km V750 es 2,12 a 2,37 km y nuestro punto esta a 0,11 a 0,30 km de mirova_center, cota inferior 1,8 a 2,3 km; V375 1,0 km. Pero la propia tabla de MIROVA en la MISMA pasada da V375 1,06 a 1,19 km contra V750 2,12 a 2,37 km (m6, seccion de la tabla): su distancia V750 no es una posicion estable. Las cuatro pasadas tienen zenit 48 a 67 grados (registros JSON), con manchas de 7 a 11 celdas V750: el pixel de la tabla es un extremo de la misma mancha en la direccion de barrido. Hipotesis de fondo: SOSPECHA, no medida pixel a pixel.
- «6 MODIS (iii) sin validar»: cuenta correcta (m6); con la mancha conservada 2 pasan a i y 4 quedan iii, pero el control MODIS (tolerancia 3 km) tiene nulo uniforme 31 % y no decide (ver 354).
- Caminos del sello probados: 351a, 351b, 351c, 351e, 351f, 351g (tolerancia fija de F5, no ajustada aca), 351d y 351i (distancia sin lamina), 351j (V5B-04). C1 y C3: V5B-03. C2: V5B-04. C4: una celda en la tolerancia de F5, y a 1 km V375 el error de 1 celda no resuelve el caso. C5: TIF de referencia EPSG:4326 (crop351.py, salida en sesion), sin desajuste de geometria observado fuera de muestra. C6: V5B-01 y V5B-02. C7: crops. C8: sha256. C9: m5.

### 352. Control de distancia falla por poco en 30 protegidas de Chillan

- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad 2 (auditor 2).
- CONFIRMADO: 30 protegidas VIIRS con control fallido, 22 V375 y 8 V750 (m6; mas 1 MODIS fuera del conteo); la tabla nunca dice 0 en esas 30 (minimo 0,84 V375, 1,06 V750); 0,018 km de la celda central reproducido (m1); nuestro punto a 0,36 km mediana en V375; yaml base con mirova_center a vent 0,385 km (m6).
- NO como esta escrito: la mancha cae en la celda central solo en 14 de 30 (10 de 22 V375, 4 de 8 V750; m4); la tabla va de 0,84 a 2,52 en V375 y 1,06 a 3,18 en V750, no «0,84 a 1,35»; «por poco» vale para 26 de 30 (19 V375 y 7 V750 con |d - tabla| <= tol + 1 celda), pero V750 tiene p50 1,71 km y maximo 3,80 km; 0,36 km es solo V375, V750 da 0,62 km.
- Mitad del problema es V5B-01: conservando la mancha el control pasa en 18 de 30 (11 V375 y 7 V750), con la salvedad de que «alguna celda de la mancha» es mas blando que «el pixel».
- La disyuntiva del auditor (origen o pixel) sigue sin resolverse: barrido de origen con mitad de ajuste y mitad de prueba (m4): Chillan V375 centro da 0,13 / 0,07 de acierto exacto, el mejor offset (3,-1) da 0,57 / 0,37, y en Lascar V375 el centro es el mejor (0,56 / 0,38, control positivo). Ningun origen unico explica Chillan.

### 353. Sin laminas MODIS 12 de 46 dias y VIIRS 2 a 3

- VEREDICTO: CONFIRMADO. Mi gravedad 2 (auditor 3).
- 12 dias comunes a los 11 volcanes (23 a 30-sep y 8 a 11-oct), igual por captured_at y por last_modified; VIIRS 2 a 3 dias (m3_cobertura.out.txt; p10 re-corrido, salida identica). Ningun hueco se explica por filas omitidas: en la ventana solo hay 105 omitidas y son de 5 a 7-nov.
- Irrecuperable, comprobado con OCR por otro camino (353c): la primera lamina tras el hueco, 2026-10-12 15:24 Chillan, cubre hasta 10-10 12:05, un panel antes de 07:40 (m3b_paneles_12oct.out.txt). Lascar 10-12 cubre hasta 10-10 01:10 y 10-01 hasta 09-29 07:15: el 25-sep y el 8-oct no aparecen.
- La atribucion «el archivo no capturo» queda sin probar en su causa: la tabla de MIROVA tiene 562 filas MODIS en esos dias (hay datos) y las laminas VIIRS si se capturaron esos dias, pero ninguna fila MODIS de ningun tipo tiene captured_at en el hueco. Si MIROVA no regenero la lamina o si fallo el poller: SIN DATO (poller fuera del repo).

### 354. La lamina MODIS no sirve de vara de posicion con el pixel mas claro

- VEREDICTO: CONFIRMADO. Mi gravedad 2 (auditor 2).
- Numeros reproducidos: 5 de 7 a 3,6 a 5,8 km; el TIF no reproduce la distancia en 4 de 7; 15 i, 6 iii, 3 iv (m2_validacion.json, m6).
- Por otro estrato: 10 alertas MODIS nuevas de Lascar, Chaiten y Villarrica sacadas de la tabla, sin mirar resultados: 4 de 10 a <= 3 km (m2d_modis.out.txt). Nulo azar en inner 21,5 %, otros paneles 27 %: apenas sobre el azar.
- Dos salvedades. La vara es dudosa: el TIF MODIS del archivo es la banda B21 en radiancia, no NTI (tif_index.csv columna band), y su maximo no reproduce la tabla en 4 de 10 tampoco. Y en estos casos debiles (0,14 a 1,83 MW) el panel casi no muestra el foco (lum_max 73 a 236); no se puede extrapolar a Chillan fuerte, donde hay mancha blanca visible (C:\Users\nmend\vrp-temporales\s175_audit\v5b\crops\chillan_modis_1017.png).

### 355. Lamina MODIS redondea el VRP a entero y marco gris

- VEREDICTO: CONFIRMADO, y mas amplio de lo escrito. Mi gravedad 1 (auditor 1).
- Lascar 2026-10-26 07:55: lamina «VRP =0 MW» con marco gris y cabecera VERY LOW (C:\Users\nmend\vrp-temporales\s175_audit\v5b\crops\lamina_355.png); tabla 0,29 MW ALERTA_TERMICA Muy Bajo (p9 y snapshot).
- El redondeo a entero tambien ocurre en VIIRS 750, no solo MODIS (29, 15, 14 en los crops de 351; VIIRS 375 lleva dos decimales).
- 10 aciertos V750 con marco gris (p13 re-corrido identico), todos de 0,18 a 0,82 MW; los verdes V750 parten en 1,03 MW (m7_marco_vrp.out.txt): el gris V750 sigue un corte de VRP, no marca sin alerta. V375 mantiene verde hasta 0,06 MW.

## 4. Hallazgos propios (V5B-01 en adelante)

TÍTULO: pixel_mas_claro borra la mancha caliente como si fuera «sin dato»
ARCHIVO:LÍNEA: experiments\_s175_audit\f5b\f5b_lib.py l. 118 a 122 (usado por p8_clasificar.py l. 128)
QUÉ PASA: en una erupcion el foco satura la paleta y se ve como mancha blanca de varias celdas; el codigo trata toda componente blanca de 20 px o mas como «sin dato» y la borra, y elige un pixel del borde. Afecta 35 de 303 laminas y se concentra en la erupcion: Chillan V750 17 de 55, MODIS 12 de 22.
CÓMO SE VE EN EL DASHBOARD: invisible (defecto del instrumento de auditoria); invalidaria afirmaciones de posicion sobre Chillan.
CÓMO REPRODUCIRLO: cd C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5b && python -I m1_mancha.py (Chillan VIIRS_NOAA20_750 2026-10-10 06:54 UTC: lum A 196,7, lum B 255, mancha 48 px)
CONFIANZA: CONFIRMADO
GRAVEDAD 1-5: 3

TÍTULO: En una mancha saturada el «pixel mas claro» es el primero en orden de barrido
ARCHIVO:LÍNEA: experiments\_s175_audit\f5b\f5b_lib.py l. 128 (np.argmax sobre paleta saturada a 255)
QUÉ PASA: varios pixeles de una mancha llegan a 255 y la lamina no los ordena; argmax elige el de la fila superior. Eso define el foco en 2026-10-18 05:06, y cuantas veces pasa no se contó por completo (3 de 69 V375 y 2 de 22 MODIS en Chillan tienen 2 componentes en inner).
CÓMO SE VE EN EL DASHBOARD: invisible.
CÓMO REPRODUCIRLO: python -I m5_detalle.py, seccion (a), VIIRS_NOAA21 2026-10-18 05:06 UTC
CONFIANZA: CONFIRMADO
GRAVEDAD 1-5: 2

TÍTULO: La regla se ajusto y se valido sobre los mismos 4 casos; fuera de muestra la georreferencia aguanta, el maximo del TIF no siempre
ARCHIVO:LÍNEA: experiments\_s175_audit\f5b\p3_regla_fija.py l. 36 a 41, l. 121 a 159; p7_mas_casos.py l. 31 a 36; f5b_lib.py l. 5 a 7; m2_validacion.out.txt
QUÉ PASA: p3 ajusta margenes por correlacion en los 4 casos y p7 valida esos mismos 4 mas 7 MODIS de Lascar (2 pasan); los 3 casos nuevos de p7 fuera de Lascar (Villarrica MODIS y V750, Puyehue V750) no tenian TIF. El uno afuera de p3 valida otra variante de regla (2 casos Lastarria son la misma grilla), y la regla final (centro de linea + DX 1,5) no paso por uno afuera. En 41 casos nuevos elegidos sin mirar: V375 20 de 25 (17 de 17 cuando el TIF reproduce la tabla) y V750 9 de 16 (2 de 2 cuando reproduce); correlacion panel-TIF p50 0,96 y 0,92; ninguno ejercita la mascara (no hay manchas grandes en la muestra).
CÓMO SE VE EN EL DASHBOARD: invisible.
CÓMO REPRODUCIRLO: python -I m2_validacion.py; python -I m5_detalle.py seccion (d)
CONFIANZA: CONFIRMADO
GRAVEDAD 1-5: 2

TÍTULO: La clase i casi no separa pasadas: con nuestro punto de otra pasada sigue siendo i en 73 % (V375) y 77 % (V750)
ARCHIVO:LÍNEA: m4_nulo_origen.out.txt, seccion (1)
QUÉ PASA: el foco y nuestro punto quedan cerca del crater en todas las pasadas; (i) dice «no esta en otro lado del inner», no «mismo foco esta noche». Observado 95 % y 94 %, nulo uniforme 2 % y 7 %, nulo permutacion 73 % y 77 %. Denominador: 116 V375 y 50 V750 con control A ok, ventana 2026-09-22 a 2026-11-06.
CÓMO SE VE EN EL DASHBOARD: invisible.
CÓMO REPRODUCIRLO: python -I m4_nulo_origen.py
CONFIANZA: CONFIRMADO
GRAVEDAD 1-5: 2

TÍTULO: El control sintetico de p8 no paso y su docstring dice lo contrario
ARCHIVO:LÍNEA: experiments\_s175_audit\f5b\p8_clasificar.py l. 21 a 22; experiments\_s175_audit\f5b\p8_clasificar_t6_max8.out.txt l. 8
QUÉ PASA: la cabecera declara que mover nuestro punto 3 km da (iii); la salida dice «-> i 1.499» (MODIS, tolerancia 3 km). El control elegido no podia fallar, y no se guarda en p8_clases.json.
CÓMO SE VE EN EL DASHBOARD: invisible.
CÓMO REPRODUCIRLO: leer p8_clasificar_t6_max8.out.txt l. 8
CONFIANZA: CONFIRMADO
GRAVEDAD 1-5: 2

## 5. SEGUIMIENTOS (fuera del eje)

- p7 pasa `nan_tif` de la pasada a pixel_mas_claro y p8 no (f5b_lib.py l. 123, p8_clasificar.py l. 128): validacion y uso no son el mismo camino. SOSPECHA de poco efecto.
- p8 no tiene control de identidad al lado de los (iii) y deja un docstring con su resultado esperado, no observado: V5B-05.
- Quien orquesta debe decidir si F5b se re-corre con la mascara corregida antes de publicar conclusiones de posicion de Chillan.

## 6. VERIFICADO LIMPIO

- Georreferencia y regla de recorte fuera de muestra (m2): V375 corr p50 0,96; nulo azar en inner 1 % a 5 %, otro panel 21 % a 33 %; vara: maximo del TIF de la misma pasada con el mismo pareo que p7.
- Pareo panel a pasada: las etiquetas de los paneles de las 5 pasadas revisadas coinciden con la hora (crops, C:\Users\nmend\vrp-temporales\s175_audit\v5b\crops\).
- Reproduccion: p13 y p10 re-corridos dan salida identica (rerun_p13.out.txt, rerun_p10.out.txt).
- Insumos: sha256 del prompt, yaml copia igual a base, our_lat/our_lon iguales a final_hotspot (m6, m5).
- Publicacion de las 4 de 351: predicado ejecutado con node, control far negativo (m5).

## 7. SIN DATO

- Causa del hueco MODIS (poller o MIROVA).
- Si el indice de archivo (copia ola 0) coincide con el remoto vivo hoy: no se consulto, la copia termina 2026-11-07.
- Origen real de la Distancia_km de MIROVA en Chillan (ningun offset unico explica V375; en los dos .m de OSF de VIIRS 750, un grep de dist, sqrt, center y summit no mostro ese calculo; SOSPECHA de que vive en otro codigo).
- Distancia real del pixel de MIROVA dentro de la mancha: solo la tabla la acota, y no hay TIF.
- Verificacion de MODIS sobre pasadas fuertes: no hay TIF despues del 22-sep.

## 8. FUERA DE ALCANCE

- Corregir f5b_lib, p8 o las clases de F5b; cambios a produccion o al tablero; decidir si la lamina reemplaza al TIF.
