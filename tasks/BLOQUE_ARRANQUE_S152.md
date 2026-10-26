# Bloque de arranque S152 (cierre de S151, el loop autónomo, vueltas 1 a 98)

Escrito el 2026-10-16 ~13:10 UTC sobre `loop/activo` en `24ac2613` (igual al remoto). **Se fijó con trabajo en
curso en GitHub** (ver tabla a). El estado vivo y la bitácora completa están en `tasks/LOOP_OBJETIVOS.md` de la rama
`loop/activo` (§4 tareas, §5 decisiones, §6 bitácora). Este bloque es el resumen; ante una discrepancia, manda la
bitácora y, por encima de ella, el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | Bloque 0 de higiene (0.1 a 0.6): referencia desde la unión histórica, alerta protegida, marca de régimen | #778, #780, #784, #781, #791, #785 |
| hecho | Mediciones cerradas: Chillán (1.1), D22 sin A/B (1.3), D25 V750 (1.5, condicionada), caja vetada (1.7), modo un píxel (1.8), banda I/M (1.9), V750 0,32 a 0,65 MW (1.10), alertas débiles (1.12), diurnas (1.13), presupuesto de magnitud (1.14), corrimiento MODIS (1.15) | bitácora vueltas 1 a 57 |
| hecho | 1.16 repaso con material crudo → 1.17 a 1.20 | `experiments/_s151_repaso_crudo/INVENTARIO.md` |
| hecho | 1.18 saturación en Chillán: 0 saturados en 385 + 58 gránulos, máx I04 355,96 K (2026-10-16 06:18) sin bit | `experiments/_s151_saturacion_chillan/`, verificador CONFIRMADO |
| hecho (PARCIAL) | 1.19 dependencia angular: sólo el escalón de MIROVA a 52,66° se sostiene; sin palanca | `experiments/_s151_angular_119/verificador/` |
| hecho (PARCIAL) | 1.20 techos M15 y NOAA-21: hoy no borran; techo efectivo I04 ~354 K; riesgo vivo en Chillán | `experiments/_s151_techos_120/verificador/` |
| hecho | 1.17 probe MxD03: PIERDE PROTEGIDA por la letra, pero las 2 pérdidas son A46 (etiqueta por hotspot final), no posición; MxD03 gana 9 protegidas | `experiments/_s151_mxd03_etiquetas_verif/resultado/` |
| hecho | Mirova-v1#25 (distancia aproximada) mergeado 2026-10-16 11:43 UTC (`2eac1758`); historia recalculada; hito A119 en #838 | Mirova-v1 PR #25, VRP-chile #838 |
| hecho | Evaluador diurno: G3 con tolerancia (#833); W1 informada (72 % de publicación diurna en negativos limpios V375 Láscar) | #833, `experiments/_s151_ab_diurno/salidas/38723828037_union/` |
| hecho | Cron externo del NRT en cron-job.org: primera `workflow_dispatch` 2026-10-16 13:00:12 UTC | `gh run list --workflow nrt.yml` |
| a medias | **Mirova-v1 aún no escribe `Distancia_aprox_*`**: OCR 12:00 y 12:30 en rojo en ese paso (push rechazado, caché tapada); el OCR de 13:00 es el primero con caché completa (`mirova-dist-hist-38902737639`) | Mirova-v1 runs 38897513837, 38900944678 |
| corriendo | F/K V2a intento 2 (38648773684); V1 intento 3 pendiente (38639658446); diurno W2b (38853273752); W2a intento 2 pendiente (38853230521) | `gh run view` |
| sin evaluar | F/K V1 (cobertura despareja: 31 de 44 jobs cortos), V2a, W2a: esperan sus repeticiones (D-13: repetir y unir) | `experiments/_s151_prereg_fk_11/v1_cobertura/` |
| en rama | 60 commits de `loop/activo` sin integrar a `main` (bitácora, informes, scripts de experimentos) | `git cherry origin/main loop/activo` |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Cadencia del cron externo del NRT (hoy cada 30 min desde las 10:00) | cada 30 min · `10 1-12 * * *` UTC (doc S150) · cada hora | **`10 1-12 * * *` UTC o cada hora**: el NRT dura 50 a 60 min, así que cada 30 min deja una corrida pendiente siempre, ocupa runners todo el día y retrasa los A/B (ya se vio un job esperando runner 1 h); los datos nocturnos llegan entre 01:30 y 12:00 UTC |
| 2 | Vencimiento del token `vrp-chile-cron-externo` | dar la fecha (nunca el valor) | anotarlo en `REGISTRO_CREDENCIALES.md` §2; si «nunca vence», regenerarlo con 90 días |
| 3 | 1.21: probe de tres brazos (C; MxD03; MxD03 + etiqueta desde el cúmulo) | pre-registrar · no | **pre-registrar**: es la única forma de decidir el arreglo MxD03 sin que la asimetría A46 lo vete |
| 4 | Arreglo de la caché de Mirova-v1 si el OCR de 13:00 tampoco escribe la columna | `restore-keys` que prefiera `mirova-dist-hist-` · nada | decidir sólo si 13:00 y 13:30 fallan; toca producción de Mirova-v1 |
| 5 | Pendientes de antes: sello de la sonda 1.2, cronología OVDAS y coordenadas para 1.11, Mirova-v1#23 punto 4 | entregar o esperar | la cronología OVDAS es la vara del experimental: sin ella sus detecciones extra no se pueden juzgar |

## c. Lo aprendido (destino propuesto)

1. **Los A/B largos pierden pasadas al azar por cortes de NASA (0,5 a 1,4 % por job), en todos los brazos.** Pasó en
   W1, V2a, V1 y W2a. Decisión de Nicolás (D-13): repetir y unir intentos, exigiendo records comunes idénticos
   (`experiments/_s151_ab_diurno/unir_intentos.py`). → regla A108 enmienda en `CLAUDE.md` del proyecto.
2. **Comparar floats con `!=` entre runners mide la máquina** (OpenBLAS cambia el último bit de `np.polyfit` según la
   CPU): G3 dio FALLA falsa en 179 de 183 noches. Tolerancia relativa más piso absoluto, con casos de autoprueba en los
   dos lados. → **regla general del workspace** (ya era S142; segunda vez).
3. **El verificador limpio rebajó tres resultados fuertes el mismo día** (1.19 «la agregación explica todo», 1.17
   «MxD03 pierde por la posición», 1.20 «techo 359 K»). Ninguno se habría notado sin él. → refuerza A111; sin cambio.
4. **`restore-keys` de `actions/cache` toma la caché más NUEVA del prefijo**: una caché parcial posterior tapa a la
   completa. → regla general del workspace (GitHub Actions).
5. **La distancia del OCR sí acierta el lado cráter/lejana (197 de 197 contra la tabla)**; la discrepancia de ~24 % es
   de distancia, no de lado. «No confiable para summit/far» era falso. → memoria corregida.
6. **Un subagente con hijos en segundo plano reenvía su informe**: detenerlo con TaskStop cuando ya entregó. → regla
   general del workspace (herramienta).

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | Mirova-v1: OCR 12:00 y 12:30 en rojo en el paso de distancia aproximada; el commit del OCR y la caché salieron bien | runs 38897513837, 38900944678 |
| SOSPECHA | con la caché completa, el OCR de 13:00 escribe la columna en segundos y el push ya no pierde | sin verificar |
| CONFIRMADO | las 2 protegidas que pierde MxD03 vienen de `distance_class` por hotspot final (`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`, `process_modis.py:1293-1330`) | verificador 1.17 |
| SOSPECHA | el Test 1 deja de disparar con MxD03 en esas 2 pasadas (inferido: el probe no guarda `triggered_test1` del brazo M) | verificador 1.17 |
| CONFIRMADO | `_interp_geo` también corre la posición a lo largo de la traza (2 − 0,00197·línea km) | verificador 1.17, r = 0,955 |
| CONFIRMADO | techo efectivo de I04 ~354 K en el corpus; pero 355,96 K sin bit el 2026-10-16 06:18 | 1.20 y re-medición 1.18 |
| SOSPECHA | el foco de feb-2025 a 12 a 19 km al W de Chillán es un incendio forestal | sin confirmar en la web |
| CONFIRMADO | el probe de saturación cae con `IndexError` si un tramo queda sin días (ventanas cortas) | run 38882932077 |

## e. Lo que ya está cerrado (no rehacer)

- La palanca de área por agregación VIIRS (1.19): sin palanca que pre-registrar; sólo el escalón de 52,66°.
- La saturación como causa del déficit de magnitud en Chillán: descartada (0 saturados).
- La distancia OCR como «no confiable para summit/far»: falso (197 de 197).
- La tolerancia de G3 y la unión de intentos: implementadas y verificadas (#833, `unir_intentos.py`).
- El cron externo: creado y funcionando (`workflow_dispatch` 13:00:12 UTC).
- El hito A119 de V31.1 y el de la distancia aproximada: en main (#832, #838).

## f. Prompt para la próxima sesión

```
/loop Sigue tasks/LOOP_OBJETIVOS.md del repo VRP Chile: en cada vuelta lee el archivo entero (desde la rama loop/activo), aplica su protocolo de la sección 2, ejecuta una sola tarea, anota la bitácora y commitea. No adoptes cambios en la réplica de producción (sección 1.1). Detente solo por las condiciones de la sección 1.5.

Antes de la primera vuelta: lee tasks/BLOQUE_ARRANQUE_S152.md y las entradas de la bitácora desde la vuelta 93. Verifica contra el remoto antes de creerle a nada (gh run view, gh api). Luego, en este orden:
1. Mirova-v1: comprueba que el OCR desde las 13:00 UTC del 2026-10-16 escribe Distancia_aprox_* en registro_vrp_ocr.csv con Distancia_km intacta byte a byte. Si no, diagnostica (restore-keys de la caché, push rechazado) y propónme el arreglo; no toques producción sin mi sí.
2. D-13 (repetir y unir): cuando terminen F/K V1 intento 3 (run 38639658446), V2a intento 2 (38648773684) y W2a intento 2 (38853230521), une los intentos de cada brazo con experiments/_s151_ab_diurno/unir_intentos.py, cuenta cobertura con el instrumento de cada pre-registro, y si queda pareja evalúa (evaluar_fk.py, evaluar_diurno.py) y pasa verificador limpio. Si sigue despareja, otra vuelta. No despaches V2b ni W3 mientras haya un pendiente en su grupo.
3. Pre-registra la 1.21 (MxD03 con etiqueta desde el cúmulo, tres brazos más ruido) y pásala por verificador limpio antes de pedirme el sello.
4. Revisa el paper en docs/paper/ (sec4_background, sec5_methods, sec6_validation, numbers.json, editados por última vez el 2026-09-15) contra lo que cambió desde entonces (A113): distancia OCR, corrimiento MODIS y MxD03, saturación, agregación VIIRS, criterio de alerta protegida. Entrega un informe de cambios propuestos; no reescribas sin mi visto bueno.
5. Arregla el IndexError del probe de saturación con tramos sin días.
Esperan mi decisión: cadencia del cron externo (recomendado 10 1-12 * * * UTC), vencimiento del token, MxD03 en producción (después de la 1.21), Mirova-v1#23 punto 4.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué run quedó sin evaluar, y para.
```
