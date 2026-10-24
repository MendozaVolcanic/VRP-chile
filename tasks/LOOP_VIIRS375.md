# Loop de VIIRS 375 (S162, sesión hija de la coordinadora «Retomar», local_4152952c)

Única fuente de verdad entre vueltas. Worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864`, rama
`claude/s162-viirs375-c1b864`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §4.

Reglas de esta sesión (las de la coordinadora, 2026-10-24): sólo este worktree y esta rama; no escribo
`tasks/LOOP_OBJETIVOS.md` ni archivos de las sesiones de instrumento, VIIRS 750 o MODIS; nada en `pipeline/` sin
pre-registro sellado, verificador limpio, tag defensivo y el sí de Nicolás (A45); **todo despacho de GitHub Actions se
pide a la coordinadora** (SendMessage a local_4152952c) con el pre-registro y la lista de brazos; ningún A/B nuevo antes
de que el instrumento entregue la cobertura contra la referencia (fase 0, PD0); sólo `EARTHDATA_TOKEN` (A71); nunca
`git stash`; `git add` por archivo; verificador con contexto limpio de otro modelo antes de aceptar cualquier resultado;
parada si C: o D: bajan de 3 GB. Puedo abrir sesiones propias (permiso de Nicolás vía coordinadora, 2026-10-24), cada
una en su worktree y con su archivo enlazado aquí; hoy no hay ninguna.

## Cola (en el orden del programa)

| id | qué | estado |
|---|---|---|
| V375-B | pre-registro del lote de negativos limpios neg_resto para el port (D-36, aprobado) | en curso |
| V375-C | pre-registro de los brazos de ROI (caja de 13, 14 y 21 celdas, cráter, círculo, sensible) | en curso, mismo lote que B |
| V375-E | pre-registro del paquete V375 contra K (curva de razón por cenit contra la de MIROVA) | pendiente |
| V375-D | números propios de 375 | sólo si B o C lo exigen (PD1) |
| V375-F | Chillán sobre 3 MW (port 0,939, n 6) | después de V375-E |
| V375-A | etiqueta de protegida de cráter | la hace la sesión del instrumento; la uso cuando la entregue |

## Decisiones para Nicolás (con recomendación)

(ninguna abierta todavía)

## Bitácora

### 2026-10-24 (vuelta 0)
- Leí CLAUDE.md, la memoria del código de MIROVA, el programa (§1, §2, §4, §7, §9, §11), `experiments/_s159/portes/`
  (INFORME, PREREGISTRO y verificador, en `origin/s159-portes`: no están en `loop/activo`), `experiments/_s159/p2/INFORME.md`
  (commit 3f133d69d) y `experiments/_s162_vuelta1/` (Chillán y D25).
- Diseño: V375-B y V375-C comparten UN lote de sólo lectura. El runner baja el gránulo, arma la grilla de 134 x 134 de
  MIROVA, corre todos los brazos y guarda la grilla; el evaluador recalcula los brazos sin red sobre la grilla guardada
  (control) y suma las 150 pasadas del lote de S159, cuyas grillas siguen en `D:\vrp-trabajo\temporales\s159_portes\`.
