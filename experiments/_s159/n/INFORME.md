# S159, frente N: el fondo y la suma del código de MIROVA en VIIRS 750, a escala y en las dos direcciones

2026-10-21 (cuerpo cerrado a las 23:09 UTC, commit `3b49af569`; el apéndice del censo, al final, es posterior). Ola 2 del plan
`docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md` (fila N). Worktree
`C:\vrp-trabajo\s159-n`, rama `s159-n`. Sólo lectura: no se tocó `pipeline/`, `data/` ni `frontend/`; los brazos son
reemplazos en memoria del módulo (patrón A75), escritos en `probe_n.py`. Pre-registro commiteado **antes** de
despachar: `PREREGISTRO_N.md`, commit `0b20eb1f3`. Workflows de sólo lectura (rama de disparo `s159-n-disparo`, no se
mergea; autentica sólo con `EARTHDATA_TOKEN`): humo 39680724047 (10 pasadas), lote 39682867040 (398 pasadas, 8 trozos),
redisparo 39690106947 (las 7 SIN DATO, siguen SIN DATO). Artefactos en `D:\vrp-trabajo\temporales\s159_n\`; resultados
y bitácoras en `run_39682867040\` de esta carpeta.

## En una pantalla

1. ⚠️ **Corregido por el censo (apéndice al final, run 39693661527)**: el 3,8 % y el ΔE +104 salieron de un sorteo con suerte (verificador, afirmación 1). Contado entero: F enciende 60 negativos (los 60 cúmulos de cumbre en 0,0 MW; ninguno de los 59 `far`), publica 114 de 5.476 (2,1 %) y ΔE = +12. El veredicto sigue siendo ENCIENDE DE MÁS, pero del orden de una decena. Texto original:
   **La hipótesis queda refutada para el fondo y la suma solos (brazo F) y para F más quitar la compuerta (FC).**
   Sobre la detección de producción (K), el fondo del código recupera 48 alertas de MIROVA bajo 1 MW (las no
   publicadas bajan de 65 a 17 de 175, ponderado) y no pierde ninguna protegida, pero enciende negativos limpios: de 54
   a 206 de 5.385 (1,0 % a 3,8 %). Por la regla 2 de MISSION la suma de errores sube 104 (IC 95 % 14,5 a 212,3).
   Veredicto pre-registrado: **ENCIENDE DE MÁS**. Los 6 negativos que F enciende en la muestra son cúmulos de un píxel
   que K ya detectaba (en 0,0 MW, sólo del segundo pase) y que **el código de MIROVA no detecta** (0 píxeles en el
   oráculo): el recorte a cero de K tapaba una divergencia de detección, y el fondo solo la destapa.
2. **El código entero de MIROVA, en la grilla de GEO, reproduce lo que MIROVA publicó.** Sin mirar la tabla, el oráculo
   (detección, remuestreo lineal a la grilla de 750 m con la esquina de GEO, fondo y suma) da una razón contra el VRP de
   MIROVA de **0,999 (cuartiles 0,978 y 1,007) en 145 alertas**, y en la de 1 píxel 47 de 59 a menos de 5 %. Con la
   grilla de R2 la mediana también es 1,000, pero los cuartiles abren a 0,868 y 1,108 y detecta 113 en vez de 145. Es
   la primera medición por valores (no por encabezados) de que la grilla de GEO es la de MIROVA.
3. **La compuerta de 3 K del primer pase (D22, brazo C) no cambia ninguna publicación**: 0 de 391 pasadas. Cambia el
   camino (sin ella, el primer pase encuentra lo que antes recapturaba el segundo: cúmulos sin píxel del primer pase,
   108 a 1) y en 8 pasadas agrega un segundo píxel al cúmulo, que sólo se nota en la magnitud de FC. Los 55 cúmulos en
   0,0 MW de la muestra siguen en 0,0 con C: **el cero lo pone el fondo, no la compuerta** (responde a VA-1).
4. Contado como brazo con la misma regla (post hoc, no estaba pre-registrado como brazo), el oráculo con umbrales de
   cumbre en todo el recuadro de 21 × 21 celdas **gana en las dos caras**: 0 protegidas perdidas, una ganada, 59
   alertas bajo 1 MW ganadas, 0 perdidas, y 46 negativos limpios apagados (de 54 a 8); suma de errores −105. Para la
   ola 3: lo que acerca a MIROVA es el **paquete entero** (detección, remuestreo a la grilla de GEO, fondo y suma
   juntos), no el fondo sobre nuestra detección.

## Hallazgos, de mayor a menor gravedad

### N-1. El fondo y la suma del código sobre la detección de producción encienden negativos limpios por encima de lo que ganan

- ⚠️ **Los números de esta sección quedan reemplazados por el censo del apéndice** (F enciende 60, no 152; ΔE +12, no +104; «del orden de 150 puntos» pasa a 60). El mecanismo se sostiene. Texto original:
- **SCRIPT:SALIDA**: `03_analizar.py` → `03_analizar_salida.txt` §8 y `resumen.json`; detalle en `05_detalle.py` →
  `05_detalle_salida.txt` (a).
- **QUÉ PASA**: de noche la cumbre de Isluga, Planchón-Peteroa o Tupungatito tiene a veces un píxel algo más tibio que
  sus vecinos inmediatos, pero más frío que la mediana del anillo de 5 a 25 km. Producción lo detecta en el segundo
  pase, le resta la mediana del anillo, el exceso queda negativo y lo recorta a 0,0 MW: el tablero no lo muestra. El
  fondo del código lo compara contra sus vecinos interpolados y no recorta, así que el mismo píxel sale con 0,23 a 0,45
  MW y se publica. MIROVA, que corre ese mismo fondo, no lo publica porque **su detección no lo encuentra** (el oráculo
  da 0 píxeles en las 6 pasadas). Números, ponderados a la población de abril a octubre (sin el 18 y 19 de octubre):

  | brazo | protegidas perdidas (de 78) | alertas bajo 1 MW sin publicar (de 175) | negativos limpios publicados (de 5.385) | ΔE contra K | IC 95 % | veredicto |
  |---|---|---|---|---|---|---|
  | K (producción) | 0 | 65 | 54 (1,0 %) | 0 | | |
  | K2 (nulo) | 0 | 65 | 54 | 0 | 0 a 0 | EMPATE |
  | C | 0 | 65 | 54 | 0 | 0 a 0 | EMPATE |
  | F | 0 | 17 | 206,3 (3,8 %) | +104,3 | 14,5 a 212,3 | **ENCIENDE DE MÁS** |
  | FC | 0 | 17 | 206,3 (3,8 %) | +104,3 | 3,7 a 207,7 | **ENCIENDE DE MÁS** |

  Los 6 negativos de la muestra que F enciende (peso 20,8 a 30,8 cada uno): Tupungatito 2026-05-11 05:54, Isluga
  2026-06-28 05:54, 2026-09-06 05:42 y 2026-04-18 05:30, Planchón-Peteroa 2026-07-04 05:48 y 2026-10-05 05:48. Los 6:
  un píxel, K en 0,0 MW, 0 píxeles del primer pase, oráculo 0 píxeles, MIROVA RUTINA 0,0. Ninguna pasada ambigua por la
  triangulación (la banda nunca cruza el predicado). El estimador descansa en 6 eventos de 141 negativos muestreados: el
  intervalo no toca el 0, pero es ancho.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy (F no está en producción). Si se adoptara F solo, el operador vería del
  orden de 150 puntos de cumbre más en seis meses, de 0,2 a 0,5 MW, en noches en que MIROVA no vio nada, sobre todo en
  Isluga, Planchón-Peteroa y Tupungatito; a cambio, unas 48 alertas débiles de MIROVA que hoy faltan aparecerían.
- **CÓMO REPRODUCIRLO**: `python probe_n.py --objetivos objetivos_n.json --out out --solo 40,91,99,134,188,326` en un
  runner con `EARTHDATA_TOKEN` (o copiar `probe-s159-n.yml` a una rama de disparo con `SOLO` puesto); después
  `python 03_analizar.py --art <carpeta>` y `python 05_detalle.py --art <carpeta>`.
- **CONFIANZA**: CONFIRMADO (medido, con controles §Controles en verde).
- **GRAVEDAD**: 4. Decide la forma del pre-registro de adopción: adoptar el fondo sin la detección del código tuerce la
  publicación hacia falsas alarmas débiles.

### N-2. El código entero en la grilla de GEO reproduce la magnitud y la detección de MIROVA; la grilla de R2 no

- **SCRIPT:SALIDA**: `04_oraculo_grilla.py` → `04_oraculo_grilla_salida.txt`; `05_detalle_salida.txt` (b), (c) y (d).
- **QUÉ PASA**: MIROVA no mira el gránulo crudo: lo interpola a una grilla UTM fija y detecta ahí. Si nuestra copia
  de esa grilla está corrida media celda, un foco de un píxel cae repartido entre dos celdas y su radiancia baja; si está
  en el lugar correcto, el oráculo tiene que dar lo mismo que MIROVA. Con la grilla de GEO (esquina de la de 375 m menos
  187,5 m en x e y) y el interpolador lineal, en las 181 alertas que deciden:

  | variante del oráculo | alertas detectadas | protegidas | negativos con alerta (crudo, ponderado) | razón O/MIROVA: mediana [q1, q3] | entre 0,8 y 1,25 |
  |---|---|---|---|---|---|
  | GEO, lineal | 145 | 71 de 78 | 4 de 195 (4) | 0,999 [0,978, 1,007] | 127 de 145 |
  | GEO, vecino más cercano | 133 | 71 | 25 (114) | 1,226 [0,951, 1,454] | 56 de 133 |
  | GEO, cúbico | 136 | 71 | 11 (51) | 1,206 [1,115, 1,286] | 85 de 136 |
  | R2 (esquina de 375 m), lineal | 113 | 71 | 15 (85) | 1,000 [0,868, 1,108] | 83 de 113 |
  | R2, vecino más cercano | 129 | 70 | 23 (122) | 1,238 [0,937, 1,512] | 48 de 129 |
  | GEO, lineal, recuadro 21 × 21 entero con umbrales de cumbre | 175 | **78 de 78** | 8 (8) | 0,999 [0,973, 1,009] | 144 de 175 |

  Por píxeles (GEO lineal): 1 píxel, 35 de 59 a menos de 2 % y 47 de 59 a menos de 5 %; 2 a 4, 40 de 67 a menos de 5 %;
  5 o más, 13 de 18. Por cenit no hay escalón (≤40°: 1,000, n 97; >40°: 0,997, n 48). Casos del bloque R2 con la grilla
  de GEO: Chillán 2026-10-10 05:54 da 5 píxeles y 13,131 MW (MIROVA 13,13); Láscar 2026-10-08 05:42 1 px 0,358 (0,36);
  Villarrica 2026-09-19 05:48 1 px 0,452 (0,45; con la grilla de R2 eran 2 píxeles y 0,474); Chillán 2026-10-01 05:24
  7 px 9,157 (9,0).
- **CÓMO SE VE EN EL DASHBOARD**: invisible (el remuestreo está apagado, `ENABLE_UTM_REGRID = False`). Pesa en D17 y
  en el pre-registro de la ola 3: el remuestreo a la grilla de GEO con interpolación lineal es la pieza que convierte el
  fondo del código en paridad, y el vecino más cercano y el cúbico quedan descartados por los datos.
- **CÓMO REPRODUCIRLO**: `python 04_oraculo_grilla.py --art D:\vrp-trabajo\temporales\s159_n\run_39682867040`.
- **CONFIANZA**: CONFIRMADO como medición. Dos supuestos declarados: (1) «alerta del oráculo» = al menos un píxel, VRP
  mayor que 0 y el píxel más radiante a no más de `inner_radius_km` del centro (no es la regla del scraper); (2) el
  recuadro de 21 × 21 «con umbrales de cumbre» se aplica a los 11 volcanes y es una aproximación de la ROI de MIROVA,
  que sigue sin conocerse por volcán. Que la triangulación de MATLAB coincida con la de scipy sin perturbar: SOSPECHA
  apoyada en datos (en 56 alertas de un píxel cuya banda de triangulación pasa de 5 %, la central coincide con MIROVA a
  menos de 5 % en 44); sólo O2 lo cierra.
- **GRAVEDAD**: 4 (positivo, pero orienta la adopción y la fase 0 de D17).

### N-3. La ROI de MIROVA en Cordón Caulle y Tupungatito se comporta como umbrales de cumbre hasta 8 km o más

- **SCRIPT:SALIDA**: `05_detalle_salida.txt` (c); `04_oraculo_grilla_salida.txt`, casos.
- **QUÉ PASA**: con la caja de cumbre por defecto (7 × 7 celdas, ±2,6 km) el oráculo no detecta 7 protegidas de Cordón
  Caulle (MIROVA a 4,6 a 10,5 km): 2026-05-25 05:42, 06-05 05:36, 06-07 05:54, 07-03 05:48, 07-06 05:54, 09-18 05:24 y
  10-10 05:54. Con umbrales de cumbre en todo el recuadro de 21 × 21 aparecen las 7, y tres coinciden con MIROVA al
  centésimo: Cordón Caulle 10-10 05:54 2 px 1,193 MW (1,19), 10-16 05:42 1 px 0,610 (0,61), Tupungatito 08-21 05:48 1 px
  0,194 (0,19). Producción publica 6 de esas 7 (todas menos 10-10).
- **CÓMO SE VE EN EL DASHBOARD**: hoy producción sí publica 6 de 7 con su círculo de 20 km; el riesgo es para la ola 3:
  un paquete con la caja por defecto perdería 6 protegidas (regla 1 de MISSION).
- **CÓMO REPRODUCIRLO**: igual que N-2.
- **CONFIANZA**: CONFIRMADO que el recuadro sensible las recupera; SOSPECHA que ése sea el recuadro de MIROVA (podría
  ser una caja propia por volcán).
- **GRAVEDAD**: 4 para el diseño del paquete (sin la ROI correcta pierde protegidas).

### N-4. La compuerta de 3 K del primer pase no decide ninguna publicación

- **SCRIPT:SALIDA**: `03_analizar_salida.txt` §5, §8 y §10.
- **QUÉ PASA**: la compuerta exige que el píxel esté 3 K sobre el fondo del anillo antes de los tests contextuales; en
  una cumbre fría eso vacía el primer pase y el segundo pase recaptura sin compuerta. Quitarla (C) mueve los píxeles al
  primer pase (cúmulos sin píxel del primer pase: K 108 de 238, C 1 de 238) y en 8 pasadas agrega un segundo píxel al
  cúmulo, pero **no cambia ninguna publicación** (0 de 391) ni el cero de los 55 cúmulos en 0,0 MW. En FC ese segundo
  píxel sube la magnitud (por ejemplo Chillán 2026-09-29 06:36: K 0,329, F 1,149, FC 1,451; MIROVA 2,03).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python 03_analizar.py --art <carpeta>`; las 8 pasadas: ids 58, 117, 137, 257, 345, 381, 386, 392
  de `tabla_por_pasada.csv` (columnas `K_n` contra `C_n`).
- **CONFIANZA**: CONFIRMADO en esta población (VIIRS 750, nocturno, abril a octubre).
- **GRAVEDAD**: 3. Quita una pieza del paquete de la lista de cosas que deciden; sigue siendo divergencia literal con
  el `.m` (que no tiene compuerta), con efecto sólo en la magnitud de FC.

### N-5. El tope D9 de 5 MW recorta a una protegida de Chillán en cuanto el fondo deja de subestimarla

- **SCRIPT:SALIDA**: `03_analizar_salida.txt` §5 («magnitud post hoc contra la del pipeline, distintas en 1 de 238»).
- **QUÉ PASA**: Chillán 2026-10-01 05:24 (alerta protegida, MIROVA 9,0 MW; oráculo 7 px 9,157). Producción publica 2,655
  MW. Con el fondo del código la magnitud sube a 6,21 y el tope de 5 MW de la vía contextual sobre fondo frío (D9,
  `PATH_D_ONLY_CAP_MW`) la deja en 5,0. Hoy el tope no muerde porque el fondo de anillo subestima; con un fondo más fiel
  empieza a recortar una erupción real.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy; con F, Chillán se vería en 5,0 MW contra 9,0 de MIROVA.
- **CÓMO REPRODUCIRLO**: id 319 de `objetivos_n.json` (`--solo 319`).
- **CONFIANZA**: CONFIRMADO en una pasada.
- **GRAVEDAD**: 3. Toca la marca A23 (S151): el tope recorta y no está medido que lo recortado sea artefacto; aquí no lo
  es. Cualquier adopción del fondo tiene que revisar el tope en el mismo paquete (A113).

### N-6. La magnitud de F acierta la mediana pero no la pasada; lo que falta es el remuestreo

- **SCRIPT:SALIDA**: `03_analizar_salida.txt` §9.
- **QUÉ PASA**: un píxel nativo de 750 m con un foco tiene más radiancia que la celda interpolada de MIROVA, que lo
  reparte con sus vecinas. F usa el fondo del código pero sobre el píxel nativo. Razón contra MIROVA en las alertas que
  publica cada brazo: K 0,510 [0,370, 0,733] n 115; F 0,990 [0,703, 1,290] n 163; FC 1,014 [0,723, 1,310]; oráculo
  0,999 [0,978, 1,007] n 145. Protegidas: K 0,536, F 0,783, oráculo 1,001. Placebo K × 1,2: 0,612 (la razón se mueve con
  el placebo por construcción, es descriptiva). Ejemplo: Villarrica 2026-09-19 05:48, F 0,699, oráculo 0,452, MIROVA 0,45.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### N-7. Producción no tiene cúmulo en 18 alertas; el código detecta 11 de ellas

- **SCRIPT:SALIDA**: `05_detalle_salida.txt` (a), segunda lista.
- **QUÉ PASA**: 18 alertas que deciden (17 bajo 1 MW y la protegida de Cordón Caulle 10-10) quedan sin publicar aun con
  F, porque K no tiene cúmulo. El oráculo con la caja por defecto detecta 11 (Isluga, Planchón-Peteroa, Láscar,
  Chillán; 1 píxel cada una, razones de 0,54 a 1,29, 8 de ellas a menos de 5 % de MIROVA); de las 7 de Cordón Caulle,
  el recuadro sensible de N-3 recupera 5 (ids 146 y 288 quedan en 0 píxeles con las dos cajas).
- **CÓMO SE VE EN EL DASHBOARD**: alertas débiles de MIROVA sin punto nuestro.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (todas bajo 1 MW salvo la de Cordón Caulle).

### N-8. Dos «negativos limpios» de Chaitén son pasadas que no ven el volcán

- **SCRIPT:SALIDA**: `run_39682867040\redisparo_39690106947_resultados_00.json` (`dist_min_km`).
- **QUÉ PASA**: Chaitén 2026-06-30 06:12 (VJ202MOD) y 2026-05-15 04:24 (VNP02MOD): el píxel del gránulo más cercano al
  volcán está a 10,4 y 23,5 km. Producción guarda el record porque el recuadro de 25 km toca el borde del gránulo, y el
  etiquetador lo cuenta como negativo limpio. Un negativo que no miró el cráter entra al denominador.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (no publica).
- **CONFIANZA**: CONFIRMADO en 2 de 143 negativos muestreados; la frecuencia en la población: SOSPECHA (no medida).
- **GRAVEDAD**: 1 (diluye la tasa de publicación en negativos, no tuerce una alerta).

## Controles (pre-registro §7), leídos antes del veredicto

Pregunta 1 (si un brazo estuviera roto, ¿se vería?) y pregunta 2 (instrumento muerto), contestadas con números:

| control | resultado | denominador |
|---|---|---|
| Cobertura (A108) | 391 pasadas con los cinco brazos ok; SIN DATO: 3 del 2026-10-12 (CMR no devuelve el gránulo por nombre, por día y caja ni por ventana; reintentado en 39690106947), 2 de Chaitén con el volcán fuera del gránulo (N-8), 2 diurnas (no se encontró gránulo por ventana y caja) | 396 nocturnas + 2 diurnas |
| Por clase | pos_nopub 66 de 68, pos_prot 91 de 92, pos_resto 38 de 38, neg_pub 54 de 54, neg_resto 141 de 143, r2_fuera 1 de 1 | |
| Nulo K2 = K | idéntico en 391 de 391 (record completo) | 391 |
| K = producción publicada | publica igual en 391 de 391 y `pc.vrp_mw` a 0,001 MW en 391 de 391 | 391 |
| Los reemplazos actúan | F con fondo y recorte evitado en todas las pasadas con alertados; C con la compuerta reemplazada en las 391; el cúmulo cambia con F en 238 de 238 con cúmulo | |
| F post hoc = F del pipeline | 237 de 238; la que difiere es el tope D9 (N-5) | 238 |
| Control positivo de F | Láscar 2026-10-08 05:42: K 0,0 MW, F 0,422 (banda 0,327 a 0,422) | |
| Control positivo del oráculo (grilla R2, lineal) | Láscar 10-08 1 px 0,328 (esperado 0,33); Chillán 10-10 5 px 12,367 (12,37); Villarrica 09-19 2 px 0,474 (0,47) | 3 de 3 |
| Prueba sin red | fondo del código en geometría de gránulo = fondo del oráculo sobre la misma matriz (0,327832450 los dos); proxy de `np` sólo intercepta `maximum(x, 0.0)` | |

Ventana de todos los números: pasadas VIIRS 750 nocturnas del 2026-04-01 al 2026-10-21 sin el 18 y 19 de octubre;
records de `origin/main` 533398f8f; referencia de Mirova-v1 remota (consolidado `7ea275df`, OCR `4ddd5481`). Tramo A119:
antes del 2026-06-13, 86 alertas que deciden (K publica 60, F 83); desde el 13, 95 (K 55, F 80); 14 alertas sólo OCR
antes del 13 se informan aparte y las publican los cinco brazos.

## Lo que quedó sin medir, y por qué

- **Estrato diurno** (rama de día del código): las 2 protegidas diurnas de Chillán quedaron SIN DATO (no se encontró el
  gránulo; puede que la hora de MIROVA no sea la de inicio del gránulo). Sin medición del día.
- **El 2026-10-12**: 3 pasadas (una protegida de Chillán 05:18) SIN DATO; CMR con credenciales no devuelve nada ese día
  para esos gránulos, lo que contradice al verificador de R2-13 (que sí los vio en CMR público): causa sin explicar.
- **VIIRS 375 (VA-2) y MODIS**: fuera de este lote; pendientes como estratos aparte.
- **Escala**: el estimador de negativos encendidos descansa en 6 eventos sobre 141 negativos muestreados. Agrandar la
  muestra de `neg_resto` para angostar el intervalo pasa el tope de 400: **decisión de Nicolás**.
- **Incidente de proceso**: a las 22:16 UTC la cuenta de GitHub llegó al límite de la API (5.000 por hora); contribuyó
  mi `gh run watch` con su intervalo por defecto (dos vigilantes a la vez). Si otra sesión vio errores 403 a esa hora,
  la causa es ésta. Después se usó intervalo de 60 s o más.
- **Ruido observado, sin investigar**: el push a `s159-n-disparo` generó también un run fallido de
  `vigilar-osf-mirova.yml` (39680721824, sin log), que sólo tiene disparador programado.

## VERIFICADO LIMPIO

- **Pareo con MIROVA**: toda fila de referencia pareada a una pasada V750 está a 2 s o menos (`01_poblacion_salida.txt`);
  el pareo a 8 min de R2.3 no cambia ninguna etiqueta ya puesta y sólo agrega 143 negativos y 1 positivo que salen del
  gránulo vecino. Comando: `python 01_poblacion.py --data <data_main> --ref-dest <dir>`.
- **Cobertura de VIIRS 750 de abril a octubre**: 0 alertas de MIROVA sin record nuestro a ±120 s (misma salida).
- **El envoltorio es producción**: K reproduce el record publicado en 391 de 391 (§Controles).
- **Calibración**: el coeficiente por área de producción en VIIRS 750 (19,7 × 562.500 m²) es el del `.m`
  (1,97e7 × 0,5625 km²); `pipeline/process_viirs_mod.py:55` y `:66`.
- **La banda de un píxel no decide ninguna publicación de F ni de FC** (0 ambiguas).
- **`pipeline/` sin diferencias con `origin/main`** al correr (`git diff --stat origin/main -- pipeline/` vacío).
- **El tope de 400 se respetó**: 398 pasadas (`02_seleccion_salida.txt`).

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|
| Píxeles tibios de un píxel en la cumbre que el segundo pase nuestro ve y MIROVA no (Isluga, Planchón-Peteroa, Tupungatito) | Si son fumarolas o domos tibios reales, son categoría b (A54) que la réplica debe callar y el experimental podría mostrar; si son ruido, confirman que el segundo pase de K es más laxo que el del código | N-1, 6 pasadas con hora; validar contra OVDAS y SWIR | hipótesis |
| Magnitud en la geometría nativa del sensor | El remuestreo lineal de MIROVA reparte un foco sub-píxel entre celdas y baja su radiancia (Villarrica 09-19: nativo 0,70, MIROVA 0,45); en el experimental la magnitud nativa podría estar más cerca del calor real | N-6; validar contra SWIR de alta resolución | hipótesis |
| Declarar «no observado» cuando el volcán cae fuera del gránulo | Dos «negativos» de Chaitén no miran el cráter; un SDA que separa «no vi» de «no miré» es más honesto que la tabla de MIROVA | N-8 | idea, barata |
| Fondo determinista | La triangulación sin perturbar coincide con MIROVA en la mayoría de los casos de un píxel; fijarla explícitamente quita la ambigüedad de O1 (amplía MEJ-2) | N-2 | idea |

## Apéndice: censo de F en los negativos que puede encender (run 39693661527)

Aprobado por Nicolás el 2026-10-21. Pre-registro `PREREGISTRO_CENSO_N.md`, commit `bf6cf4db5`, antes del disparo.
Lista: `06_censo.py` → `objetivos_censo.json`; lectura: `07_censo_analizar.py` → `07_censo_analizar_salida.txt`;
resultados y bitácoras en `run_39693661527\`. Por qué alcanza un censo: F no cambia la detección (verificador v3), así
que sólo puede encender un negativo donde K ya tiene un cúmulo que no publica; en la población (sin el 18 y 19 de
octubre) son 60 con cúmulo de cumbre en 0,0 MW y 59 `far`; los otros 5.303 no tienen ningún píxel alertado.

**Controles** (antes de leer): 119 de 119 pasadas de negativos ok con los cinco brazos; K publica igual que producción
y con el mismo `pc.vrp_mw` en 119 de 119; K2 = K en 119; F no cambia la detección ni la clase de distancia en ninguna.
Control positivo: F tiene que publicar los cúmulos que K deja en 0,0 MW, y lo hace (abajo).

| clase | n | K publica | F publica | FC publica | oráculo (predicado del tablero), caja por defecto | oráculo, recuadro sensible |
|---|---|---|---|---|---|---|
| cumbre en 0,0 MW | 60 | 0 | **60** | 60 | 1 | 4 |
| far | 59 | 0 | **0** | 0 | 0 | 0 |
| Isluga 2026-10-12 05:48 (alerta) | 1 | SIN DATO | SIN DATO | | | |
| Chillán 2026-10-12 05:18 (protegida) y 05:54, reintento | 2 | SIN DATO | SIN DATO | | | |

- **Encendidos de F**: 60 de 60 en cumbre (todos de 1 píxel, 0,06 a 0,61 MW; Isluga 22, Tupungatito 17, Láscar 10,
  Planchón-Peteroa 6, Cordón Caulle 4, Lastarria 1); 0 de 59 `far` (F no cambia la clase de distancia, así que un `far`
  sigue sin publicarse). Una de las 60 es ambigua por la triangulación (Isluga 2026-04-06 05:54, banda −0,009 a 0,237).
  Apagados: 0 (los 54 que producción publica siguen publicados, censo del lote).
- **Negativos limpios publicados**: K 54 de 5.476 (0,99 %), F 114 de 5.476 (2,08 %).
- **ΔE de F por censo** = 60 encendidos − 0 apagados − 48 alertas bajo 1 MW ganadas (censo del lote) = **+12**; con
  Isluga 10-12 (SIN DATO) ganada sería +11, y con la ambigua apagada +10 a +11. Denominadores: 5.476 negativos, 175
  alertas bajo 1 MW que deciden (ponderado del lote). Las alertas perdidas siguen en 0: 0 de 78 protegidas medidas
  (censo) y 0 de 36 en la muestra de `pos_resto` (esta parte sigue siendo muestra).
- **Contra la predicción del verificador** (ΔE ≈ +11 si F publica todo cúmulo de cumbre en 0,0 MW, `far` de 0 a +59):
  se cumple; los `far` aportan 0.
- **Veredicto pre-registrado, con el censo**: ENCIENDE DE MÁS, ahora contado y no estimado, y pequeño: F gana 48 alertas
  débiles y enciende 60 negativos débiles. Lo de N-1 sobre el mecanismo se sostiene: el oráculo (el código entero) publica
  1 de esos 60 con la caja por defecto y 4 con el recuadro sensible, o sea que la detección del código no los ve.
- **Protegidas, de nuevo**: 0 perdidas de 78 medidas en todos los brazos. Chillán 2026-10-12 05:18 (MIROVA 8,44 MW en
  la referencia) sigue SIN DATO: CMR con credenciales no devuelve el gránulo por nombre, por día y caja ni por ventana,
  en tres intentos más (runs 39690106947 y 39693661527).
- **Oráculo, aparte** (predicado del tablero sobre un record sintético del oráculo, sin `store`): 1 de 119 negativos
  con la caja por defecto (Isluga 2026-07-15 05:36) y 4 con el recuadro sensible (más Tupungatito 2026-04-05 05:30,
  04-24 05:24 y 06-05 05:36). Sobre los otros 5.303 negativos el oráculo no tiene techo por censo (cambia la detección):
  su tasa en negativos sigue siendo de muestra (verificador, afirmación 3).
