# S159, frente PORTES: el código de VIIRS 750 de MIROVA, portado a VIIRS 375 y a MODIS

2026-10-22 (UTC). Worktree `C:\vrp-trabajo\s159-n`, rama `s159-portes`. Sólo lectura: no se tocó `pipeline/`, `data/`
ni `frontend/`. Pre-registro commiteado **antes** del primer disparo: `PREREGISTRO.md`, commit `6fb94d1c3`. Workflows
de sólo lectura (rama de disparo `s159-portes-disparo`, no se mergea; autentica sólo con `EARTHDATA_TOKEN`): humo
39712215283 (8 pasadas, sólo para probar la cadena) y lote **39712862945** (310 pasadas: 150 VIIRS 375, 150 MODIS, 10
de control de VIIRS 750). Artefactos en `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\`; resultados y
bitácoras copiados a `C:\vrp-trabajo\s159-n\experiments\_s159\portes\run_39712862945\`.

## En una pantalla

1. **MODIS: el mismo código, con la banda 22 primaria y la geolocalización del MxD03, reproduce lo que MIROVA
   publica.** 50 de 50 alertas protegidas, 39 de 42 alertas bajo 1 MW, 2 de 57 negativos limpios (ponderado 0,04 %,
   contra 0,76 % de producción), razón de magnitud **1,006 [0,889; 1,143]** en 89 alertas. Producción (K) en las mismas
   pasadas: 48 de 50, 32 de 42 y razón 0,516. Contra K, el port **GANA** (ΔE −44, IC 95 % −58,8 a −29,5). La magnitud
   queda PARCIAL por la regla pre-registrada: 66 de 89 (74 %) dentro de [0,8; 1,25], a un caso del 75 %.
2. **La banda 21 primaria en el mismo código hunde la detección** (20 de 92 alertas, 28 protegidas perdidas, razón
   0,794), y la geolocalización interpolada de la grilla de 5 km (la de producción) degrada la magnitud (0,903 con la
   mitad fuera de banda) y pierde 3 protegidas. Es la primera medición contra MIROVA de D21 y de la geolocalización de
   MODIS con el código de MIROVA.
3. **VIIRS 375: la magnitud se reproduce al centésimo**: razón **1,000 [0,966; 1,019]** en 61 alertas (48 dentro de
   banda), contra 0,651 de K. La detección con la caja del mismo tamaño en metros que la de 750 pierde alertas débiles
   de Cordón Caulle y Tupungatito, cuya anomalía MIROVA ubica a 5 a 8 km (fuera del ROI de cumbre de ±2,6 km); con el
   ROI de escena en umbrales de cumbre el recall bajo 1 MW sube de 31 a 42 de 45 (lo mismo que N-3 en 750).
4. **Las 6 protegidas de VIIRS 375 que el port «pierde» contra K no son pérdidas de detección.** Las 6 son alertas
   sólo OCR; 5 son de Suomi NPP antes del 2026-10-09, el tramo en que A119 avisa que la distancia es de otra pasada. El
   port encuentra en esas pasadas píxeles a 9 a 24 km del cráter con **el mismo VRP que MIROVA** (Isluga 2026-09-09
   06:06: 6 píxeles a 21 km, 2,18 MW contra 1,91; Tupungatito 2026-09-14 06:18: 2 píxeles a 12,5 km, 2,28 contra 2,22).
   La sexta (Isluga 2026-06-17 05:06) es un artefacto de mi regla de distancia (centroide). Sin esas 5 filas y con la
   distancia del píxel más cercano, 0 de 30 perdidas (post hoc).
5. Respuesta a la pregunta del frente: **sí, el código de 750 cambiando sólo bandas, grilla y coeficiente describe
   la magnitud de MIROVA en los dos sensores y su detección en MODIS**; en VIIRS 375 lo que no calza es la caja (dónde
   rige el umbral de cumbre), no los umbrales ni el fondo.

## Controles (pre-registro §4), leídos antes de cualquier lectura

| control | resultado | denominador |
|---|---|---|
| Cobertura (A108) | SIN DATO 2: Chillán 2026-10-12 05:18 V375 protegida (CMR no sirve el gránulo, igual que en N) y Cordón Caulle 2026-08-31 02:50 MODIS negativo (volcán fuera del gránulo) | 310 |
| Port sin red con config de 750 = oráculo de N | 391 de 391 en npix y VRP (`03_control_v750_sin_red.py`); control positivo: con config de 375 cambia en 162 | 391 grillas de N |
| CTL750: cadena completa en el runner = oráculo de N | 10 de 10 (incluidas Láscar 10-08 0,358, Chillán 10-10 13,131, Villarrica 09-19 0,452) | 10 |
| K re-corrido = lo publicado | publica igual 149 de 149 y `pc.vrp_mw` a 0,001 MW 149 de 149, en VIIRS 375 y en MODIS | 149 + 149 |
| Control positivo del port | protegidas de Láscar o Chillán con píxeles: V375 24 de 24, MODIS 49 de 49 | |
| Prueba sintética (proyección, centros, orientación de las grillas nuevas) | foco en (X0, Y0) cae en la celda de cumbre en 375 y en MODIS; sin foco, 0 píxeles | |

Las dos preguntas del instrumento: (1) si el port no publicara nunca, R2 daría 0 y el control positivo fallaría; si
publicara siempre, R3 daría 1; (2) una pasada sin resultado queda SIN DATO y no entra a ningún denominador.

Ventana de todos los números: pasadas nocturnas, VIIRS 375 del 2026-04-01 al 2026-10-21 y MODIS del 2026-03-01 al
2026-10-21, sin el 17 al 20 de octubre; records de `origin/main` 533398f8f; referencia de Mirova-v1 remota
(consolidado `fe2d0a57`, OCR `4ddd5481`); regla D-9 en modo SN; protegida = lectura A. Ponderado = estimador por los
pesos de la muestra estratificada (`02_seleccion.py`).

## Hallazgos, de mayor a menor gravedad

### P-1. En MODIS el código de MIROVA, con banda 22 primaria y MxD03, reproduce la detección y el silencio de MIROVA, y gana a producción

- **SCRIPT:SALIDA**: `04_analizar.py` → `04_analizar_salida.txt` (MODIS, variante `fisica`); `05_posthoc.py` →
  `05_posthoc_salida.txt`.
- **QUÉ PASA**: de noche, el foco de Láscar o de Chillán ocupa una fracción de un píxel de 1 km. El código de MIROVA lo
  detecta por contraste local del NTI y del ETI y mide su fondo interpolando por debajo de un halo, sin recortar. Con
  sólo cambiar bandas, grilla (51 × 51 de 1 km con la esquina de GEO) y coeficiente (1,89e7 × 1 km²):

  | lectura (pre-registro §5) | port | K (producción) | vara | veredicto |
  |---|---|---|---|---|
  | R1 protegidas que K publica y el port no | 0 de 48 (y gana 2 de 2) | | 0 | sin pérdidas |
  | R2 recall protegidas | 50 de 50 (Wilson 0,929 a 1,000) | 48 de 50 | 0,91 (oráculo en 750) | REPRODUCE |
  | R2 recall bajo 1 MW | 39 de 42 | 32 de 42 | | |
  | R3 negativos limpios publicados (ponderado) | 0,0004 [0,0000; 0,0010], 2 de 57 crudo | 0,0076 (39 de 5.132) | la de K | REPRODUCE |
  | R4 razón port / MIROVA | 1,006 [0,889; 1,143], n 89, 66 en banda | 0,516 [0,311; 0,729], n 80 | mediana en [0,95; 1,05] y 3 de 4 en banda | PARCIAL (74 %) |
  | MISSION contra K | ΔE −44,0 [−58,8; −29,5] | | | **GANA** |

  Los 2 negativos que el port publica son de Láscar y producción también los publica (2026-06-04 01:20, 1,43 MW;
  2026-08-04 07:45, 0,29 MW); apaga 18 de los 20 negativos que K publica. Las 3 alertas que no ve: Láscar 2026-06-26
  07:40 (0,24 MW) y 2026-07-09 07:40 (0,27 MW), con 0 píxeles, y Villarrica 2026-09-25 08:05 (0,9 MW), pasada partida
  (otro record nuestro a ≤ 7 min). Por tamaño de MIROVA: bajo 1 MW 1,037, de 1 a 3 MW 0,970, sobre 3 MW 1,005.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy (no está en producción). Si se adoptara, el operador vería las alertas
  débiles de Láscar que hoy faltan (7 más de 42) y la magnitud de MODIS al doble de la actual, a la par de MIROVA, y
  dejaría de ver los puntos que producción publica en noches en que MIROVA no vio nada (de los 14 negativos de Cordón Caulle de la
  muestra, K publica 12 y el port ninguno; la clase neg_pub está sobrerrepresentada a propósito).
- **CÓMO REPRODUCIRLO**: `python -I 04_analizar.py --art D:\vrp-trabajo\temporales\s159_portes\run_39712862945 --n-art
  D:\vrp-trabajo\temporales\s159_n\run_39682867040`; una pasada: Láscar 2026-03-01 01:40 (id 0) con
  `probe_portes.py --sensor MODIS --solo 0` en un runner con `EARTHDATA_TOKEN`.
- **CONFIANZA**: CONFIRMADO como medición (controles en verde). La caja de 5 × 5 y 15 × 15 km es hipótesis declarada;
  la variante del mismo tamaño en celdas (7 × 7 y 21 × 21) y la sensible dan **idéntico** recall y silencio en esta
  muestra, así que en MODIS la caja no decide. Muestra concentrada en Láscar (80 de 92 alertas): fuera de Láscar,
  Chillán y Villarrica no hay alertas de MIROVA en MODIS en la ventana.
- **GRAVEDAD**: 4. Es la descripción medida de la detección de MODIS que ningún paper da (P3), y orienta la ola 3.

### P-2. En MODIS la banda 21 primaria y la geolocalización de 5 km se separan de MIROVA (D21 y la geolocalización, medidos con el código)

- **SCRIPT:SALIDA**: `04_analizar_salida.txt`, variantes `fisica_b21` y `fisica_geo5km`.
- **QUÉ PASA**: la banda 21 es la de baja ganancia, con un ruido unas diez veces mayor que la 22 (NEdT 0,183 contra
  0,017 K, `pipeline/process_modis.py:328`). Con ella el contraste local del NTI se pierde en el ruido: el mismo
  código detecta 20 de 92 alertas (0 de 42 bajo 1 MW), pierde 28 protegidas que K publica y su magnitud baja a 0,794.
  La geolocalización interpolada de la grilla de 5 km corre el foco (P3 midió 0,5 a 3,4 km): con ella la razón baja a
  0,903 con sólo 35 de 76 en banda y se pierden 3 protegidas.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (producción ya usa la banda 22 primaria desde S153; sigue con `_interp_geo`).
- **CÓMO REPRODUCIRLO**: igual que P-1.
- **CONFIANZA**: CONFIRMADO para estos dos insumos dentro del código de MIROVA. Que MIROVA use MxD03 es inferencia por
  los datos (no está escrito en ninguna fuente, P3).
- **GRAVEDAD**: 3. Cierra por medición la pregunta de D21 para el código de MIROVA y pesa en el pre-registro de MxD03 v2.

### P-3. En VIIRS 375 el código reproduce la magnitud de MIROVA al centésimo

- **SCRIPT:SALIDA**: `04_analizar_salida.txt` (VIIRS 375, `fisica`); `05_posthoc_salida.txt` (por tamaño).
- **QUÉ PASA**: con I4 (3,74 µm) e I5 (11,45 µm), la grilla de 134 × 134 celdas de 375 m de los TIF UTM de MIROVA y
  1,80e7 × 0,140625 km², la razón contra el VRP de MIROVA es **1,000 [0,966; 1,019] en 61 alertas** (IC de la mediana
  0,994 a 1,003), 48 de 61 en [0,8; 1,25]: **REPRODUCE**. Por píxeles: 1 px 1,000 (n 8), 2 a 4 px 1,002 (n 32), 5 o más
  0,999 (n 21). Ninguna pasada ambigua por la triangulación. K en las mismas alertas: 0,651 [0,436; 0,848], 14 de 76 en
  banda. Única excepción: las alertas de Chillán sobre 3 MW dan 0,939 [0,817; 0,985] (n 6; por ejemplo 2026-10-10
  05:12, 5,94 contra 8,75 MW); el recorte no tiene píxeles con bandera de saturación. Causa: SOSPECHA (sin investigar).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy; el tablero muestra en VIIRS 375 un 65 % de lo que MIROVA mide.
- **CÓMO REPRODUCIRLO**: igual que P-1; pasada de ejemplo: Láscar 2026-04-04 05:48 (id 150), port 2,688 contra 2,69.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4 (positivo). Es la descripción de la magnitud de VIIRS 375 que el paper no da (P2 H1): el mismo fondo y
  la misma suma que en 750, con el coeficiente de S14.

### P-4. En VIIRS 375, dónde rige el umbral de cumbre decide la detección débil de Cordón Caulle y Tupungatito

- **SCRIPT:SALIDA**: `04_analizar_salida.txt` (variantes `fisica`, `pixel`, `sensible`); `05_posthoc_salida.txt`
  («alertas que el port NO publica»).
- **QUÉ PASA**: en Cordón Caulle la anomalía está en el campo del lacolito, a 5 a 8 km del punto de MIROVA; en
  Tupungatito, a 5 km. Con la caja del mismo tamaño en metros que la de 750, eso cae en el ROI de escena, con 10 sigma
  y mínimos 0,02 / 0,01, y el código no ve nada: 11 de las 14 alertas bajo 1 MW que el port no publica tienen 0
  píxeles y son de esos dos volcanes (MIROVA a 4,9 a 8,2 km). Con todo el ROI de escena en umbrales de cumbre
  (`sensible`) el recall bajo 1 MW sube de 31 a 42 de 45 (ponderado 0,618 a 0,905; K 0,881), el de protegidas no
  cambia (30 de 39 con la regla del centroide) y los negativos limpios publicados pasan de 7 a 11 de 65 (ponderado
  0,0090 a 0,0480, contra 0,0385 de K). La caja de 7 × 7 y 21 × 21 celdas (2,6 × 2,6 km de cumbre) es peor: 23 de 45.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. Para una adopción: con la caja por defecto, alertas débiles de MIROVA
  en Cordón Caulle y Tupungatito quedarían sin punto nuestro.
- **CÓMO REPRODUCIRLO**: ids 170, 175, 177, 178, 186, 217, 232, 234, 235, 251, 256 de `objetivos_portes.json`.
- **CONFIANZA**: CONFIRMADO que la caja sensible las recupera; SOSPECHA que ésa sea la ROI de MIROVA (el `.m` dice
  que las ROI se ajustan por volcán; podría ser una caja propia por volcán, igual que en N-3).
- **GRAVEDAD**: 4 para el diseño de un paquete de 375 (la caja por defecto pierde alertas, aunque bajo 1 MW).

### P-5. Las 6 «protegidas perdidas» de VIIRS 375 son un problema de etiqueta y de mi regla de distancia, no de detección

- **SCRIPT:SALIDA**: `05_posthoc.py` → `05_posthoc_salida.txt` (POST HOC, no pre-registrado).
- **QUÉ PASA**: por la regla 1 del pre-registro el port en VIIRS 375 **PIERDE PROTEGIDA** (6 de 36 que K publica). Las
  6 son alertas sólo OCR; 5 de ellas son de Suomi NPP antes del 2026-10-09, donde la distancia y la clase de la fila
  pueden ser de otra pasada y el VRP sí es de la suya (hito de `scripts/calidad_referencia_mirova.py`). En esas pasadas
  el código encuentra píxeles a 9 a 24 km del punto de MIROVA con el mismo VRP que MIROVA: Isluga 2026-09-09 06:06
  (6 px a 21 a 24 km, 2,18 contra 1,91), Tupungatito 2026-09-14 06:18 (2 px a 12,5 km, 2,28 contra 2,22), Tupungatito
  2026-08-01 05:00 (3 px a 14 a 15 km, 1,28 contra 1,25), Isluga 2026-09-28 05:12 y 2026-10-03 05:18 (cúmulo en la cumbre
  más píxeles lejanos). El `.m` suma **todos** los alertados de la ventana de 50 km (VRP.m l. 83-85), así que el VRP
  de MIROVA de esas pasadas incluye fuentes lejanas. La sexta, Isluga 2026-06-17 05:06 (NOAA-21), tiene el cúmulo en la
  cumbre y un píxel a 15,7 km que corre el centroide fuera de los 5 km: es mi regla del record sintético (centroide).
  Con la distancia del alertado más cercano y sin las 14 filas dudosas (9 protegidas): **0 de 30 perdidas**, recall
  ponderado de protegidas 1,000 (K 1,000).
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Pesa en la vara: en VIIRS 375 parte de las «alertas protegidas» de la
  lectura A antes del 2026-10-09 podrían ser fuentes a decenas de km que MIROVA suma en la ventana del volcán.
- **CÓMO REPRODUCIRLO**: `python -I 05_posthoc.py --art D:\vrp-trabajo\temporales\s159_portes\run_39712862945`.
- **CONFIANZA**: CONFIRMADO que el port y MIROVA coinciden en VRP con los píxeles lejos; SOSPECHA qué son esas fuentes
  (no se miró ninguna imagen) y que MIROVA las haya alertado ahí.
- **GRAVEDAD**: 3. Ninguna alerta real queda en riesgo, pero el veredicto pre-registrado de R1 en 375 lo decide una
  etiqueta dudosa; el censo de protegidas de 375 tiene que separar este estrato.

### P-6. VIIRS 375: el port calla donde producción publica

- **SCRIPT:SALIDA**: `04_analizar_salida.txt` y `05_posthoc_salida.txt` («negativos que el port publica»).
- **QUÉ PASA**: en negativos limpios el port publica 7 de 65 (ponderado 0,0090, IC 0,0022 a 0,0192, contra 0,0385 de
  K): **REPRODUCE**. Los 7 son pasadas que K también publica (apaga 13 de 20 de esa clase, enciende 0); 5 de los 7 son de
  0,024 a 0,049 MW, debajo del corte que la regla D-9 trata como «MIROVA no vio nada» del lado de MIROVA.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy; con el port desaparecerían dos de cada tres puntos de cumbre que hoy
  se publican en noches en que MIROVA no vio nada.
- **CONFIANZA**: CONFIRMADO en la muestra (65 negativos; el intervalo es ancho).
- **GRAVEDAD**: 3.

### P-7. Veredicto MISSION del port en VIIRS 375: domina la caja, no el código

- **SCRIPT:SALIDA**: `04_analizar_salida.txt`.
- **QUÉ PASA**: ΔE contra K: física +148,3 [−34,1; +333,3], píxel +263,8 [+66,7; +459,2], sensible +9,8 [−189,0;
  +305,5]; las tres llevan la marca PIERDE PROTEGIDA por P-5. El peso lo hacen las alertas bajo 1 MW de Cordón Caulle y
  Tupungatito (P-4, 952 en la población) contra los negativos que el port apaga.
- **CONFIANZA**: CONFIRMADO como cuenta; el intervalo con 45 alertas bajo 1 MW de 952 es ancho.
- **GRAVEDAD**: 2 (descriptivo; no decide adopción).

### P-8. Una escena MODIS inválida es silencio correcto

- **SCRIPT:SALIDA**: `04_analizar_salida.txt` («motivos de vacío»).
- **QUÉ PASA**: Villarrica MODIS 2026-03-11 01:30 (negativo, pasada partida, cenit 54°): 1.462 de 2.601 celdas sin dato
  porque la ventana cae medio fuera del gránulo; el `.m` rechaza la escena (más de la mitad en NaN). Correcto.
- **GRAVEDAD**: 1.

## Lo que quedó sin medir, y por qué

- **El día**: sólo nocturnas (pre-registro §6).
- **La ROI de MIROVA por volcán** en VIIRS 375 (P-4): una sola caja sensible es una aproximación; falta medirla.
- **Las fuentes lejanas de P-5**: no se miró ninguna imagen; quedan como SOSPECHA.
- **Chillán sobre 3 MW en 375** (0,939): sin investigar.
- **Escala**: 150 + 150 pasadas. VIIRS 375 tiene 952 alertas bajo 1 MW y 3.482 negativos en la población; los
  intervalos de R3 y de ΔE son anchos. Agrandar el lote es decisión de Nicolás.
- La regla R4 de MODIS quedó a un caso del 75 % (66 de 89); se informa como PARCIAL, sin mover el corte.

## VERIFICADO LIMPIO

- **El envoltorio del port es el oráculo validado**: con la config de 750, 391 de 391 grillas de N iguales en npix y
  VRP (`python -I 03_control_v750_sin_red.py --art D:\vrp-trabajo\temporales\s159_n\run_39682867040`), y 10 de 10 con
  la cadena completa en el runner (`04_analizar_salida.txt` §2).
- **La caja física de 750 es la del `.m`** (assert en `mirova_port.control_sin_red`, `python -I mirova_port.py`).
- **K re-corrido = lo publicado**: 149 de 149 en VIIRS 375 y 149 de 149 en MODIS (publicación y `pc.vrp_mw` a 0,001 MW):
  los records de `data/` de 533398f8f son los del detector de hoy en estas pasadas.
- **Ninguna pasada ambigua por la triangulación** de `fillmissing2` en ninguna variante.
- **Sin saturación con bandera** en los recortes de VIIRS 375 (bit 2 del quality flag de I04 e I05, 0 en 149) ni en MODIS (B22 en
  NaN con B21 válida: 0 en 149).
- **`pipeline/`, `data/` y `frontend/` sin tocar**: `git diff --stat origin/s159-pruebas -- pipeline data frontend` vacío.
- **El tope de 300 se respetó**: 150 VIIRS 375 y 150 MODIS (`02_seleccion_salida.txt`), más 10 de control de 750.

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|
| Separar en la ventana del volcán lo que está en la cumbre de lo que está a decenas de km | El `.m` suma todos los alertados de los 50 km: en Isluga y Tupungatito el VRP de MIROVA incluye píxeles a 12 a 24 km. Un SDA que informe la cumbre aparte es más fiel al volcán | P-5, 5 pasadas con hora; validar contra imágenes y OVDAS | hipótesis |
| Ver el campo del lacolito de Cordón Caulle y el de Tupungatito con umbrales de cumbre | Son focos débiles reales a 5 a 8 km que la caja por defecto calla | P-4, 11 pasadas; validar contra OVDAS y SWIR | hipótesis |
| Declarar «no observado» cuando la escena es inválida o el volcán cae al borde del gránulo | Separa «no vi» de «no miré» (amplía la candidata de N-8) | P-8 | idea, barata |
| Magnitud de Chillán sobre 3 MW en VIIRS 375 | El port queda 6 % bajo MIROVA justo en las alertas grandes; si es por el fondo de un cúmulo extenso, el experimental podría medirlo mejor | P-3, n 6 | sin investigar |
