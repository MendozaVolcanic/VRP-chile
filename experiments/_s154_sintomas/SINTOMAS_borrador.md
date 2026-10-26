# Índice por síntoma (BORRADOR de `docs/SINTOMAS.md`, tarea 1.34 del loop)

> Borrador escrito el 2026-10-18 (S154) en `experiments/_s154_sintomas/`. No es aún el documento vivo. Cada número
> sale de un archivo leído al escribirlo, con su ruta y sección; lo que no se pudo comprobar dice **SIN VERIFICAR**.
> Una afirmación con marca ⚠️ de rebaja se cita como rebajada, nunca como cierre vigente (A113).

## Cómo usar este índice

1. Llegas con un síntoma («la magnitud sale baja»), no con un número de divergencia. Busca el síntoma acá.
2. Lee **MEDIDO** antes de proponer nada: casi todo síntoma ya tiene una medición, y a veces tres que no coinciden.
3. **Estratifica antes de concluir.** Fronteras de régimen que cambian cualquier métrica:
   - **#535**: 2026-08-28 23:00 UTC (máscara de nube de 260 K apagada; A104 en `CLAUDE.md`).
   - **K adoptada** (#850): 2026-10-18 09:57:30 UTC (`tasks/LOOP_OBJETIVOS.md`, bitácora 2026-10-18 10:10 UTC). K =
     sin Test 1, conectiva `max`, banda 22 primaria en MODIS (`experiments/_s151_prereg_fk_11/PREREGISTRO.md` §2;
     hoy en `pipeline/profiles/mirova_equivalent.yaml`: `enable_test1_path: false`, `enable_tests_23_prose_branch:
     true`, `enable_modis_b22_primary: true`). El histórico con K está corriendo (tarea 1.24): hasta que se aplique,
     la serie mezcla C0 y K.
   - **Gates intra-radio**: los records MODIS de enero a junio de 2026 (3.231) se escribieron con los gates
     encendidos y nunca se reprocesaron (A85, marca S153, en `CLAUDE.md`).
   - **Calidad de la referencia** por mes y por canal (A119 y sus correcciones S151; `scripts/calidad_referencia_mirova.py`).
   - **Cenit del sensor**, **sensor**, **volcán** (con y sin `local_kernel_bg`: PCC, Villarrica, Chaitén, PP,
     Lastarria, según D25 en `docs/MIROVA_DIVERGENCES.md`).
4. Al cambiar una divergencia, se actualiza su síntoma en el mismo PR (A113).

---

## S1. Magnitud baja contra MIROVA

**El fenómeno.** MIROVA suma el exceso de radiancia de todos los píxeles que alertó, con el fondo de cada uno igual
a la media de sus vecinos no alertados, sobre una grilla remuestreada. Nosotros podemos perder energía por cuatro
lados: el ángulo de la pasada (el píxel oblicuo cubre más terreno y el foco se diluye), el fondo (un anillo de valle
tibio resta más que los vecinos del cráter), la selección (alertamos menos vecinos) y el recorte de lo publicado.

**MEDIDO**
- **Ángulo, versión S130** (`docs/s130/GRADIENTE_CENITAL.md`, tablas 1 y 2; script
  `experiments/_s130_cenital/medir_gradiente_cenital.py`; `pc.vrp_mw`, CONS ∪ OCR, noche, ventana 2026, 11 Tier A).
  VIIRS 375: razón 0,740 a 0-15° (n 385) y 0,253 sobre 50° (n 1.144); MIROVA plano (0,23 a 0,27 MW medianos) y lo
  nuestro cae 2,7×. VIIRS 750: 0,781 a 0,326. MODIS no monótono (0,778, 0,828, 0,862, 1,253, 0,400; 17 a 21 pares
  por bin): **no probado en MODIS**. Lo atribuye al remuestreo de MIROVA (D17).
- **Ángulo, versión S133** (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`, «El número que decide»; VIIRS 375, 643 pares,
  2026-04-01 a 05-31): control 0,879 a nadir y 0,619 sobre 50°. Mismo signo que S130, curva mucho más suave.
- **Ángulo, versión 1.14** (`experiments/_s151_presupuesto_magnitud/README.md` §3.2, verificado PARCIAL): R 0,76 a
  nadir y 0,45 en el borde (VIIRS 375 sin kernel, OSF 2025). El Npix de MIROVA **no** crece con el ángulo (3, 5, 5,
  4), así que la curva **no** es la firma del remuestreo; F_bg cae de 0,85 a 0,73. Queda **SIN ATRIBUIR**.
- **Ángulo, versión 1.19** (`experiments/_s151_angular_119/INFORME.md` y `verificador/VERIFICADOR.md`, PARCIAL): la
  huella nativa con la agregación del ATBD aplana R a 0,80-0,87 en Láscar, Isluga y Copahue (máx/mín 1,09), pero con
  todos los volcanes no aplana (1,26) y el verificador sólo sostiene el escalón de MIROVA a 52,66°; «no cierra D17»,
  sin palanca que pre-registrar (bitácora 2026-10-16 08:15 UTC).
- **Fondo (D25)** (`docs/MIROVA_DIVERGENCES.md` D25; 1.14 §3.4): fondo por vecinos 1,28 [1,21; 1,35] sobre 468
  pasadas VIIRS 375 dentro del brazo `literal` (no sobre producción), 1,18 a nadir y 1,41 en el borde; Isluga 1,72,
  Tupungatito 2,37, Láscar 1,20, Lastarria 0,91 (empeora). En VIIRS 750 el sustrato es fidelidad de magnitud, no
  recall: 1.035 de 9.338 pasadas con el cráter en 0,0 MW, premio en noches cero (D25, «S145, sustrato»). Tarea 1.5:
  D25 calza la magnitud (mediana 1,19 en 28 rescates) pero el cierre quedó condicionado a la detección
  (`tasks/LOOP_OBJETIVOS.md` 1.5).
- **Selección de vecinos (A103)**: los vecinos tibios se pierden en la detección, no en el ensamblado (dETI en 52 de
  52 en la ruta contextual, compuerta de BT en 18 de 18 en la del Test 1, piso C1 = 0,003 en los 70;
  `docs/HYPOTHESIS_LOG.md` H_S141_VECINO_FOCO_V2, **no confirmada**, el desglose es post hoc).
- **A99 rebajada**: el 0,995 «a igual conteo» compensa 1,140 (píxel caliente) contra 0,873 (fondo) y 0,66 (Copahue)
  contra 1,39 (Villarrica); no apaga la búsqueda en k, área, banda ni Planck (A99, marca S146, `CLAUDE.md`).
- **Recorte publicado (D32)**: sumar todos los alertados cierra el 26 % de la brecha en VIIRS 375, nada en Láscar e
  Isluga (+0,031 y +0,015) y se pasa en VIIRS 750 (D32, tabla «Cuánto vale»). F_rec en Láscar, Isluga y Tupungatito
  ≈ 1,00; en Lastarria 0,86 (1.14 §3.3).
- **K bajó la magnitud**: VIIRS 375 0,762 a 0,669 y VIIRS 750 0,594 a 0,534 en V2 (bitácora 2026-10-18 02:39 UTC);
  ninguna protegida cruza bajo 1 MW (02:54 UTC).
- **Chillán en erupción** (tarea 1.33, «Primer resultado», `tasks/LOOP_OBJETIVOS.md`): 10 de 10 alertas nocturnas
  publicadas, razón 0,12 a 0,72 (mediana ~0,46); 0,64-0,72 a 20-22°, 0,41-0,46 a 49°, 0,35 (375) y 0,12 (750) a 67,6°.
  **SIN VERIFICAR**: no hay script ni salida guardados en el repo (el commit `730cd733` sólo toca el archivo del
  loop) y no pasó por verificador. Sin saturación en la erupción: 0 píxeles saturados en 385 gránulos (tarea 1.18).

**CONTRADICCIÓN ABIERTA (decide qué pre-registrar).** 1.33 y la tarea 1.36 leen la curva de Chillán como D17 citando
S130. Pero 1.14 §3.2 retiró explícitamente «el ángulo es D17» (arreglo c de su verificador), 1.19 no lo cierra, y la
nota S141 de D17 dice que el grupo MIROVA escribe que su remuestreo corrige el cenit sólo «partially» y que su propio
VRP cae con el ángulo (Aveni et al. 2023, citado en D17). S130 tampoco controló el fondo, que 1.14 ve empeorar con el
ángulo y que D25 corrige más en el borde. **Hoy la dependencia angular es real y su mecanismo está SIN ATRIBUIR**;
D17 y D25 son candidatos que compiten por la misma curva.

**ABIERTO**: D17 (premisa probada, consecuencia no; grilla F70 mal centrada, mediana 368 m, 6 de 11 sobre 187 m),
D25, D28 (bow tie, parte de D17), D32; tareas 1.33, 1.36 (D17 sobre K, antes que D25), 1.29 (D25 sobre K).

**NO REABRIR**
- Área geolocalizada completa: se pasa de largo (1,36 en el borde, 20,1 % de razones sobre 2; S133 chunk 1,
  veredicto parcial). La ley de huella de 1.19 es ~15 % más suave y también se pasa con todos los volcanes.
- Regrid F70: refutado en S124 (D16), con título rebajado en S146: lo refutado fue F70, no la grilla de MIROVA.
- Modo de un píxel en erupción: 0 publicaciones cambian (tarea 1.8). Preferencia I/M: no existe en el NRT (1.9).
- No usar el «1,35×» de D5: sin respaldo desde S125 (D5, marca S125).

**ESTRATIFICAR**: por cenit (≤ 40° obligatorio antes de atribuir el ~0,7, nota S141 de D17), por sensor (MODIS sin
curva probada), por volcán con y sin kernel local, y por régimen (pares S130 y 1.14 son anteriores a K; 1.14 §3.3
muestra que «abr a ago» de producción es código previo a #535). Unidad: `pc.vrp_mw` vs magnitud publicada (A10
rebajada; `f5_core_vrp_mw` en VIIRS 375).

---

## S2. Magnitud alta contra MIROVA

**MEDIDO**
- Tope D9 de 5 MW: 1.565 cúmulos topados (277 `summit`) y 343 sobre 5 MW (110 `summit`), corpus al 2026-10-14 (A23,
  marca S151; D9, estado S151). El tope recorta; no está medido que lo recortado sea artefacto.
- Volcanes con kernel local: R cerca o sobre 1 (1.14 §3.1). A99 rebajada: Villarrica 1,39, Planchón-Peteroa 1,33.
- Suma de alertados en VIIRS 750: 17,4 % de pares sobre 1,5× y 7,3 % sobre 10× (D32).
- Kernel-bg en glaciar: Tupungatito empeora 10,37× a 18,46× (A19); D25 infla donde el anillo es más frío que el
  entorno del foco (D25, «Fenómeno»).

**ABIERTO**: D9 en la cara de co-validación del path D (A23, marca S146). **NO REABRIR**: el gate por `t_bg`
(anti-MIROVA, A23). **ESTRATIFICAR**: por volcán (kernel local), por `primary_cluster.d9_capped`, por cenit (toda
corrección de área se pasa en el borde).

---

## S3. Sobre-publicación (publicamos donde MIROVA no vio nada)

**MEDIDO**
- La brecha de paridad es sobre-publicación, no recall: 874 de 877 noches con alerta detectadas (A98).
- VIIRS 375 en negativos limpios: 62,1 % antes y 87,1 % después de #571 (A104).
- Con el Test 1 encendido la tasa es 80 a 92 % en cualquier estrato; sin él aparece estructura (18,6 / 25,0 / 38,1 %
  del nadir al borde; 12,2 / 27,9 / 42,0 % del fondo tibio al frío) (A114).
- K en V2: negativos limpios MODIS 10,8 a 0,9 %, VIIRS 375 85,4 a 3,7 %, VIIRS 750 21,8 a 1,1 % (bitácora 2026-10-18
  02:39 UTC). K publica un subconjunto estricto de C0; de las 1.363 pasadas que deja de publicar, 713 son negativos
  limpios y 21 positivas (`experiments/_s153_localizacion/verificador/INFORME.md`).

**ABIERTO**: sombra de K (1.28); D22, D26, D30; sonda de los tres campos (1.2). **NO REABRIR**: gates intra-radio
como «protección» (A85; pero bajo la regla de la anomalía mayor «0 robos» ya no es la vara, marca S151). D22 se
resolvió sin A/B (1.3). **ESTRATIFICAR**: negativos limpios según A98; antes y después de #535 y de K; por zona del
barrido y temperatura del fondo (A114). Antes de filtrar, clasificar artefacto contra cat-b real (A54, A72).

---

## S4. Pérdida de recall (MIROVA alertó y no publicamos)

**MEDIDO**
- K en V2, lectura A: MODIS 39 de 39 protegidas (C0: 6), VIIRS 375 38 de 38, VIIRS 750 42 de 42; con OCR, VIIRS 375
  57 de 59 (bitácora 2026-10-18 02:39 UTC). Las 4 alertas que K no publica son lejanas, no pérdida neta (vuelta 183).
- MODIS 2026 en C0: 6 pasadas con alerta publicadas antes de #535 y ninguna después (etiqueta `far`, 1.14 §3.5).
- Estrato fuera de las etiquetas: 50 publicaciones apagadas en noches en que MIROVA alertó por otra pasada (A118).
- Alertas de VIIRS 375 de 0,05 MW o menos cuentan como «MIROVA no vio nada» (regla SN, D-9; glosario «Recall»).

**ABIERTO**: D12 (rebajada S146: las «76 FN» no son FN), MxD03 sobre K (1.30), 1.17. **NO REABRIR como cierre**: el
«irreducible» de A82, A83 y A84 (rebajados S124, S138 y S146). **ESTRATIFICAR**: por noche-volcán y no por record
(A94), por canal de la referencia (tabla sola en ventanas antes del 2026-06-13, A119), por sensor.

---

## S5. Posición corrida del cúmulo o del marcador

**MEDIDO**
- MODIS: `_interp_geo` ignora el offset 2 de la grilla de 5 km y corre cada píxel hacia el nadir; MxD03 se baja y no
  se usa (`experiments/_s151_corrimiento_modis/README.md`, veredicto, verificador PARCIAL). Láscar bajo 35°: MxD03
  más cerca de lo que ve VIIRS, dd 0,62 km [0,32; 0,96], n 76 (tarea 1.23).
- Marcador del mapa en records `ctx_cluster`: era `anomaly_pixels[0]`; arreglado en #853 (tarea 1.31).
- K no relocaliza: deja de publicar las pasadas con cúmulo en el borde del disco del Test 1 (verificador de
  `_s153_localizacion`). Records Test 1 dominantes van al cráter a 0,0 km (D11-bis).
- Grilla F70 descentrada de MIROVA: mediana 368 m, máx 2.996 m (D17).

**ABIERTO**: 1.30, 1.17, D11 (condicionada S138), D19 (keep_peak). **NO REABRIR**: re-ancla `ctx_cluster` por la vía
de A84 (pero A84 hereda la rebaja de A82). **ESTRATIFICAR**: por satélite y cenit (el corrimiento MODIS crece con el
ángulo), mediana del offset con rumbo y no media de la distancia (A70), separar marcador de cúmulo. `Distancia_km`
no trae acimut y está cuantizada a su grilla: un radio no es una posición (A93, D15, A107).

---

## S6. Detecciones lejanas (`far`, extensión)

**MEDIDO**
- La cerca `distance_class != summit` apaga 31 % de los records y 70,7 % de la magnitud (D13, título rebajado S146).
- A46 es bidireccional; far→summit en 15 a 17 % de los records de cada mes, 9.196 en total (A81, marca S130).
- PCC «lejos» es el lacolito real a ~7 km (A68).

**ABIERTO**: 1.4 (`vrp_max` contra `vent_anchored`; D-6: la réplica debe reproducir también lo lejano; universo 359
lejanas nocturnas). **NO REABRIR como cierre**: el «NO destapar» de A81 (rebajado S146). **ESTRATIFICAR**: por
volcán (`inner_radius_km` 3 a 20 km), por sensor (MODIS por el corrimiento de S5).

---

## S7. Diferencias diurnas

**MEDIDO**: MIROVA procesa VIIRS de día; bajo A119, 40 pasadas protegidas diurnas contra 232 nocturnas
(`experiments/_s151_alertas_diurnas/README.md` §5); 135 filas de alerta diurna, 97 protegidas. A/B W2 a W6 sobre C0:
NO ADOPTAR, que no se traslada a K (tarea 1.25). Reflejo solar en nubes: A76 (su cita de Coppola 2023 está rebajada).

**ABIERTO**: 1.32 (diurno sobre K, adenda sellada D-25), D-10, D27 (deliberada). **ESTRATIFICAR**: por sensor y
elevación solar; el q_neg del evaluador debe ir por sensor (1.32, H1).

---

## S8. Un A/B que «no cambia nada» o «mejora demasiado»

- **No cambia nada**: ¿algo satura la métrica? (A114); ¿el flag llega a todos sus consumidores? (A118, la caja D18 y
  el segundo pase); ¿el instrumento puede dar distinto de cero? (A116); ¿hay sustrato? (memoria S130).
- **Mejora demasiado** (más de 30 %): audit independiente antes de aceptar (tabla de skills, regla S33).
- Siempre: cobertura pareja por brazo (A108), mismo pipeline en las dos máquinas (`argsort` inestable según la CPU,
  memoria S152; despachar cada ventana desde un tag), árbol quieto (A112), caso objetivo además del agregado (A79),
  nulo medido (A110).

---

## S9. Referencia de MIROVA incompleta o desfasada

**MEDIDO**: tabla sana desde marzo; OCR con geometría mal calibrada hasta el 2026-06-11 y sin distancia hasta el
06-13; las cifras «86 % en enero» y «0 alertas MODIS del OCR» cayeron en S151 (A119 y su marca). El OSF v2.5 es
filtrado, sus conteos no valen para el NRT (A105). TIF: UTM nativo sólo del 2026-09-14 06:36 al 09-15 06:24 (A106);
archivo congelado desde el 2026-09-22 (tarea 1.33; memoria `reference_mirova_tif_congelados_20260922`). Alerta «sólo
OCR» puede traer distancia de otra pasada (memoria `reference_ocr_imagen_de_otra_pasada`).

**ESTRATIFICAR**: por canal (CONS contra OCR) y por mes; usar la referencia congelada de la unión histórica, no el
consolidado vivo, que pierde filas (A119, marca S151).
