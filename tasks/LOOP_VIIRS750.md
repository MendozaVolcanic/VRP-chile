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

1. [hecho, sin verificar] **V750-C, ablación del oráculo en local**: `experiments/_s162_v750c/INFORME.md` (`8cc1cba83`).
2. [en curso] Verificador limpio de V750-C (Fable, esfuerzo alto, en segundo plano): escribe
   `experiments/_s162_v750c/verificador/VERIFICADOR_V750C.md`. Al llegar: leer, contrastar, commitear, marcar A113 si refuta.
3. [borrador] Pre-registro V750-B: `experiments/_s162_v750b/PREREGISTRO_V750B.md`. Falta su §11 (probe, objetivos,
   analizador, prueba sin red) y su verificador antes del sello.
4. [borrador] Pre-registro V750-A: `experiments/_s162_v750a/PREREGISTRO_V750A.md` (equivalencia, censo, sombra; brazos
   K, P, P-def, P-sinfiltro, Kgeo, K×1,2, O). Falta su §11 (analizador, test de equivalencia rojo) y su verificador.
5. [hecho] Paso a paso de V750-F para Nicolás: `experiments/_s162_v750f/PASO_A_PASO_O2.md` (paquete comprobado, md5 OK).
6. [pendiente] Resumen para la coordinadora (nota en la carpeta compartida + SendMessage corto).
7. [después] V750-D (subsumido por V750-A salvo que no se adopte); V750-E (diurno) al final.

## Decisiones para Nicolás

- **DN-1 (para el sello de V750-B)**: sellar `experiments/_s162_v750b/PREREGISTRO_V750B.md` cuando su §11 esté hecho y
  verificado. Recomendación: sí.
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
