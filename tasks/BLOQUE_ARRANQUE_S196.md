# Bloque de arranque S196 (escrito por S195, 2026-11-23 ~05:00 UTC)

> El bloque anterior (S195, escrito por S194) queda como histórico en `tasks/BLOQUE_ARRANQUE_S195.md`. Detalle de S195
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S195, arriba) y en la carpeta de notas
> `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_2a09ce8a-792a-4847-9085-2c485762b00d\s195_*.md`
> (decisiones de Nicolás en `s195_decisiones.md`). **Sin trabajo en vuelo al fijar el estado**: ningún subagente ni
> cadena de merge vivos (`ps` sin `gh run watch`, `uno.sh` ni `cadena`).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.78** | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1095 (cráter no medido, MIR saturada) | MERGED 2026-11-22 12:38 UTC, v1.76; worktree `s194m-1095` quitado | `gh pr view 1095` |
| **#1097** pre-registro del control diurno VIIRS | MERGED 2026-11-23 00:21 UTC, **v1.77**; sha256 del evaluador `24050c7a...`; veredicto único **no antes del 2027-03-07** | `experiments/_s195_viirs_dia_control/PREREGISTRO.md`; log `D:\vrp-trabajo\temporales\s195\merge\uno_1097.log` |
| **#1096** laboratorio paso 3 (zona A del cráter, diseño (a)) | MERGED 2026-11-23 00:39 UTC, **v1.78**; tag `pre-s195-laboratorio-paso3`; producción idéntica byte a byte; perfiles `_s195_lab_control` y `_s195_lab_s50`..`_s10`; workflow `reproc-s195-lab-barrido.yml` | `docs/superpowers/plans/2026-11-22-laboratorio-paso3.md`; `cadena_1096.log` |
| Prueba de humo del barrido | **verde**: run 45093187693 (Villarrica 2026-11-10 a 12, 10 brazos); COMPARAR «IDENTICOS: 25 records pareados, 0 distintos» (s = 5,0 contra control) | rama `s195-lab-barrido/45093187693` |
| Barrido completo (2026-03-01 a hoy, 10 volcanes) | **NO despachado**: ~540 jobs (cifra medida sobre K, sin verificar en la vía); espera el sí de Nicolás; por tandas | cabecera del yml |
| Día MODIS en producción | 143 pasadas diurnas desde el 15-nov en los 11 Tier A, 0 con VRP > 0 (conteo del 22-nov 14:25); en el tablero vivo apareció Chillán MODIS_AQUA 2026-11-22 20:40 ☀ 6,654 MW (Chillán en erupción) | `D:\vrp-trabajo\temporales\s195\dia_modis\RESULTADO.md` |
| VIIRS de día | **apagado** por decisión de Nicolás («No encender aún»): 3 de los 8 negativos publicados eran artefactos ≥ 1 MW en cumbre (Láscar flanco E; Cordón Caulle a 17 y 18,5 km) | `s195_viirs_dia.md` |
| Sesiones archivadas | 24 (S176 a S193 y laterales); vivas: S194, mazos, paper, VIIRS día, independencia, miniaturas (#1015) | `s195_revision_sesiones.md`; notas respaldadas en `D:\vrp-trabajo\temporales\s195\notas_respaldo\` |
| Mazos del congreso | L8/L14 de AT3.6 **restauradas** (charlas de 15 + 5 min, P1 cerrada «cabe»); logos (congreso y SERNAGEOMIN; RNVV sin logo en su web) y lámina AT8.7 L2 «Lo que cambia con un sistema propio»; AT8.7 ~13:30 nominal | `...\congreso geologico 2026\2_PRESENTACIONES\ACTUALIZACION_S196.md` |
| Difusión Instagram del congreso | **lista para que Nicolás envíe**: textos de 40 palabras, imágenes y foto | `...\congreso geologico 2026\3_MATERIAL\difusion_instagram\RESPUESTA_DIFUSION.md` |
| Sesión del congreso de VRP Chile | **AT8.7** (web del congreso, 2026-11-23); el «AT8.3» del PDF de la plataforma es un error de la plataforma (AT8.3 es geoquímica de fluidos) | https://www.congresogeologicochileno.cl/program/sessions |
| PR abiertos | #1015 (miniaturas S184, DIRTY), #913 (plan S163, CLEAN, docs) | `gh pr list` |
| Disco | C: 25 GB, D: 19 GB; worktrees: sólo el checkout canónico | `df`, `git worktree list` |
| Sin commitear en `loop/activo` (no son de S195) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` (12 entradas, las mismas del inicio) |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Despachar el barrido completo del laboratorio paso 3 | sí, por tandas / esperar | **Sí, por tandas** (2 a 3 volcanes y ~1 mes por despacho), revisando la identidad del brazo 5,0 en cada tanda. Ojo: el crítico de #1096 sospecha que el piso 0,003 limita la palanca (con s = 1 el umbral le gana al piso en sólo 16 de 5.518 pasadas MODIS, 26 de 10.362 V750 y 0 de 10.368 V375): si la tasa se aplana, la palanca es el piso y pide otro pre-registro |
| 2 | Control diurno VIIRS: ¿una sola mirada en marzo de 2027? | sí / medir antes con lo ya ocurrido | **Sí** (sin respuesta explícita todavía) |
| 3 | NHI-v1 centra Nevados de Chillán a 60,97 km, junto a Antuco: corregir y re-sellar #1097 y el laboratorio paso 2 | corregir y re-sellar / dejar Chillán fuera de NHI | **Corregir y re-sellar** antes de medir nada (sin respuesta todavía) |
| 4 | Independencia C1 a C5 (`docs/CAMINO_INDEPENDENCIA_MIROVA.md`, sólo en loop/activo) | | empezar por C1 (requisito escrito del OVDAS) |
| 5 | Mazos P2 a P8 (`ACTUALIZACION_S194.md` §4) y Q1 a Q5 (`ACTUALIZACION_S196.md`) | | ver esos archivos |
| 6 | Paper R2 (recall con o sin alertas diurnas en `paper_numbers.py` del repo público) | arreglar el script / borrar la frase | **Arreglar el script** con la regla de la auditoría semanal (el arreglo lo hace el loop tras el sí) |
| 7 | Radio del flanco (AR3) | 10 km fijo / por edificio | 10 km mientras no se fije por volcán |
| 8 | Heredadas: Laguna del Maule (mover punto), episodios OVDAS (D4), Codex ronda 3 desde 2026-11-24 04:20 UTC, rotar el PAT de `settings.json` | | las del bloque S194 |

**Preguntas de Nicolás de S195 sin respuesta explícita:** ninguna. Las tres preguntas del control diurno quedaron con
respuesta parcial: Nicolás respondió con un criterio general («deberiamos apuntar a lo mismo que tiene mirova, si el
tiene artefactos nosotros tambien»), aplicado como «cero pérdidas de lo que MIROVA publica»; las preguntas 2 y 3 de §b
no las contestó.

## c. Lo aprendido

- **REGLA GENERAL (redacción para difusión):** en un post con título visible, la descripción no debe repetir el título;
  contar palabras con script; «en pocos meses» junto a «con IA» se lee como apurado, «validados por profesionales» lo
  compensa; preferir capacidades verificables («zonas configurables») a afirmaciones de operación («filtra»).
- **REGLA GENERAL (imágenes para redes):** recortar barras de navegador (IP interna) y difuminar nombres de personas
  antes de publicar una foto de pantalla; medir la razón de aspecto del espacio de destino (la figura del post del
  congreso es ~3:2 apaisada) antes de armar un collage.
- **REGLA GENERAL (Windows):** PIL no puede sobrescribir una imagen abierta en el visor de Nicolás (`OSError 22`):
  guardar con sufijo de versión y mover la vieja a `_antiguas\`.
- **Proyecto:** en el tablero, los rectángulos amarillos del mapa son «Píxeles medidos» de la última pasada; el anillo
  verde es «confirmado por MIROVA» (`frontend/index.html:3727`); `?volcano=<clave>` abre el detalle con `#hotspot-map`.
- **Proyecto:** el script de merge `uno.sh` ahora quita su worktree al quedar MERGED
  (`D:\vrp-trabajo\temporales\s195\merge\uno.sh`); úsalo en vez del de S194.
- **Proyecto:** el número de sesión del PDF de la plataforma del congreso puede estar mal; mandar el nombre de la sesión
  y verificarlo en la web del congreso.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** el brazo s = 5,0 del laboratorio reproduce al control (25 de 25 records, Villarrica, 3 días).
- **SOSPECHA:** el piso 0,003 hace que bajar s casi no cambie nada (cifras del crítico de #1096, sin barrido).
- **SOSPECHA:** el costo del barrido completo (~540 jobs, ~47.000 min de runner) está medido sobre K, no sobre la vía.
- **CONFIRMADO:** NHI-v1 centra Nevados de Chillán a 60,97 km (hallazgo de #1097; afecta también el laboratorio paso 2).
- **SOSPECHA:** el foco de flanco de Chillán (5 a 6 km E, abr-may 2026) es actividad real (heredada de S194).
- **SIN VERIFICAR:** el record de la guardia K con el código de #1096 (la pasada sintética no llega a su lector; la
  guardia no pasa por el código cambiado).

## e. Ya cerrado, no rehacer

- VIIRS de día: NO se enciende por ahora (decisión de Nicolás del 2026-11-23); el control diurno ya está pre-registrado
  (#1097) y no se mide antes del 2027-03-07.
- Zona A del laboratorio: diseño (a) elegido por Nicolás («Sólo la caja sensible»); (b) y (c) descartados; 4.636 celdas
  del círculo caen fuera de la caja sensible (`D:\vrp-trabajo\temporales\s195\lab_paso3\salida_contar_zona_a.txt`).
- Día MODIS: sin falsas alarmas diurnas en 143 pasadas; no reabrir sin datos nuevos.
- Mazos: P1 (reloj) CERRADA, las charlas son de 15 + 5 min; L8 y L14 de AT3.6 en su lugar (sha256 igual al respaldo).
- Sesión del congreso de VRP Chile: AT8.7 (verificado en la web); no cambiar los mazos.
- Difusión: textos e imágenes cerrados con Nicolás; falta sólo que él envíe el correo (y nombres de pila de coautores
  de AT3.6).

## f. Prompt para S196

```
Retomas VRP Chile como sesión dueña del loop (S196). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S195 cerró y no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; ficha de main (esperado v1.78); gh pr list (esperado #1015 DIRTY y #913).
   - git worktree list (sólo el checkout canónico); df de C: y D:.
   - Sesiones vivas del proyecto (list_sessions limit 30, filtra VRP Chile, paper_vrp_chile, congreso geologico 2026):
     S194 loop (local_2a09ce8a), Mazos (local_4421d9f3), Paper (local_2bbf8c30), VIIRS día (local_78135e33),
     Independencia (local_adc86ae9), Miniaturas (local_62838c8e). Notas en
     C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_2a09ce8a-792a-4847-9085-2c485762b00d\
     (s195_*.md y s196_*.md).
   - Primera vigilancia diaria con el día MODIS encendido (23-nov): ¿falsas alarmas diurnas?
2. Lee tasks/BLOQUE_ARRANQUE_S196.md (rama loop/activo) y la entrada S195 de tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Llevar a Nicolás la decisión 1 de §b (barrido completo por tandas) y, con su sí, despachar la primera tanda de
      reproc-s195-lab-barrido.yml desde main con barrido_aprobado=si, revisando COMPARAR en cada tanda.
   b. Decisiones 2 y 3 de §b (control diurno: mirada única y caja de Chillán de NHI-v1); con sí a la 3, PR de re-sello.
   c. Auditoría semanal del lunes 23-nov: primera con el día MODIS; revisar la frontera diurna.
   d. Codex ronda 3 desde el 2026-11-24 04:20 UTC.
   e. Ofrecer archivar las sesiones de S194 ya terminadas (sólo con el sí de Nicolás; archivar antes de quitar worktrees).
4. Reglas duras: A45 (tag y sí de Nicolás para EMPEZAR cambios en pipeline/process_*.py, store.py,
   mirova_equivalent.yaml, mirova_v750_codigo.py); los merges que recomiendas los haces tú (CLEAN, CI verde, ficha al
   mergear con D:/vrp-trabajo/temporales/s195/merge/uno.sh, que quita su worktree, --match-head-commit) e informas;
   nada de git stash; git add por archivo; nunca experiments/_s176_codex/; temporales y worktrees en D:; números sólo
   de scripts; .md con newline=""; scripts con rutas Windows escritos con Write.
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
