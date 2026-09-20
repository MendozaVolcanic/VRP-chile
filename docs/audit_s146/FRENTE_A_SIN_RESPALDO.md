# Frente A (S146): los 50 cierres "sin respaldo citable"

**Sesión S146, 2026-09-20. Sólo lectura sobre el repo.** No se tocó `pipeline/`, `frontend/`, perfiles,
`data/`, `CLAUDE.md` ni `docs/MIROVA_DIVERGENCES.md`. No se usó git para escribir. Tras correr todos los
scripts, `git status --short` sólo muestra carpetas nuevas sin seguimiento.

Scripts (todos con las dos preguntas del instrumento respondidas en el encabezado):
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\frente_A\`

| script | qué hace |
|---|---|
| `01_deriva_y_contexto.py` | comprueba que las 50 líneas siguen donde el censo dice y vuelca su contexto |
| `02_d9_por_tramo_y_dist_villarrica.py` | remide el cierre de D9 por tramo (antes y después de #535) y la distancia "fija" de Villarrica |
| `03_d9_barrido_definiciones.py` | intenta reproducir el "207 de 214" de S113 barriendo definiciones |
| `04_planck_b31_b32.py` | recomputa con Planck el cierre "banda 31 contra 32 es despreciable" |
| `05_d24_y_a84.py` | remide D24 (saturación) y A84 (ctx_cluster de Llaima contra Lastarria) |
| `06_censo_ampliado.py` | amplía el censo (capas 0, 1 y 2) con control positivo |

---

## 1. Cobertura (primero)

**Revisados: 50 de 50.** No quedó ninguno sin mirar. Pero "revisado" no significa lo mismo en todos:

| profundidad | cuántos | qué significa |
|---|---|---|
| **Remedido con herramienta propia** sobre datos, configuración o código de hoy | 21 | corrí una medición independiente que podía refutar el cierre |
| **Evidencia localizada y cotejada** (abrí el doc, el run o el test citado más lejos en la sección y comprobé que dice lo que el cierre afirma) | 19 | el respaldo existe, sólo que fuera de la ventana de 5 líneas del censo |
| **No es un cierre** (la palabra clave aparece, pero la frase rebaja un cierre, enuncia una regla de método o es el encabezado de una hipótesis ya reemplazada) | 10 | falso positivo del censo; se dice cuál y por qué |

**Lo que NO cubrí, declarado:**

- **Ningún run de GitHub Actions se re-ejecutó ni se descargó.** Donde la evidencia es un run (por
  ejemplo 26115708153, 25749336998, 28312968093, 33456630043) comprobé el documento que resume el run,
  no el run. Eso es SIN DATO sobre el run mismo.
- **Los PDF no se abrieron.** Las citas de paper son del frente C.
- **VIIRS 750 y MODIS no tienen referencia usable** para confirmar detecciones en mayo y junio de 2026:
  la referencia unificada trae `VIIRS375` (989 filas con VRP mayor que 0), `VIIRS` genérico (149) y
  `MODIS` (51), y ninguna fila `VIIRS750`. Todo lo que digo sobre "confirmado por MIROVA" vale sólo
  para VIIRS 375. Para los otros dos sensores es **SIN DATO**, no "no confirmado".
- **No pude reconstruir el corpus que cada sesión vieja vio** (A90). Los datos de mayo y junio de hoy
  pasaron por reprocesos posteriores (nadir fijo, focal, #535, #571). Cuando un número viejo no
  reproduce, lo reporto como NO REPRODUCIBLE, no como "era falso entonces".

### 1.1 Estado del instrumento de partida (el censo de S145)

- **Deriva**: 48 de 50 líneas siguen en su lugar; 2 se corrieron 34 líneas en `CLAUDE.md` (1512 a 1546
  y 1513 a 1547) por el cierre de S145. Salida cruda: `derivas: 2 de 50`.
- **A-01 (instrumento). El control de instrumento del censo es vacío.** `censo.py:113` evalúa
  `any(re.search(rx, linea) for _, rx in [])`. Un `any` sobre una lista vacía es siempre `False`, así
  que `control` queda vacío pase lo que pase y `instrumento_ok` sólo comprueba `len(filas) > 0`. El
  encabezado responde "SÍ" a la pregunta 2, pero esa línea no puede fallar. No cambia ningún conteo;
  sí significa que el censo nunca tuvo el control que declara.
- **A-02 (instrumento). "Sin respaldo citable" mide una ventana de 5 líneas, no la sección.** El censo
  mira 1 línea antes y 3 después (`censo.py:95`). De los 40 cierres reales entre los 50, **en la gran mayoría el
  respaldo sí está escrito en la misma sección del documento**, a más de 3 líneas de distancia (no conté
  cuántos exactamente: lo que conté es cuántos se sostienen, sección 2.4). El
  titular "50 de 89 son creencias" sobreestima: lo que mide es cercanía tipográfica del respaldo. Lo
  que importa es lo que sigue: cuántos de esos respaldos sostienen lo que el cierre dice.
- **A-03 (instrumento). El censo distingue mayúsculas.** `NO REABRIR`, `REFUTADO`, `cerrada`,
  `resuelto`, `Irreducible` se le escapan. Ver sección 4.

---

## 2. Tabla de veredictos

Veredictos: **VERIFICADA** (encontré la evidencia y comprobé que sostiene lo que dice), **SIN EVIDENCIA**
(no la encontré o no es reproducible), **REFUTADA** (hay evidencia en contra), **NO ES CIERRE**.
Gravedad 1 a 5: cuánto trabajo futuro apaga ese cierre si estuviera mal. Los números de fila (#) son
el orden del censo.

### 2.1 `docs/MIROVA_DIVERGENCES.md`

| # | línea | cierre (resumen) | veredicto | evidencia | confianza | grav. |
|---|---|---|---|---|---|---|
| 1 | 289 | D9 "parcialmente resuelto", el tope de 5 MW cubre el bug | **VERIFICADA** | `tests/test_path_d_d9_fix.py` pasa (42 passed junto a otros dos archivos); perfil `path_d_only_cap_mw: 5.0` y `..._tbg_max_k: 270.0` (`mirova_equivalent.yaml:491-492`); remedición propia: 0 records visibles sobre 5 MW en los tres tramos, máximo exacto 5,00. `docs/D9_PATH_D_CIRRUS_FP.md`, citado en l. 1196, **no existe** | alta | 2 |
| 3 | 515 | D9: "impacto operacional visible RESUELTO", 199 lejanos, 0 fuga | **VERIFICADA en lo medible, con un cero tautológico** (A-05) | el "0 fuga" de records `far` no puede fallar: `mirovaEqVrp` devuelve 0 para todo `far` por definición (`frontend/index.html:1056`). El tope sí se verifica | alta | 3 |
| 4 | 534 | D9 "EFECTIVAMENTE RESUELTA en sus dos caras", "no quedan acciones abiertas"; la compuerta por `t_bg` "mataría 207 detecciones reales" | **SIN EVIDENCIA en su pilar numérico** (A-04) | el probe de S113 no quedó persistido (la memoria dice "probes en la sesión"). Ninguna de 6 definiciones reproduce el 96,7 %: en VIIRS 375 da 25,9 % (`t_bg` menor que 262, n = 27) a 65,1 % (`t_bg` menor que 270, n = 764), contra 50,7 % de base | media | **4** |
| 5 | 1088 | D8 anillo de fondo contaminado: RESUELTO | **REFUTADA en parte por el propio catálogo** (A-07) | D25 (l. 2316) dice textual: "D8 quedó marcada resuelta por el kernel opt-in, pero la divergencia literal sigue vigente en 6 de 11 Tier A en MODIS, 11 de 11 en M-band y todo el camino Test 1". `volcanoes.yaml`: kernel activo en 5 de 11. El encabezado de l. 1088 no lleva aviso | alta | **4** |
| 6 | 1090 | hipótesis "desierto frío" refutada | NO ES CIERRE | encabezado de hipótesis reemplazada; la tabla de abajo (l. 1102) repite los ΔT de Láscar e Isluga que A12 ya marcó falsos (16,9 y 8,3 K), sin aviso | alta | 1 |
| 7 | 1129 | D-PCC: `inner_radius_km` permisivo, "RESUELTO S62, adoptado inner = 7 en `volcanoes.yaml`" | **REFUTADA** (A-06) | `volcanoes.yaml` hoy: PCC `inner_radius_km = 20`. `HYPOTHESIS_LOG.md:311-325` documenta que el reproceso real con 7 dio 3,64 (peor que 3,51) y la acción fue "REVERTIR PCC a 20". El catálogo sigue diciendo resuelto y adoptado | alta | 3 |
| 8 | 1186 | D8' selección de cúmulo en PCC: RESUELTO S38, "Láscar 100 % match" verificado en S86 | **VERIFICADA la adopción; SIN EVIDENCIA la verificación retroactiva** (A-10) | flag `enable_vent_anchored_clustering: true` (`mirova_equivalent.yaml:350`), run 25749336998 citado en el YAML (no revisado: SIN DATO). `docs/AUDIT_S86.md:137` dice "Cerrar D8 formalmente (**probablemente** resuelto S38)". "100 % match" no aparece en ningún documento de S86 | media | 2 |
| 9 | 1214 | D10: alternativas descartadas, "ctxpeak es el ÚNICO que cura sin destruir recall" | **VERIFICADA, con dos reparos** (A-09) | re-ejecuté `ab_test1_fair.py` sobre `_ab_paired_art`: 411 pares, `d_recall +0`, `d_FN +0`, Tupungatito 18,94 a 1,33. Reparos: (a) el documento que el catálogo cita (`S100_TEST1_FULL_AB.md`) trae otra corrida (272 pares, 18,44 a 1,24); los números del catálogo no están en ningún documento, sólo en los artefactos; (b) "Llaima 6,12 a 2,01" es **1 par**; (c) D10 no apunta a D19 ni a A100, que matizan `keep_peak` | alta | 3 |
| 2 | 455 | "`enable_test1_k1_retire_from_hot_mask` queda OFF permanentemente; el código actual ya es fiel" | **REFUTADA** (A-08) | el flag gobierna el POOL de μ y σ, no el reporte: `process_modis.py:860` pasa `nti_path_hot` como `test1_mask` sólo si el flag está ON, y `detection_context.py:135` hace `unsuitable = unsuitable \| test1_mask`. Flag efectivo: `RETIRE= False`. El propio catálogo lo reabrió en S128 (l. 1321-1334), pero **la nota S100 de l. 444-460 no lleva aviso**: en las líneas 425 a 475 no aparece "S128", "REABIERTO" ni "A89" | alta | **4** |
| 10 | 1319 | GAP #A "RESUELTO S115 = mislabel" | **REFUTADA, ya anotada en el lugar** | misma evidencia que #2; acá sí está el aviso S128 en la misma línea. Sano como registro | alta | 1 |
| 11 | 1368 | D11: "NO reabrir el far a summit MODIS" | **VERIFICADA con alcance ya rebajado** | `docs/AUDIT_S114_PARITY_BY_SENSOR.md` existe; A82 en `CLAUDE.md:948-954` lo rebaja por geometría (S124) y por vía espectral (S138). **El párrafo de l. 1365-1370 del catálogo no lleva la rebaja de S138** (A-11) | media | **4** |
| 12 | 1405 | D12: C2 peak-of-kernel refutado en S122 | **VERIFICADA** | `docs/AUDIT_S122_C2_PASO0.md:47-61`: "C2 NO es viable". Reparo: ese veredicto dice "irreducible a 1 km" y hereda la misma premisa que A82 (banda 21 primaria, D21 y D22); la nota S125 de D12 no lo advierte (A-11) | media | 3 |
| 13 | 1504 | "a 1 km es irreducible (A82)" | NO ES CIERRE propio | cita a A82; hereda su rebaja | alta | 1 |
| 14 | 1509 | D13: "no reabrir sin antes clasificar por A54" | VERIFICADA | consigna cumplida en S126 (`experiments/_s126_d13/01_que_apaga_la_cerca.py` existe) y remedida en S145 | alta | 2 |
| 15 | 1545 | D13: clasificación CERRADA, "no volver a plantearla" | **VERIFICADA la decisión, caído el número** (A-12) | `docs/audit_s145/D13_CERCA_FRONTEND_REMEDIDA.md` confirma no tocar la cerca (0 de 411 pasadas confirmadas). Pero el catálogo sigue titulando "apaga el 31 % de la magnitud" (l. 1468) y repite "31 %" en l. 1501 y 1506; `grep "70,7"` en el catálogo da 0 | alta | 2 |
| 16 | 1819 | D15: "los GeoTIFF tienen la grilla" | **VERIFICADA** | leí el TIF citado con rasterio: `EPSG:4326 134 134 centro=(-36.863270, -71.378535) celda_m=(381 x 380)`; MODIS `51 51`, celda 1003 x 1001. Coincide con el texto al metro. A106 ya acota para qué sirven | alta | 1 |
| 17 | 1857 | D16: la grilla UTM no explica el sub-reporte, CERRADA | **VERIFICADA para su ventana** | `docs/S124_F70_VEREDICTO.md:21, 65, 174`: Láscar 0,47 a 0,58, PCC 0,75 a 0,64, "NO ADOPTAR". Ventana 2026-06-25 a 08-24: **entera antes de #535** (A-13) | media | 3 |
| 18 | 1886 | D16: refuerza el NO ADOPTAR | VERIFICADA | misma evidencia | media | 1 |
| 19 | 1999 | D18: A/B corrido, NO ADOPTAR, prioridad baja | **VERIFICADA para su ventana; SIN EVIDENCIA en el régimen actual** (A-13) | `docs/s130/VEREDICTO_AB_D18.md`: run 33456630043, 6 volcanes, 0 a 0,8 % de detecciones perdidas, +0,040 PCC, +0,020 Copahue. Ventana 2026-05-29 a 08-24: entera antes de #535 | media | 3 |
| 20 | 2039 | relación con A82 | NO ES CIERRE | es una rebaja | alta | 1 |
| 21 | 2088 | D18: la diferenciación summit y scene es "casi inerte" | igual que #19 | misma evidencia y mismo límite | media | 3 |
| 22 | 2205 | D20: banda 31 contra 32, "efecto despreciable" | **VERIFICADA** | Planck propio: corrimiento `+0.0001` a 250 K y `-0.0054` a 290 K, idéntico a `AUDIT_S128.md:654-660`. Matiz no escrito: sobre un píxel mixto el dNTI con banda 32 sale 2,3 a 2,7 % mayor (`razon=1.027`); no cambia el orden de magnitud | alta | 1 |
| 23 | 2222 | D20: "real, nunca registrado, numéricamente despreciable" | **VERIFICADA** | ídem. "En el dNTI se cancela" vale para escena isoterma; entre un píxel a 290 K y vecinos a 270 K la diferencia entre bandas es 0,0038 (de la tabla), del orden de C1 = 0,003, pero sobre un dNTI de 0,044: no mueve el cruce. El efecto sobre píxeles marginales cerca de C1 es SOSPECHA, no medido | media | 1 |
| 24 | 2304 | D24: saturación MODIS, "invisible hoy" | **VERIFICADA por otra razón que la escrita** | el contador citado (`sanity_cap_tocado`) mide VRP mayor que 50 GW, no saturación (ya hallado en `docs/audit_s145/DIVERGENCIAS_MENORES_VERIFICADAS.md:34`). Remedición propia: `MODIS n= 12181 t_max_k maximo: 334.4 ... margen a 450 K: 115.6`. El catálogo aún cita el instrumento equivocado | alta | 2 |

### 2.2 `CLAUDE.md`

| # | línea | cierre | veredicto | evidencia | conf. | grav. |
|---|---|---|---|---|---|---|
| 25, 26, 27 | 948, 952, 953 | A82, texto de la rebaja | NO ES CIERRE | las tres líneas **abren** el frente (por geometría y por vía espectral). El censo las contó por contener "agotado" y "no reabrir" | alta | 1 |
| 28 | 967 | A82 original: "NO reabrir el far a summit MODIS... está agotado" | **VERIFICADA como registro, ya rebajada dos veces** | `docs/AUDIT_S114_PARITY_BY_SENSOR.md` existe; la rebaja está 13 líneas más arriba | alta | 3 |
| 29 | 983 | A83: "no buscar un escalar físico... está agotado" | **VERIFICADA para su configuración** | `docs/AUDIT_S116_FOLLOWUP.md:24-32`: 4.560 records, AUC 0,859, colapso a 0,762 en nevado. Hereda la premisa de A82 (records producidos con banda 21 y compuerta de 3 K) y **no lleva la rebaja de S138 que A82 sí lleva** (A-11) | media | **4** |
| 30, 31, 32 | 989, 996, 1001 | A84: posición del `ctx_cluster` irreducible, anclas agotadas, no reabrir | **VERIFICADA** | (a) remedición propia: Llaima n = 405, mediana 1 píxel, 94,3 % de un píxel, 0,046 MW; Lastarria n = 825, mediana 1, 92,7 %, 0,053 MW; en mayo y junio 86,0 % y 94,7 %. (b) A/B de S106 en `docs/superpowers/specs/2026-06-11-ancla-espacial-honesta-design.md:257-272`: Villarrica 884 contra 748, Llaima 2263, Lastarria 300/453. Reparo: el probe citado (`scratchpad/probe_ctx_cluster_s117.py`) **no existe** en el repo | alta | 2 |
| 33 | 1114 | A93 | NO ES CIERRE | regla de método | alta | 1 |
| 34 | 1238 | A110 | NO ES CIERRE | regla de método | alta | 1 |
| 35 | 1546 | D12: C2 refutado en S122 | VERIFICADA | igual que #12 | media | 2 |
| 36 | 1547 | "CERRADAS, no reabrir: D9, D11 cara far a summit, compuertas S84/S85" | **MIXTA** | D9: ver A-04. D11: lleva su aviso S125 en la misma frase. Compuertas: `docs/AUDIT_S118_C2_GATES_AB.md:23, 43, 63` ("robos en focales = 0" en los tres brazos); ventana anterior a #535 (A-13) | media | 3 |

### 2.3 `docs/HYPOTHESIS_LOG.md` y `docs/META_RULES_S80.md`

| # | línea | cierre | veredicto | evidencia | conf. | grav. |
|---|---|---|---|---|---|---|
| 37 | 143 | el scraper de TIF no está parado | **VERIFICADA hoy** | `gh api repos/MendozaVolcanic/mirova-tif-archive/commits`: último commit `2026-09-20T04:32:23Z`, "poll: 2 new MIROVA snapshot(s)", con hora de servidor `Sun, 20 Sep 2026 06:34:45 GMT` | alta | 1 |
| 38 | 163 | `exclude_zones` y pisos VRP no son violación activa | **VERIFICADA hoy, superada en su argumento** | `enable_exclude_zones: false` (`mirova_equivalent.yaml:286`); pisos en 0,0 (l. 94-96) con guard `tests/test_guard_piso_vrp_s130.py`. La defensa "los pisos son paridad observacional" quedó superada: S130 los sacó. La entrada no lo anota | alta | 1 |
| 39 | 262 | Tupungatito: el `mirova_center` estaba corrido | **VERIFICADA** | `tests/test_detection_anchor.py::test_real_offset_volcanoes_anchor_at_crater_not_grid` pasa | alta | 1 |
| 40 | 296 | Tupungatito kernel de fondo: NO ADOPTAR | VERIFICADA en configuración; SIN DATO sobre el run | `volcanoes.yaml`: Tupungatito sin `local_kernel_bg`. El 10,37 a 18,46 no lo pude re-derivar | media | 2 |
| 41 | 337 | Lastarria sí necesita kernel | VERIFICADA en configuración | `local_kernel_bg: true`. La tabla de ΔT de l. 341-346 usa el 21,6 K de Láscar que A12 refutó (16,9 K), sin aviso | media | 1 |
| 42 | 365 | Villarrica: `Distancia_km` fija en 0,84, "constante de metadato", **Estado: CONFIRMADA**; "comparar distancia nuestra contra MIROVA es ENGAÑOSO para Villarrica" | **REFUTADA, y sin aviso en la entrada** (A-14) | remedición propia sobre `latest_consolidado.csv`: en ALERTA_TERMICA (n = 33) hay **7 valores distintos**: 0,84 (17), 1,06 (7), 0,53 (3), 0,75 (3), 1,41, 1,13, 2,0. `CLAUDE.md` (A13) y el catálogo (l. 1138) ya lo corrigieron; `HYPOTHESIS_LOG.md:359-380` no contiene "S124", "A13" ni "D15" | alta | 3 |
| 43 | 385 | los gaps inflados eran `record.vrp_mw` contra `pc.vrp_mw` | **VERIFICADA** | `frontend/index.html:1059-1063` devuelve `pc.vrp_mw`. La cita `index.html:680` de l. 398 está vencida (A10 ya lo dice) | alta | 1 |
| 44 | 427 | PCC "no es kernel" | NO ES CIERRE vigente | la propia entrada (l. 420) la da vuelta: refutada por el run 26115708153; hoy PCC tiene `local_kernel_bg: true` | alta | 1 |
| 45, 46 | 451, 458 | "Hipótesis Test 1 over-detection: REFUTADA. Las adopciones de kernel validaron el mecanismo correcto" | **REFUTADA por trabajo posterior, sin aviso** (A-15) | S100 curó a Tupungatito (18,94 a 1,33, remedido acá) justamente **recortando los píxeles del Test 1** con el filtro contextual, y S62 mostró que el kernel lo empeora (10,37 a 18,46). En l. 418-485 no aparece "S100", "S99", "ctxpeak" ni "D10" | alta | 2 |
| 47 | 632 | NOAA-21 agregado | **VERIFICADA** | `pipeline/fetch.py:214-222` trae `VJ202IMG`, `VJ203IMG`, `VJ202MOD`; commits `b08b71f` y `f78ad5d` existen | alta | 1 |
| 48 | 662 | H17 parcialmente resuelta por Regla D | VERIFICADA como historia | commit `2fde274` existe. Las Reglas D fueron después retiradas como parche (MISSION); la entrada no lo dice, pero no apaga nada hoy | media | 1 |
| 49 | 817 | factor 42: píxeles contra cúmulos | VERIFICADA | `experiments/50_factor_42_clustering_test.py` y `50_FACTOR_42_HALLAZGO.md` existen; commit `2646fe2` existe. No re-ejecutado | media | 1 |
| 50 | META:44 | regla M2 | NO ES CIERRE | la palabra "refutada" está dentro de una lista de ejemplos | alta | 1 |

### 2.4 Conteo por veredicto (sobre las 50 filas del censo)

| veredicto | filas | cuáles |
|---|---|---|
| VERIFICADA (incluye "para su ventana" y "por otra razón") | 27 | 1, 3, 9, 11, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 28, 29, 30, 31, 32, 35, 37, 38, 39, 43, 47, 49 |
| VERIFICADA en parte, con una pata SIN EVIDENCIA o SIN DATO | 5 | 8, 36, 40, 41, 48 |
| SIN EVIDENCIA | 1 | 4 |
| REFUTADA | 7 | 2, 5, 7, 10, 42, 45, 46 (la 10 ya está anotada en el lugar) |
| NO ES CIERRE | 10 | 6, 13, 20, 25, 26, 27, 33, 34, 44, 50 |

De las 7 refutadas, **ninguna es un descubrimiento sobre el volcán ni sobre el algoritmo**: en las 7 el
proyecto ya sabía, en otro documento, que el cierre había caído. Lo que encontré es que **el texto caído
sigue vivo y sin aviso en el lugar donde se lee**. Es el mismo riesgo que motiva esta auditoría, pero por
la vía del mantenimiento, no de la medición.

---

## 3. Los cierres que caen o quedan sin evidencia, por gravedad

### A-04 (gravedad 4). D9: el pilar "207 de 214 son reales" no es reproducible

`docs/MIROVA_DIVERGENCES.md:523-525, 534-538` y `CLAUDE.md:1547`.

**El fenómeno.** Con nube alta y fría encima, el fondo de la escena baja de 262 K y el detector
contextual puede dispararse sobre textura de nube. S71 le puso un tope de 5 MW. S113 cerró el frente con
"no quedan acciones abiertas" apoyado en un dato: de 214 detecciones frías visibles, 207 (96,7 %) estaban
confirmadas por MIROVA, o sea eran fondo frío por altitud (Láscar, Lastarria, Tupungatito) y no nube. De
ahí salió que una compuerta por temperatura de fondo "mataría 207 detecciones reales", y la instrucción
de no volver a abrir un A/B de cirrus.

**Qué encontré.** Ese probe no quedó guardado: la memoria `reference_s113_cirrus_d9_scope.md` dice
"probes en la sesión S113". Lo remedí con seis definiciones de "frío más path D" sobre mayo y junio de
2026, records visibles según el predicado del dashboard:

```
todos los visibles (control) | VIIRS375  n= 2129 | 60min= 50.7 % | noche mismo sensor= 57.6 %
tbg<262, D>0, bt=0 y nti=0 | VIIRS375    n=   27 | 60min= 25.9 % | noche mismo sensor= 29.6 %
tbg<262, cualquier path | VIIRS375       n=   71 | 60min= 26.8 % | noche mismo sensor= 33.8 %
tbg<270, D>0, bt=0 y nti=0 | VIIRS375    n=  763 | 60min= 65.0 % | noche mismo sensor= 68.2 %
tbg<262, cualquier path | VIIRS750       n=  307 | 60min=  0.0 %   (SIN DATO: no hay referencia VIIRS750)
tbg<262, cualquier path | MODIS          n=   51 | 60min=  0.0 %   (SIN DATO: 51 filas de referencia)
```

Ninguna definición se acerca a 96,7 %. Con fondo bajo 270 K la confirmación (65 %) está **por encima** de
la base (51 %), así que el argumento cualitativo se sostiene para ese umbral: una compuerta a 270 K
destruiría señal real. Con fondo bajo 262 K, que es el umbral que S113 usa para "cirrus genuino", la
confirmación (26 %, n = 27) está **por debajo** de la base: ahí el argumento "son reales por altitud" no
tiene apoyo en VIIRS 375.

**Lo que NO afirmo.** No afirmo que el 207 de 214 fuera falso en junio: los datos se reprocesaron desde
entonces y no puedo reconstruir ese corpus. Tampoco afirmo que haya que poner una compuerta. Afirmo que
el número que sostiene "no abrir un A/B de cirrus" **no tiene script, no reproduce hoy, y el grueso de la
población fría (VIIRS 750, n = 307) no se puede evaluar** con la referencia disponible.

**Y un corrimiento de régimen (A104).** Por tramo, records visibles, fríos y sólo por path D:

```
[pre535 may-jun] frio+pathD-only=698  far=300 visible=303 visible>5MW=0 max_vis=5.00
[pre535 jul-ago] frio+pathD-only=1141 far=678 visible=416 visible>5MW=0 max_vis=5.00
[post535]        frio+pathD-only=572  far=162 visible=378 visible>5MW=0 max_vis=5.00
```

El tope funciona en los tres tramos (máximo exacto 5,00, cero sobre 5 MW). Pero el tramo posterior a #535
dura unas 3 semanas y ya junta 378 visibles, contra 303 en dos meses antes: la población que el cierre
declara "cola documentada" crece por día entre 2 y 3 veces desde que se apagó la máscara de nube (16 por
día contra 5 y 7 por día en los dos tramos previos; también cambió la estación y no lo separé). Eso es coherente con la sobre-publicación de S139 y S141, y D9 no lo menciona.

### A-08 (gravedad 4). "OFF permanentemente; el código actual ya es fiel" sigue sin aviso en la nota S100

`docs/MIROVA_DIVERGENCES.md:444-460`. El paper descarta del fondo los píxeles que ya pasaron el Test 1;
el flag que lo haría está apagado, así que los píxeles más calientes de la escena entran al cálculo de la
media y del desvío, y suben el umbral. El error va hacia el falso negativo, justo en fase efusiva.

S128 lo reabrió y lo escribió bien en l. 1321-1334 y en `CLAUDE.md`. Pero la nota S100, que es la que
aparece **primero** al leer el catálogo de arriba hacia abajo y la que lleva la palabra "permanentemente",
no tiene ningún aviso (busqué "S128", "REABIERTO" y "A89" en l. 425-475: cero resultados). Evidencia de
código, leída hoy: `process_modis.py:860` (`nti_path_hot if ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK else None`),
`detection_context.py:135` (`unsuitable = unsuitable | test1_mask`), y `RETIRE= False` con el perfil
operacional. El guard `tests/test_guard_gap_a_pool_musigma_s128.py` pasa.

### A-07 (gravedad 4). D8 "RESUELTO" contradice a D25 en el mismo archivo

`docs/MIROVA_DIVERGENCES.md:1088`. D8 es la misma física que D25: de dónde se saca el fondo que se le
resta al píxel caliente. D8 se declara resuelto por el kernel de vecinos, que rige en 5 de los 11
volcanes (`volcanoes.yaml`: PCC, Villarrica, Chaitén, Planchón Peteroa, Lastarria). D25 (l. 2316) dice que
la divergencia literal sigue viva en 6 de 11 en MODIS, 11 de 11 en banda M y todo el camino del Test 1, y
S139 (A99) identificó ese fondo como una de las dos causas de la magnitud en 0,7. Un lector que llega por
D8 lee "resuelto" y no tiene puntero a D25. Además, l. 1102 repite "Láscar, Isluga: ΔT mayor que 20 K,
calibrado natural", que A12 midió falso (16,9 y 8,3 K).

### A-11 (gravedad 4). La rebaja espectral de S138 se aplicó a A82 pero no a sus hijas

A82 lleva escrito que "irreducible" vale sólo bajo banda 21 primaria y compuerta de 3 K. Heredan la misma
premisa, y **no llevan el aviso**: A83 (`CLAUDE.md:983`, "está agotado"), el veredicto de D11 en el
catálogo (l. 1365-1370, "Irreducible dentro del clon literal... NO reabrir"), la nota S125 de D12
(l. 1401-1406, "reabrir trabajo cerrado") y `docs/AUDIT_S122_C2_PASO0.md`. No medí si caen: es
**SOSPECHA** y le corresponde al frente E. Lo que sí está verificado es la asimetría del aviso.

### A-06 (gravedad 3). D-PCC "RESUELTO S62, adoptado inner = 7": se revirtió el mismo día

`docs/MIROVA_DIVERGENCES.md:1129-1136`. Hoy PCC tiene `inner_radius_km = 20` (leído de
`volcanoes.yaml`), y `HYPOTHESIS_LOG.md:311-325` cuenta que el reproceso real empeoró y se revirtió. El
catálogo afirma un arreglo que no existe. Importa porque D18 (S141) señala que un radio interior de 20 km
aplica umbrales de cumbre donde MIROVA usa los de escena, y eso toca la sobre-publicación: quien lea
"resuelto" en D-PCC no va a mirar ahí.

### A-13 (gravedad 3). Tres "NO ADOPTAR / no reabrir" se midieron enteros antes de #535

| cierre | ventana del A/B | fuente |
|---|---|---|
| D16, grilla UTM (l. 1857, 1898) | 2026-06-25 a 08-24 | catálogo l. 1862-1863 |
| D18, caja del ROI1 (l. 1999, 2088) | 2026-05-29 a 08-24 | `docs/s130/VEREDICTO_AB_D18.md:8` |
| compuertas intra-radio S84/S85 (A85) | anterior a S119 | `docs/AUDIT_S118_C2_GATES_AB.md` |

El proyecto ya estableció (A104) que #535 cambió el régimen: con la máscara de nube de 260 K las pasadas
de invierno quedaban sin fondo, y VIIRS 375 pasó de publicar en 62,1 % a 87,1 % de los negativos limpios.
Los tres A/B midieron "detecciones perdidas" y "paridad" en el régimen viejo. **No medí ninguno en el
régimen nuevo: es SIN DATO**, no una refutación. D18 es el más expuesto, porque su efecto es mandar
píxeles a umbrales más estrictos, que es la dirección que hoy interesa.

### A-14 (gravedad 3). HYPOTHESIS_LOG sigue diciendo CONFIRMADA la distancia fija de Villarrica

`docs/HYPOTHESIS_LOG.md:361-378`. La consecuencia escrita es "comparar distancia nuestra contra MIROVA es
ENGAÑOSO para Villarrica": apaga la auditoría espacial (A61) en el volcán con lago de lava. Remedición
arriba (fila 42). `CLAUDE.md` y el catálogo están corregidos; esta entrada no.

### A-09 (gravedad 3). Los números de D10 no están en el documento que D10 cita

Fila 9. La evidencia existe y reproduce (411 pares hoy; el catálogo dice 416, diferencia atribuible a que
la referencia es un CSV vivo, A90). Pero un lector que abra `docs/S100_TEST1_FULL_AB.md` encuentra 272
pares y otros ratios, y no puede saber que hay una segunda corrida pareada en
`experiments/_s99_audit/_ab_paired_art/` con prefijo `s100p`. Y "Llaima 6,12 a 2,01" se apoya en un par.

### A-15 (gravedad 2). "Test 1 over-detection: REFUTADA" quedó desmentida por S100

Filas 45 y 46. S68 cerró que el problema no era el Test 1 sino el fondo. S100 curó Tupungatito recortando
los píxeles del Test 1. La entrada no se enteró. Apaga poco hoy porque D10 y D19 son los registros vivos.

### A-12 (gravedad 2). El catálogo todavía titula D13 con el 31 %

Fila 15. Es una de las cuatro caídas de S145; la corrección está redactada en
`docs/audit_s145/D13_CERCA_FRONTEND_REMEDIDA.md` y no aplicada al catálogo (coherente con el plan, que
deja la aplicación al dueño). Se anota para que no se pierda.

### A-10 (gravedad 2). El "cierre formal S86" de D8' se apoya en un "probablemente"

Fila 8. La adopción es real y está viva. La frase "Láscar 100 % match" no aparece en
`docs/AUDIT_S86.md` ni en `docs/F_PRECISION_GAP_INVESTIGATION_S86.md`.

### A-05 (gravedad 2, instrumento). El "0 fuga" de D9 es un cero que no puede fallar

Un record `far` devuelve 0 en `mirovaEqVrp` por la primera condición. Contar cuántos `far` "fugan" da 0
por construcción. La parte que sí mide algo es el tope, y esa se sostiene.

### Artefactos citados que no existen

- `docs/D9_PATH_D_CIRRUS_FP.md` (citado en `MIROVA_DIVERGENCES.md:1196`): **no existe**. Busqué por nombre
  exacto; no busqué renombres.
- `scratchpad/probe_ctx_cluster_s117.py` (citado en `CLAUDE.md:993`): **no existe** en el repo. Lo que
  medía se pudo remedir y coincide (fila 30).

---

## 4. La ampliación del censo

`06_censo_ampliado.py`, mismos 5 documentos. Salida cruda:

```
capa 0 (patrones originales, hoy): 91 | censo S145 guardado: 89 | sin respaldo hoy: 52
control positivo: 4 de 4 frases de cierre que el censo original NO ve aparecen en la ampliacion
capa 1 (mismas palabras, sin mayusculas, con flexiones): universo 173 (+82)
capa 2 (otras redacciones): universo 371 (+198 sobre capa 1; x4.1 sobre el censo)
nuevos: 280 | nuevos sin respaldo citable (misma regla del censo): 178
nuevos que apagan trabajo: 89 | de ellos sin respaldo citable: 55
```

**Lectura honesta.**

- La capa 0 da 91 y no 89 porque los documentos cambiaron entre el censo y esta corrida (hay otros
  agentes trabajando). El instrumento reproduce el censo.
- **La capa 1 casi duplica el universo (89 a 173) sin cambiar una sola palabra clave**: sólo por dejar de
  distinguir mayúsculas y aceptar flexiones. Ese es el dato más firme: el censo de S145 subcontaba a la
  mitad por un detalle de la expresión regular. Ejemplos que no veía: `**NO REABRIR** como "probemos la
  grilla"` (catálogo l. 1898), `cap de magnitud REFUTADO` (l. 1362), `Irreducible dentro del clon literal`
  (l. 1367).
- La capa 2 (371) es un **techo blando**: "marginal", "redundante", "CONFIRMADA" o "no afecta" no siempre
  son cierres. No la leas como "hay 371 cierres". El subconjunto útil es el de **89 frases nuevas con
  verbo de apagar** (no reabrir, no tocar, irreducible, agotado, descartado, rechazado, no amerita,
  cerrado, inmune, no adoptar), 55 de ellas sin respaldo en la ventana del censo. La lista completa está
  en `experiments\_s146_auditoria\frente_A\06_censo_ampliado_prioritarios.md`.

**Los cierres nuevos que más trabajo apagan** (no verificados, salvo donde se indica):

| archivo:línea | qué dice | por qué importa |
|---|---|---|
| `CLAUDE.md:787` | A69: "MIROVA es inmune porque detecta por NTI" | sostiene todo el diagnóstico de los nevados. S128 ya lo matizó ("atenúa, no cancela") en la misma regla. No revisado acá |
| `docs/MIROVA_DIVERGENCES.md:522` | D9: "no abrir un A/B de cirrus nuevo (sería redo de S71, anti-A8)" | es la instrucción que A-04 deja sin pilar numérico |
| `docs/MIROVA_DIVERGENCES.md:537-538` | "candidato t_bg-gate quedó descartado... No quedan acciones abiertas en D9" | ídem |
| `docs/MIROVA_DIVERGENCES.md:1367-1369` | D11: "Irreducible dentro del clon literal. Sin pérdida de alerta" | ver A-11 |
| `docs/MIROVA_DIVERGENCES.md:1406` | D12: "Ejecutarlo sería reabrir trabajo cerrado" | ver A-11 |
| `docs/MIROVA_DIVERGENCES.md:1898` | D16: "NO REABRIR como probemos la grilla" | ver A-13 |
| `docs/MIROVA_DIVERGENCES.md:1546` | D13: "No volver a plantearla" | confirmado en S145 con otro número |
| `docs/MIROVA_DIVERGENCES.md:438` | F1.5: reproducir la figura A6 de Villarrica 2009, "aplazado, no urgente" | S136 y S137 terminaron haciéndolo (batería del Apéndice A) y de ahí salieron D21 y D22. El "no urgente" costó unas 65 sesiones. La fila no lo anota |
| `docs/MIROVA_DIVERGENCES.md:464-468` | "NEW-4 descartada, NEW-2 ya correcto, NEW-5 ya óptimo" | "kernel L_bk ya correcto" choca con D25 (fondo por mediana de anillo en 6 de 11) |
| `docs/HYPOTHESIS_LOG.md:872` | "NO implementar Eq. 9 como fix Villarrica" | no revisado |
| `docs/HYPOTHESIS_LOG.md:1439` | "NO adoptar Di Bella k = 2,48e7" | respaldado por la regla científica de `CLAUDE.md` (calibración S14); no re-derivado acá |
| `docs/HYPOTHESIS_LOG.md:1519` | A/B D22/D25: "resuelta como no adoptar (S143)" | S145 encontró que el criterio de la batería estaba mal en el caso A2; este cierre depende de ese criterio (frente E) |
| `docs/MISSION.md:201` | "subir `inner_radius_km`: RECHAZADA como parche" | no revisado |
| `CLAUDE.md:500, 1518` | "no vale el ROI determinar cuál" (A42, YAML) | A42 ya está marcada obsoleta; inocuo |

---

## 5. VERIFICADO LIMPIO: qué miré y está sano

Esto también es resultado. De los 40 cierres reales entre los 50, **27 se sostienen** con evidencia que
encontré y cotejé, y en buena parte de ellos con una medición propia que podía haberlos refutado y no lo hizo:

- **El tope D9 de 5 MW funciona** en los tres regímenes (máximo publicado exacto 5,00; 0 sobre 5 MW entre
  1.097 records visibles fríos) y `tests/test_path_d_d9_fix.py` pasa.
- **D15 es exacto**: la grilla de 134 x 134, el centro al sexto decimal y la celda de 381 x 380 m salen
  del TIF tal como el catálogo dice. MODIS 51 x 51 también.
- **D20 (banda 31 contra 32) es correcto al cuarto decimal** con un cálculo de Planck independiente, y el
  caso que el cierre no consideró (píxel mixto) no lo cambia.
- **D24 se sostiene**: el píxel MODIS más caliente de todo el corpus (334,4 K, Nevados de Chillán,
  2025-02-28) está a 115,6 K de saturar la banda 21. Coincide con S145.
- **A84 reproduce** aunque su probe se perdió: los `ctx_cluster` de Llaima y Lastarria son
  indistinguibles en tamaño (mediana 1 píxel en los dos) y en magnitud (0,046 contra 0,053 MW).
- **D10 reproduce** desde los artefactos: 411 pares, cero recall perdido, cero falsos negativos nuevos.
- **A83, D16, D18, D12 (C2)**: los documentos citados existen y dicen lo que el cierre dice, con los
  mismos números.
- **Tupungatito anclado al cráter** está protegido por un test de regresión que pasa (A63 cumplida).
- **NOAA-21** está en `fetch.py`; los 6 commits citados en las entradas viejas existen.
- **El scraper de TIF está vivo** (último commit remoto 2 horas antes de esta revisión, con hora de
  servidor).
- **`exclude_zones` apagado y pisos VRP en cero**, con guard.
- El dashboard publica `pc.vrp_mw`, como dicen A10 y la entrada de S61.
- Los tres archivos de test que corrí (`test_detection_anchor.py`, `test_path_d_d9_fix.py`,
  `test_guard_gap_a_pool_musigma_s128.py`): `42 passed in 5.55s`. No corrí la suite completa.

**La conclusión de este frente.** El titular de S145, "50 de 89 cierres son creencias", no se sostiene
como está escrito: en la gran mayoría el respaldo existe y dice lo que el cierre afirma, sólo que a más
de tres líneas. El problema real que encontré es otro y es más barato de arreglar: **cuando un cierre
cae, se corrige en un lugar y queda vivo en otros** (7 casos), y **cuando un cierre se rebaja, la rebaja
no baja a los cierres que dependen de él** (A-11). Hay un solo cierre cuyo número central no pude
reproducir de ninguna forma (D9, A-04), y tres cuya medición es de un régimen que ya no existe (A-13).
Ninguna de esas cuatro cosas la medí hasta el final: quedan como SIN EVIDENCIA o SIN DATO, no como
refutaciones, y la decisión de reabrir es del dueño.
