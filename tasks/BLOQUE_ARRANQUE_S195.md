# Bloque de arranque S195 (escrito por S194, 2026-11-22 ~12:45 UTC)

> El bloque anterior (S194, escrito por S193) queda como histórico en `tasks/BLOQUE_ARRANQUE_S194.md`. El detalle de
> S194 está en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S194, arriba) y en `tasks/PLAN_S194_PROMPTS.md`.
> **El estado se fijó con trabajo en curso** (filas «corriendo» de la tabla a): comprobarlo contra el remoto.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.75** (merge de #1094, 11:27 UTC); #1095 empujado con v1.76 a las 12:22 UTC, esperando CI | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md`; log `D:\vrp-trabajo\temporales\s194\merge\uno_1095.log` |
| PR mergeados en S194 (11) | #1084 (v1.67, A/B diurno), #1086 (v1.68, tablero distingue el día), #1087 (v1.69, perfil `laboratorio`), #1089 (v1.70, frente 5 de Codex; unión a mano con #1086 en el minigráfico del mosaico), #1088 (regla de merge S193 en `CLAUDE.md`, sin ficha), #1090 (v1.71, **día MODIS encendido en producción**), #1091 (v1.72, marcador «también hay calor en la cumbre»), #1092 (v1.73, partición por áreas), #1093 (v1.74, pre-registro del laboratorio paso 2, re-sellado con las respuestas de Nicolás), #1094 (v1.75, vigilancia C1-101 y C1-106) | logs `D:\vrp-trabajo\temporales\s194\merge\` |
| **#1095** (tablero «cráter no medido» y MIR saturada, Codex C1-102 y C1-V202) | **corriendo**: `uno.sh` espera su CI para mergear con `--match-head-commit`; worktree `D:\vrp-trabajo\worktrees\s194m-1095` (quitar después) | `uno_1095.log`; si no dice «mergeado», correr `bash D:/vrp-trabajo/temporales/s190/mergear_verdes.sh 1095` |
| Día MODIS en producción | **funciona**: el NRT ya escribe pasadas diurnas (11 a 13 por volcán desde el 15-nov en Chillán, Villarrica, Láscar, Copahue; todas 0 MW); MIROVA no publicó ninguna alerta MODIS diurna de cumbre esos días (sus 5 diurnas con calor son lejanas, 10 a 33 km, FALSO_POSITIVO) | scripts en `D:\vrp-trabajo\temporales\s194\dia\` |
| Pages | `diurno.js` y `cumbre.js` publicados (HTTP 200); marcador visible en Isluga en el sitio vivo | navegador, 2026-11-22 |
| **Mazos del congreso** (sesión local_4421d9f3) | **corriendo**: copias listas en `D:\vrp-trabajo\temporales\s194_mazos\`, respaldo en `...\congreso geologico 2026\2_PRESENTACIONES\_previo_S194\`; espera su verificador limpio para tocar los .pptx vivos y escribir `ACTUALIZACION_S194.md`. Incluye láminas nuevas de riesgos de la IA y salvaguardas (pedido de Nicolás); su crítica dice que la charla podría no caber en el tiempo | nota `s194_mazos.md` cuando aparezca |
| **Paper** (sesión local_2bbf8c30) | **corriendo**: `revisiones\REVISION_S194.md` commiteada local en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\paper_vrp_chile` (`1e0cffb`, sin push); espera su verificador limpio. La prosa la escribe Nicolás (política de Volcanica) | nota `s194_paper.md` cuando aparezca |
| VIIRS de día | recálculo hecho (regla sellada sha256 `cbb10758...`); veredicto sigue DECIDE NICOLÁS CON M4; V375 recupera 23 de 34 (no 23 de 42: 8 filas OCR eran lejanas); lo recuperado es cumbre real (22 de 23 sobre el punto de MIROVA); **recomienda encender** | `D:\vrp-trabajo\temporales\s194_viirs_dia\INFORME_RECALCULO.md` |
| Áreas del laboratorio | opción A en main (#1092): 624 pasadas con calor en el cráter y fuera a la vez, 528 publicadas lejanas; agua sin repetición de 3 noches; foco de flanco en Chillán 5 a 6 km E (abr-may 2026) | `experiments/_s194_areas/INFORME.md` |
| Camino a la independencia | borrador en `docs/CAMINO_INDEPENDENCIA_MIROVA.md` (loop/activo): falta el requisito del OVDAS, aviso, manual y licencia; latencia S150 5,05 h contra 2,77 h | nota `s194_independencia.md` |
| Comandos nuevos | `/critico` y `/socio` en `C:\Users\nmend\.claude\commands\` (globales) | archivos |
| Disco | C: 28 GB, D: 17 GB (D: llegó a 0 a las ~11:50 UTC; se liberó quitando worktrees de merge) | `df` |
| Sin commitear en `loop/activo` (no son de S194) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |
| PR abiertos | #1095 (en merge), #1015 (miniaturas S184, DIRTY), #913 (plan S163) | `gh pr list` |

Notas de las sesiones: `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_63e4043e-88e1-4b47-b998-e7ecbfaf5413\s194_*.md`.

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Encender el día en VIIRS (375 y 750 juntos) | sí, PR de perfil con A45 y tag / todavía no | **Sí**: el recálculo quitó la contaminación del OCR y lo recuperado es cumbre real; costo ~3 artefactos de 1 MW o más fuera de Chillán en 5 meses. Antes, mirar en imagen los 8 negativos publicados (no se miraron) |
| 2 | Camino a la independencia, C1 a C5 (`docs/CAMINO_INDEPENDENCIA_MIROVA.md` §6) | quién en el OVDAS fija el requisito; marcha blanca ya; aviso automático; licencia y cuenta; fases del visualizador | Empezar por C1: conversar con la jefatura del OVDAS y escribir su requisito |
| 3 | Radio del flanco por volcán (AR3) | 10 km fijo / por edificio volcánico | Por volcán cuando Nicolás lo fije; mientras, 10 km |
| 4 | Laboratorio paso 3 (barrido y zona A en la vía) | A45 sí / esperar | Sí, A45 con tag: el criterio ya está sellado (#1093) |
| 5 | Mazos: preguntas que deje la sesión (salvaguardas del OVDAS sin fuente escrita, duración de la charla) | ver `ACTUALIZACION_S194.md` | ver ese archivo |
| 6 | Heredadas de S194 §b: Laguna del Maule (mover el punto), tabla de episodios OVDAS (D4), Codex ronda 3 desde 2026-11-24 04:20 UTC, rotar el PAT de `settings.json` | | las del bloque S194 |

Preguntas de Nicolás de S194 sin respuesta explícita: ninguna. Las respondidas: prompts (plan escrito), plan por sensor (resumen dado), worktrees (liberados), áreas (AR1 A, AR2 cinco, AR4 sin incendio), criterio del laboratorio (por noche, desde marzo, sorteo temporal), recálculo VIIRS (hecho).

## c. Lo aprendido

- **REGLA GENERAL (disco D:):** los worktrees de merge `s19Xm-<N>` pesan 1,7 GB cada uno y se acumulan; D: se llenó en S194 con 5 de ellos más temporales de pruebas. Quitar el worktree de merge apenas el PR queda MERGED (agregarlo a `uno.sh`). Un subagente con la suite corriendo durante un llenado puede dar resultados falsos: repetir la corrida.
- **REGLA GENERAL (sesiones):** una sesión archivada no siempre quita su worktree si quedó en HEAD desacoplado; revisar `git worktree list` después de archivar.
- **REGLA GENERAL (prompts):** «hasta N» con evidencia, nunca «exactamente N»; un número fijo de preguntas o debilidades empuja a inventar. Comandos `/critico` y `/socio`.
- **REGLA DEL LOOP:** `start_session` sólo funciona en un turno con palabras del usuario; en turnos de notificación usar subagentes en worktrees de D: (no gastan C:).
- **Proyecto:** al unir dos PR de frontend que tocan la misma función (mosaico, minigráfico), revisar en el navegador la combinación: las pruebas de cada PR no cubren la mezcla.
- **Proyecto:** las filas OCR de VIIRS 375 contaminan las «protegidas»: 8 de 19 no recuperadas eran alertas lejanas con distancia leída de otra pasada (ver `reference_ocr_imagen_de_otra_pasada`).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** el día MODIS escribe records en producción; ninguna alerta diurna de cumbre de MIROVA perdida entre el 15 y el 22-nov.
- **SOSPECHA:** el foco de flanco de Chillán (5 a 6 km E, abr-may 2026) es actividad real; cruzar con OVDAS.
- **SOSPECHA:** los episodios del área «resto» en Copahue, Llaima y Chillán son incendios (sin FIRMS; su clave no está configurada).
- **SOSPECHA:** el polígono de agua de 933 km² de Chaitén es el mar (#1092).
- **CONFIRMADO:** la marca de MIR perdida sólo existe en records procesados desde el 2026-11-20 (543 de 77.172); MIR realmente perdida sobre el cráter: 0 de 214 (#1095).

## e. Ya cerrado, no rehacer

- Día MODIS: encendido y verificado (#1090); no reprocesar la historia de día sin decisión aparte.
- Marcador de cumbre: 218 de 707 pasadas lejanas (30,8 %), recupera la vista de las 12 de 12 protegidas sólo OCR; «radiante» se mantiene.
- `anomaly_pixels` trae todos los alertados (10.361 de 10.361) pero no VRP por píxel (se reconstruye por Planck, cierra en 8.997 de 8.997).
- Criterio del laboratorio paso 2 sellado (hash 072400b7) con tasa por noche, calibración desde marzo y sorteo temporal.
- Reflejo solar especular NO explica los artefactos diurnos VIIRS (ángulo 33,9 a 74,1°, corte de MIROVA 12°).
- Regla de merge S193 ya está en el `CLAUDE.md` (#1088).

## f. Prompt para S195

```
Retomas VRP Chile como sesión dueña del loop (S195). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S194 cerró y no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; ficha de main (esperado v1.76 si #1095 entró; si no, mergear_verdes.sh 1095); gh pr list.
   - Quitar D:\vrp-trabajo\worktrees\s194m-1095 y, si ya terminaron, s194-mazos y s194-paper.
   - Sesiones: Mazos (local_4421d9f3), Paper (local_2bbf8c30), VIIRS día (local_78135e33), Independencia (local_adc86ae9).
     Notas en C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_63e4043e-88e1-4b47-b998-e7ecbfaf5413\s194_*.md
   - df de C: y D: (D: se llenó en S194).
   - Primer día completo de MODIS diurno: ¿hay pasadas de tarde con VRP > 0 o falsas alarmas en la vigilancia?
2. Lee tasks/BLOQUE_ARRANQUE_S195.md (rama loop/activo) y la entrada S194 de tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Revisar lo que entreguen Mazos y Paper (verificador limpio, nada sin fuente) y reportárselo a Nicolás.
   b. Decisión 1 de §b (VIIRS de día): si Nicolás dice sí, PR de perfil con A45 y tag, como #1090.
   c. Laboratorio paso 3 si Nicolás da A45.
   d. Codex ronda 3 desde el 2026-11-24 04:20 UTC.
   e. Auditoría semanal del lunes 2026-11-23: primera con el día MODIS; revisar que la frontera diurna funcione.
4. Reglas duras: A45 (tag y sí de Nicolás para EMPEZAR cambios en pipeline/process_*.py, store.py,
   mirova_equivalent.yaml, mirova_v750_codigo.py); los merges que recomiendas los haces tú (CLEAN, CI verde, ficha al
   mergear con D:/vrp-trabajo/temporales/s194/merge/uno.sh, --match-head-commit) e informas; nada de git stash;
   git add por archivo; nunca experiments/_s176_codex/; temporales y worktrees en D: y quitarlos al mergear;
   archivar una sesión ANTES de quitar su worktree; números sólo de scripts; .md con newline="".
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
