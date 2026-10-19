# Bloque de arranque S157 (cierre de S156: «retomar» + loop, vueltas 223 a 226)

Escrito el 2026-10-19 a las 17:48 UTC (hora del servidor) sobre `loop/activo` (`13940241`, igual al remoto); `main` en
`9ac09b16` (#863) más los commits automáticos. **Se fijó con trabajo en curso en GitHub**, que no escribe en esta rama: el
reproceso histórico con K (run 39125546355: 165 verdes, 3 fallidos, 9 pendientes a las 17:48), el NRT de cada hora y
la sombra diaria del 19-oct (`experimental-diario`, todavía sin correr a esa hora; al terminar dispara por primera vez
la vigilancia de la sombra automática). Ningún agente ni proceso local vivo; ningún worktree aparte de la raíz.
Bitácora en `tasks/LOOP_OBJETIVOS.md` §6 (vueltas 223 a 226); el bloque anterior, `tasks/BLOQUE_ARRANQUE_S156.md`,
queda como histórico. Ante discrepancia manda la bitácora y, por encima, el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | **Auto-audit por detector** (arreglos 2 y 3 de AUDIT_S155): cada noche con records de su detector, frontera leída de `frontend/cambio_detector.js`, flags sólo de K, D-9 SN, magnitud publicada por volcán y sensor, falsas por detector y cenit, alertas protegidas sin publicar por nombre | #862, squash `484d037d`; `experiments/_s156_autoaudit/` (corrida local y verificador) |
| hecho | **Primer issue del auto-audit nuevo**: #864, 10 avisos, todos de K (recall VIIRS 750 73,3 %; magnitud Chillán en los tres sensores y Tupungatito; 5 protegidas sin publicar). Era lo predicho | issue #864 (run `audit-weekly` del 2026-10-19 16:16, cron atrasado) |
| hecho | **#779 cerrado** con comentario hacia #862 | issue #779 |
| hecho | **Vigilancia de la sombra** (arreglo 4, V1-04): reversión candidata, fuera de plazo, investigación, duración, vigilancia ciega; workflow diario tras `experimental-diario` y cron de respaldo 23:40 UTC | #863, squash `9ac09b16`; `scripts/vigilancia_sombra.py`, `.github/workflows/vigilancia-sombra.yml`; 65 pruebas, 82 de 82 mutaciones por aserción; cinco verificadores en `experiments/_s156_autoaudit/sombra/verificador*/` |
| hecho | **Run real de la vigilancia** despachado a mano: todos los pasos verdes, VERDE, commit de resultados, sin issue | run 39294849891, commit `a4a9d222` |
| hecho | **Decisiones de Nicolás sobre la sombra** (a a f) escritas al inicio del paso 9 de la regla | `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`; `sombra_pasadas_juzgadas.json` |
| abierto | **Caso PCC VIIRS 750 2026-10-10 05:54**: la sombra publica, K no; mismo objeto que MIROVA; retrospectivo, decisión «no revertir, investigar» | issue #865; `experiments/_s156_autoaudit/sombra/` |
| corriendo | Histórico con K (2025-02-15 a 2026-09-17), run 39125546355 | 165 verdes, 9 pendientes |
| **fallido** | 3 trozos del histórico, todos de Nevados de Chillán: **5** (2025-07-13 a 08-18) y **6** (2025-08-19 a 09-24) por el tope de 170 min del paso; **9** (2025-12-08 a 2026-01-13) por caída del runner | logs de los jobs 117669982154, 117669982210, 117669982393; `reproc-chunked.yml:119/136` (180 y 170 min) |
| pendiente | Reemplazo de los datos con el histórico, mover `DATOS_K_DESDE_UTC`, A/B diurno sobre K | plan S156 punto 3; `experiments/_s151_ab_diurno/DESPACHO_K.md` |

Discos al cierre: C: 27 GB libres, D: 21 GB. Temporales de la sesión en `D:\vrp-trabajo\temporales\s156_audit\` y
`D:\vrp-trabajo\temporales\s156_sombra\` (la evidencia útil ya está en el repo; se pueden borrar).

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Cómo recuperar los trozos 5 y 6 de Chillán (170 min no alcanzan para 37 días de Chillán en 2025) | relanzarlos partidos en dos (≈18 días cada uno) · subir el tope del paso · relanzar igual | **partirlos en dos** sobre el mismo commit del run (A15: `timeout >= duración × 1,3`; los demás trozos tardaron hasta 160 min, así que no hay margen para subir el tope sin rozar las 6 h del job). El 9 se relanza igual (`gh run rerun --failed`), porque fue el runner |
| 2 | #864 (primer issue del auto-audit nuevo) | dejarlo abierto como el estado de K · cerrarlo | **dejarlo abierto**: son hallazgos reales de K (los mismos de AUDIT_S155 F2-02, F3-04, F5-01); se cierra cuando se atiendan |
| 3 | Falsa alarma residual de Muy Bajo en la vigilancia (0,58 de probabilidad de al menos un «investigar» en 120 días, bajó de 0,68) | aceptarla · exigir un mínimo de pasadas | **aceptarla por ahora**: es un issue de investigación que se deduplica, no una reversión; reabrir si molesta |
| 4 | #824 (watchdog) y PR #776 (sonda de tres campos, borrador desde S150) | cerrar · mantener | #824: cerrar con el hallazgo F3-10 (mide el run, no el job) y abrir la tarea; #776: decidir si sigue vivo |
| 5 | Cronología OVDAS de Chillán; rotar el PAT; aviso a OVDAS del cambio de detector (fecha de datos 18-sep) | hacerlo · postergar | hacerlo (arrastre de S155; el PAT sigue en `~/.claude/settings.json`) |
| 6 | #813 (D-10, abrir el día en la réplica) | decidir · postergar | sin evaluar en S156 |

## c. Lo aprendido

1. **Un verificador limpio por ronda sigue encontrando algo, y eso es la señal de que hacía falta** (S156, regla de
   método del proyecto). Cinco rondas sobre la vigilancia: sombra muerta en un volcán daba VERDE, el issue no se abría
   si fallaba el push, la deduplicación era por bolsa de palabras, el plazo dependía del día de la corrida, una racha
   disparaba para siempre. Ninguno lo vio el autor. Destino: este bloque y `experiments/_s156_autoaudit/sombra/README.md`.
2. **Una batería de mutaciones necesita su propio control**: el criterio «la suite falla» contaba como atrapada una
   mutación que sólo hacía caer el script. Ahora se lee el XML de JUnit y se exige `AssertionError`, con una mutación de
   control que debe salir NO atrapada (A110 aplicado a las mutaciones). Regla general del workspace.
3. **Una vigilancia ciega no da error: da VERDE.** Hubo que agregar avisos por cada lado que puede morir (referencia,
   sombra y producción por volcán Y sensor, perfiles cruzados) y medir que el umbral no dé falsas cegueras (0 huecos
   de más de 3 días desde agosto). Regla general del workspace.
4. **Decidir una regla viendo el caso se escribe así, en la regla misma**: la lectura B quedó marcada como «se tomó
   después de ver el caso». Proyecto (paso 9 de la regla).
5. **Causa de la falla «local SIN ATRIBUIR» de S155**: `test_guard_libro_de_pruebas_s146.py` g1d y g2c fallan con el
   repo en D: y el temporal en C: (`relpath` entre discos); con `TMP`/`TEMP` en D: pasan. Memoria
   `reference_onedrive_no_sincroniza`. Regla general del workspace.
6. **Heredoc con barras invertidas, quinta y sexta vez** (un `\n` en el `printf` del workflow, otro en una mutación).
   No hay reemplazo «corto»: si hay una barra invertida, herramienta Edit. Memoria `feedback_s144_heredoc_y_grep_cortan`.
   Regla general.
7. **El cron de GitHub llega con horas de atraso** (auto-audit de las 09:00 corrió a las 16:16). No esperar el issue a
   la hora del cron. Proyecto.

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | K pierde una protegida en VIIRS 750 que C0 ve (PCC 10-oct, mismo objeto que MIROVA); la misma pasada la publica en VIIRS 375 | #865, `experiments/_s156_autoaudit/sombra/` |
| CONFIRMADO | Los 10 avisos de K del auto-audit (recall V750, magnitud Chillán y Tupungatito, 5 protegidas) | #864 |
| CONFIRMADO | Trozos 5 y 6 de Chillán no caben en 170 min; el 9 cayó por el runner | logs de los jobs |
| CONFIRMADO | Falsa alarma residual de Muy Bajo 0,58 en 120 días | `experiments/_s156_autoaudit/sombra/verificador4/` |
| SOSPECHA | La clase de una pasada de la vigilancia puede cambiar si entra o sale de la referencia una protegida anterior; en snapshots semanales no se vio con protegidas, a escala diaria sin medir | verificador 5, e2 |
| SOSPECHA | Por qué K calla en PCC VIIRS 750: el primer paso queda vacío con `max` y sin Test 1 en una señal sub-umbral (NTI −0,906) | #865 |
| SIN VERIFICAR | El primer disparo automático de la vigilancia tras `experimental-diario` del 19-oct | mirar `gh run list -w vigilancia-sombra.yml` |

## e. Lo que ya está cerrado y no hay que rehacer

- El auto-audit por detector y la vigilancia de la sombra: código, pruebas, mutaciones y cinco verificadores. No se
  re-auditan salvo cambio de regla.
- Las decisiones a a f del paso 9 (en la regla). El caso PCC está juzgado: no revertir, investigar (#865).
- La cota SE de Muy Bajo (7 de 161 y 12 de 343): derivada de los JSON del A/B y verificada; el denominador real
  (163 a 166, cerca de 350) da una cota apenas menor, del lado que dispara más.
- La causa de g1d/g2c (discos). La deduplicación de issues por prefijo funciona con el `gh` real.

## f. Prompt para la próxima sesión

```
/retomar

Luego, en el repo VRP Chile (rama loop/activo), antes de creerle a nada: git fetch --prune; hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date); gh run view 39125546355 (histórico con K: ¿terminó?, ¿cuántos fallidos?); gh run list -w vigilancia-sombra.yml -L 3 y gh run list -w experimental-diario.yml -L 2 (¿corrió sola la vigilancia?); gh issue list (¿#864, #865, issues nuevos de «Sombra de K»?); df -h /c /d.
Lee en orden: tasks/BLOQUE_ARRANQUE_S157.md, experiments/_s156_autoaudit/sombra/README.md, la bitácora de tasks/LOOP_OBJETIVOS.md desde la vuelta 223, el paso 9 de experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md (marca al inicio).
Trabajo, en orden (salvo que Nicolás decida otro en la tabla b):
1. Cuando el histórico termine: relanzar el trozo 9 de Chillán con gh run rerun 39125546355 --failed SOLO si los únicos fallidos son de runner; los trozos 5 y 6 de Chillán (timeout de 170 min) se relanzan partidos en dos sobre el MISMO commit del run (A15, A108). Contar pasadas de cada trozo contra lo esperado antes de dar el histórico por completo.
2. Ensayo del reemplazo por volcán, verificador limpio, aplicar entre corridas del NRT, verificar_ventana.py y R8. En el mismo PR mover DATOS_K_DESDE_UTC en frontend/cambio_detector.js (tests/test_cambio_detector_frontera_s155.py se pondrá rojo). Con el reemplazo, el auto-audit y la vigilancia siguen la frontera solos.
3. Despacho del A/B diurno sobre K desde el tag s154-diurno-k-codigo con --sha-codigo e66b402c70b1c97cb8164bc05e33a70d63501c9d (experiments/_s151_ab_diurno/DESPACHO_K.md).
4. Investigación de #865 (PCC VIIRS 750) y pre-registro de D25 sobre K con Chillán (1.29), F5-01 incluido; para el sello de Nicolás.
5. Propagación de K en los textos (arreglo 5 de AUDIT_S155): tablero, ficha SDA, CLAUDE.md y MISSION, catálogo, cabeceras, INDEX.
Reglas duras: no adoptar nada en producción sin el sí explícito de Nicolás (A45, tag defensivo); la vigilancia de la sombra NO revierte sola: una candidata se confirma en la cabecera de MIROVA y se le avisa a Nicolás; una sola sesión dueña del loop; ningún número a Nicolás sin script commiteado; la hora se pide al servidor (A86); verificador limpio antes de aceptar un resultado; worktrees y temporales grandes en D:\vrp-trabajo\ y pytest en D: con TMP/TEMP en D:; texto con barras invertidas siempre con la herramienta Edit, nunca en un heredoc; cerrar a ~30 intercambios o tras dos hitos; sin guiones largos ni medios; rutas absolutas al informar.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué quedó corriendo y corre /cierre.
```
