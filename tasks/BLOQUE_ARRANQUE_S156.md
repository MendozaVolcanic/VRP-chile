# Bloque de arranque S156 (cierre de S155: «retomar» + loop, vueltas 218 a 222)

Escrito el 2026-10-19 a las 11:31 UTC (hora del servidor) sobre `loop/activo`; `main` en `dd1c0b7b` (#861) más los
commits del NRT. **Se fijó con trabajo en curso en GitHub**, que no escribe en esta rama: el reproceso histórico con K
(run 39125546355, 141 de 177 trozos, todos verdes, a las 11:31) y el NRT de cada hora (cron-job.org a :10 UTC). Ningún
agente ni proceso local vivo; ningún worktree aparte de la raíz. Bitácora completa en `tasks/LOOP_OBJETIVOS.md` §6
(vueltas 218 a 222); el bloque anterior, `tasks/BLOQUE_ARRANQUE_S155.md`, queda como histórico. Ante discrepancia manda
la bitácora y, por encima, el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | **Candado del A/B diurno sobre K cerrado**: 72 mutaciones (42 del verificador v2, 30 del v3), 71 atrapadas por prueba, 0 por caída, 1 equivalente demostrada (`xobs_techo`, 0 diferencias en 12.502.499 pares); batería completa 138 de 138 | #859, squash `e66b402c`; `experiments/_s151_ab_diurno/candado_k_s155/m6_final_salida.txt`, `xobs_techo_equivalente_salida.txt`; verificador v3 en `experiments/_s151_ab_diurno/verificador_candado_k_v3/INFORME.md` (rama `loop/activo`) |
| hecho | **Tag de despacho** `s154-diurno-k-codigo` (objeto `26a8398c`, commit `e66b402c70b1c97cb8164bc05e33a70d63501c9d`); procedimiento en `experiments/_s151_ab_diurno/DESPACHO_K.md` | `git ls-remote --tags origin s154-diurno-k-codigo` |
| **NO despachado** | A/B diurno sobre K | espera el fin del histórico y su reemplazo (1.24), adenda K §4 |
| hecho | **Auditoría post-K**: 5 frentes, cada uno con su verificador limpio | #861, squash `dd1c0b7b`; `docs/AUDIT_S155.md`, `experiments/_s155_audit/` |
| hecho | **Marca del cambio de detector en la frontera de los datos** (fecha de observación 2026-09-18, no el merge del 18-oct) con prueba contra los JSON | #860, squash `67122696`; `tests/test_cambio_detector_frontera_s155.py`; verificado en el tablero público (Copahue, `diario.html`) |
| corriendo | Reproceso histórico con K (2025-02-15 a 2026-09-17) | run 39125546355, 141 de 177 a las 11:31 UTC, unos 6 trozos por hora |
| abierto | Arreglos 2 a 7 de `docs/AUDIT_S155.md` §5 (régimen en el auto-audit y las vistas, protegidas, código de la sombra, propagación de K en textos, magnitud en erupción, watchdog) | sin empezar |

Discos al cierre: C: 23 GB libres, D: 22 GB libres. C: bajó de 33 a 22 GB entre las 03:48 y las 10:40 UTC sin causa
encontrada (ver d).

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Orden de los arreglos de la auditoría (`docs/AUDIT_S155.md` §5) | 2 y 3 juntos ya · otro orden | **2 y 3 juntos antes del auto-audit del lunes 2026-10-20**: separar C0 y K en el auto-audit y listar las protegidas. Si no, el lunes abre un issue con 2 flags (Chillán, Tupungatito) que son mezcla de detectores, sumado al #779 |
| 2 | Cierres medidos bajo C0 (frente 4: D22, D25, D2 con `conditioned`, A98, A103, A117) | re-medir sobre K los que apagan frentes vivos · dejarlos SIN EVIDENCIA | re-medir sólo D22/D25 (ya hay pre-registro 1.29 en camino) y D2 (sostiene 17 a 31 % de lo publicado con K); marcar los demás SIN EVIDENCIA con A113 |
| 3 | Modo de un píxel y selección `vent_anchored` en erupción (F5-01) | pre-registro · dejarlo descrito | pre-registro junto con D25 (1.29), referencia de MIROVA fijada por hash (V5-03); toca `pipeline/` (A45) |
| 4 | Cronología OVDAS de Chillán (fases y foco activo) | entregar · esperar | entregarla: sin ella no se interpretan las distancias de MIROVA ni el experimental (1.11) |
| 5 | Rotar el PAT de GitHub y avisar a OVDAS del cambio de detector | hacerlo · postergar | hacerlo: el aviso a OVDAS se debía el 18-oct; ahora además con la fecha correcta de los datos (18-sep) |
| 6 | #824 (watchdog) y #779 (auto-audit) | cerrar · mantener | #824: cerrar con el hallazgo F3-10 (mide el run, no el job) y abrir la tarea del arreglo; #779: mantener hasta el arreglo 2 |

## c. Lo aprendido

1. **Un aviso de cambio de régimen se ancla a los datos, no al código** (regla general del workspace). La marca de K
   quedó en la hora del merge mientras un reproceso ya había reescrito con K los 30 días anteriores: el operador veía a
   Copahue «dejar de tener anomalías» el 18-sep sin marca. Lo encontraron por separado cuatro agentes. Arreglo: la
   frontera se declara en la fecha de observación y una prueba la mide contra los datos, de modo que se pone roja
   cuando un reproceso la mueve. Destino: memoria `feedback_s155_marca_en_los_datos` y este bloque.
2. **Una mutación que antes caía por prueba puede pasar a caer por caída por un arreglo propio**: el chequeo nuevo de 40
   caracteres hizo reventar `sha_opcional`. Defensa: que cada rechazo dé su motivo y la prueba lo mire. Proyecto
   (bitácora vuelta 218).
3. **Mutación equivalente se demuestra, no se descarta**: `xobs_techo` se dio por equivalente con un barrido de 12,5
   millones de pares y un control positivo. Proyecto.
4. **Convergencia de agentes independientes como señal y verificador como corrector de números**: cuatro llegaron a la
   frontera por vías distintas; los verificadores refutaron o corrigieron números del auditor en los cinco frentes
   (F4-07 V750, F5-01 factores, F3-01 flags). Mantener el verificador obligatorio. Proyecto (ya en el plan S155).
5. **Predecir un instrumento exige la misma referencia que usará**: con el snapshot del 14-oct el auto-audit daba 3
   flags; con la referencia fresca que baja el cron, 2 (V3-01). Refuerza `feedback_s139_fuente_curada_y_loader_filtro`.
   Regla general.
6. **Los escapes en heredocs volvieron a romper un archivo** (`\v` de `D:\vrp-trabajo` se volvió un carácter de control
   en la bitácora). Tercera vez. Para texto con barras invertidas: herramienta de edición o script escrito a archivo,
   nunca un heredoc en línea. Memoria `feedback_s144_heredoc_y_grep_cortan` actualizada. Regla general.
7. **Horas estimadas sin preguntar al servidor** (A86): escribí «~14:30» en una vuelta de las 11:19. Corregido contra
   los commits. Proyecto (A86 ya existe).

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | El auto-audit mezcla C0 y K: 31,1 % de publicación en negativos de VIIRS 375 = C0 86,5 % y K 1,8 %; va a `history.jsonl` y es unas 8 veces la cota de la sombra | `docs/AUDIT_S155.md` F3-02 |
| CONFIRMADO | Dos protegidas MODIS de Chillán (2026-10-12 07:20, 2,18 MW; 2026-10-15 01:05, 1,72 MW) sin detección con K y sin instrumento que las vea | F3-04, F5-05 |
| CONFIRMADO | Chillán se ve un nivel bajo MIROVA (24 de 38 Moderado como Bajo o Muy Bajo); depende del cenit | F2-02 |
| CONFIRMADO | Cúmulo parcial en VIIRS 750 y MODIS: 36 % del déficit es el modo de un píxel y 64 % la selección | F5-01 |
| CONFIRMADO | La vigilancia de la sombra, disparador de la reversión pre-autorizada, no tiene código | V1-04 |
| CONFIRMADO | Nadie lee `regimen.codigo_sha` (vistas ni instrumentos) | F2-12, F3-09 |
| CONFIRMADO | 26 MODIS Terra C0 sin reprocesar dentro de la ventana K; 2 publicados en PCC con RUTINA de MIROVA | F2-08, F4-02 |
| CONFIRMADO | `test_guard_libro_de_pruebas_s146.py` g1d y g2c fallan en este computador también sin los cambios de la sesión; el CI no | bitácora vuelta 222 |
| SOSPECHA | La caída con el ángulo en VIIRS 375 es del área (D17), no del fondo | F5-03 (con fondo cero la curva sigue cayendo; la causa no está medida) |
| SOSPECHA | Los fragmentos de VIIRS 750 son huellas solapadas: «sumar todo» también contaría doble | V5-02 |
| SOSPECHA | La alerta de Copahue del 2026-10-16 06:18 que el tablero oculta como lejana es el mismo objeto que vio MIROVA | V2-01 |
| SOSPECHA | El `GITHUB_SHA` de un despacho desde el tag anotado es el commit (la documentación lo dice; no probado en un run) | verificador v3 del candado |
| SIN ATRIBUIR | C: bajó 10 GB en la mañana del 2026-10-19 | no viene de los worktrees (D:) ni del scratchpad de Poleras (quieto desde 01:19) |

## e. Lo que ya está cerrado y no hay que rehacer

- El candado del A/B diurno sobre K: 71 de 72 por prueba, 1 equivalente; no se vuelve a verificar salvo que cambie
  `evaluar_diurno.py` entre el tag y la evaluación (condición del verificador v3).
- La frontera C0/K de los datos (2026-09-18) y su marca en el tablero: medida, verificada por tres verificadores,
  publicada.
- La auditoría post-K: 10 informes con scripts; no se re-audita, se arregla en el orden de §5.
- El #779 es ventana rodante (reproducido desde commits viejos), con un cambio de nivel dentro de C0 (F3-05).
- Lo que los verificadores refutaron: F4-07 en VIIRS 750 (0,418 a 0,418 en el par), «A98 se invirtió», los factores
  ×1,46/×1,92 de F5-01, «el revert deja el aviso diciendo K».

## f. Prompt para la próxima sesión

```
/retomar

Luego, en el repo VRP Chile (rama loop/activo), antes de creerle a nada: git fetch --prune; hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date); gh run view 39125546355 (histórico con K: ¿terminó?); gh run list -w nrt.yml -L 3; gh run list -w audit-weekly.yml -L 2 y gh issue list (¿abrió el auto-audit del lunes un issue nuevo?); df -h /c /d.
Lee en orden: tasks/BLOQUE_ARRANQUE_S156.md, docs/AUDIT_S155.md (§5 arreglos y §6 decisiones), la bitácora de tasks/LOOP_OBJETIVOS.md desde la vuelta 218.
Trabajo, en orden (salvo que Nicolás decida otro en la tabla b):
1. Arreglos 2 y 3 de AUDIT_S155 §5: el auto-audit separa C0 y K por regimen.codigo_sha y estratifica (sensor dentro del volcán, cenit, D-9, cráter contra publicación), y lista cada alerta protegida sin publicar. Sin tocar pipeline/. Prueba primero, verificador limpio, PR.
2. Arreglo 4: código de la vigilancia de la sombra (el disparador de la reversión pre-autorizada de K).
3. Cuando termine el histórico: ensayo del reemplazo por volcán, verificador, aplicar entre NRT, verificar_ventana.py y R8. Al aplicarlo, tests/test_cambio_detector_frontera_s155.py se pondrá rojo: mover DATOS_K_DESDE_UTC en frontend/cambio_detector.js en el mismo PR. Después, despacho del A/B diurno sobre K desde el tag s154-diurno-k-codigo con --sha-codigo e66b402c70b1c97cb8164bc05e33a70d63501c9d (experiments/_s151_ab_diurno/DESPACHO_K.md).
4. Pre-registro de D25 sobre K con Chillán (1.29) usando experiments/_s155_audit/frente_5*/ y la referencia fijada por hash; F5-01 (modo de un píxel, selección) como parte o como pre-registro aparte; para el sello de Nicolás.
5. Propagación de K en los textos (arreglo 5, frente 1), en el orden: tablero, ficha SDA, CLAUDE.md y MISSION, encabezados del catálogo, cabeceras de código, INDEX.
Reglas duras: no adoptar nada en producción sin el sí explícito de Nicolás (A45, tag defensivo); una sola sesión dueña del loop; ningún número a Nicolás sin script commiteado; la hora se pide al servidor, no se estima (A86); antes de atribuir un mecanismo, leer el síntoma y todas las fuentes posteriores y estratificar por cenit, sensor, volcán y régimen (antes y después del 2026-09-18); verificador limpio antes de aceptar un resultado; worktrees y temporales grandes en D:\vrp-trabajo\; texto con barras invertidas nunca en un heredoc; cerrar a ~30 intercambios o tras dos hitos; sin guiones largos ni medios; rutas absolutas al informar.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué quedó corriendo y corre /cierre.
```
