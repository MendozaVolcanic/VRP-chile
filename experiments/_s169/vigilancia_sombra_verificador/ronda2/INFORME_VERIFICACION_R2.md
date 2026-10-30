# Verificación corta de la ronda 2 de la vigilancia de la sombra (f743d7b8f contra 16d9e894d)

## 1. Encabezado

- Fecha y hora del servidor (`date -u`): 2026-10-30, 05:33:58 UTC al fijar caminos.md; 05:46:53 UTC al cerrar. (El reloj avanzó poco para el tiempo de pared que sentí; lo dejo como lo dio `date -u`.)
- caminos.md: sha256 `833c13b7a2e77f19534061f4537758c869f5b623284a0f30b84dfc1020dfbed2`, fijado a las 05:33:58 UTC, antes de abrir ningún archivo citado. Verificado sin cambios al cerrar.
- Commit medido: `f743d7b8f` (árbol parcial en `arbol/`, completado con `git archive` de CLAUDE.md, README.md, docs/, `experiments/_s153_fk_v2` y `experiments/_s151_prereg_fk_11/sombra_pasadas_juzgadas.json`, porque 8 guardias leen esos archivos).
- Modelo: claude-sonnet-5-5, esfuerzo bajo.
- CARPETA: `D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/`. Instrumentos en `medidas/` (m2_revisar_r2.py, m3_monitor.js, m6_tachar.py, m4_copia.py, m5_extra.py, con sus `_salida.txt`).
- NO miré: `data/sombra_codigo_mirova/` (prohibido); ningún run real de GitHub (sin red); el comportamiento real de `actions/github-script`, `upload-artifact` y del `GITHUB_STEP_SUMMARY` en Actions; la versión de earthaccess que instala el runner; si el log real de la vía imprime el token. Las 32 mutaciones del autor las reproduje sólo en parte (9 de 32, ver R7) porque el script entero dura unos 40 s por mutación (más de 10 min): el límite de la tarea me lo impidió.

## 2. En una pantalla

- MERGEABLE CON CAMBIOS. R1, R2, R4, R5 y R6 se sostienen en lo que afirman; R3 se sostiene como regla pero deja un hueco que su propio texto no avisa (VR2-01); R7 se reproduce (39/39, 208/208 con 4 saltadas), no así el 32/32 completo.
- Lo peor que encontré (gravedad 2): un día X perdido se marca una sola vez, en la corrida de X; desde X+1 el control por sensor no lo ve y la NOTA dice «lo cubrió una corrida previa» sin comprobarlo (VR2-01). Y la víspera puede tapar un catálogo vacío de hoy (VR2-02).
- El tachado del token es correcto en el camino normal (token por entorno, no por argv; token vacío no llega al paso), pero falla abierto: si el script cae, el artefacto se sube crudo (VR2-03, gravedad 1).
- Pruebas: las 32 mutaciones del autor no cubren 4 de mis 11 mutaciones extra (frontera de 6 h, falla sin fecha, `strip()` del token, token vacío).

## 3. Hallazgos

### VR2-01
- TÍTULO: Un día perdido se marca sólo en su propia corrida; desde el día siguiente es NOTA con un texto que no se comprueba
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:142-154 (clasificación de fallas viejas) y :122-124 (conteo por sensor); medida en medidas/m2_revisar_r2_salida.txt, caso «R3 HUECO»
- QUÉ PASA: si las búsquedas o descargas del día X fallan en la corrida de X, esa corrida sale roja (bien). En la corrida de X+1 la ventana de 8 días reintenta X; si vuelve a fallar, la falla es «día anterior» y queda como NOTA, y el control por sensor sólo exige un record de X o de X+1, que lo cumple X+1. Resultado sintético: 3 fallas del día X, cero records de X, hoy sano: verde, con la línea «lo cubrió una corrida previa y la ventana lo vuelve a buscar». Esa frase no se verifica: si la corrida de X estaba caída (job rojo por otra causa, evento `schedule` perdido, `corrio` sin fijar), nadie cubrió X. El issue del monitor se cierra solo con la verde de X+1.
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no se lee en el tablero); en el job, una línea NOTA en 1 de los 11 logs, durante hasta 7 corridas.
- CÓMO REPRODUCIRLO: `C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -B D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas/m2_revisar_r2.py` (caso «R3 HUECO»).
- CONFIANZA: CONFIRMADO el mecanismo con datos sintéticos; la frecuencia real es SIN DATO. Respuesta a la pregunta de R3: sí, un día se puede perder sin que nada lo marque desde X+1; sólo lo marcó la corrida roja de X (y el issue de 26 h).
- GRAVEDAD: 2. Afecta cuántas noches mide la sombra que decide la adopción, no una alerta de volcán. Cambio posible (no lo hago): que la NOTA diga «sin records del día X» cuando X no tenga ningún record del sensor, y que eso sea FALLA después de dos corridas.

### VR2-02
- TÍTULO: La víspera puede tapar un catálogo vacío de hoy
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:119-124 y :159-172; medidas/m2_revisar_r2_salida.txt, caso «R2 MASCARA»
- QUÉ PASA: la regla de VV169-02 sólo se dispara para sensores que además no tienen records de fin ni de la víspera. Con los tres sensores sin gránulos el día fin pero con records de la víspera reescritos hoy (reemplazo NRT a estándar), el resumen sale verde, sin NOTA y sin FALLA. Un catálogo de CMR vacío como el del 2026-10-18 cae en la misma corrida en que la víspera se reescribe sólo si CMR devuelve estándar de ayer y nada de hoy; es posible, no medido.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el mismo script, caso «R2 MASCARA».
- CONFIANZA: CONFIRMADO el mecanismo (sintético); frecuencia SOSPECHA (hay que tener datos de la sombra reales).
- GRAVEDAD: 2 (el hueco que VV169-02 quiso cerrar sigue abierto en esa combinación; el diseño de «víspera» de VV169-01 lo permite).

### VR2-03
- TÍTULO: El tachado falla abierto y no cubre variantes del token
- ARCHIVO:LÍNEA: scripts/tachar_secreto_log.py:25-37; .github/workflows/sombra-codigo-mirova.yml:165-181; medidas/m6_tachar_salida.txt
- QUÉ PASA: el paso de tachado y el de subida llevan ambos `if: always()`. Si el script lanza una excepción (medido: `pipeline.log` convertido en directorio da PermissionError, rc 1) los archivos siguientes no se procesan (`cobertura.json` quedó sin tachar) y el artefacto se sube igual con el contenido crudo. Tampoco tacha variantes: codificado como URL, base64, con `\/` escapado o partido en dos líneas (medido SIGUE en las cuatro). Con un JWT de Earthdata (alfabeto base64url y puntos) las variantes de URL y JSON no cambian el texto, así que el riesgo real es bajo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `.../python.exe -B D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas/m6_tachar.py`.
- CONFIANZA: CONFIRMADO (medido con token falso).
- GRAVEDAD: 1. La exposición real depende de que el pipeline alguna vez imprima el token, cosa que el autor no vio y yo tampoco puedo comprobar (SIN DATO para el runner).

### VR2-04
- TÍTULO: «La línea K sale siempre» tiene excepciones, y no es una alarma
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:178-179 (línea), :199-212 (main); medidas/m2_revisar_r2_salida.txt, líneas INFO R5
- QUÉ PASA: sale en toda corrida que llega a `revisar` (verde, roja, con o sin `GITHUB_STEP_SUMMARY`: medido). No sale si el JSON de la sombra o la cobertura están corruptos, o `--desde-utc` viene vacío: traceback, rc 1, sin línea ni resumen. Esos casos son rojos de todos modos. Además la línea es un número en el resumen de cada uno de los 11 jobs; nada la agrega ni abre un issue por K acumulados.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el mismo m2, bloque «R5 main».
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VR2-05
- TÍTULO: Varios comportamientos pedidos por R1 a R6 no tienen prueba que los atrape
- ARCHIVO:LÍNEA: scripts/nrt_monitor_decision.js (`< horasPendiente`), scripts/revisar_sombra.py:146 (`if fecha and fecha < fin`), scripts/tachar_secreto_log.py:21 (`.strip()`) y :22-24 (token vacío); medidas/m5_extra_salida.txt
- QUÉ PASA: con las 2 pruebas nuevas, 4 de mis 11 mutaciones extra sobreviven con 39 passed: X3 (frontera de 6 h inclusiva: una corrida de exactamente 6 h pasa a «pendiente»), X8 (una falla sin fecha pasa de FALLA a NOTA), X12 (sin `strip()` un token con salto de línea final no se tacha) y X13 (sin la guarda de token vacío el script insertaría `***` entre cada carácter del log). Las otras 7 se atraparon (X1, X4, X6, X7, X15, X16, X17). X13 y X12 son poco alcanzables en el workflow real (token vacío corta antes, línea 106-109).
- CÓMO REPRODUCIRLO: `.../python.exe -B medidas/m5_extra.py D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/arbol` (unos 8 min).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 4. Veredicto por afirmación

| Afirmación | Veredicto | Evidencia de esta sesión |
|---|---|---|
| R1 (VV169-01) | CONFIRMADO | `revisar_sombra.py:113-124`: `datetime_utc[:10] >= vispera`, y la ventana ya acota a `<= fin`. m2: fin y víspera cuentan; fin-2, fin-3 y `datetime_utc` None no; cambio de mes (30-nov con fin 01-dic cuenta, 29-nov no); formato sin `T` cuenta. Cuenta records por sensor, no «pasadas»; en la sombra un record es una pasada por plataforma. Mutaciones X1 atrapada, V1 del autor no reproducida por tiempo. Matiz: ver VR2-02. |
| R2 (VV169-02) | CONFIRMADO EN PARTE | Línea 171: FALLA con los tres, o con V750 y V375 vacíos a la vez (m2: sí, y no con V750 solo, V375 solo, MODIS+V750 ni MODIS+V375, que quedan en NOTA por diseño). Pero sólo cuenta sensores sin records de fin ni de víspera: VR2-02. |
| R3 (VV169-03) | CONFIRMADO EN PARTE | Falla con fecha < fin: NOTA; fecha == fin, sin fecha o vacía: FALLA (m2). `fetch.py:757-758,890,913,1284` fijan `fecha` como AAAA-MM-DD en todos los puntos que registran fallas, así que el parseo coincide con el formato real. Hueco de pérdida de un día: VR2-01. El texto «lo cubrió una corrida previa» no se verifica. |
| R4 (VV169-04) | CONFIRMADO | `nrt_monitor_decision.js:63-76` y `nrt-monitor.yml:164-165`. m3: 20 de 20 casos esperados: pendiente con schedule en queued, in_progress, waiting, requested, pending de menos de 6 h; alerta con 6,0 h exactas, 6,01 h y 20 h; despacho a mano en curso no cuenta; verde de 25,9 h gana antes que pendiente; `created_at` basura o ausente da alerta (falla hacia el lado seguro). El yml sale antes de `const TITLE` con `pendiente`, sin tocar el issue. Frontera de 6 h sin prueba: VR2-05. |
| R5 (VV169-05) | CONFIRMADO EN PARTE | La línea sale en verde, rojo, con K=0 y K>0, en stdout y en GITHUB_STEP_SUMMARY (m2 «R5 main»); no sale si el JSON o `--desde-utc` están corruptos (traceback). VR2-04. |
| R6 (VV169-07) | CONFIRMADO EN PARTE | El token entra por `env` y se lee de `os.environ`, no por argv (workflow 165-170; script 21); el paso imprime sólo el nombre del archivo y el conteo (m6: el stdout no contiene el token); token vacío o ausente: no toca nada y sale 0, y en el workflow ese caso no llega porque la línea 106-109 hace `exit 1` antes de escribir `corrio=true` (los dos pasos exigen `corrio == 'true'`); `cobertura.json` se tacha junto con el log. Reservas: sube igual si el tachado cae (VR2-03). |
| R7 pruebas | CONFIRMADO | Las dos pruebas nuevas: 39 passed (`pytest` en `arbol/`, 8 s). Batería de 12 archivos: 208 passed, 4 skipped (`guardias_salida_2.txt`); los 4 saltados son `test_guard_timeout_vs_ventana_s129.py:102` (backfill-tier-a, nrt, reproc-chunked y sombra-codigo-mirova «no declara fechas por defecto parseables»), archivo no incluido en el delta. En un árbol sin docs/README/fixtures de experimentos dan 8 fallas ambientales (`guardias_salida.txt`); no son del delta. |
| R7 nulo 32/32 | CONFIRMADO EN PARTE | Control sin mutar: 39 passed. Reproduje las 9 primeras del autor (A a I): mismas pruebas rojas y mismos conteos que `m4_r2_salida.txt` (`m4_copia_salida.txt`). Las otras 23 no las corrí: el script entero da unos 40 s por mutación (más de 10 min). Mi clasificación «por aserción» no quedó medida por mi parser (`tipos E` vacío); lo que sí consta: las pruebas rojas son de aserción por nombre y mensaje (`Ass...`). Mis 11 mutaciones extra: 7 atrapadas, 4 sobreviven (VR2-05). Equivalentes declarados: 0, no objeto. |

## 5. SEGUIMIENTOS (fuera de mi eje)

- S1. `m4_mutaciones_r2.py` (experiments/_s169/vigilancia_sombra/) tiene `DST` fijo en `D:/vrp-trabajo/temporales/s169_vigilancia/arbol_mut` y una línea «ATRAPADA si ' failed' en la salida» que no distingue aserción de error de colección: lo corrí con otro `DST`. Confianza: CONFIRMADO. Gravedad 1.
- S2. `scripts/revisar_sombra.py` no mira las incidencias `sin_geolocalizacion` ni `dia_parcial` (`pipeline/fetch.py:789`, `cuenta_estricto` True); un L1B sin geolocalización cuyo sensor tiene otra plataforma con record pasa sin NOTA. Preexistente, no del delta. SOSPECHA, gravedad 1.
- S3. El tope «<6 h» para pendiente supone que un run no dura más: con `max-parallel: 4`, 11 jobs y 75 min por job la cota teórica del run es 3 oleadas × 75 min = 3,75 h, bajo 6 h, por lo que no hay choque; lo dejo anotado por si se sube el timeout. SOSPECHA, gravedad 1.

## 6. VERIFICADO LIMPIO

- Sensor/plataforma a familia (A48): `familia()` con MODIS_AQUA/TERRA, VIIRS_SNPP/NOAA21 (375), VIIRS_*_750 (750), GOES (None). Vara: la convención de A48 del CLAUDE.md. m2.
- Frontera de mes y formato de fecha de `fecha` de las fallas. Vara: `fetch.py` usa `date.strftime("%Y-%m-%d")`.
- Monitor: ordenamiento ok antes de pendiente; despacho no cuenta; `created_at` inválido. Comando: `node medidas/m3_monitor.js` (control positivo: los casos con alerta; instrumento muerto: sale 1 si algún esperado falla).
- Tachado literal con metacaracteres de regex (usa `str.replace`), bytes no UTF-8 (se reemplazan por U+FFFD), archivos inexistentes. m6.

## 7. SIN DATO

- Comportamiento real en GitHub (github-script, upload-artifact, `GITHUB_STEP_SUMMARY`), frecuencia real de reescrituras NRT a estándar en la sombra, contenido del log real, versión de earthaccess del runner, las 23 mutaciones del autor no corridas.

## 8. FUERA DE ALCANCE

- `pipeline/` (congelado), `data/sombra_codigo_mirova/`, despachos de workflows.
