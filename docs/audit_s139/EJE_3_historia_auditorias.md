# Auditoría S139, eje 3: qué dicen las auditorías anteriores sobre el plan A, y por qué no convergemos

**Fecha**: 2026-09-13 (hora de la sesión; commits de hoy visibles: `b973ccc39` 14:35 -0300, #642).
**Modo**: read-only sobre el repo. Único archivo escrito fuera de este informe: dos scripts en
`experiments/_s139_audit/eje3/`. Sin commits, ramas ni CI.
**Material leído** (secciones pertinentes, no todo): `docs/AUDIT_S138.md` completo, `docs/audit_s138/EJE_5` §4 y
`EJE_6` §1, `tasks/BLOQUE_ARRANQUE_S139.md` completo y §e de S136 y S137, `docs/MIROVA_DIVERGENCES.md`
(D1 a D8, D12, D13, D18 a D29), `docs/MISSION.md` completo, `docs/AUDIT_S134.md` §1 a §5, `docs/AUDIT_S114_PARITY_BY_SENSOR.md`
§1 a §6, `docs/AUDIT_S104_SYSTEMIC_DIVERGENCE.md`, `docs/AUDIT_S86.md` TL;DR, `docs/AUDIT_S108_AB_MODIS_VEREDICTO.md`,
`docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md`, `docs/AUDIT_S111_TEST1_LOWMAG_FN.md`, `docs/AUDIT_S112_DASHBOARD_MIROVA.md`,
`docs/AUDIT_S121_D12_AB.md`, `docs/AUDIT_S128.md` §3, `docs/AUDIT_INTEGRAL_S81.md` §4, `docs/REAUDITORIA_S52.md`,
`docs/PROCESS_RULES_S33.md`, `docs/s132/AB_DISTANCE_CLASS_MODIS.md`, `docs/s133/B22_EVIDENCIA.md`,
`docs/s133/AB_B22_VEREDICTO.md`, `docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md` (índice de
secciones y veredicto), `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md`, `experiments/_s136/ETIQUETA_IMPACTO_NETO.md`,
`experiments/_s137/{EL_AB_DE_D1_YA_ESTABA_CORRIDO,RESULTADO_FONDO_LOCAL,EL_CIERRE_DE_S136_ES_CIRCULAR}.md`,
`reports/h8_ab_final_report.md`, índice de encabezados de `docs/HYPOTHESIS_LOG.md`, `frontend/index.html:1043-1480`.

**Supuestos declarados**
- S1. "Plan A" es el texto del brief de S139 (5 pasos). No leí ningún documento que lo formalice.
- S2. Las cifras de motivación del brief (9 de 75, 17 %, 97 %, 92 %) son de otros ejes; no las re-medí.
- S3. Noche local aproximada = fecha de (UTC menos 16 h); "nocturno" aproximado = hora UTC fuera de 11 a 21.
  No es el filtro solar del pipeline; se usa sólo para ver la forma del etiquetado de la referencia.
- S4. La partición focal/nevado oficial es la de `scripts/build_c2ab_windows.py:41-42` (leída hoy).

---

## 0. Las dos mediciones propias de esta sesión

### 0.1 `01_rutina_como_negativo.py`: ¿una noche RUTINA es un negativo limpio?

1. *Si RUTINA no fuera un negativo, ¿lo vería?* Sí: cuenta las noches RUTINA que además tienen ALERTA.
2. *Si el instrumento estuviera muerto*: con 0 filas imprime SIN DATO; los conteos por Tipo_Registro son el
   control de que la columna se leyó. **Control positivo**: noches ALERTA de Láscar = 189 (> 0).

Sustrato: `latest_consolidado.csv` (37.319 filas, 2026-01-10 a 2026-09-13; RUTINA 35.018, ALERTA_TERMICA 1.450,
FALSO_POSITIVO 851) y `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (937 filas, hasta 2026-09-07).
Salida (con filtro nocturno aproximado):

| lo medido | valor |
|---|---|
| noches-volcán con al menos una fila RUTINA | 2.661 |
| de esas, con ALERTA (CONS u OCR, cualquier sensor) la misma noche | **927 (34,8 %)** |
| noches RUTINA sin ALERTA (candidatas a negativo) | 1.734; **304 de ellas con FALSO_POSITIVO** |
| noches RUTINA por volcán / con ALERTA | Chaitén 246/41, Copahue 246/5, Isluga 245/170, Láscar 236/179, Lastarria 246/157, Llaima 246/2, NdC 246/10, PP 246/97, PCC 246/125, Tupungatito 212/110, Villarrica 246/31 |
| filas RUTINA con VRP_MW > 0 | 17 |

**Todos los volcanes tienen RUTINA prácticamente todas las noches de la ventana** (246 de 246, salvo Tupungatito que
arranca después, D2 F-B3). "Hay al menos un RUTINA esa noche" es por lo tanto casi siempre verdadero y no distingue
una noche que MIROVA procesó de una que no.

### 0.2 `02_rutina_por_pasada.py`: ¿RUTINA marca pasadas o sólo que el scraper corrió?

1. *Si RUTINA fuera un marcador por escaneo y no por pasada, ¿lo vería?* Sí: fracción de nuestras pasadas nocturnas
   con una fila CONS del mismo sensor a 20 min o menos, contra el mismo cálculo con el reloj de CONS corrido 6 h.
2. *Si el pareo estuviera muerto* (sensores mal mapeados, zona horaria): real y corrido darían lo mismo o ambos 0.
   **Control positivo**: ALERTA de CONS con pasada nuestra a 20 min o menos (Láscar VIIRS375 206/228, Isluga 204/206).

| volcán | sensor | pasadas nuestras nocturnas | con fila CONS a <=20 min | control reloj +6 h |
|---|---|---|---|---|
| Láscar | MODIS / V750 / V375 | 434 / 836 / 843 | 0,952 / 0,749 / 0,722 | 0,279 / 0,000 / 0,000 |
| Llaima | MODIS / V750 / V375 | 508 / 1.021 / 1.023 | 0,980 / 0,748 / 0,724 | 0,317 / 0,000 / 0,000 |
| Villarrica | MODIS / V750 / V375 | 547 / 1.106 / 1.109 | 0,960 / 0,729 / 0,714 | 0,300 / 0,000 / 0,000 |
| Isluga | MODIS / V750 / V375 | 420 / 812 / 816 | 0,971 / 0,767 / 0,750 | 0,298 / 0,000 / 0,000 |

Lectura: **RUTINA es un registro por pasada y por sensor**, no un marcador de escaneo (en VIIRS el control corrido cae
a 0). En MODIS el control no cae a 0 porque Terra y Aqua suman varias pasadas diarias y un corrimiento de 6 h cae cerca
de otra; el 0,95 a 0,98 real sigue siendo muy superior. **Un 22 a 29 % de nuestras pasadas VIIRS nocturnas no tienen
ninguna fila de MIROVA** del mismo sensor: eso es la cobertura parcial de la referencia (D2), y en esas pasadas no hay
negativo ni positivo. Ventana: 2026-01-10 a hoy; denominadores en la tabla.

---

## 1. Hallazgos, por gravedad

### H301. El banco de negativos y las métricas del paso 1 y 2 del plan ya están pre-registrados en S138, con un predicado que tampoco es el del dashboard

- **ARCHIVO:LÍNEA**: `docs/audit_s138/EJE_5_bateria_apendice_instrumento.md` §4.4 (unidad "noche local por volcán";
  "publica" = `primary_cluster.vrp_mw > 0` con `final_hotspot_dist_km <= inner_radius_km`; C2 sobre-detección = noches
  sin ALERTA en ningún sensor "con al menos un registro RUTINA de MIROVA esa noche", bootstrap pareado por noche); §4.2
  (holdout jun-ago 2026, 316 noches); `frontend/index.html:1043-1064` (`mirovaEqVrp`).
- **QUÉ PASA**: el plan A propone construir desde cero un banco de positivos y negativos por noche y métricas
  pre-registradas. Eso existe desde hoy a la mañana, escrito por el eje 5 de S138, y está "en espera" por la regla de
  salida. Pero su predicado de publicación usa `final_hotspot_dist_km`, no `distance_class == "summit"` ni
  `pc.centroid_dist_km`, que es lo que exige `mirovaEqVrp`. Es el mismo defecto que S138 le imputó a la batería
  (H-S138-03: "usa un predicado que no es el del dashboard").
- **DASHBOARD**: invisible; decide si el A/B mide lo que ve el operador.
- **REPRODUCIR**: leer §4.4 del eje 5 y `frontend/index.html:1056-1060`.
- **CONFIANZA**: CONFIRMADO (leído).
- **GRAVEDAD**: 4. Si el plan A se escribe como banco nuevo, se duplica la decisión (patrón P5 abajo) y se arriesga a
  heredar o no heredar el defecto sin saberlo.

### H302. "Al menos un RUTINA esa noche" no mide paridad de cobertura; la cobertura hay que medirla por pasada

- **SCRIPT:SALIDA**: `01_rutina_como_negativo.py` (246/246 noches con RUTINA por volcán) y `02_rutina_por_pasada.py`
  (VIIRS: 71 a 77 % de nuestras pasadas nocturnas con fila MIROVA; control 0,000).
- **QUÉ PASA**: el scraper registra una fila por pasada y sensor, pero hay fila casi todas las noches de todos los
  volcanes, así que la condición de cobertura del pre-registro S138 §4.4 es casi siempre verdadera. Donde de verdad falta
  la referencia es por pasada: una de cada cuatro pasadas VIIRS nuestras no tiene fila. Una noche cuyo único dato nuestro
  cae en una pasada sin fila MIROVA puede contarse como "negativo con detección" sin que MIROVA la haya mirado.
- **DASHBOARD**: invisible.
- **REPRODUCIR**: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje3/02_rutina_por_pasada.py`.
- **CONFIANZA**: CONFIRMADO en 4 volcanes (Láscar, Llaima, Villarrica, Isluga), ventana 2026-01-10 a 2026-09-13. Que el
  efecto sobre la tasa en negativos sea grande: SOSPECHA (no lo crucé con nuestras detecciones).
- **GRAVEDAD**: 4. La tasa de detección en negativos es la mitad de la motivación del plan (17 % RUTINA).

### H303. Un tercio de las noches RUTINA son noches con ALERTA en otra pasada, y los negativos quedan dominados por los nevados sin actividad publicada

- **SCRIPT:SALIDA**: `01_rutina_como_negativo.py`: 927 de 2.661 noches RUTINA tienen ALERTA (34,8 %); 304 de 1.734
  negativos candidatos tienen FALSO_POSITIVO; por volcán Llaima 246/2 y Copahue 246/5 contra Láscar 236/179.
- **QUÉ PASA**: una noche en que MIROVA publicó ALERTA en una pasada tiene filas RUTINA en las demás. Si el banco toma
  "RUTINA" como etiqueta de noche, un tercio de sus negativos son positivos. Excluidas esas, los negativos se concentran
  en Llaima, Copahue, NdC y Villarrica, que son el estrato donde vive el artefacto A69 y donde MIROVA casi no publica: una
  tasa agregada en negativos mide sobre todo esos cuatro volcanes. Y 304 negativos llevan FALSO_POSITIVO, que según el
  scraper es "MIROVA vio un hotspot fuera del radio" (`docs/AUDIT_INTEGRAL_S81.md:68`, `docs/REAUDITORIA_S52.md:41-42`):
  no es un negativo, es una detección lejana de MIROVA.
- **DASHBOARD**: invisible.
- **REPRODUCIR**: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje3/01_rutina_como_negativo.py`.
- **CONFIANZA**: CONFIRMADO (medido). La unidad de noche es aproximada (S3).
- **GRAVEDAD**: 4. Sin estratificar por volcán (lección S126 en memoria) el 17 % se puede mover sólo por composición.

### H304. El segundo pase condicionado, solo, ya se midió y empeora el artefacto 46,6 %; el brazo más fiel pierde 12 noches

- **ARCHIVO:LÍNEA**: `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md` (tabla de 5 brazos; runs 34173711390 y 34208191011);
  flags de hoy: `ENABLE_SECOND_PASS_CONDITIONED False`, `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK True` (medido con
  `pipeline.profile`).
- **QUÉ PASA**: el plan pone "segundo pase condicionado (D19/D2)" como brazo encima de B22 y del fondo por vecinos. S135
  ya corrió exactamente ese brazo en VIIRS375 (260 noches, 6 volcanes): condicionar o apagar el segundo pase sin tocar
  `keep_peak` produce 47 % más registros de nivel base falso, porque el Test 1 con su píxel único gana la selección; y
  condicionarlo junto con `keep_peak` OFF pierde 12 noches confirmadas (PP 5, Isluga 3, Lastarria 2, Tupungatito 2). S137
  (`EL_AB_DE_D1_YA_ESTABA_CORRIDO.md`) concluyó que ese eje "no contiene la solución" y que el problema está en la
  intersección del Test 1 con la máscara contextual (D23 en el catálogo de hoy). El plan no nombra `keep_peak` ni la
  intersección.
- **DASHBOARD**: el artefacto es un punto rojo summit "0,0 km, 0,03 a 0,17 MW" en los 11 Tier A (AUDIT_S134 §3).
- **REPRODUCIR**: `python experiments/_s135_ab_d1d2/evaluar_ab.py` sobre sus JSON (no re-corrido por mí).
- **CONFIANZA**: CONFIRMADO que el resultado existe y dice eso (leído). Salvedades del propio A/B: sólo VIIRS375, 6 de
  11, predicado propio con cota A93, y parte de sus conteos del régimen previo a #535 (D19 nota S135).
- **GRAVEDAD**: 4. Repetir el brazo C de S135 es una sesión perdida y un veredicto ya conocido.

### H305. El fondo local se probó cuatro veces con cuatro objetos distintos y resultados opuestos; D25 "en los 3 sensores" reabre A19

- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:1088-1127` (D8 kernel 3x3 adoptado S61-S62 por volcán: Villarrica
  31,59 a 2,16×, PP 11,80 a 2,64×); `CLAUDE.md` A19 (Tupungatito empeora 10,37 a 18,46× con kernel-bg);
  `docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md` §15 ("REFUTADO en todo el barrido", S106);
  `docs/AUDIT_S108_AB_MODIS_VEREDICTO.md` (corona fondo local MODIS: curados 5/111 y 23/111, "más records suben que se
  curan", la corona es más fría que el fondo regional en Chaitén y Villarrica); `experiments/_s137/RESULTADO_FONDO_LOCAL.md`
  (3x3 cura A6, n = 9 escenas); `docs/MIROVA_DIVERGENCES.md:2248` (hoy opt-in en 5 volcanes).
- **QUÉ PASA**: físicamente el fondo local resta el entorno inmediato del foco. Donde ese entorno es valle tibio o lago
  (Villarrica) baja la magnitud inflada; donde es glaciar o nieve más fría que el anillo (Tupungatito, corona MODIS de
  Chaitén) la sube. El proyecto ya lo vio en S62 y en S108, y por eso quedó opt-in por volcán, que MISSION.md:82-94 llama
  deuda. Uniformarlo en los 3 sensores es fiel al paper (Eq. 6) pero toca 5 volcanes calibrados a mano y 6 donde la
  única evidencia a favor es una escena. Los cuatro "fondos locales" no son el mismo objeto (3x3 del píxel activo, corona
  del cúmulo, NTI en el Test 1, kernel opt-in): que el de S137 equivalga al de S61: SOSPECHA.
- **DASHBOARD**: magnitud; en nevados glaciares puede multiplicar la barra por 2 o más (A19).
- **REPRODUCIR**: leer los cuatro documentos citados.
- **CONFIANZA**: CONFIRMADO que las cuatro mediciones existen con esos resultados (leído); no re-corridas.
- **GRAVEDAD**: 4 en magnitud. D25 en recall es casi nula en noches de volcán (AUDIT_S138 resumen 2).

### H306. El primer brazo (B22) no toca el número que motiva el plan: el recall MODIS del dashboard lo decide la etiqueta far, medido cinco veces

- **ARCHIVO:LÍNEA**: `docs/AUDIT_S114_PARITY_BY_SENSOR.md:16` (MODIS cráter 17/19, dashboard 3/19); `docs/s132/AB_DISTANCE_CLASS_MODIS.md`
  (flip de etiqueta: TP 436 a 2.332, 9.218 records, 5.192 sin MIROVA); `docs/AUDIT_S134.md:135` (H5: 43 de 48 pasadas
  confirmadas quedan `far` con `pc.vrp_mw > 0`); `experiments/_s136/ETIQUETA_IMPACTO_NETO.md` (4 noches de 946 enteramente
  ocultas); `docs/s133/AB_B22_VEREDICTO.md` (B22: C2 detección 0 pasadas MIROVA perdidas, magnitud ON/OFF 0,107 Láscar y
  0,256 Villarrica, paridad no medible con n = 2).
- **QUÉ PASA**: la motivación "MODIS nocturno detecta 9 de 75 noches ALERTA de Láscar" es, por lo que midieron S114,
  S132, S134 y S136, la etiqueta: el cúmulo del cráter existe y el píxel más caliente de la escena está en el Salar. B22
  quita ruido del primer pase y divide la magnitud por 4 a 10, pero la etiqueta se deriva del `final_hotspot` en MIR
  absoluto, que B22 no reubica. Que B22 no mueva el 9 de 75: SOSPECHA con mecanismo documentado. Además, en la unidad del
  operador MODIS casi no aporta alertas propias: el holdout jun-ago tiene 15 noches MODIS, todas de Láscar (eje 5 H4).
- **DASHBOARD**: con B22 las barras MODIS de Láscar bajarían a un cuarto o un décimo; el conteo summit, probablemente igual.
- **REPRODUCIR**: los cinco documentos citados.
- **CONFIANZA**: CONFIRMADO lo medido antes (leído); SOSPECHA que B22 no mueva el recall del dashboard.
- **GRAVEDAD**: 3. El orden del plan decide el primer mes de trabajo.

### H307. Retirar a la vez la etiqueta summit/far y el tope del path D es la combinación que S121 midió como destape

- **ARCHIVO:LÍNEA**: `docs/AUDIT_S121_D12_AB.md` (ancla MODIS: cura 76 noches de Láscar, destapa path D en los 4 volcanes,
  PCC 117 MW a 2,7 km, 100 % path D); `docs/AUDIT_S108_AB_MODIS_VEREDICTO.md` "Implicaciones 2" (flip bloqueado sin cura de
  magnitud); `PATH_D_ONLY_CAP_MW 5.0` y `ENABLE_FOCAL_CLUSTER_MAGNITUDE True` (medidos hoy).
- **QUÉ PASA**: el paso 5 del plan retira "etiqueta summit/far como filtro, tope path D, etc.". El campo difuso MODIS que
  el dNTI contextual enciende cerca del cráter queda hoy contenido por dos cosas: la etiqueta `far` lo esconde y el tope
  de 5 MW lo acota. S121 quitó una (la etiqueta) y apareció el blob a 117 MW. Quitar las dos es el peor caso medido.
- **DASHBOARD**: barras summit de decenas a cien MW en PCC, Tupungatito y NdC sin alerta de MIROVA.
- **REPRODUCIR**: `experiments/_s121_d12_ab/analyze.py` (no re-corrido).
- **CONFIANZA**: CONFIRMADO lo medido en S121; que el plan los retire juntos depende de su redacción final (S1).
- **GRAVEDAD**: 3 (4 si se retiran sin A/B).

### H308. A54 ("95,4 % de los FP son calor real") no puede leerse como etiqueta de los negativos: tres mediciones posteriores la contradicen y nadie la re-midió

- **ARCHIVO:LÍNEA**: `docs/AUDIT_S86.md:12-20` (clasificación por subagente, 3.687 "FP"); `docs/MISSION.md:26-31` (la codifica
  como hecho); `docs/AUDIT_S104_SYSTEMIC_DIVERGENCE.md:21` (MODIS difuso "~0 % real"); `docs/MIROVA_DIVERGENCES.md:1519-1526`
  (S126: de 2.694 records que la cerca apaga, 36,9 % en el anillo artefacto y 1,5 % corroborados); `docs/AUDIT_S128.md` §3
  (el instrumento TIF no separa: 14,6 % de las ALERTAS con realce).
- **QUÉ PASA**: el plan necesita interpretar "detecta en 17 % de las noches RUTINA". Si A54 vale, eso es mayormente
  calor volcánico real no publicado y bajar esa tasa destruye valor; si vale S104 o S126, es artefacto. S86 lo midió con
  subagentes antes de A69 (S104), del nadir fijo (S102/S103) y de la retirada de la máscara de nube (S126); sus tres
  categorías no se recalcularon con el código de hoy, y S128 mostró que el único instrumento externo disponible (el TIF de
  MIROVA, sólo MIR) no separa las dos cosas. **Hoy no existe instrumento que diga qué fracción de un negativo con
  detección es calor real.**
- **DASHBOARD**: decide si el operador debe ver o no el "nivel base" diario en nevados.
- **REPRODUCIR**: leer los cuatro documentos.
- **CONFIANZA**: CONFIRMADO que las fuentes discrepan y que A54 no tiene re-medición posterior (búsqueda en los documentos
  listados; una re-medición en otro archivo: SOSPECHA de ausencia).
- **GRAVEDAD**: 3. Condiciona el criterio del paso 2: la tasa en negativos no es tasa de falsos positivos.

### H309. El "predicado literal del dashboard" es un blanco móvil: cambió hoy y tiene capas que las auditorías omiten

- **ARCHIVO:LÍNEA**: `frontend/index.html:1043-1064` (`mirovaEqVrp`), `:1166-1188` (`mirovaEqVrpCore`, F5' en V375),
  `:1236` (`isThermalArtifact` = cirrus o campo difuso) aplicado en `:1296` y `:2258`; `:1466-1476` (`isValidDetection`,
  modificado por `b973ccc39` "S139 S138-H", 2026-09-13 14:35 -0300, #642).
- **QUÉ PASA**: lo que el operador ve en el gráfico es `mirovaEqVrp` más la supresión de artefacto térmico más, en V375,
  la magnitud núcleo; lo que ve en contadores es `isValidDetection`, que cambió durante esta misma sesión. S114 midió con
  `mirovaEqVrp` sin `isThermalArtifact`; el eje 5 de S138 con `final_hotspot_dist_km`. Tres "predicados del operador"
  distintos en tres documentos.
- **DASHBOARD**: es el dashboard.
- **REPRODUCIR**: `git log -3 --format='%h %ci %s' -- frontend/index.html`; leer las líneas citadas.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. El plan debe fijar predicado por función y sha, y medir con las dos capas (gráfico y contador).

### H310. Ya existe métrica de precisión contra MIROVA, y hubo al menos siete mediciones de "sobre-detección en RUTINA", todas con unidad o predicado distinto

- **ARCHIVO:LÍNEA**: `frontend/index.html:1246-1293` (S77 F30 P4, `computeMetrics`: FP = record nuestro con `mirovaEqVrp > 0`
  sin alerta del mismo sensor a 60 min); `docs/AUDIT_INTEGRAL_S81.md:60-68` (precisión 0 a 33 %, corregida por tags);
  `docs/AUDIT_S86.md:10` (precisión 0,024); `docs/AUDIT_S112_DASHBOARD_MIROVA.md:15` (RUTINA MODIS 91 a 98 %);
  `docs/AUDIT_S114_PARITY_BY_SENSOR.md:138` (V375 84,3 %) y `:34-36` (834 far a summit en noches RUTINA);
  `docs/AUDIT_S134.md:156` (control ALERTA 82 % contra RUTINA 9 %, sobre el TIF); `docs/MIROVA_DIVERGENCES.md:97-105`
  (S27: 234 FP de MIROVA, 24 nuestros reales).
- **QUÉ PASA**: la pregunta "¿cuánto detectamos cuando MIROVA no publica?" se contestó siete veces entre S27 y S134, con
  pasada-sensor, noche-sensor o noche-volcán, con `record.vrp_mw`, `pc.vrp_mw` o el TIF. Ninguna es comparable con el 17 %
  de hoy sin reconstruir su corpus (A90). Y el script de S112 (`experiments/_s112_audit/parity_by_vol_sensor.py:147-154`)
  toma "noches RUTINA sin alerta" por sensor, que por H303 no excluye ALERTAS de otro sensor.
- **DASHBOARD**: el panel de métricas live ya muestra una precisión por sensor que el operador puede estar leyendo.
- **REPRODUCIR**: leer las fuentes.
- **CONFIANZA**: CONFIRMADO (leído).
- **GRAVEDAD**: 3. Un banco nuevo sin declarar qué reemplaza deja ocho métricas vivas.

### H311. "MISSION l.77" apunta a otra línea, y el principio de "un algoritmo por sensor" tiene hoy dos excepciones que el plan heredaría

- **ARCHIVO:LÍNEA**: `docs/MISSION.md:82-87` (hecho canónico: "NO conmuta de método por volcán ni por régimen"), `:89-94` (nota
  S125: `lbg_global_compatible` en Láscar, NdC, Lastarria); `docs/MIROVA_DIVERGENCES.md:2248` (`local_kernel_bg` en 5
  volcanes).
- **QUÉ PASA**: la cita "l.77" de A85 y del brief ya no está en esa línea (A6 aplicada a la cita). El contenido sigue en
  pie, pero el operacional conmuta por volcán en dos puntos del fondo, que son justo los que D25 toca. La partición
  focal/nevado del plan (paso 4) es legítima para medir; si algún brazo terminara adoptado por estrato sería el trap que
  A85 y S118 excluyeron.
- **DASHBOARD**: invisible.
- **REPRODUCIR**: `grep -n "Hecho canónico\|NO conmuta" docs/MISSION.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### H312. El registro de hipótesis dejó de llevarse: ningún A/B de S119 a S136 está en `HYPOTHESIS_LOG.md`

- **ARCHIVO:LÍNEA**: `docs/HYPOTHESIS_LOG.md` (encabezados: `H_S118_C2_GATES_NO_THEFT` en l. 9, luego S70 a S24, y
  `H_S137_*` en l. 1458-1478; 29 "REFUTADA", 51 "CONFIRMADA").
- **QUÉ PASA**: los A/B de S121 (ancla MODIS), S132 (etiqueta), S133 (B22, área), S135 (D1/D2) y la batería de S136 viven
  en `docs/sNNN/` y `experiments/`, no en el registro. Es la vía por la que S137 casi relanzó el A/B de D1 (A8/A50).
- **DASHBOARD**: invisible.
- **REPRODUCIR**: `grep -n "^## " docs/HYPOTHESIS_LOG.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

---

## 2. Pregunta 1: ¿ya se hizo?

| paso del plan A | ¿se hizo? | resultado | instrumento y sus defectos a la luz de S138 |
|---|---|---|---|
| 1. Banco con positivos y negativos por noche | **Pre-registrado, no corrido** (S138 eje 5 §4) | en espera | predicado `final_hotspot_dist_km`, no el del dashboard (H301); cobertura por noche (H302); negativos sin excluir ALERTAS de otra pasada si se lee literal (H303) |
| 2. Recall y tasa en negativos | **Siete veces** (S27, S81, S86, S112, S114, S128, S134) más la métrica live S77 | precisión 0,024 a 33 %; RUTINA 84 a 98 % | unidades y predicados mezclados (H310); S86 con subagentes pre-A69 (H308) |
| 3. B22 primaria | **Sí, dos veces**: A/B S133 (Láscar 61, Villarrica 70, agosto) y batería S137 (9 escenas) | S133 NO ADOPTAR (magnitud a 0,11 y 0,26; fondo -1,2 K; detección sin pérdida; paridad n = 2). S137: sigma dNTI 3,5 a 4,7× menor, primer pase vacío 80/84 | S133 sin predicado del dashboard y sin paridad; S137 batería con predicado equivocado (2/6 real) |
| 4a. Fondo local | **Cuatro veces** (S61-S62, S106, S108, S137) | adoptado opt-in; refutado; refutado; cura A6 | objetos distintos; S108 y A19 muestran que en glaciar sube la magnitud (H305) |
| 4b. Segundo pase condicionado | **Sí**, A/B S135 de 5 brazos, 260 noches | ningún brazo cumple; condicionar solo empeora 46,6 %; con keep_peak OFF pierde 12 noches | VIIRS375, 6 volcanes, cota A93, régimen pre-#535 parcial (H304) |
| 4c. Recall por noche, cualquier sensor | **Sí**: S136 (946 noches, 94,8 %), S138 verificador (33 a 0), eje 5 §4.2 | la pérdida real en noches de volcán es pequeña | coherente con A94 |
| 4d. Partición focal/nevado | **Existe**, cuatro versiones (S114, S131, `_s135`, `_s136`); S138-G recomienda la de S131 | eje 4 de S138 inventó una quinta y su signo se invirtió | A48 |
| 5a. Etiqueta por cúmulo | **Sí**: S121 (ancla MODIS), S132 (flip MODIS), S136 (impacto neto) | S121 destape path D 117 MW; S132 NO ADOPTAR (C2 mal calibrado en km); S136: 4 noches de 946 | S132 C2 en km fijos (A91) |
| 5b. Tope path D | Existe desde S71 (cap C); S104 midió que sólo atrapa 23 % del difuso MODIS | vigente (5,0 MW) | `docs/AUDIT_S104_SYSTEMIC_DIVERGENCE.md:22-24` |

## 3. Pregunta 2: conclusiones previas que condicionan el plan, y si siguen en pie

| conclusión | dónde | ¿en pie hoy? | cómo condiciona |
|---|---|---|---|
| A54: 95,4 % de los FP son calor real | AUDIT_S86, MISSION:26-31 | **Condicionada**: S104, S126, S128 la contradicen o la hacen inmedible; no re-medida (H308) | la tasa en negativos no es tasa de FP; necesita categoría o se reporta como "no publicada" |
| A68: la sobre-detección es sistémica y en parte cat-b | CLAUDE.md A68 | **Condicionada** por lo mismo; su proxy `t_bg<270K` está contaminado por altitud (la propia A68 lo dice) | idem |
| A82/A83: irreducible a 1 km, no hay discriminante per-record | AUDIT_S114 §3, §6b; AUDIT_S116_FOLLOWUP | **Rebajada** (S124 geometría; S138 C3 vía espectral: barrida con B21 y compuerta) | el A/B de B22 es justo la vía que la rebaja deja abierta; no es licencia para un gate |
| A85: medir el robo antes de cercar | AUDIT_S118 | **En pie** (flags OFF desde S118, verificado S119 y S131 según catálogo) | el paso 5 "retirar parches" debe medir cada retiro con su criterio propio, como S118 |
| MISSION: un algoritmo por sensor | MISSION:82-87 | **En pie como norte, violada en 2 puntos** (H311) | D25 uniforme cumple la misión y rompe calibraciones S61-S62 |
| S113 / S136: no destapar far a summit | CLAUDE.md A81; ETIQUETA_IMPACTO_NETO | **En pie en noches**: beneficio 1 noche de 946 | el 97 % de recall "por cúmulo" es por noche-sensor MODIS; en noche de volcán el aporte es mínimo |
| S121: la etiqueta MODIS está atada a la magnitud path D | AUDIT_S121 | **En pie** (flags OFF, tope 5 MW) | H307 |
| S135: el eje keep_peak / 2º pase no contiene la solución | RESULTADO_FINAL, S137 | **En pie**; S138-4 sigue abierta | H304 |
| S136: la conectiva `min` y el "sigma irrelevante" | S136 | **Refutado el cierre** (S137 circular); la conectiva sigue abierta (S138-2) | B22 mueve la detección sólo bajo `max` o con primer pase ruidoso; el plan no dice qué conectiva |
| S137: la compuerta borra A6 | S137 | **Refutado** (S138: el fondo) | no correr brazo "sólo sin compuerta" |
| S138: D22, D19/D2 y D25 no se pueden A/B-ear por separado | D22 nota S138 | **En pie** | el plan apila; bien, pero necesita brazos de atribución como el eje 5 §4.3 |

## 4. Pregunta 3: por qué no convergemos

### 4.1 Línea de tiempo corta de los grandes giros

| sesión | qué se creyó | qué lo refutó | sesiones que duró |
|---|---|---|---|
| S27 (2026-04-29) | D5 "calibración de magnitud lograda, 1,35×" | S125: hoy ~0,75×, sub-reporte (`MIROVA_DIVERGENCES.md:131-137`) | ~98 |
| S27 | pisos VRP "Removidos" | S124: activos en `store.py` (MISSION:143) | ~97 |
| S27 a S33 | adopción Driver B validada 2,52 a 1,66× | S33: `mirovaEqVrp` sin chequeo de inner; recall 74,2 a 55,6 % (`PROCESS_RULES_S33.md`) | ~6 |
| S52, S81, S104 | RUTINA y FALSO_POSITIVO como juicios de MIROVA | corrección de Nicolás, tres veces (REAUDITORIA_S52, AUDIT_INTEGRAL_S81:68, AUDIT_S104:72-81) | recurrente |
| S62 | "~99 % del universo Tier A en ratio <=3× = clon literal logrado" con kernel-bg | A19 Tupungatito (S62), S108 corona MODIS | inmediato, pero el opt-in quedó |
| S86 (2026-05-28) | 95,4 % de los FP son calor real (entra a MISSION) | S104, S126, S128 (H308) | no cerrado |
| S104 | A69 resuelto por el rediseño Test 1 NTI | S125: `ENABLE_TEST1_NTI_INTEGRAL = False` (CLAUDE.md A69) | ~21 |
| S114 (2026-06-19) | detección MODIS fiel; A82 irreducible; "no quedan gaps" | S124 (geometría), S137 (D21, D22), S138 (C2, C3) | 10 a 24 |
| S115 | GAP #A mislabel, no reabrir | S128 reabre; `CLAUDE.md` lo sostuvo hasta S138 (C1) | 13 a 23 |
| S133 | el anillo de Villarrica es sesgo espacial | S134: efecto del denominador | 1 |
| S133 | B22 invisible en el fondo (predicción -0,0036 K) | el propio A/B: -1,2 K | 0 (pre-registro funcionó) |
| S136 | sigma irrelevante; batería 6/6 | S137 (circular bajo `min`); S138 (2/6 con predicado del operador) | 1 a 2 |
| S137 | la compuerta borra A6; D1 "sin experimento" | S138 (el fondo); el A/B ya estaba corrido | 0 a 1 |

### 4.2 Patrones, cada uno con dos o más casos

**P1. Cierres que heredan una lectura o una auditoría incompleta (A95).** S114 "fiel" sin mirar los pasos previos a los
Tests (S137, S138 C2/C3); S115 GAP #A (S128, S138 C1); S136 cierra tres frentes bajo `min` (S137); S27 pisos y D5
(S124, S125); A69 cerrado con un flag OFF (S125). Duración típica: decenas de sesiones, porque un cierre apaga la
búsqueda.

**P2. El instrumento mide otra cosa que lo que dice.** S33 `mirovaEqVrp` sin inner; S132 `NaN != NaN` y C2 en km fijos;
S134 radio sin acimut y pares TIF contados como alertas; S135 `off_pierde` ignoraba el segundo pase; S136 batería con
predicado propio; S138 eje 5 §4.4 con `final_hotspot_dist_km` (H301); S128 índice TIF MIR absoluto que no separa ni las
ALERTAS de MIROVA.

**P3. Unidad y denominador.** far a summit 2.527 a 9.196 por backfill (A90); 33 noches-sensor a 0 noches de volcán
(S138); ~9.350 records ocultos contra 4 noches (S136); anillo de S133 como denominador (S134); RUTINA por noche que no
excluye ALERTAS de otra pasada (H303, esta sesión).

**P4. Atribución sin simular el paso siguiente ni aislar.** S137 compuerta (el segundo pase rescata); S62 preview
offline de `inner_radius` 1,86× contra 3,64× real (A18); S108 el diseño asumió corona más tibia y era más fría; S21
callee sin trazar caller (A6).

**P5. Olvido y re-descubrimiento del propio repo.** S137 casi relanza el A/B de D1; D20 anotado en S128 y
re-descubierto en S135; semántica de RUTINA corregida tres veces; la misma decisión escrita tres veces con tres números
(eje 6 §1: 16 abiertas, 12 distintas); registro de hipótesis abandonado desde S118 (H312).

**P6. Dos blancos que no coinciden y ninguna regla dice cuál manda.** MISSION declara a la vez clon literal del paper y
paridad con lo que MIROVA publica (MISSION:12-31). Cuando el brazo más fiel pierde paridad no hay desempate: S135 brazo D
(el más fiel) pierde 12 noches; S133 B22 (fiel) "falla" el criterio de magnitud; D18 caja del paper (fiel) no se adopta
"por ausencia de beneficio"; S137 el mejor brazo fiel cumple 5/6 y no se adopta. Y la referencia es escasa justo donde
está el problema: 15 noches MODIS en tres meses, todas de Láscar (eje 5 H4); 1 noche en toda la serie para Llaima
(H303: 246/2).

**P7. Parches acoplados que ningún A/B de un factor puede separar.** S121 (etiqueta atada a magnitud path D); S108 (flip
bloqueado por magnitud); S135 (2º pase solo empeora, con keep_peak pierde); S138 (D22, D19, D25 inseparables). Cada A/B
de un factor sale "ningún brazo cumple" y el frente queda abierto.

## 5. Pregunta 4: riesgos de repetir errores en el plan A

| riesgo | se parece a | mitigación mínima |
|---|---|---|
| Medir con un predicado que no es el que ve el operador | S33, S136, eje 5 §4.4 (P2) | fijar `mirovaEqVrp` + `isThermalArtifact` + `isValidDetection` por sha; test que compare el predicado del script con el JS |
| Negativos contaminados o sin cobertura | H302, H303 | negativo = pasada con fila MIROVA RUTINA del mismo sensor, en noche sin ALERTA ni FALSO_POSITIVO en ningún sensor |
| Agregado que oculta el volcán | A79, S126 (mediana agrupada invirtió un veredicto) | reportar por volcán; decidir por estrato S131 y por volcán; nunca adoptar por estrato |
| Repetir el brazo C de S135 | P5 | incluir `keep_peak` y la intersección contextual (D23) como factores o declarar por qué no |
| Uniformar fondo sin mirar glaciares | A19, S108 | criterio de magnitud por volcán con Tupungatito y Chaitén como casos de falla pre-registrados |
| Retirar parches juntos | S121 | retirar uno por A/B, con el criterio de S118 (medir el daño que el parche evitaba) |
| Criterio pre-registrado en unidades equivocadas | S132 C2 en km, A91 | posición en unidades de `inner_radius`; recall en noches de volcán |
| Subagente que inventa partición o regex | A48, eje 4 S138 | la partición y el mapeo de sensores se importan del repo, no se reescriben |
| Cierre circular | A95, S136 | todo "cerrado" del plan lleva la configuración bajo la que vale (banda, conectiva, fondo, predicado) |
| Preview offline en lugar de reproceso | A18 | los brazos se deciden con reproceso real, no filtrando JSON |

## 6. Pregunta 5: qué debería tener un plan definitivo

1. **Decidir primero el desempate fidelidad contra paridad** (P6), por escrito y con Nicolás: qué pasa cuando el brazo
   más fiel al paper pierde una noche que MIROVA publica. Sin eso cada A/B vuelve a terminar en "ningún brazo cumple".
2. **Heredar, no reescribir**: partir del pre-registro del eje 5 §4 y corregirlo (predicado del dashboard, cobertura por
   pasada, negativos sin FALSO_POSITIVO, factor `keep_peak`). Marcar como superadas las decisiones S134-D1/D2, S136-1,
   S138-4, S137-2, S138-B/C/D/G en una sola tabla.
3. **Diseño factorial pequeño, no una torre**: el acoplamiento (P7) exige brazos de atribución. Mínimo: control; B22;
   B22 + fondo 3x3; B22 + fondo 3x3 + 2º pase condicionado + keep_peak OFF; y el mismo sin B22 en VIIRS.
4. **Criterios de salida escritos antes**: C1 pérdida cero en noches de volcán confirmadas, cualquier sensor, por volcán;
   C2 pasadas negativas limpias con detección, por volcán con bootstrap pareado; C3 magnitud contra MIROVA por volcán con
   casos de falla nombrados (Tupungatito, Chaitén); C4 posición en unidades de `inner_radius`. Qué refuta el
   pre-registro entero.
5. **Controles de instrumento obligatorios** en cada script: brazo idéntico al control que debe dar 0 diferencias; un
   caso sintético que debe cambiar; comparación con máscara explícita, nunca `!=` sobre NaN.
6. **Un verificador con contexto limpio** que reciba sólo rutas y scripts (rindió en S134 y S138).
7. **Registrar cada resultado en `HYPOTHESIS_LOG.md` el mismo día**, con la configuración bajo la que vale.
8. **Qué NO reabrir sin evidencia nueva**: brazo sólo sin compuerta (S138 e.3); 2º pase condicionado solo (S135);
   discriminante geométrico del hotspot robado (S136 e.4); K1 para VIIRS (S137 e.1); gates intra-radio (S118);
   ruido de banda o remuestreo como palanca de detección bajo `min` (S137 e.8, e.9, condicionados por A95); la cerca D13
   como palanca (S126).
9. **Aceptar el techo de la referencia**: con 15 noches MODIS en tres meses y 0 en nevados, MODIS no se puede calibrar
   por paridad; su criterio tiene que ser de fidelidad (conformidad con el paper) más no perder lo que VIIRS375 ya cubre.

---

## VERIFICADO LIMPIO

| qué | comando | resultado |
|---|---|---|
| Flags del perfil operacional que el plan toca | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` | B22 False, `NTI_BT_SANITY_K` 3.0, 2º pase condicionado False, prosa False, contextual filter y keep_peak True, UTM regrid False, K1 retire False, Test 1 NTI False, ancla honesta True (MODIS False), día False, cap path D 5.0, focal magnitude True, nube 0.0, etiqueta MODIS por cúmulo False |
| RUTINA es por pasada y sensor, no por escaneo | `python experiments/_s139_audit/eje3/02_rutina_por_pasada.py` | VIIRS 0,71 a 0,77 real contra 0,000 corrido 6 h, en 4 volcanes |
| Filas RUTINA sin duplicados por (volcán, sensor, hora) y casi sin VRP | `01_rutina_como_negativo.py` | 0 duplicadas; 17 de 35.018 con VRP > 0 |
| Mapeo de sensor del scraper (MODIS, VIIRS = M-band, VIIRS375) coincide con A48 | `01_rutina_como_negativo.py` (conteo por Sensor) y pareo ALERTA a pasada 204/206 Isluga V375, 40/40 V750 | sano |
| `mirovaEqVrp` sigue exigiendo summit, inner y tope 50.000 | `sed -n 1043,1064p frontend/index.html` | sano (igual a lo que S114 citó) |
| La partición focal/nevado de S131 existe donde el bloque S139 dice | `sed -n 30,50p scripts/build_c2ab_windows.py` | l. 41-42, 5 focales y 6 nevados |
| El A/B de D1/D2, el de B22 y el de etiqueta MODIS existen con sus veredictos escritos | lectura de `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md`, `docs/s133/AB_B22_VEREDICTO.md`, `docs/s132/AB_DISTANCE_CLASS_MODIS.md` | sanos; no volver a buscarlos |
| Árbol de trabajo sin cambios ajenos a este eje | `git status --short` | sólo `experiments/_s139_audit/` sin trackear |

No re-corrí ningún A/B ni reprocesé granules; todo lo que sale de un documento anterior está marcado como leído, no medido.
