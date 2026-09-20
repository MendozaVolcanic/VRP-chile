
## 3. Los CONFIG y los PERDIDO, ordenados por cuánto trabajo apagan

Conteo por veredicto (salida de `tabla.py`): **CONFIG 30, SIGUE 10, NUNCA 6, OBSOLETA 4, PERDIDO 3**.

### 3.1 Los que más apagan

**H-01 (apaga 5). El Test 1 con fondo local sobre NTI se refutó por proteger al detector que hoy es el problema.**
Qué pasa en el volcán: en un cono nevado de noche la cumbre está a unos 272 K y el valle a unos
281 K. Cualquier método que sume "exceso de radiancia MIR sobre un anillo lejano" ve el valle tibio
como calor (A69). S105 diseñó la cura que la física pide: medir el exceso contra los vecinos
inmediatos y en el índice MIR/TIR, que atenúa la topografía. S106 la corrió con barrido de k y
predicciones escritas antes. Lo que dio, leído de `docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md:213-219`:

| volcán | corrimiento al norte, m (anillo → k=2,0) | records con Test 1 disparado | "recall" |
|---|---|---|---|
| Tupungatito | 1047 → 182 | 465 → 220 | 75/75 → 75/75 |
| Villarrica | 748 → 170 | 462 → 177 | 8/11 → 8/11 |
| Llaima | 1097 → 206 | 428 → 209 | 1/1 → 1/1 |
| Láscar (control) | 23 → 43 | 446 → 409 | 117/127 → 117/127 |
| Lastarria (control) | 886 → 742 | 441 → 424 | 94/105 → 94/105 |

Se refutó porque "el Test 1 se apaga en noches ALERTA" (Tupungatito 59 de 75, Villarrica 3 de 11),
con el argumento de que "degradarlo en las noches reales adelgaza la redundancia" (líneas 233-238).
Tres cosas que abrí hoy cambian esa lectura:

- el "recall" de ese script **no mide detección**: `audit_local_sweep.py:70-71` cuenta una noche
  como acertada si existe cualquier record VIIRS 375 con esa fecha, haya o no detección. Es una
  medida de cobertura de gránulos, y por eso da idéntica en los cinco brazos;
- **nunca se midió la publicación por noche con el predicado del dashboard, ni los negativos
  limpios**. La única cantidad sensible que el A/B produjo es la caída de los disparos del Test 1, y
  se contó como daño;
- hoy está medido (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md:79-88`) que el Test 1 solo
  sostiene 186 de los 322 negativos limpios publicados en VIIRS 375 y que sin él siguen seguras 71
  de 75 noches positivas, con 0 pérdidas seguras.

Qué habría que repetir: nada nuevo de código. El flag `ENABLE_TEST1_LOCAL_BG_NTI` sigue en
`pipeline/profile.py:288` y en `pipeline/process_viirs.py:1110`, y los perfiles están en
`pipeline/profiles/_archive/_test1_nti_local{,_ks20,_ks25}.yaml`. Falta correrlo con el código de
hoy y evaluarlo con el banco de paridad de S145. SOSPECHA que no verifiqué: que el flag siga
funcionando después de tres meses de cambios alrededor.

**H-A01 (apaga 5). La adopción del Test 1 integrado se justificó con un recall que nunca se volvió a medir.**
`docs/MIROVA_DIVERGENCES.md:848-870`: recall de ~50 % a 80 % (406 de 507 records) sobre 2026-01-29 a
04-29. Tres problemas: (a) el acierto se contaba como "`pc.vrp_mw` o `triggered_test1`" (línea 887),
o sea que el disparo del propio Test 1 contaba como detección: circular; (b) los FP se contaron sólo
como detecciones `far` (3.840 contra 3.500, líneas 876-879), nunca como pasadas donde MIROVA calló;
(c) la detección contextual de abril ya no existe (hecho 3 de la sección 0). El frente que eso apaga
es exactamente la Fase 2 del plan: hoy se teme apagar el Test 1 "porque subió el recall de 50 a
80 %" (`docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md:163-166`), y ese número es de otra detección.

**H-23 (apaga 5). El barrido de 22 variantes de S46 era ciego a la sobre-publicación.**
`experiments/87_audit_s46_round1.py:153` y `:202`: un FP es sólo "detectamos cuando el scraper marca
`FALSO_POSITIVO` en ese timestamp". Una pasada RUTINA donde publicamos no contaba. Resultado
(`experiments/87_results.md:8-31`): **FP = 39 en 18 de las 22 variantes** (las otras cuatro son subconjuntos por sensor o un brazo aislado: 38, 38, 26 y 0), con C2 en 3, 4 u 8, con o
sin dual-ROI, con n = 12. De ahí salió la idea, repetida después, de que "los umbrales no mueven la
precisión". No se sabe: el instrumento no podía verlo. Lo mismo vale, más suave, para todo A/B
anterior a S139: ninguno tiene negativos limpios salvo S112, que sí los midió (H-17).

**H-A04 (apaga 5). `ctxpeak` se adoptó con 272 pares donde MIROVA publicó y cero negativos.**
`docs/S100_TEST1_FULL_AB.md:16-33`: 256 de los 272 pares son de seis volcanes; Llaima 0, Copahue 1,
Villarrica 2, NdC 3. El criterio "justo" (sólo records comunes) se escribió después de detectar que
los dos brazos habían bajado gránulos distintos (líneas 8-14), así que no es pre-registrado. Lo que
pasó después ya lo sabe el proyecto (A100, D19, S143) pero la fila de la adopción no lo dice.

### 3.2 Los que apagan 4

- **H-05** (S135, brazo B sin `keep_peak`): 0 noches perdidas de 260, 100 % del artefacto quitado, y
  rechazado por paridad agregada 0,692 contra 0,708 (`experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:15-25`).
  Esa paridad es la que A100 mostró accidental y V-12 mostró compensada entre volcanes.
- **H-09** (banda 22, S133): el criterio que falló era de invariancia ON/OFF, no de paridad
  (`docs/audit_s139/VERIFICADOR.md:30-32`). Dos volcanes, un mes, con la compuerta puesta.
- **H-14** (F70): ya rebajado por V-04; agrego que corrió con M260.
- **H-17 / H-A07** (S112): ver sección 4.
- **H-22** (D9, co-validación): reabierta por V-01. Mi aporte es una SOSPECHA de instrumento: la
  evidencia de S70 se leyó de `diag_n_dnti_ctx_path` cinco días después de que ese contador pasara a
  ser sólo diagnóstico (`pipeline/process_viirs.py:1235-1237`). No la verifiqué corriendo nada.

### 3.3 Los que apagan 3

H-02, H-03 (las otras dos versiones NTI del Test 1, mismo defecto de criterio que H-01), H-08 (área:
veredicto declarado parcial, chunk 1), H-10 (D18: régimen correcto, unidad equivocada), H-12 (corona:
contó como daño perder 8 detecciones de 0,021 a 0,042 MW), H-15 (D12), H-18 (fondo local de magnitud
en MODIS: misma familia que D25, medida con banda 21 y sin referencia), H-20 y H-21 (la justificación
de `ctxpeak`, que `docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:78-84` ya declara sin respaldo), H-24
(A19 Tupungatito: medido un día antes de descubrir que el ancla apuntaba al flanco equivocado), H-36
(A82), H-A03 (kernel por volcán), H-A08 (máscara apagada).

### 3.4 Instrumentos perdidos

| fila | qué se perdió | quién lo encontró |
|---|---|---|
| H-15 | artefactos del A/B de D12; el script no carga referencia | V-09 (hoy) |
| H-19 | `scratchpad/probe_ctx_cluster_s117.py` (A84) | B-09 (hoy) |
| H-35 | script del AUC 0,859 de A83 (queda un JSON) | B-08, V-03 (hoy) |
| (D9) | el script del "207 de 214" | V-01 (hoy) |
| todos los A/B de `_archive/` | **SOSPECHA**: los artefactos de GitHub Actions de los runs de abril a junio caducan a los 90 días. Si las salidas por brazo no se commitearon a `data/` o a `experiments/`, los brazos de H-01, H-02, H-03, H-20 y H-21 no se pueden re-evaluar sin re-correr. No lo comprobé contra la API de GitHub | este frente |

Instrumentos que **sí existen** (comprobado con `ls`, no corridos): `experiments/51_p31_ab/DELTA_REPORT.md`,
`52_aveni_tir_poc.py`, `41_DIAGNOSIS_FINAL_S21.md`, `50_factor_42_clustering_test.py`,
`100_aggregation_strategies_offline.py`, `101_background_variants_offline.py`,
`98_calibrate_te_villarrica.py`, `104_s60_*.md`, `105_s61_*.py`, `120_audit_tif_vrp_sumable/`,
`122_r2_chaiten/`, `125_r2_pcc/`, `127_path_d_tbg_calibration/`, `130_r3_*/`, `131_r2_*/`,
`76_audit_independent.py`, `88_audit_s47_fps_distribution.py`, `scripts/verify_reproc.py`,
`docs/DRIFTS_S17.md`, `_s118_c2ab/`, `_s121_d12_ab/`, `_s124_f70/`, `_s125_magnitud/02_veredicto_ab.py`,
`_s126_cloudmask/02_veredicto.py`, `_s126_corona/01_veredicto.py`, `_s129_suma/02_radio_de_suma.py`,
`_s130_d18/`, `_s133/resultado_ab_b22.json`, `_s135_ab_d1d2/evaluar_ab.py`, `_s99_audit/ab_test1_fair.py`,
`_s112_test1_lowmag/audit_t1lm_ab.py`, `_s107_modis_localmag/`, `_s109_modis_mag/`, `_s111_d11/`.

## 4. Adopciones medidas con un criterio que hoy se sabe defectuoso

Perfil efectivo de hoy (`VRP_PROFILE=mirova_equivalent`, leído de `pipeline.profile`): 28 flags en
True. Cada uno es una adopción. Las que pude fechar con `git log -S` sobre `mirova_equivalent.yaml`:
Test 1 y dual-ROI BT 2026-05-01; agrupamiento anclado al cráter y filtro de distancia por píxel
2026-05-12; fondo global del Test 1 por volcán 2026-05-13; primer y segundo pase 2026-05-16; kernel
local 2026-05-18; píxel único sub-MW y compuerta TIR 2026-05-24; `ctxpeak` 2026-06-04; ancla honesta
2026-06-11; núcleo focal MODIS 2026-06-15. **Todas son anteriores a #535 y todas menos las tres
últimas son anteriores al nadir fijo.**

| fila | adopción | defecto del criterio | qué dice hoy la medición |
|---|---|---|---|
| **H-A07** | anillo intermedio y prioridad al cúmulo débil (S112), por volcán | **se adoptó contra su propio pre-registro.** El A/B midió inflación en pasadas RUTINA y dio 24 (control) contra 54 (`docs/S112_TEST1_LOWMAG_AB_RESULTS.md:37-48`). Se adoptó el mismo día por evidencia externa (Sentinel-2) y "recall sobre precisión" (líneas 3-16) | es la única adopción cuyo A/B vio duplicarse la sobre-publicación. Sigue en True. Bajo la regla S143 es candidata directa a mudarse al perfil experimental. Está gateada por volcán, que la misión prohíbe |
| **H-A01** | Test 1 integrado | acierto circular (contaba su propio disparo), FP sólo `far`, detección de abril ya reemplazada | sin él siguen seguras 71 de 75 noches (FASE1) |
| **H-A04** | `ctxpeak` / `keep_peak` | sólo positivos; nevados con 0 a 3 pares; criterio escrito tras ver un confusor | A100, D19, S143: toda la baja de publicación en negativos viene de apagarlo |
| **H-A08** | máscara apagada | "21 de 286 detecciones nuevas caen en noches que MIROVA confirma" leído como costo chico (`docs/S126_CLOUDMASK_RESULTADO.md:63`) | 265 de 286 son publicaciones donde MIROVA no alertó. La decisión es correcta por fidelidad; el costo está mal dimensionado |
| **H-A03** | kernel de fondo por volcán | Villarrica con n = 2; por volcán; "N de records summit baja 65 %" nunca leído como efecto sobre negativos | D25 propone lo mismo, uniforme |
| **H-A02** | primer y segundo pase (S46) | la ganancia medida son 3 records MODIS; FP invariante | defendible por fidelidad, no por la medición |
| **H-A06** | núcleo focal MODIS (S109) | C2 de 71 % contra 85 % pre-registrado, reinterpretado después como "métrica de maximizar" (`docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md:30-33`); sin referencia fuera de Láscar | el plan definitivo dice que MODIS publica igual con alerta (11,5 %) que sin ella (10,2 %) |
| H-A05 | nadir fijo | bien medido para lo que es (fórmula). MODIS con n = 1 fuera de Láscar | sigue valiendo; no leer 0,78 como paridad sana |
| H-A09, H-A10 | pisos, cercas, y las de mayo | no abrí los audits: SIN DATO | |

Patrón común, en una línea: **hasta S139 ninguna adopción midió qué pasa donde MIROVA mira y no ve
nada**, salvo S112, que lo midió, vio que empeoraba y adoptó igual.

## 5. Cosas que vale la pena probar, que nunca se probaron o se probaron bajo condiciones que ya no existen

Ordenadas por lo que pueden mover por unidad de costo. Ninguna toca `pipeline/` en su primer paso.
Donde la puerta de la misión tiene algo que decir, lo digo.

**P1. La curva de dosis del Test 1 integrado: cuánta sobre-publicación y cuántas noches se van a cada umbral k.**
- Qué es: hoy dispara a 3 sigmas. `test1_k_observed` está persistido en todos los records de los tres
  sensores (`FASE1_SUSTRATO:56`). Se tabula, por volcán y sensor, cuántos negativos limpios T1_SOLO y
  cuántas noches positivas quedan a k = 3, 4, 5, 6, 8.
- Por qué podría funcionar: el frente F mostró hoy que el recorte `max(0, ...)` hace que el ruido puro
  sume positivo (F-01, `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:124-140`), o sea que 3 sigmas
  nominales valen menos. Y el recall casi no depende de él (71 de 75 noches siguen sin Test 1), así
  que el umbral no necesita discriminar: basta con que deje de disparar.
- Qué lo sugiere: H-01 (a k = 2,0 con fondo local los disparos ya caían a la mitad sin perder
  noches); `docs/MIROVA_DIVERGENCES.md:1435` ("k_sigma REFUTADO offline": se juzgó sólo por posición,
  "el gatillo no mueve el centroide").
- Costo del sustrato: minutos, sobre lo persistido, con el banco de S145.
- Riesgo de recall: las 4 noches SIN DATO de `FASE1_SUSTRATO:103` (Isluga 09-19, Lastarria 09-01,
  NdC 09-18, Villarrica 09-16). Listarlas una por una.
- Misión: es un umbral de un detector propio. No es literal; es la versión graduada de la Fase 2b
  (mudar el Test 1 al experimental) y sirve para saber cuánto cuesta esa mudanza.

**P2. Re-evaluar, sin re-correr, las salidas de S135 (brazo B) y S143 con criterio por volcán y en pasadas.**
- Qué es: los evaluadores y sus JSON están en `experiments/_s135_ab_d1d2/` y `experiments/_s143_evaluador/`.
  Cambiar el criterio 3 de paridad agregada por razón estratificada por volcán con n declarado.
- Por qué: el brazo B perdió por 0,016 de una métrica que premiaba un píxel a ~3 km del cráter (A100).
- Costo: horas, sin CI. Riesgo de recall: ninguno nuevo (0 de 260 noches en S135).
- Límite: S144 dejó "no habilitado apagar `keep_peak`" porque no se separa relieve tibio de fuente
  permanente. Esto no lo resuelve; sólo quita un criterio malo de encima del veredicto.

**P3. El Test 1 con fondo local sobre NTI (H-01), corrido hoy y medido con el banco de paridad.**
- Por qué físicamente: es la única cura de A69 que el proyecto diseñó y que además baja los disparos
  del Test 1 en los nevados (Villarrica, Llaima, Tupungatito), que en la tabla por volcán de la Fase 1
  son justo donde T1_SOLO manda (Villarrica 27 de 40, Llaima 26 de 45, Copahue 39 de 48).
- Costo del sustrato: **no se puede medir sobre lo persistido** (cambia el fondo del Test 1). Pide un
  probe de sólo lectura tipo A75 o un A/B en Actions con los perfiles archivados. Antes, comprobar si
  los artefactos de los runs 27275241269 y 27276651420 siguen vivos (SOSPECHA: caducaron).
- Riesgo de recall: en junio, con otro régimen, Villarrica perdía el disparo en 5 de 7 noches de lava
  en VIIRS 375 (design, líneas 254-270). Hay que ver si esas noches se siguen publicando por el camino
  contextual: es exactamente lo que no se midió.
- Misión: mejora un detector propio. Si la Fase 2 decide mudar el Test 1 al experimental, P3 pasa a
  ser una mejora del experimental, no del clon.

**P4. Mudar al experimental el anillo intermedio de S112 (H-A07), midiendo antes cuánto sostiene.**
- Qué es: `ENABLE_TEST1_INTERMEDIATE_BG` y `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER`, gateados por volcán
  en Láscar, NdC y Lastarria.
- Sustrato: en la Fase 1, NdC tiene 26 T1_SOLO de 44 negativos publicados y Lastarria 13 de 21
  (`FASE1_SUSTRATO:135-139`). Cuántos dependen del anillo intermedio no sale de lo persistido: SIN DATO,
  pide probe. Costo: un probe chico (tres volcanes).
- Riesgo de recall: las alertas de 0,02 a 0,06 MW de NdC, que son reales (Sentinel-2) y que MIROVA sí
  publica. Por eso es mudanza y no borrado.

**P5. La caja de 5 km del ROI1 (D18), re-evaluada en pasadas con negativo limpio.**
- Por qué: en PCC el radio interno es de 20 km; con la caja del paper casi todo el lacolito pasa a
  umbrales de escena (C1 = 0,010, C2 = 10). PCC concentra 31 de las 50 publicaciones MODIS en negativo
  limpio, 28 por el camino del paper (`FASE1_SUSTRATO:175, 187`). El A/B de S130 ya cambió el 17,98 %
  de los records de PCC (`docs/s130/VEREDICTO_AB_D18.md:12-14`) y nadie miró si eso eran negativos.
- Costo: si las salidas de `_s130_d18_*` siguen en el repo o en artefactos, horas; si no, un A/B.
  No lo comprobé. Es uniforme y literal: pasa la puerta de la misión por la pregunta 1.
- Riesgo de recall: bajo (0 a 0,8 % de detecciones perdidas en S130), pero PCC tiene 12 noches
  positivas en la ventana actual y son AMBOS o CTX: mirarlas una por una.

**P6. La regla de preferencia entre banda I y banda M (F-07 del frente F), que nadie midió.**
- Qué es: Coppola 2026 retiene la de 750 m cuando coinciden. Nosotros publicamos las dos.
- Por qué importa acá: VIIRS 375 publica en 86,3 % de los negativos y VIIRS 750 en 21,4 %. Y podría
  ser en parte un artefacto del cruce (una fila de MIROVA contra dos records nuestros).
- Costo: minutos. Salvedad A105: es la regla del archivo OSF, no necesariamente del NRT.

**P7. El fondo por vecinos (D25) junto con el conteo de píxeles, en VIIRS 375, para la magnitud.**
- Lo sugieren F-03 y F-05 del frente F, `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:45-64`
  y el probe v2 de S142. Ya se probó la mitad (S143: D25 mueve la magnitud de 0,75 a 0,94 y empuja la
  publicación +0,052). Lo que **nunca se corrió** es la suma de escena como brazo de reproceso
  (`docs/s129/RADIO_DE_SUMA.md:69-80` la dejó "como brazo" y ahí quedó) ni el cúmulo de VRP máximo,
  que offline gana en 8 de 11 volcanes (0,83 contra 0,71, `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:34-47`,
  ventana que cruza #535 y sólo sobre noches donde MIROVA publicó).
- Riesgo: es de magnitud, no de alerta; y S124 avisa que el máximo puede reintroducir el robo de
  cúmulo. S118 midió después 0 robos en 214 noches, pero con las cercas recién apagadas y M260.

**P8. El brazo fiel de geometría: bow tie más remuestreo centrado en `get_grid_center`.**
- Ya está en la Fase 4 del plan. Lo anoto porque es el caso más limpio de "refutado lo que no era":
  D16 refutó el regrid F70 (mal centrado, sin bow tie, con M260), y el A/B del área (H-08) tiene
  veredicto sólo del chunk 1. Sustrato: minutos (razón por bin de cenit, sólo código posterior a #535).

**P9. El Test 1 sin el recorte a cero, o con el nulo de ruido descontado.**
- Sale de F-01. Nunca se probó nada parecido: todos los A/B del Test 1 tocaron el fondo, el filtro o
  el ancla, nunca el estadístico. Es la corrección mínima a un detector propio. Costo: el nulo ya lo
  midió el frente F (`experiments/_s146_auditoria/frente_F/`); falta pasarlo a pasadas publicadas.

**Lo que NO propongo, y por qué**: un piso de intensidad (H-37: cortaría alertas reales de 0,02 MW y
no es del NRT); un discriminante por record contra la etiqueta de MIROVA (H-35, prohibido y además
paradoja de Simpson); radios o umbrales por volcán (la suma con radio por volcán de S129, el inner de
PCC); la compuerta de campo difuso de S93 y la supresión de cirrus en display (parches de display para
artefactos, A72); una compuerta por `t_bg` (anti-MIROVA). El máximo diario de Laiolo 2026 tampoco: es
el procesamiento del estudio de Stromboli, igual que el filtro de intensidad.

## 6. Verificado limpio: se midió bien y no hay que repetirlo

- **H-04 (S143)** y **H-07 (probes de S141/S142)**: corridos con el código de hoy, con pre-registro,
  verificador antes y después, negativos limpios y cobertura contada. La atribución de S143 (todo el
  descenso viene de `keep_peak`; D22 y D25 empujan en contra en VIIRS 375) no hay que repetirla.
- **H-11**: el GAP #A no tiene sustrato en volcanes sin lava expuesta. Dos mediciones independientes
  (S130 y la Fase 1 de hoy: `diag_n_nti_path > 0` en 5 de 954 pasadas).
- **H-31, H-40 y el brazo "sin test de temperatura de brillo"**: ese camino está apagado desde S40 y
  su contador es cero en toda la ventana actual. Nada que correr.
- **H-32**: el k de 18,0 y la no adopción de la Ec. 9 de Aveni. Son de fórmula.
- **H-34**: las hipótesis de infraestructura de S17 y NOAA-21.
- **H-37**: el filtro de intensidad, descartado por dos vías y releído por el verificador de S141.
- **H-25 y H-26**: el radio de PCC y el percentil de anillo. No por bien medidos, sino porque la
  puerta de la misión los rechaza igual y D25 dice otra cosa.
- **H-42**: la batería del Apéndice A corre con el código de hoy. Sirve para fidelidad MODIS, no para
  la sobre-publicación.
- **H-A05**: el nadir fijo como fórmula.

## 7. Límites de este informe

- Ningún script se corrió. "Existe" es `ls`; "mide tal cosa" es lectura del código en las dos filas A
  donde lo abrí, y lectura del documento en el resto.
- La fecha de código de cada A/B la deduje del commit de su flag, de su perfil o de sus datos. No
  consulté la API de GitHub para la fecha de cada run.
- Los A/B de mayo (S38 a S44, S72 a S73) están agrupados con sólo existencia y ventana.
- No cubrí los bloques de arranque ni las notas de cierre de `tasks/`. Ahí puede haber ideas anotadas
  que esta lista no tiene.
- La columna "trabajo que apaga" (0 a 5) es mi juicio, no una medición.
- Todo esto es hallazgo del que midió. Falta el verificador con contexto limpio.

## Apéndice A. Las 66 entradas de `HYPOTHESIS_LOG.md` y dónde quedaron

| entradas | destino |
|---|---|
| H_S118_C2_GATES_NO_THEFT | H-16 |
| H_S70_PATH_D_CIRRUS_FP | H-22 |
| H_S70_R2_RETROACTIVO_4VOLS, H_S69_R2_RETROACTIVO_LASTARRIA, H_S70_TIF_VRP_SUMABILITY | H-A03 (validación R2 de un caso por volcán); confirmadas, no son descartes |
| H_S69_MODIS_OUTLIERS_05_17, H_S68_TIF_ARCHIVE_NOT_STOPPED, H_S68_ANTIPATRONES_AUDIT, H_S67_DASHBOARD_AUDIT_FINDINGS | confirmadas, fuera del censo (diagnósticos y display) |
| H_S66, H_S64 (Tupungatito, ancla) | contexto de H-24; verificadas limpias por el frente A |
| H_S62_LASTARRIA_TUPUNGATITO_AB_RESULTS | H-24 y H-A03 |
| H_S62_PCC_INNER_REPROC | H-25 |
| H_S61_LASTARRIA, H_S61_PLANCHON, H_S60_KERNEL_BG, H_S58 (dos), H_S57 | H-A03. **H_S61_PLANCHON_KERNEL_BG sigue con el estado sin llenar** ("<CONFIRMADA / REFUTADA> tras Task 3", líneas 501-502) |
| H_S61_MIROVA_DIST_FIXED_VILLARRICA | refutada en S124 (A13); el frente A ya lo marcó (A-14) |
| H_S61_AUDIT_FIELD_FIX | confirmada (A10), verificada por el frente B |
| H_S61_PCC_INFLATION_NOT_KERNEL, H_S61_TUPUNGATITO_KERNEL_BG_REVIEW | refutadas por S63 y S62. La segunda decía "Test 1 sobre-detecta, 70 a 470 píxeles" y se cerró como "especulativa": hoy D30 y la Fase 1 le dan la razón en lo esencial. Es un descarte que el tiempo revirtió |
| H1, H2, H3, H5, H7, H8, H9 | H-34 |
| H4, H6, H10, H15, H12, H18, H_S21_11, H_S47 | confirmadas y resueltas (infraestructura, esquema, NOAA-21, media aritmética) |
| H17 | H-33 y H-34 (H17a descartada por inspección visual de Nicolás: NUNCA medida) |
| H_S21_10 | H-33 |
| H11 | activa, de display |
| H13 | H-31 |
| H14, H16, H_S24_AVENI_NEGATIVE, H_S24_DIBELLA_OUT_OF_OSF | H-32 |
| H_S23_FACTOR42 | confirmada (agregación) |
| H_S23_LOCAL_ROI | H-40 |
| H_S24_P31_VALIDATED | adopción de mayo, PRE46: dentro de H-A10 |
| H_S49, H_S48 (dos) | H-A01 (el arreglo de auditoría de S48 es el origen del acierto circular: cuenta TP por `test1 + summit` aunque `pc.vrp` sea 0, líneas 920-923) |
| H_S56, H_S55, H_S54, H_S53 | H-26, H-27, H-28 y fila de Eq.16 en `docs/MISSION.md:183` |
| H_S52, H_S51, H_S48_PCC_COORD | confirmadas (ancla de PCC) |
| H_S137 (tres), H_S141 (dos), H_S143, H_S144 | H-42, H-07, H-04, H-06. Las tres de S137 siguen "active" sin resolución |

## Apéndice B. Hallazgos numerados

- **H-01 a H-43 y H-A01 a H-A10**: las filas de la tabla.
- **H-44. La máscara de 260 K era código, no perfil, y sólo de VIIRS 375** (sección 0, hecho 1). Todo
  A/B de VIIRS 375 del 5 de abril al 28 de agosto corrió con ella aunque su perfil dijera 0.
- **H-45. Corrección a A-13 del frente A**: D18 no corrió en el régimen viejo (sección 0, hecho 2).
- **H-46. Hasta S139 ningún A/B tiene negativos limpios, salvo S112** (sección 4).
- **H-47. `H_S61_PLANCHON_KERNEL_BG` quedó con el veredicto sin escribir** y tres hipótesis de S137
  siguen "active" (apéndice A).
- **H-48. Un descarte que el tiempo revirtió**: `H_S61_TUPUNGATITO_KERNEL_BG_REVIEW` ("el Test 1
  acepta demasiados píxeles") se cerró en S68 como especulativa (`docs/HYPOTHESIS_LOG.md:451`).
