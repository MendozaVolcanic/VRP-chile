# Programa de investigación de la réplica de MIROVA, por sensor (S162, 2026-10-24)

Pedido de Nicolás (2026-10-24): «más que sólo los frentes deberían haber planes para continuar los estudios y
experimentos para alcanzar los objetivos después de la información nueva que salió de la fórmula de VIIRS 750 que
encontramos»; «cada plan puede ir en sesiones diferentes o hijas»; «cada una con su loop si es que se puede».

Borrador de un agente planificador (Opus) que leyó el código de MIROVA, las auditorías S158 y S158 R2, los frentes S159
y los informes de S162; revisado por la sesión coordinadora (S162). Rutas relativas a la raíz del repo; entre corchetes
la rama cuando el archivo no está en `loop/activo`. Lo no medido va como SOSPECHA o SIN DATO. **Nada de esto se adopta
sin pre-registro, sello de Nicolás, verificador con contexto limpio, tag defensivo y su sí (A45).**

Actualización de la coordinadora sobre el borrador: CM162 (cúmulos por matriz) ya tiene verificador
(`experiments/_s162_vuelta2/VERIFICADOR_CUMULOS_MATRIZ.md`): CONFIRMADO EN PARTE, efecto más chico (7 a 13 de 290
publicaciones V750 en K, 1 protegida cruza 1 MW), y es **una sola divergencia con el doble conteo: D17 sin de-solape ni
remuestreo**. Pegar fragmentos no es neutro (un negativo limpio de PCC sube de 0,447 a 3,03 MW).

## 1. Diagnóstico en una pantalla

Criterio de victoria: `docs/MISSION.md:59-103` (ninguna protegida perdida en lectura A; suma de errores bajo 1 MW;
recall, negativos limpios y razón de magnitud por sensor y por tramo A119).

| | VIIRS 750 | VIIRS 375 | MODIS |
|---|---|---|---|
| Recall (K) | 72,9 % (n 48, 2026-08-24 a 10-23), fuera de banda (`experiments/_s161_estado_864/INFORME.md:29`); en el censo abr-oct K publica 77 de 78 protegidas y deja sin publicar 65 de 175 alertas bajo 1 MW ([s159-pruebas] `experiments/_s159/oraculo_censo/02_analizar_salida.txt`) | 96,8 % (n 93, ventana de #864) | 66,7 % (n 12); en la muestra del port K publica 48 de 50 protegidas y 32 de 42 bajo 1 MW (`experiments/_s159/portes/INFORME.md:66-68`) |
| Negativos limpios publicados (K) | 54 de 5.353 (1,01 %) | 3,7 %; 3,85 % ponderado en la muestra del port | 0,76 % (39 de 5.132) |
| Magnitud K/MIROVA | 0,510 [0,370; 0,733] n 115 ([s159-pruebas] `experiments/_s159/n/INFORME.md:156`); 0,178 sobre 50°, 0,163 Chillán sobre 50° (`experiments/_s159/oblicuo_paquete/INFORME.md:47,57`) | 0,651 [0,436; 0,848] (`portes/INFORME.md:110`); Chillán 0,65, Tupungatito 0,448 | 0,516 [0,311; 0,729] n 80; Chillán 0,485 n 7 |
| Mejor candidato medido | el código entero de MIROVA (port validado contra Octave en 791 de 791 escenas, `experiments/_s159/o1/INFORME.md:9-15`), remuestreado a la grilla GEO con la caja sensible (O-sens): 0 protegidas perdidas y 1 ganada, 15 negativos contra 54, ΔE −90; razón 0,999 [0,978; 1,007] | el mismo código con bandas I y grilla de 134 celdas: razón 1,000 [0,966; 1,019] n 61; negativos 0,9 % con cota honesta de 8,5 % | el mismo código (B22, MxD03, grilla 51 × 51): 50 de 50 protegidas, razón 1,006; el «GANA» contra K NO RESUELTO (neg_resto 0 de 37, cota 9,4 %) |
| Lo que falla hoy | detección y magnitud: cumbres en 0 MW, fragmentos oblicuos, modo de un píxel, fondo de anillo | magnitud (fondo y conteo); detección débil de Cordón Caulle y Tupungatito según la ROI | magnitud, geolocalización, cumbre nevada vista de lado (Chillán) |

### Lo nuevo que cambia la estrategia

1. **Las palancas sueltas sobre K quedan descartadas como camino a la paridad**: el fondo y la suma del código sobre
   K encienden de más (ΔE +12, `n/INFORME.md:265-272`); quitar la compuerta de 3 K no cambia ninguna publicación (0 de
   391, `n/INFORME.md:27-30`); D25 actúa como ganancia pareja (`lectura_s162/README.md`). El código entero en la grilla
   de MIROVA reproduce la magnitud al centésimo en los tres sensores. **El programa pasa de «probar palancas» a
   «adoptar el paquete del código por sensor, con brazos de diagnóstico adentro».**
2. **D25 sale del programa de la réplica**: MIROVA dilata el hueco, interpola con `fillmissing2`, suma todo y no
   recorta (`MIROVA_VIIRS750_VRP.m:63-85`); D25 en V750 publica el 100 % de las cumbres que K deja en 0 MW sin
   seleccionar (`experiments/_s162_vuelta1/VERIFICADOR_ENCENDIDAS.md`).
3. **Las cumbres de 0 MW no las calla la compuerta**: el código de MIROVA, sin compuerta, tampoco las detecta (1 de
   60 con caja por defecto, 4 de 60 con la sensible, `n/INFORME.md:256,273-274`). Qué pieza las calla es SIN DATO: de
   ahí V750-C.
4. **D17 (remuestreo) deja de competir y pasa a ser pieza obligatoria**: con la grilla GEO el oráculo da 0,999 (±2 %)
   y 0,996 sobre 50°; MIROVA no agrupa, publica la unión. Los cúmulos por matriz (CM162) quedan subsumidos.
5. **La ROI por volcán es el mayor riesgo para las protegidas**: con la caja por defecto el paquete V750 pierde 6
   protegidas de Cordón Caulle (`oraculo_censo/INFORME.md:89-102`).
6. **No se busca aplanar la curva con el cenit sino reproducir la de MIROVA**, que también cae (más oblicua sobre
   menos oblicua de la misma noche: MIROVA 0,503, oráculo 0,517, K 0,239; `tasks/LOOP_OBJETIVOS.md:1121-1122`).
7. **El instrumento tiene un hueco que ningún control veía** (12-oct: 44 pasadas ausentes en todos los brazos, una
   protegida de 8,44 MW; `experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`).
8. **Suomi NPP cesa el 2026-11-02 13:00 UTC**: toda ventana posterior es otro régimen.

## 2. Reglas comunes a todos los experimentos

- **Ventanas (A119, A104)**: **T**, tabla sola, decide: VIIRS 2026-04-01 a 06-12, MODIS desde 2026-03-01. **O**, tabla
  más OCR: 2026-06-13 a 2026-11-02 12:59 UTC, sin el 13 ni el 17-20 de octubre (D-29); el 12-oct sólo con los gránulos
  rescatados de LAADS o excluido en todos los brazos; siempre se informa la tabla sola al lado. **P**, prospectiva
  desde el 2026-11-03, sin Suomi NPP, confirmatoria.
- **Cortes**: #535 se informa por tramo aunque no separe brazos; adopción de K (2026-10-18 09:57 UTC) y cese de Suomi
  NPP para producción y sombra; TIF de MIROVA congelados desde 2026-09-22.
- **Métricas**: P1 veto de protegidas (lectura A, regla SN); P1b cruces de 1 MW **en las dos direcciones**; P2 suma
  bajo 1 MW por prueba de signos por bloque noche-volcán (D-45); M con comparador de ganancia pareja (D-28/D-30/D-32);
  placebo K × 1,2 obligatorio; todo por tramos de 10° de cenit, por volcán y por canal.
- **Escala**: 5 agentes y 2 A/B a la vez en todo el proyecto. Referencia congelada por hash.

## 3. VIIRS 750 (manda el código, decisión del 2026-10-21)

- **V750-C, ablación del oráculo** (primero; 0 runs, sólo lectura, sin sello). Hipótesis: el remuestreo a la grilla
  fija reparte el exceso de una cumbre tibia y la calla. Brazos dentro del oráculo sobre las grillas de N
  (`D:\vrp-trabajo\temporales\s159_n\run_39682867040\s159-n-chunk-*\grilla_*.npz`, 206 MB; que traigan la ventana
  nativa es SOSPECHA fuerte): O completo; O sin remuestreo; O con 8 vecinos; O sin recalcular la regresión del segundo
  pase; O con compuerta; O con recorte; O con K1 −0,8 y mínimo 0,010. Métrica: cuántas de las 55 cumbres en 0 MW y de
  los 6 negativos de F detecta cada brazo, razón en las 145 alertas, máscaras contra O. Decide si D17 es condición del
  paquete o si hay un paquete «sin remuestreo» para la detección.
- **V750-F, `fillmissing2` en MATLAB (O2)**: Nicolás corre `experiments/_s159/o1/o2_paquete/` en MATLAB Online (~15
  min). Cierra la banda de 1,82× en alertas de 1 píxel (`o1/INFORME.md:24-45`). No bloquea la publicación; sí M en 1
  píxel.
- **V750-B, ROI de MIROVA por volcán**. Hipótesis: en Cordón Caulle el calor está en el lacolito a 4,6-10,5 km del
  centro, en Tupungatito el cráter a 4,79 km NW del centro del TIF; MIROVA ajusta las ROI por volcán (el `.m` lo dice).
  Brazos: O-def, O-sens, caja 7 × 7 en el cráter del yaml, círculo `inner_radius_km` como caja sensible, O-sens sólo en
  PCC y Tupungatito. Ventanas T y O. Sustrato: 5.746 pasadas, 79 protegidas, 177 alertas bajo 1 MW, 5.476 negativos.
  1 run de sólo lectura, combinable con V375-B, V375-C y MOD-C. Necesita pre-registro y el sí para despachar.
- **V750-A, el paquete del código contra K** (adopción). Vía de proceso alternativa detrás de flag: port como
  procesador V750 + remuestreo con la regla GEO (centros `X0 ± 25.000` m, paso 750, `experiments/_s159/geo/INFORME.md:16-20`)
  + la ROI de V750-B, sin modo de un píxel ni tope D9 (N-5: el tope recorta una erupción real). Brazos: K, P, P-def,
  P-sinfiltro (publica todo lo que detecta), Kgeo (K con agrupación geográfica y huellas deduplicadas, diagnóstico de
  CM162). Métricas de §2 más identidad P contra oráculo pasada por pasada. Predicción: censo O-sens ΔE −90, 0
  protegidas perdidas. Sello y A45 para la implementación, el pre-registro y el despacho.
- **V750-D, cúmulos por matriz (CM162)**: verificado; se cierra como subsumido si V750-A se adopta; si no, A/B propio
  de Kgeo con PCC 2026-06-11 06:18 como caso de costo. Sonda L1B de fila/columna/`Bowtie_Deleted` en Chillán
  2026-10-14 06:18 como seguimiento (necesita el sí para despachar).
- **V750-E, rama diurna (D-10)**: 3 protegidas diurnas de Chillán sin record; después del paquete nocturno.
- **No es palanca**: el escalón de 50° del OSF (es del archivo, SOSPECHA fuerte).

## 4. VIIRS 375 (se traslada la estructura, no los números)

- **V375-A, higiene de la etiqueta de protegida** (primero, 0 runs): 5 de las 6 protegidas que «pierde» el port son
  alertas sólo OCR de Suomi NPP con fuentes a 9-24 km (`portes/INFORME.md:137-157`); con la tabla sola el port pierde 0
  de 29. Regla de «protegida de cráter» informada al lado de la lectura A, sin reemplazarla; arreglo de
  `scripts/clase_mirova.py:65-75` (cuenta FALSO_POSITIVO como protegida).
- **V375-B, negativos del port en neg_resto (D-36)**: 300 a 400 noches de 3.348; con 0 en 400 la cota baja a ~0,95 %.
  Pre-registro y sí; mismo despacho que V750-B.
- **V375-C, ROI en VIIRS 375**: brazos de V750-B con caja de 13, 14 y 21 celdas; 952 alertas bajo 1 MW.
- **V375-D, números propios de 375** (sólo si B o C lo exigen): conjunto cerrado de candidatos, elegido en T y validado
  en O (A115).
- **V375-E, paquete V375 contra K**: curva de razón por cenit comparada contra la de MIROVA, no contra 1 (la del port en
  375 es SIN DATO).
- **V375-F, Chillán sobre 3 MW** (port 0,939, n 6): después de V375-E.

## 5. MODIS (se traslada la estructura, no los números)

- **MOD-A, la cita de MOD03** (trivial): renderizar la p. 4 de
  `documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` y citarla (P1 y P3 discrepan).
- **MOD-B, MxD03 sobre K (D-19, tarea 1.30)**: pre-registro v2 en `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`;
  M midió 2,85 km de corrimiento y 12 de 63 publicaciones cambian sobre 40°; con la geolocalización de 5 km el código
  pierde 3 protegidas. ~47 h de runner. Sello, tag y despacho.
- **MOD-C, negativos del port MODIS (D-36)**: 5.093 noches en neg_resto; mismo despacho.
- **MOD-D, paquete MODIS contra K**: brazos K, PM (port con D33 corregido), PM sin MxD03. El déficit de Chillán (0,485)
  se juzga aquí. MODIS sólo corre en Linux.
- **MOD-E, bow tie de MODIS (D28)**: ablación local sobre las grillas del port (`D:\vrp-trabajo\temporales\s159_portes\`).

## 6. Perfil experimental (no se mide contra MIROVA)

Candidatas de S162: las cumbres tibias de 1 píxel que el 750 de MIROVA calla y su 375 alerta en la misma pasada; el
lacolito de Cordón Caulle; la magnitud en geometría nativa. Se validan contra OVDAS y SWIR (A115); bloqueadas por la
tarea 1.11 (cronología OVDAS de Nicolás).

## 7. Fases y puntos de decisión

| fase | qué | punto de decisión |
|---|---|---|
| 0 | instrumento (§8), V375-A, MOD-A | PD0: cada arreglo con prueba roja y mutaciones; sin eso no se despacha ningún A/B |
| 1 | V750-C, V750-F (Nicolás), MOD-E, y un despacho de sólo lectura con V750-B, V375-B, V375-C y MOD-C | PD1: piezas obligatorias, caja por volcán, silencio de los ports |
| 2 | V375-D si hace falta; MOD-B | PD2: números de 375; MxD03 sola o en el paquete |
| 3 | vía de proceso «código MIROVA» en `pipeline/` detrás de flag (A45), V750 primero; prueba de equivalencia contra el oráculo | PD3: la vía reproduce al oráculo pasada por pasada |
| 4 | paquetes V750-A, V375-E, MOD-D (A/B o sombra) | PD4: adopción por A45 |
| 5 | V750-E diurno, V375-F, V750-D si V750-A no se adopta | |

Combinar en un brazo lo que el `.m` acopla (remuestreo, Test 1 como alerta, 3 × 3 con central, umbrales, sin
compuerta, segundo pase con regresión, fondo sin recorte, suma, sin modo de un píxel ni D9); la atribución pieza a
pieza va en la ablación local. Aislar lo separable con riesgo propio sobre las protegidas: ROI, filtro de publicación,
geolocalización MODIS, D33, diurno, agrupación.

**Regla de posición del record (decisión de Nicolás, 2026-10-27, S165).** Sus palabras: «Sí: no fijes la regla
todavía; mídela como brazo (radiante, cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA».
- Los A/B de fase 4 (V750-A, V375-E y MOD-D) llevan tres brazos de posición sobre la misma detección:
  - **radiante**: centroide del cúmulo de la alertada más radiante, lo que hace hoy `procesar_grilla`;
  - **cercano**: el alertado más cercano al cráter;
  - **pico**: el píxel de mayor radiancia.
- La vara es lo que publica MIROVA. Cuentan también las pasadas en que MIROVA publicó una fuente lejana
  (`FALSO_POSITIVO` de la tabla), que la medición de S165 no pudo mirar en VIIRS (338 en VIIRS 375 y 19 en VIIRS 750).
- Evidencia: `experiments/_s165_regla_posicion/INFORME.md` y `verificador/INFORME.md`. «Cercano» cambia 8 de 2.012
  pasadas en VIIRS 375 (4 protegidas), 1 de 5.321 en MODIS (una publicación de más) y 1 a 2 de 5.640 en VIIRS 750.
  La distancia de MIROVA calza mejor con el píxel pico que con el centroide.
- Si un pre-registro ya está sellado, los brazos entran por adenda, antes de ver los datos.

## 8. Arreglos del instrumento antes de cualquier A/B nuevo

Existe R2.1 en #889 (borrador, toca `pipeline/fetch.py` y `scripts/run_pipeline.py`: A45). Falta:
1. **Cobertura contra la referencia de MIROVA**: para cada brazo y producción, pasadas de la referencia sin record a
   ±120 s por volcán, sensor y día; una protegida sin record en todos los brazos que producción sí tiene, o un día con
   pasadas de MIROVA y cero records, es falla de cobertura antes de leer el veredicto. Va en el evaluador (sin A45).
2. **«No observado» como estado propio** (volcán fuera del gránulo, escenas inválidas), fuera del denominador.
3. **Placebo de ganancia y comparador d′ en un evaluador común** (hoy sólo en `evaluar_d25.py`; MODIS no tiene
   evaluador), con los placebos de D-44.
4. **Una sola definición de alerta** en `scripts/clase_mirova.py` (canal, SN, ±120 s, distancia compatible, fuente
   lejana, arreglo de FALSO_POSITIVO).
5. **P1b en las dos direcciones** y conteo de publicaciones sobre pasadas RUTINA (VE162-03).
6. **Estratificación automática por cenit y régimen** (tarea 1.35).

## 9. Decisiones para Nicolás (con recomendación)

1. D25: no adoptar, cerrar como «no es el fondo de MIROVA» (sí).
2. Pasar de palancas sueltas a un paquete por sensor con brazos de diagnóstico (sí).
3. Validar el paquete con equivalencia + censo + sombra prospectiva desde el 2026-11-03 en vez de tres A/B
   retrospectivos (sí; la alternativa clásica cuesta ~3 runs de ~12 h por sensor).
4. Etiqueta de protegida de cráter informada al lado; decide la lectura A (no cambiar la vara sin medir).
5. Filtro de publicación del paquete: mantener el predicado de cumbre y medir P-sinfiltro.
6. ROI de Cordón Caulle y Tupungatito: medirla y enviar el correo ya redactado a Coppola
   (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`).
7. Correr O2 en MATLAB Online (15 min, tú).
8. D-36: lote de 300 a 400 negativos en VIIRS 375 y MODIS, en el mismo despacho que V750-B.
9. MxD03: sellar el pre-registro v2 y correrlo; adoptarla dentro del paquete MODIS salvo que se atrase más de un mes.
10. #889: mergear con tag y sí, más la cobertura contra la referencia en un PR del evaluador.
11. Vía de proceso «código MIROVA» en `pipeline/` detrás de flag, con el remuestreo GEO, después de PD1.
12. Tope D9 fuera del paquete, medido.
13. Tope de cordura de `store.py` (R2-7) aparte, con tag y sí.
14. Diurno (D-10) después del paquete nocturno.

## 10. Qué no reabrir y qué cierres quedan rebajados

**Vigentes**: K (#850; conectiva `max` confirmada por el código, B22 por el port); lectura A, regla SN y corte de
1 MW; el fondo del código sobre K enciende de más; la compuerta sola no cambia la publicación; negativo limpio con
cráter refutado; pareo MODIS ±120 s; escalón de 50° por zonas de agregación refutado; K1 casi no decide (3 de 791);
COB; tareas 1.9 y 1.13; D-29.

**Rebajados (cada uno pide su marca A113)**: tarea 1.8 «el modo de un píxel no se toca» (midió publicaciones, no
magnitud); tarea 1.14 «D25 es la palanca que más mueve» y las tareas 1.29 y 1.33; AUDIT_S158 §0.1 «la brecha entera es
el fondo» (Etna, N = 1); AUDIT_S158 §0.3 sobre la compuerta; AUDIT_S158_R2 §2 «el port es vara a pocos por ciento»
(sólo con 2 o más píxeles); D-13 y la «cobertura PAREJA» de los A/B; D17 «consecuencia NO» y la tarea 1.36; el radio de
20 km de PCC (condicionado a V750-B); la tarea 1.7 (caja 5 × 5, medida con `_interp_geo`); F5-09 (ahora con
mecanismo, verificado como D17); «MIROVA usa MOD03» (en disputa hasta MOD-A). ⚠️ **S162, 2026-10-25 (A113)**: MOD-A resuelto en el PR #902 (Coppola
2026 Sci Data p. 4, con p. 3 y p. 6): MOD03 es insumo también en el NRT; el método del remuestreo sigue SIN LOCALIZAR.
D35 queda registrada en el PR #906 con el veredicto de MxD03 (CUMPLE SIN DAÑO).

## 11. Sesiones hijas (cada una con su loop)

| sesión | alcance | cola y bitácora propia |
|---|---|---|
| Instrumento | §8, V375-A, MOD-A | `tasks/LOOP_INSTRUMENTO.md` |
| VIIRS 750 | V750-C, V750-B (diseño del despacho combinado), V750-A, V750-D, V750-E | `tasks/LOOP_VIIRS750.md` |
| VIIRS 375 | V375-B a V375-F | `tasks/LOOP_VIIRS375.md` |
| MODIS | MOD-B a MOD-E | `tasks/LOOP_MODIS.md` |

Reglas entre loops: cada sesión en su worktree y su rama, sin tocar archivos de otra; nadie escribe en
`tasks/LOOP_OBJETIVOS.md` salvo la coordinadora (S162); **todo despacho a GitHub Actions se pide a la coordinadora**
(grupo de un solo pendiente, tope de 2 A/B); el despacho combinado de la fase 1 lo arma la coordinadora con los brazos
que entreguen VIIRS 750, VIIRS 375 y MODIS; nada en producción sin sello, verificador, tag y sí; parada si C: o D:
bajan de 3 GB.
