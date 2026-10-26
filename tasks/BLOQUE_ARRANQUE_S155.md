# Bloque de arranque S155 (cierre de S154: «retomar» + loop, vueltas 195 a 217)

Escrito el 2026-10-19 ~03:50 UTC (hora del servidor) sobre `loop/activo` en `b4242112` (igual al remoto); `main` en
`4877788b`. **Se fijó con trabajo en curso en GitHub** (no escribe en esta rama): el reproceso histórico con K
(run 39125546355, 99 de 176 trozos a las 03:44) y un NRT en cola (39194422201). Ningún agente ni proceso local vivo. El
plan acordado con Nicolás para esta sesión está en `tasks/PLAN_S155.md`; la bitácora completa en
`tasks/LOOP_OBJETIVOS.md` §6 (vueltas 195 a 217). Ante discrepancia manda la bitácora y, por encima, el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | **K en producción**: Test 1 integrado apagado, conectiva `max`, banda 22 MODIS (D-21, sí de Nicolás) | #850, squash `34cea39e` a las 09:57:30 UTC del 2026-10-18; CI de `main` verde |
| hecho | Marca del cambio de detector en las tres vistas, con la hora del merge | #851; R8: aviso visible en el tablero público |
| hecho | Reproceso con K de los últimos 30 días (2026-09-18 a 10-18) | run 39117638055; `experiments/_s154_reproc_k/ventana_30d.json`: 3.521 de 3.577 con K, 0 perdidas, 0 cambiadas fuera |
| hecho | 56 pasadas de esa ventana sin K: Terra irrecuperable (huecos del archivo estándar de NASA), NOAA-21 del 18-oct ya rehechas por el NRT | bitácora vuelta 200; consulta CMR `MOD021KM` con control del 9-oct |
| corriendo | **Reproceso histórico con K** 2025-02-15 a 2026-09-17, por trozos en perfil aislado | run 39125546355 (`reproc-chunked.yml`, `_s154_reproc_k_historico`); #852 (perfil, `scripts/reemplazar_ventana_reproceso.py`, 11 tests) |
| hecho | Marcador del mapa de detalle = cúmulo publicado en `ctx_cluster` (D-24, sí de Nicolás) | #853; R8: Láscar 2026-10-18 05:06 pasó de 24,7 a 1,0 km; capturas en `experiments/_s154_marcador/` |
| hecho | A/B diurno W2 a W6 sobre C0: **NO ADOPTAR**, verificador PARCIAL: no se traslada a K | `experiments/_s151_ab_diurno/salidas/W2_W6_s154/` (evaluación y verificador) |
| hecho | Adenda del pre-registro del diurno sobre K, **sellada por Nicolás** (cola exacta en G1; «cumple sin W2, falla con W2» = decide Nicolás con M4) | #857; `experiments/_s151_ab_diurno/ADENDA_K.md` |
| hecho | Infraestructura del A/B diurno sobre K: perfiles, `--brazos`/`--base k`, workflow sin nombre fijo; aviso A114 por sensor; nulo determinista | #856, #854, #855 |
| **a medias** | **Candado de la adenda** (cola exacta, regla W2, H2a, H2b) mergeado, pero **las pruebas no alcanzan**: 11 de 42 mutaciones no atrapadas, 4 pasan la batería completa | #858 (`cf272543`); `experiments/_s151_ab_diurno/verificador_candado_k_v2/INFORME.md` |
| hecho | Verificador de localización: la tesis «K junta las detecciones en el cráter» REFUTADA (K no relocaliza, deja de publicar las del borde) | `experiments/_s153_localizacion/verificador/INFORME.md` |
| hecho | Chillán 2026-10-18: 10 de 10 alertas nocturnas de MIROVA detectadas; magnitud 0,12 a 0,72 que cae con el cenit; mecanismo SIN ATRIBUIR (D25 y D17 compiten) | `experiments/_s154_chillan/razon_por_cenit.py` y su salida; tarea 1.33 |
| borrador | Índice por síntoma (9 síntomas, tres contradicciones entre fuentes) | `experiments/_s154_sintomas/SINTOMAS_borrador.md` (sin verificar, sin PR) |
| hecho | cron-job.org en UTC, comprobado | despacho del NRT a las 02:10:21 UTC del 2026-10-19 |
| hecho | Dos discos: worktrees y temporales grandes en `D:\vrp-trabajo\`, repo en C: | protocolo §2 de `tasks/LOOP_OBJETIVOS.md`; probado con un worktree de prueba |

Discos al cierre: C: 32 GB libres, D: 22 GB libres. Los worktrees `s153-adopcion` y `s154-marcador` (ramas ya
integradas en `main` por squash, comprobado por contenido) se borraron en este cierre.

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Cronología OVDAS de Chillán: fases y dónde está hoy el foco activo (cráter, flujo, domo) | entregar · esperar | **entregarla**: sin ella no se puede saber si las distancias de MIROVA de hasta 2,7 km son un flujo real; también es la vara del experimental (1.11) |
| 2 | Sello del pre-registro de D25 sobre K con Chillán como caso (1.29), cuando esté escrito | sellar · pedir cambios | revisarlo con el desglose de la auditoría post-K (frente 5) antes de sellar |
| 3 | Rotar el PAT de GitHub y avisar a OVDAS del cambio de detector | hacerlo · postergar | hacerlo esta semana (el aviso a OVDAS se debía el día del merge, 2026-10-18) |
| 4 | #813 (D-10) y #776 (sonda de tres campos) | mantener abiertos · cerrar | #813 abierto hasta el A/B diurno sobre K; #776 revisar si tiene sentido con K |

## c. Lo aprendido (destino)

1. **El conocimiento está indexado por número y por sesión, no por síntoma; las correcciones viven donde se
   corrigió, no donde se cita primero.** Atribuí el déficit de Chillán a D25 sin estratificar, y luego a D17 citando
   S130, cuando la tarea 1.14 ya había retirado «el ángulo es D17». → índice por síntoma (1.34) y regla de leer todas
   las fuentes posteriores antes de atribuir. Memoria `feedback_s154_estratificar_por_cenit`. **Regla general.**
2. **Ningún número llega al dueño sin script commiteado.** La tabla de Chillán vivió una hora sólo en la
   conversación. → acuerdo de proceso (`tasks/PLAN_S155.md`), memoria `feedback_s154_duracion_sesion`. **Regla general.**
3. **Sesiones largas pierden lo que está en el repo.** Acuerdo: cerrar a ~30 intercambios o tras dos hitos grandes.
   **Regla general.**
4. **El verificador limpio encontró algo real las cinco veces** (marcador del mapa, atribución de localización,
   no-traslado del diurno a K, huecos del candado dos veces). Mantenerlo obligatorio. Proyecto.
5. **Una mutación que hace caer el evaluador no está atrapada** (S152, se repitió con `--sha-codigo`): la defensa es
   que la condición se informe como problema, no que el programa se caiga. Proyecto (ya en memoria S152).
6. **Leer un resumen parcial de mutaciones da conteos equivocados**: dije «5 no atrapadas» y eran 12 en la corrida
   filtrada. Contar desde la salida completa. Proyecto.
7. **OneDrive no sincroniza** (ruta heredada) y desde hoy se usan los dos discos. Memoria
   `reference_onedrive_no_sincroniza`. **Regla general.**
8. **cron-job.org lee la expresión en la zona del trabajo**: ya en UTC y comprobado. Memoria
   `reference_cronjob_org_zona_horaria`. **Regla general.**
9. **Una espera colgada (`gh pr checks --watch`) no es un CI pendiente**: mirar el run con conclusión. Proyecto.

Pendiente de la sesión, no hecho en este cierre: **adelgazar el `CLAUDE.md` del proyecto** (acordado; va al bloque 2
de `tasks/PLAN_S155.md`, porque hacerlo con el contexto de esta sesión ya cargado era arriesgar el mismo error de hoy).

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | Las pruebas del candado no protegen la regla sellada: 11 de 42 mutaciones no atrapadas (`g1_regla_inversa`, `h2a_solo_primera_raiz`, `h2a_solo_lascar`, `h2a_solo_diurno` pasan 107 de 107); ninguna prueba distingue cola exacta de p95 muestreado | `verificador_candado_k_v2/INFORME.md`, `m1_salida.txt`, `m4_reglas_discrepan_salida.txt` |
| CONFIRMADO | Con el código de hoy el evaluador decide con la regla sellada | mismo informe, corridas reales `real_c0_salida.txt` y `real_basek_salida.txt` |
| CONFIRMADO | El catálogo `docs/MIROVA_DIVERGENCES.md` no registra K (#850): D21 sigue «ABIERTA» (A113) | borrador del índice por síntoma; tarea 1.37 |
| CONFIRMADO | Chillán: la razón de magnitud cae con el cenit del sensor | `experiments/_s154_chillan/razon_por_cenit_salida_20261018.txt` |
| SOSPECHA | El mecanismo de esa curva es mayormente el fondo (D25), porque su efecto crece con el ángulo (1.14 Tabla C2) | sin verificar sobre K ni sobre Chillán |
| SOSPECHA | VIIRS 750 de las 06:48 en Chillán (0,12) es selección de cúmulo, además del ángulo | sin verificar |
| SOSPECHA | El marcador del mapa tiene otros defectos con K en diario y mosaico | sin auditar (frente 2) |

## e. Lo que ya está cerrado y no hay que rehacer

- Adopción de K (#850) y su marca (#851): en producción; reversión pre-autorizada sólo por pérdida de protegida en la
  sombra (regla §4.9).
- Reproceso de 30 días con K: verificado. Las pasadas Terra sin K de esa ventana no tienen de dónde reprocesarse.
- El A/B diurno sobre C0: NO ADOPTAR medido y verificado; no se reabre, se repite sobre K.
- La adenda del diurno sobre K: sellada; no se cambia el criterio.
- Marcador del mapa en `ctx_cluster` (#853): arreglado y publicado.
- La tesis de que K relocaliza las detecciones: refutada.
- cron-job.org en UTC: comprobado.

## f. Prompt para la próxima sesión

```
/retomar

Luego, en el repo VRP Chile (rama loop/activo), antes de creerle a nada: git fetch --prune; pide la hora al servidor (gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date); gh run view 39125546355 (histórico con K); gh run list -w nrt.yml -L 3 (los despachos tienen que salir a :10 UTC desde las 01:10); df -h /c /d.
Lee en orden: tasks/BLOQUE_ARRANQUE_S155.md, tasks/PLAN_S155.md, la bitácora de tasks/LOOP_OBJETIVOS.md desde la vuelta 213, experiments/_s151_ab_diurno/verificador_candado_k_v2/INFORME.md.
Trabajo, en orden (el plan tiene el detalle):
1. Cerrar las pruebas del candado del A/B diurno sobre K: N-1 a N-5, H-3 (regla) y H-5; repetir las 42 mutaciones con m1_mutaciones_v2.py del verificador hasta que todas caigan por prueba (ninguna por caída); tercera vuelta corta de verificador limpio. No despachar antes.
2. Auditoría post-K: 5 frentes en paralelo, cada uno con su verificador limpio y su worktree en D:\vrp-trabajo\worktrees\ (propagación de K, lo que ve el operador, instrumentos, cierres que K volvió falsos, magnitud de Chillán pasada por pasada). Preámbulo de ../../GUIA_MAESTRA_AUDITORIAS.md §5 entero.
3. Memoria del proyecto: índice por síntoma (revisar experiments/_s154_sintomas/SINTOMAS_borrador.md, verificador, PR a docs/SINTOMAS.md, paso nuevo en el protocolo §2); adelgazar el CLAUDE.md del proyecto (unas 20 reglas vinculantes con su porqué, el resto a un documento buscable); estratificación automática por cenit y régimen (1.35).
4. Cuando termine el histórico: ensayo del reemplazo por volcán, verificador, aplicar en un commit entre NRT, verificar_ventana.py y R8. Después, despacho del A/B diurno sobre K desde un tag (sha con git rev-parse <tag>^{commit}).
5. Pre-registro de D25 sobre K con Chillán como caso (1.29) para el sello de Nicolás; D17 como competidora después (1.36).
Reglas duras: no adoptar nada en producción sin el sí explícito de Nicolás (A45); una sola sesión dueña del loop; ningún número a Nicolás sin script commiteado; antes de atribuir un mecanismo, leer el síntoma y TODAS las fuentes posteriores y estratificar por cenit, sensor, volcán y régimen; verificador limpio antes de aceptar un resultado; worktrees y temporales grandes en D:\vrp-trabajo\; cerrar a ~30 intercambios o tras dos hitos; sin guiones largos ni medios; rutas absolutas al informar.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué quedó corriendo y corre /cierre.
```
