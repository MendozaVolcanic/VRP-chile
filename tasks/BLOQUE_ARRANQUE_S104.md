# BLOQUE ARRANQUE S104

**Sesión previa S103 (2026-06-07/08).** MUY larga y muy productiva. Cerró el frente
VIIRS (nadir-fijo **adoptado + promovido + validado**, §1 completo) + auditoría profunda
pre-flip + re-auditoría de sobre-detección (pedido Nicolás) + limpiezas. **8 PRs (#366-373)
+ archive#1.** Registro completo: `project_s103_estado` (memoria). Docs clave:
`docs/S103_VIIRS_NADIR_PROMOTE_RESULTS.md`, `docs/AUDIT_S103_PRE_VIIRS.md`,
`docs/AUDIT_S103_OVERDETECTION_PCC_VILLARRICA.md`, `docs/S103_S2_VIIRS750_PATHD_PREP.md`,
`docs/MIROVA_DIVERGENCES.md` (S103).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat ../../[ruta]/memory/project_s103_estado.md
```
Worktree canónico: raíz `VRP Chile/` en `main` (los hermanos se limpiaron en S103).

## ✅ Cerrado en S103 (en producción)
- **Nadir-fijo VIIRS ADOPTADO+PROMOVIDO** (#368 flip + #373 promoción, A45 completo). R3:
  VIIRS375 global 2.27×→**0.78×**, VIIRS750 1.59×→**0.80×**, 0 FN nuevos VIIRS375. Curados
  Villarrica 18.3→1.0×, Tupun 11.2→0.71×, PCC 2.4→0.95×. MODIS byte-idéntico. R8 live OK.
  Tag `pre-s103-nadir-fixed-viirs`. ctxpeak + pisos VIIRS intactos.
- **Costo aceptado**: Isluga VIIRS750 +2 FN (señales tiny glaciar = §2). Documentado.
- **Backlog hecho**: parseUtcMs 3 vistas (#366), `"on":` quoted (#366), polling TIF
  reactivado (archive#1), test integración nadir→VRP (#367), worktrees -6GB, CI 25→12 (#371).
- **NRT verde** (circuit-breaker S102 aguanta, 4+ runs success).

## §1 — PRIORIDAD recomendada: DISPLAY PCC/Villarrica (cierra la observación de Nicolás)
La re-auditoría S103 (A68) confirmó que la "sobre-detección" que Nicolás ve es **mayormente
DISPLAY + recall real**, no un bug. Ganancia VISIBLE de bajo riesgo (no toca pipeline):
- **PCC**: el `inner_radius_km=20` pinta el lacolito difuso offset (mediana 10.5km del cráter
  Puyehue = Cordón Caulle real) como "summit-rojo" denso. Opción: renderizar el campo lejano
  como "extensión" (naranja) cuando está lejos del cráter físico, NO summit-rojo.
- **Ventana del mapa + dedup**: el mapa acumula 30 días sin deduplicar (1 punto/pasada × ~8
  sensores). Acortar a 48h/7d y/o deduplicar por noche/celda reduce la densidad visual.
- **Replicar en las 3 vistas** (S92 L5). Verificación = preview real (no node --check).
- Detalle: `docs/AUDIT_S103_OVERDETECTION_PCC_VILLARRICA.md`. Display-only, sin A45.

## §2 — Frente path D (magnitud, 2ª palanca; brainstorming + A45)
- **VIIRS750 glaciar** (Tupun/PP 16.6×, Isluga 4.76× residual): **portar ctxpeak a VIIRS750**.
  A48 YA VERIFICADO (S103, `docs/S103_S2_VIIRS750_PATHD_PREP.md`): ctxpeak está SOLO en
  process_viirs.py (VIIRS375), ausente en process_viirs_mod.py (VIIRS750) y process_modis.py.
  Test1 domina el residuo (53-86%) PERO hay eruption-source (31-47%) + D9 ya capea 15-35% →
  ctxpeak ayuda a la mayoría, NO resuelve todo. Espejo VIIRS375 (filtro contextual + keep-peak).
  ⚠️ El nadir VIIRS ya reduce algo el residuo — re-medir baseline VIIRS750 actual antes.
- **PCC MODIS** (residuo path D 2 recs 27+60MW, contextual t_bg 270-272K): cap D9 270→273K
  (verificar vs TIF que no enmascara magnitud real) O dejar cat-b. Opción C (gate intra-radio)
  VETADA A55.
- **D9/A23 raíz** (sobre-detección sistémica path-D): co-validación BT/NTI para path-D
  contextual + discriminante de cirrus mejor que `t_bg` (contaminado por altitud, A68). Frente
  grande. Brainstorming + A45.

## §3 — Pasivos / monitoreo / higiene menor
- **NRT**: verde; verificar que sigue (`gh run list --workflow=nrt.yml`). El cron diurno UTC
  ahora procesa el día en curso (S96).
- **Workflow re-reproc** `reproc-s103-viirs-pcc-tupun.yml` (#372): one-off, archivar en algún
  cleanup futuro (junto con reproc-s101/s102 cuando ya no se referencien).
- **MEMORY.md sobre el cap** (~580+ líneas, M9 dice ≤500): correr `consolidate-memory` para
  archivar detalle S80-S95 a `MEMORY_ARCHIVE_*`. Pendiente desde antes.
- **Branches remotas stale** (~76+): podar las `--merged origin/main` (no hecho).
- **Higiene git menor** (evaluada baja prioridad S103): `*.tif` gitignore es fiddly (kmz/*.tif
  son R2 intencionales → necesita excepción); test golden stale es skip deliberado. Skip salvo
  pedido.

## Tags defensivos S103
`pre-s103-nadir-fixed-viirs`, `pre-s103-workflows-cleanup`, `pre-s81-discard-nostalgic-aryabhata`
(pusheado a origin). Branches con trabajo sin mergear preservadas en GitHub: `claude/s79-f66-
hybrid-bg-gate` (F66 Tasks 7-15), `claude/s81-vrp-tir-gate` (S82).

## Lecciones de tooling S103 (entorno, ver memoria feedback_s103_tooling)
- `sleep` NO espera de verdad en comandos background → usar `gh run watch` (espera interna)
  para esperar runs CI, no loops de sleep.
- `gh run watch` puede salir rc=1 por timeout de red transitorio (el run sigue sano) → verificar
  el run directo y relanzar.
- `gh pr create --body "...\`x\`..."` con backticks en bash = command substitution (mangла el
  body) → usar archivo/heredoc o evitar backticks.
- `gh run download` NO sobreescribe artifacts existentes → `rm -rf` el subdir antes de re-bajar.

---
## Prompt copy-paste para S104
```
Sesión S104 — VRP Chile. Sincronizá (raíz "VRP Chile/" en main: git fetch origin --prune
&& git pull --ff-only) y leé tasks/BLOQUE_ARRANQUE_S104.md + project_s103_estado (memoria).

S103 cerró §1: nadir-fijo VIIRS adoptado+promovido+validado (R3 VIIRS375 2.27→0.78×, 0 FN
nuevos, Villarrica 18→1×, R8 live). Todo en producción.

PRIORIDAD §1 recomendada: mejorar el DISPLAY de PCC/Villarrica (cierra la observación de
Nicolás de "sobre-detección" — que la re-auditoría A68 mostró que es display+recall real,
no bug): PCC lacolito difuso como "extensión" naranja no summit-rojo, ventana/dedup del mapa,
replicar en las 3 vistas (S92 L5), verificar preview. Display-only, sin A45.
Después §2: portar ctxpeak a VIIRS750 (A48 ya verificado) + cap D9 PCC MODIS — brainstorming
+ A45. Y D9/A23 raíz (co-validación path-D, discriminante cirrus mejor que t_bg).

Recordá: explicame como geólogo; si dudás, refutá con datos antes de reafirmar (A62);
no mezcles MODIS con VIIRS; antes de tocar pipeline operacional = A45 (tag + OK + TDD).
```
