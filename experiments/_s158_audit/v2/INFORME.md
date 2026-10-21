# Verificador V2 (contexto limpio), auditoría S158: F2-H1, F2-H2, F5-01, F5-02

Rama `s158-d17-diseno`, 2026-10-21. No leí los informes de F2 ni F5; re-corrí un script de F5 (m1, copia sin
cambios en `v2_m1_rerun.py`) y leí los datos de la rama del run por `git show`. Todo lo demás es lectura propia de
la fuente y scripts propios en esta carpeta. Rutas relativas a `D:\vrp-trabajo\temporales\s158_d17\`.
Código de MIROVA: `experiments\_s158_d17_diseno\osf_codigo_mirova\` (H = `MIROVA_VIIRS750_hotspot_detection.m`,
V = `MIROVA_VIIRS750_VRP.m`).

## Tabla

| hallazgo | veredicto | mi gravedad | por qué, en una línea |
|---|---|---|---|
| F5-01 cobertura del A/B de D25 | **CONFIRMADO, con matiz en el mecanismo** | **4** | faltan 152 de 4.762 pasadas y el 18-oct entero; entre ellas **9 alertas protegidas de Chillán**, el caso del A/B. Sí hay un control absoluto, pero su 5 % por volcán y sensor sobre 51 días traga un día entero |
| F5-02 placebo D = 1,10·K | **CONFIRMADO, con matiz** | **3** | reproducido idéntico. M es «más cerca de MIROVA» y K está bajo: cualquier ganancia hacia arriba da MEJORA y una hacia abajo da EMPEORA. Con la calibración sellada (simétrica, opción A) el placebo llega a MEJORA en V1; V2 sin medir |
| F2-H2 segundo pase | **CONFIRMADO, con matiz** | **3** | el código corre el pase 2 sobre toda la escena con la misma función, y en una escena sintética alerta un píxel aislado a 17 columnas que la condición (b) perdería. Pero la condición (a) en el código no hace nada (pase 1 vacío da pase 2 vacío), e «igualar» tiene que ser igualar al código: nuestro primer pase de V750 tiene una compuerta de temperatura que MIROVA no tiene |
| F2-H1 n_hotspots | **CONFIRMADO, con matiz** | **2** (3 si se cuenta como raíz documental de D32) | MIROVA cuenta píxeles: guía del tablero, Npix del OSF plano en fondo por píxel, código V:61. Además el «factor 42» ya no existe: hoy contamos **menos** píxeles que MIROVA (0,67). La consecuencia de magnitud ya está en D32 |
| V2-1 (propio) | nuevo | **3** | el pipeline imprime «Cobertura: completa» con cero gránulos en un día que producción tiene entero: ausencia silenciosa, es la causa directa de F5-01 |
| V2-2 (propio) | nuevo | **3** | 53 records V750 bajo K (49 summit) tienen primer pase vacío y segundo pase que marca; en MIROVA eso es imposible. Condicionar (a) los borraría, pero algunos pueden ser los que MIROVA detecta en su primer pase sin compuerta de temperatura |

Orden por gravedad abajo.

---

## F5-01: al A/B de D25 le faltan el 18 de octubre entero y 9 protegidas de Chillán

- **ARCHIVO:LÍNEA**: `experiments\_s157_prereg_d25\evaluar_d25.py:504-525` (los tres controles de cobertura);
  `experiments\_s149_prereg_invierno\armar_tabla.py:37-49` (las claves de la tabla salen sólo de los records de los
  brazos). Datos: commit `4b6d7f5f2` de `origin/s146-ab/39530508296` (intento 1 del run 39530508296; el run quedó
  `completed/failure`, con `recolectar` en failure y el job Villarrica tramo 4 sin conclusión, `gh run view`).
- **SCRIPT:SALIDA**: `v2\f501_cobertura.py` → `v2\f501_cobertura_salida.txt`.
- **QUÉ PASA**. Fenómeno: los gránulos del 18-oct no estaban en ninguna colección de la NASA cuando corrió el
  reproceso (el 21-oct a las 05:10 UTC): el Standard todavía no los traía y el NRT ya no. El brazo quedó sin esas
  pasadas en los tres brazos por igual. Código: los tres controles del evaluador no lo ven.
  1. Control 1 (brazos contra K): 0 faltan, 0 sobran. Ciego por construcción: los tres brazos bajan los mismos gránulos.
  2. Control 2 (protegidas sin record en algún brazo): las claves salen de la unión de las tablas, y la tabla se arma
     sólo con records de los brazos (`armar_tabla.py:37-49`). Una protegida sin record en ningún brazo no existe para él.
  3. Control 3 (referencia de cobertura `claves_cobertura`, umbral 5 % por volcán y sensor): **existe** y compara
     contra una referencia externa (histórico con K y producción). El auditor dijo que la cobertura sólo se compara entre
     brazos; eso es incompleto. No salta porque la peor fracción es **0,038** y el umbral es 0,05 sobre la ventana
     entera de 51 días: un día entero pesa 2 a 3 %.
  Números (denominador: pasadas VIIRS 375 y 750, volcán|bucket|minuto, 11 Tier A, V1 2026-08-29 a 2026-10-18):
  referencia 4.762, K 4.610; faltan **152 (3,19 %)**: 44 del 12-oct, 22 del 13-oct, **86 del 18-oct (86 de 86)**.
  Con la función de protección del propio evaluador y la referencia congelada de V1: **9 faltantes son protegidas A
  (1 MW o más), las 9 de Nevados de Chillán** (12-oct 05:18 en los dos sensores; 18-oct 05:06, 06:00 y 06:48 en VIIRS
  375; 05:06, 05:42, 06:00 y 06:48 en VIIRS 750) y 18 tienen alguna fila ALERTA (Chillán, Isluga, Tupungatito, PCC).
  La pasada del 18-oct 06:48 es la que el resumen del sello usa de ejemplo del probe del L1B.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Torcería el veredicto del A/B: el veto P1 y la M de Chillán se calculan
  sin 9 de sus alertas protegidas, justo en el volcán que motivó la prueba.
- **CÓMO REPRODUCIRLO**: `MSYS_NO_PATHCONV=1 python -B experiments/_s158_audit/v2/f501_cobertura.py`.
- **Controles**. Positivo: quitándole al brazo K una semana (01 a 07-oct) el control 3 da 22 disparos; quitándole un
  día más (17-oct) da 8. O sea el control funciona y su umbral tolera exactamente un día. Pareo: 375 de 4.610 pasadas
  de K tienen ALERTA, así que el pareo no está muerto.
- **CONFIANZA**: CONFIRMADO (conteos y lectura). El porqué de la NASA es SOSPECHA (ver V2-1).
- **GRAVEDAD**: 4. Un A/B que decide sobre Chillán sin sus alertas de 1 MW o más del 18-oct puede dar CUMPLE sin
  haber mirado el caso.

## V2-1 (propio): «Cobertura: completa» con cero gránulos

- **ARCHIVO:LÍNEA**: `scripts\run_pipeline.py:417` (el mensaje); `pipeline\fetch.py:622-643` (`_buscar_ventana`: un
  día sin gránulos en Standard ni NRT queda como lista vacía, `resultado[d] = []`, sin registrar falla) y `:686-723`.
  Log: `git show 4b6d7f5f2:experiments/_s146_ab_sin_test1/salidas/39530508296/logs/_s157_ab_d25_k_control_NevadosDeChillan.log`.
- **QUÉ PASA**. Para el 18-oct el log muestra `SEARCH_VENTANA ... VNP02IMG v2 2026-10-16..2026-10-18 n=4` y después
  `VNP02IMG_NRT v2 2026-10-18..2026-10-18 n=0`, igual en los seis productos VIIRS; luego `SEARCH_DONE VIIRS_* n_l1b=0` en
  los seis sensores y **«Cobertura: completa (ninguna búsqueda ni descarga fallida).»** Lo mismo el 12-oct (SNPP y NOAA-21
  con `n_l1b=0`, NRT `2026-10-12..2026-10-13 n=0`). Producción tiene esas pasadas (el 12-oct 05:54 SNPP con
  `product_version: standard`). El informe de cobertura sólo cuenta fallas; «la búsqueda contestó cero» no es falla.
- **CÓMO SE VE EN EL DASHBOARD**: en el NRT de producción, SOSPECHA de que no se vea casi nunca (el NRT del día sí
  existe). En reprocesos de días recientes (entre que el NRT caduca y el Standard aparece), un hueco que nadie anuncia.
- **CONFIANZA**: CONFIRMADO el mensaje y los `n=0`; SOSPECHA la causa (caducidad del NRT y latencia del Standard).
- **GRAVEDAD**: 3. Es la causa directa de F5-01 y puede repetirse en V2a/V2b o en cualquier reproceso de fechas recientes.

## F5-02: la métrica M da MEJORA a un placebo de ganancia

- **ARCHIVO:LÍNEA**: `experiments\_s157_prereg_d25\evaluar_d25.py:152-161` (`regla_m`, `d_par`), `:187-200`
  (`calibrar_simetrico`), `:396-414` (calibración y regla de dos volcanes), `:432-462` (`global_ventana`);
  `ADENDA_CALIBRACION.md:3-9` (sellada D-27: simétrica más opción A); `PREREGISTRO.md` §8 d (CUMPLE exige M MEJORA en
  algún estrato que decide en cada ventana y EMPEORA en ninguno).
- **SCRIPT:SALIDA**: `v2\v2_m1_rerun.py` (copia sin cambios de `f5\m1_pares_y_predicados.py` más un bloque mío al
  final) → `v2\v2_m1_rerun_salida.txt`. Las secciones (a) y (a2) salen **idénticas** a `f5\m1_salida.txt` (`diff` vacío).
- **QUÉ PASA**. Fenómeno: nuestra magnitud está sistemáticamente bajo la de MIROVA (razón mediana K/MIROVA 0,35 a 0,68
  en los estratos que deciden). Código: con D = c·K, `d = |log(cK/M)| − |log(K/M)|` vale exactamente `−log10(c)` en todo
  par con cK ≤ M. Medido: la fracción de pares con K/M ≤ 1/1,10 es 0,714 (V750 z≤40), 0,947 (V750 z>40), **0,983**
  (V375 sin kernel z≤40), 0,898 (V375 sin kernel z>40). La mediana de d queda clavada en −0,041 con intervalo degenerado,
  y la regla da MEJORA en todos los estratos que deciden. El placebo hacia abajo (c = 0,90) da EMPEORA en los cuatro
  [0,046; 0,046]. Con la calibración sellada (simétrica, opción A), c = 1,10 da: V750 z≤40 **MEJORA** (3 volcanes con
  d < 0), V750 z>40 NEUTRO (1 volcán), V375 sin kernel z≤40 **MEJORA** (4 volcanes), V375 z>40 NEUTRO (sólo bloquea).
  O sea, en V1 un placebo llega al estado de ventana MEJORA si P1 y P2 no se mueven (una ganancia hacia arriba no apaga
  publicaciones ni cruza 1 MW hacia abajo).
- **Matiz (caminos por los que el hallazgo podría estar mal)**.
  1. M responde lo que el pre-registro le pregunta («si D queda más cerca de ese valor que K», §5), y el placebo **sí**
     queda más cerca. No es un error de cálculo: es que M no puede atribuir la mejora al fondo. Con K tan bajo, el estrato
     V375 sin kernel z≤40 da MEJORA a **cualquier** aumento mayor que cero, así que en ese estrato M tiene poder para
     rechazar a D25 sólo si se pasa de largo.
  2. La calibración vieja (`--calibracion sellada` del código, que no rige) deja V750 en INDECIDIBLE y frenaría al
     placebo; rige la simétrica (adenda D-27), que no lo frena.
  3. El CUMPLE pide además V2. No pude medir el placebo en V2: los records de producción anteriores al 2026-09-18 no son
     K. SOSPECHA de que pase igual, porque el déficit de magnitud es anterior a K (A99).
  4. CUMPLE abre el ciclo de adopción con R2 por píxel, verificador y el «sí» de Nicolás (§8 d): hay frenos humanos
     después. Por eso gravedad 3 y no 4.
  Contexto que sube la importancia: el oráculo (`experiments\_s158_oraculo_mirova\README.md`) y V:63-81 muestran que el
  fondo de MIROVA en VIIRS 750 no es la media de los vecinos no alertados sino una exclusión dilatada (3, 5 o 7 según
  npix) e interpolación lineal (`fillmissing2`). Un MEJORA de D25 no diría que D25 es lo que hace MIROVA.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hasta una adopción; después, magnitudes que suben por la razón equivocada.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/v2/v2_m1_rerun.py` (25 s).
- **CONFIANZA**: CONFIRMADO en V1; SOSPECHA en V2.
- **GRAVEDAD**: 3.

## F2-H2: el segundo pase en el código de MIROVA

- **ARCHIVO:LÍNEA**: H:208-235 (dos llamadas a la misma `contextualDetectionPass`, la segunda con
  `contextualAlertsPass1` como excluidos), H:272-277 (los ya alertados quedan en NaN y no pueden volver a alertar),
  H:389-399 (los tres dominios se prueban sobre toda la ventana de 67 × 67, sin restricción de vecindad).
  Paper renderizado: `sp426.5.pdf`, página 7 del PDF (índice 6), columna derecha, «Second run»: *«The last step is
  applied only if one or more pixels have been detected by the previous tests, and focuses on refining the hotspot
  detection for the pixels adjacent to those already flagged»* (`v2\render\sp426_p7_low.png`); página 8 (índice 7):
  *«step 2 (spatial analysis) is performed a second time ... the previous step (contextual threshold: tests 2 and 3)
  are applied again to the new dNTI and dETI matrices»* (`v2\render\sp426_p8.png`).
  Nuestro: `pipeline\detection_context.py:822-967` (`second_pass_adjacent`), `:413-560` (`first_pass_tests_2_and_3`);
  `pipeline\process_viirs_mod.py:869-965`; perfil leído desde `pipeline.profile` (`v2\h2_flags.txt`):
  `ENABLE_SECOND_PASS_ADJACENT True`, `ENABLE_SECOND_PASS_CONDITIONED False`, `NTI_BT_SANITY_K 3.0`,
  `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 False`.
- **SCRIPT:SALIDA**: `v2\h2_oraculo_segundo_pase.py` → `v2\h2_oraculo_salida.txt`.
- **QUÉ PASA**.
  1. **El código no restringe a los adyacentes** (condición b). En una escena sintética ruidosa con un foco de 3 × 3 en el
     centro y un píxel débil aislado en (33, 50), el oráculo alerta ese píxel **sólo en el pase 2**: al sacar el foco, el
     umbral de dNTI de BOX0 baja de 0,0310 a 0,0270. Ese píxel está a 17 columnas: la vecindad-8 lo perdería. En la
     búsqueda, 37 de 351 escenas tienen alertas del pase 2 no adyacentes a lo ya alertado. Control: en Etna el único píxel
     del pase 2 es adyacente (no prueba nada por sí solo, Etna es un foco compacto).
  2. **La condición (a) en el código no hace nada.** Si el pase 1 contextual sale vacío, el pase 2 recibe las mismas
     entradas y devuelve lo mismo: vacío. Medido: escena isoterma con ruido, pase 1 `[0,0,0]`, pase 2 `[0,0,0]`; con un
     foco inyectado, pase 1 `[0,0,1]` (el oráculo no está muerto). O sea condicionar (a) **coincide en efecto** con el
     código; lo que se aparta del código es (b).
  3. **El paper sí dice las dos condiciones** (renderizado arriba). La afirmación del proyecto de que el pase condicionado
     es «lo que manda Coppola 2016a» es una lectura literal correcta del paper; lo que muestra el código es que la (b)
     no es operacional. Para VIIRS 750 manda el código (decisión de Nicolás del 2026-10-21); para VIIRS 375 y MODIS no hay
     código publicado.
  4. **«Igualar los dos pases» tiene que ser igualarlos al código, no el segundo al primero.** Nuestros dos pases difieren
     en tres cosas (lectura de `detection_context.py`): el primero exige `bt > t_bg + 3 K` (`:546-553`) y el segundo no;
     el primero saca del fondo los dNTI y dETI menores que −0,1 (`:492-499`, `build_unsuitable_mask`) y el segundo usa
     todo lo no activo (`:923`); y el segundo reusa la ETI del primero sin rehacer la regresión sin los activos (MIROVA la
     rehace, H:328-345). MIROVA no tiene compuerta de temperatura en ningún pase y aplica el −0,1 sólo al contraste de
     NTI (H:298), no al de ETI. Igualar el segundo a nuestro primero agregaría al segundo una compuerta que MIROVA no tiene.
- **CÓMO SE VE EN EL DASHBOARD**: ver V2-2.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/v2/h2_oraculo_segundo_pase.py`.
- **CONFIANZA**: CONFIRMADO (lectura del código, del paper renderizado y oráculo).
- **GRAVEDAD**: 3. Toca la decisión D1/D2 pendiente: el brazo «condicionado» del pre-registro S135 implementa (a) y (b)
  juntos; (b) aleja de MIROVA en VIIRS 750.

## V2-2 (propio): nuestro segundo pase marca con el primero vacío, cosa que MIROVA no puede

- **ARCHIVO:LÍNEA**: `pipeline\detection_context.py:906-967`; `pipeline\process_viirs_mod.py:932-965`.
- **SCRIPT:SALIDA**: `v2\h2_segundo_pase_vacio.py` → `v2\h2_segundo_pase_vacio_salida.txt`.
- **QUÉ PASA**. Records con `diag_n_first_pass_pixels == 0` y `diag_n_second_pass_recapture > 0` (denominador: todos los
  records de los 11 Tier A en `data\mirova_equivalent\`; ventana K desde la observación del 2026-09-18): **VIIRS 750 53 de
  1.553 (49 summit)**, VIIRS 375 61 de 1.566 (59 summit), MODIS 5 de 777. De los 53 de V750, 20 quedan summit con
  `pc.vrp_mw > 0` (proxy del tablero, no el predicado con node: SOSPECHA para «publica»). En MIROVA esto no puede pasar
  (F2-H2 punto 2). Pero no se sigue que haya que borrarlos: nuestro primer pase tiene la compuerta de temperatura que
  MIROVA no tiene, así que una parte puede ser exactamente lo que MIROVA detecta en su primer pase (SOSPECHA, sin medir
  por píxel). Condicionar (a) sin quitar esa compuerta los borraría; igualar al código podría conservarlos.
- **Control positivo**: con primer pase > 0 el segundo pase agrega píxeles en 23 records V750 (109 V375): el campo no está muerto.
- **CÓMO SE VE EN EL DASHBOARD**: hasta unas 20 pasadas V750 en un mes de K cuyo cúmulo entero viene del segundo pase.
- **CONFIANZA**: CONFIRMADO el conteo; SOSPECHA la atribución a la compuerta de temperatura.
- **GRAVEDAD**: 3. Es el sustrato que decide qué brazo de D1/D2 pierde o conserva alertas.

## F2-H1: MIROVA cuenta píxeles, no regiones

- **ARCHIVO:LÍNEA**: `CLAUDE.md:1676-1682` (glosario, leído); `docs\MIROVA_DIVERGENCES.md:37-41` (D1, leído);
  `docs\MISSION.md:345-347` (licencia para divergir «alineación con n_hotspots MIROVA via scipy.ndimage.label 8-conn,
  explícitamente Coppola 2016a "neighbor pixels"», leído); `tests\test_cluster_hotspots.py:1-8`;
  `experiments\50_FACTOR_42_HALLAZGO.md:1-50`. Código: V:61 `npix = numel(alert)`, V:83-85 suma sobre todos los alertados;
  H:241-248 (concatenación sin agrupar; los conjuntos son disjuntos por H:275-277). Paper renderizado, `sp426.5.pdf`
  página 9 (índice 8), ec. 8: *«where "n alert" is the number of alerted pixels»* (`v2\render\sp426_p9_suma.png`).
  Guía del tablero de MIROVA v2.5 (`documentacion\MIROVA_Dashboard_UserGuide_V_2_5.md`, tabla de campos): Npix
  *«Number of alerted pixels used in the detection»*.
- **SCRIPT:SALIDA**: `v2\h1_npix_osf.py` → `h1_npix_osf_salida.txt`; `v2\h1_pareo_npix.py` → `h1_pareo_npix_salida.txt`.
- **QUÉ PASA**. Si Npix contara regiones, el fondo MIR por unidad de Npix crecería con Npix. Medido sobre las 615.470
  filas del OSF v2.5 (2000 a 2025): en 375 m, `Tot_Lmir_bk / Npix` mediano vale 0,173 con Npix = 1 y 0,170 a 0,187 hasta
  Npix = 100; en 750 m, 0,46 a 0,33 (baja, no sube). Plano: cuenta píxeles. El coeficiente VRP/ΔL es constante por
  resolución (2,53e6 / 1,108e7 / 1,89e7): suma por píxel. Pareo por pasada (|dt| ≤ 10 min, mediana 0 min) contra
  nuestros records de hoy, 2025, 8 Tier A: **2.020 pares VIIRS 375, Npix MIROVA mediana 3, nuestro
  `n_anomalous_pixels` mediana 2, razón 0,67**; 25 pares V750, razón 0,50. El caso que originó el «factor 42» (Láscar
  2025-11-15): el OSF da **Npix = 4** a las 05:48 SNPP, y nuestro record de hoy da **3** píxeles (no 77).
  Caminos por los que podría estar mal, revisados: (a) que el glosario hable de otro conteo: no, dice «n_hotspots
  (regiones espacialmente contiguas)» y el único conteo que publica MIROVA es Npix; (b) que 50_FACTOR_42 lo haya probado:
  no probó el caso original (midió Lastarria y Chaitén con un radio de agrupamiento propio y no comparó con ningún
  número de MIROVA); (c) que el código de V750 no valga para el producto de 375 m: el OSF de 375 m da el mismo patrón plano.
- **Matiz**. El «factor 42» era sobre-detección real del pipeline de entonces y hoy no existe; la brecha actual va al
  revés (contamos menos píxeles que MIROVA, coherente con el déficit de selección de A99 y A103). El tablero no usa
  `n_hotspots_clustered` (0 apariciones en `frontend\index.html`). La consecuencia de magnitud (publicamos un cúmulo,
  MIROVA suma todo lo alertado) ya está registrada en D32 (`docs\MIROVA_DIVERGENCES.md:3150`). No sumo gravedad nueva
  sobre D32; la pongo en 2, o 3 si se quiere contar que esta premisa es la licencia de MISSION que sostuvo esa divergencia.
- **CÓMO SE VE EN EL DASHBOARD**: invisible como conteo; como magnitud, es D32.
- **CONFIANZA**: CONFIRMADO. La cita de MISSION a «neighbor pixels» de Coppola 2016a: en `sp426_5.txt` las apariciones
  de «neighbo» y «adjacent» son el núcleo de 8 vecinos y el segundo pase, ninguna es una regla de conectividad para
  contar regiones (búsqueda de texto: SOSPECHA de cita sin respaldo, no renderé esas páginas).
- **GRAVEDAD**: 2.

---

## VERIFICADO LIMPIO

- El oráculo de MIROVA corre y reproduce Etna: pase 1 `[0,0,4]`, pase 2 `[0,0,1]`, 5 píxeles
  (`python -B experiments/_s158_audit/v2/h2_oraculo_segundo_pase.py`).
- Los alertados del código de MIROVA son disjuntos aunque no use `unique`: H:275-277 y H:328-330 ponen en NaN los
  previos, y el contraste en NaN no pasa ningún umbral (lectura).
- Control 1 de cobertura del evaluador: G y D tienen exactamente las 4.610 pasadas VIIRS de K, 0 de diferencia
  (`f501_cobertura.py`).
- Control 3 de cobertura del evaluador funciona: salta con dos días faltantes (8 disparos) y con una semana (22)
  (`f501_cobertura.py`).
- El m1 de F5 es reproducible: re-corrido en 25 s, (a) y (a2) idénticos (`diff` vacío; `v2_m1_rerun.py`).
- La adenda de calibración está sellada (simétrica más opción A, D-27, `ADENDA_CALIBRACION.md:3-9`); el código la
  aplica en `evaluar_d25.py:403-414`.
- Los flags del segundo pase se leyeron desde `pipeline.profile`, no del YAML (`h2_flags.txt`).
- El Npix del OSF cuenta píxeles en las tres resoluciones (`h1_npix_osf.py`).

## Lo que no pude verificar

- El placebo de F5-02 en V2 (no hay records K anteriores al 2026-09-18 en producción).
- Si los 53 records V750 de V2-2 los detectaría MIROVA en su primer pase: pide correr el oráculo sobre esos gránulos.
- El predicado del tablero con node en V2-2 (usé summit más `pc.vrp_mw > 0`).
- Por qué el Standard no traía el 12 y 13-oct a las 04:49 UTC del 21-oct, si producción los tiene como `standard`.
- El código de MIROVA para VIIRS 375 y MODIS (no publicado): F2-H1 y F2-H2 valen con certeza sólo para VIIRS 750;
  para 375 m F2-H1 se apoya en el OSF.
- Las páginas del paper que citan «neighbouring pixels» para el núcleo (sólo búsqueda de texto).

Datos de prueba: no copié datos; los JSON del run se leyeron con `git show` en memoria. `f501_faltantes.json` es salida
mía (lista de claves).
