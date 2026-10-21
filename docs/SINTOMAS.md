# Índice por síntoma

> Creado S157 (2026-10-20, tarea 1.34 de `tasks/LOOP_OBJETIVOS.md`, rama `loop/activo`). **Por qué existe**: el
> 2026-10-19 se atribuyó la caída de magnitud de Chillán a D17 citando una lectura de S130 que la tarea 1.14 ya
> había retirado. El conocimiento estaba, pero repartido entre `docs/MIROVA_DIVERGENCES.md`, las reglas A-n de
> `CLAUDE.md` y los documentos de sesión, y se busca por número cuando uno llega con un síntoma.
>
> **Cómo se usa**: antes de proponer una palanca, leer el síntoma acá, seguir los punteros y estratificar por
> cenit, sensor, volcán y régimen (C0 antes del 2026-09-18, K después; antes y después de #535). Este archivo
> **no es fuente de verdad**: resume y apunta. Si un puntero y este resumen discrepan, manda el puntero, salvo que
> el puntero no tenga todavía la marca ⚠️ de lo que aquí se dice rebajado (entonces la discrepancia es un hallazgo
> A113: se marca el puntero en el mismo PR). **Se actualiza en el mismo PR en que cambia una divergencia** (A113).
>
> **Convención**: `D25` (sin guion) es una divergencia del catálogo; `D-19` (con guion) es una decisión de Nicolás
> en la tabla de decisiones de `tasks/LOOP_OBJETIVOS.md`. Las tareas `1.n` y las decisiones `D-n` posteriores a
> S150 viven en la rama `loop/activo` de ese archivo, no en `main`. Lo que no está en `main` lleva su rama o PR.

Régimen vigente: el detector K está en producción desde #850 (2026-10-18): sin Test 1 integrado (D30), conectiva
`max` en los Tests 2 y 3, banda 22 primaria en MODIS (D21). En los datos rige desde la observación del 2026-09-18
(`frontend/cambio_detector.js`, `DATOS_K_DESDE_UTC`), salvo 26 records MODIS Terra; la frontera se moverá más
atrás cuando se aplique el reproceso histórico con K (marca S157 de `docs/MISSION.md`). Cifras de la adopción:
`experiments/_s153_fk_v2/combinado.log` (veredicto), `r3/controles_salida.txt`, `v1.log` y `v2.log`; regla
`experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`. Todo lo medido con C0 hay que releerlo con eso.

## 1. Magnitud baja contra MIROVA

**Medido**
- La razón contra MIROVA cae con el cenit del sensor. S130: VIIRS 375 de 0,740 cerca del nadir a 0,253 sobre 50°,
  MIROVA plano (`docs/s130/GRADIENTE_CENITAL.md`). En MODIS no es monótono. La curva es real; su explicación por
  D17 está retirada (siguiente punto y marca S157 de D17).
- Tarea 1.14 (`experiments/_s151_presupuesto_magnitud/README.md`): el reparto selección/fondo depende de la
  bisagra; **§3.2: el ángulo NO es la firma del remuestreo** (el Npix de MIROVA no crece hacia el borde; lo que
  empeora es nuestro fondo, F_bg 0,85 a 0,73). La dependencia angular queda SIN ATRIBUIR. D25 es la palanca que
  más mueve (§3.4: ×1,28 medido dentro del brazo `literal`, no sobre producción; crece hacia el borde, Tabla C2).
- En tensión con lo anterior: AUDIT_S155 F5-03 (`docs/AUDIT_S155.md`): en VIIRS 375 de Chillán el fondo no explica
  la caída con el ángulo (con fondo cero la razón sigue cayendo).
- Chillán en erupción con K, 87 pasadas (PR #869 ABIERTO, rama `s157-magnitud-chillan`,
  `experiments/_s157_magnitud_chillan/README.md`, verificador PARCIAL): en VIIRS 375 oblicuo **ni con fondo cero
  se cierra el déficit**; en VIIRS 750 de borde pesa el recorte del tablero (F_rec 0,57). Recomienda D25 primero
  con el criterio de Chillán corregido (V375 sólo con cenit de 40° o menos) y D17 después. Tabla por cenit:
  script `razon_por_cenit` en `experiments/_s154_chillan/`, que sólo existe en la rama `loop/activo` (por eso no
  va como ruta completa: el guard G2 de S146 rechaza rutas que no están en `main`).
- AUDIT_S155 F2-02: Chillán se ve un nivel más abajo que MIROVA (24 de 38 Moderado mostradas como Bajo o Muy Bajo);
  no es propio de K y depende del cenit.
- AUDIT_S155 F5-01: en VIIRS 750 de Chillán (13 de 37 pasadas) se publica un cúmulo parcial; 36 % del déficit es el
  modo de un píxel y 64 % la selección. La tarea 1.8 (`experiments/_s151_modo_un_pixel/README.md`, bajo C0) había
  medido que el modo sólo decide en VIIRS 750 y no cambia publicaciones. Y F5-09: VIIRS 375 cuenta doble en el borde
  del barrido (6 de 51 pasadas de Chillán, todas sobre 50°), lo que infla en vez de bajar.
- D33 (#872, mergeado con flag apagado): con K la vuelta a radiancia de MODIS usa la λ de B21 sobre temperaturas
  de B22; encender el arreglo sube la magnitud MODIS +5 a +7,5 % (`experiments/_s157_lambda_b22/README.md` §9).
  No es la palanca de Chillán. Encender `enable_modis_mir_lambda_por_banda` es decisión de Nicolás (A45).
- D32: MIROVA publica la suma de todos los alertados; nosotros un recorte (cúmulo, y en banda I su núcleo). A10
  quedó rebajada en su premisa (`pc.vrp_mw` no es «lo que MIROVA reporta»). AUDIT_S155 F3-06: el auto-audit usa
  `pc.vrp_mw` y mezcla sensores, así que su «K/C0 = 1,0» no es la magnitud publicada.
- Vecinos tibios en VIIRS 375 (`docs/HYPOTHESIS_LOG.md`, H_S141_VECINO_FOCO_V2, bajo C0, 38 pasadas focales): ningún
  test limitante común y el fondo del cúmulo no cierra la brecha en ningún volcán focal; los nevados quedaron
  INDETERMINADO. Es sobre la selección de vecinos, **no evalúa D25**. H_S143_D22_D25 (mismo archivo) es el A/B de
  D22 y D25 en V375.
- En M-band el efecto dominante de D25 cae del lado de la sobre-publicación (`experiments/_s145_d25_v750/sustrato.py`,
  sección S145 de D25).
- Saturación en Chillán: 0 píxeles saturados en 385 gránulos (tarea 1.18; citado en
  `experiments/_s155_audit/frente_5/INFORME.md`). D24 (MODIS DN 65533 se elimina) sigue abierta.

- S158 (`docs/DISENO_D17_REMUESTREO_UTM.md`): los TIF UTM de MIROVA muestran que su grilla no está centrada en `mirova_center`
  (falla hasta 310 m), que es UTM verdadera y que MIROVA interpola; nuestro F70 deja huecos en oblicuo y pierde energía con el
  ángulo como el área fija. Propone una Fase 0 de sólo lectura (reproducir los TIF) y un A/B sólo VIIRS sobre la base de D25.

- S158 (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`): el código operacional de MIROVA para VIIRS 750 estima el fondo del VRP interpolando bajo un halo
  dilatado de los alertados, sin recortar ΔL a cero, y publica la suma de todos los alertados. El brazo de D25 (media de
  los vecinos no alertados) no es ese fondo. Y fuera de la cumbre MIROVA exige un dNTI del doble que nosotros (0,02).

**Abierto**: D25 (fondo = mediana del anillo, no media de vecinos; pre-registro sobre K en PR #871, borrador,
espera sello); D17 como hipótesis competidora de la curva angular (tarea 1.36, rama `loop/activo`: sólo si después
de D25 queda dependencia con el cenit); D32; D33 (encendido); D24.

**No reabrir / no citar como cierre**
- «El ángulo es D17» o «el grueso del déficit es geométrico»: retirado por 1.14 §3.2. Es el error que motivó este
  archivo.
- A99 («0,995 a igual conteo»): rebajada S146; compensa dos factores opuestos y entre volcanes. No apaga la
  búsqueda en k, área, banda ni Planck.
- El «NO ADOPTAR» de D22/D25 de H_S143 se midió con el Test 1 encendido, `min` y sólo V375 (AUDIT_S155 F4-05): no
  vale para K.
- La suma de píxeles del TIF de MIROVA no es VRP (A24, D6).
- El tope de 5 MW (D9, A23) recorta por arriba y no está medido que lo recortado sea artefacto. AUDIT_S150 lo listó
  en MODIS en erupción, pero en las 105 pasadas pareadas de Chillán no recortó ninguna
  (`experiments/_s155_audit/frente_5/INFORME.md`).

## 2. Sobre-publicación (publicamos donde MIROVA miró y no vio nada)

**Medido**
- La brecha de paridad es de sobre-publicación, no de recall (A98; `docs/audit_s139/`).
- K bajó la publicación de VIIRS 375 en negativos limpios de 88,2 y 85,4 % (C0) a 2,5 y 3,7 % (V1 y V2,
  `experiments/_s153_fk_v2/r3/controles_salida.txt`, sección 9). Fuera de Láscar, MODIS publica 7 de 825 (V1) y
  18 de 2.173 (V2), contra 107 y 242 con C0 (marca S157 de D11).
- Con el Test 1 integrado encendido la métrica saturaba en 80 a 92 % en cualquier estrato (A114;
  `experiments/_s147_residual/estructura_del_residual.py`).
- El auto-audit mezclaba C0 y K (AUDIT_S155 F3-02); desde #862 informa por detector; el issue #864 sigue abierto.
- Regla SN (D-9): las alertas V375 de 0,05 MW o menos cuentan como «MIROVA no vio nada»
  (`scripts/clase_mirova.py::aplicar_regla_minimas`; `docs/MISSION.md`, criterio de victoria).

**Abierto**: D26 bajo `max` (sin medir); D25 en M-band como riesgo de sobre-publicación; D9/A23 en su cara de
co-validación del path D sobre fondo frío; la sombra de K (tarea 1.28, rama `loop/activo`; vigilancia diaria #863).

**No reabrir**: los «95 % de FP son físicos» de A54 se midieron en S86, bajo otro detector (inferencia; A54 no
tiene marca, y AUDIT_S155 F4 lista los cierres medidos bajo C0). Sirven como marco de clasificación (artefacto
contra cat-b real, A72), no como número vigente. Un gate post-hoc sin clasificar lo que filtra repite A55.

## 3. Posición corrida del cúmulo o del hotspot

**Medido**
- Píxel MODIS del cráter corrido hacia el sensor, creciendo con el ángulo (Láscar, hasta 3,5 km a 45°): marca S151
  de D18; tareas 1.15, 1.17, 1.21 y 1.23 (rama `loop/activo`; `experiments/_s151_mxd03_etiquetas/`,
  `experiments/_s151_mxd03_cumulo_121/`, `experiments/_s151_mxd03_sola_123/`). En Láscar bajo 35° MxD03 acerca el
  píxel a donde VIIRS ve el calor. **Bajo C0** pierde 2 protegidas, las dos por el Test 1, que K apagó; el paso
  siguiente es el pre-registro de MxD03 sobre K (tarea 1.30 y decisión D-19, rama `loop/activo`; sello de Nicolás).
- Gradiente topográfico nocturno en paths de MIR absoluto (A69, D11; `docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md`),
  **medido bajo C0**. Con K el Test 1 integrado no corre (0 de 3.661 records con `triggered_test1`, marca S157 de
  D11); que el mecanismo siga por otra puerta (compuerta D22, etiqueta MODIS desde `final_hotspot`) es SOSPECHA.
- `Distancia_km` de MIROVA está cuantizada a su grilla y no trae acimut (D15, A93, A107): un radio no es una
  posición. La grilla UTM de los TIF V375 duró sólo ocho adquisiciones (A106).
- Schema asimétrico hotspot contra cúmulo, en las dos direcciones (A46, A81; `docs/S113_A46_COHERENCE_GUARD.md`).
- Marcador primario de `ctx_cluster` = cúmulo publicado (#853, decisión D-24).

**Abierto**: geolocalización MODIS (`_interp_geo` contra MxD03, D-19); D11 (qué hacer con ella con K es decisión
de Nicolás, marca S157); caso PCC V750 del 2026-10-10 (issue #865).

**No reabrir**: PCC lejos del cráter es el lacolito real (A20, A68); el offset de Lastarria es Lazufre (A69); el
A/B vent contra `nti_peak` ya se corrió en S106 y se descartó (A84). Auditar el offset con mediana y rumbo, no con
distancia media (A61, A70).

## 4. Pérdida de recall o alerta protegida sin publicar

**Criterio vigente**: `docs/MISSION.md`, «Criterio de victoria de la réplica»: ninguna alerta protegida (1 MW o
más, lectura A, D-4) se puede perder; bajo 1 MW una pérdida y una publicación de más pesan igual. La unidad del
operador es la **noche** (A94).

**Medido**
- 874 de 877 noches con alerta detectadas (A98, medido S139, antes de K).
- K, lectura A: CUMPLE en V1 y V2 (`experiments/_s153_fk_v2/combinado.log`). Por pasada, en VIIRS 375 publica 19
  de 21 protegidas A en V1 y 38 de 38 en V2; pierde alertas Muy Bajo (V375 16 de 194 y 26 de 388; V750 14 de 30 y
  26 de 75), que pesan igual que las publicaciones de más (`r3/controles_salida.txt`, secciones P2 y 9).
- MODIS con K: recall de alertas de 7 a 60 de 65 y 39 de 39 protegidas de Láscar en V2 (marca S157 de D12).
- Issue #864 (auto-audit del 2026-10-19): recall VIIRS 750 de 73,3 % con K (n = 30) y 5 protegidas sin publicar por
  pasada (Tupungatito, con referencia sospechosa sólo OCR de Suomi NPP; PCC; Chillán), todas con la noche cubierta.
- Protegidas MODIS de Chillán sin detección (2026-10-12 07:20 y 10-15 01:05, cenit ~58°): por noche no se pierden,
  VIIRS 375 publicó esas noches (AUDIT_S155 F3-04 y F5-05).
- D25 en noches: el cráter en 0,0 MW de VIIRS 750 no pierde noches de volcán (0 de 33, sección D25).
- Estratos fuera de las etiquetas del evaluador pueden esconder el costo (A118 punto 2).

**Abierto**: issue #865 (PCC V750, K pierde lo que la sombra publica); reversión pre-autorizada de K si se pierde
una protegida A que MIROVA y la sombra publican y producción calla, confirmada en la cabecera de la imagen (tarea
1.28, rama `loop/activo`); la reversión ya no es un `git revert` limpio (choca en 3 archivos y no toca los datos
reescritos, marca S157 de `docs/MISSION.md`); D12 (leer su marca S157); D27 diurno (rama cableada y apagada, A/B
sobre K en tarea 1.32, rama `loop/activo`); D13 (la cerca `far` del frontend apaga 70,7 % de la magnitud, no 31 %).

**No reabrir / leer antes**: A82 está rebajada (su 90 % no tiene tasa base); A83, A84 y A85 la heredan. Foco
sub-píxel: SWIR de alta resolución, no VRP (A77); fase explosiva invisible al MIR (A78). Reflejo solar diurno en la
referencia: perderlo es correcto (A76). Nombres de volcán en el CSV (A14) y calidad de la referencia (§8) antes de
contar un FN.

## 5. El A/B no cambia nada (o cambia menos de lo esperado)

**Medido**
- El flag no llegaba a todos sus consumidores: la caja D18 sólo llegaba al primer pase y el segundo recapturaba
  (A118; `docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md`; arreglado S149, guard
  `tests/test_guard_caja_llega_al_segundo_pase_s149.py`). Con el cableado arreglado la caja se volvió a medir en
  S151: KC NO CUMPLE (veto) en D1 por una protegida MODIS de Láscar a 3,2 km, válido con la geolocalización MODIS de
  hoy; sobre K su neto es cero en 8 volcanes (marcas S151 de D18). El «D18 nunca se ha medido» de A118 quedó viejo.
- Saturación por otra palanca encendida (A114): el A/B de la caja de S130 corrió con el Test 1 integrado.
- Sin sustrato: la palanca nunca llega a ejecutarse (`docs/s130/AB_FONDOS_SIN_SUSTRATO.md`).
- La clave se leía de otra sección del YAML (A89, `enable_utm_regrid`): leer el flag desde `pipeline.profile`.

**Antes de concluir «inerte»**: medir cuántos casos mueve y el nulo del instrumento (A116, A110); trazar por etapa
(A75); paridad de cobertura entre brazos (A108, `experiments/_s143_evaluador/bajar_tramos.py --estricto`); no
cruzar fronteras de régimen (A104: #535; frontera de K; A85, marca S153: records MODIS de enero a junio de 2026
escritos con los gates intra-radio encendidos); despachar cada ventana desde un tag para no mezclar dos pipelines
(decisión D-15, rama `loop/activo`).

## 6. Run verde sin datos, o el aviso no llega

**Medido (S157)**
- Cortacircuito de búsqueda en CMR (S116, comentario en `pipeline/fetch.py:475-482`; distinto del de descarga en
  LANCE de A64): con `SEARCH_CMR_TIMEOUT` (l. 520) marca CMR caído y salta productos con `SEARCH_SKIP` (l. 482) sin
  fallar el job. En el histórico de Chillán faltaban 326 pasadas de la operacional
  (`experiments/_s157_chillan_rearmado/cobertura.md`, rama `s157-chillan-rearmado`), casi todas en trozos verdes del
  run original (bitácora del 2026-10-20 08:15 UTC en `tasks/LOOP_OBJETIVOS.md`, rama `loop/activo`).
- La segunda pasada de Chillán (run 39391332259) salió 31 de 31 verde con 0 records nuevos: CMR devolvía HTTP 500.
- El NRT salió `success` de 09:10 a 12:10 UTC sin commits de datos; el healthcheck mira 48 h
  (`.github/workflows/nrt-healthcheck.yml`). No se pierde nada porque `default_date_window`
  (`scripts/run_pipeline.py:384`) reprocesa 7 días; cuesta latencia (bitácora del 2026-10-20 12:30 UTC, misma rama).
- El merge de `reproc-chunked.yml` borraba lo que main tenía fuera de las ventanas; arreglado en #873.
- Antes: token de Earthdata vencido que apagó el NRT 5 días sin que el aviso llegara a una persona (`docs/AUDIT_S150.md`;
  nota del token en `CLAUDE.md`, Constraints técnicos); credenciales que bloquean la cuenta (A71); host caído que cuelga el job (A64).

**Abierto**: vigilar cuántos `SEARCH_SKIP` hay por corrida (SOSPECHA de días sin procesar en el NRT); plan de
relleno sin despachar (`experiments/_s157_relleno/`).

**Regla**: contar las pasadas de cada brazo o trozo contra un control ANTES de leer un veredicto (A108); mirar
duración y salida del job, no sólo su color (lección S141: un `tee` sin `pipefail` devolvió 0 con el script
caído); markers con `flush=True` para ver dónde se cuelga (A65); el watchdog juzga cada job desde #867. Un guard
puede pasar por subcadena (A92), y un laboratorio puede quedar más ciego que producción sin que nadie lo note (A117).

## 7. Un número que no se reproduce o cambió entre sesiones

- Corpus vivo que crece, también hacia atrás por backfill: registrar proporción y ventana (A90).
- Cambio de régimen: #535 (A104); frontera de K en la fecha de observación 2026-09-18, no en el merge
  (AUDIT_S155, #860).
- Citas `archivo:línea` que derivan: remapear por contenido (A101).
- Suite corrida mientras se editaba (A112); empates desempatados según la CPU (decisión D-16 y tarea 1.22,
  rama `loop/activo`); reprocesos paralelos sobre el mismo JSON lo corrompen (A47).
- El ejemplo de A87 no se reproduce hoy: la lección vale, el número no.

## 8. La referencia de MIROVA da algo raro

- No sirve igual todo el año (A119 con su marca S151; `scripts/calidad_referencia_mirova.py`;
  `docs/audit_s139/MAPA_BASES_MIROVA_V1.md` §2). El OSF no es el NRT (A105).
- Alertas «sólo OCR» de Suomi NPP antes del 2026-10-09 pueden traer la distancia de otra pasada (issue #864;
  arreglo en Mirova-v1#20). La línea de MIROVA del tablero no leía el OCR (AUDIT_S150, familia 4).
- Artefactos solares diurnos publicados por MIROVA (A76). TIF de MIROVA: no sumables (A24), CRS y hora a verificar
  (A106), y a veces la misma imagen servida bajo una hora nueva (A106).

## 9. Un cierre que no se sostiene

Un cierre que no cita script, run, PR, paper ni `archivo:línea` es una creencia (A111;
`experiments/_s145_censo_cierres/censo.py`). Hereda las premisas de la lectura con que se derivó (A95) y la rebaja
se propaga a los hijos en el mismo PR (A113). Leer el PDF renderizado, no la capa de texto (A95). Si un criterio
necesita un umbral, preguntarle primero a la referencia de MIROVA (A115).
