# Bloque de arranque S193 (escrito por S192, 2026-11-20 ~21:00 UTC)

> El bloque anterior (S192, escrito por S191) queda como histórico en `tasks/BLOQUE_ARRANQUE_S192.md`. El detalle de
> cada paso de S192 está en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entradas S192, la más nueva arriba).
> **El estado se fijó con trabajo en curso** (filas «corriendo» de la tabla a): comprobarlo contra el remoto y `ps`.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.51** a las 20:55 UTC | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| `loop/activo` | commit de este cierre, sobre `e58e9cef9` | `git ls-remote origin -h refs/heads/loop/activo` |
| #1061, #1062 (tanda 5) | en main; los mergeó la sesión «s192» (local_841efdd9, 01:46 a 02:14 UTC) y aplicó la tanda 5 (run 44658784431, commit `da372acd1`) | `D:\vrp-trabajo\temporales\s191\merge_106*.log` |
| #1063, #1064 (documentos Codex frentes 2 y 3) | en main, ficha v1.49 y v1.50; los mergeó S192 con la orden de Nicolás en la sesión Codex («mergea #1063 y después #1064») | `D:\vrp-trabajo\temporales\s192\merge\` |
| **#1065 fondo nulo, opción (a)** | **en main** 17:50 UTC, ficha **v1.51**, tag A45 `pre-s192-fondo-nulo`. MODIS sin fondo bajo ningún alertado = escena no medida (`motivo_vacio` «fondo_no_estimado»); VIIRS igual y con marca `alertados_sin_fondo`; `t_bg_k` sólo con alertados con fondo; rótulo «fondo no estimado» en el tablero | suite 4.224 pasan (`D:\vrp-trabajo\temporales\s192\fondo_nulo_suite.txt`); mutaciones 6 de 6; verificador limpio |
| **Reemplazo de los MODIS sin fondo ya guardados** | **pendiente**: el código nuevo no reescribe records viejos. 14 al 2026-11-20 en `434c21a37` (6 de los 11 y 8 de la historia de los 34) más 1 de la tanda 6 (CorcovadoYanteles); recontar con la tanda 7 aplicada | `D:\vrp-trabajo\temporales\s192\plan\fondo_nulo_lista.py` |
| #1066 tanda 6 | en main 17:35 UTC y aplicada (run 44784790668, tag `pre-historia-34-tanda6`, commit `41cbd0b88`): **28 volcanes con historia** | `experiments/_historia_34/TANDAS.md` |
| **Tanda 7** (Melimoyu, MacaCay, Mentolat, Hudson) | **corriendo**: run 44768057665, a las 20:55 UTC 54 trabajos verdes, 6 en curso, 73 en cola. Cadena `cadena_7_s192.sh` viva (cuenta rojos por trozo); sólo vigila, no une | log `D:\vrp-trabajo\temporales\s192\tanda7\cadena.log` |
| **#1067 tablero** (F5-105 «no cargó» y F5-101 «Sin anomalía») | **«mergea #1067» dado por Nicolás**; la ficha v1.52 la empujó la sesión del tablero (`492834454`, revisada: cabecera v1.52 y una fila); mergeador `mergear_verdes.sh 1067` **corriendo**, espera el CI | log `D:\vrp-trabajo\temporales\s192\merge\merge_1067b.log` |
| §12.11 del plan por sensor | escrita (`70418272a`): guardias, marcador, fondo nulo, TIR, Codex, los 34, cinco mejoras | `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §12.11 |
| Codex ronda 2 | frentes 2, 3 y 5 cerrados (205 filas en total, ninguna de gravedad 4 o más); frentes 9 a 12 para la próxima sesión de Codex; Codex en 73 % de la semana | `D:\codex-vrp\_salida\ronda2\ESTADO_COORDINACION.md`, `RESUMEN_F5_PARA_NICOLAS.md` |
| A/B diurno (#813, sesión local_1a9c0903) | W2 a W7 bajadas (W7 verde 09:43 UTC); S192 le pidió la cobertura A108 de W6 y W7; el veredicto espera R-W7 | `D:\vrp-trabajo\temporales\s190_diurno\cadena_log.txt` |
| Sesión «Limpieza de worktrees» (local_325cc12c) | espera decisión de Nicolás (mover carpetas, hibernación) | `D:\vrp-trabajo\temporales\s191\limpieza\INVENTARIO.md` |
| **Sesiones lanzadas por S192 después del cierre** (Nicolás: «continua con todo, si es necesario abre sesiones paralelas») | «Reemplazo de los MODIS sin fondo ya guardados» (local_0dbb6738): script y prueba para `aplicar-reemplazo.yml`, PR sin aplicar. «Marcador del cráter: ¿el MIR inválido en VIIRS es bow-tie?» (local_b41707b7): sólo lectura, informe en `D:\vrp-trabajo\temporales\s192\bowtie\INFORME.md`. «Auditoría Codex, ronda 2: frentes 9 a 12» (local_b9a0c0a7). La sesión del tablero (local_b2a2dcac) sigue con F5-114 y F5-V201 tras #1067 | `mcp__ccd_session_mgmt__list_sessions` |
| Sin commitear en `loop/activo` (no son de S192, no se commitean) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |
| PR abiertos ajenos | #1015 (miniaturas, S184) y #913 (plan, S163) | `gh pr list` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Cómo reemplazar los MODIS sin fondo ya guardados (lo aprobado en la opción a) | transformación determinista vía `aplicar-reemplazo.yml` / reproceso de esas fechas con `--overwrite` | Transformación: `L_bk = 0` con VRP > 0 en MODIS equivale exactamente a «ningún alertado con fondo», y el record nuevo es la rama vacía de `procesar_grilla`; con prueba de igualdad contra `procesar_grilla` en la pasada 3933. Después de aplicar la tanda 7 |
| 2 | R-W7 del A/B diurno (`experiments/_s190_diurno/PREGUNTA_R_W7.md`, rama `s190-diurno`) | lectura 1 literal / lectura 2 simétrica | Lectura 2: conserva la capacidad de decir NO ADOPTAR |
| 3 | Marcador del cráter antes del paso B (mejora 2 de §12.11) | separar MIR/TIR y no contar el relleno bow-tie / dejarlo | Separar y confirmar bow-tie abriendo un gránulo NOAA-21 (A45, sin efecto en detección) |
| 4 | F2-V303 (`roi` dice `def` en VIIRS 375) y F3-107 (VRP indeterminado como 0,0), A45 | sí / no | Sí, en un PR chico |
| 5 | F3-110 («or» de la Tabla 1 en MODIS) | medir con el A/B de 330 pasadas / nada | Medir, después de la tanda 7 |
| 6 | Cotejar con FIRMS las detecciones lejanas de 5 MW o más de los 34 (mejora 4) | sí / no | Sí, sólo lectura, antes de D1 a D15 |
| 7 | Resto del frente 5 (F5-114, F5-V201, F5-V301, F5-106, firma de comparacion) | PR por tema / dejar | PR: F5-114 y F5-V201 primero (rótulos que inducen a error) |
| 8 | Mover `Goes`, `Automatizacion web` y `Diversion` a D:; apagar la hibernación (13,6 GB) | sí / no | Sí; la hibernación la apaga Nicolás |
| 9 | Rotar el PAT de `C:\Users\nmend\.claude\settings.json` | | Sí (Nicolás) |
| 0a | **Lector M13 de la vía corta a 512 K** (hallazgo de la sesión bow-tie, `D:\vrp-trabajo\temporales\s192\bowtie\INFORME.md` §5): en `VJ202MOD_NRT` v2.1 la M13 viene en uint32 (válidos hasta 327670) y el lector pone NaN todo DN >= 65528, o sea M13 sobre 512,1 K; un foco efusivo fuerte se borraría antes de interpolar. No ha actuado (máximo publicado 358,7 K). A45 | arreglar el corte por `valid_max` del archivo / dejar | Arreglar pronto, con prueba roja y tag; revisar si el camino K tiene el mismo corte |
| 00 | **F11-102, gravedad 4 CONDICIONAL (Codex frente 11, verificador limpio):** si se aplica la reversión pre-autorizada de un sensor (`git revert` de su PR), la serie de los 11 pasa de vía a K sin ninguna marca: `frontend/cambio_detector.js::primeraVia` sólo marca K seguido de vía. La potencia caería a cerca de la mitad sin aviso. Hoy hay 0 records K en producción, así que la marca naranja ya no se dibuja y la premisa de `REGLA_REVERSION_MODD` §4.7 punto 2 es falsa. Relacionados (gravedad 3): F11-V201 (el revert no toca los 73.047 records de la vía anteriores al encendido), F11-104 (el NRT no repone con K los records estándar), F11-101 (si a la guardia K le falta la pasada que la vía calla, la vigilancia queda VERDE). Hoy 0 de 48 protegidas calladas, ninguna reversión en curso. Evidencia: `D:\codex-vrp\_salida\ronda2\f11_verificacion\VEREDICTO.md` | (a) suspender la reversión pre-autorizada hasta que el tablero marque vía→K y una regla diga qué pasa con la historia; (b) dejarla y arreglar después | **(a)**: una reversión sin marca haría leer como baja de actividad un cambio de método. Arreglo de tablero fuera de A45 + enmienda de las reglas de reversión, en una sesión aparte |
| 01 | **Tanda 7 detenida (2026-11-21 05:23 UTC):** 3 trozos rojos tras 3 relanzamientos, todos el trozo 28 (2026-07-30 a 08-18) de Mentolat, Hudson y MacaCay: `MOD021KM.A2026213.0300` (Terra 2026-08-01 03:00) da `ValueError: No points given` en la vía (error determinista, job 136733185611). Tarjeta propuesta «Vía MODIS: No points given» (task_e399f2d6). SOSPECHA: el filtro de cobertura cuenta geolocalización y `griddata` recibe 0 puntos con radiancia. Puede repetirse en el NRT | arreglo A45 (escena vacía con motivo propio) y relanzar el trozo 28 | Sí, con tag y prueba roja |
| 02 | **Codex ronda 2 completa:** frentes 9 a 12 cerrados (82 filas nuevas, 287 en total); sólo F11-102 en gravedad 4 (condicional). Sin PR; resúmenes en `D:\codex-vrp\_salida\ronda2\` | llevar los resúmenes de 9 a 12 a Nicolás | Leerlos en S193 |
| 03 | #1071 y #1072 (suspensión de la reversión): «mergea #1071 y #1072» de Nicolás dado en S192; MERGEADOS: #1071 a las 05:30 UTC (v1.55) y #1072 a las 05:50 UTC (v1.56) del 2026-11-21; antes decía «mergeo en curso al escribir esto» (`D:\vrp-trabajo\temporales\s192\merge\cadena_1071_1072.log`, ficha v1.55 y v1.56) | comprobar | Comprobar con `gh pr view` |
| 0a-ter | **#1070 en main** 2026-11-21 00:01 UTC («mergea #1070» de Nicolás en S192), ficha **v1.54** | hecho | nada |
| 0a-bis | **Estado al 2026-11-20 23:50 UTC:** Nicolás aprobó el arreglo («Sí, arréglalo»); PR #1070 abierto (lector VIIRS marca inválido todo DN sobre el `valid_max` del archivo; arregla la vía y la máscara fija del camino K; tag `pre-s192-m13-512k`). El corte nunca actuó en la historia de los 11: nada que reprocesar. #1067 y #1068 en main (ficha v1.53). Codex frente 9: la guardia de memoria lo cortó a las 23:36 UTC con el commit en 92 % (9,5 M de tokens, 5 hallazgos, informe sin terminar); se reanuda solo bajo 85 % | mergear #1070 con «mergea #1070» | Sí, con CI verde |
| 0b | Marcador del cráter: el informe bow-tie confirma que los 105 píxeles contados el 2026-11-20 son relleno bow-tie, no dato perdido (veredicto MIXTO por la regla preregistrada: 6 de 105 fallan cobertura a cenit alto). Diff propuesto en el informe (A45) | aplicar el diff / esperar | Aplicar junto con 0a en un PR A45 |
| 0c | PR #1069 (reemplazo de 15 MODIS sin fondo: 6 en los 11, 9 en historia_34) | mergear y aplicar tras la tanda 7 / esperar | Sí, después de la tanda 7 y de repetir el ensayo |
| 10 | Pendientes heredados de S192 §b: frente 6 (rojo si un volcán no mide nada), F1M-114, D15, reintento en las sombras, D-10, D5/D13/D11 de los 34 | ver `tasks/BLOQUE_ARRANQUE_S192.md` §b | Las de ese bloque |

Preguntas de Nicolás de S192 sin respuesta explícita: ninguna. «¿cómo vamos?» (relevada por S191) se respondió en texto.

## c. Lo aprendido

- **REGLA DEL LOOP (Nicolás, S192):** la sesión coordinadora nunca queda anidada; al abrir, `detach_session self`. Sólo las paralelas de trabajo menor se anidan. Memoria `feedback_s192_coordinadora_no_anidada.md`.
- **REGLA DEL LOOP:** GitHub puede dejar trabajos fantasma «queued» para siempre tras `gh run rerun` (tanda 6: 10 de 12 copias de dos trozos). Contar rojos por trozo con `filter=all` (alguna copia en success) y confirmar con los artifacts; `per_page=100` en ese endpoint da 502. Memoria `feedback_s192_trabajos_fantasma.md`.
- **REGLA GENERAL (Windows, ya conocida de S184):** los heredoc de bash con Python que llevan rutas `D:\...` o comillas raras fallan o rompen las barras (`\v`, `\t`, `\f` se volvieron caracteres de control en la descripción de #1065). Scripts con rutas Windows: escribirlos con la herramienta Write y correrlos.
- **Proyecto:** antes de mergear un PR de otra sesión, mirar si esa sesión ya empujó su propio commit de ficha (#1067: dos actores prepararon la v1.52; el push del segundo se rechazó sin daño).
- **Proyecto:** una mutación que sobrevive señala la prueba que falta (fondo parcial en MODIS).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** el marcador de #1060 salta en VIIRS sólo en pasadas de borde: las 27 con MIR inválido sobre el cráter tienen cenit de 54,7° a 67,0° (mediana 59,3°) contra mediana 28,0° sin marca (`D:\vrp-trabajo\temporales\s192\plan\numeros_12_11.py`).
- **SOSPECHA:** es el relleno de la supresión bow-tie de VIIRS, no dato perdido. Sin abrir un gránulo.
- **CONFIRMADO:** en MODIS, una escena con fondo parcial sigue publicando la suma del `.m` (incluye la radiancia entera del alertado sin fondo); queda marcada en `alertados_sin_fondo`. Cuántas: SIN DATO hasta que los records nuevos traigan la marca.
- **SOSPECHA:** Lanin feb-2025 y Callaqui mar-2025 son incendios forestales; Nevado de Longaví 2026-02-27 (43 y 86 MW MODIS sin fondo, 5 píxeles) también podría serlo. Sin cotejar.
- **CONFIRMADO:** la tanda 7 avanza lento (5 h para 54 de 133 trabajos); causa no revisada (runners compartidos con CI y NRT).

## e. Ya cerrado, no rehacer

- Fondo nulo: decidido (opción a) e implementado (#1065, v1.51). No volver a discutir (b) o (c); lo que falta es el reemplazo de datos.
- #1061 a #1066 en main; tandas 1 a 6 aplicadas (28 volcanes).
- La «falla» de la tanda 6 era de GitHub, no del reproceso: 165 de 165 trozos con artifact.
- TIR perdida: no es defecto de fidelidad (el `.m` hace lo mismo); no tocar `remuestrear_grilla`.
- Frente 5 de Codex lanzado y cerrado (máximo 77 % de memoria, sin incidentes).
- CLAUDE.md de `loop/activo` igual al de main (2026-11-20).

## f. Prompt para S193

```
Retomas VRP Chile como sesión dueña del loop (S193). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self") (regla de Nicolás: la coordinadora no va anidada).

1. Verifica antes de creer:
   - git fetch; git status -sb; ps -ef | grep -E "cadena_7_s192|mergear_verdes"; hora del servidor (A86).
   - gh pr view 1067 (¿mergeado? log D:\vrp-trabajo\temporales\s192\merge\merge_1067b.log; si no, la orden «mergea #1067»
     ya la dio Nicolás el 2026-11-20: la ficha v1.52 está en la rama, sólo falta mergear con --match-head-commit tras CI verde).
   - Tanda 7: run 44768057665, log D:\vrp-trabajo\temporales\s192\tanda7\cadena.log.
   - Ficha en main (v1.51 o v1.52).
2. Lee tasks/BLOQUE_ARRANQUE_S193.md (rama loop/activo) y la bitácora tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Tanda 7 limpia: bajar, unir y ensayar con BASE=D:/vrp-trabajo/temporales/historia_34/tanda7
      WT=D:/vrp-trabajo/worktrees/s193-tanda7 RAMA=s193-historia34-tanda7 bash D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh 44768057665;
      números con una copia de D:\vrp-trabajo\temporales\s192\tanda6\tanda6_numeros.py; TANDAS.md con la fila aplicada de la 6;
      PR; aplicar sólo con «mergea #N» (aplicar-reemplazo.yml, tag pre-historia-34-tanda7).
   b. Reemplazo de los MODIS sin fondo (decisión 1 de §b): recontar con D:\vrp-trabajo\temporales\s192\plan\fondo_nulo_lista.py
      con la tanda 7 aplicada; proponer el método a Nicolás con recomendación; aplicar sólo con su sí.
   c. Llevar a Nicolás las decisiones de §b con recomendación.
4. Reglas duras: A45 (tag y sí de Nicolás antes de pipeline/process_*.py, store.py, mirova_equivalent.yaml y
   pipeline/mirova_v750_codigo.py), todo PR con «mergea #N», merge commit --match-head-commit, ficha al mergear,
   nada de git stash, git add por archivo, nunca experiments/_s176_codex/, temporales y worktrees en D:, números con
   script, .md reescritos con newline="", scripts con rutas Windows escritos con Write (no heredoc).
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
