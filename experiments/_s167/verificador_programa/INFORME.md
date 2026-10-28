# Verificación del programa por sensor tras las marcas S167 y el §12 (sólo lectura)

Documento revisado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\superpowers\specs\2026-10-24-programa-replica-por-sensor.md` (cambios sin commitear; el remoto `loop/activo` ya trae `1ffdb3155`, "programa por sensor actualizado, en verificador").
Hora del servidor al verificar: 2026-10-28 13:29 UTC. Verificador: Sonnet 5.5, contexto limpio.

## Veredicto: LISTO CON CAMBIOS

Las cifras y los PR se sostienen casi todos. Lo que falla es de juicio y de propagación: el orden entre sensores (§12.4), la regla de posición "después de leer los tres", la recomendación sobre la sombra, y varias marcas que cierran o generalizan de más.

## Caminos por los que el texto podía estar mal (escritos antes de leer las fuentes)

1. Cifra mal copiada (0,52 %, 2,48 %, 5.841, 330/329, 20, 7 contra 6 protegidas, 166 de 166, 18 de 18, 2 de 390, −41, 0,635).
2. Estado ya cambiado (W6, ramas, tags, shas, V750-A con VP-01 a VP-03, mutaciones de MOD-D).
3. PR mal atribuido o mal fechado (#889 contra #909, #915 como PR, #813, #864, #920 a #924).
4. Cita de bitácora a la entrada equivocada (A101).
5. "CERRADO" sobre algo cuya respuesta quedó SIN DATO (A111, A113).
6. Decisión atribuida a Nicolás que no tomó (D-48, regla N-3, regla de posición, PD1).
7. Regla generalizada a pre-registros donde no está (N-3 en V750-B, V750-A, MOD-D).
8. Orden de pasos imposible o contradictorio (§12.4 contra §12.2 y §12.3 y contra los pre-registros).
9. Sombra: perfil inexistente, fecha de inicio, costo en el NRT.
10. Texto viejo sin marca que sigue afirmando algo caído.
11. Violaciones de estilo (guiones largos, voseo).

## Hallazgos

### VP167-01 (gravedad 3): el orden de §12.4 y la frase "más avanzado / más cerca de PD4" no se siguen de la evidencia
- Frases: §12.4 "MODIS primero (su pre-registro es el más avanzado y no depende de otro sensor), VIIRS 375 después (lectura sin run largo)"; §12.3 "Es el sensor más cerca de PD4."; §12.2 "Es el segundo más cerca de PD4".
- Evidencia:
  - MOD-D fase 4 es **BORRADOR** (`git show ff03538dd:experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` l. 3) y su §11 (l. 291-335) lista 7 pasos por construir tras el sello (población, arnés `probe_f4.py`, identidad, externos, workflow, humo, tag y verificador) y ~14 h de runner en tres tandas, más sombra de 28 noches (§12.6).
  - V375-E tiene la **adenda 2 sellada** (tag `s166-v375e-adenda2-sellada`, batería 140 de 140), la vía en `main`, los datos retrospectivos ya corridos (S159, S162, S162b), y le falta una corrida de 350 pasadas de ~2,5 h (§8.8) y la lectura local.
  - V750-B está sellado y V750-A tiene el medidor casi listo.
  - El propio §12.4, tres líneas después, secuencia los despachos "W6, la corrida lejana de V375-E, V750-B el 2026-11-03 y MOD-D fase 4 cuando tenga sello y candado": V375 va antes que MODIS.
- Corrección propuesta: ordenar por trabajo restante: VIIRS 375, MODIS, VIIRS 750 (con MODIS y VIIRS 375 casi en paralelo porque los cupos se turnan). Cambiar "más avanzado" por el criterio medible (sellos, candado, runs pendientes). Corregir "más cerca de PD4" en §12.3 y "segundo" en §12.2. Dejar escrita la salvedad: V375 trae un veto probable (Isluga 06-17 y Láscar 10-01 con "radiante") y MODIS el riesgo de Chillán.

### VP167-02 (gravedad 2): "la regla de posición se decide después de leer los tres" contradice los pre-registros y atrasa el PD4 de los sensores más cercanos
- Frases: §12.4 "La regla de posición se decide **después de leer los tres** (la función es compartida), salvo que un sensor la necesite antes para su PD4."; §12.5 punto 5 "decidirla una sola vez, con los tres A/B leídos".
- Evidencia: cada pre-registro elige su brazo con su propia regla antes de su veredicto: V375-E §8.5 paso 1 y §8.13; MOD-D fase 4 §6 bis, y su §14 dice "La regla de posición de VIIRS 750 y VIIRS 375: cada sensor la mide en su propio A/B"; V750-A §6 bis (l. 139-160). O sea que **todo sensor la necesita antes de su PD4**, y la cláusula "salvo que" se come la regla. Las palabras de Nicolás (§7) son "no fijes la regla todavía; mídela como brazo en los A/B de cada sensor": no dicen "espera a los tres". Esperar a V750 (que recién lee después del 2026-11-03 y aún debe sellar V750-A) bloquea a los otros dos.
- Corrección propuesta: cada sensor aplica su regla de elección al leer; la unificación es posterior y opcional. Si dos sensores eligen brazos distintos, el costo es un parámetro por sensor en `procesar_grilla` (un PR a `pipeline/`, A45), que el propio §12.0 ya reconoce. Reescribir §12.4 y §12.5-5 en ese sentido, y presentar §12.5-5 como decisión pendiente de Nicolás, no como hecho en §12.4.

### VP167-03 (gravedad 2): la recomendación de no armar el perfil de sombra (§12.5 punto 4) choca con los tres pre-registros y su costo en calendario no se dice
- Frase: "*Recomendación: no armarlo todavía; cada sensor abre su sombra después de que su A/B retrospectivo salga CUMPLE ...*"
- Evidencia: V375-E §3 paso 3 (l. 57): sombra "desde el 2026-11-03", hasta 30 noches o 40 alertas; V750-A §4.3 (l. 104-108): "Desde el 2026-11-03 ... P corre en el NRT en un perfil sombra", 4 semanas; MOD-D fase 4 §12.6: "desde el 2026-11-03 o desde el sí de Nicolás si es posterior, 28 noches". Y V375-E §5.4 exige cumplir "en la lectura retrospectiva Y en la sombra prospectiva". Diferir la sombra suma 28 a 30 noches **después** de cada CUMPLE retrospectivo, y eso no aparece en "lo que falta para PD4". Que hoy no exista ningún perfil de sombra en `pipeline/profiles/` es correcto (sólo hay A/B `_s15x_*` y `experimental*`).
- Corrección propuesta: (a) escribir la consecuencia de calendario (PD4 no antes de unas 4 semanas tras el último CUMPLE); (b) considerar la alternativa de **un solo perfil de sombra con las tres vías encendidas** (los flags `ENABLE_V750_CODIGO_MIROVA`, `ENABLE_MODIS_CODIGO_MIROVA` y `ENABLE_V375_CODIGO_MIROVA` son independientes por sensor), con `data_subdir` propio (A47), midiendo antes su costo en el NRT con una corrida en seco; así las tres ventanas P parten juntas el 2026-11-03 o cuando Nicolás dé el sí; (c) dejar la decisión a Nicolás con ese costo a la vista. Hoy la recomendación pide esperar sin medir el costo que dice temer.

### VP167-04 (gravedad 2): "MOD-E CERRADO ... entra a MOD-D sólo como brazo informativo" no está respaldado
- Frase (§5, marca): "**MOD-E CERRADO** con los recortes nativos reales de MOD-C (no con las grillas del port); entra a MOD-D sólo como brazo informativo."
- Evidencia: la ablación real se hizo (bitácora S162 ~20:15 UTC, "ablación real del bow tie de MODIS (D28) verificada"), pero su resultado es "Efecto de D28 sobre la magnitud SIN DATO". El censo de MOD-D sacó PM-sin_dup de los brazos (`experiments/_s162_modis_paquete/PREREGISTRO.md`, VCD-03: "sale de los brazos"; §3: la eliminación de duplicados "no entra como brazo hasta que se localice el método de MIROVA"). Y el pre-registro de fase 4 (§14) lista "el bow tie (MOD-E)" entre lo que NO decide y no tiene ese brazo (§2).
- Corrección propuesta: "MOD-E hecho con los recortes nativos reales de MOD-C; el efecto de D28 sobre la magnitud queda **SIN DATO**; no es brazo de MOD-D ni de la fase 4 (sólo la clasificación informativa por costura del censo)". No usar "CERRADO" (A111).

### VP167-05 (gravedad 2): propagación incompleta de la regla N-3 (protegidas sólo OCR de Suomi NPP antes del 2026-10-09)
- Frases: §2 marca "igual en el audit semanal (#924) y en los pre-registros (N-3 en V375-E)"; §12.0 "V750-A y MOD-D fase 4 deben declarar si la aplican antes de su sello."
- Evidencia: sólo V375-E la tiene (`PREREGISTRO_E.md` §8.13). (1) **V750-B**, sellado y el primero en leerse (2026-11-03), decide en la ventana O con "tabla más OCR" (`PREREGISTRO_V750B.md` l. 96-107) y no trae N-3; el programa no lo menciona. Si hay protegidas sólo OCR de Suomi NPP antes del 10-09 en 750 (SIN DATO, no medido), podrían bloquear brazos de ROI, justo lo que N-3 evita en 375. (2) **MOD-D no tiene Suomi NPP** (MODIS es Terra/Aqua), así que declararla ahí no tiene objeto; su regla propia ya es otra (fase 4 §12 punto 5: "una protegida perdida sólo por el OCR va a DECIDE NICOLÁS y no veta"). (3) "los pre-registros" en plural exagera: es uno.
- Corrección propuesta: §12.0: "Aplicada en el audit (#924) y en V375-E. **V750-B (sellado) no la tiene: medir antes del 2026-11-03 si hay protegidas sólo OCR de Suomi NPP anteriores al 10-09 en 750 y, si las hay, decidir una adenda antes de leer.** V750-A debe declararla. En MOD-D no aplica (sin Suomi NPP)". Corregir también el §2.

### VP167-06 (gravedad 2): la marca de §9 dice que las 14 decisiones "se aplicaron" con sólo tres excepciones, y hay más
- Frase: "estas 14 decisiones ya están tomadas ... y se aplicaron. Excepciones: el correo a Coppola ...; el tope de cordura ... (13) ...; y el diurno (14) ...; punto 3 no se cumplió así".
- Evidencia: la decisión 11 ("vía ... detrás de flag, ... **después de PD1**") no se cumplió para VIIRS 750: la vía entró en `main` (#907, 2026-10-26) con `roi_v750: def` antes de que V750-B diera la ROI (`pipeline/grillas_mirova.yaml` en `origin/main`; el propio §7 lo dice: "entró antes de PD1 de VIIRS 750"). La decisión 8 ("D-36 ... en el mismo despacho que V750-B") tampoco: V375-B2 y MOD-C corrieron el 2026-10-24 por separado y V750-B sale el 11-03 solo. La decisión 7 (O2, "tú") la hizo la coordinadora con la cuenta de MATLAB Online que Nicolás activó (bitácora S163 vuelta 2).
- Corrección propuesta: agregar las excepciones 8 y 11 (y matizar 7) a la marca, o decir "se aplicaron, con desvíos en 3, 7, 8, 11, 13 y 14".

### VP167-07 (gravedad 2): §12.5 punto 2 omite la dependencia de V750-A respecto del resultado de V750-B
- Frase: "**Sello de V750-A**: esperar el medidor completo de mutaciones y el verificador de `equivalencia_v750a.py`. *Recomendación: esperar.*"
- Evidencia: `PREREGISTRO_V750A.md` §11 (l. 255-272) pone como pendiente antes del sello el "Resultado de V750-B (la ROI) y del brazo nativo N0/N1", y su cabecera dice "Depende de V750-B (la ROI)". El propio §12.1 paso 4 sí lo incluye ("incorporar la ROI de V750-B"). Si el medidor termina antes del 11-03, la lectura literal de §12.5-2 invita a sellar con la ROI sin decidir.
- Corrección propuesta: "esperar el medidor completo, el verificador de la equivalencia **y la lectura de V750-B**".

### VP167-08 (gravedad 2): "V375 NO EQUIVALENTE sólo por la regla de posición" es incompleto
- Frase (§7 marca): "V375 NO EQUIVALENTE sólo por la regla de posición."
- Evidencia: `PREREGISTRO_E.md` §8.3 (tabla) lista **dos** causas: la posición (NO EQUIVALENTE en 8 pasadas con máscara idéntica) y el "fondo sobre 4 píxeles" (40 de 329 fuera de 1e-3 MW contra `brazos.py` con el port viejo; lo resuelve la vara nueva del §8.6 b, aceptada por Nicolás al sellar la adenda 2).
- Corrección propuesta: "NO EQUIVALENTE en #921 por dos causas (posición en 8 pasadas y relleno del fondo sobre 4 píxeles en 40 de 329); las dos tienen vara nueva en la adenda 2 sellada, aún sin leer".

### VP167-09 (gravedad 1): cita de bitácora a la entrada equivocada
- Frase (§1 punto 6, marca): "esas cifras están en la entrada de S159 «gemelo de D25 medido; oblicuo y prompting entregados»".
- Evidencia: MIROVA 0,503 / oráculo 0,517 / K 0,239 están en `tasks/LOOP_OBJETIVOS.md` l. 2773, bajo el encabezado de la l. 2762 "2026-10-21 (S159, dueña del loop): negativo con cráter, código OSF, verificador del oblicuo; guía y censo del oráculo lanzados". El encabezado "gemelo de D25 medido..." (l. 2778) es otra entrada.
- Corrección: citar la entrada de la l. 2762.

### VP167-10 (gravedad 1): V750-B "SELLADO con las adendas 1 y 2" y las cifras de objetivos
- Frase (§3 marca): "**V750-B SELLADO** con las adendas 1 y 2 ... sobre 5.841 objetivos más 20 lejanas".
- Evidencia: la adenda 1 se declara "informativa, agregada después del sello" (l. 11 del pre-registro); sólo la 2 la selló Nicolás. 5.841 y 20 son del ensayo con ventana hasta 2026-10-26; "al 2026-11-02 serán unas 6.000" (§9 del pre-registro) y las 20 también cambian.
- Corrección: "sellado; adenda 1 informativa, adenda 2 sellada por Nicolás el 2026-10-28; 5.841 + 20 en el ensayo del 10-26 (unas 6.000 al 11-02)".

### VP167-11 (gravedad 1): "V750-F no lo corrió Nicolás"
- Evidencia: bitácora S163 vuelta 2: "Nicolás activó MATLAB Online basic (llenó él el formulario ...)"; la coordinadora subió el paquete y corrió. Reescribir: "lo corrió la coordinadora S163 en la cuenta de MATLAB Online que Nicolás activó".

### VP167-12 (gravedad 1): "fase 0 hecha" contra §8 ítem 4 "en parte"
- La marca de §7 dice "fases 0 y 2 hechas" y la de §8 dice que el ítem 4 (una sola definición de alerta) quedó "en parte" y que siguen abiertos `--cobertura-json` en `nrt.yml` y el ruido entre runners. PD0 exige "cada arreglo con prueba roja y mutaciones". Decir "fase 0 hecha salvo el ítem 4 de §8 (en parte)".

### VP167-13 (gravedad 1): estados sin verificar al 13:30
- "mutaciones finales sobre 53 escenarios sin commitear" (§12.3): el pre-registro commiteado en `ff03538dd` trae en su §13 "40 escenarios ... 46 de 46 mutaciones", aunque el mensaje del commit dice "bateria de 53 escenarios". El §13 no está al día con el 53; el sello (§12.5-1) debe esperar a que §13 diga la cifra final. SIN VERIFICAR el 53 con mutaciones.
- "W6 corriendo" (§12.0): el run 40681454167 figura `queued` a las 13:29 UTC (`gh run view`); el bloque S167 habla de 4 verdes, 3 corriendo y 15 en cola. Decir "W6 despachado (en cola o corriendo)".
- "medidor completo M1 a M85 ... corriendo" (§12.1 paso 4): según la bitácora S167 vuelta 2 "parte cuando termine la batería de identidad (26 de 74)"; SIN VERIFICAR que esté corriendo.

### VP167-14 (gravedad 1): cita textual no localizable
- §12 intro: «revisa el estado del plan de los 3 sensores y adaptalos o actualizalos segun los nuevos resultados». No está en `tasks/` ni en el bloque; no pude comprobarla (es del chat de la coordinadora S167). Lleva voseo ("adaptalos", "actualizalos"); si es literal de Nicolás, dejar entre comillas con "sic" o parafrasear en español de Chile.

## Respuestas a lo pedido

(a) Recomendaciones del §12.5: 1 (MOD-D), 3 (V375-E) y 6 se siguen de la evidencia. La 2 (V750-A) está incompleta (VP167-07). La 4 (sombra) y la 5 (posición) no se siguen; ver VP167-02 y VP167-03. Una mejor para la 4: medir el costo de una sombra ahora y armar un perfil único con los tres flags.
(b) Orden de §12.4: tiene un error (VP167-01).
(c) Marcas que rebajan algo vigente: no encontré ninguna. Lo contrario sí: marcas que cierran o generalizan de más (MOD-E, N-3 en "los pre-registros", "se aplicaron").
(d) Falta propagar: N-3 a V750-B (VP167-05); la dependencia de V750-B para el sello de V750-A (VP167-07); los desvíos 8 y 11 en la marca de §9 (VP167-06). Los pasajes sin marca que quedan (§6, §10, §3 V750-D y V750-E, §4 V375-F) siguen vigentes.

## Comprobado y está bien (con evidencia)

- PR: #902, #903, #904, #905, #906, #907, #909, #914, #919, #920, #921, #922, #923 y #924 MERGED en las fechas citadas (`gh pr view`); #889 CLOSED; #850 MERGED 2026-10-18 09:57:30Z; #915 y #813 son issues abiertos y #864 un issue cerrado (el texto no los llama PR). Tag `pre-s163-merge-909` existe.
- Tags: `s162-v750b-adenda2-sellada` (anotado, `609fa1c88`), `s166-v375e-adenda2-sellada` (`67838f2a5`); rama `claude/s166-modd-f4` en `ff03538dd`; `5c45c0c07` es ancestro de `claude/s162-viirs750-2-918174` (hoy `0f16adaa8`).
- Flags (`VRP_PROFILE=mirova_equivalent`): `ENABLE_V750_CODIGO_MIROVA`, `ENABLE_MODIS_CODIGO_MIROVA`, `ENABLE_V375_CODIGO_MIROVA`, `ENABLE_MODIS_GEO_MXD03` y los otros dos de MxD03 en False; `ENABLE_MODIS_B22_PRIMARY` True. `pipeline/` de `loop/activo` es igual al de `origin/main`.
- `pipeline/grillas_mirova.yaml` (main): `roi_v750: def` en los 11 volcanes.
- V750-C: dos piezas (23 de 38 dentro; Tupungatito 17, PCC 4, Láscar 1 fuera), 7 protegidas perdidas, todas de PCC (71 de 78) (`experiments/_s162_v750c/INFORME.md`).
- V375-B2: 6 de 1.165, 0,52 % [0,24; 1,12], cota 2,48 %. MOD-C: 2 de 390, INDECIDIBLE. Censo MOD-D: P2 neto −41, DECIDE NICOLÁS por P1b = 1, Nicolás aprobó CANDIDATO el 2026-10-26; Chillán 6 de 7 p 8/128 y 0,635 (n 7).
- #915: recall MODIS 62,5 % (n 16) y V750 74,0 % (n 50). #924: regla de Suomi NPP antes del hito y pérdida aceptada de PCC; el punto "mismo objeto" quedó fuera del PR.
- V375-E: adenda 2 sellada, cuerpo en borrador por su propio encabezado, N-3 (§8.13: Isluga 09-28 y 10-03 dejan de vetar; Isluga 06-17 y Láscar 10-01, NOAA-21, siguen), 330 pasadas lejanas (329 de la tabla), §8.8 con 350 pasadas, ~2,5 h, 14 trozos, rama `s166-v375e-far-disparo`; el 12-oct queda excluido.
- V750-B: brazos B0 a B5, K, N0/N1; 5.841 + 20 (ensayo); tres cambios de la adenda 2; "no antes del 2026-11-03" y fuera del despacho combinado (bitácora S162 17:40 UTC).
- V750-A: brazos K, K×1,2, O, P, P-def, P-sinfiltro, Kgeo, P-cercano y P-pico; borrador; #907 en main antes del sello.
- MOD-D fase 4: brazos K, V, V-cercano, V-pico, placebo y V-grilla; 8 decisiones en su §12; sombra 28 noches; humo ~25 con Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20; ~14 h en tres tandas.
- Bit a bit run 40683093630: VERDE en 375 y 750, 44 por lado, control ROJO, sustrato real. NRT: 12 records MODIS iguales. MOD-B ~15 h y no 47. Probe 40584157486: 18 de 18 y 18 de 18.
- Diurno: adenda 1 y regla (VIIRS 750 no se adopta solo; MODIS no entra) en `experiments/_s163_diurno_k/PREREGISTRO.md`.
- §11: `LOOP_MODIS.md` en `e15e50153`, `LOOP_VIIRS750.md` en la rama de Loop VIIRS 750 2; en `loop/activo` sólo `LOOP_OBJETIVOS.md` y `LOOP_VIIRS375.md`.
- Conteo de guiones largos y medios: 0; sin voseo salvo la cita de VP167-14. No hay perfil de sombra en `pipeline/profiles/`.

## No pude comprobar

- La cita de Nicolás del §12 (chat de la coordinadora S167).
- Que el medidor completo de V750-A y las mutaciones finales de MOD-D estén corriendo (13:30 UTC).
- Los 53 escenarios de MOD-D (el texto commiteado dice 40; el mensaje del commit dice 53).
- Qué protegidas sólo OCR de Suomi NPP hay en VIIRS 750 (necesario para VP167-05).
- El estado final de W6.
