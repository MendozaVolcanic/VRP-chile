# S139 eje 4: revisión adversarial del plan A y de sus alternativas

Auditor: agente eje 4, 2026-09-13. Read-only sobre el repo (HEAD `b16bb8fab`, `main`). Sólo se crearon
este informe y los scripts de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje4\`
(salidas en `out\`). Nada de lo que sigue viene de memoria: cada número sale de uno de los tres scripts
de esta sesión y cada cita de código de una lectura hecha hoy.

## Resumen en una pantalla

El plan A ataca bien la fidelidad literal de MODIS, pero **no es el mejor orden** por cuatro razones
medidas:

1. **Mezcla unidades en su motivación.** El "9 de 75" es noche-sensor MODIS de Láscar; el "432 de 2.513"
   es la suma de los 11 volcanes (47 % de esos 432 es Puyehue-Cordón Caulle). En la unidad que S138-D
   fijó para el operador (noche de volcán, cualquier sensor) el recall ya es 886 de 891, y la brecha de
   paridad real está del otro lado: **publicamos detección summit en 1.400 de 1.557 noches en que MIROVA
   calló (90 %)**, y 1.263 de ellas las carga VIIRS 375, no MODIS (278).
2. **En MODIS el predicado del dashboard mide sobre todo la etiqueta, no la detección.** Hay cúmulo
   dentro del radio interno en 80 de 80 noches positivas y en 97 % de las negativas; la magnitud del
   cúmulo no separa positivos de negativos (AUC 0,38 focal, 0,51 nevado). Un brazo "banda 22" evaluado
   con ese predicado va a medir cuánto cambia `final_hotspot`, no cuánto cambia la detección.
3. **El segundo pase condicionado es un no-op en MODIS con banda 21**: el primer pase dispara en el 100 %
   de las noches (positivas y negativas). D19 y D21 están acoplados; ablacionarlos por separado en MODIS
   no informa. En VIIRS 750 el acople es el inverso y el riesgo de recall es real.
4. **El poder MODIS es de un volcán y se acaba en junio**: 80 noches positivas propias en la ventana, 74 de
   Láscar; Láscar tiene 2 en julio y 1 en agosto. Un holdout temporal MODIS tiene 3 positivos.

Recomendación: **plan B+C** (sección 7): primero arreglar el instrumento de evaluación sin tocar
`pipeline/` (una sesión), después un brazo "literal completo por sensor" contra la base con ablaciones
"todo menos uno", en los 3 sensores, con criterio decisorio en noches negativas y pérdida cero en
positivas.

---

## 0. Mediciones y las dos preguntas del instrumento

### M1. `01_linea_base_noches.py` (salida `out/linea_base_noches.json`)
Línea base por noche local (fecha de `datetime_utc - 12 h`), 11 Tier A, 3 sensores, con el predicado del
dashboard portado de `frontend/index.html:1043-1065` (`mirovaEqVrp`) y `:1480-1488` (`isSummitDetection`)
y, lado a lado, el predicado "por cúmulo" (`primary_cluster.vrp_mw > 0` y centroide dentro de
`inner_radius_km`). Referencia CONS unión OCR del snapshot (`pipeline/mirova_csv_loader.py:123`).
Negativo = noche con fila RUTINA de MIROVA para el volcán y sin ALERTA en ningún sensor.
- **Ventana**: 2026-01-10 19:06 a 2026-09-07 13:30 UTC (la del CSV). Denominador: noches en que
  tenemos al menos una pasada del sensor (paridad de cobertura; sin pasada = SIN DATO, no pérdida).
- **P1** (¿vería un predicado roto?): sí; las dos variantes difieren hasta 9 contra 74 en la misma
  población, así que un predicado que lo marcara todo summit se vería.
- **P2** (¿instrumento muerto?): control de fechas barajadas (noches ALERTA desplazadas 183 días, fuera
  de noches ALERTA). Resultado: en noche de volcán focal el "recall" de las fechas barajadas es 63 de 79
  (80 %) contra 690 de 690 en las reales. **El instrumento distingue poco**: la tasa de publicación
  basal es tan alta que el recall en noche de volcán casi no tiene información (ver H401).
- **Control positivo**: el predicado por cúmulo sube MODIS de 9 a 74 en Láscar; la medición lo ve.
- **Supuesto declarado**: RUTINA es etiqueta de nuestro scraper (Mirova-v1), no de MIROVA; otro eje
  revisa su semántica. Si RUTINA no significa "MIROVA miró y no vio", los negativos están sesgados.

### M2. `02_primer_pase_discrimina.py` (salida `out/primer_pase_discrimina.json`)
Fracción de noches positivas y negativas en que el primer pase de los Tests 2 y 3 dispara en la escena
(`diag_n_first_pass_pixels > 0`), en el radio interno (`diag_n_first_pass_summit > 0`), y en que el
segundo pase recaptura; AUC de la magnitud máxima del cúmulo por noche.
- **P1**: si el primer pase estuviera muerto daría 0 en los dos grupos; no da 0 (MODIS 100 %).
- **P2**: **falló para `diag_n_first_pass_summit` en VIIRS**: el campo sólo lo escribe
  `pipeline/process_modis.py:1531`; en VIIRS no existe la clave, y mi script lo leyó como 0. Esos ceros
  son SIN DATO y no se usan (H405). La fracción en escena usa `diag_n_first_pass_pixels`, que sí existe
  en los 3 sensores; los records sin esa clave se contaron aparte como SIN DATO (0 en la ventana).
- Ventana y unidad: las de M1.

### M3. `03_denominador_y_poder.py` (salida `out/denominador_y_poder.json`)
Reproduce la motivación del plan con tres definiciones de negativo y la serie mensual de ALERTAS MODIS
por volcán. P1: una definición que no reproduzca el 432 queda descartada como la del orquestador; P2:
volcanes con 0 positivos se reportan como SIN DATO de positivos, no como recall 0.

---

## 1. Hallazgos, por gravedad

### H401. La motivación del plan mezcla unidades; en la unidad del operador la brecha está en las noches silenciosas y la carga VIIRS 375, no MODIS
- SCRIPT:SALIDA: `01_linea_base_noches.py` → `out/linea_base_noches.json` (claves `totales`);
  `03_denominador_y_poder.py` → `out/denominador_y_poder.json` (`POOL_11`, `Lascar`).
- QUÉ PASA: físicamente, lo que MIROVA "calla" en una noche no es ausencia de calor (A54: gran parte es
  señal sub-umbral real), pero es lo que el clon debe reproducir. En noche de volcán con cualquier
  sensor publicamos detección summit en **1.400 de 1.557 noches negativas (90 %)**: VIIRS 375 1.263,
  VIIRS 750 822, MODIS 274 (conteos no excluyentes; focal 378 de 423, nevado 1.022 de 1.134). El recall
  en esa unidad es 886 de 891 (99,4 %; las 5 que faltan son Nevados de Chillán y Tupungatito). La
  motivación del plan usa otras unidades: "9 de 75" es noche-sensor MODIS de Láscar (medido: 9 de 74), y
  "432 de 2.513" **no es de Láscar**: se reproduce el numerador exacto sumando los 11 volcanes con
  negativo = "noche sin ALERTA MODIS" (432 de 2.386 en mi ventana; el denominador del orquestador
  difiere, probablemente por ventana), de los cuales 203 son de Puyehue-Cordón Caulle. Con la
  definición de negativo de S138 (sin alerta en ningún sensor) MODIS da 278 de 1.580 (17,6 %).
- CÓMO SE VE EN EL DASHBOARD: el operador ve detecciones summit casi todas las noches en casi todos los
  volcanes, y MIROVA no. El plan A empieza por el sensor que menos aporta a esa diferencia.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje4/01_linea_base_noches.py`
  y `... 03_denominador_y_poder.py`.
- CONFIANZA: CONFIRMADO en los conteos; SOSPECHA sobre el denominador exacto del orquestador (2.513).
- GRAVEDAD: 4. Puede torcer la prioridad entera del frente de paridad y hacer que se declare
  "definitivo" un plan que no mueve lo que el operador ve.

### H402. En MODIS el predicado del dashboard mide la etiqueta `far`/`summit`, no la detección; la magnitud del cúmulo no discrimina
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:294-314` (`derivar_distance_class`: sale de
  `final_hotspot_dist_km` salvo que `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`, hoy `False`),
  `:1314-1316`; `frontend/index.html:1057` (cúmulo con clase no summit vale 0). SCRIPT: M1 y M2.
- QUÉ PASA: a 1 km el píxel más brillante en MIR absoluta de la escena suele estar en el Salar o el valle
  (A69), y la etiqueta sale de ahí. Medido: cúmulo dentro del radio interno en **80 de 80** noches
  positivas MODIS propias y en **1.512 de 1.556** negativas (97 %); con el predicado del dashboard 10
  de 80 y 274 de 1.556. La magnitud del cúmulo no separa: AUC 0,38 focal (invertida) y 0,51 nevado,
  contra 0,81 y 0,82 en VIIRS 375. Es decir, con banda 21 MODIS no tiene capacidad de discriminar noche
  alerta de noche silenciosa, y el predicado del dashboard filtra por un criterio (la etiqueta) que
  tampoco discrimina bien (dash en positivos 12,5 %, en negativos 17,6 %).
- CÓMO SE VE EN EL DASHBOARD: MODIS aparece "casi siempre far" en Láscar; cualquier cambio que mueva el
  píxel máximo mueve el conteo aunque la detección no cambie.
- CÓMO REPRODUCIRLO: M1, fila `Lascar MODIS`: `74 9 74`; M2, claves `AUC_maxvrp_*_MODIS`.
- CONFIANZA: CONFIRMADO. SOSPECHA: que la banda 22 mueva `final_hotspot` (no lo reprocesé).
- GRAVEDAD: 4. Un A/B de banda 22 leído sólo con el predicado del dashboard puede adoptar o rechazar
  por el efecto sobre la etiqueta. Hay que reportar siempre los dos predicados.

### H403. El segundo pase condicionado (D19) no hace nada en MODIS mientras la banda 21 mande, y en VIIRS 750 puede quitar recall: D19 y D21 no se ordenan "uno encima del otro"
- ARCHIVO:LÍNEA: paper p. 7 renderizado (`out/sp426_p7.png`): *"The last step is applied only if one or
  more pixels have been detected by the previous tests"*; flag `ENABLE_SECOND_PASS_CONDITIONED=False`
  cableado en `process_modis.py:796,813,936`, `process_viirs.py:1157,1172,1301`,
  `process_viirs_mod.py:759`. SCRIPT: M2.
- QUÉ PASA: con banda 21 la textura de ganancia baja deja siempre algún píxel sobre el piso, así que el
  primer pase dispara en **685 de 685** noches positivas focales, 422 de 422 negativas focales, 201 de
  201 y 1.134 de 1.134 nevadas. Condicionar el segundo pase a "que haya activos" no cambia ninguna
  noche MODIS. Sólo muerde si antes la banda 22 vacía el primer pase (S137: 80 de 84 escenas vacías).
  En VIIRS 750 pasa lo contrario: en el nevado el primer pase dispara en 24 de 201 noches positivas y el
  segundo pase recaptura en 153; condicionar puede apagar gran parte del recall noche-sensor V750
  (SOSPECHA: otros caminos, Test 1, pueden sostener el cúmulo; no reprocesado).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; si se adopta D19 sola en VIIRS 750, desaparecerían
  detecciones V750 nevadas (en noche de volcán, S138 midió que VIIRS 375 las cubre).
- CÓMO REPRODUCIRLO: `python experiments/_s139_audit/eje4/02_primer_pase_discrimina.py`, claves
  `*_MODIS_*` y `nevado_VIIRS750_pos`.
- CONFIANZA: CONFIRMADO para MODIS; SOSPECHA para el tamaño de la pérdida V750.
- GRAVEDAD: 4. Orden equivocado = un brazo "D19 MODIS" que sale nulo y se cierra por error (A95).

### H404. El poder estadístico MODIS es de un volcán y se agota en junio de 2026; un holdout temporal MODIS no existe
- SCRIPT:SALIDA: M3, `Lascar.modis_alerta_por_mes` = ene 2, feb 11, mar 23, abr 16, may 9, jun 12,
  **jul 2, ago 1**; `POOL_11.pos_modis_ventana` = 80 (Láscar 74, Chaitén 3, Villarrica 2, NdC 1).
- QUÉ PASA: los positivos MODIS propios son casi todos de un volcán desértico focal de cráter de roca
  caliente, el caso en que la banda 21 y la 22 menos difieren en física (no hay nieve ni valle tibio).
  Todo criterio MODIS "por su propio sensor" queda sobreajustado a Láscar, y un holdout jul a sep tiene
  3 positivos. Con 80 positivos, una pérdida de 1 noche es 1,25 %: un criterio de "pérdida cero" es
  determinista pero no dice nada del nevado, donde el plan espera el daño (A6).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s139_audit/eje4/03_denominador_y_poder.py`.
- CONFIANZA: CONFIRMADO (coincide con el H4 de S138 eje 5, medido aquí de forma independiente).
- GRAVEDAD: 4.

### H405. `diag_n_first_pass_summit` no existe en VIIRS y falta en parte de MODIS: cualquier criterio que lo lea confunde SIN DATO con cero
- ARCHIVO:LÍNEA: único escritor `pipeline/process_modis.py:1531`; en `process_viirs.py` y
  `process_viirs_mod.py` no aparece (grep). Medido en Láscar desde 2026-01-10: 843 records V375 y 836
  V750 sin la clave; 224 MODIS sin la clave frente a ~200 con ella.
- QUÉ PASA: el ancla A73 ("usar el primer pase dentro del radio") y cualquier estratificación del plan
  por "detección genuina de primer pase" no se pueden calcular en VIIRS. Mi propio script M2 cayó en la
  trampa (`fps or 0`) y dio 0 en todas las noches VIIRS, positivas incluidas: dato inválido, descartado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -c "import json;from collections import Counter;r=json.load(open('data/mirova_equivalent/Lascar.json'))['records'];print(Counter((x['sensor'][:4],'diag_n_first_pass_summit' in x) for x in r if x['datetime_utc']>='2026-01-10'))"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (tuerce la evaluación, no la alerta).

### H406. "Quitar la compuerta" no tiene flag propio: la constante que la controla es compartida con el camino del NTI absoluto
- ARCHIVO:LÍNEA: `NTI_BT_SANITY_K` en `process_modis.py:665` (camino NTI > K1 y BT > fondo + 3),
  `:693,701,869` (Tests 2 y 3), `:821` (restricción del camino ETI); `process_viirs.py:976,998,1038,
  1046,1178,1240`; `process_viirs_mod.py:624,643,677,685,780`. En `pipeline/profile.py` no hay flag de
  compuerta ni de fondo por vecinos (grep sin resultados).
- QUÉ PASA: un brazo que baje la constante a menos infinito para imitar "sin compuerta en Tests 2 y 3"
  también abre el camino del NTI absoluto (D23) y la restricción ETI: mezclaría tres divergencias en un
  solo brazo sin poder atribuir. Las dos correcciones de la batería S137 (compuerta y fondo local) viven
  sólo en la batería.
- CÓMO SE VE EN EL DASHBOARD: invisible hasta que se implemente.
- CÓMO REPRODUCIRLO: `grep -n NTI_BT_SANITY_K pipeline/process_*.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Obliga a código nuevo con A45 antes de cualquier A/B, y a separar los usos.

### H407. VIIRS no tiene fuente literal para las palancas del plan: SP426.5 es un paper MODIS
- ARCHIVO:LÍNEA: `sp426.5.pdf` p. 3 renderizada: "The MIROVA system is based on MODIS Level 1B data";
  `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:141`: los umbrales VIIRS "que Coppola 2016/Campus 2022 no
  publican". Umbrales actuales: los mismos del perfil para los 3 sensores (banner del perfil).
- QUÉ PASA: para VIIRS, "quitar la compuerta" o "fondo por vecinos" es literal sólo por analogía con
  MODIS. La pregunta 1 de MISSION exige cita verbatim de que MIROVA NRT lo aplica **para ese sensor**. No
  leí Campus 2022 en esta sesión: puede que lo diga. Y la divergencia VIIRS con evidencia medida propia
  es geométrica (D17: ratio V375 cae de 0,74 a nadir a 0,25 en oblicuo, catálogo l. 1894-1920), que el
  plan no incluye como brazo.
- CÓMO SE VE EN EL DASHBOARD: la magnitud VIIRS oblicua sale a un cuarto de MIROVA.
- CÓMO REPRODUCIRLO: renderizar p. 3 (`out/sp426_p3.png`), leer `BIBLIOGRAPHY_SYNTHESIS.md:96-141`.
- CONFIANZA: CONFIRMADO que SP426.5 es MODIS; SOSPECHA sobre lo que dicen Campus 2022 y Coppola 2022.
- GRAVEDAD: 3.

### H408. El plan retira parches "después", pero los parches vivos cambian qué cúmulo y qué etiqueta se publican: medir brazos con ellos puestos contamina la atribución
- ARCHIVO:LÍNEA: flags leídos con `VRP_PROFILE=mirova_equivalent`: `PATH_D_ONLY_CAP_MW=5.0` con
  `PATH_D_ONLY_CAP_TBG_MAX_K=270.0` (`process_modis.py:998-1004,1064,1158`; ejemplo real: record Láscar
  MODIS_AQUA 2026-09-13 08:35 con `vrp_mw=5.0`), `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True` (D19),
  `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER=True` (Regla D, MISSION), `ENABLE_TEST1_LBG_GLOBAL=True`
  (conmuta por volcán), `ENABLE_LOCAL_KERNEL_BG=True` opt-in por volcán (`process_modis.py:1041`),
  `delta_L` recortado a 0 (`:1056`).
- QUÉ PASA: el tope de 5 MW y el recorte a 0 actúan justo en las cumbres frías donde la banda 22 y el
  fondo por vecinos cambian la magnitud; el opt-in por volcán hace que "fondo por vecinos" ya esté en 5
  de 11 volcanes en la base, con lo que el efecto medido del brazo se diluye en esos 5.
- CÓMO SE VE EN EL DASHBOARD: magnitudes MODIS clavadas en 5,0 MW; cúmulos summit en 0,0 MW.
- CÓMO REPRODUCIRLO: comando de flags de la sección 0; `data/mirova_equivalent/Lascar.json`, último
  record MODIS.
- CONFIANZA: CONFIRMADO en el código y los flags; SOSPECHA sobre el tamaño de la contaminación.
- GRAVEDAD: 3.

### H409. Banda 22 y fondo por vecinos: literales confirmados en el PDF, pero el paper los aplica sobre la grilla remuestreada sin bow tie
- ARCHIVO:LÍNEA: p. 3 renderizada: "using the L21 or L22 radiance, depending on band 22 saturation (or
  not), respectively" y "remove the bow-tie effect", "cropped and resampled (into an equally spaced 1 km
  grid)"; p. 8 renderizada, ecuación 6: "L4bk is estimated from the arithmetic mean of all the pixels
  surrounding the active one (or around the active cluster)". Código: `merge_mir_bands`
  (`process_modis.py:317-334`) con `b22_primary=True` coincide; fondo `np.median` del anillo
  (`detection_context.py:1064`); `ENABLE_UTM_REGRID=False`.
- QUÉ PASA: las dos palancas del plan son literales. Pero la media de 8 vecinos sobre píxeles nativos con
  solape de barridos repite el píxel caliente en sus vecinos a ángulos altos, lo que baja el dNTI del
  foco; eso es candidato explícito (S137, `RESULTADO_BATERIA_B22.md` "Lo que queda abierto" 1) a por qué
  el cráter de Villarrica A6 queda bajo el piso con banda 22. Banda 22 sin D17/D28 es literal en la
  banda y no en la geometría sobre la que el paper midió sus umbrales.
- Además, p. 8: "a visual inspection of the images allows ... cloud-affected data to be discarded (a
  posteriori)". El paper admite limpieza manual; nuestro canal NRT no la tiene (feedback S135).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -c "import fitz;d=fitz.open('documentacion/sp426.5.pdf');[d[p-1].get_pixmap(dpi=150).save(f'p{p}.png') for p in (3,7,8)]"` y mirar las imágenes.
- CONFIANZA: CONFIRMADO en la lectura; SOSPECHA sobre el efecto del bow tie en A6.
- GRAVEDAD: 2.

### H410. Hallazgo lateral: `isValidDetection` ya cambió en S139 (PR #642)
- ARCHIVO:LÍNEA: `frontend/index.html:1466-1478`, commit `b973ccc39`.
- QUÉ PASA: el predicado del dashboard que el plan congela como métrica ya no es el de S138; cualquier
  batería o línea base calculada antes del commit usa otra definición. Mi M1 no usa `isValidDetection`
  (usa `isSummitDetection` y `mirovaEqVrp`, sin cambios), pero el pre-registro debe fijar el sha.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

---

## 2. Las palancas literales, frente a frente (sólo lo que leí hoy)

| palanca | en el paper | en el código hoy | sensor | acople medido o leído |
|---|---|---|---|---|
| D21 banda 22 | p. 3, sí | flag OFF | MODIS | vacía el primer pase (S137); sin ella D19 es no-op (H403) |
| D22 compuerta BT | p. 7 no la tiene | constante compartida con camino NTI (H406) | 3 | S138: no es lo que pierde A6 |
| D25 fondo media de vecinos | p. 8, sí | mediana del anillo, opt-in 5 volcanes | 3 | devuelve magnitud en A6 (S137) |
| D19/D2 segundo pase condicionado | p. 7, sí | flag OFF | 3 | no-op MODIS B21; riesgo V750 (H403) |
| D17 + D28 remuestreo y bow tie | p. 3, sí, antes de todo | `ENABLE_UTM_REGRID=False` | 3 | gradiente cenital VIIRS medido (catálogo D17) |
| D24 saturados conservados | p. 3, sí | eliminados | MODIS | sólo paroxismos |
| D23 Test 1 como detección | p. 6 | no es camino | 3 | eventos energéticos |
| Etiqueta summit/far por `final_hotspot` | no está en el paper | activo; flag desde cúmulo existe | MODIS | domina el predicado MODIS (H402) |
| Tope 5 MW, recorte a 0, keep_peak, Regla D, lbg global por volcán | no están | activos | 3 | contaminan magnitud y etiqueta (H408) |

Lectura geológica: el paper es una cadena en orden fijo (geometría, banda, índices, pruebas, segundo pase,
fondo). Nuestras divergencias están repartidas en toda la cadena, y varias se tapan entre sí: la textura
de la banda 21 esconde que el segundo pase no está condicionado, el segundo pase esconde la compuerta, la
mediana del anillo esconde que el cráter pasó las pruebas. Corregir de a una desde el medio de la cadena
produce brazos que salen nulos por una razón que está en otro eslabón.

## 3. Las 3 preguntas de MISSION por brazo

| brazo | P1 papers (cita verbatim leída) | P2 divergencia catalogada | P3 interna | veredicto |
|---|---|---|---|---|
| Banda 22 MODIS | SÍ, p. 3 | D21 | | puede |
| Sin compuerta en Tests 2 y 3 | SÍ por ausencia, p. 7 (fórmula sin BT) | D22 | | puede, pero exige flag nuevo (H406) |
| Fondo media de vecinos uniforme | SÍ, p. 8 ec. 6 | D25 | | puede; opt-in por volcán viola "uniforme por sensor" |
| Segundo pase condicionado | SÍ, p. 7 | D19/D2 | | puede |
| Las mismas en VIIRS | NO verificado para VIIRS (H407) | D22, D25, D19 | | puede sólo por P2; buscar cita VIIRS |
| Remuestreo + bow tie | SÍ, p. 3 | D17, D28 | | puede; cirugía de núcleo |
| Etiqueta desde cúmulo | NO | D12/D13 relacionadas | alineación de display discutible | gris; A94 dice que rinde poco en noches |
| Banco de prueba, predicados, persistir diags | | | SÍ | puede y no toca `pipeline/` salvo diags |

## 4. Diseño experimental: lo que el plan A no cubre y criterios propuestos

1. **Unidad**: primaria noche de volcán con cualquier sensor (S138-D); **pero el recall en esa unidad
   está saturado** (886 de 891, y 80 % en fechas barajadas). El criterio decisorio de mejora tiene que
   estar en las noches negativas; el recall sólo como restricción de pérdida cero.
2. **Dos predicados siempre**: dashboard y cúmulo (H402). Un brazo que cambia uno sin el otro está
   moviendo la etiqueta.
3. **Holdout**: la batería del Apéndice A y todo 2026-01 a 2026-05 ya se miraron; propongo desarrollo
   2026-01-10 a 2026-05-31 y prueba 2026-06-01 a 2026-09-07 (el mismo universo que S138 eje 5 §4.2,
   con 316 noches positivas, 64 nevadas), congelado con el sha del frontend (H410) y del snapshot CSV.
   Holdout por volcán no es necesario para sobreajuste de parámetros (ningún brazo ajusta números),
   **sí** para la elección de brazos: reportar por volcán y exigir que ningún volcán empeore.
4. **Criterios decisorios pre-registrados** (propuesta):
   - C1 pérdida cero: noches de volcán confirmadas por MIROVA en la ventana de prueba que la base
     publica y el brazo no. Umbral 0 por estrato focal/nevado (S131, `scripts/build_c2ab_windows.py:41-42`).
   - C2 sobre-publicación: noches negativas publicadas, pareadas por noche, IC 95 % bootstrap (5.000,
     semilla 42). Adoptar si el IC de la diferencia excluye 0 a favor del brazo en al menos un estrato y no
     incluye aumento en el otro. Poder calculado **antes** sobre la base: con 1.557 negativas y 90 % de
     publicación, el IC de la tasa es estrecho, así que el efecto mínimo detectable es chico.
   - C3 por sensor, informativo: los mismos dos números por noche-sensor, para no esconder que VIIRS 750
     pierde (H403).
   - C4 magnitud: ratio nuestro/MIROVA por bin de ángulo cenital (D17), no mediana global.
   - C5 batería del Apéndice A con el predicado del dashboard, sólo como control de cordura, nunca como
     decisor (S138 eje 5 H1-H3).
5. **Anti S33**: la métrica la calcula un script escrito y commiteado antes de abrir los brazos, con un
   control positivo (un brazo sintético que fuerza todo summit debe subir C2) y un control negativo
   (base contra base debe dar diferencia 0).

## 5. Alternativa A (el plan propuesto)
Ventajas: empieza por la palanca con flag y medición previa; bajo costo inicial. Costos: los brazos se
agregan de a uno sobre una cadena acoplada (H403, H409), el poder MODIS es de Láscar (H404), el predicado
mide la etiqueta (H402), y no toca lo que domina la brecha en el dashboard (H401). Riesgo principal:
brazos nulos cerrados por error, repitiendo A95.

## 6. Alternativa B: primero el instrumento, sin tocar `pipeline/`
Contenido: (a) congelar el banco con sha de frontend y snapshot; (b) resolver la semántica de RUTINA con
el eje que la audita; (c) calcular la línea base en las dos unidades y los dos predicados (este informe
ya tiene el esqueleto en `01_linea_base_noches.py`); (d) persistir en los 3 sensores los diagnósticos
que faltan (`diag_n_first_pass_summit`, etapa que originó el cúmulo), lo único que toca `pipeline/` y es
sólo escritura de campos; (e) clasificar una muestra de las 1.400 noches negativas publicadas en
categoría A54 (real sub-umbral contra artefacto) para saber si C2 debe bajar o no.
Ventajas: barato (una sesión), decide si la brecha es de detección o de referencia antes de gastar
reprocesos. Costos: no mejora nada visible. Riesgo: que se convierta en otra auditoría sin fin (A51).

## 7. Alternativa C: brazo literal completo por sensor y ablaciones "todo menos uno"
Contenido: para cada sensor, un brazo con todas las palancas literales de la tabla §2 que tienen
cita (MODIS: banda 22, sin compuerta en Tests 2 y 3, fondo media de vecinos uniforme y sin recorte,
segundo pase condicionado, saturados conservados; parches no literales apagados: tope 5 MW, keep_peak,
Regla D, lbg global por volcán, kernel opt-in). Comparado contra la base con C1 a C5; luego k brazos
"literal menos una palanca" para atribuir. D17+D28 como segundo escalón (cirugía de núcleo) o en brazo
propio si el primero no cierra la magnitud oblicua.
Ventajas: captura los acoples (una palanca que sólo funciona con otra aparece en la ablación), el
número de brazos es 1 + k y no 2^k, y responde directo a "¿el clon literal reproduce a MIROVA?".
Costos: exige crear flags para compuerta y fondo (H406) y apagar parches, todo con A45; más reprocesos.
Riesgo: si el literal completo empeora, la ablación dice qué eslabón; si el literal completo mejora
pero pierde una noche, C1 lo bloquea igual que en A.

## 8. Recomendación

**B y después C**, no A. B primero porque dos de mis propias mediciones cambiaron de sentido por el
instrumento (el campo muerto de H405 y el recall saturado de H401), y porque el plan A iba a decidir con
un predicado que en MODIS mide la etiqueta. C después porque la cadena del paper está acoplada: medí que
D19 es no-op sin D21 en MODIS y que D19 tiene el efecto inverso en VIIRS 750; agregar de a una produce
nulos engañosos. Si hay que elegir un solo brazo MODIS antes de C, que sea **banda 22 + segundo pase
condicionado juntos** (su acople es el que está medido), evaluado con los dos predicados y en noche de
volcán, no banda 22 sola.

Supuestos que tomé sin poder consultarlos: RUTINA equivale a "MIROVA miró y no vio"; la noche local es
fecha UTC menos 12 h; el umbral de publicación del dashboard es `isSummitDetection` y `mirovaEqVrp > 0`
con el `inner_radius_km` del yaml.

---

## VERIFICADO LIMPIO

- **Banda 22 como la entiende el código es la del paper**: `merge_mir_bands` con `b22_primary=True`
  usa L22 salvo NaN por saturación (`process_modis.py:317-334`) y el paper p. 3 renderizado dice lo
  mismo. No hay que volver a verificar la lectura del PDF para D21.
- **El segundo pase condicionado está en el paper** (p. 7 renderizada, "applied only if one or more
  pixels have been detected") y el flag está cableado en los 3 procesadores
  (`grep -rn ENABLE_SECOND_PASS_CONDITIONED pipeline/*.py`: 7 usos en 3 archivos).
- **Fondo de la ecuación 6 = media aritmética de los vecinos del activo o del cúmulo** (p. 8
  renderizada). No es necesario releerlo.
- **La conectiva de Tests 2 y 3** en la imagen de p. 7: "or" dentro de cada test, "and" entre tests;
  mu y sigma "of all the suitable pixels within the image". Coincide con el docstring de
  `detection_context.py:803-840`.
- **El "9 de 75" de Láscar MODIS** se reproduce (9 de 74 en noche-sensor, ventana del CSV) y el 432
  también (suma de 11 volcanes, negativo = sin ALERTA MODIS). Comandos: M1 y M3.
- **Flags del perfil operacional** leídos con
  `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` (listado completo en la
  sesión): `ENABLE_MODIS_B22_PRIMARY False`, `ENABLE_SECOND_PASS_CONDITIONED False`,
  `ENABLE_UTM_REGRID False`, `ENABLE_TESTS_23_PROSE_BRANCH False`, `NTI_BT_SANITY_K 3.0`,
  `PATH_D_ONLY_CAP_MW 5.0`.
- **`isSummitDetection` y `mirovaEqVrp`** sin cambios respecto de lo que usa M1
  (`frontend/index.html:1043-1065`, `:1480-1488`); sólo cambió `isValidDetection` (H410).
