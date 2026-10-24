# Loop de MODIS (sesión hija de S162)

Única fuente de verdad de este loop entre vueltas. Rama `claude/s162-modis-774bb0`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0`.
Coordinadora: sesión «Retomar» (`local_4152952c-6afd-433a-82b3-b07575feee3b`), la única que despacha GitHub Actions
y la única que escribe `tasks/LOOP_OBJETIVOS.md`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§5 (MOD-A a MOD-E). Notas compartidas: `C:\Users\nmend\AppData\Roaming\Claude\side-session-notes\local_4152952c-6afd-433a-82b3-b07575feee3b`.

## Reglas de este loop

- Sólo mi worktree y mi rama. No escribo `tasks/LOOP_OBJETIVOS.md` ni archivos de instrumento, VIIRS 750 o VIIRS 375.
- Nada en `pipeline/` sin tag defensivo y el sí de Nicolás para ese cambio (A45).
- Nunca despacho: pido a la coordinadora, con el pre-registro y los comandos exactos. Sólo `EARTHDATA_TOKEN` (A71).
- Nada de `git stash`; `git add` por archivo; verificador con contexto limpio de otro modelo antes de aceptar un
  resultado; CI con conclusión antes de dar un PR por listo.
- Parada si C: o D: bajan de 3 GB libres.
- Permiso de Nicolás (2026-10-24, reenviado por la coordinadora): puedo abrir sub-sesiones o sub-loops, cada una en su
  worktree y rama, con cola propia enlazada desde aquí, sin despachar por su cuenta; aviso a la coordinadora con nombre e
  id `local_…`. Sub-sesiones abiertas: ninguna.

## Insumos (dónde están)

Los informes de S159 no están en `loop/activo`: viven en `origin/s159-pruebas` (y `origin/s159-portes`). Copia de
lectura en el scratchpad de la sesión. `experiments/_s159/mxd03_prereg/` se trajo a esta rama desde `origin/s159-pruebas`
(`812624cc6`) para anotar el sello. Grillas del port: `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\` (sólo
grillas 51 × 51 ya remuestreadas: `mir`, `tir`, `mir_b21`, `mir_geo5`, `tir_geo5`; ningún recorte nativo).

## Cola (en el orden del programa)

### MOD-B, MxD03 sobre K (D-19, tarea 1.30)
- [ ] B1. Anotar el sello D-48 en el pre-registro v2 (texto y fecha), con las respuestas del §11 según la
  recomendación, y una adenda declarada con lo que cambia al implementar (D34 del catálogo ya está tomada por el código
  de MIROVA V750: la divergencia nueva sería D35; tag sobre un commit de disparo, no sobre `main`; censo re-medido en el
  sha que se congele).
- [ ] B2. Re-medir el censo (records, gránulos, ≤ 35°, etiquetas) sobre el `origin/main` que se congele y la referencia
  remota congelada (`MANIFIESTO.json`, sha256 LF).
- [ ] B3. Arnés `probe_mxd03_ab.py` (brazos K, K2, X, R0 a R19 en ≤ 35°, X_fondo y X_det en las que cambian), partes por
  gránulo, con prueba sintética sin HDF (pyhdf no corre en Windows).
- [ ] B4. Workflow de disparo (`"on":` entre comillas, `EARTHDATA_TOKEN` que falla vacío, `ubuntu-24.04`, 24 partes).
- [ ] B5. Evaluador `evaluar_mxd03.py` + `probar_evaluar_mxd03.py` (las 12 pruebas del §8, rojas antes, verdes
  después) y las 5 mutaciones con control de caída.
- [ ] B6. Verificador con contexto limpio, de otro modelo, sobre arnés y evaluador.
- [ ] B7. Pedido de despacho a la coordinadora (tag, tres tandas de 8 partes, ~47 h de runner).

### MOD-C, negativos neg_resto del port MODIS (D-36)
- [ ] C1. Pre-registro del lote (300 a 400 de las 5.093 noches neg_resto), selección con semilla, objetivos, regla de
  decisión (Wilson), para el despacho combinado de la fase 1. Guardar el recorte nativo de cada pasada (lo pide MOD-E).
- [ ] C2. Verificador limpio del pre-registro y entrega a la coordinadora.

### MOD-E, bow tie (D28), ablación local
- [ ] E1. Leer cómo grilla el port MODIS y qué hay en disco; decidir si la ablación se puede hacer sin red.
- [ ] E2. Ablación (o veredicto de sustrato) con verificador limpio.

### MOD-D, paquete MODIS contra K
- [ ] D1. Pre-registro: brazos K, PM (port con D33 corregido), PM sin MxD03; el déficit de Chillán (0,485) se juzga aquí.
- [ ] D2. Verificador limpio del pre-registro.

### MOD-A (la hace la sesión del instrumento)
- [ ] A1. Usar la cita de MOD03 de Coppola 2026 p. 4 cuando la entregue (afecta §2 del pre-registro de MxD03).

### Cierre de esta etapa
- [ ] Z1. Resumen para la coordinadora (en las notas compartidas y por mensaje).

## Decisiones para Nicolás (con recomendación)

(ninguna todavía)

## Bitácora (la más nueva arriba)

### 2026-10-24 (vuelta 0): arranque
- Leídos: programa (§1, §2, §5, §7, §9, §11), pre-registro MxD03 v2, informes M, PORTES y su verificador, Chillán MODIS,
  D28 y D33 del catálogo (D33 está en `main`, no en `loop/activo`).
- Hallazgos de arranque: (1) el evaluador `evaluar_mxd03.py` del §8 del pre-registro **no existe** en ninguna rama (sólo
  el de 1.17 en `_s151_mxd03_etiquetas`), ni el arnés ni el workflow: el candado hay que construirlo (B3 a B6).
  (2) La «D34» que el §11 punto 9 propone ya está usada en el catálogo (S158). (3) Las grillas del port en D: no traen
  el recorte nativo, así que la ablación del bow tie no se puede hacer sólo con ellas (E1 lo confirma o lo refuta).
- Sello: decisión D-48 de Nicolás (2026-10-24), registrada por la coordinadora en `tasks/LOOP_OBJETIVOS.md` de
  `loop/activo` (`c8423ce9a`): «sobre las decisiones mías haz lo que tú recomiendes»; la recomendación 9 del programa es
  «sellar el pre-registro v2 y correrlo; adoptarla dentro del paquete MODIS salvo que se atrase más de un mes».
- Disco al arranque: C: 37 GB, D: 8,6 GB.
