# Bloque de arranque S158 (cierre de S157: «retomar» + loop, 2026-10-20 a 2026-10-21)

Escrito el 2026-10-21 a las ~02:15 UTC (hora del servidor) sobre `loop/activo`; `main` en `66961f65` (= tag
`s157-d25-k-codigo`) más los commits automáticos. **Se fijó con trabajo en curso**, y tres procesos LOCALES de esta
sesión mueren si se cierra la app:

1. **A/B de D25, V1** en GitHub (run 39530508296, tres brazos, 2026-08-29..10-18). Corre solo.
2. **Despacho en serie de V2a y V2b de D25** (proceso local). **Si la sesión se cerró, nadie los despachó**: hay que
   hacerlo a mano según `experiments/_s157_prereg_d25/PREREGISTRO.md` §6 (desde el tag, uno a la vez, sólo con 0
   A/B vivos).
3. **`armar_relleno.py` contra CMR** (proceso local en `D:\vrp-trabajo\temporales\s157_relleno_wt`, worktree
   detached de `main`). Si murió, se vuelve a correr.
4. **Control del NRT de las 09:35 UTC** (proceso local): contar commits `NRT update` de 02:00 a 09:30 del 21-oct contra
   los **24** del 20-oct. Si murió, se cuenta a mano.

Bitácora completa en `tasks/LOOP_OBJETIVOS.md` §6 (entradas del 2026-10-20 y 21); el bloque anterior,
`tasks/BLOQUE_ARRANQUE_S157.md`, queda como histórico. Ante discrepancia manda la bitácora y, por encima, el remoto.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | Histórico con K de Chillán reprocesado: 6 trozos caídos (5 por tope de 170 min, 1 runner) relanzados partidos, más dos pasadas de relleno porque el cortacircuito de CMR dejó días vacíos en trozos VERDES | runs 39363774747, 39363796988, 39370713699, 39431309981, 39467050396; tag `pre-s157-chillan-trozos` |
| borrador | **PR #878**: JSON de Chillán rearmado (6.396 records, control contra el tag 3.637 de 3.637, faltan 6 `nrt` de Suomi NPP del 5 y 6-ago sin estándar) | `experiments/_s157_chillan_rearmado/rearmar_y_contar.py` |
| mergeado | #866 ensayo del reemplazo de los otros 10: los 10 PASAN el tope del 2 % (peor 0,37 %); aplicar los 11 juntos (G4) | `8c94c847`, `experiments/_s154_reproc_k/ensayo_s157/` |
| mergeado | #867 watchdog por duración de job (F3-10); #824 cerrado | `e81438fd` |
| mergeado | #868 K propagado a los textos (A113) | `f101d730` |
| mergeado | #872 λ de B22 en MODIS con K, **flag apagado** (`enable_modis_mir_lambda_por_banda: false`, leído False) | `5fd2ac2e`; D33 |
| mergeado | #873 el merge de `reproc-chunked` conserva lo que main tiene fuera de las ventanas | `c408a909` |
| mergeado | #874 auto-audit por tramo de cenit y régimen (claves nuevas, veredictos idénticos) | `b249b1b9` |
| mergeado | #875 `docs/SINTOMAS.md` (índice por síntoma) | `3868c5db` |
| mergeado | #877 búsqueda en CMR por ventana, brazos de A/B en el mismo job, `--estricto-cobertura` en reprocesos (no en NRT) | `54a085ed`; tag `pre-s157-busqueda-ventana`; NRT 39525751661 verde con 484 `SEARCH_VENTANA` |
| mergeado | #871 pre-registro de D25 sobre K + candado (`evaluar_d25.py`, 27 pruebas, 22 de 23 mutaciones) | `49c70c99`; **D-26 y D-27 sellados** |
| corriendo | **A/B de D25** V1 (V2a y V2b, ver arriba) | tag `s157-d25-k-codigo`; prueba corta 39510227734 pasó |
| cerrado | #865 (PCC V750): dos píxeles contiguos se bajan el contraste; aislado (1 de 155 protegidas); `min` costaría +314 negativos limpios. #870 cerrado | PR #881 (borrador, verificado) |
| borrador | #869 descomposición de la magnitud de Chillán (recomendó D25 primero); #879 azimut (verificado); #880 saturación (midió 2 de 40, no decide) | ramas `s157-*` |
| abierto | #876 (watchdog reabre corridas ya juzgadas), #864 (estado de K), #813 (D-10) | issues |
| pendiente | Relleno de las 31 `standard` de los otros 10 (10 despachos de un día, en serie) | `experiments/_s157_relleno/PLAN_RELLENO.md` |
| pendiente | Reemplazo de la serie con los 11 juntos, mover `DATOS_K_DESDE_UTC`, R8 | plan 1.24 |

Discos al cierre: C: 18 GB libres (7,8 GB son el temporal de Claude del proyecto `Diversion-Poleras`, no tocado),
D: 19 GB. Worktrees: sólo la raíz y `D:\vrp-trabajo\temporales\s157_relleno_wt`. Artefactos de Chillán en
`D:\vrp-trabajo\temporales\s157_chillan\` (los del run original vencen el 2026-10-26; ya están en #878).

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Las ~64 pasadas `nrt` sin producto estándar (58 de Suomi NPP del 4 al 6-ago en los otros 10, 6 en Chillán) | quedan en C0 con su marca · se procesan desde el NRT con K | **procesarlas desde el NRT con K**: el pipeline acepta NRT (delta de BT bajo 0,1 K, CLAUDE.md) y así la serie queda entera en K |
| 2 | Mergear #878 (Chillán rearmado, sólo `data/_s154_reproc_k_historico/` y `experiments/`) | sí · revisar antes | **sí**, antes del reemplazo |
| 3 | Encender la λ de B22 en MODIS (#872; +5,75 % mediana) | ahora con reproceso · junto con el próximo reproceso | **juntarlo con el reproceso que traiga el resultado de D25**, para no reprocesar dos veces |
| 4 | Mergear los PRs de investigación (#869, #879, #880, #881; sólo `experiments/`) | sí · dejarlos en borrador | **sí** para #869, #879 y #881 (verificados); #880 cuando mida el grupo del 18-oct |
| 5 | Watchdog con lista de corridas ya juzgadas (#876) | implementar · tolerar | **implementar** (un JSON de corridas juzgadas, como `sombra_pasadas_juzgadas.json`) |
| 6 | #813 (D-10, abrir el día) | decidir · postergar | postergar hasta tener el A/B de D25 |
| 7 | Rotar el PAT de GitHub (`~/.claude/settings.json`) y avisar a OVDAS del cambio de detector | | de Nicolás (credencial y mensaje a terceros) |

## c. Lo aprendido

1. **Un cortacircuito que salta sin fallar convierte una caída del proveedor en una ausencia silenciosa** (regla
   general del workspace; refuerzo de A108). Con CMR inestable, el `breaker ON esta corrida` saltó días enteros:
   326 pasadas perdidas en trozos VERDES de Chillán, y 6 de 9 NRT verdes sin un dato. Arreglo: `--estricto-cobertura`
   en reprocesos (#877). Destino propuesto: regla A120 del CLAUDE.md del proyecto (va por PR a `main`).
2. **Una aprobación reenviada entre sesiones no vale** (regla general). El control de permisos no dejó que la sesión
   lateral registrara el sello de Nicolás: se registra en la sesión donde se dio, con la cita textual. Memoria.
3. **Un nulo que mueve al azar algo que ya calza da «empeora» siempre** (regla de método, familia A110). La calibración
   de M sorteaba el signo de log10(D/K); con K ya cerca de MIROVA, cualquier movimiento aleja. El nulo correcto sortea
   el signo de la diferencia (D-27).
4. **El merge de trozos no conservaba el archivo** (proyecto, arreglado #873): relanzar unos trozos borraba el resto.
5. **Lado del barrido y hora son la misma variable en VIIRS** (proyecto, #879): la primera pasada de la noche viene
   del este; cualquier efecto de lado se confunde con la hora salvo en MODIS.
6. **Pedir los verificadores en primer plano** (regla general): tres subagentes se cortaron con su verificador corriendo
   en segundo plano y entregaron sin él.
7. **Una batería de mutaciones llenó D: a 0 GB** (regla general): cada mutación debe borrar su temporal.
8. **Git Bash convierte `origin/main:.github/...` en una ruta de Windows** (regla general): usar `MSYS_NO_PATHCONV=1`
   antes de `git show <rev>:<ruta>`.

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | La magnitud con el sensor oblicuo sigue corta; D25 aporta x1,08 a x2,16 y la selección no cierra (probe L1B, #871) | `experiments/_s157_prereg_d25/probe_l1b/` |
| CONFIRMADO | Nuestra razón contra MIROVA es más baja desde el este: 0,79 noche a noche sin Isluga, p < 0,001 (C0, VIIRS 375) | #879 |
| CONFIRMADO | El script de S130 agrega un par por record aunque su docstring diga «máximo de cada lado» | `experiments/_s130_cenital/medir_gradiente_cenital.py` l. 20, 92-94, 102-103 |
| CONFIRMADO | El pipeline pone NaN en píxeles saturados (VIIRS bit 4, tope de LUT, M15 ≥ 342,5 K; MODIS SI > 32767) | #880 (lectura de código verificada) |
| CONFIRMADO | El watchdog reabre corridas ya juzgadas | #876 |
| SOSPECHA | La saturación explica parte del déficit de VIIRS 375 en Chillán; en VIIRS 750 sería improbable (M13 de doble ganancia) | #880 no midió el 18-oct |
| SOSPECHA | El resto del déficit oblicuo es D17 (pista: a las 06:48 del 18-oct VIIRS 375 ~310 K y M13 273 K) | verificador de #880 |
| SOSPECHA | 44 de 156 píxeles de VIIRS 750 con M15 en sentinela y M13 sano pierden su NTI | #880 |
| SOSPECHA | El efecto de lado de MIROVA es procesamiento suyo (D17, paralaje) y no hora | #879 |
| SIN VERIFICAR | Que el NRT con #877 publique igual que antes de noche (control de las 09:35 UTC) | ver arriba |
| SIN VERIFICAR | El 401 de LAADS para NOAA-21 en el probe de saturación afecta o no al NRT | el NRT de las 01:10 no lo mostró |

## e. Lo que ya está cerrado y no hay que rehacer

- #865: no reabrir; la única palanca (`min` en VIIRS 750) cuesta +314 negativos limpios.
- D25 sellado (D-26: V375 oblicuo sólo bloquea, 7x7, MODIS fuera) y calibración sellada (D-27: nulo simétrico por
  bloque noche-volcán, opción A de dos volcanes). No rediseñar el A/B; leerlo con `evaluar_d25.py --calibracion simetrica`.
- #877: identidad comprobada (0 diferencias en 327 producto-días y 807 gránulos; records iguales salvo redondeo
  9e-12). No volver a medir la búsqueda por día.
- El ensayo del reemplazo de los 10 (#866) y el control del rearmado de Chillán (#878): hechos y verificados.
- La «MIROVA plana con el cenit» de S130 se lee ahora junto con el efecto de lado (#879); no citarla sola.

## f. Prompt para la próxima sesión

```
/retomar

Luego, en el repo VRP Chile (rama loop/activo), antes de creerle a nada: git fetch --prune; hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date); gh run list -w reproc-s146-ab-sin-test1.yml -L 4 (¿terminó V1 de D25, run 39530508296?, ¿se despacharon V2a y V2b?); gh run list -w nrt.yml -L 6 y cuenta commits "NRT update" del 2026-10-21 02:00-09:30 contra los 24 del día anterior (git log origin/main --since ... | grep -c "NRT update"); gh issue list y gh pr list; df -h /c /d; git worktree list.
Lee en orden: tasks/BLOQUE_ARRANQUE_S158.md, la bitácora de tasks/LOOP_OBJETIVOS.md desde 2026-10-20, docs/SINTOMAS.md, experiments/_s157_prereg_d25/PREREGISTRO.md §5 a §8 y ADENDA_CALIBRACION.md.
Trabajo, en orden (salvo que Nicolás decida otro en la tabla b):
1. Si V2a o V2b de D25 no se despacharon (el proceso local murió con la sesión), despacharlos desde el tag s157-d25-k-codigo según PREREGISTRO §6, uno a la vez y sólo con 0 A/B vivos. Al terminar los tres: contar cobertura (A108), evaluar con evaluar_d25.py --calibracion simetrica, verificador limpio, informe para Nicolás.
2. Relleno de las 31 pasadas standard de los otros 10: rehacer armar_relleno.py con CMR arriba (worktree en D:), despachar los 10 días en serie con reproc-chunked (modo estricto), contar pasadas.
3. Con #878 mergeado y el relleno hecho: ensayo de Chillán, verificador limpio, reemplazo de los 11 juntos entre corridas del NRT (tag defensivo), mover DATOS_K_DESDE_UTC en el mismo PR, verificar_ventana.py y R8.
4. Watchdog con lista de corridas juzgadas (#876).
5. Saturación: medir el grupo del 18-oct cuando CMR lo indexe (#880).
Reglas duras: nada se adopta en producción sin el sí explícito de Nicolás (A45, tag defensivo); merges de PRs: el clasificador de permisos exige su sí en la conversación; un sello o aprobación se registra en la sesión donde se dio; ningún número sin script commiteado; la hora se pide al servidor (A86); verificador limpio en PRIMER plano antes de aceptar un resultado; worktrees y temporales en D:\vrp-trabajo\ con TMP/TEMP en D:; MSYS_NO_PATHCONV=1 para git show <rev>:<ruta>; texto con barras invertidas con la herramienta Edit; cerrar a ~30 intercambios; sin guiones largos ni medios; rutas absolutas al informar.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué quedó corriendo y corre /cierre.
```
