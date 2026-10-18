# Bloque de arranque S154 (cierre de S153, sesión «retomar» + loop, vueltas 172 a 193)

Escrito el 2026-10-18 06:07 UTC (hora del servidor) sobre `loop/activo` en `95e36a29` (igual al remoto); `main` en
`a2032623`. **Se fijó con trabajo en curso:** el A/B diurno W6a (run 39090434307, 12 de 22 jobs) corre y W6b (run
39097155412) espera detrás. Ningún agente ni proceso local vivo. El bloque S153 queda como histórico. La bitácora
completa está en `tasks/LOOP_OBJETIVOS.md` §6 (vueltas 172 a 193); ante discrepancia manda la bitácora y, por encima,
el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | #847 (G3 del diurno y `unir_intentos`: `borde` sólo si el recorte cortó y sólo con píxeles del VRP mínimo) mergeado | `2766c198`; mutaciones 15 de 15, autoprueba 69 de 69 |
| hecho | Regla de adopción de K escrita y aprobada por Nicolás ANTES de evaluar V2 | #848 (`cf507f46`), `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` |
| hecho | F/K V1 re-evaluada y V2 evaluada con el instrumento fijado `2766c198`: **K lectura A CUMPLE** (original y SN) | `experiments/_s153_fk_v2/` (README, v1/v2/combinado.log) |
| hecho | Ciclo de la regla: verificador CONFIRMADO, R3 idéntico, cruce de 1 MW ninguno, A61 sin protegidas a otro objeto, segundo lector 4 de 4 lejanas, R2 5 de 5, K sobre `main` 56 de 56 iguales | `experiments/_s153_fk_v2/{verificador,r3,a61,lector2,r2}/`, `k_main_contra_tag_salida.txt` |
| **en rama, sin mergear** | **PR de adopción de K** (#850): 3 flags, 46 perfiles derivados congelados en C0, guards, ficha SDA v1.9, marcas A113, historial del auto-audit, `frontend/cambio_detector.js`; CI verde, CLEAN | #850 (`e0d3ebfd`), tag `pre-s153-adopcion-k` (`5849ee65`) |
| hecho | Tablero: selector de noche o rango en las tres vistas, clic en barra, mapa con el criterio del gráfico; publicado y R8 | #849 (`60c45833`) |
| hecho | 1.23 completa: MxD03 ubica mejor el calor en Láscar (dd 0,62 km), no adoptable por la letra; D-19 | `experiments/_s151_mxd03_sola_123/resultado/` (verificador CONFIRMADO) |
| hecho | 1.23 bis: la deriva de 8 records MODIS son los gates intra-radio (2026-05-28 a 07-01), 3.231 records MODIS de ene a jun 2026 escritos con ellos | `experiments/_s153_deriva_123bis/` (verificador CONFIRMADO); A85 marcada |
| hecho | Localización: la sobre-publicación y la mala posición de VIIRS 375 son el mismo mecanismo (Test 1, borde del disco de 3 km); con K se juntan en el cráter | `experiments/_s153_localizacion/` (POR VERIFICAR) |
| hecho | Diurno: W5 completa y pareja (W5a unida 1.199 contra 1.199 con desviación D-22; W5b verde) | `C:\Users\nmend\AppData\Local\Temp\claude\w5a_39032518643\union\` (temporal: rehacer con `experiments/_s153_fk_v2/unir_ventana.py` si se pierde) |
| corriendo | Diurno W6a (2026-10-01 a 10-07) y W6b (10-08 a 10-14), `--ref s151-diurno-codigo` | runs 39090434307 y 39097155412 |
| a medias | Evaluación del diurno (W2 a W6) con `evaluar_diurno.py` y verificador | espera W6 |
| corriendo bien | NRT verde cada hora desde las 04:10 UTC (cron externo); último dato 04:38 UTC | `gh run list -w nrt.yml` |

Los temporales (`C:\Users\nmend\AppData\Local\Temp\claude\*`) con las uniones de V1, V2a, V2b y W5a no están en el
repo: se rehacen con `experiments/_s153_fk_v2/unir_ventana.py` desde los artefactos de los runs.

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| D-21 | **Merge de la adopción de K (#850)** | sí · no | **sí**: cumple la regla aprobada entera; reversión pre-autorizada por `git revert` |
| D-21b | Auto-audit con K (magnitud VIIRS 375 0,669 bajo la banda [0,7; 1,4]; recall por pasada ~92-94 %) | recalibrar · aceptar que salte | **aceptar las primeras semanas**: recalibrar sin datos de producción con K sería inventar un umbral (A115) |
| D-21c | `experimental_lowT` y `experimental_ndc_focus` quedaron congelados en C0 como `experimental` | dejar · que sigan a la réplica | dejar (son laboratorios) |
| D-21d | Aviso a OVDAS e Integracion_Plataformas del cambio de detector | lo envía Nicolás | enviarlo el día del merge |
| D-22 | Ratificar la desviación de W5a (intento 2 entero en Llaima diurno: 2 records diurnos VIIRS 375 distintos por empate del top-100, mismo predicado y mismo cúmulo); y extender a VIIRS el desempate de #844 | ratificar · repetir | ratificar; el desempate VIIRS como tarea propia (A45) |
| D-23 | Reprocesar los 3.231 MODIS de ene a jun 2026 escritos con los gates intra-radio | ahora · dentro del reproceso con K | **dentro del reproceso histórico con K** si se adopta #850 |
| D-19 | MxD03 en producción | sobre C0 · sobre K | pre-registrarla **sobre K** (sus 2 pérdidas son el Test 1, que K quita) |
| cron | cron-job.org lee `10 1-12 * * *` en hora de Chile (04:10 a 15:10 UTC): deja fuera la ventana MODIS de 01 a 03 UTC | zona UTC · `10 22-23,0-9 * * *` en Chile | poner la zona horaria del trabajo en UTC |
| 1.11 | Cronología OVDAS de Chillán y coordenadas de Cerro Blanco, Pichi-Llaima, Lazufre, El Agrio | entregar · esperar | entregarlas (vara del experimental) |
| #776 | Sello de la sonda de tres campos (1.2) | sellar · cerrar | revisar si sigue teniendo sentido con K adoptada |

## c. Lo aprendido (destino propuesto)

1. **Una sola sesión dueña del loop.** Hoy la sesión de S152 seguía viva con un agente que editaba el worktree del
   #847 mientras S153 lo verificaba: una corrida de mutaciones de más de una hora quedó inválida (A112) y casi se
   duplicaron despachos. `/cierre` debe detener los agentes antes de cerrar, y `LOOP_OBJETIVOS.md` debería llevar una
   línea «dueño: sesión X». → **regla general del workspace** (memoria `feedback_s153_una_sesion_duena_del_loop.md`).
2. **La regla de adopción va dentro del pre-registro, antes del resultado.** Con #848 la medición terminó en decisión
   en una noche, después de un mes y medio midiendo `max`. → `CLAUDE.md` del proyecto (propuesta) y plantilla de
   pre-registro.
3. **Un perfil derivado hereda en silencio el cambio de producción.** Al adoptar K, 46 perfiles `extends:
   mirova_equivalent` cambiaban de significado (los C0 de A/B ya evaluados). Congelarlos con los flags escritos y un
   guard (`tests/test_guard_perfiles_congelados_s153.py`). → A117 ya lo dice; agregar el caso.
4. **Un flag apagado sin reproceso deja el corpus con dos detectores** (1.23 bis: gates intra-radio, 3.231 records). →
   A104/A85 (marcada); regla: todo flip de flag de detección lleva reproceso o marca de régimen.
5. **cron-job.org interpreta la expresión en la zona horaria del trabajo**, no en UTC. → **regla general del
   workspace** (memoria `reference_cronjob_org_zona_horaria.md`).
6. **Pedir la hora al servidor antes de cada entrada (A86)**: en S153 se escribieron tres horas estimadas en el futuro.
   Sin regla nueva; reforzar.
7. **El control de cableado de `evaluar_fk.py` exige los 11 volcanes por carpeta de logs**: una repetición parcial
   necesita unir logs (desviación documentada en `experiments/_s153_fk_v2/README.md`). → proyecto.
8. **Heredocs con rutas de Windows rompen scripts** (otra vez). Sin regla nueva.

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | K cumple la regla de adopción en V1 y V2 (verificador y R3 independientes) | `experiments/_s153_fk_v2/` |
| CONFIRMADO | 3.231 MODIS ene a jun 2026 escritos con los gates intra-radio; 2025 escrito por el backfill S120 después del flip | `experiments/_s153_deriva_123bis/verificador/` |
| CONFIRMADO | El desempate del top-100 sigue sin ser estable en VIIRS (#844 sólo MODIS) | W5a Llaima, bitácora vuelta 189 |
| CONFIRMADO | cron-job.org despacha en hora de Chile | NRT `workflow_dispatch` a las 04:10 y 05:10 UTC |
| SOSPECHA | Con K la posición publicada de VIIRS 375 se junta en el cráter en casi todos los volcanes (Villarrica 2,75 a 0,18 km) | `experiments/_s153_localizacion/`, sin verificador |
| SOSPECHA | Deriva de los gates también en VIIRS (~4.500 records expuestos), probablemente chica | verificador de la deriva |
| SOSPECHA | Tupungatito 2026-09-29: punto tenue cerca del cráter en la miniatura de MIROVA | `experiments/_s153_fk_v2/lector2/INFORME.md` |
| abierto | Magnitud baja con K (VIIRS 375 0,669); D25 es la palanca siguiente, re-pre-registrar sobre K | regla §5 |

## e. Lo que ya está cerrado (no rehacer)

- La regla de adopción de K y su evaluación: no se reabren; el instrumento quedó en `2766c198`.
- El G3 del diurno y `unir_intentos` (#847): `borde` acotado; no tocar sin verificador.
- El tablero con selector de período (#849): publicado y verificado.
- La 1.23: MxD03 mejor posición, no adoptable sobre C0 (D-19 decide cómo seguir).
- La 1.23 bis: causa encontrada y confirmada (no es un commit de código).
- El NRT: retomó cada hora; no hay caída.

## f. Prompt para la próxima sesión

```
/retomar

Luego, en el repo VRP Chile (rama loop/activo), antes de creerle a nada: git fetch; gh pr view 850; gh run view 39090434307 y 39097155412 (diurno W6a y W6b); gh run list -w nrt.yml -L 3; pide la hora al servidor.
Lee en orden: tasks/BLOQUE_ARRANQUE_S154.md, la bitácora de tasks/LOOP_OBJETIVOS.md desde la vuelta 186, experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md.
Trabajo, en orden:
1. Si Nicolás dio el sí a #850: comprueba CI verde y CLEAN, mergea, completa CAMBIO_DETECTOR_UTC en frontend/cambio_detector.js con la hora del merge (PR aparte, CI, merge), y prepara el reproceso con K de la ventana por defecto del tablero (30 días, jobs partidos, A15) y luego el histórico (incluye los 3.231 MODIS de D-23). Después R8 y la sombra (§4.9 de la regla: laboratorio congelado en C0, hasta 29 protegidas, reversión con git revert si se pierde una protegida que la sombra publica).
2. Diurno: cuando W6a y W6b terminen, contar cobertura, repetir y unir si hace falta (experiments/_s153_fk_v2/unir_ventana.py), juntar W2 a W6 y evaluar con evaluar_diurno.py; verificador limpio.
3. Pasar verificador limpio a experiments/_s153_localizacion/ antes de citarlo.
4. Pre-registrar D25 sobre K (regla §5) y MxD03 sobre K (D-19) si Nicolás lo aprueba.
Reglas duras: no adoptar nada en producción sin el sí explícito de Nicolás (A45); una sola sesión dueña del loop; pedir la hora al servidor antes de cada entrada (A86); verificador limpio antes de aceptar un resultado; sin guiones largos ni medios; rutas absolutas al informar.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué run quedó sin evaluar y corre /cierre.
```
