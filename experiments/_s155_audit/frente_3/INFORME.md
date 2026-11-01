# Frente 3 (S155): los instrumentos con que el proyecto se mide a sí mismo, después de K

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f3`, detached en `cb90031a` (origin/main del 2026-10-19).
Hora del servidor al empezar: `Mon, 19 Oct 2026 10:41:55 GMT` (`gh api -i`). Nada del repositorio se modificó
(`git status --porcelain` = sólo `?? experiments/_s155_audit/`). Todos los scripts y salidas están en
`D:\vrp-trabajo\worktrees\s155-audit-f3\experiments\_s155_audit\frente_3\`; los commits viejos extraídos con
`git show`, en `D:\vrp-trabajo\temporales\frente_3\`. Los flags se leyeron de `pipeline.profile`.

## 0. El sustrato: dónde está la frontera C0 / K en los datos

`regimen_por_ventana.py` clasifica cada record por `regimen.codigo_sha` (K si `34cea39e` es ancestro, con
`git merge-base --is-ancestor`).

- P1: si el corte estuviera mal, el control positivo fallaría. Control positivo: los 2.609 records con
  `processed_utc` posterior al merge salen 100 % K.
- P2: un sha desconocido o un record sin marca van a su propio estrato, nunca a C0.
- Resultado: los 11 sha presentes en el corpus son todos K. **Ningún record del corpus lleva marca C0.** Los
  records C0 son los que no tienen marca. La frontera es diaria y limpia: el 2026-09-17 tiene 121 records sin marca
  y 0 K; el 2026-09-18 tiene 0 sin marca y 122 K.
- Ventana de hoy del auto-audit (2026-08-20 a 2026-10-19, 11 Tier A): 3.468 C0 contra 3.661 K, o sea 49 % C0.
- Ventana de falsas publicaciones (2026-09-01 a 2026-10-19): 2.048 C0 contra 3.661 K.

## Hallazgos, de mayor a menor gravedad

### F3-01. El auto-audit semanal mezcla C0 y K en recall y magnitud, y la mezcla oculta el déficit de recall de K en VIIRS 375
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:360` (ventana rodante de 60 días sin régimen), `:316-334` (recall), `:426-463` (magnitud). No hay ninguna lectura de `regimen` ni de `codigo_sha` en el script (lo leí entero).
- SCRIPT:SALIDA: `simular_audit_hoy.py` (corre `main()` con `OUTDIR` desviado a temporales, salida en `simular_audit_hoy_salida.txt`) y `recall_por_regimen.py` (`recall_por_regimen.json`).
- QUÉ PASA: la mitad de la ventana son noches vistas con el detector viejo y la otra mitad con el nuevo, y el script las promedia como si fueran una sola serie. El recall por noche (predicado «cráter») da:

  | sensor | todo (lo que el audit reporta) | C0 | K | banda |
  |---|---|---|---|---|
  | VIIRS 375 | 95,6 % (n=204) | 99,1 % (110) | **91,5 % (94)** | 93,4 |
  | VIIRS 750 | 78,4 % (51) | 88,0 % (25) | 69,2 % (26) | 79,5 |
  | MODIS | 66,7 % (12) | 100 % (2) | 60,0 % (10) | 95,0, no evaluable con n<15 |

  En VIIRS 375 la mezcla pasa la banda y K sola no la pasa. Viola el paso 10 de la propia regla de adopción
  (`experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`, sección 4, punto 10: «Toda comparación con MIROVA que cruce la
  fecha de adopción se estratifica por régimen»).
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero; se ve en el issue semanal. **Predicción para hoy**: el cron de
  este lunes (llega históricamente entre 15 y 18 UTC) va a escribir `FUERA_DE_BANDA` con 3 flags: recall VIIRS 750
  78,4 %, magnitud Nevados de Chillán 0,684 y Tupungatito 0,54. Las tres son mezclas.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_3/simular_audit_hoy.py` y `python experiments/_s155_audit/frente_3/recall_por_regimen.py` sobre `cb90031a`.
- CONFIANZA: CONFIRMADO (medido). Matiz de D-9 en F3-08: 5 de las 8 noches K de VIIRS 375 sin cráter son alertas de 0,05 MW o menos.
- GRAVEDAD: 4. Es el instrumento que debía avisar si K pierde alertas, y la mezcla le tapa justo eso durante las próximas cinco semanas.

### F3-02. La serie de falsas publicaciones que la sombra de K usa como disparador mezcla 86,5 % con 2,0 %
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:62` (`INICIO_REGIMEN_FALSAS = "2026-09-01"`), `:85-88` (`ventana_falsas`), `:337-355` (`linea_historial` escribe `falsas_pub_pct` sin régimen).
- SCRIPT:SALIDA: `falsas_y_recall_por_regimen.py` (`falsas_y_recall_por_regimen.json`), mismo banco y mismo predicado node que el audit.
- QUÉ PASA: en pasadas donde MIROVA miró y no vio nada, VIIRS 375 publica 86,5 % con C0 (n=325) y 2,0 % con K (n=552); el audit escribe **33,3 %** (n=877), número que no corresponde a ningún detector. MODIS 11,2 contra 1,4 (mezcla 5,3); VIIRS 750 21,0 contra 1,2 (mezcla 9,4). El inicio queda fijo en el 2026-09-01 hasta que `hoy − 60 días` lo pase, así que la parte C0 (09-01 a 09-17) sigue dentro hasta el 2026-11-16 inclusive (derivado de `:87`). La regla de adopción (sección 4, punto 9, iii) compara justamente esta tasa contra la cota del A/B (V1: 0,0166 a 0,0383): durante cinco semanas la mezcla la supera por diez veces sin que K haya cambiado.
- CÓMO SE VE EN EL DASHBOARD: invisible; aparece en `data/audit_continuous/history.jsonl`.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_3/falsas_y_recall_por_regimen.py` (ventana 2026-09-01 a 2026-10-19).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4. Puede disparar una investigación de K por un artefacto de la ventana, o, leída al revés, una bajada de 88,6 a 33,3 se lee como mejora gradual.

### F3-03. La marca «detector K» del tablero está 30 días después del escalón real de los datos
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js:16` (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`) y el texto de `textoAviso` (`:44-46`).
- SCRIPT:SALIDA: `escalon_0918.py`. Pasadas nocturnas VIIRS 375 que publican (predicado del audit, que coincide con node en 211 de 211 noches con alerta, ver VERIFICADO LIMPIO), por semana desde el jueves:

  | semana desde | 11 Tier A | Nevados de Chillán |
  |---|---|---|
  | 2026-09-11 | 87,1 % (333) | 90,6 % (32) |
  | 2026-09-18 | **14,9 % (342)** | **6,2 % (32)** |
  | 2026-10-09 | 21,4 % (299) | 70,4 % (27) |

- QUÉ PASA: los últimos 30 días se reprocesaron con K, así que el corte en los datos es el 2026-09-18, pero la línea punteada y el aviso dicen 2026-10-18. Es exactamente el caso que la marca debía evitar: con Chillán en erupción, la caída de publicación el 18 de septiembre no tiene marca y se lee como «la erupción declina»; la marca cae donde la serie no cambia.
- CÓMO SE VE EN EL DASHBOARD: `diario.html` e `index.html` muestran la línea «detector K» en el 18 de octubre y un aviso que dice que las comparaciones que crucen ESA fecha mezclan detectores; el escalón está un mes antes, sin marca.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_3/escalon_0918.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4. Es lo que mira el operador del OVDAS para decidir si un volcán cambió.

### F3-04. La alerta protegida de Chillán MODIS del 2026-10-12 07:20 UTC (2,18 MW) no la ve ningún instrumento automático
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:91` (`MIN_N_RECALL = 15`), `:467-472` (único criterio de recall), y ausencia de cualquier criterio de alerta protegida en el script.
- SCRIPT:SALIDA: `caso_ndc_modis_1012.py`; `poder_de_las_bandas.py` (`poder_de_las_bandas_salida.txt`).
- QUÉ PASA: el consolidado de MIROVA trae `ALERTA_TERMICA` de 2,18 MW a 2,24 km en Chillán, MODIS, 2026-10-12 07:20 (noche, tabla, no OCR). Con K, los dos records MODIS de esa noche no tienen cúmulo (`primary_cluster` vacío). La sombra C0 sí tiene cúmulo (1,376 MW a 1,68 km) pero etiquetado `far`, así que tampoco publicaría; por eso el disparador de reversión de la regla (protegida que la sombra publica y producción calla) no salta. El auto-audit no tiene criterio de protegidas, que es el criterio de victoria de la réplica, y su banda de recall MODIS no puede dispararse: desde el lunes 2026-08-03 ninguna ventana de 60 días alcanza 15 noches MODIS con alerta (hoy 12; mínimo 3 el 2026-08-31). Con K cambió justamente MODIS (banda 22) y es el sensor que el audit no puede juzgar.
- CÓMO SE VE EN EL DASHBOARD: no aparece nada esa noche en MODIS para Chillán; ningún issue lo menciona.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_3/caso_ndc_modis_1012.py`; Nevados de Chillán, MODIS_AQUA, 2026-10-12 07:20 UTC.
- CONFIANZA: CONFIRMADO que la alerta existe, que producción no tiene cúmulo y que el audit no puede verlo. SOSPECHA en la causa física (si es la banda 22, la conectiva o la geometría): no es de este frente.
- GRAVEDAD: 4.

### F3-05. #779: la ventana rodante explica el cruce del umbral, no el problema; con los datos de hoy es mezcla más K
- SCRIPT:SALIDA: `reproducir_779.py` (corpus y referencia de los commits `0a3b4e3ac` y `f3b414213`, lógica del audit de hoy); `tupungatito_779_mitades.py`; `auto_audit_estratificado.py`; `pareado_k_vs_sombra.py`; `pareado_por_pasada.py`.
- Control del instrumento: reproduce exacto 0,707 con n=24 (2026-08-13 a 10-12) y 0,647 con n=23 (08-15 a 10-14), con y sin la unión histórica (no cambia Tupungatito). La afirmación del loop, «salió una noche (2026-08-13, 0,793) y la mediana cambió de lado», queda **CONFIRMADA**.
- Pero esa ventana (todo C0) tiene un cambio de nivel adentro: 0,838 (n=11, 08-15 a 09-12) contra **0,384** (n=12, 09-13 a 10-14). En la segunda mitad MIROVA publica alertas de 0,87 a 2,51 MW donde nuestro cúmulo da 0,03 a 0,16 veces eso. «No es una regresión» es incompleto: es un cambio de nivel desde mediados de septiembre, previo a K.
- Hoy (ventana 08-20 a 10-19, corpus con K): 0,540 (n=23), C0 0,828 (n=14), K **0,281** (n=9); todo VIIRS 375.
- ¿Efecto de K? En las mismas pasadas (sombra C0 contra producción K, 2026-10-02 a 10-18): por noche K 0,469 contra C0 0,800 (n=5). Pero pasada a pasada, donde los dos publican, K/C0 = **1,0** (n=17): K no achica la magnitud de una pasada, publica en menos pasadas (62 pasadas sólo C0 contra 17 en ambos) y el audit toma el máximo de la noche. Ver F3-06.
- CÓMO SE VE EN EL DASHBOARD: invisible salvo como issue.
- CONFIANZA: CONFIRMADO lo medido. SOSPECHA la causa física del cambio de nivel de septiembre.
- GRAVEDAD: 3.

### F3-06. La magnitud del audit no es la que se publica, mezcla sensores y confunde «cuánto» con «cuántas pasadas»
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:413` (usa `pc.vrp_mw`), `:439-440` (`max(o["dash"]) / mvrp` y `ratios_by_vol[vol]` sin sensor). En el tablero, VIIRS 375 publica `f5_core_vrp_mw` (`frontend/index.html:1255`, `:1295-1317`).
- SCRIPT:SALIDA: `auto_audit_estratificado.py`, `pareado_por_pasada.py`.
- QUÉ PASA: (a) Con la magnitud que el operador ve, Tupungatito da 0,72 y Chillán 0,717 (dentro de banda); con `pc.vrp_mw`, 0,540 y 0,684 (fuera). Dos de los tres flags de hoy dependen de medir un número que no se publica. (b) La mediana de Chillán junta MODIS (5 noches), VIIRS 750 (10) y VIIRS 375 (19), sensores con calibraciones distintas. (c) Bajo K la razón por noche baja porque publican menos pasadas por noche y el máximo sale de menos candidatos; pasada a pasada K/C0 = 1,0 en Tupungatito (n=17), Isluga (40), Chillán (82), PCC (36), Planchón (16), Chaitén (7), Lastarria (7); Láscar 0,705 (18).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### F3-07. El issue atribuye la causa antes de medirla, cita una banda que no es la del código y no deduplica
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:156-159` (todo sub-banda se rotula «déficit de régimen débil S124»); `.github/workflows/audit-weekly.yml:115` («magnitud [0.5-2.0]x») contra `scripts/auto_audit_weekly.py:132` (`RATIO_BAND_MEDIAN = (0.7, 1.4)`); `audit-weekly.yml:111-115` crea un issue nuevo en cada `FUERA_DE_BANDA` sin buscar uno abierto (la rama DEGRADADO sí busca).
- QUÉ PASA: quien lee #779 ve 0,647 y una banda declarada de 0,5 a 2,0, o sea «dentro»; y la causa ya viene escrita (S124) cuando hoy la caída de Chillán es de K y de menos pasadas (F3-05, F3-06). La decisión de PR #850 de «aceptar que el issue salte las primeras semanas» vive en el cuerpo del PR, no en el generador: el issue de hoy no lo dice.
- CÓMO SE VE EN EL DASHBOARD: invisible; en el issue. Hoy se abrirá un segundo issue con #779 todavía abierto (`gh issue list` lo muestra abierto).
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 2.

### F3-08. El recall del audit juzga «cráter», no publicación, y no aplica la regla D-9
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:469-471` (flag sobre `recall_crater_pct`); `:366` (`alertas_mirova` sin `aplicar_regla_minimas`); `scripts/banco_paridad.py:210` (`regla_minimas="original"` por defecto) usado sin modo en `:219`.
- QUÉ PASA: con C0, `latest.json` del 2026-10-14 daba MODIS cráter 100 % y tablero 30 % (n=10): 7 de 10 noches con alerta no se veían y el audit quedó VERDE en ese eje. Y de las 8 noches K de VIIRS 375 contadas como pérdida, 5 son alertas de 0,05 MW o menos, que el banner de MIROVA llama NONE y que la regla decidida (SN) cuenta como «MIROVA no vio nada». En las mismas pasadas, la publicación en positivos de VIIRS 375 con K es 88,3 % (n=163) con la regla original y 94,4 % (n=143) con SN.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `recall_por_regimen.py` (lista `perdidas_K`), `falsas_y_recall_por_regimen.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### F3-09. Ningún instrumento sabe de régimen; el régimen C0 sólo se reconoce por ausencia de marca
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:538-553` y `:349-355` (sin `codigo_sha` ni fracción por régimen en `latest.json` ni en `history.jsonl`); `experiments/_s143_evaluador/evaluar.py:133-180` (carga brazos de `data/<brazo>` y compara cobertura y `product_version`, no `codigo_sha`); `grep -rn codigo_sha scripts/ experiments/_s143_evaluador/` da 0.
- QUÉ PASA: la regla de adopción (sección 4, punto 10) dice «el resto de la historia queda con su marca»; medido, 0 records del corpus llevan marca C0. Cuando el reproceso histórico con K (`_s154_reproc_k_historico`, run 39125546355, 176 trozos) entre a producción, la frontera se moverá otra vez sin que ninguna serie lo registre.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### F3-10. El watchdog llama «colgada» a una corrida por la edad del run, no del job
- ARCHIVO:LÍNEA: `.github/workflows/reproc-watchdog.yml`, función `evaluarCorrida` (`horas` desde `r.created_at`, umbral 7 h) y el texto «lleva X h en `queued`, sobre el techo de 6 h por job».
- SCRIPT:SALIDA: `watchdog_vs_jobs.py` (`watchdog_vs_jobs_salida.txt`): run 39125546355, edad 22,9 h, 177 jobs (137 completados, 8 en curso, 32 en cola), job más largo **2,14 h**, 0 jobs sobre 6 h; el watchdog lo da por colgado. El estado `queued` del run sale porque hay jobs en cola detrás de `max-parallel`, no porque nada corra. Además una falla de un A/B de una sola vez sigue reportándose 14 días (`MAX_DIAS_ANTIGUEDAD`): #824 lleva 25 comentarios en 4 días.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (no tuerce una alerta volcánica; el ruido tapa la falla real cuando llegue).

### F3-11. `pipeline/audit_metrics.py` replica el cúmulo, no lo publicado
- ARCHIVO:LÍNEA: `pipeline/audit_metrics.py:68-109` replica `mirovaEqVrp` pero no `mirovaEqVrpDisplay` (núcleo F5 en VIIRS 375) ni el predicado de publicación (`isValidDetection`, `isSummitDetection`, `isThermalArtifact`). Sin consumidores vivos: `grep` sólo lo encuentra en tests y en experimentos viejos.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (trampa latente: el nombre promete «lo que ve MIROVA-equivalente»).

### F3-12. Los avisos de calidad de la referencia no quedan en la salida del audit
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:366` lee los CSV con `load_mirova_alertas` sin `calidad_referencia_mirova.avisar` (regla A119 d); el aviso sale sólo por stderr desde el banco (`scripts/banco_paridad.py:225`) y no se guarda en `latest.json`. Hoy pisa los hitos 2026-10-09 y 2026-10-10 del OCR.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## Estratos propuestos para la tarea 1.35 (sin implementar)

Para todo instrumento que compare contra MIROVA o contra sí mismo en el tiempo:

1. **Régimen** por `regimen.codigo_sha` (K si desciende de `34cea39e`; C0 = sin marca y fecha anterior a la frontera, que hoy es 2026-09-18 y cambiará al entrar el histórico). Informar la fracción de cada régimen en la ventana y no emitir un veredicto mezclado: o se juzga sólo el régimen vigente, o se informa cada uno.
2. **Sensor dentro de volcán** para la magnitud (no mezclar MODIS, VIIRS 750 y VIIRS 375 en una mediana).
3. **Ángulo cenital** (z<30, 30 a 50, 50 a 60, 60 o más, el `zbin` del banco) para magnitud y para falsas de VIIRS 375; el banco ya lo calcula (`cenital_neg_v375`) y el audit no lo usa.
4. **Día / noche**: hoy sólo noche (`ENABLE_DAYTIME_MODIS` y `flag_viirs_diurno()` en False); el estrato diurno debe nacer el día que se encienda cualquiera.
5. **Regla D-9** en los tres modos (SN decide; SE y original informados), en recall, falsas y magnitud.
6. **Predicado**: cráter y publicación (node) por separado; el flag sobre publicación.
7. **Magnitud publicada** (`f5_core_vrp_mw` en VIIRS 375) junto a `pc.vrp_mw`, y **pasadas que publican por noche** junto a la magnitud, para separar «cuánto» de «cuántas».
8. **Alertas protegidas** (1 MW o más, lectura A) como lista nominal, no como tasa: con n chico una sola pérdida es el dato.
9. Para el watchdog: duración del job más largo y progreso (completados sobre total), no edad del run.
10. Para la marca del tablero: la fecha del primer record K en los datos, además de la del merge.

## VERIFICADO LIMPIO

- Radios `inner_radius_km` idénticos en las cuatro fuentes (audit, `audit_metrics`, `frontend/index.html`, `volcanoes.yaml`) para los 11 Tier A: `python experiments/_s155_audit/frente_3/radios_inner.py`.
- El predicado «dash» del audit coincide con el predicado del tablero ejecutado con node en las 211 noches con alerta de 2026-09-01 a 2026-10-19 (MODIS 11, VIIRS 750 38, VIIRS 375 162; 0 discrepancias): `falsas_y_recall_por_regimen.py`, bloque `predicado_audit_vs_node`.
- El audit es determinista y reproducible desde commits viejos: 0,707/24 y 0,647/23 exactos (`reproducir_779.py`); la unión histórica no cambia Tupungatito en esas ventanas.
- `nrt-healthcheck.yml` usa `records[-1]` como último dato: los 11 JSON están ordenados (0 inversiones, último = máximo): `orden_records.py`.
- Clasificación de régimen: control positivo 2.609 de 2.609 records procesados después del merge son K; frontera diaria limpia 09-17 / 09-18: `regimen_por_ventana.py`.
- Con K, `triggered_test1` es False en 3.687 de 3.687 records y `n_test1_pixels` es 0 en todos; el audit semanal no lee ningún campo del Test 1 (leído entero), así que no hay campos vacíos que cambien de sentido en él: `campos_test1_por_regimen.py`.
- Filtros diurnos apagados en producción (`ENABLE_DAYTIME_MODIS False`, `flag_viirs_diurno() False`), así que el audit y el pipeline excluyen lo mismo.
- `calidad_referencia_mirova.avisos_de_ventana` es correcta: el hito es «desde cuándo el defecto ya no aplica», así que una ventana anterior al hito sí está afectada; mi sospecha inicial quedó refutada: `calidad_ventana_fuera.py`.
- `nrt-monitor.yml` maneja SIN DATO y no depende del régimen (leído).
- Tests de los instrumentos en verde, 45 passed (`pytest tests/test_audit_metrics_paridad_frontend_s126.py tests/test_audit_metrics.py tests/test_auto_audit_cobertura_s150.py tests/test_reproc_watchdog_vivos_s133.py`), pero ninguno cubre régimen: el verde no prueba nada de F3-01 a F3-10.
- La sombra (`data/experimental_v2`) no es copia de producción: de 1.900 pares posteriores al 2026-09-18, 740 tienen `pc.vrp_mw` idéntico y 1.160 no; cubre del 2026-10-02 al 2026-10-18.

## Lo que no miré

- `experiments/_s151_ab_diurno/evaluar_diurno.py` (excluido por encargo).
- `experiments/_s151_prereg_fk_11/evaluar_fk.py` y `experiments/_s146_ab_sin_test1/evaluar.py` más allá de comprobar que el segundo, como el de S143, llama `indexar_referencia` sin modo D-9 (`:794`).
- `scripts/libro_de_cuentas.py`: no lo corrí; usa `triggered_test1` en su predicado de validez (`:142`, `:170`), que con K es siempre False, y recalcula sobre el corpus mezclado (A90). Queda SOSPECHA de números que cambian por régimen, no por fenómeno.
- No diagnostiqué por qué producción no tiene cúmulo en Chillán MODIS 2026-10-12 (F3-04): es del detector.
