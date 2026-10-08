# Pre-registro S150: la réplica frente a una erupción (Nevados de Chillán, 2026-09-14 a 2026-10-07)

> **VERSIÓN 2, SIN APROBAR.** Reescrita tras el verificador con contexto limpio
> (`docs/audit_s150/VERIFICADOR_PREREGISTRO_NDC.md`, veredicto de la v1: no despachable) y los auditores B y
> C de S150. No se despacha nada hasta que (1) un segundo verificador limpio revise esta versión y (2)
> Nicolás escriba "sí" (el candado `preregistro_aprobado` es suyo). **Fecha más temprana de despacho:
> 2026-10-13** (§3). Escrito y commiteado antes de correr ningún brazo sobre esta ventana.

## 1. Por qué esta prueba, y qué no puede decidir

**El fenómeno.** Desde el 2026-09-28 Nevados de Chillán tiene actividad fuerte: MIROVA publica alertas de 2 a
10 MW en los tres sensores. Todo lo que el proyecto midió de marzo a septiembre fue en volcanes en reposo,
con señales de 0,05 a 0,5 MW y uno o pocos píxeles. Una erupción es otro régimen: muchos píxeles calientes,
un cúmulo extendido, focos secundarios en la escena, y magnitudes que cruzan los topes y modos pensados para
el reposo. Es la primera vez que hay con qué probarlo fuera de Láscar.

**Lo que ya se sabe sin correr nada** (records de producción hasta el 2026-10-02 07:35, referencia congelada;
verificador H1 y H14, auditores B y C):
- VIIRS 375 publica las 11 alertas nocturnas de MIROVA de ese tramo; VIIRS 750, 7 de 8; **MODIS, 1 de 3**. La
  que pierde es la del 2026-10-01 08:35 (MIROVA 5,18 MW): el cúmulo está a 0,9 km del cráter, pero la
  etiqueta `far` sale del píxel más caliente de la escena, a 32,8 km, y el tablero la oculta (A46/A81).
- **Arreglar sólo la etiqueta no sirve**: reetiquetar producción desde el cúmulo (lo único que hace el flag
  `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`) recupera esa alerta y además publica **22 de 28** pasadas MODIS
  de reposo en que MIROVA no vio nada (5 de ellas topadas en 5,00 MW), contra 0 de producción. La etiqueta
  `far` esconde hoy un detector MODIS que, con la banda 21 y el Test 1, se dispara casi todas las noches
  frías. **El brazo "sólo etiqueta" queda descartado por esta medición** y en el run sólo sirve de control de
  cableado.
- **El tope D9 de 5 MW está armado en casi toda la erupción** (21 de 27 pasadas MODIS, 44 de 56 VIIRS 375,
  53 de 55 VIIRS 750, del 09-20 al 10-02) porque con el camino de temperatura de brillo apagado su condición
  se reduce a fondo bajo 270 K, y **ya recortó 11 de 27 magnitudes MODIS**.

**Lo que esta prueba puede decidir.** Es una **prueba de estrés con veto**: un volcán y diez días de
actividad no adoptan nada. Un candidato que en la erupción pierde una alerta de 1 MW o más que hoy
publicamos queda vetado; lo que la pasa sigue a una corrida de los 11 volcanes con su propio pre-registro.
Y responde una pregunta que hoy no tiene respuesta: **qué parte del MODIS de la réplica falla en una
erupción: el detector, el tope o la etiqueta.**

## 2. Brazos (perfiles verificados: `diff_perfiles_ndc_salida.txt`, cada uno difiere sólo en lo declarado)

| brazo | perfil | qué es | para qué |
|---|---|---|---|
| C0 | `_s146_ab_control` | producción tal cual | control |
| T0 | `_s150_sin_tope_d9` | C0 sin el tope D9 | qué hace el tope en una erupción |
| E | `_s150_etiqueta_cumulo` | C0 con la etiqueta MODIS desde el cúmulo | **sólo control de cableado** (§4) |
| B | `_s146_ab_sin_test1` | C0 sin el Test 1 integrado | candidato de A/B anteriores |
| F | `_s147_ab_sin_test1_max` | B con la conectiva `max` | candidato VIIRS |
| J | `_s149_ab_sin_test1_b22` | B con banda 22 primaria | atribución de la banda 22 |
| K | `_s149_ab_sin_test1_b22_max` | J con `max` | atribución de `max` en MODIS |
| KE | `_s150_k_etiqueta` | K con la etiqueta desde el cúmulo | candidato MODIS completo |
| KET | `_s150_k_etiqueta_sin_tope` | KE sin el tope D9 | candidato MODIS completo sin tope |
| G | `_s149_ab_sin_test1_gemelo` | gemelo de B | determinismo |

Despacho: un solo run, `vols=["NevadosDeChillan"]`, `start=2026-09-14`, `end=2026-10-07`, los diez brazos,
`control=_s146_ab_control`, **desde `main` con los perfiles ya mergeados** (el workflow imprime ahora la
etiqueta y el tope de cada brazo). Diez jobs de un volcán y 24 días: del orden de una hora cada uno.

## 3. Ventana, referencia, fecha de despacho y sustrato

- **Ventana**: 2026-09-14 a 2026-10-07. Reposo del 14 al 27 de septiembre; actividad del 28 en adelante. No
  cruza el 2026-08-28 23:00 UTC (#535). Posterior al 2026-06-13: **decide la etiqueta con tabla y OCR** (A119).
- **Referencia congelada** desde Mirova-v1 (commit `83aba69`), no desde el snapshot local, que el 2026-10-08
  tenía su última sincronización el 2026-10-05: `_congelado_ndc/` con sha256 en `MANIFIESTO.json`
  (`congelar_desde_remoto.py`). Los CSV están en git (forzados: `*.csv` está en `.gitignore`).
- **Fecha de despacho, 2026-10-13 o después** (verificador H5): NASA publica el producto estándar 3 a 5 días
  después de la adquisición, y los jobs corren en dos tandas; antes de esa fecha unos brazos podrían ver el
  gránulo de tiempo casi real y otros el estándar en las mismas pasadas fuertes. El evaluador además
  verifica que cada pasada tenga la **misma versión de producto en todos los brazos** (§4.2).
- **Sustrato**: lo cuenta el propio evaluador sobre las pasadas que C0 procesa, de noche, con el etiquetador
  del evaluador (la v1 contaba pasadas diurnas y FALSO_POSITIVO como "sin alerta": verificador H3). Con los
  records de producción hasta el 2026-10-02 da: MODIS 3 alertas en actividad (2 de 1 MW o más), 28 negativos
  limpios en reposo y 5 en actividad; VIIRS 375 11 alertas (8 de 1 MW o más); VIIRS 750 8 (6 de 1 MW o más).
  El verificador contó con el mismo cargador hasta el 2026-10-07: **20 alertas VIIRS 375 nocturnas en
  actividad (13 de 1 MW o más) y 13 VIIRS 750 (11)**. El número que vale es el que imprima el evaluador
  sobre el run.

## 4. Controles, antes de mirar ningún resultado (sección 1 a 4 de `medir_ndc.py`)

1. **Cobertura pareja** entre los diez brazos, y **cada alerta de 1 MW o más con record en todos los brazos**
   (A108). Si falla, se repite el job corto con el mismo código; no se interpreta.
2. **Misma versión de producto por pasada** en las alertas de 1 MW o más. Si no, INDECIDIBLE y se re-despacha.
3. **Determinismo**: G contra B, misma decisión de publicar en 98 de cada 100 pasadas o más, **en cada
   sensor por separado**.
4. **Cableado de la etiqueta**: E tiene que ser **exactamente C0 reetiquetado**, pasada por pasada (misma
   magnitud del cúmulo, mismo tope, etiqueta MODIS igual a la que da el centroide del cúmulo contra el
   inner de 5 km), y publicar la pasada del 2026-10-01 08:35. Si no, el cableado está roto: INDECIDIBLE para
   E, KE y KET, y se traza por etapa (A75).
5. **Identidad del predicado del tablero**: el de node, a través de `armar_tabla.py`.

**El evaluador está probado antes de despachar** (`probar_medir_ndc.py`, sobre producción y la referencia
congelada): con todos los brazos iguales a producción (salvo E reetiquetado) da controles OK, cableado OK y
cero pérdidas; con una pérdida sembrada en la alerta VIIRS 375 del 2026-09-29 05:18 (5,73 MW), P1 la veta y
lista esa pasada; con E sin reetiquetar, el control 4 acusa cableado roto. Seis de seis.

## 5. Predicciones y reglas (sección 5 a 9 de `medir_ndc.py`)

Una pérdida es una alerta de MIROVA de 1 MW o más que el control publica y el brazo no. **Las pérdidas en
pasadas donde el gemelo G también cambia de decisión respecto de B se descuentan** (no son atribuibles al
brazo: verificador H6).

| # | qué | regla | si falla |
|---|---|---|---|
| **P1** (veto VIIRS) | F no pierde ninguna alerta de 1 MW o más en VIIRS 375 ni VIIRS 750, **ni contra B ni contra C0** | cero pérdidas netas | `max` vetado en régimen de erupción hasta entender cada pérdida |
| **P2** (veto VIIRS) | B no pierde ninguna contra C0 | cero | quitar el Test 1 vetado en erupción |
| **P3** (atribución MODIS) | J no pierde ninguna alerta MODIS de 1 MW o más contra B (banda 22), y K ninguna contra J (`max`) | cero en cada par | se atribuye la pérdida al ingrediente que la produce |
| **P4** (candidato MODIS) | KE y KET publican **todas** las alertas MODIS de 1 MW o más | todas | el candidato completo no sirve en erupción |
| **P5** (el tope no decide) | T0 contra C0 y KET contra KE: **ninguna decisión de publicar cambia**; el tope sólo mueve magnitud | cero cambios | el tope D9 decide publicación (afecta `isSummitDetection`, que lee `vrp_mw`) y hay que tratarlo como compuerta, no como cota |
| P6 (informativa) | costo MODIS: publicaciones en negativos limpios de reposo y de actividad por brazo, **separando las topadas en 5 MW** | se informa | el costo en falsos se decide en la corrida de 11 volcanes |
| P7 (informativa) | recall por tramo (bajo y sobre 1 MW) y razón de magnitud contra MIROVA en actividad, por brazo y sensor; T0 y KET muestran la magnitud sin tope | se informa | |
| P8 (informativa) | lo que cada brazo publica el 26 y 27 de septiembre, antes de la primera alerta de MIROVA, con magnitud y distancia del cúmulo | se informa: sólo la cronología de OVDAS o un SWIR de alta resolución dirían si era calor real | |

**Veredicto por brazo** (sólo con los controles de §4 en OK): VETADO si falla su P1, P2 o P4; P3 atribuye; P5
dice si el tope es una cota o una compuerta. SIGUE A 11 VOLCANES lo que cumple. Nada se adopta con esta prueba.

## 6. Lo que queda fuera, dicho

- **La etiqueta `far` sale de un píxel que `store.py` ya descartó** (`store.py:225-277` recalcula `hotspot_*`
  pero no `final_hotspot_*`; verificador H15, auditor B). No mueve ninguna publicación (en 0 de 20 casos el
  hotspot recalculado cae dentro del inner): frente aparte, con su ciclo A45.
- **El píxel VIIRS 375 saturado se borra** en vez de conservarse (auditor C, C-02) y **el modo de un solo
  píxel corta en 5 MW** (C-03): no tienen brazo acá. Si P7 muestra magnitudes topadas en VIIRS, son el
  siguiente frente.
- La suma de píxeles alertados como magnitud, la caja de 5 × 5 km (D18) y el experimental.

## 7. Costo y riesgo

Diez jobs de un volcán; no toca `data/mirova_equivalent/` ni el NRT. Autentica sólo con `EARTHDATA_TOKEN`
(rotado el 2026-10-08, vence el 2026-12-07). MODIS sólo corre en GitHub Actions (pyhdf), así que no hay ensayo
local de los brazos completos; el control 4 es el ensayo del cableado.

## 8. Qué cambió respecto de la versión 1, y por qué

| hallazgo del verificador | cambio |
|---|---|
| H1 (4): E no podía fallar; su costo se mide sin correr | E pasa a control de cableado; su costo medido va al §1 |
| H2 (3): P4 culpaba a la banda 22 de una pérdida de la etiqueta | P3 atribuye por pares (B a J, J a K); P4 sólo para KE y KET |
| H3 (3): sustrato con diurnas y FALSO_POSITIVO | lo cuenta el evaluador con su etiquetador |
| H4 (3): no había evaluador | `medir_ndc.py`, probado con nulo y dos positivos |
| H5 (3): mezcla de NRT y estándar | despacho desde el 2026-10-13 y control 4.2 |
| H6 (3): la cadena F contra B escondía pérdidas contra C0; veto cero con 2 % de tolerancia | P1 contra B y contra C0; pérdidas descontadas donde el gemelo cambia |
| H14 (3): el tope D9 no estaba | brazos T0 y KET, P5, y P6 separa las topadas |
| menores: perfiles fuera de main, el workflow no imprimía el flag, "13 alertas" eran 11, P7 censurada, alertas sin record | despacho desde main, el workflow imprime etiqueta y tope, cifra corregida, T0 y KET dan la magnitud sin tope, control 4.1 |
