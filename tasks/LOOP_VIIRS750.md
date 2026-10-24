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

## Cola (en orden)

1. [hecho y verificado] **V750-C**: `experiments/_s162_v750c/INFORME.md`, con la marca del verificador.
2. [hecho] Verificador limpio de V750-C (Fable 5.1): `experiments/_s162_v750c/verificador/VERIFICADOR_V750C.md`.
   Confirma los números; corrige la atribución: dos piezas (interpolación dentro de la caja sensible; ROI fuera).
3. [v3, en tercera vuelta corta (Fable) sobre el delta 607062ba7..439968ec1] Pre-registro V750-B v3 (`81a5cfcd2`). Segunda vuelta
   (Sonnet): «conforme con cambios», VB2-01 a VB2-15, todos hechos o declarados. Batería sellada
   `bateria_regla_v750b.py` 11/11. La coordinadora confirmó VB2-02 bajo D-48 y pidió tercera vuelta corta: si da conforme sin
   cambios en la regla, queda sellada; si toca la regla, avisarle ANTES de corregir. El **2026-11-03**:
   `objetivos_v750b.py --hasta 2026-11-02` (escribe también `sin_granulo_v750b.json`), commitear, pedir despacho con sha256.
4. [borrador] Pre-registro V750-A: `experiments/_s162_v750a/PREREGISTRO_V750A.md` (equivalencia, censo, sombra; brazos
   K, P, P-def, P-sinfiltro, Kgeo, K×1,2, O). Prueba de equivalencia hecha y probada (roja sin módulo, 6/6 mutaciones).
   Falta: analizador `evaluar_v750a.py` (conviene después del resultado de V750-B, que fija la ROI) y su verificador.
5. [hecho] Paso a paso de V750-F para Nicolás: `experiments/_s162_v750f/PASO_A_PASO_O2.md` (paquete comprobado, md5 OK).
6. [pendiente] Resumen para la coordinadora (nota en la carpeta compartida + SendMessage corto).
7. [después] V750-D (subsumido por V750-A salvo que no se adopte); V750-E (diurno) al final.

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
