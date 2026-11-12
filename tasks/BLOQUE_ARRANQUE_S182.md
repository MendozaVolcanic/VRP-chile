# Bloque de arranque S182 (cierre de S181, 2026-11-12 22:35 UTC)

S181 coordinó el loop desde la rama `loop/activo`, como sesión dueña única (respondía sólo a Nicolás). Cerró por contexto.

**Estado del trabajo al fijar este bloque.** No queda ningún agente, proceso local ni workflow propio corriendo. Los cinco agentes y los cuatro verificadores terminaron. Las sesiones de S180 («Reemplazar la historia» `local_f37923b4`, «Rediseño del tablero» `local_ad53d287`) están detenidas, y su trabajo ya está integrado (#994, #986).

**Lo anterior.** `tasks/BLOQUE_ARRANQUE_S181.md` (cierre de S180) queda como histórico. La bitácora completa de S181 está en `tasks/LOOP_OBJETIVOS.md` §6, en las entradas «(S181)» de 2026-11-12 05:12 a 22:27 UTC.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| SOSPECHA del reemplazo (guardias ciegas, encendido VIIRS corrido) | CONFIRMADA y ARREGLADA | #993, merge `6c23e2003`. Nulo sellado en `experiments/_s181_guardias_reemplazo/nulo_sellado.json` (MODIS 167, V375 274, V750 270 pares, 0 distintas) |
| Unión de la historia con la vía (#994) | EN MAIN | merge `97979b94a`, 21:15 UTC. Verificada sobre el main del día: ensayo idéntico salvo NRT nuevos |
| **Historia de los 11 Tier A reemplazada con la vía en `data/`** | APLICADA (A45: «Sí, aplícalo») | `aplicar-reemplazo.yml` run 43310112245; commit `21ea8166b` (21:37 UTC); tag `pre-s180-reemplazo-historia` = `23841347d`. 602 pruebas pasan. Sin par máx. MODIS 3,32 %, V375 6,22 %, V750 0; K restante 0 |
| Vigilancias de las guardias sobre main | VERDE las tres, encendidos sin cambio, nulo sellado | runs 43312343316 (MODIS) y 43312348741 (VIIRS) |
| NRT que corría durante el reemplazo | NO devolvió K | `D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py` sobre `4217de367`: 11 de 11 OK; su control sobre `21ea8166b~1` marca los 11 |
| Sitio publicado | CON LA HISTORIA NUEVA | Pages de `4217de367` verde; en el sitio, Láscar 5.806 records, 0 K antes del corte; sin errores de consola |
| Qué cambió en la serie (antes y después) | MEDIDO, sin verificador propio de otro modelo | `experiments/_s181_verif_994/` (`cambio.txt`, `banco_ab_salida.txt`, `banco_solo_tabla_salida.txt`). Por noche, tabla sola: recall MODIS 0,874 a 0,966, V375 0,986 a 0,991, V750 0,755 a 0,953 |
| Paper (repo privado `vrp-chile-paper`) | NÚMEROS, TABLAS Y REVISIÓN LISTOS; prosa intacta | commits `f8bbd68`, `b4f5f4a`, `3e7580b`; `revisiones/REVISION_S181.md` (42 pasajes). Verificador Sonnet: CORRECTO CON OBSERVACIONES |
| Mazos del congreso y de jefatura | ACTUALIZADOS (fuera de git) | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\congreso geologico 2026\` (originales en `2_PRESENTACIONES\_previo_S181\`; inventario y pendientes en `2_PRESENTACIONES\ACTUALIZACION_S181.md` §5). Dos vueltas del verificador; la última tanda de 5 retoques de texto no se re-verificó |
| Ficha SDA (v1.23 y v1.24 vigentes, v1.25 del reemplazo) | PR #996 EN BORRADOR, CI verde | head `a2b1f49d2`, CLEAN. Verificador: CORRECTO CON OBSERVACIONES, todas aplicadas |
| Issues | #995 (sombra 34): la corrida programada del 11-12 20:44 UTC salió `success`, así que debería cerrarse sola. #973 (auto-audit 11-09), #943, #813 | `gh issue list --state open` |
| Disco | **C: 2,4 GB libres, BAJO EL UMBRAL DE PARADA (3 GB)**; D: 13 GB | `df -h`, 22:32 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ~~Merge de #996 (ficha SDA)~~ **HECHO** | «mergea #996» de Nicolás, merge `f53148aa1` (2026-11-12 23:58 UTC) | (texto original: Mergear: la ficha pública dice hoy que VIIRS sigue en propuesta y que la historia es K, y las dos cosas son falsas) |
| 2 | `frontend/index.html:544` dice que lo anterior a las fechas de cambio es K y que el gráfico marca el cambio con una línea vertical. Desde el reemplazo es falso | PR de frontend con tag y sí (A45), o dejarlo | PR chico ahora, junto con la decisión 3 |
| 3 | Quitar el selector «Cluster / Núcleo F5'» | quitarlo o dejarlo | Quitarlo: la historia ya no tiene records K y el núcleo no aplica a la vía |
| 4 | Mecanismo de reversión (decisión 5 de `docs/AUDIT_S179.md`) | revert del PR o apagar el flag | Apagar el flag. Ojo: tras el reemplazo, revertir también exige restaurar la historia K desde el tag `pre-s180-reemplazo-historia` |
| 5 | Vigilar «la vía calla y K también» (decisión 7) | vigilante diario o audit semanal | Vigilante diario |
| 6 | Mazos: idea central nueva de AT8.7; «código abierto» en 4 láminas sin LICENSE en el repo; figura `[FIGURA]` de jefatura L2 y QR | aprobar o pedir cambios; poner licencia o cambiar el texto | Leer `ACTUALIZACION_S181.md` §5. Elegir licencia antes del congreso o decir «código publicado» |
| 7 | Paper: reescribir los 42 pasajes con `REVISION_S181.md` | lo escribe Nicolás (política de Volcanica) | Empezar por §6 (validación), que es la que más cambia |
| 8 | Disco C: con 2,4 GB | liberar espacio | Mirar `pagefile.sys` primero (S175); no correr agentes pesados hasta pasar de 3 GB |

## c. Lo aprendido

**Reglas generales del workspace:**
1. **El aviso que imprime un instrumento no dice lo que el instrumento hace.** `banco_paridad` imprime «Decide: SOLO la tabla», pero `cargar_referencia_unificada` une la tabla con el OCR. Yo publiqué «sólo la tabla» en la bitácora y en un brief, y lo cazó un agente que leyó el código. La referencia se nombra leyendo el loader.
2. **`git pull --rebase -X theirs` favorece al commit LOCAL que se reaplica, no al remoto.** Un reemplazo de datos que corre mientras un NRT está en vuelo puede quedar pisado. Después de ese NRT hay que correr un chequeo que pueda fallar, con su control sobre el commit anterior.
3. **Con `MSYS_NO_PATHCONV=1`, `git worktree add /d/...` crea `C:\d\...`.** Usar `D:/...`.
4. **Una segunda vuelta corta del verificador, sólo sobre lo nuevo, rinde.** La primera cazó una frase falsa en la ficha pública y cinco sobre-afirmaciones en los mazos; la segunda cazó una frase que la figura nueva contradecía.

**Propio del proyecto:**
5. Un paper con política de IA (Volcanica) se actualiza regenerando números y tablas y escribiendo una revisión pasaje por pasaje; la prosa no se toca.
6. Tras el reemplazo, el antes y después del paper mezcla tres cosas: la vía, la salida del Núcleo F5' (Láscar V375) y un denominador de MIROVA distinto (82 a 84 noches en MODIS). Cada número va con su ventana.

## d. Problemas abiertos e hipótesis

| # | Qué | Marca |
|---|---|---|
| 1 | Cordón Caulle V750 2026-10-21 05:48 UTC NOAA-21: publicamos 10,1 MW (11 píxeles entre 2,9 y 12,1 km del cráter, fondo 249 K) y MIROVA 0,36 MW. Posible sobre-publicación de la vía; causa sin encontrar | CONFIRMADO el caso; causa SOSPECHA |
| 2 | La vía V750 acepta 522 pasadas de borde de franja (cenital mediano 69,5°) que K descartaba; la única con detección es Chillán 2026-10-13 06:42, 10,94 MW. ¿Hace lo mismo el código de MIROVA? | SOSPECHA |
| 3 | Por pasada, el recall V375 baja de 0,954 a 0,937: 15 pasadas de 1 MW o más que K publicaba y la vía no. Las 15 noches siguen publicadas por otra pasada | CONFIRMADO (sin verificador independiente) |
| 4 | `frontend/index.html:544`: texto falso tras el reemplazo | CONFIRMADO (verificador de la ficha) |
| 5 | Las noches de alerta de MIROVA cambian entre el antes y el después del paper (82 a 84 en MODIS); ¿cargador #652 o CSV? | SOSPECHA |
| 6 | Que MODIS y V375 difieran del código publicado por MIROVA sólo en lo que depende del sensor (lo afirman L4 y L17 de AT8.7) | SOSPECHA, dicho con cautela en el mazo |
| 7 | Guardia K VIIRS: 0 de 29 comparaciones después del encendido; la primera real, la noche del 11-13 | Por leer |
| 8 | #973: el auto-audit del 11-16 será el primero sobre la historia con la vía; puede moverse por construcción (O1 de #993) | SOSPECHA |

## e. Lo que ya está cerrado y no hay que rehacer

- La SOSPECHA de guardias ciegas tras el reemplazo: arreglada en #993 y comprobada sobre main después de aplicar.
- El reemplazo de la historia: aplicado. No volver a correrlo salvo que el chequeo post NRT marque K. Para eso: `python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main`, que debe decir OK.
- La unión de la vía (#994) y el ensayo: verificados dos veces (Sonnet de S180 y S181 sobre main).
- Paper: números y revisión verificados. No regenerar salvo que cambien los datos.
- Mazos: dos vueltas de verificación; quedan sólo las decisiones de Nicolás.
- #995: la sombra de los 34 salió verde el 11-12; la falla del 11-11 fue el servicio de artifacts de GitHub.

## f. Prompt para la próxima sesión

```text
Sesión S182 de VRP Chile, dueña única del loop (respondes sólo a Nicolás). Carpeta
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer:
   - git fetch origin --prune; git status -sb; df -h /c /d. Con C: bajo 3 GB, para y avisa.
   - gh pr list --state open y gh issue list --state open. ¿#996 sigue en borrador? ¿#995 cerró?
   - python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main tiene que decir OK.
     Si marca K, la historia se pisó: avisa a Nicolás antes de nada.
   - Corre las vigilancias de las guardias (vigilancia-guardia-modis.yml y -viirs.yml) o lee su último run.
2. Lee CLAUDE.md, tasks/BLOQUE_ARRANQUE_S182.md y las entradas (S181) de tasks/LOOP_OBJETIVOS.md §6.
3. Dile a Nicolás qué issues siguen abiertos y pide las decisiones de la sección b, con tu recomendación.
4. Trabajo, en orden:
   a. (#996 ya integrado, f53148aa1.)
   b. PR de frontend (texto de index.html:544 y selector Núcleo F5'), con tag y su sí (A45),
      verificado en el navegador.
   c. Leer la primera comparación real de la guardia K VIIRS después del encendido.
   d. Investigar Cordón Caulle V750 2026-10-21 05:48 (10,1 MW contra 0,36 de MIROVA) y las 522 pasadas
      de borde de V750, contra el código de MIROVA en OSF (reference_codigo_mirova_osf).
   e. Auditoría semanal del 11-16 (#973) y plazo MODIS (12 de 29 vistas).
Reglas duras:
- Los merges a main, toda A45 nueva y aplicar a data/ son sólo de Nicolás, con «mergea #N».
- Merge commit, nunca squash.
- Nada en pipeline/, data/ ni frontend/ sin tag y sí.
- Sólo EARTHDATA_TOKEN.
- Verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito; temporales en D:.
- Máximo 5 agentes y 2 procesos pesados; tope de 500 MB por agente; parada bajo 3 GB.
- git add por archivo; nunca git stash; nada de experiments/_s176_codex/.
- date -u antes de cada encabezado de bitácora.
- export MSYS_NO_PATHCONV=1 y rutas D:/ (nunca /d/) en git worktree.
- Rutas de Windows en Python como string crudo.
- Español de Chile, sin guiones largos ni medios; rutas absolutas para Nicolás.
- Nombra la referencia de MIROVA leyendo el loader (tabla, OCR o ambos).
Si la sesión no alcanza: deja en la bitácora qué quedó a medias y cierra con /cierre al 50 % del contexto.
```
