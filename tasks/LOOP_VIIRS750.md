# Loop de VIIRS 750 (sesión hija de S162)

Única fuente de verdad entre vueltas de esta sesión. Rama `claude/s162-viirs750-f63ef4`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4`.
Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §3. Coordinadora: sesión
`local_4152952c-6afd-433a-82b3-b07575feee3b` (todo despacho de GitHub Actions se le pide a ella). Notas compartidas:
`C:\Users\nmend\AppData\Roaming\Claude\side-session-notes\local_4152952c-6afd-433a-82b3-b07575feee3b`.

Límites: sólo este worktree y esta rama; no tocar `tasks/LOOP_OBJETIVOS.md` ni los loops de instrumento, VIIRS 375 y
MODIS; nada en `pipeline/` sin pre-registro sellado, verificador limpio, tag y el sí de Nicolás (A45); ningún A/B
nuevo antes de que el instrumento entregue la cobertura contra la referencia (fase 0); sólo `EARTHDATA_TOKEN`; nunca
`git stash`; `git add` por archivo; parada si C: o D: bajan de 3 GB libres (D: ~8,6 GB al empezar: no copiar grillas).

## Relevo (sesión VIIRS 750 2, desde el 2026-10-25 ~22:40 hora de Chile)

Rama `claude/s162-viirs750-2-918174` (sale de `s162-v750a-evaluador` `7d5e723c6`), worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174`. La vía en
`pipeline/` va aparte: rama `s162-via-mirova` desde `origin/main`, worktree `C:\vrp-trabajo\s162-via-mirova`, tag
defensivo `pre-s162-via-mirova` (`deaf8f59b`). Cola de este relevo:

- R1 [hecho y verificado; falta que S163 la confirme bajo D-48] **Adenda 1 de V750-B** (`e7c56af0b`, v2 `7aa2788a0`):
  el analizador sellado deja caer sin contar la pasada «ok» sin una caja del oráculo. Verificador Sonnet: LISTO CON
  CAMBIOS, todos hechos: lector `adenda1/leer_v750b.py` (no deja pasar al analizador si el compañero cierra), cajas
  ilegibles cierran siempre, comando con rutas absolutas. Batería 52/52, nulo 17/17. **El 2026-11-03 se lee con el
  lector** (comando al final de `PREREGISTRO_V750B.md`).
- R2 [hecho y verificado; falta el medidor final] **V750-A, L2/L4/L7/L18 por D-48** (`9f9ae9259`) y segunda vuelta del
  verificador (Fable, `experiments/_s162_v750a/verificador_v2/INFORME.md`: listo con cambios de texto, ninguna lectura
  abre adopción falsa). Corregido: VB-A01 (el tope de 50.000 MW del tablero también explica el placebo; la frase «no se
  puede producir» era falsa), VB-A02 (§6.1 y S-1 sobre todas las observadas, escrito), VB-A03 a A06 (E53 a E60, M57 a
  M62), VB-A07 (con menos de 100 pasadas el 1 % es cero, escrito). Batería 61/61. Medidor de 62 mutaciones corriendo.
- R3 [hecho, falta suite y PR] **Vía «código MIROVA» V750** en `s162-via-mirova`: módulo, grilla por volcán (regla
  GEO con las filas de sur a norte: Y0 = ul_y - 25062,5, probada contra el yaml), flag apagado; equivalencia ROJA a
  VERDE (1.020 + 10); nulo del módulo real 8/8. PR en borrador. **Corrección A45 (aviso de S162)**: había editado
  `process_viirs_mod.py` y `store.py` antes del sí de Nicolás; se devolvieron a `origin/main` y el cableado quedó como
  parche propuesto en `experiments/_s162_v750a/cableado_pendiente/` (aplica limpio, 6 pruebas verdes). Entra sólo
  con el sí de Nicolás, pedido por S163.
- R4 [2026-11-03] objetivos de V750-B desde su tag y pedido de despacho con los sha256 (paso 2 de abajo); la lectura
  va con `adenda1/leer_v750b.py` (adenda 1 CONFIRMADA por S163 bajo D-48 el 2026-10-26, sobre `7aa2788a0`). S163 pide
  para el despacho: objetivos y su sha256, el tag desde el que se despacha, el número de jobs y el comando exacto del
  workflow (`probe-s162-v750b.yml`). **Ensayo hecho el 2026-10-26** sobre main `cff07d173` (los archivos de V750-B son
  idénticos al tag sellado): `python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest
  C:/vrp-trabajo/temporales/v750b_ensayo/ref --hasta 2026-10-25` → 5.781 objetivos, 0 sin gránulo, 279 alertas de MIROVA
  (103 protegidas), 0 alertas sin record nuestro, 41 s. Los archivos del ensayo se borraron (no son los definitivos).
  El 2026-11-03: el mismo comando con `--hasta 2026-11-02` sobre el main de ese día, commitear objetivos_v750b.json,
  sin_granulo_v750b.json y poblacion_completa.json con su sha256 y pedir el despacho a S164.
- R7 [hecho] #907 mergeado por S164 (merge `cff07d173`, tag `pre-s164-merge-907`, Tests verde). Flag apagado. Avisado a
  loop-viirs375 que la vía está en main.
- R5 [HECHO, `d4f1c891c` y `a16aa14b4` en `s162-via-mirova`, PR #907, CI verde] la regla de MATLAB la halló el
  subagente de S163 (Delaunay con desempate simbólico, x = fila); portada: VRP 166/166 contra MATLAB, fondo 84/84,
  Etna exacto; oro de 8 escenas en `tests/data/`; equivalencia contra el módulo independiente de S163; nulo del módulo
  17/17 con seis simetrías rivales; extrapolación fuera de la envolvente marcada NO CUBIERTA (sólo Etna). Texto original:
  **fillmissing2 exacto de MATLAB** (pedido de S163, 2026-10-26): O2 corrió en
  MATLAB R2026b (rama `s163-o2-paquete` `9b755f315`, `experiments/_s163_o2/RESULTADO_O2.md`): detección igual a Octave en
  311 de 311, pero ningún modelo de `fillmissing2` reproduce el VRP de MATLAB (más de 1 % en 32, 26 y 45 de 166).
  Tarea: un `fillmissing2` en Python que dé MATLAB en las 166 escenas con alerta (las de 1 píxel a menos de 1e-6
  relativo), con prueba roja contra los ports actuales y mutaciones; si no se logra exacto, documentar la regla que
  falta y usar las 166 salidas de MATLAB como vara de M en V750-A. Otra corrida de MATLAB: paquete con .mat, .m,
  correr_*.m y md5, y se le pide a S163.

**Coordinadora desde el 2026-10-26 12:35 UTC: S164** (`local_34f868ef-c156-4906-9b6c-e691fc445650`; antes S163
`local_8a135e90-b711-4bb9-9dec-ff02036f206b`, y antes S162). Despachos, avisos y resultados van a ella.

- R6 [HECHO, espera el merge de S164] **Cableado aprobado por Nicolás** (vía S163, «continúa con todo lo que
  recomiendes apruebo los últimos 3 puntos»), flag apagado: PR #907 en `f96b379e7` (rebasado sobre main con #911; tag
  defensivo `pre-rebase-s162-via-mirova` sobre `a16aa14b4`). La vía reconoce el volcán por coordenadas (sin cambiar la
  firma ni run_pipeline.py). Bit a bit del almacén 6.143/6.143; suite 2.582 aprobadas, 0 fallas; verificador Sonnet
  listo con cambios, todos hechos; CI verde. Avisado a S164 el 2026-10-26 ~13:20 UTC. fillmissing2: NaN fuera de la
  envolvente, como MATLAB. Workflow opcional del NRT real (`probe-s162-bitabit-nrt.yml`): S164 lo deja para después.

## Cola (en orden)

**Estado al 2026-10-24 ~19:30 UTC: loop DETENIDO a propósito** (lo que sigue espera fechas o decisiones externas;
reiniciarlo con `/loop Loop de VIIRS 750 de VRP Chile: lee tasks/LOOP_VIIRS750.md, ...` cuando toque).

1. [hecho y verificado] **V750-C**: `experiments/_s162_v750c/INFORME.md` (verificador Fable). Dos piezas callan las
   cumbres tibias: la interpolación lineal (dentro de la zona sensible) y la ROI (fuera, Tupungatito). La magnitud la
   da el fondo del código.
2. [SELLADO bajo D-48] **V750-B**: `experiments/_s162_v750b/PREREGISTRO_V750B.md`, commit `1af6c3cd8`, tag
   `s162-v750b-sellado`. Tres vueltas de verificador (Fable, Sonnet, Fable); batería de 19 escenarios que atrapa 13
   de 13 mutaciones por aserción (`mutar_bateria_salida.txt`).
   **PRÓXIMA ACCIÓN, 2026-11-03** (después de que el NRT tenga las pasadas del 11-02): en un árbol de `origin/main` con
   `experiments/_s162_v750b/` del tag, correr `python experiments/_s162_v750b/objetivos_v750b.py --data <data de
   origin/main extraída> --ref-dest <carpeta> --hasta 2026-11-02`; commitear `objetivos_v750b.json`,
   `sin_granulo_v750b.json` y `poblacion_completa.json`; pedir el despacho a la coordinadora con los sha256 (ella
   despacha desde un tag; la cobertura contra la referencia del instrumento, #904, tiene que estar entregada).
   Lectura: comando del §9 con `--sin-granulo`.
3. [borrador] **V750-A**: `experiments/_s162_v750a/PREREGISTRO_V750A.md`; prueba de equivalencia local hecha y probada
   (`equivalencia_v750a_salida.txt`: roja sin módulo, 6/6 mutaciones). Falta el analizador `evaluar_v750a.py` (reusar
   la regla, las etiquetas y los controles de `analizar_v750b.py`; P2 contra K; M con el comparador y el placebo de
   `evaluar_d25.py` del tag) y su verificador. Bloqueado por el resultado de V750-B (la ROI) y, para el brazo P desde
   el gránulo, por la vía de proceso en `pipeline/` (A45: tag y sí de Nicolás). Incluye el diagnóstico de acoplamiento
   por la sigma de escena (seguimiento cruzado de MODIS, S-1, anotado en §5 del pre-registro).
4. [hecho] **V750-F**: paso a paso de O2 para Nicolás (`experiments/_s162_v750f/PASO_A_PASO_O2.md`).
5. [hecho] Resumen a la coordinadora (mensajes + nota en la carpeta compartida).
6. [después] V750-D (subsumido por V750-A salvo que no se adopte); V750-E (diurno) al final.

## Decisiones para Nicolás

- ~~**DN-1**~~ resuelta por la coordinadora bajo D-48 (2026-10-24). Texto original: **DN-1 (sello de V750-B)**: sellar `experiments/_s162_v750b/PREREGISTRO_V750B.md` v2. Al sellar confirma cuatro
  lecturas que tomé conservadoras tras el verificador: en T decide sólo la tabla; sin ganador nunca se elige un brazo
  que pierde o bloquea; la distancia del record se mide desde el cráter; brazo B5 con la lectura del comentario del
  `.m`. Recomendación: sí a las cuatro y al sello.
- **DN-2 (V750-B §6.5)**: si gana una ROI por volcán (B4 o B2), confirmar que es fidelidad al `.m` (MIROVA declara que
  ajusta la ROI por volcán) y no un gate nuestro de los que excluye A85. Recomendación: tratarla como fidelidad.
- **DN-3 (V750-F, la haces tú)**: correr O2 en MATLAB Online, ~15 min, paso a paso en
  `experiments/_s162_v750f/PASO_A_PASO_O2.md`. No bloquea; fija la vara de M en alertas de un píxel.
- **DN-4 (V750-A, cuando esté su §11)**: sellar `experiments/_s162_v750a/PREREGISTRO_V750A.md`. Recomendación: sí.

## Bitácora

- 2026-10-24, vuelta 0. Leído el programa, la memoria del código OSF, el informe de N (S159). **Hallazgo previo a la
  ablación**: los `grilla_*.npz` de N (`D:\vrp-trabajo\temporales\s159_n\run_*\s159-n-chunk-*\`, 510 pasadas: 391 del
  lote + 119 del censo) traen SÓLO la grilla GEO lineal de 67 × 67 (`m13`, `m15`), no la ventana nativa
  (`probe_n.py:383`). La SOSPECHA fuerte del programa queda REFUTADA: el brazo «O sin remuestreo» no se puede correr
  con esas grillas. Sustitutos locales: (a) `F_L_hot_pc` de los resultados de N es la radiancia nativa M13 del píxel
  de K, comparable con la celda de la grilla; (b) 10 recortes nativos de R2 en
  `experiments/_s158_audit_r2/granulos/run_39641637298/` (rama s159-pruebas), todos alertas, ninguna cumbre de 0 MW.
- 2026-10-24 ~15:45 UTC, vuelta 1. **V750-C hecho** (`8cc1cba83`): controles 510/510; el remuestreo lineal calla
  las cumbres tibias (censo 60: el `.m` 1, piezas de K sueltas ≤ 5, todas juntas 8, vecino más cercano 23, grilla R2 13;
  el remuestreo conserva 54 % del exceso nativo); el fondo del código da la magnitud (anillo 0,458 contra 0,999).
  SOSPECHA FUERTE por usar sustitutos; el brazo nativo va en el run de V750-B (N0/N1). Verificador Fable lanzado.
  Borrador del pre-registro V750-B escrito. Coordinadora avisada del hallazgo de los npz y de que no abro sub-sesiones.
- 2026-10-24 vuelta 1 (sigue). Borrador del pre-registro V750-A escrito: P = remuestreo GEO lineal + `.m` literal + ROI
  de V750-B, sin modo de un píxel ni D9; validación por equivalencia + censo + sombra desde el 11-03; el laboratorio
  sigue con K si P se adopta (A117).
- 2026-10-24 ~16:10 UTC, vuelta 2. Verificador de V750-C entregó: V2, V3, V5, V6, V7, V9 CONFIRMADO; V1, V4, V8 en
  parte. Lo más grave (VV-04): son dos piezas; en las 22 cumbres fuera del 7 × 7 (Tupungatito 17) calla la ROI, no el
  remuestreo. VV-01: la caja por defecto es de una sola matriz de ejemplo (BOX == 1 de 21 × 19). Marcas propagadas al
  informe de V750-C y a los dos pre-registros (A113); predicción de N0 revisada antes de datos; brazo B0e agregado.
  Analizador de V750-B escrito.
- 2026-10-24 ~16:20 UTC, vuelta 3. Prueba local de V750-B en verde. B0e (matriz de ejemplo de 21 × 19) retirado: la
  zona 0 y la 1 comparten umbrales en el `.m` (l. 389-395), así que no puede cambiar ninguna máscara (0 de 510). El
  ensayo encontró que importar `evaluar_d25.py` arrastra todo el evaluador de D25: el analizador ahora extrae la prueba
  de signos con ast, probada en 6 casos de resultado conocido. Workflow del probe escrito (artefactos en C:, pedido de
  la coordinadora). Verificador del pre-registro lanzado.
- 2026-10-24 ~17:30 UTC, vuelta 4. Verificador del pre-registro V750-B entregó (listo para sello con cambios, 16
  hallazgos). Corregidos todos: regla §6 (VB-01, VB-08), canal que decide (VB-03), SIN DATO con nombre y salida 2
  (VB-04, VB-05), controles en la compuerta (VB-06), ancla en el cráter (VB-07), brazo B5 (VB-09), cajas nativas en km
  (VB-10), 12-oct fuera (VB-11), K distinto de producción con tope (VB-12), citas (VB-13), artefacto vacío (VB-14),
  placebo (VB-15), cobertura en el cráter (VB-16), sha256 del evaluador fijado. Batería v2 8/8; ensayo con el censo
  503/503. Enviado a la coordinadora. Prueba de equivalencia de V750-A corriendo con mutaciones.
- 2026-10-24 ~17:50 UTC, vuelta 5. Coordinadora resolvió DN-1 bajo D-48 y pidió segunda vuelta (VB-01 cambió la regla);
  anotado y lanzada con Sonnet. Prueba de equivalencia de V750-A: roja sin módulo (salida 2), identidad 1.020 casos y
  10 recortes en verde, 6 de 6 mutaciones atrapadas por aserción, control caído.
- 2026-10-24 ~18:40 UTC, vuelta 6. Segunda vuelta del verificador (Sonnet): conforme con cambios. Hechos: desempate
  sin brazos peores con la tabla (VB2-01), SIN SUSTRATO con neto ≤ 0 (VB2-02), banderas marcadas y camino para leer
  con faltantes (VB2-03/04), controles con filo (VB2-06), batería que comprueba sola 11 escenarios (VB2-05; encontró
  un defecto propio de la v3, corregido), y VB2-07 a VB2-15. Ensayo real: compuerta abierta, censo 503/503 en posición.
- 2026-10-24 17:36 UTC (servidor), vuelta 7. Coordinadora: VB2-02 confirmada (D-48), anotada; tercera vuelta corta con
  Fable sobre el delta lanzada (escribe en `experiments/_s162_v750b/verificador_v3/`).
- 2026-10-24 ~19:30 UTC, vuelta 8. Coordinadora aprobó VB3-01 bajo D-48 y fijó la condición de sello. Aplicado
  VB3-01 (escenario S3) y VB3-02 a VB3-07; medidor `mutar_bateria.py`: 13 de 13 mutaciones atrapadas por aserción,
  identidad PASA, control de caída CAÍDA. Ensayo final con la compuerta abierta. **V750-B SELLADO** (`1af6c3cd8`, tag
  `s162-v750b-sellado`). Loop detenido: lo próximo es el 2026-11-03.
- 2026-10-24, después de detener el loop. Seguimiento cruzado de MODIS (S-1 del verificador del bow tie D28): el umbral
  del `.m` usa la sigma de toda la grilla, así que un A/B de remuestreo queda acoplado al borde de la escena. Anotado
  en V750-A §5 como diagnóstico obligatorio (cambio de sd entre brazos, margen del cráter, pasadas decididas por la
  escena). No cambia V750-B sellado.
