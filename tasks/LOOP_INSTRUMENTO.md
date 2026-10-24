# Loop del instrumento (fase 0 del programa por sensor): cola, decisiones y bitácora

> **Para el agente que corre este loop:** este archivo es tu única fuente de verdad entre vueltas. En cada vuelta se
> lee entero, se avanza UNA tarea de la cola (o se revisa lo que corre: CI, verificador), se anota en la bitácora y
> se commitea en la rama `claude/s162-instrumento-021324`. Nunca supongas el estado: reconstrúyelo con `git log`,
> `gh pr list`, `gh run list` y la bitácora.

**Dueña:** sesión hija «Instrumento» de S162 (abierta por la coordinadora `local_4152952c-6afd-433a-82b3-b07575feee3b`
el 2026-10-24). **Programa:** `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §8, V375-A (§4) y
MOD-A (§5). **Reglas del loop general:** `tasks/LOOP_OBJETIVOS.md` §1 (esta sesión no escribe ese archivo).

**Por qué existe.** El A/B de D25 mostró que el instrumento tenía un hueco que ningún control veía: el 2026-10-12 a
los tres brazos les faltaban 44 pasadas que producción sí tenía (una protegida de 8,44 MW en Chillán), porque CMR no
devolvió los gránulos reprocesados, y la cobertura comparaba brazos entre sí, no contra la referencia de MIROVA
(`experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`). Sin estos arreglos ningún A/B nuevo se despacha (PD0).

## 1. Reglas propias

1. Trabajo en mi worktree (`...\.claude\worktrees\s162-instrumento-021324`, esta rama sólo lleva este archivo y
   la bitácora) y en un worktree de tareas en `D:\vrp-trabajo\worktrees\s162-instrumento-tareas` (regla de discos de
   `LOOP_OBJETIVOS.md` §2.0), con una rama `instrumento/<tarea>` desde `origin/main` por PR.
2. No escribo `tasks/LOOP_OBJETIVOS.md` ni `tasks/LOOP_VIIRS750.md`, `LOOP_VIIRS375.md`, `LOOP_MODIS.md`.
3. Nada en `pipeline/` sin tag defensivo y el sí de Nicolás (A45): PR en borrador y aviso a la coordinadora.
4. Ningún despacho de GitHub Actions: se piden a la coordinadora por SendMessage.
5. TDD: prueba roja por aserción (no por caída), verde, mutaciones contadas sólo si las atrapa una aserción y con
   control de caída (`feedback_s156`), verificador con contexto limpio de otro modelo antes de dar la tarea por lista.
6. Nunca `git stash` (usar `git show <commit>:<archivo>`); `git add` por archivo; CI con conclusión antes de dar un
   PR por listo (A39 enmienda S142); suite sobre árbol quieto (A112).
7. Parada si C: o D: bajan de 3 GB libres (`df -h /c /d`).
8. Español de Chile, sin guiones largos ni medios; rutas absolutas al informar.

## 2. Cola (en orden; una por vuelta)

Estado: `[ ]` pendiente, `[~]` en curso, `[v]` en verificación, `[x]` lista (PR + CI verde + verificador limpio).

- [ ] **T7. MOD-A, la cita de MOD03.** Renderizar a imagen la p. 4 de
  `documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` (`page.get_pixmap(dpi=200)`, A95) y
  citar qué dice de MOD03 (P1 y P3 discrepan). Entregable: nota en `experiments/_s162_instrumento/MOD_A_CITA_MOD03.md`,
  render fuera del repo público (feedback S158). Sin código.
- [ ] **T4. Una sola definición de alerta y protegida** en `scripts/clase_mirova.py`: canal (tabla, OCR, tabla sola),
  regla SN, pareo ±120 s, distancia compatible, marca de fuente lejana, y el arreglo del riesgo latente de
  `clase_mirova.py:65-75` (una fila OCR de alerta cuenta protegida aunque la tabla diga FALSO_POSITIVO en la misma
  pasada; `experiments/_s159/mirova_v1_auditoria/INFORME.md:246-250`). La decisión debe ser por PASADA, no por fila.
- [ ] **T6. V375-A, «protegida de cráter»**, informada al lado de la lectura A sin reemplazarla: excluye filas sólo
  OCR de Suomi NPP antes del hito 2026-10-09 (`HITO_SNPP`) y fuentes lejanas (`experiments/_s159/portes/INFORME.md`
  P-5). Depende de T4.
- [ ] **T1. Cobertura contra la referencia de MIROVA** en un evaluador común (`scripts/evaluador_comun.py` o similar):
  por brazo y producción, pasadas de la referencia sin record a ±120 s por volcán, sensor y día; una protegida sin
  record en todos los brazos que producción sí tiene, o un día con pasadas de MIROVA y cero records en un brazo, es
  INVALIDO POR INSTRUMENTO antes del veredicto. Caso de prueba obligatorio: el 2026-10-12 de V1 de D25.
- [ ] **T2. «No observado» como estado propio**, fuera del denominador (volcán fuera del gránulo, escena inválida).
- [ ] **T5. P1b en las dos direcciones** (cruces de 1 MW hacia arriba y hacia abajo) y conteo de publicaciones sobre
  pasadas RUTINA (VE162-03).
- [ ] **T3. Placebo de ganancia y comparador d′ (D-28) en el evaluador común**, reutilizable por VIIRS y MODIS, con
  los placebos de D-44; hoy sólo en `evaluar_d25.py` (rama `s159-evaluador-d25`, tag `s161-d25-lectura`).

## 3. Decisiones pendientes (para la coordinadora o Nicolás)

(ninguna todavía)

## 4. Bitácora (la más nueva arriba)

### 2026-10-24 15:18 UTC, hora del servidor: arranque
- Leídos `CLAUDE.md`, el programa (§2, §4, §5, §8, §9, §11), `LOOP_OBJETIVOS.md` §1-§2, el informe del 12-oct.
- Mi rama = punta de `loop/activo` (`b05d60527`), 708 commits detrás de `origin/main` en `scripts/` y `tests/`: por eso
  las tareas salen de `origin/main` en un worktree aparte. #889 (`s159-instrumentos`, borrador) toca
  `clase_mirova.py` (sólo `VENTANA_S` como definición única) y `banco_paridad.py` (`TOL_S = VENTANA_S`): compatible,
  lo reproduzco igual para no chocar.
- Hallazgo de lectura: la lectura A de `alerta_protegida` NO cuenta filas FALSO_POSITIVO (exige
  `ALERTA_TERMICA[_OCR]`); el riesgo real es por pasada (la fila OCR gana a la de la tabla con la misma llave en
  `referencia_mirova_unificada.py:172-177`). Hoy 0 casos según la auditoría de Mirova-v1. T4 lo arregla por
  construcción.
- Discos: C: 38 GB, D: 8,6 GB libres.
- Aviso de arranque: issue #864 (auto-audit semanal fuera de banda, desde el 2026-10-19) sigue abierto; va en el
  resumen a la coordinadora.
