# Verificador S159 PORTES: el código de VIIRS 750 de MIROVA portado a VIIRS 375 y a MODIS

2026-10-22. Contexto limpio; no encontré yo estos resultados, intenté romperlos. Sólo lectura: no toqué `pipeline/`,
`data/`, `frontend/` ni git; no despaché workflows. Scripts y salidas en esta carpeta
(`C:\vrp-trabajo\s159-pruebas\experiments\_s159\portes\verificador\`). Ojo: durante la verificación la carpeta
`portes/` desapareció de `C:\vrp-trabajo\s159-pruebas` (otra sesión cambió de rama); trabajé sobre la copia de
`C:\vrp-trabajo\s159-n\experiments\_s159\portes\` (la que nombra el informe) y la comparé byte a byte con el commit
despachado.

Ventana de todos los números: pasadas nocturnas, VIIRS 375 del 2026-04-01 al 2026-10-21, MODIS del 2026-03-01 al
2026-10-21, sin el 17 al 20 de octubre; muestra de `objetivos_portes.json` (150 + 150 + 10); artefactos del run
39712862945 en `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\`; referencia en
`D:\vrp-trabajo\temporales\s159_portes\ref\`; regla D-9 en modo SN; protegida = lectura A.

## Veredicto por afirmación

| afirmación | veredicto | lo que lo sostiene |
|---|---|---|
| 1. MODIS: 50/50, 39/42, negativos 2/57, razón 1,006, GANA contra K; B21 se hunde; geo 5 km degrada | **PARCIAL** | Detección, B21 y geo 5 km: CONFIRMADOS, idénticos con la tabla sola. El «0,04 % contra 0,76 %» y el **GANA** no: el intervalo no ve el estrato neg_resto (0 de 37, cada uno pesa 134); con la cota de Wilson del estrato el silencio del port puede llegar a 9,4 % y ΔE a +421: **NO RESUELTO**. |
| 2. VIIRS 375: razón 1,000 en 61, negativos 7/65, la caja decide lo débil de CC y Tupungatito | **CONFIRMADA con un matiz** | Razón reproducida (tabla sola: 1,000 en 57, 46 en banda) y propia de la pasada (control A109). Caja: los 11 recuperan píxeles a la distancia de MIROVA con su VRP en la variante sensible. El «0,9 % contra 3,85 %» tiene el mismo defecto de 1: cota honesta 8,5 %. |
| 3. Pierde 6 protegidas; post hoc son OCR de otra pasada; 0 de 30 | **PARCIAL** | Con la **tabla sola** el port pierde **0 de 29** protegidas sin cambiar ninguna regla. Pero de las 6: 3 son de la regla del centroide (el port sí tiene píxeles en la cumbre), 2 (279, 288) calzan con un píxel débil del cráter que producción ve y el port no, y la explicación «otra pasada» no se puede distinguir de «pérdida real» con estos datos; 1 (289) apoya «otra pasada». El «0 de 30» necesita dos cambios post hoc a la vez. |
| 4. Controles 391/391, 10/10, 149/149 | **CONFIRMADA** | 391 de 391 re-corrido por mí (162 con píxeles, 229 ceros en ambos lados); control positivo 162. Código local idéntico al commit despachado. |

## Hallazgos, de mayor a menor gravedad

### V-1. El «GANA» de MODIS y el silencio comparado con K descansan en un intervalo que no ve el estrato que manda

- **SCRIPT:SALIDA**: `v01_tabla_sola_y_ic.py` → `v01_salida.txt`.
- **Preguntas del instrumento**: (1) si el port publicara en 5 % de las noches limpias en que producción calla, la
  muestra de 37 lo dejaría pasar sin verlo con probabilidad 0,95^37 = 15 %, y el bootstrap estratificado de un
  estrato con 0 eventos da varianza 0: no lo vería nunca. (2) El cero del estrato no distingue «no enciende» de
  «encendería poco y no lo sorteamos».
- **QUÉ PASA**: las noches en que MIROVA no vio nada y producción tampoco publica son 5.093 en MODIS (3.348 en VIIRS
  375); se sortearon 38 (45) y cada una pesa unas 134 (74) noches. El port no publica en ninguna, y el bootstrap del
  pre-registro (estratificado por clase) re-sortea siempre ceros. Por eso el intervalo de ΔE (−58,8 a −29,5) y el
  de silencio (0 a 0,10 %) sólo miden la incertidumbre de los otros estratos.
  - MODIS, física: neg_resto 0 de 37, Wilson superior 0,094 → silencio ponderado del port hasta **9,37 %** (K 0,76 %);
    ΔE con ese límite **+420,8** (no −44).
  - VIIRS 375, física: neg_resto 0 de 45, Wilson 0,079 → hasta **8,47 %** (K 3,85 %). En la variante sensible el
    port sí enciende 1 de 45, o sea que el estrato puede encenderse.
  - Lo que se mantiene: R3 «REPRODUCE» por la regla pre-registrada (el intervalo contiene la tasa de K), la cuenta
    de ΔE es la del pre-registro, y la reproduje exacta (control positivo de mi script: los 12 números de
    `04_analizar_salida.txt` salen iguales).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. Si alguien adoptara el port por «gana a producción», el operador
  podría recibir puntos en noches sin actividad a una tasa que esta muestra no puede acotar bajo 9 %.
- **CÓMO REPRODUCIRLO**: `python -I v01_tabla_sola_y_ic.py`.
- **CONFIANZA**: CONFIRMADO (cuenta). Que el port encienda de verdad en neg_resto: SIN DATO.
- **GRAVEDAD**: 4. El veredicto MISSION de MODIS debe leerse NO RESUELTO hasta sortear unos 300 a 400 negativos de
  neg_resto (con 0 eventos en 400, Wilson ≈ 0,95 %, del orden de K).

### V-2. Dos de las 6 protegidas «perdidas» de VIIRS 375 pueden ser pérdida real de un píxel débil del cráter

- **SCRIPT:SALIDA**: `v05_pixel_K_vs_ocr.py` → `v05_salida.txt`; `v03_distancia.py`, `v03b_subconjunto.py`.
- **Preguntas del instrumento**: (1) control positivo de la prueba: en 28 de 28 alertas de la **tabla** (Láscar,
  Isluga, Tupungatito) la distancia de MIROVA calza a 1 km o menos con un píxel de producción medido al mismo punto
  (X0, Y0). (2) Record sin píxeles = SIN DATO (1 caso, Láscar 2026-08-17).
- **QUÉ PASA**: en Isluga y Tupungatito el cráter es la fuente persistente; las fuentes lejanas (a 12 a 24 km) son
  las que suben el VRP de la ventana sobre 1 MW. Producción y el port ubican esas fuentes lejanas en el mismo lugar
  (Isluga 2026-09-09: K a 21,5 y 24,0 km, port a 21,2 a 21,7 y 24,0 a 24,1 km), así que no es un error de
  geolocalización del port. Pero:
  - **Isluga 2026-09-09 06:06** (SNPP): OCR 0,81 km; producción tiene un píxel de 0,04 MW a **0,83 km** de (X0, Y0);
    el port no tiene nada bajo 21 km ni con la caja sensible.
  - **Tupungatito 2026-08-01 05:00** (SNPP): OCR 5,41 km; producción tiene un píxel de 0,016 MW a **5,07 km**; el port,
    nada bajo 14 km.
  - Tupungatito 2026-09-14 06:18: OCR 2,97 km, sin píxel de producción ni del port a esa distancia: apoya «otra pasada».
  - Isluga 2026-06-17 (NOAA-21, fuera del hito de SNPP), 2026-09-28 y 2026-10-03: el port **sí** tiene píxeles en la
    cumbre (0,67 a 1,41 km) y los pierde sólo porque el centroide del record sintético se corre con los lejanos.
  Como el cráter es la fuente de casi todas las pasadas, una distancia «de otra pasada» también caería en el cráter:
  la coincidencia no distingue las dos lecturas. La cabecera «Last Update» de la imagen per-volcán sí las
  distinguiría y no la miré. Además, la tabla muestra que MIROVA informa el píxel cercano aunque haya uno lejano más
  brillante (Láscar 2026-06-28 05:00: MIROVA 1,19 km, píxel más radiante del port a 22,4 km, el más cercano a 0,5 km),
  así que una fila de su propia pasada con distancia de cráter es posible.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Si el port reemplazara a producción, en esas dos noches el operador
  dejaría de ver un punto de 0,02 a 0,04 MW en el cráter; la magnitud protegida (1,3 a 1,9 MW) es de fuentes lejanas.
- **CÓMO REPRODUCIRLO**: `python -I v05_pixel_K_vs_ocr.py` (ids 279 y 288 de `objetivos_portes.json`).
- **CONFIANZA**: CONFIRMADO que la distancia OCR calza con un píxel que producción ve y el port no; SOSPECHA cuál de
  las dos lecturas es la verdadera.
- **GRAVEDAD**: 3. El «no son pérdidas de detección» del informe (P-5) queda en 3 de 6 confirmadas, 1 apoyada y 2
  sin resolver. No es pérdida de una alerta grande: es un píxel débil del cráter que el port no ve.

### V-3. Con la tabla de latest.php sola (pedido de Nicolás), VIIRS 375 no pierde ninguna protegida sin tocar reglas

- **SCRIPT:SALIDA**: `v01_salida.txt`, filas «tabla_sola».
- **Preguntas del instrumento**: (1) si el port no publicara nunca, el recall daría 0; da 29 de 29 y K 29 de 29. (2)
  Una pasada que la tabla no lista queda sin etiqueta y fuera de todo denominador (no hay pasadas cuyo OCR diga
  alerta y la tabla diga RUTINA: las 326 pasadas sólo OCR de VIIRS 375 de la población no tienen fila en la tabla).
- **QUÉ PASA**: las 10 protegidas sólo OCR de la muestra salen del denominador. Física, centroide (la regla
  pre-registrada): protegidas **29 de 29** (K 29), perdidas **0**; bajo 1 MW 28 de 40 (K 37); negativos 7 de 65 (los
  negativos no cambian); razón 1,000 [0,966; 1,011] en 57, 46 en banda. Sensible: 29 de 29, bajo 39 de 40 (K 37).
  MODIS: **idéntico** a la lectura combinada en todas las variantes (las 92 alertas están en la tabla).
- **Ojo**: el aviso de `calidad_referencia_mirova` que imprime el propio indexador dice para esta ventana «Decide:
  SOLO la tabla; el OCR se informa aparte» (A119); el pre-registro dejó decidir al OCR desde el 2026-06-13. La lectura
  con la tabla sola no es un rescate post hoc: es la regla vigente del proyecto, y bajo ella R1 da 0.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (cambia el veredicto R1 de VIIRS 375 de PIERDE PROTEGIDA a sin pérdidas).

### V-4. La magnitud coincide pasada a pasada, no sólo en promedio (control A109)

- **SCRIPT:SALIDA**: `v02_otra_pasada.py` → `v02_salida.txt`.
- **Preguntas del instrumento**: (1) si el port diera siempre un número parecido a la mediana de MIROVA, la razón
  contra otra pasada sería igual de estrecha que contra la misma; la medición lo vería. (2) Sin otra pasada de
  MIROVA en la noche, el par no entra (n informado).
- **QUÉ PASA**: el volcán cambia de una pasada a otra (MIROVA contra MIROVA de la misma noche: sólo 15 % en [0,8;
  1,25] en VIIRS 375). El port contra MIROVA de la misma pasada cae en banda 82 % (mediana |ln| 0,025); contra otra
  pasada de la misma noche, 15 % (|ln| 0,70). MODIS: 67 % contra 23 % (|ln| 0,13 contra 0,41). Con la tabla sola:
  VIIRS 375 80 % contra 20 %; MODIS igual. La coincidencia es del cálculo sobre el gránulo, no del estado del volcán.
- **Matiz**: que la mediana caiga en 1,000 depende del coeficiente de S14, que se calibró contra el VRP de MIROVA del
  OSF; la prueba real es la dispersión, no la mediana. En MODIS la coincidencia es más floja: sólo 19 de 89 a menos
  de 5 % (VIIRS 375: 35 de 61).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (refuerza la afirmación 2 y la magnitud de la 1).

### V-5. «Las 6 a 9 a 24 km» y el «0 de 30» mezclan casos y reglas

- **SCRIPT:SALIDA**: `05_posthoc_salida.txt` del frente (leído), `v03_salida.txt`.
- **QUÉ PASA**: el píxel a 9 km es de Láscar 2026-08-22, que no es una de las 6 (producción tampoco la publica). De
  las 6, sólo 3 tienen todos los píxeles lejos (12,5 a 24 km); las otras 3 tienen cúmulo en la cumbre. El «0 de 30»
  sale de quitar las 14 filas dudosas **y** cambiar el centroide por el píxel más cercano; con sólo quitar las filas,
  queda 1 de 30 (Isluga 2026-06-17, NOAA-21, fuera del hito). El autor sí comprobó que el cambio de regla no enciende
  negativos (7 de 65 con las dos reglas, confirmado en su salida).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### V-6. Lastarria 2026-05-13 06:36: alerta débil cercana que el port no ve con ninguna caja

- **SCRIPT:SALIDA**: lectura de `resultados_*.json` (id 272), `05_posthoc_salida.txt`.
- **QUÉ PASA**: MIROVA tabla 0,07 MW a 1,19 km; el port da 0 píxeles con la caja física y de celdas, y con la
  sensible encuentra 2 a 9,6 a 9,8 km con 0,158 MW (no es la de MIROVA). Es la duodécima alerta bajo 1 MW con 0
  píxeles; no es de Cordón Caulle ni Tupungatito y la caja no la explica.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (una alerta de 0,07 MW, sobre el corte D-9).

## Caminos que intenté y no rompieron nada

- **¿El port eligió parámetros mirando el resultado?** El pre-registro (commit 6fb94d1c3, 02:35:03Z) es anterior al
  humo (run 39712215283, 02:35:23Z); entre el humo y el lote (0e18e1053) sólo cambió una línea del yml (`SOLO`
  vacío). `mirova_port.py`, `probe_portes.py`, `objetivos_portes.json` y `PREREGISTRO.md` locales son idénticos al
  commit despachado (comparación byte a byte por la API). La esquina de la grilla de 375 viene de los TIF de MIROVA
  (geometría, no VRP).
- **¿Banda 22 y MxD03 cambiados a la vez?** No: `probe_portes.py:344-348` corre cada variante cambiando un solo
  factor (B21 con MxD03; geo de 5 km con B22).
- **¿Es un error de geolocalización del port?** No en los casos lejanos: producción, con su propia lectura, pone
  los mismos píxeles a la misma distancia (V-2).
- **¿La caja decide de verdad?** Sí: en los 11 casos de Cordón Caulle y Tupungatito la caja sensible encuentra
  píxeles a la distancia de MIROVA (CC 7,1 a 8,0 km contra 7,3 a 8,2; Tupungatito 4,3 a 5,4 contra 4,9 a 5,4) con su
  VRP (0,439 contra 0,44; 0,37 contra 0,40; 0,627 contra 0,62).
- **¿Los jobs fallidos del lote dañaron resultados?** Los dos jobs en rojo (VIIRS 375 5 y MODIS 3) terminan con
  «pasadas sin procesar: 1»: son los dos SIN DATO declarados; las demás pasadas de esos jobs tienen estado ok.

## VERIFICADO LIMPIO

- **Envoltorio = oráculo**: `python -I 03_control_v750_sin_red.py --art D:\vrp-trabajo\temporales\s159_n\run_39682867040`
  da 391 de 391 en npix y VRP; 162 de esas 391 tienen píxeles (las otras 229 son cero contra cero); con config de 375
  cambia en 162 (`v04_control_391_salida.txt`).
- **CTL750 10 de 10** (`04_analizar_salida.txt` §2, leído): 7 con píxeles, 3 cero contra cero.
- **K re-corrido = publicado 149 de 149** en los dos sensores: leído en la salida y en el código que lo compara
  (`04_analizar.py:166-184`); no lo re-corrí (necesita el runner).
- **Lecturas del frente**: mi script reproduce exactos R1 a R4 y ΔE de la variante física en los dos sensores.
- **MODIS con la tabla sola** = combinada en las cinco variantes.
- **Disco**: C: 14 GB y D: 12 GB libres al inicio.
