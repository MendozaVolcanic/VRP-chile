# Bloque de arranque S198 (escrito por S197, 2026-11-24 ~04:00 UTC)

> El bloque anterior (S197, escrito por S196) queda como histórico en `tasks/BLOQUE_ARRANQUE_S197.md`. Detalle de S197
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S197, arriba) y en la nota viva
> `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_365c6310-1a9b-49ed-a67e-cbc6eb05ccc3\s197_apertura.md`.
> **Estado fijado CON TRABAJO EN VUELO:** (1) tanda 3 del barrido del piso (run 45308651250, abril, 10 volcanes + PCC):
> al cerrar 25 trabajos verdes, 1 rojo (Villarrica trozo 5, 2026-04-21 a 04-25), 6 corriendo y 35 en cola; (2) la sesión
> [Auditoría Codex, ronda 3](#local_93fa2a9d-142e-4f60-932f-a4b32dcc5abe) (`codex-ronda3`) dejó el frente 9 de Codex para
> lanzarse solo a las 04:21 UTC y la cadena sigue con 3 y 5. S197 cerró por el umbral de contexto del hook (416 mil).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.88** | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| Token Earthdata | **rotado por Nicolás** 2026-11-23 23:35:59 UTC tras revocarlo él al generar el de Goes (NASA dio 401 desde 23:02:47 UTC); vence 2027-01-22 23:03 UTC; probablemente el MISMO token que el local de Goes | `nrt-healthcheck` run 45290346623; `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` filas 1 y 2b |
| #1106 Chaitén MODIS 2026-11-19 02:30 (MIROVA 1,07 MW) | **diagnosticado y aceptado**: borde doble (celda tibia una columna fuera de la caja sensible; con la caja en el cráter falla el ETI por 0,15 %); NO es el piso de D36; sin atribuir, probable transitorio o artefacto | #1107 (v1.86) `experiments/_s197_1106/INFORME.md` |
| A/B caja MODIS cráter contra grilla (pedido de Nicolás) | **empate**: 0 de 330 pasadas cambian; 62/62 protegidas y 0/162 negativas en los dos brazos; el brazo actúa (diagnóstico distinto en 15/16 PCC, 14/15 Tupungatito) | #1108 (v1.87) `experiments/_s197_caja_modis/INFORME.md` |
| Chaitén 2026-11-19 02:30 en `PERDIDAS_ACEPTADAS` | MERGED (Nicolás: «Sí, agrégala»); 279 pruebas de la auditoría verdes | #1109 (v1.88) `tests/test_auto_audit_perdida_chaiten_s197.py` |
| Barrido del piso | marzo **completo y válido** en los 10 volcanes. Tanda 2b INVÁLIDA (15 trabajos caídos por el 401); tanda 2c VÁLIDA (control 927/927, donde no actúa 350/350 en 7 pisos; nuevas p300 a p150: Isluga 0 a 41, Tupungatito 9 a 48, PCC 0; sin pérdidas) | run 45291948142; `D:\vrp-trabajo\temporales\s196\barrido\salida_contar_piso_t2c.txt` |
| Tanda 3 (abril, 10 + PCC) | **CORRIENDO**; 1 rojo Villarrica trozo 5 (causa sin mirar) | run 45308651250 |
| Sombra de los 34 (#1099) | GitHub no lanzó la del 23-nov; despachada a mano: 32/32 verdes; Callaqui con 6 y 8 pasadas el 22 y 23-nov | run 45294237082 |
| Sombra código MIROVA (#1110, abierto) | ya verde a las 02:02 UTC del 24-nov | run 45309398042 |
| Guardia MODIS | **PLAZO CUMPLIDO**: 30 protegidas de 29, VERDE (2026-11-24 03:47 UTC). Toca el informe de cierre para Nicolás (§12.9 del programa por sensor) | `data/audit_continuous/guardia_modis_latest.json` |
| Guardias VIIRS 750 y 375 | VERDE, 19 de 29 cada una, vencen 2027-03-11 | `guardia_{v750,v375}_latest.json` (2026-11-23 03:2x UTC) |
| Codex ronda 3 | sesión `codex-ronda3`: Codex propuso 9, 3, 5 y Cierre II (consulta 0,27 M, semana al 97 %), adoptado; copia refrescada a main `a30089468` | `D:\codex-vrp\_salida\ronda2\ESTADO_COORDINACION.md` |
| Radios del visor | **vacío** (23-nov 23:08 UTC) | ArtifactData, Artifact YaZuZ3pWuxfAZQG2UJY7PL, colección `radios` |
| PR abiertos | #1015 (miniaturas), #913 (plan S163) | `gh pr list` |
| Disco | C: 21 GB, D: 12 GB | `df` |
| Sin commitear en `loop/activo` (no son de S197) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Guardia MODIS cumplida (30 de 29): ¿se cierra la guardia K de MODIS? | cerrar tras el informe / seguir hasta el vencimiento | **Esperar el informe de cierre** (S198 lo prepara con la referencia fresca de Mirova-v1) y decidir con él |
| 2 | Radios del edificio por volcán (D-H) | fijarlos en el visor | **Fijarlos en el visor**: P0 entero depende de esto |
| 3 | Resto del §14 de #1103 (D-A LdM, D-C Lastarria, D-D zona A de PCC, D-F, D-G) | ver §14 | las del plan (sin cambio desde S196) |
| 4 | Independencia C1: quién del OVDAS fija el requisito de adopción | | conversarlo con la jefatura |
| 5 | Heredadas: fondo nulo (mejora 1 de §12.11), R-W7 del A/B diurno, marcador del cráter, Laguna del Maule, rotar el PAT de `settings.json` | | las de §12.11 del programa por sensor |

**Preguntas de Nicolás de S197 sin respuesta explícita:** ninguna. «¿Qué implica aceptar esa pérdida y por qué se
generó?» se respondió en texto. «¿Cómo van el resto de las tareas por sensor, en el experimental y en la réplica
exacta?» se respondió en el mensaje de cierre de S197 (resumen corto; el detalle por sensor está en §12.9 a §12.11 de
`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` y en `docs/PLAN_EXPERIMENTAL_MEJORAS_S196.md` §12).

## c. Lo aprendido

- **REGLA GENERAL:** un 401 de NASA puede ser un token revocado a mano al generar otro (Earthdata deja 2 activos). Cruzar
  la hora exacta del corte (último trabajo que bajó bien) con el registro de credenciales; repetir la prueba 30 min
  después distingue ventana de revocación. El `nrt-healthcheck` sólo lee el `exp`: no ve revocaciones. Nunca recibir el
  token por el chat: Nicolás lo carga con `gh secret set`. (memoria `feedback_s197_token_revocado_y_python_i.md`)
- **REGLA GENERAL:** `python -I` ignora `PYTHONIOENCODING`; con `-I` la salida a .txt sale en cp1252.
- **Proyecto:** la distancia que publica MIROVA en MODIS calzó con la distancia de la celda alertada al CENTRO de la
  grilla, no al cráter (un caso, Chaitén 19-nov; SOSPECHA como regla general).
- **Proyecto:** el arnés de D36 (`experiments/_s190_d36/brazos.py`) se había roto con la firma nueva de `detectar_mirova`
  (S195: `zona_a`); `probar_local.py` no lo detectó porque llama al detector directo, no por `procesar_grilla`. Arreglado
  en #1107.
- **Proyecto:** los recortes nativos de D36 (330 pasadas MODIS, float32) permiten A/B locales sin red hasta el
  2026-12-17; en float32 1 de 330 pasadas cambia la detección (PCC 2026-03-16 03:10), comparar brazos locales entre sí.
- **Proyecto:** `uno.sh` en cadena puede chocar en `git fetch` («incorrect old value») si otro fetch corre a la vez;
  reintentar el fetch antes de cada PR (`cadena_1108_1109.sh`).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** tanda 3 con 1 rojo (Villarrica trozo 5, 2026-04-21 a 04-25, 03:36 UTC). Causa SIN MIRAR.
- **CONFIRMADO:** guardia MODIS cumplida (30/29). Falta el informe de cierre.
- **SOSPECHA:** el token del secreto y el local de Goes son el mismo (mismo `exp` al minuto; valores no comparados).
- **SOSPECHA:** el núcleo tibio de Chaitén 19-nov es transitorio o artefacto de vista oblicua con nubes (no se cruzó con
  FIRMS).
- **SOSPECHA (heredada):** enmascaramiento en la detección (P0 parte 3).
- Issues #1106, #1099 y #1110 siguen abiertos al cerrar: el #1099 y el #1110 los cierra el `nrt-monitor` solo con
  corrida verde (ya la hay); el #1106 se resuelve con la próxima auditoría (lunes 2026-11-30).

## e. Ya cerrado, no rehacer

- #1106: no es el piso de D36 (H1 refutada, run 45290835369, ningún brazo alerta); mover la caja al cráter no cambia
  nada (0 de 330). Chaitén 2026-11-19 02:30 aceptada. No reabrir sin un caso nuevo.
- Token rotado y verificado (descarga real en run 45290835369, healthcheck 45290346623).
- Marzo del barrido del piso completo (tandas 1, 2 válida en 6 volcanes, 2c).
- Arreglos del Cierre I de Codex ya en main: C1-101 y C1-106 (#1094), C1-102 y C1-V202 (#1095).
- Lo de §e del bloque S197 sigue valiendo (NHI-v1, barrido de s pausado, MEJ-7, C0, control diurno VIIRS no antes del
  2027-03-07, día MODIS sin falsas alarmas, paper R2).

## f. Prompt para S198

```
Retomas VRP Chile como sesión dueña del loop (S198). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S197 cerró y no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; ficha de main (esperado v1.88); gh pr list (esperado #1015 y #913).
   - gh run view 45308651250 (tanda 3, abril): si terminó, relanza sólo el trozo rojo (reproc-s196-lab-piso.yml con
     barrido_aprobado=si, start 2026-04-21, end 2026-04-25, vols ["Villarrica"]) y mira su causa en el log; con todo
     verde, corre D:\vrp-trabajo\temporales\s196\barrido\contar_brazos_piso.py <run> y lee el COMPARAR del job
     «recolectar» (control idéntico y «donde no actúa» 350/350).
   - Estado de la sesión codex-ronda3 (local_93fa2a9d-142e-4f60-932f-a4b32dcc5abe) y de
     D:\codex-vrp\_salida\ronda2\ESTADO_COORDINACION.md.
   - gh issue list (esperado #1106, #1099, #1110 cerrándose solos); df de C: y D:.
2. Lee tasks/BLOQUE_ARRANQUE_S198.md (rama loop/activo), la entrada S197 de tasks/LOOP_OBJETIVOS.md §6 y la nota
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_365c6310-1a9b-49ed-a67e-cbc6eb05ccc3\s197_apertura.md
3. Trabajo, en orden:
   a. Guardia MODIS CUMPLIDA (30/29): informe de cierre para Nicolás con la referencia fresca de Mirova-v1 (tabla
      consolidada + OCR, como el workflow; §12.9 del programa por sensor).
   b. Barrido del piso por tandas: mayo en adelante (10 volcanes + PCC por mes), revisando COMPARAR en cada una; con
      marzo a hoy completo, evaluar.py calibrar según experiments/_s196_lab_piso/PREREGISTRO.md.
   c. Seguir la ronda 3 de Codex (la lleva su sesión; mergear lo que recomiende con uno.sh).
   d. Radios del visor (ArtifactData, colección radios) -> config/areas_laboratorio.yaml y P0 partes 1 y 2.
4. Reglas duras: A45; merges que recomiendas con D:/vrp-trabajo/temporales/s195/merge/uno.sh (fetch con reintento antes de
   cada uno, ficha al mergear, --match-head-commit); nada de git stash; git add por archivo; nunca experiments/_s176_codex/;
   temporales y worktrees en D:; números sólo de scripts; .md con newline=""; un vigilante por corrida con --interval 60;
   nunca pedir ni recibir tokens por el chat.
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
