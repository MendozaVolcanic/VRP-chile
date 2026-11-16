# Bloque de arranque S187 (cierre de S186, 2026-11-16 00:50 UTC)

S186 coordinó el loop desde la rama `loop/activo` como sesión dueña única, del 2026-11-15 13:00 al 2026-11-16 00:50 UTC.
Cerró por cambio de día y dos hitos grandes (pedido de Nicolás: «cierra sesión y abre la siguiente con todo»). **La
próxima sesión del loop es S187**, y Nicolás pidió que sea **una sesión propia, no anidada bajo S184**. La bitácora
completa de S186 está en `tasks/LOOP_OBJETIVOS.md` §6, entradas «(S186)» del 2026-11-15 13:09 al 2026-11-16 00:17 UTC.
El bloque anterior (`tasks/BLOQUE_ARRANQUE_S186.md`) queda como histórico.

**Trabajo en curso al cerrar:** ninguno de S186. Ningún agente ni proceso en segundo plano vivo; las sesiones que S186
lanzó o usó terminaron (documentos #1023, paper y mazos, L1B). La sombra de los 34 y el NRT siguen por cron.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| b.1: #1013, #1016, #1017, #1014, #1012 | INTEGRADOS | bitácora 13:21 UTC del 11-15 |
| b.2: parche B, guard A119 para todo VIIRS (#1020) | INTEGRADO | merge `aa3f48a5a`; ventana 09-16 a 11-15: FUERA_DE_BANDA pasa a VERDE, recall y 206 protegidas iguales |
| #1018 (probe L1B) | INTEGRADO y corrido | run 43724596931, 18 de 18; informe `D:\vrp-trabajo\temporales\s185_l1b\INFORME.md` |
| b.4: modal «Acerca de» con desempeño en vivo (#1021) | INTEGRADO y publicado | merge `e2126d441`; en Pages lee `data/audit_continuous/latest.json` |
| b.3: regla de posición «radiante» | DECIDIDA («Formalizar radiante») y PROTEGIDA | #1022, merge `5b16e9da5`: `tests/test_guard_regla_posicion_radiante_s186.py` atrapa «cercano» y «pico» |
| b.5 y b.6: documentos al día con la vía, divergencias D36 | INTEGRADO, ficha **v1.31** | #1023, merge `19b21cd0d` (2026-11-16 00:02:12 UTC); 34 de 35 contradicciones; CLAUDE.md ya no dice que VIIRS es K |
| b.7: `EARTHDATA_TOKEN` | ROTADO | secreto 2026-11-15 14:27 UTC, vence 2027-01-14 (rotar antes del 2027-01-04); NRT programado de 16:48 UTC verde con datos de los 11 |
| #1004: sombra de los 34 | ARREGLADA, issue aún abierto | run 43751792916 verde 34 de 34 con datos (19:45 a 19:59 UTC); lo cierra `nrt-monitor.yml` en su próxima corrida (la última fue 19:01 UTC) |
| Paper y mazos | VERIFICADOS | paper `fe47e03` (sin cifras cambiadas); `D:\vrp-trabajo\temporales\s186_paper_verif\VERIFICACION.md` y `verif4\` |
| Plazos de guardia | MODIS 22, V750 13, V375 11 de 29; los tres VERDE | `data/audit_continuous/guardia_*_latest.json` (00:18 UTC del 11-16) |
| Auditoría semanal | la última publicada es la del 11-09 (FUERA_DE_BANDA, #973); la del lunes 11-16 corre a las 09:00 UTC | se espera VERDE por #1020 |
| b.8: color de #1011 | ESPERA a Nicolás | PR de otra sesión |
| Historia de los 34 con la vía | PLAN SIN EJECUTAR (#1000) | ver §d y §f |
| Disco | C: 23 GB, D: 37 GB | `df -h` 00:46 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Fecha de la v1.31 de la ficha | dejar 2026-11-15 (Chile) / corregir a 2026-11-16 (UTC del merge) | Corregir a 2026-11-16 en el próximo PR que toque la ficha: las versiones anteriores usan la fecha UTC del merge |
| 2 | Color de #1011 (5 km fijo como MIROVA o regla de publicación) | MIROVA / publicación | Decide Nicolás; el PR declara la regla de publicación |
| 3 | Historia de los 34 con la vía (#1000: 7 tandas de 5 volcanes + piloto, ~520 h de runner, `data/historia_34/`) | ejecutar el piloto / esperar a D1 a D15 del plan de los 34 / no | Primero el piloto de 2 volcanes por un mes, tras decidir D1, D5 y D15 del plan (`docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` §11): mide costo real y peso antes de comprometer 520 h |
| 4 | Contradicción 35 (comentario de `USE_F5_CORE` en `frontend/diario.html` y `mosaico.html`) | PR con tag / dejar | PR chico con tag: es un comentario que describe la historia de K, ya reprocesada |
| 5 | PR viejos abiertos (#913, #955, #980, #981, #1000, #1011, #1015, #1019) | cerrar los superados / mantener | Que S187 revise cada uno contra main y proponga cerrar los superados (ver §f) |

## c. Lo aprendido

- **Regla general del workspace:** el clasificador del modo automático puede bloquear `start_session` con
  `initiation: user_asked` aun con un pedido amplio del usuario («continúa con todo lo que puedas»); la salida limpia
  es proponerla como tarjeta (`own_initiative`) y que el usuario la inicie. No reintentar ni buscar rodeos.
- **Regla general:** una prueba de guarda de una regla tiene que usar el escenario donde las reglas alternativas se
  separan; si el caso de prueba pone el foco donde todas coinciden, no protege nada. Probarlo con una mutación por cada
  alternativa («cercano» y «pico»), no sólo con la más obvia: el verificador encontró que «pico» pasaba.
- **Regla general:** `os.path.relpath` entre discos distintos en Windows lanza ValueError; pruebas que mezclan el
  worktree en D: con el temporal de pytest en C: fallan en local y pasan en CI (Linux). No es regresión.
- **Regla general:** la «fecha del merge» de una versión se lee del `mergedAt` de GitHub (UTC), no de la hora local:
  un merge a las 21:02 de Chile ya es el día siguiente en UTC.
- **Del proyecto:** para numerar la ficha al mergear un PR de otra sesión, usar un worktree propio separado de la
  rama (`git worktree add --detach ... origin/<rama>`), unir main, numerar y empujar a la rama del PR; así no se toca el
  worktree de la otra sesión.
- **Del proyecto:** el bloque S186 tenía las decisiones numeradas distinto de como se trataron (b.3 era «regla de
  posición», la verificación de la guardia K era otra fila de §a). Numerar decisiones sólo en §b.

## d. Problemas abiertos e hipótesis

| Problema | Marca |
|---|---|
| Historia de los 34 volcanes con la vía: hoy sólo existe la sombra desde el 2026-11-03 (`data/sombra_34/`) y 67 a 94 records de K de abril 2026 | CONFIRMADO (memoria `project_34_volcanes_estado.md`, plan #1000); costo de ~520 h es ESTIMACIÓN escalada de Tupungatito |
| Tupungatito V750: las 6 alertas que la vía calla dependen de la fase de la grilla (media celda N/S las recupera) | SOSPECHA; NRT contra estándar SIN DATO (LANCE guarda ~7 días) |
| Chillán V375, cola baja del este | saturación y huecos REFUTADOS; remuestreo SOSPECHA débil (n 3); causa sin atribuir |
| Corte de 5 km al centro, K1 y piso dNTI de V750 usados en MODIS, y demás de D36 | CONFIRMADO que existen; efecto SIN MEDIR (A116: medir antes de cambiar) |
| La auditoría del lunes 11-16 saldrá VERDE | SOSPECHA fundada: la ventana 09-16 a 11-15 dio VERDE con #1020 (`D:\vrp-trabajo\temporales\s186_parcheB\`) |
| #1004 se cerrará solo | SOSPECHA: depende de que `nrt-monitor.yml` corra (cron 30 */6, llega con atraso) |
| Sesiones con trabajo pendiente en el repo (S184 tanda 2, miniaturas, gráficos, plan de los 34, auditoría S175) | SIN REVISAR en S186 |

## e. Lo que ya está cerrado y no hay que rehacer

- Decisiones b.1 a b.7 del bloque S186: integradas, con verificador limpio y CI verde (ver §a).
- La regla de posición es «radiante» por decisión de Nicolás; no reabrir sin nueva medida. Cercano y pico ya medidos (S185).
- Los documentos ya describen la vía en los tres sensores (#1023); D36 lista las divergencias propias de la vía.
- El modal del tablero ya lee la auditoría en vivo; no hay que volver a escribir métricas a mano.
- Token rotado y probado en NRT programado; la sombra de los 34 ya corre con #1007.
- Probe L1B corrido; NRT contra estándar de Tupungatito ya no es recuperable.
- Paper y mazos verificados hasta la cuarta ronda.

## f. Prompt para la próxima sesión

```text
Sesión S187 de VRP Chile, dueña única del loop (respondes sólo a Nicolás). Carpeta
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Eres una sesión
propia (Nicolás pidió que no quede anidada bajo S184). Hay otras sesiones de Nicolás en este repo: no
toques sus ramas ni sus worktrees.

1. Verifica antes de creer:
   - git fetch origin --prune; git status -sb; df -h /c /d. Con C: bajo 3 GB, para y avisa.
   - gh pr list --state open y gh issue list --state open. Avísale a Nicolás los issues de alerta
     abiertos antes de cualquier otra tarea. ¿#1004 ya se cerró? ¿#973 sigue abierto?
   - Auditoría semanal del 2026-11-16 (data/audit_continuous/latest.json en origin/main): con #1020
     se espera VERDE (comparar con D:\vrp-trabajo\temporales\s186_parcheB\). Si da VERDE, propón
     cerrar #973. El modal «Acerca de» del tablero debe mostrarla con la vía en los tres sensores.
   - python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main tiene que
     decir OK.
2. Lee CLAUDE.md (ya al día con la vía, #1023), tasks/BLOQUE_ARRANQUE_S187.md y las entradas (S186)
   de tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Plazos de guardia: data/audit_continuous/guardia_{modis,v750,v375}_latest.json. MODIS va en
      22 de 29; al llegar a 29 corre D:\vrp-trabajo\temporales\s185_cierre_modis\informe_cierre_modis.py
      (README al lado) y lleva el informe a Nicolás.
   b. Historia de los 34 volcanes (pedido de Nicolás): explícale qué hay hoy (sombra desde el
      2026-11-03 en data/sombra_34/, nada histórico con la vía), qué propone el plan #1000
      (docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md: 7 tandas de 5 + piloto,
      ~520 h de runner estimadas, data/historia_34/ aparte de la sombra) y qué decisiones del plan de
      los 34 bloquean (docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md §11, D1 a D15). Lee
      antes la memoria project_34_volcanes_estado.md. Recomienda empezar por el piloto; no ejecutes
      nada sin su sí.
   c. Sesiones y PR con pendientes (pedido de Nicolás): lista las sesiones de VRP Chile no archivadas
      (list_sessions, sin filtro linked) y los PR abiertos (#913, #955, #980, #981, #1000, #1011,
      #1015, #1019 al cierre de S186). Para cada uno: qué quedó pendiente (list_events de la sesión,
      cuerpo del PR), si ya está superado por main (comparar por contenido, A96) y qué falta. Lleva
      a Nicolás una tabla con recomendación (mergear, cerrar, retomar en su sesión o archivar). Hazlo
      con subagentes de solo lectura si son muchos; no escribas en sus ramas.
   d. Decisiones b.1 (fecha de la v1.31), b.2 (color de #1011) y b.4 (contradicción 35) del bloque.
Reglas duras:
- Los merges a main, toda A45 nueva y aplicar a data/ son sólo de Nicolás, con «mergea #N».
- Merge commit con gh pr merge --merge --match-head-commit <sha completo>; nunca squash.
- Nada en pipeline/, data/ ni frontend/ sin tag y su sí.
- Sólo EARTHDATA_TOKEN (está sólo como secreto de GitHub; vence 2027-01-14).
- Verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito.
- Temporales y worktrees en D:\vrp-trabajo; export MSYS_NO_PATHCONV=1 y rutas D:/ en git worktree.
- Tope de agentes: 5 y 2 procesos pesados, salvo que Nicolás lo levante; tope de 500 MB por agente.
- Quita tu worktree al mergear, revisando list_sessions justo antes. Worktree vivo de otra sesión
  terminada: D:\vrp-trabajo\wt_s186_docs (de #1023, ya mergeado); quítalo sólo al archivar esa sesión.
- git add por archivo; nunca git stash; nada de experiments/_s176_codex/.
- Commitea antes de una prueba de mutación que restaure con git checkout.
- date -u antes de cada encabezado de bitácora.
- Texto con rutas de Windows o comillas invertidas: escríbelo con Write a un .py, nunca dentro de
  un heredoc de bash.
- Ficha SDA: la versión se toma al mergear (#1009); quien mergea une main y pone la siguiente, con la
  fecha UTC de mergedAt.
- Si start_session con user_asked lo bloquea el clasificador, propón la sesión como tarjeta.
- Español de Chile, sin guiones largos ni medios; rutas absolutas para Nicolás.
- Nombra la referencia de MIROVA leyendo el loader (tabla, OCR o ambos).
Si la sesión no alcanza: deja en la bitácora qué quedó a medias y cierra con /cierre al 50 % del
contexto; Nicolás autorizó que la sesión que cierra inicie la siguiente, como sesión propia.
```
