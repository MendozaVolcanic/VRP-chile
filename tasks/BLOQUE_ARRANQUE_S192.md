# Bloque de arranque S192 (escrito por S191, 2026-11-20 ~01:45 UTC)

> El bloque anterior (S191, escrito por S190) queda como histórico en `tasks/BLOQUE_ARRANQUE_S191.md`. El detalle de
> cada paso de S191 está en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entradas S191, de la más nueva arriba).
> **El estado se fijó con trabajo en curso** (filas «corriendo» de la tabla a): comprobarlo contra el remoto y `ps`.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | `0d366fc54` a las 01:41 UTC, ficha SDA **v1.47** | `#1060` mergeado 2026-11-19 23:05:00 UTC (`1d96f6417`) |
| `loop/activo` | commit de este cierre, sobre `ee2171dd4` | `git ls-remote origin -h refs/heads/loop/activo` |
| Marcador del cráter (paso A, F1M G3) | **en main** (#1060, v1.47): claves `crater_sin_posicion`, `px_mir_invalido_crater`, `px_saturados_crater` en `diag_codigo_mirova` | suite 4211 pasan; mutaciones 10/10; verificador 6/6 |
| PR #1061: los 34 como preliminares (N1 y D14 opción b, decisión de Nicolás 2026-11-20) | **abierto, espera «mergea #1061»**; fila de ficha en la descripción | prueba nueva 4 rojas antes y 4 verdes después; frontend 693 pasan + G8 actualizada; verificador 5/5 |
| PR #1062: unión de la tanda 5 de la historia de los 34 | **abierto, espera «mergea #1062»**; tras el merge, aplicar con `aplicar-reemplazo.yml` y tag `pre-historia-34-tanda5` | 5 volcanes, 626 días, 0 huecos; ensayo 35.285 nuevos; verificador 5/5; `D:\vrp-trabajo\temporales\s191\tanda5_numeros.txt` |
| Historia de los 34, tandas 1 a 4 | aplicadas (18 volcanes) | `experiments/_historia_34/TANDAS.md` (fila aplicada de la tanda 4 viene en #1062) |
| Tanda 6 (Calbuco, YateHornopiren, Huequi, Michinmahuida, CorcovadoYanteles) | **corriendo**: run 44653724540, en cola a las 01:41 UTC | log `D:\vrp-trabajo\temporales\s187_tanda2\cadena_5a7_s191.log` |
| Cadena de tandas 6 y 7 | **corriendo**: `cadena_5a7_s191.sh` (relanzada tras el reinicio del PC de las 23:17 UTC del 11-19). Relanza rojos hasta 3 veces y sólo con 0 rojos despacha la 7 | `ps -ef \| grep cadena_5a7_s191` |
| A/B del día (#813, sesión local_1a9c0903) | su `cadena_ventanas.sh` vive de nuevo (relanzada por esa sesión tras el aviso de S191); run 44635196200 en cola | `ps -ef \| grep cadena_ventanas` |
| Sync de MIROVA y panel de #1046 | **hecho**: sync despachado a mano (run 44573365902, commit `6e6620be9` con `pasadas_tabla`), Pages a mano; panel visible en el sitio | Isluga VIIRS 375: «TP=28 FP=0 · sin dato 3 · fuera de radio 0» |
| Sesión «Limpieza de worktrees y espacio en disco» (local_325cc12c) | **a medias**: inventario 15 de 22 worktrees; nada borrado; pedirá confirmación (A38) | `D:\vrp-trabajo\temporales\s191\limpieza\INVENTARIO.md` (cuando exista) |
| Sesión «Auditoría Codex, ronda 2: frente 2 y siguientes» (local_4d3dbc4c) | **corriendo**: propuesta F2 unificada con F4-101; pase B del frente 2 y frente 3 en Codex; un pytest suyo en `D:\vrp-trabajo\worktrees\s191-f2-documentos` | `D:\codex-vrp\_salida\ronda2\PROPUESTA_F2_PARA_NICOLAS.md` |
| Sesiones F4-101 (local_2b6790b0) y TIR perdida (local_ba18aef9) | **terminadas**, informes escritos | `D:\vrp-trabajo\temporales\s191\f4_101\INFORME.md`, `...\tir_perdida\INFORME.md` |
| S191 en la barra lateral | sacada de bajo S190 (pedido de Nicolás) | `detach_session self` |
| Sin commitear en `loop/activo` (no son de S191, no se commitean) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |
| `.claude/launch.json` | agregada la configuración `vrp-frontend-s191-prelim` (puerto 8191, worktree de #1061); ignorado por git | `.gitignore` l. 37 |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Mergear #1061 (34 preliminares) | sí / revisar antes | Sí: sólo presentación, verificado |
| 2 | Mergear #1062 (unión tanda 5) y aplicarla | sí / revisar | Sí; antes de publicar, mirar Lanin feb-2025 (64 de 66 detecciones >5 MW a 14 a 29 km, posible incendio) |
| 3 | Fondo nulo (F4-101 + F2-108, propuesta unificada §1 de `PROPUESTA_F2_PARA_NICOLAS.md`) | (a) MODIS escena no medida + VIIRS sólo marca; (b) marcar en los tres; (c) nada | (a). El OSF v2.5 no tiene ninguna detección MODIS con fondo 0 en 262.455; en VIIRS 375 MIROVA sí lo hace. Toca el detector: A45, plan y prueba roja antes |
| 4 | TIR perdida en el cráter (informe `tir_perdida`) | separar la marca de #1060 en MIR y TIR / nada | Separar (diagnóstico); no cambiar el remuestreo (el `.m` hace lo mismo y la potencia se acerca a la real) |
| 5 | Paso B del marcador | B1 «sin dato» / B2 avisar | Esperar semanas de marcas y decidir con el conteo |
| 6 | Frente 6 (NRT rojo y fila «no medida») | `D:\codex-vrp\_salida\ronda2\PENDIENTES_F6_PARA_NICOLAS.md` | Rojo si un volcán no mide nada; fila por pasada fallida |
| 7 | F1M-114 (docstring de `process_modis.py`, A45) | sí / no | Sí |
| 8 | Archivos de abril de los 34 (D15) | archivar / borrar / dejar | Archivar con tag (A38) |
| 9 | Reintento en `sombra-34.yml` y `sombra-codigo-mirova.yml` | sí / no | Sí |
| 10 | D-10 (abrir el día) | esperar A/B W5 a W7 | Decidir con el A/B completo; si se abre, extender el cron externo del NRT a 15-22 UTC |
| 11 | D5, D13, D10/Compuerta B, D11 de los 34 (`tasks/DECISIONES_34_S187.md` §2) | ver documento | Las del documento |
| 12 | Rotar el PAT de `C:\Users\nmend\.claude\settings.json` | | Sí (lo hace Nicolás) |

Preguntas de Nicolás de S191 sin respuesta explícita: ninguna. «revisa como vamos... que falta... que falencias» se respondió en texto; «sigamos en paralelo, revisa worktrees, lanza sesiones, saca la S191 de bajo de la S190» se ejecutó (la limpieza sigue a medias en su sesión).

## c. Lo aprendido

- **REGLA GENERAL:** un archivo de evidencia vale más que la frase que lo resume. El bloque S191 decía «26 rojos, todos Install deps»; `t5_fallas.txt` tenía 19 de 26 (7 eran descargas fallidas de NASA en modo estricto). Al escribir una causa, contarla en el archivo. (Memoria `feedback_s191_causa_del_archivo.md`.)
- **REGLA GENERAL (Windows):** reescribir un `.md` con Python sin `newline=""` convierte CRLF en LF y el diff marca el archivo entero (153 líneas por 3 cambios). Leer y escribir con `newline=""`. (Misma memoria.)
- **REGLA DEL LOOP:** un subagente de una sesión cerrada puede commitear en un worktree que la sesión nueva está revisando (`8ae072e2b`, 17:39 UTC): antes de commitear, `git log` del worktree y aviso a la sesión dueña.
- **Proyecto:** el cron horario de `sync-mirova-csv.yml` corre muy espaciado (12:59, luego nada hasta despacharlo a mano a las 17:05); un push hecho con `GITHUB_TOKEN` no dispara `pages-deploy.yml`, que publica por su cron cada 2 h. Para ver un cambio de datos de MIROVA ya, despachar los dos.
- **Proyecto:** el NRT tiene huecos de 5 a 9 h entre las 12 y las 01 UTC por diseño (cron externo 01-12 UTC, S142); no pierde datos nocturnos.
- **Proyecto:** el modo estricto del reproceso de historia corta un trozo entero (salida 3) por una sola descarga fallida de LAADS; la cadena lo relanza.
- **Proyecto:** CI de PR con runners ocupados por tandas y el A/B: 4 h en #1060.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** reinicio del PC 2026-11-19 23:17 UTC mató `cadena_5a7_s190d.sh` y `cadena_ventanas.sh`; las dos relanzadas.
- **CONFIRMADO:** fondo nulo (F4-101): 19 records en `data/mirova_equivalent` + 1 en `data/sombra_34` (MacaCay VIIRS 750 2026-11-15); 2 FP probados (PCC MODIS 2026-03-16, Tupungatito VIIRS 750 2026-05-15).
- **CONFIRMADO (sintético):** TIR perdida en el cráter sube la VRP sólo en VIIRS con foco que calienta la TIR; el oráculo del `.m` da las mismas matrices; MIR perdida da 0 MW en los tres sensores.
- **SOSPECHA:** Lanin feb-2025 (64 detecciones >5 MW, máximo 75,1 MW, a 14 a 29,5 km) y Callaqui mar-2025 son incendios forestales; sin verificar con otra fuente.
- **SOSPECHA:** la falla 27 de la tanda 5 (Osorno 32, «Reprocesar» y «C-via», 22:23 UTC) es otra descarga fallida; causa no revisada.
- **SOSPECHA:** `distance_class` nulo en todos los records de los 34 es por diseño (D5, `derivarClaseSombra` en el tablero); no verificado en el pipeline.
- **SIN DATO:** qué hace MIROVA con un píxel con una sola banda inválida en su remuestreo (no publicado).

## e. Ya cerrado, no rehacer

- Marcador del cráter, paso A: en main (#1060, v1.47). El blindaje de `quality_flags` no entero está incluido.
- Sync de MIROVA con `pasadas_tabla` y panel de #1046 en el sitio: hecho y visto en el navegador.
- `CLAUDE.md` de `loop/activo` traído de main (`b9e536200`).
- N1 y D14 de los 34: decididas (opción b); implementación en #1061.
- TIR perdida: no es un defecto de fidelidad (el `.m` hace lo mismo); no cambiar el remuestreo.
- Ventana del cron externo del NRT (01-12 UTC): es diseño de S142, no un fallo; el token del cron externo no vence (`REGISTRO_CREDENCIALES.md` fila 31).
- Guardias al 2026-11-20: MODIS, VIIRS 750 y 375 VERDE, 0 candidatas a reversión.

## f. Prompt para S192

```
Retomas VRP Chile como sesión dueña del loop (S192). Español de Chile, sin guiones largos, rutas absolutas.
Una sola sesión dueña del loop: S191 cerró.

1. Verifica antes de creer:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" && git fetch origin --prune
   git status -sb   (loop/activo; compara git rev-parse HEAD con git ls-remote origin -h refs/heads/loop/activo)
   ps -ef | grep -v grep | grep -E "cadena|pytest"   (al cierre vivían cadena_5a7_s191.sh y cadena_ventanas.sh)
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i '^date'   (A86)
   tail -5 D:/vrp-trabajo/temporales/s187_tanda2/cadena_5a7_s191.log   (tanda 6: run 44653724540)
   gh pr list   (#1061 y #1062 de S191 esperaban «mergea»)
   Compara el CLAUDE.md de loop/activo con el de main.
2. Lee: tasks/BLOQUE_ARRANQUE_S192.md, la bitácora tasks/LOOP_OBJETIVOS.md §6 (entradas S191) y el MEMORY.md.
3. Trabajo, en orden:
   a. Con «mergea #1061» / «mergea #1062»: une main, numera la ficha (sólo #1061 la lleva) con
      D:/vrp-trabajo/temporales/s190/lote7/uno.sh (copia body_<N>.md desde gh pr view), espera CI, merge
      --match-head-commit. #1062 sin ficha: merge y luego aplicar-reemplazo.yml con tag pre-historia-34-tanda5.
   b. Tanda 6: cuando la cadena la deje limpia, bajar_trozos.sh <run> D:/vrp-trabajo/temporales/historia_34/tanda6/run1,
      touch .completa, BASE=.../tanda6 WT=D:/vrp-trabajo/worktrees/s192-tanda6 RAMA=s192-historia34-tanda6 bash
      D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh <run>; números con un script como
      D:/vrp-trabajo/temporales/s191/tanda5_numeros.py; TANDAS.md con la fila aplicada de la 5; verificador; PR.
   c. Sesiones de S191: «Limpieza de worktrees y espacio en disco» (local_325cc12c, pedirá confirmación A38) y
      «Auditoría Codex, ronda 2: frente 2 y siguientes» (local_4d3dbc4c). Relévale a Nicolás lo que pidan.
   d. Lleva a Nicolás las decisiones de la sección b, con recomendación (la 3, fondo nulo, es la que más pesa).
4. Reglas duras: A45 (tag y sí de Nicolás antes de pipeline/process_*.py, store.py, mirova_equivalent.yaml y
   pipeline/mirova_v750_codigo.py), todo PR con «mergea #N», merge commit --match-head-commit, ficha al mergear,
   nada de git stash, git add por archivo, nunca experiments/_s176_codex/, temporales y worktrees en D:, números con
   script, archivos .md reescritos con newline="".
5. Cierra con /cierre al llegar al umbral de contexto del hook (base + 250 mil).
```
