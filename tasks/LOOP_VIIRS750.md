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

1. [en curso] **V750-C, ablación del oráculo en local** (`experiments/_s162_v750c/`). Sin red ni sello.
2. [pendiente] Verificador limpio de V750-C (otro modelo, sólo título, ruta y script).
3. [pendiente] Pre-registro V750-B (ROI por volcán: PCC y Tupungatito) para el despacho combinado de fase 1.
4. [pendiente] Pre-registro V750-A (paquete del código contra K: P, P-def, P-sinfiltro, Kgeo) y prueba de
   equivalencia contra el oráculo.
5. [pendiente] Paso a paso de V750-F (O2 en MATLAB Online) para Nicolás.
6. [pendiente] Resumen para la coordinadora (nota en la carpeta compartida + SendMessage corto).
7. [después] V750-D (subsumido por V750-A salvo que no se adopte); V750-E (diurno) al final.

## Decisiones para Nicolás

(ninguna todavía)

## Bitácora

- 2026-10-24, vuelta 0. Leído el programa, la memoria del código OSF, el informe de N (S159). **Hallazgo previo a la
  ablación**: los `grilla_*.npz` de N (`D:\vrp-trabajo\temporales\s159_n\run_*\s159-n-chunk-*\`, 510 pasadas: 391 del
  lote + 119 del censo) traen SÓLO la grilla GEO lineal de 67 × 67 (`m13`, `m15`), no la ventana nativa
  (`probe_n.py:383`). La SOSPECHA fuerte del programa queda REFUTADA: el brazo «O sin remuestreo» no se puede correr
  con esas grillas. Sustitutos locales: (a) `F_L_hot_pc` de los resultados de N es la radiancia nativa M13 del píxel
  de K, comparable con la celda de la grilla; (b) 10 recortes nativos de R2 en
  `experiments/_s158_audit_r2/granulos/run_39641637298/` (rama s159-pruebas), todos alertas, ninguna cumbre de 0 MW.
