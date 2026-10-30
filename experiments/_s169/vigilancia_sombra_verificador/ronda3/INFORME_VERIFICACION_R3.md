# Verificación corta de la ronda 3 de la vigilancia de la sombra (cd8b7074f contra f743d7b8f)

## 1. Encabezado

- Fecha y hora del servidor (`date -u`): 2026-10-30, 06:49:38 UTC al empezar; 07:16:19 UTC al cerrar.
- caminos.md: sha256 `fb0389aef7a2185a7728ce0e98e0982401481b9c9163a0957e57f527024c78a5`, fijado a las 06:50:08 UTC, antes de abrir ningún archivo citado ni el INFORME.md del autor. El sello está en `caminos_sello.txt`, aparte, para no alterar el hash. Verificado sin cambios al cerrar.
- Commit medido: `cd8b7074f`. Árbol parcial en `arbol/`: comprobé con `cmp` contra `git show cd8b7074f:<ruta>` que los 8 archivos que importan son idénticos (revisar_sombra.py, tachar_secreto_log.py, ventana_sombra.py, fetch.py, run_pipeline.py y tres tests). Completé con `git archive` CLAUDE.md, README.md y docs/ porque 4 guardias los leen.
- Modelo: claude-sonnet-5-5, esfuerzo bajo.
- CARPETA: `D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/`. Instrumentos en `medidas/` con su salida al lado.
- NO miré: `data/sombra_codigo_mirova/` (prohibido); ningún run real de GitHub (sin red), así que la semántica de `steps.tachar.outcome` en Actions la razono, no la ejecuté; Python 3.11 del runner (sólo tengo 3.12); la lista exacta de archivos de la batería de 225; 36 de las 48 mutaciones del autor (corrí 12).

## 2. En una pantalla

- MERGEABLE. Las cinco peticiones de la ronda 2 (VR2-01 a VR2-05) se cumplen en lo que afirman. T1, T2 y T4 CONFIRMADOS; T3, y el nulo y las pruebas de T5, CONFIRMADOS EN PARTE. Nada nuevo pasa de gravedad 2.
- Lo único relevante (VR3-01, gravedad 2, falso rojo): un día sin pasada NOCTURNA de MODIS sobre un volcán del norte, con gránulos de DÍA en el catálogo, deja el job rojo hasta 8 corridas, porque esa búsqueda no deja la incidencia `sin_granulos`. En `data/mirova_equivalent` Isluga tiene 4 de 228 días sin record MODIS y Láscar 3 de 228. El INFORME del autor ya declara «gránulos de día» como falso rojo, pero no su frecuencia.
- Pruebas: 56 de 56 reproducidas; 137 passed y 4 skipped en una batería de 8 archivos (no pude reproducir el 225 exacto). Nulo: reproduje 12 mutaciones del autor (todas atrapadas por aserción) y agregué 8 propias sobre T1: 3 sobreviven con significado (VR3-04, hueco de pruebas; el código es correcto).

## 3. Hallazgos

### VR3-01
- TÍTULO: Un día sin pasada nocturna de MODIS, con gránulos de día en el catálogo, es FALLA sin excusa posible (falso rojo de hasta 8 corridas)
- ARCHIVO:LÍNEA: pipeline/fetch.py:1247-1256 (filtro nocturno: `if not l1b_granules: continue` sin `registrar_incidencia`); pipeline/fetch.py:1230-1236 (`sin_granulos` sólo si la búsqueda respondió vacía); scripts/revisar_sombra.py `_sin_pasada` y el control por día. Medidas: medidas/m2_t1_escenarios_salida.txt (escenario 04), medidas/m1_dias_sin_pasada_salida.txt, medidas/m1b_salida.txt, y experiments/_s168/sombra_run_40945613044/log_job_lascar.txt (64 de 64 búsquedas con «kept N of M granules (night filter)» y M mayor que N).
- QUÉ PASA: Terra y Aqua pasan de día y de noche, y la búsqueda de un día trae ambas pasadas (en el log real de Láscar, 64 de 64 búsquedas traen gránulos que el filtro nocturno descarta). Si una noche el hueco entre órbitas deja al volcán sin pasada nocturna de ambos satélites, la plataforma cuenta `con_granulos` (los de día), no hay `sin_granulos`, no hay record ni K, y el control por día exige una prueba de que no hubo pasada: FALLA. Afecta a MODIS (2330 km de franja, huecos a baja latitud); VIIRS (3000 km) casi no.
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no se lee en el tablero). En el job, FALLA «MODIS d: ningún record de la vía y ninguna prueba de que no hubo pasada» en cada corrida mientras d esté en la ventana (hasta 8), y el monitor abre su issue a las 26 h.
- CÓMO REPRODUCIRLO: `C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -B D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/medidas/m2_t1_escenarios.py` (escenario 04: Terra con gránulos, Aqua `sin_granulos`). Frecuencia: `.../python.exe -B medidas/m1_dias_sin_pasada.py` (ventana 2026-03-01 a 2026-10-14, 228 días, `data/mirova_equivalent`, que es K y no la sombra): MODIS sin ningún record, Isluga 4 días (2026-04-24, 04-29, 05-24, 09-29), Láscar 3 (05-04, 05-24, 10-04), los otros 9 volcanes 0; VIIRS 0 en los 11. Control positivo: el mismo script con `familia()` cuenta records en los otros volcanes (Lastarria 0 días sin record de 228).
- CONFIANZA: CONFIRMADO el mecanismo (código y escenario). SOSPECHA la frecuencia real en la sombra: medí K como proxy (un día sin record en K puede ser también un fallo de procesamiento de K) y en las 8 búsquedas diarias del log de Láscar no aparece ningún «kept 0 of», o sea que no vi el caso ocurrir.
- GRAVEDAD: 2. No tuerce una alerta, pero degrada la confianza en el rojo de la sombra justo en los volcanes del norte, y el INFORME de la ronda 3 lo presenta como caso raro (gránulos de día o fuera de la grilla). Salida posible sin tocar `pipeline/` (congelado, A45): que `revisar_sombra.py` lea del `--log` la línea «kept 0 of N granules (night filter)» del día d y la acepte como prueba de no pasada nocturna (el día va en la línea `>>> volcán | fecha` anterior).

### VR3-02
- TÍTULO: Con `--ini` o `--fin` ilegibles el control por día no corre y la revisión sale verde
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py `_dias` (devuelve [] si `date.fromisoformat` falla) y `revisar` (`for d in dias`); medidas/m3_fuzz_revisar_salida.txt (casos `ini_vacio` y `fin_basura`: rc 0).
- QUÉ PASA: `_dias` traga el ValueError y devuelve lista vacía; con `--ini ""` o `--fin hoy` ningún día se juzga y, si la corrida escribió algo de la vía, el resultado es verde. El resumen dice «días juzgados: ninguno (antes del 2026-11-03)», que no es la causa. `--desde-utc` vacío, en cambio, sí es FALLA (VR2-04 cumplido).
- CÓMO SE VE EN EL DASHBOARD: invisible. No es alcanzable desde el workflow: `ini` y `fin` salen de `scripts/ventana_sombra.py`, que valida y sale con 2.
- CÓMO REPRODUCIRLO: `.../python.exe -B medidas/m3_fuzz_revisar.py` (casos `ini_vacio`, `fin_basura`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VR3-03
- TÍTULO: Un JSON o una cobertura bien formados pero de forma inesperada dan traceback, sin línea FALLA ni «K caídos»
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py `revisar` (`r.get(...)` sobre cada record; `.get` sobre incidencias y fallas); medidas/m3_fuzz_revisar_salida.txt.
- QUÉ PASA: `records` con un elemento no objeto (`null`, número, texto), `records` como diccionario, `regimen` como texto, o `fallas` con elementos no objeto, lanzan `AttributeError`. El rc es 1 (rojo igual) pero sin mensaje ni línea de K, que es lo que VR2-04 pedía para insumos malos. Los casos que la tarea nombra (JSON truncado, vacío, de raíz lista, bytes basura, directorio, cobertura corrupta, `--desde-utc` vacío o basura) sí dan FALLA con mensaje y línea de K: de 33 casos, 7 dan traceback y todos son de forma interna.
- CÓMO SE VE EN EL DASHBOARD: invisible. Poco alcanzable: el JSON lo escribe `pipeline/store.py`.
- CÓMO REPRODUCIRLO: `.../python.exe -B medidas/m3_fuzz_revisar.py`. Controles: `CONTROL_sano` rc 0 y `CONTROL_sin_records_de_hoy` rc 1 (el instrumento distingue).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VR3-04
- TÍTULO: El nulo de 48 mutaciones no atrapa tres mutaciones sobre el control por día
- ARCHIVO:LÍNEA: experiments/_s169/vigilancia_sombra/m4_mutaciones_r3.py (lista MUT); mis mutaciones en medidas/m4_muestra.py (Y1 a Y9) y su salida en medidas/m4_muestra_2_salida.txt.
- QUÉ PASA: sobreviven (56 pruebas, 0 fallas) Y2 (el primer día de la ventana no se juzga, y una ventana de un solo día queda sin días), Y3 (cualquier tipo de incidencia vale como prueba de ausencia, no sólo `sin_granulos`) y Y9 (una plataforma retirada se cuenta como muerta aunque su cese sea posterior al día). El código de hoy es correcto en los tres: los escenarios 05 y 14 (primer día y ventana de un día perdidos) y 08 (otro tipo de incidencia no es prueba) dan FALLA en medidas/m2_t1_escenarios_salida.txt. Y6 (basta un K nuevo para «la corrida escribió algo») e Y7 (SNPP vivo no exigido) también sobreviven, pero son equivalentes en la práctica: Y6 igual da FALLA por «records de otra fuente» e Y7 no importa mientras SNPP esté retirada. Y9 sí podría importar si se anuncia otro cese a mitad de ventana.
- CÓMO SE VE EN EL DASHBOARD: invisible. Es hueco de pruebas, no defecto del código.
- CÓMO REPRODUCIRLO: `.../python.exe -B medidas/m4_muestra.py D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol "Y"` (unos 3,5 min).
- CONFIANZA: CONFIRMADO. No declaro equivalentes a Y2, Y3 ni Y9.
- GRAVEDAD: 1.

### VR3-05
- TÍTULO: Re-despachar a mano una ventana ya completa sale FALLA «la corrida no produjo nada»
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py (`via_nuevos == 0`); pipeline/store.py:664-703 (deduplica por (datetime_utc, sensor) y no reescribe `processed_utc` salvo overwrite o reemplazo NRT a estándar); escenario 15 de medidas/m2_t1_escenarios_salida.txt.
- QUÉ PASA: es el diseño pedido («corrida muerta»), pero un `workflow_dispatch` sobre una ventana cuyos records ya están en el JSON no escribe nada nuevo y sale rojo aunque la ventana esté completa. El mensaje no dice que ya estaba todo. Un «re-run failed jobs» no entra aquí: el checkout sigue en el sha original, sin los datos del primer intento.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: escenario 15 (records con `processed_utc` anterior al inicio de la corrida). No ejecuté un despacho real.
- CONFIANZA: CONFIRMADO el mecanismo; el despacho real es SIN DATO.
- GRAVEDAD: 1.

## 4. Veredicto por afirmación

| Afirmación | Veredicto | Evidencia de esta sesión |
|---|---|---|
| T1 (VR2-01 y VR2-02): record de la vía por día, volcán y sensor, o prueba tomada de la cobertura de ESTA corrida; FALLA si falta, hoy o antes | CONFIRMADO | 15 de 15 escenarios con el veredicto esperado (`m2_t1_escenarios_salida.txt`): primer día, último día, ventana de un día, día medio, prueba de otro día, otro tipo de incidencia, K solo, corrida muerta. La cobertura de esta corrida sí cubre toda la ventana: `limpiar_fallas()` se llama una vez por corrida (`run_pipeline.py:655`) y el bucle recorre cada fecha sin saltar días que ya tienen records (`run_pipeline.py:662-667`), así que un día anterior sin pasada real recibe su `sin_granulos` en cada corrida; no hay falso rojo permanente por «cobertura sólo de lo nuevo». Días anteriores al 2026-11-03: excluidos (escenario 13; mutación W2 atrapada). Suomi NPP: retirada en sus dos productos (`scripts/ceses_esperados.json`, cese 2026-11-02T13:00Z); `_sin_pasada` la salta con la misma regla que `fetch.cese_cumplido` y no le exige incidencia; escenarios 09 a 11. Día con gránulos pero todos `sin_grilla` o fuera del volcán: queda como K o sin record, y es FALLA; el caso de gránulos de DÍA es VR3-01. |
| T2 (VR2-03): el tachado falla cerrado, tacha URL y JSON, el upload depende del tachado, el token no se imprime | CONFIRMADO | yml: paso `id: tachar` sin `continue-on-error` (líneas 167-173) y upload con `if: always() && steps.correr.outputs.corrio == 'true' && steps.tachar.outcome == 'success'` (línea 176). Por la semántica de Actions, si el paso falla o se cancela, `outcome` no es `success` y el artefacto no se sube. `m6_tachar_salida.txt`: literal, `quote`, `quote_plus`, `\/` y `json.dumps` quedan tachados (cada caso con control «antes=True»); directorio en vez de log: rc 1 y la cobertura se tacha igual; archivo de solo lectura: rc 1; el token no aparece en stdout ni stderr (los mensajes llevan sólo `type(e).__name__`). Fuera de lo afirmado: base64, token partido en dos líneas y en mayúsculas NO se tachan. |
| T3 (VR2-04): JSON o cobertura corruptos, o `--desde-utc` vacío, dan FALLA con mensaje, sin traceback, y «K caídos» sale | CONFIRMADO EN PARTE | Para todos los casos nombrados (truncado, vacío, raíz lista, bytes basura, directorio, cobertura corrupta, `--desde-utc` vacío y basura): rc 1, FALLA con motivo, línea «K caídos» (con «sin dato» si el JSON no se leyó) y también en `GITHUB_STEP_SUMMARY` (`m3b_resumen_job_salida.txt`). Reservas: VR3-03 (7 casos de forma interna con traceback) y VR3-02. |
| T4 (VR2-05): las cuatro pruebas existen y atrapan las mutaciones | CONFIRMADO | Existen `test_vr2_05_frontera_de_6_h_exactas_ya_alerta` (en tests/test_monitor_sombra_s169.py; prueba 6:00:00 y 5:59:59), `test_vr2_05_una_falla_de_cobertura_sin_fecha_es_falla`, `test_vr2_05_el_token_se_toma_sin_espacios_ni_salto_de_linea` y `test_vr2_05_con_token_vacio_no_toca_nada`. Corrí yo la mutación X8 (atrapada por la prueba de falla sin fecha). X3, X12 y X13 constan atrapadas en `m4_r3_salida_autor.txt`; no las corrí. |
| T5 pruebas: 56 de 56; 225 de 225 con 4 saltadas | CONFIRMADO EN PARTE | 56 passed (`t5_s169.txt`). Batería de 8 archivos (las dos S169, s167, cadencia y 4 guardias de workflows): 137 passed, 4 skipped (`t5_bateria2.txt`); las 4 saltadas son `test_guard_timeout_vs_ventana_s129.py:102`, preexistentes. Sin docs ni CLAUDE.md el árbol da 4 fallas ambientales (`t5_bateria.txt`) que desaparecen al completarlo. El 225 exacto: SIN DATO. |
| T5 nulo: 48 de 48 atrapadas por aserción | CONFIRMADO EN PARTE | Corrí 12 mutaciones más el control `ninguna` (56 pruebas, 0 fallas): A, B, D, E, H, I, W1, W2, W3, W4, W5, X8, todas atrapadas con los mismos nombres de prueba que en `m4_r3_salida_autor.txt`. El script lee el XML de pytest y cuenta como atrapada sólo una falla por aserción (`AssertionError`, `assert ...` desnudo, o «AssertionError» en la última línea E); un `<error>` o un `failure` de otro tipo no cuenta; el control «CONTROL js roto» del autor da 9 fallas por `CalledProcessError` y 0 por aserción (en su archivo; yo no lo corrí). Las otras 36 no las corrí. De mis 8 mutaciones propias, 3 sobreviven con significado (VR3-04). |

## 5. SEGUIMIENTOS (fuera de mi eje)

- S1. `scripts/revisar_sombra.py` sigue sin mirar las incidencias `sin_geolocalizacion` y `dia_parcial` (heredado del seguimiento S2 de R2). Preexistente. SOSPECHA, gravedad 1.
- S2. `scripts/ceses_esperados.json` dice «sujeto a cambio». Si NASA mueve el cese de Suomi NPP, hay que editar ese archivo; `revisar_sombra.py` toma el cese de la cobertura de la corrida, así que sigue la misma lista que el pipeline. Consistente hoy; sólo anotado. Gravedad 1.

## 6. VERIFICADO LIMPIO

- Árbol `arbol/` idéntico a `cd8b7074f` en los 8 archivos que importan (`cmp` contra `git show`). Vara: el commit.
- El delta no toca `pipeline/`: `git diff --stat f743d7b8f cd8b7074f` lista 10 archivos, ninguno en pipeline/.
- Compatibilidad con 3.11 del runner: ningún f-string con comilla repetida en los dos scripts (dos grep, sin salida). Vara débil: heurística, no ejecuté 3.11.
- Cobertura de todos los días de la ventana: vara `run_pipeline.py:655-667` y `fetch.py:1205-1286`, leídos.
- Variantes del token y fallo cerrado: `medidas/m6_tachar_salida.txt`.

## 7. SIN DATO

- Comportamiento real en Actions (`steps.tachar.outcome`, `upload-artifact`, `GITHUB_STEP_SUMMARY`).
- Frecuencia real de días sin pasada nocturna de MODIS en la sombra (VR3-01; medí K como proxy).
- El 225 exacto de la batería, 36 de las 48 mutaciones y la compatibilidad con Python 3.11.

## 8. FUERA DE ALCANCE

- `pipeline/` (congelado), `data/sombra_codigo_mirova/`, despachos de workflows, y el monitor del NRT más allá de su prueba de 6 h.

## 9. Veredicto

MERGEABLE. Lo pedido en la ronda 2 está cumplido y verificado, y lo nuevo es de gravedad 2 o menos. Recomiendo atender VR3-01 como tarea aparte (sin tocar `pipeline/`) antes de que pasen unas semanas de sombra, porque va a producir rojos en Isluga y Láscar que se leerán como fallas reales. No bloquea el merge.
